"""Adaptateur ASR → format canonique du pipeline.

Le pipeline attend `transcript-words.json` = une liste PLATE d'objets
`{"text": str, "start": float, "end": float}`, un par mot, triée par temps.

Ce script convertit vers ce format les sorties des ASR les plus courants, sans
avoir à connaître leur schéma :

  - faster-whisper / WhisperX / openai-whisper :  {"segments":[{"words":[{word,start,end}]}]}
  - whisper.cpp --output-json-full            :  {"transcription":[{"text","offsets":{from,to}}]}
  - Qwen3-ASR (ce pipeline)                    :  {"segments":[{"text","start","end"}]}
  - déjà au bon format                         :  [{"text","start","end"}]

Usage :
    python3 scripts/asr-to-words.py <sortie-asr.json> [transcript-words.json]

Vérifie aussi la cohérence (timestamps croissants, pas de durée nulle) et le signale :
un transcript incohérent produit des captions qui sautent, et on cherche le bug ailleurs.
"""
import json
import os
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC = sys.argv[1] if len(sys.argv) > 1 else "asr-output.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "transcript-words.json"


def norm(text, start, end):
    return {"text": str(text).strip(), "start": round(float(start), 3), "end": round(float(end), 3)}


def extract(data):
    """Renvoie (words, format_détecté)."""
    # 1. déjà une liste plate
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        return [norm(w["text"], w["start"], w["end"]) for w in data if w.get("text")], "liste plate"

    if not isinstance(data, dict):
        raise SystemExit(f"❌ Format non reconnu (racine {type(data).__name__}).")

    # 2. whisper.cpp : offsets en millisecondes
    if "transcription" in data:
        words = []
        for seg in data["transcription"]:
            off = seg.get("offsets") or {}
            if "from" in off and "to" in off and seg.get("text", "").strip():
                words.append(norm(seg["text"], off["from"] / 1000.0, off["to"] / 1000.0))
        return words, "whisper.cpp"

    # 3. segments[] — soit avec words[] imbriqués (whisper-like), soit un mot par segment (Qwen3)
    if "segments" in data:
        words, nested = [], False
        for seg in data["segments"]:
            sub = seg.get("words")
            if sub:
                nested = True
                for w in sub:
                    txt = w.get("word", w.get("text", ""))
                    if txt.strip() and w.get("start") is not None and w.get("end") is not None:
                        words.append(norm(txt, w["start"], w["end"]))
            elif seg.get("text", "").strip() and seg.get("start") is not None:
                words.append(norm(seg["text"], seg["start"], seg["end"]))
        return words, "segments[].words[]" if nested else "un mot par segment"

    # 4. words[] à la racine
    if "words" in data:
        return [norm(w.get("word", w.get("text", "")), w["start"], w["end"])
                for w in data["words"] if (w.get("word") or w.get("text", "")).strip()], "words[] racine"

    raise SystemExit("❌ Aucune clé connue (transcription / segments / words).")


with open(SRC) as f:
    words, fmt = extract(json.load(f))

if not words:
    raise SystemExit(f"❌ 0 mot extrait de {SRC} (format détecté : {fmt}).")

words.sort(key=lambda w: w["start"])

# Contrôles de cohérence — un transcript bancal se paie plus tard, en captions qui sautent
zero = sum(1 for w in words if w["end"] <= w["start"])
overlap = sum(1 for a, b in zip(words, words[1:]) if b["start"] < a["end"] - 0.001)
gap_max = max((b["start"] - a["end"] for a, b in zip(words, words[1:])), default=0.0)

with open(OUT, "w") as f:
    json.dump(words, f, ensure_ascii=False, indent=1)

print(f"✓ {OUT} — {len(words)} mots  (format source : {fmt})")
print(f"  durée couverte : {words[0]['start']:.2f}s → {words[-1]['end']:.2f}s")
print(f"  plus grand blanc entre deux mots : {gap_max:.2f}s")
if zero:
    print(f"  ⚠️  {zero} mot(s) de durée nulle — l'ASR n'a pas produit de vrais timestamps mot ; "
          f"vérifie que l'option word-level est bien activée")
if overlap:
    print(f"  ⚠️  {overlap} chevauchement(s) de timestamps — tolérable en petit nombre, "
          f"suspect au-delà de ~5 % des mots")
print("\n  Prochaine étape : node scripts/build-captions.mjs")
