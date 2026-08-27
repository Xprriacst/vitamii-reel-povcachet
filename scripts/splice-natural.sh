#!/bin/bash
# splice-natural.sh — le décut : garde les bonnes prises, coupe blancs et faux départs,
# et fabrique speech.mp4 (le fichier de référence de tout le reste du montage).
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ >>> À ADAPTER À CHAQUE VIDÉO <<<                                             ║
# ║  1. Les RANGES ci-dessous (bornes trim/atrim) : les tiennes viennent de      ║
# ║     cuts-suggested.json (prepare-cuts.sh) recoupé avec detect-silences.py.   ║
# ║  2. concat=n=<nombre de ranges> et la liste [v1][a1][v2][a2]…                ║
# ║  3. Si la source n'est pas déjà en 1080×1920 : préfixe "scale=1080:1920,"    ║
# ║     au FACE_FILTER.                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# TROIS RÈGLES QUI NE CHANGENT PAS :
#
#  a) INPUT = sources/speech_orig_loud.mp4  (le fichier LOUDNORMÉ).
#     Lire sources/synced.mov donne un speech.mp4 à mean -37 dB : voix inaudible
#     dans le rendu final, et rien ne le signale. C'est le bug le plus récurrent.
#
#  b) JAMAIS tpad=stop_mode=clone (freeze frame). Pour faire respirer entre deux
#     prises, on PROLONGE LA VIDÉO dans le silence qui suit (le visage continue de
#     bouger) et on rallonge l'audio avec apad.
#
#  c) video_end = audio_end + pad_dur, pour CHAQUE range. Sinon la vidéo est plus
#     courte que l'audio de pad_dur à chaque raccord → dérive A/V cumulative
#     (jusqu'à ~3 s sur une vidéo de 60 s).
#
# Pauses recommandées : 0,25 s sur un pivot narratif · 0,20 s dans une même idée ·
# 0,15 s sur la dernière prise. Jamais plus de 0,30 s (on verrait articuler en silence).

set -e
cd "$(dirname "$0")/.."

IN="sources/speech_orig_loud.mp4"
[ -f "$IN" ] || { echo "❌ $IN introuvable — lance d'abord scripts/prepare-cuts.sh"; exit 1; }

# eq + unsharp lissent le visage ; deflicker compense les écarts de luminance entre
# prises sur 15 frames — c'est LUI qui supprime les sautes de lumière aux raccords.
# (Ne pas utiliser normalize=…:smoothing=N : il amplifie les variations.)
FACE_FILTER="eq=saturation=1.12:contrast=1.04:brightness=0.04:gamma=0.98,\
unsharp=5:5:0.50:5:5:0.0,deflicker=size=15:mode=am"

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ RANGES — exemple à 3 prises. Documente ce que tu gardes ET ce que tu vires : │
# │ dans deux semaines, c'est cette liste qui explique le montage.               │
# │                                                                             │
# │  R1 [ 0.57 →  5.02] l'accroche                      + pause 0.25            │
# │  R2 [ 8.14 → 20.29] le corps de l'idée              + pause 0.20            │
# │  R3 [29.32 → 42.21] la conclusion / le CTA          (pas de pause finale)   │
# │  VIRÉ : 5.02-8.14 (blanc) · 20.29-29.32 (faux départ inachevé + reprise)     │
# └─────────────────────────────────────────────────────────────────────────────┘

ffmpeg -y -i "$IN" -filter_complex "
  [0:v]trim=start=0.57:end=5.27,setpts=PTS-STARTPTS[v1];
  [0:a]atrim=start=0.57:end=5.02,asetpts=PTS-STARTPTS,apad=pad_dur=0.25[a1];

  [0:v]trim=start=8.14:end=20.49,setpts=PTS-STARTPTS[v2];
  [0:a]atrim=start=8.14:end=20.29,asetpts=PTS-STARTPTS,apad=pad_dur=0.20[a2];

  [0:v]trim=start=29.32:end=42.21,setpts=PTS-STARTPTS[v3];
  [0:a]atrim=start=29.32:end=42.21,asetpts=PTS-STARTPTS[a3];

  [v1][a1][v2][a2][v3][a3]concat=n=3:v=1:a=1[vc][a];
  [vc]${FACE_FILTER}[v]
" -map "[v]" -map "[a]" \
  -c:v libx264 -preset fast -crf 18 -r 30 -g 30 -keyint_min 30 \
  -c:a aac -b:a 192k -movflags +faststart speech.mp4

echo
echo "═══ PORTE C — à vérifier avant de continuer ═══"
bash scripts/check-audio.sh speech.mp4
ffprobe -v error -show_entries stream=codec_type,duration -of default=noprint_wrappers=1 speech.mp4
echo
echo "  Attendu : mean ≈ -20 dB (comme $IN). Si mean ≈ -37 dB → mauvais input, re-splice."
echo "  Attendu : durées vidéo et audio à ±0,02 s. Sinon → video_end ≠ audio_end + pad_dur."
echo
echo "  Ensuite : re-transcrire CE fichier (pas le rush), puis node scripts/build-captions.mjs"
