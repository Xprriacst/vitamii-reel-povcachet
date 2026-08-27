#!/bin/bash
# verifier-installation.sh — smoke test de bout en bout, sans aucun rush.
#
#   bash scripts/verifier-installation.sh
#
# Fabrique un clip synthétique de 6 s (mire + deux « phrases » séparées par des
# silences), le fait passer dans TOUTE la chaîne — loudnorm, détection de silences,
# splice sans freeze frame, captions, lint, rendu draft — et dit ce qui manque.
#
# Tout se passe dans un dossier temporaire : rien n'est écrit dans ton projet.
# L'ASR n'est pas testé ici (1,8 Go de modèles) : le tester à part avec
#   python3 scripts/transcribe-qwenx.py <un-audio> /tmp/t.json

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'echo; echo "  (dossier de test : $WORK)"' EXIT

PASS=0; FAIL=0; SKIP=0
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
ko()   { printf "  \033[31m✗\033[0m %s\n     → %s\n" "$1" "$2"; FAIL=$((FAIL+1)); }
skip() { printf "  \033[33m—\033[0m %s\n     → %s\n" "$1" "$2"; SKIP=$((SKIP+1)); }

echo "════════════════════════════════════════════════════════════════"
echo "  VÉRIFICATION DE L'INSTALLATION"
echo "════════════════════════════════════════════════════════════════"
echo
echo "─── Outils ───"

command -v ffmpeg  >/dev/null && ok "ffmpeg  $(ffmpeg -version | head -1 | cut -d' ' -f3)" \
  || ko "ffmpeg absent" "brew install ffmpeg  (ou winget install Gyan.FFmpeg)"
command -v ffprobe >/dev/null && ok "ffprobe" || ko "ffprobe absent" "il vient avec ffmpeg"

NODE_OK=0
if command -v node >/dev/null; then
  NV=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$NV" -ge 22 ]; then ok "node $(node -v)"; NODE_OK=1
  else ko "node $(node -v) — HyperFrames exige Node ≥ 22" "installe Node 22 LTS"; fi
else ko "node absent" "https://nodejs.org (LTS)"; fi

# Python : venv du projet, sinon système
PY=""
for cand in "$SKILL_DIR/../../.venv/bin/python" ".venv/bin/python" ".venv/Scripts/python" python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1 || [ -x "$cand" ]; then PY="$cand"; break; fi
done
if [ -n "$PY" ]; then
  ok "python $("$PY" --version 2>&1 | cut -d' ' -f2)  ($PY)"
  if "$PY" -c "import numpy, scipy" 2>/dev/null; then ok "numpy + scipy"
  else ko "numpy/scipy manquants dans $PY" \
          "python3.12 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"; fi
else ko "python3 absent" "brew install python@3.12"; fi

command -v ffmpeg >/dev/null || { echo; echo "ffmpeg est indispensable, on s'arrête ici."; exit 1; }

# ════════════════════════════════════════════════════════════════
echo
echo "─── Chaîne audio ───"
cd "$WORK"
mkdir -p sources renders sfx
cp -R "$SKILL_DIR/scripts" scripts

# Clip synthétique : 6 s, deux « phrases » (1,0-3,0 et 3,8-5,6) séparées par des silences.
ffmpeg -y -f lavfi -i "testsrc2=size=540x960:rate=30:duration=6" \
       -f lavfi -i "sine=frequency=190:duration=6" \
       -filter_complex "[1:a]volume='(between(t,1.0,3.0)+between(t,3.8,5.6))*0.06':eval=frame[a]" \
       -map 0:v -map "[a]" -c:v libx264 -preset ultrafast -pix_fmt yuv420p \
       -c:a aac -shortest sources/source.mov >/dev/null 2>&1 \
  && ok "clip de test fabriqué (6 s, 2 phrases + silences)" \
  || ko "génération du clip impossible" "ffmpeg sans libx264 ou sans lavfi ?"

ffmpeg -y -i sources/source.mov \
  -af "loudnorm=I=-5:LRA=4:TP=-0.5,acompressor=threshold=0.20:ratio=4:attack=3:release=60,alimiter=level_in=1:level_out=0.95:limit=0.97:attack=3:release=50" \
  -c:v copy sources/speech_orig_loud.mp4 >/dev/null 2>&1
if [ -s sources/speech_orig_loud.mp4 ]; then
  MEAN=$(ffmpeg -i sources/speech_orig_loud.mp4 -filter:a volumedetect -f null /dev/null 2>&1 \
         | awk '/mean_volume/{print $5}')
  ok "loudnorm + compresseur + limiteur (mean ${MEAN} dB sur un signal de test)"
else
  ko "loudnorm a échoué" "ffmpeg trop ancien : le filtre loudnorm manque"
fi

bash scripts/check-audio.sh sources/speech_orig_loud.mp4 >/dev/null 2>&1 \
  && ok "check-audio.sh (les portes de contrôle audio)" \
  || ko "check-audio.sh ne tourne pas" "awk ou bash manquant ?"

if [ -n "$PY" ] && "$PY" -c "import numpy" 2>/dev/null; then
  if "$PY" scripts/detect-silences.py sources/speech_orig_loud.mp4 > /tmp/sil.txt 2>&1; then
    N=$(grep -c "ms " /tmp/sil.txt || true)
    ok "detect-silences.py — $N silence(s) détecté(s) (attendu : 3)"
  else
    ko "detect-silences.py a échoué" "$(tail -1 /tmp/sil.txt)"
  fi
else
  skip "detect-silences.py" "numpy indisponible"
fi

# Splice : méthode vidéo-prolongée (video_end = audio_end + pad), jamais de freeze frame
ffmpeg -y -i sources/speech_orig_loud.mp4 -filter_complex "
  [0:v]trim=start=1.0:end=3.2,setpts=PTS-STARTPTS[v1];
  [0:a]atrim=start=1.0:end=3.0,asetpts=PTS-STARTPTS,apad=pad_dur=0.2[a1];
  [0:v]trim=start=3.8:end=5.6,setpts=PTS-STARTPTS[v2];
  [0:a]atrim=start=3.8:end=5.6,asetpts=PTS-STARTPTS[a2];
  [v1][a1][v2][a2]concat=n=2:v=1:a=1[v][a]
" -map "[v]" -map "[a]" -c:v libx264 -preset ultrafast -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k speech.mp4 >/dev/null 2>&1

if [ -s speech.mp4 ]; then
  read -r VD AD <<< "$(ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 speech.mp4 \
    | awk -F, '$1=="video"{v=$2} $1=="audio"{a=$2} END{print v, a}')"
  DIFF=$(awk -v v="$VD" -v a="$AD" 'BEGIN{d=v-a; print (d<0?-d:d)}')
  if awk -v d="$DIFF" 'BEGIN{exit !(d<=0.05)}'; then
    ok "splice sans freeze frame — durées A/V alignées (écart ${DIFF}s)"
  else
    ko "splice : dérive A/V de ${DIFF}s" "video_end doit valoir audio_end + pad_dur"
  fi
else
  ko "le splice a échoué" "voir la sortie ffmpeg à la main"
fi

# ════════════════════════════════════════════════════════════════
echo
echo "─── Captions ───"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 speech.mp4 2>/dev/null | cut -d. -f1,2)
cat > transcript-words.json <<'JSON'
[
 {"text":"voici","start":0.10,"end":0.45},
 {"text":"un","start":0.50,"end":0.62},
 {"text":"test","start":0.66,"end":1.05},
 {"text":"de","start":1.40,"end":1.52},
 {"text":"la","start":1.56,"end":1.68},
 {"text":"chaîne","start":1.72,"end":2.20},
 {"text":"Claude","start":2.60,"end":3.10},
 {"text":"github","start":3.20,"end":3.70}
]
JSON
if [ "$NODE_OK" = 1 ]; then
  if node scripts/build-captions.mjs > /tmp/cap.txt 2>&1; then
    G=$(grep -o "Generated [0-9]*" /tmp/cap.txt | cut -d' ' -f2)
    ok "build-captions.mjs — $G groupes générés"
    # la règle de casse : minuscules partout SAUF les noms propres
    if grep -q '"text": "Claude"' captions.js && grep -q '"text": "GitHub"' captions.js \
       && grep -q '"text": "voici"' captions.js; then
      ok "règle de casse (minuscules sauf noms propres : Claude, GitHub)"
    else
      ko "la règle de casse ne s'applique pas" "vérifier PROPER_NOUNS / TEXT_FIX"
    fi
  else
    ko "build-captions.mjs a échoué" "$(tail -1 /tmp/cap.txt)"
  fi
  if "$PY" scripts/asr-to-words.py transcript-words.json /tmp/w.json >/dev/null 2>&1; then
    ok "asr-to-words.py (adaptateur de format ASR)"
  else
    skip "asr-to-words.py" "python indisponible"
  fi
else
  skip "build-captions.mjs" "Node ≥ 22 requis"
fi

# ════════════════════════════════════════════════════════════════
echo
echo "─── Effets sonores ───"
LIB="$SKILL_DIR/assets/sfx-library"
if [ -d "$LIB" ]; then
  NMP3=$(find "$LIB" -name "*.mp3" | wc -l | tr -d ' ')
  NCAT=$(find "$LIB" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
  ok "librairie fournie — $NMP3 sons, $NCAT familles ($(du -sh "$LIB" | cut -f1))"
else
  ko "assets/sfx-library/ introuvable" "la librairie doit être livrée avec le kit"
fi

# La sélection doit être cohérente ET pointer sur des fichiers qui existent vraiment
if [ -n "$PY" ] && "$PY" -c "
import json, os, sys
d = json.load(open('scripts/sfx-selection.json'))
s = d['sounds']
assert all(k in x for x in s for k in ('role','id','category','file','lpf')), 'champ manquant'
assert all(x['lpf'] <= 4000 for x in s), 'un son dépasse 4000 Hz'
lib = os.path.join('$SKILL_DIR', 'assets', 'sfx-library')
missing = [f\"{x['category']}/{x['file']}\" for x in s
           if not os.path.exists(os.path.join(lib, x['category'], x['file']))]
if missing:
    sys.exit('introuvables dans la librairie : ' + ', '.join(missing[:3]))
print(len(s))
" > /tmp/sel.txt 2>&1; then
  ok "sélection — $(cat /tmp/sel.txt) sons, réglages complets, tous présents dans la librairie"
else
  ko "sfx-selection.json incohérent" "$(tail -1 /tmp/sel.txt)"
fi

# ════════════════════════════════════════════════════════════════
echo
echo "─── HyperFrames ───"
if [ "$NODE_OK" = 1 ]; then
  cp "$SKILL_DIR/assets/projet-template/hyperframes.json" .
  cp "$SKILL_DIR/assets/projet-template/package.json" .
  # composition minimale calée sur la durée réelle du clip splicé
  sed -e "s/data-duration=\"12\"/data-duration=\"$DUR\"/g" \
      -e "s/const DUR = 12;/const DUR = $DUR;/" \
      "$SKILL_DIR/assets/projet-template/index.html" > index.html
  # bande-son de test : un silence de la bonne durée, pour valider le câblage audio
  # (plutôt que de retirer la piste — un <audio> tient sur 2 lignes et un grep -v
  #  laisserait la seconde ligne d'attributs s'afficher comme du texte dans le cadre)
  ffmpeg -y -f lavfi -i "anullsrc=r=48000:cl=mono" -t "$DUR" \
         -c:a aac -b:a 128k sfx/soundtrack-final.m4a >/dev/null 2>&1

  if npx --yes hyperframes@0.6.12 lint > /tmp/lint.txt 2>&1; then
    ok "hyperframes lint — 0 erreur"
  else
    ko "hyperframes lint remonte des erreurs" "$(grep -iE 'error|✗' /tmp/lint.txt | head -2 | tr '\n' ' ')"
  fi

  echo "     (rendu draft en cours, ~1 min au premier lancement — téléchargement de Chromium)"
  npx --yes hyperframes@0.6.12 render --quality draft --fps 24 --workers 2 \
      -o renders/smoke.mp4 . > /tmp/render.txt 2>&1
  # le code de sortie n'est PAS fiable : on vérifie le fichier ET la log
  if [ -s renders/smoke.mp4 ] && ! grep -qi "render failed" /tmp/render.txt; then
    SZ=$(du -h renders/smoke.mp4 | cut -f1)
    ok "rendu draft — renders/smoke.mp4 ($SZ)"
  else
    ko "le rendu a échoué" "$(grep -iE 'error|failed' /tmp/render.txt | head -2 | tr '\n' ' ')"
    echo "        log complète : /tmp/render.txt"
  fi
else
  skip "hyperframes lint + render" "Node ≥ 22 requis"
fi

# ════════════════════════════════════════════════════════════════
echo
echo "════════════════════════════════════════════════════════════════"
printf "  %d OK · %d échec(s) · %d ignoré(s)\n" "$PASS" "$FAIL" "$SKIP"
if [ "$FAIL" -eq 0 ] && [ "$SKIP" -eq 0 ]; then
  echo "  ✅ Tout est en place. Tu peux monter."
elif [ "$FAIL" -eq 0 ]; then
  echo "  ⚠️  Le cœur fonctionne ; les étapes ignorées le seront tant que la dépendance manque."
else
  echo "  ❌ Corriger les échecs ci-dessus (references/01-installation.md)."
fi
echo "════════════════════════════════════════════════════════════════"
[ "$FAIL" -eq 0 ]
