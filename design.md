# design.md — [nom de la vidéo]

Le document de travail du montage. Il se remplit **avant** de coder `index.html`, et il
se relit après pour capitaliser. Deux parties : l'identité (stable d'une vidéo à l'autre)
et le plan visuel (propre à celle-ci).

---

## 1. Identité visuelle (à figer une fois, puis recopier)

| Token | Valeur | Usage |
|---|---|---|
| `--bg` | `#111111` | fond |
| `--text` | `#F2EDE5` | texte principal |
| `--accent` | `#F5B81E` | mot-pivot, accents, jauges |
| `--accent-2` | `#C88C10` | variante sombre du même accent, aplats |
| `--ok` / `--ko` | `#5DC75D` / `#E24B4A` | hausse / baisse, validé / refusé |

Ni blanc pur ni noir pur. **Un** accent (deux au maximum) : au-delà, plus rien ne
ressort.

**Polices** — une display (chiffres, mots-pivots) + une sans-serif (captions, labels).
Les déposer en `.woff2` dans `fonts/` et les déclarer dans `index.html`.

- display : …
- interface : … · captions en 600, 44 px

**Signature sonore** — … (par défaut : graves + passe-bas systématique, voir
`references/06-sound-design.md`)

**Format** — stage 45/55 · ou b-roll (inserts plein cadre) → *choisir avant le brainstorm*

---

## 2. Le propos

- **Sujet** : …
- **Ce qu'on veut que le spectateur retienne** (une phrase) : …
- **Durée cible** : … s
- **Découpage en scènes** : 1 idée par scène, jamais deux.

---

## 3. Plan visuel (étape 4.0 — à remplir AVANT de coder)

Pour chaque scène : 3 pistes, dont **au moins une jamais utilisée**. À pertinence et
visualité égales, c'est la nouvelle qui gagne — sinon la créativité s'auto-copie d'une
vidéo à l'autre.

Filtre à appliquer à chaque piste : **objet-héros + VERBE d'action + moment d'impact**.
Pas de verbe visuel (s'ouvre, s'arrache, décolle, s'emboîte, se froisse, s'imprime) →
piste rejetée.

| # | fenêtre | piste retenue | keyword → anim @ timestamp | innovation proposée · choix retenu (pourquoi) |
|---|---|---|---|---|
| 1 | 0,0–… | … | « … » → … @ … | *innovation* : … · *retenu* : … parce que … |
| 2 | | | | |
| 3 | | | | |

Les timestamps se lisent dans `transcript-words.json` — jamais estimés à l'oreille.

**Transitions marquées** (4 max, aux pivots narratifs) : … s, … s

---

## 4. Décut — trace des coupes

| Range gardé | Contenu | Pause après |
|---|---|---|
| 0,57 → 5,02 | … | 0,25 s |

**Viré** : … (blanc) · … (faux départ) · … (redite)

**Δ appliqués après coup** : … (si un passage a été retiré après la composition, noter
la valeur et ce qui a été décalé)

---

## 5. Son

- musique : `sfx/music/…`
- sweep d'énergie : plateau à … s, pic à … s → `MUSIC_START_SEC = …`
- fade-in : … s (0,5-0,8 si on entre dans l'énergie, 1,5 si intro calme)
- familles de SFX utilisées : … (viser 5 minimum)

---

## 6. Ce que cette vidéo a appris

À remplir à la fin. C'est ce qui fait progresser au lieu de répéter.

- ce qui a bien rendu : …
- ce qui a été refusé et pourquoi : …
- nouveau piège rencontré : … → à ajouter dans `references/08-anti-patterns.md`
- nouvel idiome visuel qui marche : … → à ajouter dans `references/04-methode-visuelle.md`
