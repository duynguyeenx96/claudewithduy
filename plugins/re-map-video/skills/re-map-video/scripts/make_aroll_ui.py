#!/usr/bin/env python3
"""A-roll UI mode: sales person talks on camera; when they mention a spec, the frame switches style.

  python3 -I make_aroll_ui.py <project_dir>

Reads <project_dir>/aroll_ui.json:
{
  "total": 49.2,
  "aroll": "assets/aroll.mp4",            # 1080x1920, sound on the clip unless "aroll_muted": true
  "aroll_muted": false,
  "map": "assets/map.mp4",                # map render, VO-aligned, with #texts,#brand,#credits hidden
  "face": [540, 820],                     # face centre on the A-roll, px
  "voice": "assets/audio/voice.m4a",      # optional separate voice track
  "music": {"src": "assets/audio/bgm.m4a", "volume": 1},
  "brand": {"name": "TÊN DỰ ÁN", "address": "Phường … · …"},
  "captions": [{"text": "…", "start": 0.3, "end": 2.1}],
  "segments": [
    {"kind": "title",   "start": 0.4, "end": 3.8},
    {"kind": "cutaway", "start": 6.98, "end": 14.52, "kicker": "GA METRO SỐ 1", "l1": "KẾT NỐI", "l2": "METRO SỐ 1", "sub": "~9 phút · 5,1 km"},
    {"kind": "info",    "start": 14.8, "end": 20.9, "photo": "assets/photos/x.jpg", "icon": "hospital", "kicker": "BỆNH VIỆN", "label": "Hoàn Mỹ Thủ Đức", "stat": "~4 phút", "sub": "2,5 km"},
    {"kind": "cta",     "start": 49.5, "end": 56.46, "title": "Bình luận GIÁ", "sub": "…", "button": "Nhắn tin ngay"}
  ]
}
kinds (keep it calm: speaker full frame most of the time, face never jumps around):
  title   name tag at the start
  info    photo/icon card above the head (kicker, label, stat, sub); speaker stays full frame. Use for most POIs.
  cutaway full map with its photo card + a text panel (kicker, l1, l2, sub); speaker in a fixed rounded PiP. Only for the 1–2 strongest points.
  cta     soft dark gradient + call to action at the end.
Map: render the project with its VO-aligned timing and #texts,#brand,#credits hidden (photo cards stay), so map time = video time
(map_t defaults to the segment start).
"""
import html, json, os, shutil, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = {
    "metro": '<rect x="-9" y="-11" width="18" height="17" rx="4" fill="#fff"/><rect x="-6" y="-8" width="12" height="6" rx="1.5" fill="#0f3a31"/><circle cx="-4.5" cy="2" r="1.8" fill="#0f3a31"/><circle cx="4.5" cy="2" r="1.8" fill="#0f3a31"/><path d="M-7 10 L-4 6 M7 10 L4 6" stroke="#fff" stroke-width="2.4"/>',
    "hospital": '<path d="M-3.5 -11h7v7.5h7.5v7h-7.5V11h-7V3.5H-11v-7h7.5z" fill="#fff"/>',
    "school": '<path d="M0 -10 L13 -3 L0 4 L-13 -3Z" fill="#fff"/><path d="M-7 1 v6 q7 5 14 0 v-6 L0 5Z" fill="#fff"/>',
    "shop": '<path d="M-9 -4h18l-1.5 15h-15z" fill="#fff"/><path d="M-4.5 -4v-3a4.5 4.5 0 0 1 9 0v3" stroke="#fff" stroke-width="2.6" fill="none"/>',
    "plane": '<path d="M0 -12 C2 -12 2.4 -9 2.4 -7 V-2 L12 4 V7 L2.4 4 V9 L5.5 11.5 V13.5 L0 12 L-5.5 13.5 V11.5 L-2.4 9 V4 L-12 7 V4 L-2.4 -2 V-7 C-2.4 -9 -2 -12 0 -12Z" fill="#fff"/>',
    "city": '<path d="M-11 11V-2h6v13zM-3 11V-11h7V11zM6 11V-5h6v16z" fill="#fff"/>',
    "home": '<path d="M0 -11 L12 0 H8 V11 H-8 V0 H-12Z" fill="#fff"/>',
}
E = html.escape


def icon_svg(name, size):
    return f'<svg width="{size}" height="{size}" viewBox="-16 -16 32 32">{ICON.get(name, ICON["home"])}</svg>'


def main():
    pdir = os.path.abspath(sys.argv[1])
    cfg = json.load(open(os.path.join(pdir, "aroll_ui.json"), encoding="utf8"))
    total = cfg["total"]
    fx, fy = cfg.get("face", [540, 820])
    tpl_fonts = os.path.join(SKILL, "template", "assets", "fonts")
    shutil.copytree(tpl_fonts, os.path.join(pdir, "assets", "fonts"), dirs_exist_ok=True)

    els, media = [], []
    muted = " muted" if cfg.get("aroll_muted") else ""
    has_audio = "false" if cfg.get("aroll_muted") else "true"
    media.append(f'<div id="aroll-wrap"><video id="aroll" class="clip" src="{cfg["aroll"]}" data-start="0" data-duration="{total}" '
                 f'data-track-index="0" data-has-audio="{has_audio}" playsinline{muted}></video></div>')
    for n, s in enumerate(cfg["segments"]):
        k, a, b = s["kind"], s["start"], s["end"]
        d = round(b - a, 3)
        if k == "cutaway":
            mt = s.get("map_t", a)
            media.append(f'<div id="mapw{n}" class="mapw"><video id="map{n}" class="clip" src="{cfg["map"]}" data-start="{a}" data-duration="{d}" '
                         f'data-media-start="{mt}" data-track-index="{2 + n}" muted playsinline></video></div>')
            media.append(f'<div id="pip{n}" class="pip"><video id="pipv{n}" class="clip" src="{cfg["aroll"]}" data-start="{a}" data-duration="{d}" '
                         f'data-media-start="{a}" data-track-index="{30 + n}" muted playsinline></video></div>')
            els.append(f'<div id="seg{n}" class="panel"><span class="k">{E(s.get("kicker", ""))}</span><span class="l1">{E(s.get("l1", ""))}</span>'
                       f'<span class="l2">{E(s.get("l2", ""))}</span><span class="r"></span><span class="sb">{E(s.get("sub", ""))}</span></div>')
        elif k == "title":
            b_ = cfg["brand"]
            els.append(f'<div id="seg{n}" class="nametag"><span class="k">DỰ ÁN</span><span class="n">{E(b_["name"])}</span><span class="r"></span><span class="ad">{E(b_.get("address", ""))}</span></div>')
        elif k == "info":
            ph = f'<img src="{s["photo"]}" alt="">' if s.get("photo") else icon_svg(s.get("icon"), 150)
            sub = f'<span class="sb">{E(s["sub"])}</span>' if s.get("sub") else ""
            els.append(f'<div id="seg{n}" class="info"><div class="ph">{ph}</div><div class="tx"><span class="k">{E(s.get("kicker", ""))}</span>'
                       f'<span class="lb">{E(s.get("label", ""))}</span><span class="st">{E(s.get("stat", ""))}</span>{sub}</div></div>')
        elif k == "cta":
            els.append(f'<div id="seg{n}" class="cta"><span class="t">{E(s.get("title", "LIÊN HỆ"))}</span><span class="s">{E(s.get("sub", ""))}</span>'
                       f'<span class="btn">{E(s.get("button", "Nhận bảng giá"))}</span></div>')
    cta_t = min([s["start"] for s in cfg["segments"] if s["kind"] == "cta"] or [1e9])
    cfg["captions"] = [c for c in cfg.get("captions", []) if c["start"] < cta_t]   # the CTA card carries the last line
    caps = "".join(f'<div id="cap{i}" class="cap">{E(c["text"])}</div>' for i, c in enumerate(cfg.get("captions", [])))
    audio = []
    if cfg.get("voice"):
        audio.append(f'<audio id="voice" src="{cfg["voice"]}" data-start="0" data-duration="{total}" data-track-index="60"></audio>')
    if cfg.get("music"):
        m = cfg["music"]
        audio.append(f'<audio id="bgm" src="{m["src"]}" data-start="0" data-duration="{total}" data-volume="{m.get("volume", 1)}" data-track-index="61"></audio>')

    page = open(os.path.join(SKILL, "template", "aroll_ui.html"), encoding="utf8").read()
    page = (page.replace("__DUR__", str(total)).replace("__FX__", str(fx)).replace("__FY__", str(fy))
            .replace("<!--MEDIA-->", "\n      ".join(media)).replace("<!--ELS-->", "\n      ".join(els))
            .replace("<!--CAPS-->", caps).replace('<div id="brandmini"></div>', f'<div id="brandmini">{E(cfg["brand"]["name"])}</div>').replace("<!--AUDIO-->", "\n      ".join(audio))
            .replace("__PLAN__", json.dumps({"segments": cfg["segments"], "captions": cfg.get("captions", []), "total": total}, ensure_ascii=False)))
    open(os.path.join(pdir, "index.html"), "w", encoding="utf8").write(page)
    print(f"index.html · {total}s · {len(cfg['segments'])} segments · {len(cfg.get('captions', []))} captions")


if __name__ == "__main__":
    main()
