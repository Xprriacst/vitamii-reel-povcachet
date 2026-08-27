"""
build-soundtrack-final.py — SFX + musique + ducking sur la voix → sfx/soundtrack-final.m4a

C'est ce fichier qui est branché dans la composition (la voix reste une piste séparée).
La musique et les SFX sont abaissés dynamiquement sous la voix : attaque rapide (ils
s'écartent dès le premier phonème), release lente (ils reviennent sans qu'on le remarque).

Niveaux de référence, calibrés pour du MOBILE à faible volume — plus fort que ce que
suggère une écoute au casque : musique peak -10 dB, SFX peak -7 dB, plafond master 0.62.
Voir references/06-sound-design.md.
"""
import os, subprocess
import numpy as np
from scipy.io import wavfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ >>> À ADAPTER À CHAQUE VIDÉO <<<                                          ║
# ║  • DURATION       : durée de speech.mp4 (= data-duration de index.html).  ║
# ║  • MUSIC_FILE     : la piste déposée dans sfx/music/.                     ║
# ║  • MUSIC_START_SEC: fais le SWEEP D'ÉNERGIE avant (references/06) et      ║
# ║    démarre sur le plateau (ou sur le pic si le morceau a un drop).        ║
# ║    NE JAMAIS compenser une intro calme par du gain.                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
SR = 48000
DURATION = 51.5                           # composition (VO 48.80 + end card)
N = int(SR * DURATION)
VOICE_FILE = "sources/vo-loud.m4a"
# musique du CDC : alex-morgan-documentary-nature — à déposer dans sources/musique/.
# Tant qu'elle manque, le script sort un soundtrack SFX seul (avertissement).
import glob as _glob
_music = sorted(_glob.glob("sources/musique/*.mp3") + _glob.glob("sources/musique/*.m4a")
                + _glob.glob("sources/musique/*.wav"))
MUSIC_FILE = _music[0] if _music else None
MUSIC_START_SEC = 30.0  # sweep du 26/08 : plateau stable -18 dB à partir de 30 s (pas d'intro calme)

def load_audio(path):
    raw = subprocess.run(
        ["ffmpeg","-y","-i",path,"-ac","1","-ar",str(SR),"-f","s16le","-"],
        capture_output=True, check=True
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def pad_to_n(arr):
    if len(arr) < N:
        return np.concatenate([arr, np.zeros(N-len(arr), dtype=np.float32)])
    return arr[:N]

sfx = pad_to_n(load_audio("sfx/sfx-mix.wav"))

if MUSIC_FILE is None:
    print("⚠️  PAS DE MUSIQUE dans sources/musique/ — soundtrack = SFX seuls.")
    music = np.zeros(N, dtype=np.float32)
else:
    music_full = load_audio(MUSIC_FILE)
    music_start = int(MUSIC_START_SEC * SR)
    music_end = music_start + N
    if music_end > len(music_full):
        needed = N - (len(music_full) - music_start)
        music = np.concatenate([music_full[music_start:], music_full[music_start:music_start+needed]])
    else:
        music = music_full[music_start:music_end]
    music = pad_to_n(music)

# Fades : démarrage dans l'énergie pleine → fade-in court 0.6s
fade_in_n = int(SR * 0.6)
fade_out_n = int(SR * 2.5)
music[:fade_in_n] *= np.linspace(0, 1, fade_in_n).astype(np.float32)
music[-fade_out_n:] *= np.linspace(1, 0, fade_out_n).astype(np.float32)

# Voice envelope for ducking
voice_raw = subprocess.run(
    ["ffmpeg","-y","-i",VOICE_FILE,"-ac","1","-ar",str(SR),"-f","s16le","-"],
    capture_output=True, check=True
).stdout
voice = pad_to_n(np.frombuffer(voice_raw, dtype=np.int16).astype(np.float32)/32768.0)

win = int(SR * 0.030)
kernel = np.ones(win, dtype=np.float32) / win
voice_env = np.convolve(np.abs(voice), kernel, mode="same").astype(np.float32)
peak_env = float(np.max(voice_env))
if peak_env > 0: voice_env = voice_env / peak_env
attack_n = int(SR * 0.040)
attack_k = np.ones(attack_n, dtype=np.float32) / attack_n
voice_env = np.convolve(voice_env, attack_k, mode="same")

def make_duck(depth, release_s, env):
    d = 1.0 - depth * env
    alpha = 1.0 - np.exp(-1.0/(SR*release_s))
    for i in range(1, len(d)):
        if d[i] > d[i-1]:
            d[i] = d[i-1] + alpha*(d[i]-d[i-1])
    return d

duck_music = make_duck(0.90, 0.400, voice_env)
music = music * duck_music
duck_sfx = make_duck(0.50, 0.300, voice_env)
sfx = sfx * duck_sfx

# Musique : peak ~ -10 dB (baseline mobile)
mp = float(np.max(np.abs(music)))
if mp > 0: music = music * (0.32 / mp)

# SFX : peak ~ -7 dB (baseline mobile)
sp = float(np.max(np.abs(sfx)))
if sp > 0: sfx = sfx * (0.45 / sp)

master = sfx + music
peak = float(np.max(np.abs(master)))
if peak > 0.62: master = master * (0.62/peak)

out = (master*32767).astype(np.int16)
wavfile.write("sfx/soundtrack-final.wav", SR, out)
subprocess.run([
    "ffmpeg","-y","-i","sfx/soundtrack-final.wav",
    "-c:a","aac","-b:a","192k","sfx/soundtrack-final.m4a"
], capture_output=True)

print(f"Wrote sfx/soundtrack-final.{{wav,m4a}} — dur={DURATION}s, music@{MUSIC_START_SEC}s, peak={float(np.max(np.abs(master))):.3f}")
