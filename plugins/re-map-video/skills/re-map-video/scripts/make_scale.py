#!/usr/bin/env python3
"""Assemble a re-map-video *scale* project (quy mô dự án) from template/scale.html.

Usage: python3 -I make_scale.py <project_dir>

Scenes, in order (seconds, override any in project.json "timing"):
  intro 4.5   fly down from the region to the site
  area  6.5   boundary draws, fill, area counts up at the centroid
  dims  5.5   length / width dimension lines along the main axis
  pitch 5.5   site fills with football pitches, "≈ N sân bóng đá"
  zone  2.6   per zone (parks, sub-areas) — skipped if no zones
  stats 6.0   stat board (counts up) — skipped if no stats
  outro 6.5   overview + CTA
Audio: "music" / "voiceover" as in make_html.py ("start" absolute seconds), or automatic:
  "voice": {"dir": "assets/audio"}      -> uses vo_<scene>.wav (intro, area, dims, pitch, zones, stats, outro):
                                           scene = max(default, line + 1.2), outro + 1.8, VO starts 0.4 s into its scene
  "music": {"source": "city-sunshine", "volume": 0.1}   # tên bài kèm gói (assets/music/) hoặc đường dẫn file
                                        -> cut to the video length with fades into assets/audio/bgm.m4a
"""
import json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_html import probe_duration, TPL, SKILL  # noqa: E402

def music_path(src):
    """Tên bài kèm gói (city-sunshine, happy-whistling-ukulele, inspiration) hoặc đường dẫn file."""
    own = os.path.join(SKILL, "assets", "music", f"{src}.m4a")
    return own if os.path.exists(own) else os.path.expanduser(src)


DEF = {"intro": 4.5, "area": 6.5, "dims": 5.5, "pitch": 5.5, "zone": 2.6, "stats": 6.0, "outro": 6.5}


def main():
    pdir = os.path.abspath(sys.argv[1])
    cfg = json.load(open(os.path.join(pdir, "project.json"), encoding="utf8"))
    tm = {**DEF, **cfg.get("timing", {})}
    nz = len(cfg.get("zones", []))
    order = ["intro", "area", "dims", "pitch"] + (["zones"] if nz else []) + (["stats"] if cfg.get("stats") else []) + ["outro"]
    voice = cfg.get("voice")
    if voice:
        vd = os.path.join(pdir, voice.get("dir", "assets/audio"))
        vlen = {s: probe_duration(os.path.join(vd, f"vo_{s}.wav")) for s in order if os.path.exists(os.path.join(vd, f"vo_{s}.wav"))}
        for s, d in vlen.items():
            if s == "zones":
                tm["zone"] = max(tm["zone"], (d + 1.2 - 0.8) / nz)
            else:
                tm[s] = round(max(tm[s], d + (1.8 if s == "outro" else 1.2)), 2)
    t, scenes = 0.0, {}
    for s in order:
        d = tm["zone"] * nz + 0.8 if s == "zones" else tm[s]
        scenes[s] = {"start": round(t, 3), "dur": round(d, 3)}
        t += d
    timing = {"scenes": scenes, "total": round(t, 3), "zone": tm["zone"]}
    if voice:
        rel = os.path.relpath(vd, pdir)
        cfg["voiceover"] = [{"src": f"{rel}/vo_{s}.wav", "start": round(scenes[s]["start"] + (0.3 if s == "intro" else 0.4), 2)} for s in order if s in vlen]
    mus = cfg.get("music")
    if mus and mus.get("source"):
        os.makedirs(os.path.join(pdir, "assets", "audio"), exist_ok=True)
        tot = timing["total"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", music_path(mus["source"]), "-t", str(tot),
                        "-af", f"afade=t=in:d=0.6,afade=t=out:st={tot - 2.5:.2f}:d=2.5", "-c:a", "aac", "-b:a", "192k",
                        os.path.join(pdir, "assets", "audio", "bgm.m4a")], check=True)
        mus["src"] = "assets/audio/bgm.m4a"

    for sub in ("fonts",):
        shutil.copytree(os.path.join(TPL, "assets", sub), os.path.join(pdir, "assets", sub), dirs_exist_ok=True)
    with open(os.path.join(pdir, "assets", "timing.js"), "w", encoding="utf8") as f:
        f.write("window.RE_TIMING = " + json.dumps(timing) + ";\n")

    html = open(os.path.join(TPL, "scale.html"), encoding="utf8").read()
    html = html.replace('data-duration="__DUR__"', f'data-duration="{timing["total"]}"')
    audio = []
    mus = cfg.get("music")
    if mus:
        audio.append(f'<audio id="bgm" src="{mus["src"]}" data-start="0" data-duration="{timing["total"]}" '
                     f'data-volume="{mus.get("volume", 0.5)}" data-track-index="8"></audio>')
    for n, vo in enumerate(cfg.get("voiceover", [])):
        d = probe_duration(os.path.join(pdir, vo["src"]))
        audio.append(f'<audio id="vo-{n}" src="{vo["src"]}" data-start="{vo["start"]}" data-duration="{round(d, 3)}" '
                     f'data-track-index="9"></audio>')
    html = html.replace("<!--AUDIO-->", "\n      ".join(audio))
    open(os.path.join(pdir, "index.html"), "w", encoding="utf8").write(html)
    print(f"index.html written · total {timing['total']}s · scenes {', '.join(order)}")


if __name__ == "__main__":
    main()
