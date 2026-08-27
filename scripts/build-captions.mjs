// build-captions.mjs — transcript-words.json → captions.js
//
// ╔══════════════════════════════════════════════════════════════════════════╗
// ║ >>> À ADAPTER À CHAQUE VIDÉO — les 4 listes ci-dessous, et elles seules. ║
// ║  • PAIR_MERGES  : fusionner 2 tokens ASR en 1 ("pour"+"cent" → "%").     ║
// ║  • PIVOT_TERMS  : mots mis en avant (italique + accent). ≤ 7 LETTRES :   ║
// ║    au-delà, l'inclinaison italique n'est jamais visuellement centrée.    ║
// ║  • TEXT_FIX     : corrections des erreurs d'ASR propres à ce rush.       ║
// ║  • PROPER_NOUNS : les SEULS mots capitalisés. Tout le reste en minuscule.║
// ║                                                                          ║
// ║ Lire le transcript UNE fois et remplir les 4 listes d'un coup : 5 min,   ║
// ║ et ça évite des corrections visibles après le rendu.                     ║
// ╚══════════════════════════════════════════════════════════════════════════╝
//
// Réglages stables (ne pas toucher sans raison) : MAX_WORDS=3, PAUSE_BREAK=0.28,
// lead -0.18s, tail +0.22s, 1 pivot max par groupe. Voir references/03.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
process.chdir(resolve(dirname(fileURLToPath(import.meta.url)), ".."));

let transcript = JSON.parse(readFileSync("transcript-words.json", "utf8"));

const PAIR_MERGES = [
  // Exemples — remplace par les fusions utiles à TON script :
  { a: "pour", b: "cent", out: "%" },        // "quatre-vingts pour cent" → "80 %"
  // { a: "cinquante", b: "mille", out: "50k" },
  // { a: "en", b: "tout", out: "en dessous" },   // corriger une méprise d'ASR sur 2 mots
];
const merged = [];
for (let i = 0; i < transcript.length; i++) {
  const w = transcript[i];
  const nx = transcript[i + 1];
  let didMerge = false;
  if (nx) {
    for (const m of PAIR_MERGES) {
      if (w.text === m.a && nx.text === m.b) {
        merged.push({ text: m.out, start: w.start, end: nx.end });
        i++; didMerge = true; break;
      }
    }
  }
  if (!didMerge) merged.push(w);
}
transcript = merged;

// Mots-pivots : ≤ 7 lettres, ou noms propres courts. Un seul sera retenu par groupe.
const PIVOT_TERMS = new Set([
  // les mots-clés qui portent les idées de TA vidéo, ex :
  // "gratuit", "75", "mémoire", "claude", "2 ans",
]);

const norm = (s) =>
  s.toLowerCase().replace(/[.,!?;:«»"']+$/g, "").replace(/^[«»"']+/g, "");

const TEXT_FIX = {
  // corrections d'ASR quasi universelles
  "cloud": "Claude",           // l'ASR entend systématiquement "Cloud"
  "github": "GitHub",
  "api": "API",
  "ia": "IA",
  // + les erreurs propres à TON rush (accent, vocabulaire métier, noms de produits)
};

// Les SEULS mots capitalisés. Tout le reste passe en minuscules : avec 3 mots par
// groupe, capitaliser un "début de phrase" met une majuscule en plein milieu d'une
// phrase, ce qui se lit comme une faute. Ne jamais réintroduire isSentenceStart.
const PROPER_NOUNS = new Set([
  "claude", "github", "api", "ia", "ai", "mcp",
  "anthropic", "openai", "chatgpt", "gpt", "meta", "google", "facebook",
  "instagram", "linkedin", "tiktok", "youtube", "n8n",
  // + les marques et noms propres de TA vidéo
]);

function applyCaseRules(text) {
  const trail = (text.match(/[.,!?;:«»]+$/) || [""])[0];
  const stripped = trail ? text.slice(0, -trail.length) : text;
  const lower = stripped.toLowerCase();
  if (TEXT_FIX[lower]) return TEXT_FIX[lower] + trail;
  if (PROPER_NOUNS.has(lower)) {
    return stripped.charAt(0).toUpperCase() + stripped.slice(1).toLowerCase() + trail;
  }
  return lower + trail;
}

// POSITIONAL_FIX : une correction valable seulement sur une plage de temps — utile
// pour les hallucinations de début de fichier, où l'ASR manque de contexte.
//   { before: 1.0, from: "claude", to: "code" }  → avant 1,0 s, "claude" devient "code"
const POSITIONAL_FIX = [];

const words = transcript.map((w) => {
  for (const f of POSITIONAL_FIX) {
    if (norm(w.text) === f.from &&
        (f.before === undefined || w.start < f.before) &&
        (f.after  === undefined || w.start > f.after)) {
      w = { ...w, text: f.to };
    }
  }
  const text = applyCaseRules(w.text);
  return {
    text,
    start: +w.start.toFixed(3),
    end: +w.end.toFixed(3),
    pivot: PIVOT_TERMS.has(norm(text)),
  };
});

function buildGroups(words) {
  const groups = [];
  let cur = [];
  const MAX_WORDS = 3;
  const PAUSE_BREAK = 0.28;

  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    if (cur.length === 0) { cur.push(w); continue; }
    const prev = cur[cur.length - 1];
    const gap = w.start - prev.end;
    const prevEndsSentence = /[.!?]$/.test(prev.text);
    const shouldBreak = prevEndsSentence || gap > PAUSE_BREAK || cur.length >= MAX_WORDS;
    if (shouldBreak) { groups.push(cur); cur = [w]; }
    else { cur.push(w); }
  }
  if (cur.length) groups.push(cur);

  return groups.map((arr) => {
    let seenPivot = false;
    arr = arr.map((w) => {
      if (w.pivot && !seenPivot) { seenPivot = true; return w; }
      return { ...w, pivot: false };
    });
    const start = Math.max(0, arr[0].start - 0.18);
    const lastEnd = arr[arr.length - 1].end;
    return {
      start: +start.toFixed(3),
      end: +(lastEnd + 0.22).toFixed(3),
      words: arr.map((w) => ({ text: w.text, pivot: w.pivot })),
    };
  });
}

const groups = buildGroups(words);

for (let i = 0; i < groups.length - 1; i++) {
  const nextStart = groups[i + 1].start;
  if (groups[i].end > nextStart - 0.05) {
    groups[i].end = +(nextStart - 0.05).toFixed(3);
  }
}

writeFileSync(
  "captions.js",
  "// Auto-generated by build-captions.mjs — do not edit by hand.\n" +
    "window.CAPTIONS = " + JSON.stringify(groups, null, 2) + ";\n",
  "utf8",
);

console.log(`Generated ${groups.length} caption groups from ${words.length} words.`);
groups.forEach((g) =>
  console.log(`  [${g.start.toFixed(2)}-${g.end.toFixed(2)}] ${g.words.map((w) => w.text + (w.pivot ? "*" : "")).join(" ")}`),
);
console.log(`Total speech duration: ${words[words.length - 1].end.toFixed(2)}s`);
