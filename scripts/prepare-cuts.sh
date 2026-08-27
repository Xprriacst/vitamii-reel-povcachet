#!/bin/bash
# prepare-cuts.sh — tout ce qui précède le décut, en une commande.
#
#   1. Synchro micro externe ↔ caméra (offset par CONSENSUS de fenêtres)
#   2. Nettoyage de la voix (loudnorm + compresseur + limiteur) + PORTE B
#   3. Transcription verbatim avec timestamps mot
#   4. Détection des redites (n-gram) recoupée avec les silences RMS
#   5. Écrit cuts-suggested.json — les ranges à reporter dans splice-natural.sh
#
# Usage (depuis la racine du projet) :
#   bash scripts/prepare-cuts.sh sources/source.mov sources/mic.wav   # micro séparé
#   bash scripts/prepare-cuts.sh sources/source.mov                   # audio caméra
#   bash scripts/prepare-cuts.sh sources/synced.mov                   # déjà synchronisé
#
# L'étape 3 utilise Qwen3-ASR via MLX (Apple Silicon). Sur une autre plateforme :
# lance les étapes 1-2, transcris avec ton ASR, convertis avec asr-to-words.py, puis
# relance detect-cuts.py. Voir references/01-installation.md.

set -e
cd "$(dirname "$0")/.."          # racine du projet (où vivent sources/ et les sorties)
PIPE="scripts"

# Python : le venv du projet si présent, sinon celui du système
if   [ -x ".venv/bin/python" ];      then PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python" ];  then PY=".venv/Scripts/python"     # Windows/Git Bash
elif command -v python3 >/dev/null;  then PY="python3"
else echo "❌ Python introuvable. Voir references/01-installation.md"; exit 1
fi
"$PY" -c "import numpy" 2>/dev/null || {
  echo "❌ numpy manquant dans $PY"
  echo "   python3.12 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
  exit 1
}

SOURCE_VIDEO="${1:-sources/source.mov}"
MIC_WAV="${2:-}"
[ -f "$SOURCE_VIDEO" ] || { echo "❌ $SOURCE_VIDEO introuvable"; exit 1; }

echo "════════════════════════════════════════════════════════════"
echo "  PREPARE-CUTS"
echo "════════════════════════════════════════════════════════════"
echo "  Vidéo  : $SOURCE_VIDEO"
[ -n "$MIC_WAV" ] && echo "  Micro  : $MIC_WAV"
echo "  Python : $PY"
echo

# ════════════════════════════════════════════════════════════
# 1. Synchro micro ↔ caméra
# ════════════════════════════════════════════════════════════
if [ -n "$MIC_WAV" ] && [ -f "$MIC_WAV" ]; then
    echo "[1/5] Synchro micro ↔ caméra"

    # 1a. Offset audio interne du rush : les iPhone/Pixel/DJI démarrent souvent le micro
    #     quelques frames APRÈS la vidéo. L'ignorer donne une désynchro labiale constante.
    AUDIO_START=$(ffprobe -v error -select_streams a:0 -show_entries stream=start_time \
                    -of csv=p=0 "$SOURCE_VIDEO" 2>/dev/null | head -1)
    echo "      audio start_time du rush : ${AUDIO_START:-0} s"

    # 1b. Offset par consensus de fenêtres. On NE fait PAS confiance au pic de
    #     cross-corrélation globale : il se verrouille souvent sur une prise répétée.
    echo "      calcul de l'offset par consensus (peut prendre ~30 s)…"
    "$PY" "$PIPE/verify-offset.py" "$SOURCE_VIDEO" "$MIC_WAV" | tee /tmp/offset.log | sed 's/^/      /'
    OFFSET=$(grep '^CONSENSUS_OFFSET=' /tmp/offset.log | cut -d= -f2)
    AGREE=$(grep '^CONSENSUS_AGREE=' /tmp/offset.log | cut -d= -f2)

    if [ -z "$OFFSET" ]; then
        echo "  ❌ offset non déterminé — vérifie que les deux fichiers contiennent bien la même voix"
        exit 1
    fi
    echo
    echo "      → offset retenu : ${OFFSET}s (consensus ${AGREE})"
    echo "      ⚠️  PORTE A : si le consensus est faible (< 80 % des fenêtres), NE PAS continuer"
    echo "         sans vérifier à la main (un clap, ou l'audio témoin de la caméra)."

    VIDEO_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SOURCE_VIDEO")
    ffmpeg -y -ss "$OFFSET" -i "$MIC_WAV" -t "$VIDEO_DUR" \
        -c:a pcm_s16le -ar 48000 -ac 1 sources/mic_trimmed.wav 2>&1 | tail -1
    ffmpeg -y -i "$SOURCE_VIDEO" -i sources/mic_trimmed.wav \
        -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest sources/synced.mov 2>&1 | tail -1
    SYNCED="sources/synced.mov"
else
    echo "[1/5] Pas de micro séparé — on garde l'audio de la vidéo"
    SYNCED="$SOURCE_VIDEO"
fi

# ════════════════════════════════════════════════════════════
# 2. Nettoyage de la voix
# ════════════════════════════════════════════════════════════
echo
echo "[2/5] Nettoyage de la voix (loudnorm I=-5 + compresseur + limiteur)"
ffmpeg -y -i "$SYNCED" \
    -af "loudnorm=I=-5:LRA=4:TP=-0.5,acompressor=threshold=0.20:ratio=4:attack=3:release=60,alimiter=level_in=1:level_out=0.95:limit=0.97:attack=3:release=50" \
    -c:v copy sources/speech_orig_loud.mp4 2>&1 | tail -1

echo
echo "      ═══ PORTE B ═══"
bash "$PIPE/check-audio.sh" sources/speech_orig_loud.mp4 | sed 's/^/      /'
echo "      Attendu : mean -19 à -21 dB, peak -2 à -4 dB."
echo "      Si mean ≈ -37 dB → le loudnorm a échoué, NE PAS CONTINUER."

# ════════════════════════════════════════════════════════════
# 3. Transcription verbatim
# ════════════════════════════════════════════════════════════
echo
echo "[3/5] Transcription verbatim + timestamps mot"
if "$PY" -c "import mlx_qwen3_asr" 2>/dev/null; then
    "$PY" "$PIPE/transcribe-qwenx.py" sources/speech_orig_loud.mp4 transcript-qwenx.json \
        2>&1 | grep -i "qwenx\|✓" | sed 's/^/      /'
else
    echo "      ⚠️  mlx-qwen3-asr indisponible sur cette machine."
    echo "         Transcris sources/speech_orig_loud.mp4 avec ton ASR (word-level), puis :"
    echo "           python3 scripts/asr-to-words.py <sortie.json> transcript-qwenx-words.json"
    echo "           python3 scripts/detect-cuts.py transcript-qwenx.json sources/speech_orig_loud.mp4"
    echo
    echo "      En attendant, voici le catalogue des silences (il suffit pour décuper à la main) :"
    "$PY" "$PIPE/detect-silences.py" sources/speech_orig_loud.mp4 | sed 's/^/        /'
    exit 0
fi

# ════════════════════════════════════════════════════════════
# 4. Redites + silences RMS
# ════════════════════════════════════════════════════════════
echo
echo "[4/5] Détection des redites + silences RMS"
"$PY" "$PIPE/detect-cuts.py" transcript-qwenx.json sources/speech_orig_loud.mp4 2>&1 | sed 's/^/      /'

# ════════════════════════════════════════════════════════════
# 5. Suite
# ════════════════════════════════════════════════════════════
echo
echo "════════════════════════════════════════════════════════════"
echo "  ✓ TERMINÉ"
echo "════════════════════════════════════════════════════════════"
echo "  Générés :  sources/speech_orig_loud.mp4   (voix nettoyée)"
echo "             transcript-qwenx.json          (verbatim + timestamps mot)"
echo "             cuts-suggested.json            (ranges proposés)"
echo
echo "  Suite :"
echo "    1. RELIRE cuts-suggested.json — c'est une aide, pas un verdict."
echo "       Recouper avec :  $PY scripts/detect-silences.py"
echo "    2. Reporter les ranges dans scripts/splice-natural.sh"
echo "    3. bash scripts/splice-natural.sh                → speech.mp4"
echo "    4. $PY scripts/transcribe-qwenx.py speech.mp4 transcript.json"
echo "       node scripts/build-captions.mjs               → captions.js"
echo
