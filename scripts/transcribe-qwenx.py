"""
QwenX = Qwen3-ASR 0.6B + Qwen3-ForcedAligner-0.6B-8bit (MLX Apple Silicon).
Pipeline standard : transcription verbatim + word-level timestamps <100ms.

Usage:
    python scripts/transcribe-qwenx.py <input_audio> [output_json]
"""
import os, json, sys, time
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT = sys.argv[1] if len(sys.argv) > 1 else "sources/speech_orig_loud.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "transcript-qwenx.json"

print(f"[QwenX] Loading Qwen3-ASR + ForcedAligner...")
from mlx_qwen3_asr import transcribe, ForcedAligner
import mlx.core as mx

# ForcedAligner pour word-level timestamps <100ms
aligner = ForcedAligner(
    model_path="mlx-community/Qwen3-ForcedAligner-0.6B-8bit",
    dtype=mx.float16,
)

t0 = time.time()
print(f"[QwenX] Transcribing : {INPUT}")
result = transcribe(
    INPUT,
    language="French",       # explicit FR pour précision max
    return_timestamps=True,  # active la production de timestamps
    forced_aligner=aligner,  # alignment Qwen3 word-level
    verbose=False,
)
elapsed = time.time() - t0
print(f"[QwenX] Done in {elapsed:.1f}s")

# Serialize
out_data = {
    "text": result.text,
    "language": getattr(result, "language", "fr"),
    "transcribe_time_sec": elapsed,
    "model": "QwenX (Qwen3-ASR-0.6B + Qwen3-ForcedAligner-0.6B-8bit)",
    "segments": [],
}
for seg in (getattr(result, "segments", None) or []):
    seg_dict = {
        "start": seg.get("start") if isinstance(seg, dict) else getattr(seg, "start", None),
        "end":   seg.get("end")   if isinstance(seg, dict) else getattr(seg, "end", None),
        "text":  seg.get("text")  if isinstance(seg, dict) else getattr(seg, "text", ""),
    }
    words = seg.get("words") if isinstance(seg, dict) else getattr(seg, "words", None)
    if words:
        seg_dict["words"] = []
        for w in words:
            seg_dict["words"].append({
                "word":  w.get("word")  if isinstance(w, dict) else getattr(w, "word", getattr(w, "text", "")),
                "start": w.get("start") if isinstance(w, dict) else getattr(w, "start", None),
                "end":   w.get("end")   if isinstance(w, dict) else getattr(w, "end", None),
            })
    out_data["segments"].append(seg_dict)

# Build flat words array (compatible avec build-captions.mjs)
# Cas QwenX : chaque "segment" est un mot avec start/end
# Cas Whisper-style : words[] dans chaque segment
flat_words = []
for seg in out_data["segments"]:
    if seg.get("words"):
        for w in seg["words"]:
            if w["start"] is not None:
                flat_words.append({
                    "text": w["word"],
                    "start": w["start"],
                    "end":   w["end"],
                })
    elif seg.get("start") is not None and seg.get("text"):
        flat_words.append({
            "text": seg["text"],
            "start": seg["start"],
            "end":   seg.get("end", seg["start"] + 0.2),
        })

out_data["words"] = flat_words
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2, ensure_ascii=False)
print(f"[QwenX] Saved : {OUT}")
print(f"[QwenX] {len(out_data['segments'])} segments, {len(flat_words)} words")

# Also save flat words.json compatible avec pipeline existant
WORDS_OUT = OUT.replace(".json", "-words.json")
with open(WORDS_OUT, "w", encoding="utf-8") as f:
    json.dump(flat_words, f, indent=2, ensure_ascii=False)
print(f"[QwenX] Words list : {WORDS_OUT}")
