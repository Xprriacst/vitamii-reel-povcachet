"""
build-broll-cachet.py — assemble broll.mp4 1080x1920 @30fps depuis segments-timing.json.
Adapté du build-broll.sh POVIA : chemins src explicites dans le json, option "stretch"
(setpts vers la durée du slot, <=15 %), kenburns pour les stills, head_fx light-leak /
whip-zoom sur la tête du plan entrant. Frames exactes par frontières cumulées.
"""
import json, subprocess, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
t = json.load(open("segments-timing.json"))
FPS = t["fps"]
os.makedirs("work/slots", exist_ok=True)


def head_fx(kind):
    if kind == "lightleak":
        return ("eq=eval=frame:brightness='0.34*exp(-t/0.085)'"
                ":saturation='1+0.20*exp(-t/0.085)'"
                ":gamma_r='1+0.22*exp(-t/0.085)':gamma_b='1-0.12*exp(-t/0.085)'")
    if kind == "whipzoom":
        return ("zoompan=z='1+0.35*exp(-on/2.6)':d=1:x='(iw-iw/zoom)/2'"
                ":y='(ih-ih/zoom)/2':s=1080x1920:fps=30,"
                "gblur=sigma=13:enable='lt(t,0.08)',"
                "gblur=sigma=6:enable='between(t,0.08,0.16)',"
                "gblur=sigma=2.5:enable='between(t,0.16,0.24)'")
    return None


def src_dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip())


concat_lines = []
for i, s in enumerate(t["timeline"]):
    clip, dur = s["clip"], round(s["end"] - s["start"], 3)
    n = int(round(s["end"] * FPS)) - int(round(s["start"] * FPS))
    out = f"work/slots/{i:02d}-{clip}.mp4"
    concat_lines.append(f"file '{os.path.abspath(out)}'")
    if os.path.exists(out):
        print(f"[skip] {out}")
        continue
    src = s["src"]
    off = s.get("src_offset", 0.0)
    common = ["-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "fast",
              "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    base = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    fx = head_fx(s.get("transition_in"))
    tail = (fx + ",format=yuv420p") if fx else "format=yuv420p"
    if s.get("kenburns"):
        vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
              f"zoompan=z='1+0.08*on/{n}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
              f":d={n}:s=1080x1920:fps={FPS}," + tail)
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src,
               "-vf", vf] + common + [out]
    elif s.get("stretch"):
        factor = round((n / FPS) / src_dur(src), 4)
        assert factor <= 1.16, f"{clip}: stretch {factor} > 15 %"
        vf = (f"setpts=PTS*{factor},{base},fps={FPS}," + tail)
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf] + common + [out]
    else:
        vf = (f"trim=start={off}:end={off + dur + 0.15},setpts=PTS-STARTPTS,"
              f"{base},fps={FPS}," + tail)
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf] + common + [out]
    print(f"[enc] {out} ({dur}s{' stretch' if s.get('stretch') else ''}"
          f"{' KB' if s.get('kenburns') else ''}{' fx=' + s.get('transition_in') if s.get('transition_in') else ''})")
    subprocess.run(cmd, check=True)

open("work/concat.txt", "w").write("\n".join(concat_lines) + "\n")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", "work/concat.txt", "-c", "copy", "broll.mp4"], check=True)
total = src_dur("broll.mp4")
print(f"broll.mp4 : {total:.3f}s (cible {t['duration']})")
assert abs(total - t["duration"]) < 0.15, "DERIVE DE DUREE"
print("OK")
