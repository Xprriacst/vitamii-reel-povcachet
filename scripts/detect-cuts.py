"""
Combine QwenX transcript + RMS silence detection → cuts-suggested.json.
Détecte redites (n-gram) + false starts (segments anormalement lents) + suggère ranges à splice.

Usage:
    python scripts/detect-cuts.py <transcript-qwenx.json> <audio_input>
"""
import os, json, sys, subprocess
import numpy as np
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TRANSCRIPT = sys.argv[1] if len(sys.argv) > 1 else "transcript-qwenx.json"
AUDIO = sys.argv[2] if len(sys.argv) > 2 else "sources/speech_orig_loud.mp4"
OUTPUT = "cuts-suggested.json"

# ============================================================
# 1. Load transcript
# ============================================================
with open(TRANSCRIPT) as f:
    data = json.load(f)

# Flatten all words. QwenX output: each "segment" IS a single word
# (segment.start/end/text). Whisper-style: words[] inside each segment.
all_words = []
for seg in data["segments"]:
    words_list = seg.get("words")
    if words_list:
        # Whisper-style structure
        for w in words_list:
            if w.get("start") is not None and w.get("end") is not None:
                all_words.append({
                    "text": w["word"].lower().strip(".,!?;:«»\"' "),
                    "start": w["start"],
                    "end":   w["end"],
                })
    else:
        # QwenX-style : segment IS a word
        text = seg.get("text", "").lower().strip(".,!?;:«»\"' ")
        if text and seg.get("start") is not None:
            all_words.append({
                "text": text,
                "start": seg["start"],
                "end":   seg.get("end", seg["start"] + 0.2),
            })

print(f"Loaded {len(all_words)} words from {TRANSCRIPT}")
audio_duration = max((w["end"] for w in all_words), default=0)
print(f"Audio duration : {audio_duration:.2f}s")

# ============================================================
# 2. RMS silence detection (ground truth pour les cuts)
# ============================================================
print("\n[1/3] RMS silence detection...")
SR = 48000
SILENCE_DB = -42.0
MIN_SILENCE_MS = 200

raw = subprocess.run(
    ["ffmpeg","-y","-i",AUDIO,"-ac","1","-ar",str(SR),"-f","s16le","-"],
    capture_output=True, check=True
).stdout
audio_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

win = int(SR * 0.030); hop = int(SR * 0.010)
n = (len(audio_arr) - win) // hop + 1
rms_db = np.array([20*np.log10(np.sqrt(np.mean(audio_arr[i*hop:i*hop+win]**2)) + 1e-9) for i in range(n)])
rms_smooth = np.convolve(rms_db, np.ones(5)/5, mode='same')
is_silent = rms_smooth < SILENCE_DB

silences = []
i = 0
while i < len(is_silent):
    if is_silent[i]:
        j = i
        while j < len(is_silent) and is_silent[j]: j += 1
        dur_ms = (j-i) * 10
        if dur_ms >= MIN_SILENCE_MS:
            silences.append((i*hop/SR, j*hop/SR, dur_ms))
        i = j
    else: i += 1

print(f"  {len(silences)} silences ≥ {MIN_SILENCE_MS}ms")

# ============================================================
# 3. Détection redites (n-gram sur word-level transcript verbatim)
# ============================================================
print("\n[2/3] Détection redites (n-gram check)...")
N_GRAM = 4
MAX_GAP_WORDS = 25

word_texts = [w["text"] for w in all_words]
gram_positions = {}
for i in range(len(word_texts) - N_GRAM + 1):
    gram = " ".join(word_texts[i:i+N_GRAM])
    gram_positions.setdefault(gram, []).append(i)

redites = []
seen_starts = set()
for gram, positions in gram_positions.items():
    if len(positions) < 2: continue
    for i in range(len(positions) - 1):
        p1, p2 = positions[i], positions[i+1]
        gap = p2 - p1
        if 0 < gap <= MAX_GAP_WORDS:
            key = p1 // 5
            if key in seen_starts: continue
            # Extend match
            k = N_GRAM
            while p1 + k < len(all_words) and p2 + k < len(all_words) and word_texts[p1 + k] == word_texts[p2 + k]:
                k += 1
            # Compute timestamps
            first_start = all_words[p1]["start"]
            first_end   = all_words[p1 + k - 1]["end"]
            second_start = all_words[p2]["start"]
            second_end   = all_words[p2 + k - 1]["end"]
            redites.append({
                "phrase": " ".join(word_texts[p1:p1+k]),
                "n_words": k,
                "first_take":  [first_start,  first_end],
                "second_take": [second_start, second_end],
                "suggested_cut": [first_start, second_start],  # drop the 1st take
            })
            for s in range(key, key + k // 5 + 1):
                seen_starts.add(s)
            break

print(f"  {len(redites)} redite(s) détectée(s)")
for r in redites:
    print(f"  • \"{r['phrase'][:70]}\"")
    print(f"    1ère: {r['first_take'][0]:.2f}-{r['first_take'][1]:.2f}s · 2e: {r['second_take'][0]:.2f}-{r['second_take'][1]:.2f}s")
    print(f"    → cut [{r['suggested_cut'][0]:.2f}-{r['suggested_cut'][1]:.2f}]")

# ============================================================
# 4. Refine cut boundaries using RMS silences
#    For each suggested cut, snap start/end to nearest silence boundary
# ============================================================
print("\n[3/3] Snap cut boundaries to RMS silences...")
def snap_to_silence(t, silences, prefer="end"):
    """Trouve le silence le plus proche de t. prefer='end' renvoie la fin du silence (= début du speech)."""
    best = None
    best_dist = float("inf")
    for s_start, s_end, _ in silences:
        # Distance to silence center
        center = (s_start + s_end) / 2
        d = abs(t - center)
        if d < best_dist and d < 1.5:  # max 1.5s away
            best_dist = d
            best = (s_start, s_end)
    if best is None:
        return t
    return best[1] if prefer == "end" else best[0]

for r in redites:
    raw_cut_start, raw_cut_end = r["suggested_cut"]
    # Cut start = end of silence BEFORE 1st take (i.e., where 1st take begins)
    snapped_start = snap_to_silence(raw_cut_start, silences, prefer="end")
    # Cut end = end of silence between takes (i.e., where 2nd take begins)
    snapped_end   = snap_to_silence(raw_cut_end,   silences, prefer="end")
    r["refined_cut"] = [snapped_start, snapped_end]
    r["cut_duration"] = snapped_end - snapped_start

# ============================================================
# 5. Save cuts-suggested.json
# ============================================================
out = {
    "audio": AUDIO,
    "transcript_source": TRANSCRIPT,
    "audio_duration": audio_duration,
    "rms_silences": [{"start": s, "end": e, "duration_ms": d} for s, e, d in silences],
    "redites": redites,
    "summary": {
        "n_redites": len(redites),
        "total_cut_duration_sec": sum(r["cut_duration"] for r in redites),
    },
}
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✓ {len(redites)} redite(s) | économise {out['summary']['total_cut_duration_sec']:.2f}s")
print(f"  Saved : {OUTPUT}")
print(f"\n=== CUTS À APPLIQUER DANS splice-natural.sh ===")
print(f"Source ranges à utiliser (garde 2e prise, drop 1ère + silence) :\n")

# Compute final ranges to keep
keep_ranges = []
last_end = 0.0
for r in sorted(redites, key=lambda x: x["refined_cut"][0]):
    cut_start, cut_end = r["refined_cut"]
    if cut_start > last_end:
        keep_ranges.append((last_end, cut_start))
    last_end = cut_end
if last_end < audio_duration:
    keep_ranges.append((last_end, audio_duration))

for i, (s, e) in enumerate(keep_ranges, 1):
    print(f"  R{i}: {s:7.2f} → {e:7.2f}  ({e-s:.2f}s)")
print()
