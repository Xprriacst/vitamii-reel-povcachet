"""Robuste sync mic ↔ video.

Bug récurrent : les vidéos iPhone/Pixel ont souvent un `audio start_time != 0`
(ex: 0.767s) — le micro interne démarre quelques frames APRÈS la vidéo.
Si on cross-correle mic vs PCM décodé du source.mov, on obtient l'offset
mic[k] = cam_audio[0], mais cam_audio[0] = video[start_time], pas video[0].

→ vrai offset à trimmer dans mic.wav = corr_offset - audio_start_time
"""
import subprocess, json, sys
import numpy as np

SR = 48000

def probe_audio_start(path):
    out = subprocess.run(
        ["ffprobe","-v","error","-print_format","json","-show_streams",
         "-select_streams","a:0", path],
        capture_output=True, check=True
    ).stdout
    streams = json.loads(out)["streams"]
    s = streams[0]
    start = float(s.get("start_time", 0.0))
    return start

def decode_pcm(path, copyts=False):
    """Decode to mono 48kHz s16le. With copyts, preserve PTS (PCM has leading
    zeros if audio start_time > 0). Without, PCM starts at the first audio sample."""
    args = ["ffmpeg","-y"]
    if copyts:
        args += ["-copyts","-start_at_zero"]
    args += ["-i", path, "-ac","1","-ar",str(SR),"-f","s16le","-"]
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def fft_xcorr_offset(mic, cam):
    """Find lag k such that mic[k+t] aligns with cam[t]."""
    mic = mic - mic.mean(); cam = cam - cam.mean()
    mic = mic / (np.abs(mic).max() + 1e-9)
    cam = cam / (np.abs(cam).max() + 1e-9)
    n = len(mic) + len(cam)
    N = 1 << (n-1).bit_length()
    fm = np.fft.rfft(mic, N); fc = np.fft.rfft(cam, N)
    corr = np.fft.irfft(fm * np.conj(fc), N)
    lim = max(1, len(mic) - len(cam))
    k = int(np.argmax(corr[:lim]))
    peak = float(corr[k])
    return k / SR, peak

src = sys.argv[1] if len(sys.argv) > 1 else "sources/source.mov"
mic = sys.argv[2] if len(sys.argv) > 2 else "sources/mic.wav"

audio_start = probe_audio_start(src)
print(f"source.mov audio start_time : {audio_start:.4f}s")

cam = decode_pcm(src)        # PCM commence à cam_audio[0]
mic_a = decode_pcm(mic)
print(f"cam pcm : {len(cam)/SR:.3f}s, mic pcm : {len(mic_a)/SR:.3f}s")

# Cross-correlate sur fenêtre voix forte (skip 1s d'intro souvent silencieuse)
corr_offset, peak = fft_xcorr_offset(mic_a, cam)
print(f"corr peak : {corr_offset:.4f}s   strength={peak:.1f}")

# Vrai offset à trimmer dans mic.wav pour aligner avec VIDEO time 0 :
video_offset = corr_offset - audio_start
print(f"\n→ mic trim offset (aligned with VIDEO[0]) = {video_offset:.4f}s")
print(f"   (corr={corr_offset:.4f} - audio_start={audio_start:.4f})")

# Cross-check : split mic en 3 fenêtres et vérifier la cohérence
def find_offset_windowed(mic_full, cam_window, search_center, search_range=0.5):
    s = max(0, int((search_center - search_range)*SR))
    e = min(len(mic_full), int((search_center + search_range)*SR) + len(cam_window))
    chunk = mic_full[s:e]
    n = len(chunk) + len(cam_window)
    N = 1 << (n-1).bit_length()
    fm = np.fft.rfft(chunk, N); fc = np.fft.rfft(cam_window, N)
    c = np.fft.irfft(fm * np.conj(fc), N)
    lim = len(chunk) - len(cam_window)
    if lim <= 0: return None
    k = int(np.argmax(c[:lim]))
    return (s+k)/SR

print("\n--- drift check (windowed correlation) ---")
for t in [5, 30, 60]:
    if (t+5)*SR > len(cam): continue
    w = cam[t*SR:(t+5)*SR]
    o = find_offset_windowed(mic_a, w, corr_offset + t, 1.0)
    if o is not None:
        eq_start = o - t - audio_start
        print(f"  cam[{t}:{t+5}]  mic_align={o:.4f}s  → video_offset_eq={eq_start:.4f}s")
