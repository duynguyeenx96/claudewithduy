#!/usr/bin/env python3
"""Assemble a re-map-video HyperFrames project from template + project.json.

Usage: python3 -I make_html.py <project_dir>

Timing rules (seconds):
  default      intro 5, each POI beat 7, outro 7  (hero image adds hero.dur before intro)
  per-POI      "dur": n  overrides the beat length (ai_voice: set from the VO line length)
  aroll mode   "aroll": {"src": "assets/aroll.mp4", "shape": "circle"|"rect",
                         "beats": {"<poi id>": <start sec>, ...}, "outro": <start sec>}
               -> beat starts follow the talking points in the sales clip; total = clip length.
Audio:
  "music":     {"src": "assets/audio/bgm.mp3", "volume": 0.5}
  "voiceover": [{"src": "assets/audio/vo_intro.mp3", "start": 0.4}, ...]
"""
import json, os, re, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SKILL, "template")


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    pdir = os.path.abspath(sys.argv[1])
    cfg = json.load(open(os.path.join(pdir, "project.json"), encoding="utf8"))
    tm = {"intro": 5.0, "beat": 7.0, "outro": 7.0, **cfg.get("timing", {})}
    pois = cfg["pois"]

    hero = cfg.get("hero")
    t = 0.0
    timing = {"hero": None}
    if hero:
        timing["hero"] = {"dur": float(hero.get("dur", 2.8))}
        t = timing["hero"]["dur"] - 0.4

    aroll = cfg.get("aroll")
    beats = []
    if aroll and aroll.get("beats"):
        total = probe_duration(os.path.join(pdir, aroll["src"]))
        starts = sorted((float(s), pid) for pid, s in aroll["beats"].items())
        timing["intro"] = {"start": t, "dur": max(2.5, starts[0][0] - t)}
        outro_start = float(aroll.get("outro", total - tm["outro"]))
        for n, (s, pid) in enumerate(starts):
            end = starts[n + 1][0] if n + 1 < len(starts) else outro_start
            beats.append({"i": [p["id"] for p in pois].index(pid), "start": s, "dur": round(end - s, 3)})
        timing["outro"] = {"start": outro_start, "dur": round(total - outro_start, 3)}
    else:
        timing["intro"] = {"start": t, "dur": tm["intro"]}
        t += tm["intro"]
        for i, p in enumerate(pois):
            d = float(p.get("dur", tm["beat"]))
            beats.append({"i": i, "start": round(t, 3), "dur": d})
            t += d
        timing["outro"] = {"start": round(t, 3), "dur": tm["outro"]}
        total = t + tm["outro"]
    timing["beats"] = beats
    timing["total"] = round(total, 3)

    # copy static template assets
    for sub in ("fonts", "fx"):
        dst = os.path.join(pdir, "assets", sub)
        shutil.copytree(os.path.join(TPL, "assets", sub), dst, dirs_exist_ok=True)

    with open(os.path.join(pdir, "assets", "timing.js"), "w", encoding="utf8") as f:
        f.write("window.RE_TIMING = " + json.dumps(timing) + ";\n")

    html = open(os.path.join(TPL, "index.html"), encoding="utf8").read()
    html = html.replace('data-duration="__DUR__"', f'data-duration="{timing["total"]}"')
    if hero:
        html = html.replace("<!--HERO-->", f'<div id="hero"><img src="{hero["src"]}" alt="" /></div>')
    if aroll:
        cls = "rect" if aroll.get("shape") == "rect" else ""
        html = html.replace("<!--AROLL-->",
            f'<div id="aroll" class="{cls}"><video id="aroll-video" src="{aroll["src"]}" data-start="0" '
            f'data-duration="{timing["total"]}" data-track-index="5" playsinline></video></div>')
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
    print(f"index.html written · total {timing['total']}s · {len(beats)} beats")


if __name__ == "__main__":
    main()
