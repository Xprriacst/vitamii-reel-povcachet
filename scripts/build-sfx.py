"""
build-sfx.py — mixe les SFX, calés au centième sur les cues d'animation de index.html.
Sortie : sfx/sfx-mix.wav, ensuite combiné à la musique par build-soundtrack-final.py.

Principe : chaque son ILLUSTRE ce qu'on voit au même instant (voir la table de cohérence
audio-visuel dans references/06-sound-design.md). Un whoosh posé au hasard s'entend comme
un habillage ; un son qui correspond à l'image devient invisible — et c'est le but.

Signature sonore par défaut : GRAVES + passe-bas systématique. C'est un choix esthétique,
motivé par le fait que les aigus piquent et sonnent cheap sur un haut-parleur de téléphone.
Si tu changes de signature, garde le ducking, les écarts de niveau, le mono et la reverb
courte — c'est ce qui fait tenir le mix.
"""
import os, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ >>> À ADAPTER À CHAQUE VIDÉO <<<                                          ║
# ║  • DURATION : durée exacte de speech.mp4 (= data-duration de index.html). ║
# ║  • Les CUES plus bas : re-mappe-les sur les temps de TON index.html.      ║
# ║    Chaque place(...) porte un commentaire « ce qu'on voit à cet instant » ║
# ║    — le tenir à jour, c'est ce qui rend le mix relisible dans un mois.    ║
# ║  • Viser 5 familles de sons minimum, sinon le mix devient monotone.       ║
# ║  • La librairie s'installe une fois :                                     ║
# ║        python3 scripts/scrape-sfx-library.py                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
SR = 48000
DURATION = 51.5           # durée de la composition (VO 48.80 + end card)
VOICE_FILE = "sources/vo-loud.m4a"
N = int(SR * DURATION)
LIB = "sfx/library"       # catalogue des sons : sfx/library/CATALOG.md

master = np.zeros(N, dtype=np.float32)

def load_mp3(path):
    raw = subprocess.run(
        ["ffmpeg","-y","-i",path,"-ac","1","-ar",str(SR),"-f","s16le","-"],
        capture_output=True, check=True
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def load(cat, fn): return load_mp3(os.path.join(LIB, cat, fn))
def lpf(sig, hz):
    sos = butter(4, hz/(SR/2), btype="low", output="sos")
    return sosfiltfilt(sos, sig).astype(np.float32)
def normalize(sig, target=0.85):
    p = float(np.max(np.abs(sig)))
    return sig * (target/p) if p > 0 else sig
def trim(sig, max_dur, fade_in=0.002, fade_out=0.10):
    n = int(SR * max_dur)
    out = sig[:n].copy() if len(sig) > n else sig.copy()
    if fade_in > 0:
        fi = int(SR * fade_in); out[:fi] *= np.linspace(0,1,fi)
    if fade_out > 0:
        fo = min(int(SR * fade_out), len(out)//4); out[-fo:] *= np.linspace(1,0,fo)
    return out
def place(sample, t, volume=1.0):
    start = int(t*SR); end = min(start + len(sample), N)
    if start >= N: return
    master[start:end] += sample[:end-start] * volume

# === Banks (graves + LPF) ===
paper_slide  = lpf(normalize(trim(load("paper","1530-paper-slide.mp3"), 0.9), 0.65), 3000)
paper_quick  = lpf(normalize(trim(load("paper","2380-paper-quick-movement.mp3"), 0.45), 0.60), 3000)
page_var_1   = lpf(normalize(trim(load("paper","1100-paper-magazine-paging.mp3"), 0.8), 0.50), 3500)
page_var_2   = lpf(normalize(trim(load("paper","1101-single-book-paging.mp3"), 0.8), 0.50), 3500)
sub_boom_400 = lpf(normalize(trim(load("boom","1694-short-explosion.mp3"), 0.7), 0.65), 400)
sub_boom_500 = lpf(normalize(trim(load("boom","1694-short-explosion.mp3"), 0.7), 0.65), 500)
sub_boom_350 = lpf(normalize(trim(load("boom","1694-short-explosion.mp3"), 0.9), 0.75), 350)
bass_hit_1500= lpf(normalize(trim(load("hit","2299-short-bass-hit.mp3"), 0.9), 0.75), 1500)
bass_hit_big = lpf(normalize(trim(load("hit","2299-short-bass-hit.mp3"), 1.1), 0.85), 1500)
wood_hit     = lpf(normalize(trim(load("impact","2182-wood-hard-hit.mp3"), 0.8), 0.85), 2500)
wood_med     = lpf(normalize(trim(load("impact","2182-wood-hard-hit.mp3"), 0.6), 0.75), 2000)
whoosh_fast  = lpf(normalize(trim(load("whoosh","1490-fast-whoosh-transition.mp3"), 0.5), 0.55), 2500)
attn_whoosh  = lpf(normalize(trim(load("whoosh","1486-cinematic-tunnel-reverb-woosh.mp3"), 1.0), 0.55), 2000)
bass_trans   = lpf(normalize(trim(load("transition","2295-pulsating-bass-transition.mp3"), 0.55), 0.60), 1500)
click_low    = lpf(normalize(trim(load("click","1117-classic-click.mp3"), 0.12), 0.50), 1000)
keyclick     = lpf(normalize(trim(load("keyboard","2533-single-key-type.mp3"), 0.16), 0.65), 2500)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ CUES — exemples couvrant les cas les plus fréquents.                      ║
# ║ Remplace-les par les tiens, aux temps de TON index.html.                  ║
# ║ Convention : le commentaire dit ce qu'on VOIT à cet instant.              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# POVCACHET — clay tendre et comique : tout feutré, la voix prime.

# --- Hook : petit appui sur la capsule « grattages » (0.62) ---
place(paper_quick,  0.62, volume=0.22)

# --- Whip-zoom vers la macro fromage-radio (10.34) ---
place(whoosh_fast,  10.20, volume=0.38)
place(bass_trans,   10.23, volume=0.26)

# --- Refus : secouement de tete (13.9) — leger bruit d'oreilles ---
place(paper_quick,  13.95, volume=0.24)
place(paper_quick,  14.35, volume=0.18)

# --- Recrache le cachet (~16.55 : le crachat) puis il atterrit au sol (17.45) ---
place(paper_quick,  16.55, volume=0.32)
place(sub_boom_500, 16.58, volume=0.18)
place(click_low,    17.45, volume=0.45)
place(wood_med,     17.47, volume=0.14)

# --- Horloge « 10 minutes » : pop (21.6) + tic-tac (keyclick alterne) ---
place(paper_slide,  21.58, volume=0.34)
for k in range(6):
    place(keyclick, 21.95 + k*0.48, volume=0.20 if k % 2 == 0 else 0.14)
place(paper_quick,  24.66, volume=0.18)   # sortie de l'horloge

# --- Light-leak bascule SOLUTION (24.89) puis pot sorti du colis (25.6) ---
place(attn_whoosh,  24.72, volume=0.30)
place(paper_slide,  25.55, volume=0.30)
place(sub_boom_500, 25.60, volume=0.16)

# --- Salto (27.75 envol · 28.9 atterrissage) ---
place(whoosh_fast,  27.75, volume=0.30)
place(sub_boom_350, 28.90, volume=0.34)

# --- Friandise prise (31.05) puis engloutie (32.25) ---
place(paper_quick,  31.05, volume=0.28)
place(sub_boom_500, 31.10, volume=0.18)
place(wood_med,     32.25, volume=0.22)

# --- Whip-zoom vers la presentation produit (33.52) ---
place(whoosh_fast,  33.38, volume=0.36)
place(bass_trans,   33.41, volume=0.24)

# --- 12 actifs : cascade de chips (33.95 + i*0.19), variantes alternees ---
for k in range(12):
    t = 33.95 + k*0.19
    smp = (paper_quick, page_var_1, page_var_2)[k % 3]
    place(smp, t, volume=0.20)
    if k % 3 == 0:
        place(sub_boom_500, t + 0.03, volume=0.10)

# --- Light-leak bascule PARC (41.19) ---
place(attn_whoosh,  39.31, volume=0.30)

# --- Badge « CURE 90 J » : slam (47.55) ---
place(wood_med,     47.55, volume=0.30)
place(sub_boom_400, 47.58, volume=0.26)

# --- End card : iris (49.15) puis pop du CTA (49.72) ---
place(attn_whoosh,  48.95, volume=0.42)
place(sub_boom_350, 49.17, volume=0.40)
place(paper_slide,  49.19, volume=0.40)
place(bass_hit_1500, 49.74, volume=0.24)

# === DUCKING via voice envelope ===
voice_raw = subprocess.run(
    ["ffmpeg","-y","-i",VOICE_FILE,"-ac","1","-ar",str(SR),"-f","s16le","-"],
    capture_output=True, check=True
).stdout
voice = np.frombuffer(voice_raw, dtype=np.int16).astype(np.float32)/32768.0
if len(voice) < N:
    voice = np.concatenate([voice, np.zeros(N-len(voice), dtype=np.float32)])
else:
    voice = voice[:N]

win_s = int(SR*0.030)
kernel = np.ones(win_s, dtype=np.float32)/win_s
voice_env = np.convolve(np.abs(voice), kernel, mode="same").astype(np.float32)
peak_env = float(np.max(voice_env))
if peak_env > 0: voice_env = voice_env / peak_env
attack_n = int(SR*0.040)
attack_k = np.ones(attack_n, dtype=np.float32)/attack_n
voice_env = np.convolve(voice_env, attack_k, mode="same")

# Ducking des SFX sous la voix : attaque rapide (ils s'écartent dès le premier phonème),
# release lente (300 ms, ils reviennent sans qu'on le remarque). La musique est duckée
# plus fort — 0.90 — dans build-soundtrack-final.py.
DUCK_DEPTH = 0.55
duck = 1.0 - DUCK_DEPTH * voice_env
release_alpha = 1.0 - np.exp(-1.0/(SR*0.300))
for i in range(1, len(duck)):
    if duck[i] > duck[i-1]:
        duck[i] = duck[i-1] + release_alpha*(duck[i]-duck[i-1])

master = master * duck

peak = float(np.max(np.abs(master)))
if peak > 0:
    master = master * (0.50/peak)

out = (master*32767).astype(np.int16)
wavfile.write("sfx/sfx-mix.wav", SR, out)
print(f"Wrote sfx/sfx-mix.wav — duration={DURATION}s, peak={float(np.max(np.abs(master))):.3f}")
