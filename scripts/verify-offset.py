"""verify-offset.py — offset micro ↔ caméra par CONSENSUS de fenêtres. PORTE A.

Pourquoi pas une simple cross-corrélation globale : un rush contient presque toujours des
prises répétées (faux départs, CTA en double). La corrélation globale peut se verrouiller
sur la MAUVAISE copie du contenu répété — pic fort, cohérent entre les méthodes, donc
trompeur. Deux exemples mesurés : 3,04 s annoncés au lieu de 4,33 s ; 0,92 s au lieu de
5,41 s — ce dernier sur un rush d'une seule prise continue, il suffit que le contenu soit
répétitif pour créer un pic secondaire.

Méthode : découper la caméra en fenêtres de 5 s à fort RMS, corréler chacune contre le
micro complet, prendre la MÉDIANE des offsets locaux. Les fenêtres doivent s'accorder à
±20 ms avec un peak_ratio > 2.

Usage :
    python3 scripts/verify-offset.py sources/source.mov sources/mic.wav

Sortie machine (utilisée par prepare-cuts.sh) :
    CONSENSUS_OFFSET=<secondes à trimmer dans le micro>
    CONSENSUS_AGREE=<n/total>
"""
import subprocess
import sys

import numpy as np

SR = 48000
WIN_S = 5        # longueur d'une fenêtre de test
STEP_S = 8       # pas entre deux fenêtres
AGREE_TOL = 0.02  # 20 ms


def decode_pcm(path):
    raw = subprocess.run(
        ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def xcorr_best(mic_sig, cam_win):
    """Retourne (offset_s, corrélation, ratio pic principal / 2e pic)."""
    m = mic_sig - mic_sig.mean()
    c = cam_win - cam_win.mean()
    m = m / (np.abs(m).max() + 1e-9)
    c = c / (np.abs(c).max() + 1e-9)
    N = 1 << (len(m) + len(c) - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(m, N) * np.conj(np.fft.rfft(c, N)), N)
    lim = len(m) - len(c)
    if lim <= 0:
        raise SystemExit("❌ le micro est plus court que la fenêtre de test")
    k = int(np.argmax(corr[:lim]))
    guard = int(0.05 * SR)                      # ignorer le voisinage immédiat du pic
    masked = corr[:lim].copy()
    masked[max(0, k - guard):k + guard] = -1e9
    k2 = int(np.argmax(masked))
    return k / SR, float(corr[k]), float(corr[k] / max(corr[k2], 1e-9))


cam_path = sys.argv[1] if len(sys.argv) > 1 else "sources/source.mov"
mic_path = sys.argv[2] if len(sys.argv) > 2 else "sources/mic.wav"

cam = decode_pcm(cam_path)
mic = decode_pcm(mic_path)
print(f"caméra : {len(cam)/SR:7.2f}s   micro : {len(mic)/SR:7.2f}s")
print(f"{'fenêtre caméra':>18}  {'rms':>7}  {'offset':>10}  {'ratio':>6}")

results = []
for t in range(3, max(int(len(cam) / SR) - WIN_S - 1, 4), STEP_S):
    w = cam[t*SR:(t+WIN_S)*SR]
    if len(w) < WIN_S * SR // 2:
        break
    rms = float(np.sqrt(np.mean(w ** 2)))
    if rms < 0.01:
        print(f"  cam[{t:4d}:{t+WIN_S:4d}]  {rms:7.4f}   (silence, ignorée)")
        continue
    o, _, ratio = xcorr_best(mic, w)
    off = o - t
    results.append((t, off, ratio))
    flag = "" if ratio > 2.0 else "  ⚠️ pic peu marqué"
    print(f"  cam[{t:4d}:{t+WIN_S:4d}]  {rms:7.4f}  {off:+10.4f}s  {ratio:6.2f}{flag}")

if not results:
    raise SystemExit("❌ aucune fenêtre exploitable (audio caméra trop faible ?)")

offs = np.array([r[1] for r in results])
med = float(np.median(offs))
agree = offs[np.abs(offs - med) < AGREE_TOL]
ratio_pct = len(agree) / len(offs)

print()
print(f"MÉDIANE = {med:+.4f}s   consensus {len(agree)}/{len(offs)} fenêtres à ±20 ms "
      f"({ratio_pct*100:.0f} %)")
print(f"écart-type des fenêtres en consensus : {np.std(agree)*1000:.1f} ms")
print()

if ratio_pct >= 0.8:
    print("✓ PORTE A franchie — offset fiable.")
elif ratio_pct >= 0.5:
    print("⚠️  PORTE A limite : la moitié des fenêtres seulement s'accordent.")
    print("   Vérifie à la main (un clap au début/fin de prise) avant de merger,")
    print("   et contrôle impérativement le lag résiduel après le merge.")
else:
    print("❌ PORTE A échouée : pas de consensus. Ne pas merger tel quel.")
    print("   Causes fréquentes : audio caméra saturé ou muet, deux prises différentes,")
    print("   ou une horloge qui dérive (offsets qui augmentent régulièrement ci-dessus).")

# Lignes machine (parsées par prepare-cuts.sh)
print(f"CONSENSUS_OFFSET={med:.4f}")
print(f"CONSENSUS_AGREE={len(agree)}/{len(offs)}")
