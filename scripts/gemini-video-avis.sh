#!/bin/bash
# Second avis d'un modèle vidéo natif (Gemini) sur une ou plusieurs vidéos :
# ressenti du mouvement, musique, ton — ce que l'analyse frame-par-frame ne capture pas.
# Requiert $GEMINI_API_KEY dans l'environnement (jamais de clé en clair ici).
#   bash gemini-video-avis.sh <video.mp4> [autres.mp4…]
# Sorties : work/gemini/<nom>-avis.md
set -euo pipefail

[ $# -ge 1 ] || { echo "usage: gemini-video-avis.sh <video.mp4> [...]"; exit 1; }
[ -n "${GEMINI_API_KEY:-}" ] || { echo "❌ GEMINI_API_KEY absente (export dans ~/.zshrc)"; exit 1; }

MODEL="${GEMINI_MODEL:-gemini-flash-latest}"
BASE="https://generativelanguage.googleapis.com"
PY="$HOME/.claude/.venv/bin/python"
mkdir -p work/gemini

PROMPT="Tu analyses une vidéo (pub verticale réseaux sociaux). Un monteur a déjà mesuré
les specs objectives (coupes, dB, transcription). Donne UNIQUEMENT ce que ses mesures
image-par-image ne capturent pas : 1) ressenti du mouvement et du rythme (fluidité,
énergie, où ça traîne/accélère), 2) musique : genre, tempo approx, ambiance, évolution,
interaction avec la voix, 3) ton émotionnel et ses bascules, 4) les 3 choses à
reproduire pour qu'un remontage « sonne » pareil. Concret et bref, en français."

for F in "$@"; do
  NAME=$(basename "${F%.*}" | tr ' /' '__')
  echo "═══════════ $NAME ═══════════"
  SIZE=$(stat -f%z "$F" 2>/dev/null || stat -c%s "$F")

  curl -s -D work/gemini/hdr.txt -o /dev/null "$BASE/upload/v1beta/files" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H "X-Goog-Upload-Protocol: resumable" -H "X-Goog-Upload-Command: start" \
    -H "X-Goog-Upload-Header-Content-Length: $SIZE" \
    -H "X-Goog-Upload-Header-Content-Type: video/mp4" \
    -H "Content-Type: application/json" -d "{\"file\": {\"display_name\": \"$NAME\"}}"
  UPLOAD_URL=$(grep -i "^x-goog-upload-url:" work/gemini/hdr.txt | tr -d '\r' | cut -d' ' -f2)
  [ -n "$UPLOAD_URL" ] || { echo "❌ pas d'URL d'upload (clé invalide ?)"; exit 1; }

  curl -s -o "work/gemini/$NAME-file.json" "$UPLOAD_URL" \
    -H "X-Goog-Upload-Command: upload, finalize" -H "X-Goog-Upload-Offset: 0" \
    --data-binary "@$F"
  FILE_NAME=$("$PY" -c "import json;print(json.load(open('work/gemini/$NAME-file.json'))['file']['name'])")
  FILE_URI=$("$PY" -c "import json;print(json.load(open('work/gemini/$NAME-file.json'))['file']['uri'])")

  for i in $(seq 1 30); do
    STATE=$(curl -s "$BASE/v1beta/$FILE_NAME" -H "x-goog-api-key: $GEMINI_API_KEY" \
      | "$PY" -c "import json,sys;print(json.load(sys.stdin).get('state','?'))")
    [ "$STATE" = "ACTIVE" ] && break
    sleep 4
  done
  echo "(fichier $STATE)"

  "$PY" - "$FILE_URI" "$PROMPT" > "work/gemini/$NAME-req.json" <<'EOF'
import json, sys
print(json.dumps({"contents": [{"parts": [
    {"file_data": {"file_uri": sys.argv[1], "mime_type": "video/mp4"}},
    {"text": sys.argv[2]}]}]}))
EOF
  curl -s "$BASE/v1beta/models/$MODEL:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" -H "Content-Type: application/json" \
    -d "@work/gemini/$NAME-req.json" > "work/gemini/$NAME-resp.json"
  "$PY" -c "
import json
r = json.load(open('work/gemini/$NAME-resp.json'))
try:
    print(r['candidates'][0]['content']['parts'][0]['text'])
except Exception:
    print('❌ réponse inattendue :', json.dumps(r)[:600])" | tee "work/gemini/$NAME-avis.md"
  echo
done
echo "→ work/gemini/*-avis.md"
