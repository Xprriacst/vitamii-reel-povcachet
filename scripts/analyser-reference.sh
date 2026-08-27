#!/bin/bash
# Analyse une vidéo de référence (exemple client) et en sort les specs mesurables :
# cadence des coupes, planche contact aux coupes, zone/style des sous-titres,
# profil sonore (musique vs voix), et transcription.
#
#   bash scripts/analyser-reference.sh <video.mp4> [--no-asr]
#
# Sorties dans work/ref/<nom>/ :
#   cuts.txt        timestamps des coupes + stats de cadence
#   contact.png     une vignette par plan (label = t + durée du plan)
#   captions.png    bande basse recadrée sur 4 moments (style/position du texte)
#   audio.txt       loudness globale + sweep par fenêtres de 2 s
#   transcript.txt  transcription (sauf --no-asr)
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:?usage: analyser-reference.sh <video> [--no-asr]}"
NO_ASR="${2:-}"
NAME="$(basename "${SRC%.*}" | tr ' /' '__')"
OUT="work/ref/$NAME"
mkdir -p "$OUT"
PY="$HOME/.claude/.venv/bin/python"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC")
GEO=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$SRC")
echo "═══ $NAME — ${DUR}s — $GEO ═══"

# ── 1. Détection des coupes (seuil 0.30 = changement de plan franc)
ffmpeg -v error -i "$SRC" -vf "select='gt(scene,0.30)',metadata=print:file=-" -an -f null - 2>/dev/null \
  | grep -o "pts_time:[0-9.]*" | cut -d: -f2 > "$OUT/cuts-raw.txt" || true

"$PY" - "$SRC" "$OUT" "$DUR" <<'EOF' > "$OUT/cuts.txt"
import sys, statistics
src, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
ts = [0.0] + [float(x) for x in open(f"{out}/cuts-raw.txt") if x.strip()]
# fusionne les détections trop proches (< 0.4 s = même coupe / flash)
merged = [ts[0]]
for t in ts[1:]:
    if t - merged[-1] >= 0.40:
        merged.append(t)
shots = [(merged[i], (merged[i+1] if i+1 < len(merged) else dur) - merged[i])
         for i in range(len(merged))]
print(f"{len(shots)} plans sur {dur:.1f}s")
print(f"cadence : médiane {statistics.median(d for _, d in shots):.2f}s · "
      f"min {min(d for _, d in shots):.2f}s · max {max(d for _, d in shots):.2f}s · "
      f"moyenne {sum(d for _, d in shots)/len(shots):.2f}s")
print()
for i, (t, d) in enumerate(shots, 1):
    print(f"  {i:3d}  {t:7.2f} → {t+d:7.2f}   {d:5.2f}s")
open(f"{out}/shots.txt", "w").write("\n".join(f"{t:.3f} {d:.3f}" for t, d in shots))
EOF
cat "$OUT/cuts.txt" | head -8

# ── 2. Planche contact : 1 vignette au milieu de chaque plan (24 max)
rm -f "$OUT"/thumb-*.png
i=0
while read -r t d; do
  i=$((i+1)); [ "$i" -gt 24 ] && break
  mid=$("$PY" -c "print(round($t + $d/2, 2))")
  ffmpeg -y -v error -ss "$mid" -i "$SRC" -frames:v 1 \
    -vf "scale=250:-1,drawtext=text='$i · ${mid}s · ${d}s':x=6:y=6:fontsize=17:fontcolor=yellow:box=1:boxcolor=black@0.65" \
    "$OUT/thumb-$(printf %02d $i).png" 2>/dev/null || true
done < "$OUT/shots.txt"
COLS=6
ffmpeg -y -v error -pattern_type glob -i "$OUT/thumb-*.png" -filter_complex "tile=${COLS}x4" "$OUT/contact.png" 2>/dev/null || true

# ── 3. Zone des sous-titres : bande basse (55→100 % de la hauteur) à 4 moments
H=$(echo "$GEO" | cut -d, -f2)
CROP_Y=$("$PY" -c "print(int($H*0.55))")
CROP_H=$("$PY" -c "print(int($H*0.45))")
rm -f "$OUT"/cap-*.png
j=0
for frac in 0.12 0.35 0.60 0.85; do
  j=$((j+1))
  t=$("$PY" -c "print(round($DUR*$frac, 2))")
  ffmpeg -y -v error -ss "$t" -i "$SRC" -frames:v 1 \
    -vf "crop=iw:$CROP_H:0:$CROP_Y,scale=520:-1,drawtext=text='t=${t}s':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.65" \
    "$OUT/cap-$j.png" 2>/dev/null || true
done
ffmpeg -y -v error -pattern_type glob -i "$OUT/cap-*.png" -filter_complex "tile=2x2" "$OUT/captions.png" 2>/dev/null || true

# ── 4. Profil sonore : loudness globale + sweep 2 s (repère la musique sous la voix)
{
  echo "── loudness globale ──"
  ffmpeg -hide_banner -i "$SRC" -af "volumedetect" -f null - 2>&1 | grep -E "mean_volume|max_volume" || true
  echo
  echo "── sweep par fenêtres de 2 s (mean dB) ──"
  n=$("$PY" -c "print(int($DUR//2))")
  for k in $(seq 0 $((n-1))); do
    s=$((k*2))
    v=$(ffmpeg -hide_banner -ss "$s" -t 2 -i "$SRC" -af "volumedetect" -f null - 2>&1 \
        | grep mean_volume | grep -o -- "-\?[0-9.]* dB" | head -1)
    printf "  %5ss  %s\n" "$s" "$v"
  done
} > "$OUT/audio.txt"
head -4 "$OUT/audio.txt"

# ── 5. Transcription
if [ "$NO_ASR" != "--no-asr" ]; then
  ffmpeg -y -v error -i "$SRC" -vn -ac 1 -ar 48000 -c:a aac -b:a 160k "$OUT/audio.m4a"
  "$PY" scripts/transcribe-qwenx.py "$OUT/audio.m4a" "$OUT/transcript.json" >/dev/null 2>&1 || true
  [ -f "$OUT/transcript.json" ] && "$PY" -c "
import json,sys
t=json.load(open('$OUT/transcript.json'))
print(t['text'] if isinstance(t,dict) and 'text' in t else t)" > "$OUT/transcript.txt" 2>/dev/null || true
fi

echo
echo "→ $OUT/  (contact.png · captions.png · cuts.txt · audio.txt · transcript.txt)"
