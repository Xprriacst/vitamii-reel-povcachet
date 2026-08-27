"""detect-silences.py — le catalogue des VRAIS silences. Source de vérité du décut.

Les timestamps d'un ASR ne servent PAS à décider les coupes : l'ASR transcrit les deux
essais d'un faux départ comme de la parole continue, sans détecter le silence entre les
deux. La vérité est dans l'énergie du signal.

Usage :
    python3 scripts/detect-silences.py [fichier] [seuil_dB] [durée_min_ms]
    python3 scripts/detect-silences.py                        # sources/speech_orig_loud.mp4
    python3 scripts/detect-silences.py speech.mp4 -50 80      # plus fin, pour traquer un
                                                              # faux départ dans un raccord

Lecture : un range de coupe COMMENCE juste après un silence et FINIT juste avant le
suivant — jamais au milieu d'un mot.
"""
import os
import subprocess
import sys

import numpy as np

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC = sys.argv[1] if len(sys.argv) > 1 else "sources/speech_orig_loud.mp4"
SILENCE_DB = float(sys.argv[2]) if len(sys.argv) > 2 else -45.0
MIN_SILENCE_MS = int(sys.argv[3]) if len(sys.argv) > 3 else 150
SR = 48000

if not os.path.exists(SRC):
    raise SystemExit(f"❌ {SRC} introuvable (lance prepare-cuts.sh, ou passe le fichier en argument)")

raw = subprocess.run(
    ["ffmpeg", "-y", "-i", SRC, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
    capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

win = int(SR * 0.030)
hop = int(SR * 0.010)
n = (len(audio) - win) // hop + 1
rms_db = np.array([20 * np.log10(np.sqrt(np.mean(audio[i*hop:i*hop+win] ** 2)) + 1e-9)
                   for i in range(n)])
rms_smooth = np.convolve(rms_db, np.ones(5) / 5, mode="same")
is_silent = rms_smooth < SILENCE_DB

print(f"═══ {SRC} — {len(audio)/SR:.2f}s — silences < {SILENCE_DB} dB, ≥ {MIN_SILENCE_MS} ms ═══")
print(f"{'début':>8}  {'fin':>8}  {'durée':>8}   lecture")

silences = []
i = 0
while i < len(is_silent):
    if is_silent[i]:
        j = i
        while j < len(is_silent) and is_silent[j]:
            j += 1
        dur_ms = (j - i) * 10
        if dur_ms >= MIN_SILENCE_MS:
            t0, t1 = i * hop / SR, j * hop / SR
            silences.append((t0, t1, dur_ms))
            # Une lecture indicative : ce que la durée suggère, à confirmer à l'oreille
            if dur_ms < 300:
                hint = "respiration"
            elif dur_ms < 900:
                hint = "fin de phrase"
            elif dur_ms < 2500:
                hint = "pause entre deux idées"
            else:
                hint = "grosse pause — souvent un faux départ juste avant ou après"
            print(f"{t0:8.3f}  {t1:8.3f}  {dur_ms:6d}ms   {hint}")
        i = j
    else:
        i += 1

if not silences:
    print("  (aucun silence détecté — seuil trop bas ? essaie -40)")
    raise SystemExit(0)

# Les ranges de parole = le complément des silences. C'est ce qu'on reporte dans le splice.
print()
print("═══ Ranges de parole (le complément) — base de départ pour splice-natural.sh ═══")
prev_end = 0.0
for t0, t1, _ in silences:
    if t0 - prev_end > 0.20:
        print(f"  [{prev_end:7.3f} → {t0:7.3f}]   {t0-prev_end:6.2f}s")
    prev_end = t1
total = len(audio) / SR
if total - prev_end > 0.20:
    print(f"  [{prev_end:7.3f} → {total:7.3f}]   {total-prev_end:6.2f}s")

print()
print("  Ces ranges incluent encore les faux départs : c'est à toi de choisir lequel")
print("  des deux essais garder. Les 4 patterns à traquer sont dans references/02.")
