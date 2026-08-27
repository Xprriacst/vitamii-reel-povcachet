# JJ_20260706_IMD_POVCACHET_V1 — plan de production

Brief : https://vitamii-studio.vitamii.workers.dev/b/b_1783325186173?t=F5nzh3XTaVRQAirWe0dLR-8pnss5YJ73gPJ1E7sOnlQ
Concept « POV chien — cachet vs friandise » · style clay Wallace & Gromit · **chien = cocker anglais**
(décision post-brief, le storyboard dit encore « bouledogue ») · livrables **9:16 + 4:5** · IA.
Référence : pub Wuffes (refs/inspiration-wuffes.mp4 — 16 plans/38 s, coupe médiane 2,5 s, mean −16,6 dB).

## Contraintes impératives du brief

1. Grattage **pattes arrières** uniquement (jamais avant)
2. Personnages/décors **identiques** sur toute la vidéo (planche 360 si besoin)
3. B-rolls **sans texte, sans VO, sans SFX** (tout au montage)
4. Pot = réplique exacte du vrai (taille + étiquette) en version clay
   (réf : refs/exemple-plan16-pot-main.mp4 = photo du vrai pot, refs/exemple-plan12-pot.mp4 = étiquette)
5. Friandise en cœur, taille moyenne
6. Cachet oblong blanc type Doliprane

## VO (sources/vo-povcachet.mp3 — 48,8 s, transcript-vo.json)

La VO suit fidèlement le storyboard (contrairement à la POVIA). Corrections captions :
`grattejais→grattages · vitamis→Vitamii · salto→saltos · cachets à cachet→cachets à cacher ·
Dix→10 · quatrevingtdix→90 · anti démangeaison→anti-démangeaisons`.
Captions : **phrases entières** (CDC août 2026), style 2 charte (capsules safran, capsule jaune produit).

## Beat map (frontières = milieux des gaps RMS, detect-silences sur la VO)

| Plan | Slot (s) | VO | Statut b-roll |
|---|---|---|---|
| 1 | 0.00–1.44 | Voici comment mes grattages | générer (cocker se gratte patte arrière, zones rouges) |
| 2 | 1.44–5.04 | et mon côté difficile à table… | générer (mains proposent fromage/friandises/beurre) |
| 3 | 5.04–6.53 | pour apaiser mes démangeaisons | générer (push-in cocker apaisé, rougeurs s'estompent) |
| 4 | 6.53–10.34 | Chaque matin, maman galérait… | **RECYCLÉ** : brolls/broll_maman-cachet-dans-fromage_3s_muet_clipA.mp4 (3,0 s → ralenti ≤15 % ou punch-in) |
| 5 | 10.34–12.54 | Elle le cachait dans un morceau de fromage | générer (macro fromage, cachet radiographie contour bleu) |
| 6 | 12.54–13.67 | ou du beurre de cacahuète | **RECYCLÉ (à re-DL)** : broll_maman-cachet-dans-beurre-cacahuete_3s_muet_clipB.mp4 — gdown rate-limited, id 1t02uP_fuoX2VZs6jNtRQngbDz6M5YFEz |
| 7 | 13.67–15.89 | mais je suis bien trop difficile pour ça | générer (cocker secoue la tête, refus) |
| 8 | 15.89–17.42 | Je mangeais le fromage | générer (mâche puis recrache le cachet) + MD « recrache » + SFX ptoo |
| 9 | 17.42–19.22 | et je recrachais le cachet par terre | générer (cachet mouillé au sol damier) |
| 10 | 19.22–21.60 | Je mettais un de ces bazars | générer (regard coupable en coin) |
| 11 | 21.60–24.89 | 10 minutes chaque jour… | générer (maman épuisée, main levée) + MD aiguilles + SFX tic-tac |
| 12 | 24.89–27.68 | Et puis elle a ramené les friandises Vitamii | générer (colis ouvert, pot bien visible) |
| 13 | 27.68–30.00 | Maintenant je fais carrément des saltos | générer (cocker saute/salto, cf. Wuffes 26,5 s) + SFX boing/whoosh |
| 14 | 30.00–31.64 | Elles ont un goût délicieux | générer (pot ouvert en main + friandise cœur tendue) + MD gobe + SFX gnam |
| 15 | 31.64–33.52 | alors je les engloutis direct | générer (cocker engloutit la friandise) |
| 16 | 33.52–37.80 | En plus, maman adore : 12 actifs validés par des vétérinaires | générer (maman tient le pot type photo réelle, plan posé) — **les 12 pops d'ingrédients = HyperFrames au montage** |
| 17 | 37.80–39.48 | Fini les cachets à cacher | générer (cocker mange à sa gamelle — complément pendant/après repas) |
| 18 | 39.48–41.19 | fini le sol en bazar | générer (sol propre, cocker près de la gamelle) |
| 19 | 41.19–42.33 | Un chien heureux | générer (parc lever de soleil, banc, cocker trotte) |
| 20 | 42.33–45.60 | et une routine anti-démangeaisons en 2 secondes chrono | générer (même parc, elle s'agenouille, câlin) |
| 21 | 45.60–48.81+ | Vous ne risquez rien. Offrez-lui la cure de 90 jours. | générer (elle se relève, pouce levé) + badge « Cure 90 jours · Efficacité ou remboursé » (HyperFrames, style clay, ≤24 chars sur r=92) |

Bilan : **2 recyclés / 19 à générer** + planche 360 cocker + réplique pot clay.

## Univers canon (à verrouiller avant génération)

- **Décor cuisine** : cottage W&G de clipA — murs chaux crème, étagères terre cuite,
  casseroles cuivre, sol damier crème/noir. ⚠️ Deux autres clips de la même série
  (debout-donne-cachet, jeune-desespere-soupir) partagent maman + décor mais montrent un
  **bouledogue** → régénérer même cadrage avec le cocker.
- **Maman** : brune, chignon lâche, cardigan tricot beige, jupe brune (canon = clipA).
  ⚠️ broll_maman-cachets-bouledogue_refus_v1 = une **grand-mère** ≠ persona, hors canon.
- **Cocker anglais** : à créer (planche 360 : face/profil/¾, assis/debout/couché, expressions
  gratté-refus-joie). Robe dorée, oreilles longues ondulées, collier rouge.
  Réf. geste patte arrière : brolls/P02_grattage-patte-arriere.mp4 (style 3D lisse ≠ clay, geste OK).
- **Pot** : réplique clay du vrai (photo dos réel + étiquette « Vitamii / IMMUNITÉ &
  ANTI-DÉMANGEAISONS » bandeau vert, photo chien).
- **Parc** (plans 19-21) : lever de soleil, banc — générer un still décor d'abord.
- Hors style (ne pas recycler tels quels) : cockers_bisou_* (Pixar glossy), chien-saute-friandise
  (feutrine), cleanup-crew_03 / main-dans-pot (3D lisse), main-pose-coeur (feutrine),
  broll_pot-pouf (mascotte 3D). cleanup-crew_07 (cadre feuilles + cœur + ingrédients) = seul
  candidat insert plan 16, à faire valider, sinon régénérer l'idée en clay.

## Workflow consistance (contrainte 2)

1. Stills de référence : planche 360 cocker + pot clay + décor parc → validation client
2. Image-to-video (Kling/Veo/Kie) : start frame issue des stills + prompt d'action
3. Tout générer en 9:16, **action centrée dans la zone 4:5** (le 4:5 se dérive au montage
   par re-rendu HyperFrames 1080×1350, pas par crop des captions)

## Audio / montage (rappels mesurés)

- VO avant rendu : `loudnorm=I=-14:TP=-1.2` · master post-rendu `volume=2.5dB,alimiter=0.891`
- Musique fournie : assets/musique-wiggle.mp3 — faire le sweep volumedetect avant de choisir
  MUSIC_START_SEC (règle 7) · lit musical p10 ≈ −19/−20 dB sous la voix
- Transitions : light-leak / whip-zoom — recettes `head_fx()` dans
  `../JJ_20260616_IMD_POVIA_V1/scripts/build-broll.sh`
- Découpe b-roll par frames exactes (`round(end×fps)−round(start×fps)`, réf. 10 du skill)

## Génération Higgsfield (MCP connecté le 26/08)

- Refs uploadées : clipA `523559ee…`, étiquette `aa779705…`, photo pot `0edf559c…`
- Stills validés à faire approuver (nano_banana_pro, 2 cr/img) : cocker 360 `b134653b…`,
  pot clay `ae396ec9…`, parc `1348eae7…` (fichiers : `work/stills/`)
- Start frame plan 1 : `0d1c705c…` · pilote vidéo plan 1 (veo3_1_lite 4 s 720p, 4 cr) :
  `da731102…` → `brolls-gen/plan01_hook_gratte_veo-lite_v1.mp4`. Cohérence OK ;
  réserve : le geste dérive vers « patte avant » en fin de clip — les 2 premières
  secondes suffisent (slot 1 = 1,4 s).
- Coûts mesurés par clip 9:16 : veo3_1_lite 4 s = 4 cr · kling3_0_turbo 5 s = 7,5 cr ·
  seedance_2_0_mini = 12,5 cr · seedance_2_5 = 32,5 cr. Workflow par plan :
  start frame nano banana (2 cr, refs = planche cocker + cuisine/pot/parc) → i2v.
- Solde après pilote : 98 crédits (plan Plus). Run complet restant ≈ 100-108 cr en
  veo lite → prévoir petite recharge ou mutualiser les start frames (parc 19-21).

### Run complet du 26/08 (terminé — solde final 0 crédit)

Tous les b-rolls sont dans `brolls-gen/` (720p 24fps 4 s, veo3_1_lite), start frames 2K
dans `work/stills/sf-*.png`, planches QC dans `work/qc/`. Mutualisations : sf-P1→P3,
sf-P7→P10, sf-P17→P18, sf-parc→P19/20/21. clipB beurre-cacahuète re-téléchargé ✓ (plan 6).
P9 = still seul (`sf-p09.png`) → Ken Burns zoompan au montage. P16 : garder la **v2**.

QC à l'attention du montage :
- plan03 : les rougeurs ne s'estompent pas (elles persistent) — slot court 1,5 s,
  prendre la fin du clip (yeux fermés, apaisé) et/ou fake du fade en HyperFrames.
- plan05 : halo bleu devient orageux après ~2 s — slot 2,2 s, garder le début.
- plan13 : salto ok sur ~2 premières secondes, ensuite le chien reste debout sur
  2 pattes — slot 2,3 s, trim.
- plan17 : la gamelle est sur le plan de travail (pas au sol) — slot 1,7 s serré, passable ;
  plan18 : prendre la 2ᵉ moitié (chien assis au sol près de la gamelle propre + pot).
- plan01 (pilote) : patte arrière nette sur les 2 premières secondes (slot 1,4 s ✓).

## Montage (26/08, terminé)

- Livrables : `renders/JJ_20260706_IMD_POVCACHET_V1_9x16.mp4` (1080×1920, 51,5 s, −15,0/−0,8 dB)
  et `renders/JJ_20260706_IMD_POVCACHET_V1_4x5.mp4` (1080×1350, crop y=285 du master).
- `broll.mp4` 51,500 s exact (22 slots, `segments-timing.json` + `scripts/build-broll-cachet.py`) ;
  frontière 03→04 déplacée à 7,30 s pour que clipA remplisse son slot sans stretch ;
  plan 16 en setpts ×1,067 ; light-leaks 12/19, whip-zooms 05/16.
- Compo `index.html` : captions phrases entières style 2 (capsules safran/céleri/jaune),
  glow céleri sur plan 3 (compense les rougeurs), horloge plan 11, cascade 12 chips
  d'actifs plan 16 (noms = étiquette réelle), badge « CURE 90 J / EFFICACITÉ OU REMBOURSÉ »
  plan 21, end card iris + CTA. Overlays à top ≥ 340 → survivent au crop 4:5 (285–1635).
- Audio : VO loudnorm −14 → rendu direct à −15,0 mean / −0,8 peak = dans la cible approuvée,
  **sans master post-rendu** (le +2,5 dB de la POVIA ne s'applique pas ici ; un essai
  volume=1dB+alimiter a clippé à 0 dB → abandonné). Musique wiggle à MUSIC_START_SEC=30.
- QC frames : grilles dans `work/qc-draft/` (safe zones 222/285/1632 vérifiées).
- **Fix v3 (retour Alexandre, ~40 s)** : toute la matière « gamelle » (plan17/18 + leurs
  start frames) montre le chien perché sur le plan de travail → slots remplacés sans
  re-génération : slot 17 = fin du plan 14 (maman donne la friandise à découvert),
  slots 18+19 = **un trot parc continu** (plan19 en deux tronçons, offset 0 puis 1,700 =
  raccord frame-à-frame), light-leak et whoosh avancés à 39,48/39,31 — même structure que
  la réf Wuffes (« no more messy floors » joué sur le parc). Les clips gamelle sont à
  re-générer plus tard si un vrai plan « repas » est exigé (prompt : gamelle AU SOL).

## État de la session du 26/08

Fait : projet monté depuis le template · VO téléchargée + transcrite (transcript-vo.json) ·
musique + inspiration + 3 exemples + badges téléchargés (refs/) · listing Drive complet
(refs/brolls-drive-listing.json, 314 fichiers) · 17 clips candidats audités (brolls/ +
planches work/audit/) · analyse Wuffes (work/ref/inspiration-wuffes/).
Bloquant : clipB beurre-cacahuète à re-télécharger · génération des 19 plans (outil de gen
côté Alexandre) · validation client de la planche 360.
