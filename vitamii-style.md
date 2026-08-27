# Kit de marque Vitamii — bible de style mesurée

Source : brand book 2024 + **mesures sur les 2 vidéos approuvées cliente** (Frame.io,
`JJ_20260616_IMD_POVIA_V1` 26/06 et `JJ_20260616_IMD_MECANISME_V1` 15/07 — analyses
et transcriptions dans `refs-approuvees/`). À copier/adapter au démarrage de chaque
nouvelle vidéo Vitamii, avec le `design.md` du projet.

## Couleurs (charte)

| Token | Hex | Usage |
|---|---|---|
| vert forêt | `#112B1E` | fonds sombres, end card, contours, scrim |
| blanc écru | `#FEFBED` | texte sur sombre, captions |
| orange safran | `#ED6A44` | capsules mots importants, badge garantie |
| jaune soleil | `#FFC747` | capsule nom produit / CTA (jaune = produits chien) |
| vert céleri | `#D5E6AD` | chips numérotées, badges doux, pictos |

Interdits : logo incliné/déformé/ombré · logo entier sur fond orange · clair sur clair.

## Typos

- Titres / display : **Hiragino Sans** (système macOS, W7-W8)
- Captions / UI : **Albert Sans** (`assets/AlbertSans*.ttf`, variable) — captions 600, 46 px/1080

## Captions — deux styles validés cliente

1. *POVIA approuvée* : mot-à-mot centré à ~60-65 % de hauteur, blanc gras contour
   sombre, **mots-clés jaune soleil en gros**.
2. *MECANISME approuvée + notre V2* : blanc gras + **capsules orange safran** (rotation
   −2°), chips céleri pour les numéros, capsule jaune pour le nom du produit.

⚠️ Depuis le CDC d'août 2026 : **phrases entières obligatoires** (public âgé, pas de
mot-à-mot). Le style 2 est le plus compatible charte.

## Langage de transition (mesuré sur la POVIA approuvée)

- **Light-leak** : flash chaud ~250 ms sur le plan entrant (expo +0,34 · saturation
  +20 % · rouges +22 % / bleus −12 %, décroissance exp τ=0,085 s)
- **Whip-zoom** : zoom 1,35→1,0 (exp, ~10 frames) + flou dégressif 13→6→2,5 par paliers
  de 80 ms — utilisé pour entrer/sortir du « monde intérieur » (ventre, cerveau)
- Recettes ffmpeg prêtes : `head_fx()` dans `JJ_20260616_IMD_POVIA_V1/scripts/build-broll.sh`
- Fondu noir intégré au plan « friandise zoom » pour la bascule produit · iris vert
  forêt pour l'end card

## Cibles audio (mesurées)

| Mesure | Cible |
|---|---|
| Loudness mix final | mean −14 à −16 dB · peak −0,5 dB (master : `volume=2.5dB,alimiter=0.891` après rendu) |
| VO source avant rendu HyperFrames | `loudnorm=I=-14:TP=-1.2` (le mixeur du moteur atténue ~3 dB) |
| **Lit musical dans les respirations** | **p10 RMS ≈ −19 à −20 dB** (POVIA approuvée) |
| SFX | feutrés, graves, passe-bas — pops capsules 0,3 · whooshs transitions 0,3-0,4 |

## Cadence

Médiane approuvée : **3,6-3,9 s/plan** (min ~0,6, max ~10). Notre V2 : 2,9 s — ok CDC
(« coupes dynamiques »). B-rolls IA : border collie constant, intérieurs cosy chaleureux ;
le MECANISME mélange aussi des rushes réels (mains, produit, extérieur).

## Structure narrative validée (2 angles)

- **POV chien « je »** : hook question → 3 signes → intestin déséquilibré → 2ᵉ cerveau →
  réassurance → produit → bénéfices → appétence → CTA
- **Mécanisme « vous »** : que se passe-t-il dans son corps → rééquilibrage → bénéfices
  observables → preuve sociale → CTA
- La V2 (VO 07/02) ajoute : signes numérotés 1/2/3, « 12 actifs choisis par des
  vétérinaires », **garantie 3 mois sinon remboursé** en CTA.

## Assets du kit

`assets/` : logo détouré (transparent + sur vert), Albert Sans variable.
Badges circulaires (« Approuvé par les vétérinaires », « Satisfait ou remboursé · 3 mois »),
pills bénéfices et end card : blocs SVG/CSS réutilisables dans
`JJ_20260616_IMD_POVIA_V1/index.html` (⚠️ texte circulaire : ~24 caractères max sur r=92/viewBox 250).
