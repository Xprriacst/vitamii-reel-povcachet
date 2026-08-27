#!/bin/bash
# check-audio.sh — les portes de contrôle audio du pipeline, en une commande.
#
#   bash scripts/check-audio.sh sources/speech_orig_loud.mp4
#   bash scripts/check-audio.sh                       # vérifie tous les fichiers usuels
#
# Affiche mean/peak et dit si c'est dans la cible. Une erreur audio est SILENCIEUSE :
# elle se propage jusqu'au rendu final. C'est ce script qui l'attrape à temps.

set -uo pipefail

levels() {  # $1 = fichier → "mean peak"
  ffmpeg -i "$1" -filter:a volumedetect -f null /dev/null 2>&1 \
    | awk '/mean_volume/{m=$5} /max_volume/{p=$5} END{print m, p}'
}

# $1 fichier, $2 mean_min, $3 mean_max, $4 peak_min, $5 peak_max, $6 libellé
check() {
  local f="$1" lo="$2" hi="$3" plo="$4" phi="$5" label="$6"
  if [ ! -f "$f" ]; then
    printf "  \033[90m—     %-34s (absent)\033[0m\n" "$f"
    return 0
  fi
  read -r mean peak <<< "$(levels "$f")"
  if [ -z "${mean:-}" ]; then
    printf "  \033[31m✗\033[0m     %-34s pas de piste audio lisible\n" "$f"
    return 1
  fi
  local ok=1
  awk -v v="$mean" -v a="$lo" -v b="$hi" 'BEGIN{exit !(v>=a && v<=b)}' || ok=0
  awk -v v="$peak" -v a="$plo" -v b="$phi" 'BEGIN{exit !(v>=a && v<=b)}' || ok=0
  if [ "$ok" = 1 ]; then
    printf "  \033[32m✓\033[0m     %-34s mean %7s dB   peak %7s dB\n" "$f" "$mean" "$peak"
  else
    printf "  \033[31m✗\033[0m     %-34s mean %7s dB   peak %7s dB   \033[31m(cible : mean %s..%s / peak %s..%s — %s)\033[0m\n" \
      "$f" "$mean" "$peak" "$lo" "$hi" "$plo" "$phi" "$label"
  fi
  return 0
}

echo "═══ Niveaux audio ═══"

if [ $# -ge 1 ]; then
  # un fichier explicite : on devine la cible d'après son nom
  case "$1" in
    *speech*|*voice*|*synced*) check "$1" -22 -18 -5 -1 "voix : loudnorm OK ?" ;;
    *soundtrack*|*music*|*sfx*) check "$1" -35 -20 -12 -3 "bande-son sur disque (la compo l'atténue ensuite de moitié)" ;;
    *final*|*render*|*draft*)   check "$1" -20 -13  -3  0  "mix final" ;;
    *)                          check "$1" -99   0 -99  0  "informatif" ;;
  esac
else
  check sources/speech_orig_loud.mp4 -22 -18 -5 -1 "loudnorm échoué si mean ≈ -37"
  check speech.mp4                   -22 -18 -5 -1 "le splice a lu le mauvais fichier si mean ≈ -37"
  check sfx/soundtrack-final.m4a      -35 -20 -12 -3 "bande-son sur disque, avant l'atténuation data-volume 0.50"
  check renders/final.mp4             -20 -13  -3  0  "mix final"
fi

# Parité des durées A/V sur speech.mp4 : un écart > 0,02 s = splice qui dérive
if [ -f speech.mp4 ]; then
  echo
  echo "═══ Durées A/V de speech.mp4 (écart toléré : 0,02 s) ═══"
  ffprobe -v error -show_entries stream=codec_type,duration \
    -of csv=p=0 speech.mp4 | awk -F, '
      $1=="video"{v=$2} $1=="audio"{a=$2}
      END{
        d = (v>a ? v-a : a-v);
        printf "  video %.3fs   audio %.3fs   écart %.3fs   %s\n", v, a, d,
               (d<=0.02 ? "✓" : "✗ le splice dérive : video_end doit valoir audio_end + pad_dur");
      }'
fi
