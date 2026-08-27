# fonts/

Le template tourne avec les polices du système, pour marcher sans aucun asset. Pour poser
ta charte, dépose ici deux familles en **`.woff2`** et déclare-les dans `index.html`.

## Ce qu'il faut

| Rôle | À quoi ça sert | Ce qui marche |
|---|---|---|
| **display** | chiffres, mots-pivots, gros nombres | un serif à fort contraste, ou un sans très gras |
| **interface** | captions, labels, kickers | un sans-serif lisible en 600, avec des chiffres tabulaires |

Deux familles suffisent. Trois commencent à se disputer l'attention.

## Déclaration

```css
@font-face {
  font-family: "MaDisplay";
  font-weight: 400;
  src: url("fonts/ma-display-400.woff2") format("woff2");
  font-display: block;   /* block, pas swap : au rendu on ne veut aucun reflow */
}
@font-face {
  font-family: "MonUI";
  font-weight: 600;
  src: url("fonts/mon-ui-600.woff2") format("woff2");
  font-display: block;
}
```

Puis dans `:root` :

```css
--font-display: "MaDisplay", Georgia, serif;
--font-ui: "MonUI", system-ui, sans-serif;
```

## Pourquoi des fichiers locaux

Le rendu se fait dans un navigateur headless : une police chargée depuis un CDN peut
arriver après la première frame et produire un flash de texte non stylé, ou ne pas
arriver du tout. Les `.woff2` locaux sont déterministes.

## Où en trouver

Google Fonts (licence OFL, `.woff2` téléchargeables via un service de conversion, ou
`google-webfonts-helper`), Fontsource, ou les fonderies indépendantes pour un rendu plus
personnel. Vérifier que la licence couvre l'**embarquement dans une vidéo diffusée**.
