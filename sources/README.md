# sources/ — les originaux, jamais référencés par la composition

| Fichier | Quoi |
|---|---|
| `source.mov` | le rush caméra brut (à déposer) |
| `mic.wav` | l'audio du micro externe brut, si séparé (à déposer) |
| `mic_trimmed.wav` | généré — micro recalé sur la vidéo |
| `synced.mov` | généré — vidéo + micro synchronisés |
| `speech_orig_loud.mp4` | généré — voix nettoyée. **C'est l'entrée du splice.** |

La composition ne référence que `speech.mp4` (à la racine), jamais un fichier de
`sources/`. Ce dossier est une archive : on peut tout regénérer depuis `source.mov`.

## Au tournage

- **Vertical 9:16** si possible. Sinon prévoir `scale=1080:1920` dans le splice.
- **Micro externe en WAV** : nettement meilleur que la piste embarquée de la caméra.
- **Un clap au début ET à la fin** de la prise : filet de secours si la synchro
  automatique échoue, et point de contrôle visuel gratuit.
- Ne pas couper l'enregistrement entre les prises : les silences inter-prises sont ce qui
  permet de faire respirer le montage **sans freeze frame**.
- Laisser tourner 2 secondes avant de parler et après avoir fini.

## Gros fichiers

`sources/` et `renders/` sont exclus de git (voir `.gitignore`) : ce sont des dizaines,
voire des centaines de Mo.
