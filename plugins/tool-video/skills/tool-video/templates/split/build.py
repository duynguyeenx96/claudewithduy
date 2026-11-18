"""Demo: CIVAGO2.MOV (talking head mockup) + motion graphics kiểu split-screen về website HyperFrames.

python3 build.py   # dựng public/index.html
"""
import html
import json
import random
from pathlib import Path

import sys
import os
SK = os.environ.get("TOOL_VIDEO_SK") or sys.exit("thiếu TOOL_VIDEO_SK: chạy TOOL_VIDEO_SK=<thư mục skill tool-video> python3 build.py")
sys.path.insert(0, os.path.join(SK, "scripts"))
from sfxkit import sfx_tags   # bộ SFX CC0 của skill: mức + điểm neo theo vai, xoay vòng bản
WORK = Path(__file__).parent
PUB = WORK / "public"
FPS, W, H = 30, 1080, 1920
DURATION = 9.31
SEAM = 960            # nửa trên: graphic, nửa dưới: người nói
FULL = (1.40, 2.50)   # đoạn phóng người nói ra full màn hình
ACC = "#3df0b4"       # mint của HyperFrames
FONT = '"Be Vietnam Pro", sans-serif'

# cảnh ở nửa trên: (id, bắt đầu, kết thúc)
SCENES = {
    "burst": (0.0, 1.40),
    "browser": (2.50, 3.90),
    "slot": (3.90, 5.20),
    "stack": (5.20, 6.30),
    "price": (6.30, 7.80),
    "cta": (7.80, DURATION),
}
KEYWORDS = {"CIVAGO", "400ML", "SỨ", "CÀ", "PHÊ"}


def q(t):
    return f"{round(t * FPS) / FPS:.4f}"


tl, sfx, css, hosts = [], [], [], []


def host(sid, inner, style=""):
    s, e = SCENES[sid]
    hosts.append(f'<div id="sc-{sid}" class="scene clip" data-start="{s:.4f}" data-duration="{e - s:.4f}" data-track-index="3">{inner}</div>')
    if style:
        css.append(style)
    if e < DURATION:
        tl.append(f"tl.to('#sc-{sid}', {{opacity:0, scale:0.96, duration:0.15, ease:'power2.in'}}, {q(e - 0.15)});")
    sfx.append(("pop", s + 0.02))


# ---------- A. Burst: nút Generate + thumbnail bung ra quỹ đạo ----------
thumbs = [("th-tpl1.jpg", -370, -150, -9, 170), ("th-tpl2.jpg", 370, -170, 8, 170), ("th-what.jpg", -330, 150, 6, 250),
          ("th-tpl4.jpg", 360, 120, -7, 160), ("th-framer.jpg", 0, -190, -3, 260)]
th_html = "".join(f'<img class="th" id="th{i}" src="img/{f}" style="width:{w}px">' for i, (f, *_rest, w) in enumerate(thumbs))
host("burst", f"""
  <img id="logo" src="img/logo.png">
  <div id="orbit">{th_html}
    <div id="gen"><span>Generate</span><span class="spark">✦</span><span class="zero">0</span></div>
  </div>
  <div id="burst-title"><div>HYPERFRAMES</div><div class="hl">100% MIỄN PHÍ</div></div>""", f"""
  #logo {{ position:absolute; left:50%; top:260px; width:220px; transform:translateX(-50%); }}
  #orbit {{ position:absolute; left:540px; top:520px; width:0; height:0; }}
  #orbit .th {{ position:absolute; left:0; top:0; border-radius:18px; border:3px solid rgba(255,255,255,.9);
    box-shadow:0 20px 50px rgba(0,0,0,.6); transform:translate(-50%,-50%); }}
  #gen {{ position:absolute; left:0; top:0; transform:translate(-50%,-50%); display:flex; align-items:center; gap:18px;
    padding:26px 30px 26px 48px; border-radius:999px; background:{ACC}; color:#04120c; font:900 58px/1 {FONT}; white-space:nowrap;
    box-shadow:0 0 80px rgba(61,240,180,.55); }}
  #gen .zero {{ display:inline-flex; align-items:center; justify-content:center; width:64px; height:64px; border-radius:50%;
    background:#04120c; color:{ACC}; font-size:36px; }}
  #burst-title {{ position:absolute; left:0; right:0; top:730px; text-align:center; font:900 84px/1 {FONT}; color:#fff;
    letter-spacing:-.01em; transform:skewX(-8deg); }}
  #burst-title .hl {{ color:{ACC}; margin-top:10px; }}""")
tl.append(f"tl.from('#logo', {{opacity:0, y:-30, duration:0.3, ease:'power2.out'}}, {q(0.05)});")
tl.append(f"tl.from('#gen', {{scale:0, duration:0.4, ease:'back.out(2)'}}, {q(0.05)});")
for i, (_f, x, y, rot, _w) in enumerate(thumbs):
    tl.append(f"tl.fromTo('#th{i}', {{x:0, y:0, scale:0, rotation:0, opacity:0}}, "
              f"{{x:{x}, y:{y}, scale:1, rotation:{rot}, opacity:1, duration:0.55, ease:'back.out(1.5)'}}, {q(0.25 + i * 0.05)});")
    tl.append(f"tl.to('#th{i}', {{y:'+={-14 if i % 2 else 14}', duration:0.6, ease:'sine.inOut'}}, {q(0.8)});")
tl.append(f"tl.from('#burst-title div', {{opacity:0, y:40, duration:0.3, ease:'power3.out', stagger:0.12}}, {q(0.45)});")
sfx.append(("whoosh", 0.2))

# ---------- B. Browser mockup: lao tới 3D, zoom vào ô nhập, gõ chữ ----------
BX, BY, BW = 110, 280, 860   # vùng an toàn: không lên trên 250px
BH = round(BW * 900 / 1440)
IN_X, IN_Y = round(BW * 317 / 1440), 44 + round(BH * 343 / 900)    # ô "Enter your brand website"
IN_W, IN_H = round(BW * 653 / 1440), round(BH * 48 / 900)
ORX, ORY = IN_X + IN_W // 2, IN_Y + IN_H // 2
typed = "civago.vn"
host("browser", f"""
  <div id="persp"><div id="browser">
    <div class="bar"><i></i><i></i><i></i><div class="url">hyperframes.dev</div></div>
    <img src="img/site-full.jpg">
    <div id="typer">{''.join(f'<span class="ch">{c}</span>' for c in typed)}<span id="caret"></span></div>
    <div id="go"></div>
  </div></div>
  <div id="browser-tag">Dán link web → ra video quảng cáo</div>""", f"""
  #persp {{ position:absolute; inset:0; perspective:1400px; }}
  #browser {{ position:absolute; left:{BX}px; top:{BY}px; width:{BW}px; border-radius:16px; overflow:hidden; background:#0b0b0b;
    border:1px solid rgba(255,255,255,.18); box-shadow:0 40px 90px rgba(0,0,0,.7), 0 0 60px rgba(61,240,180,.15);
    transform-origin:{ORX}px {ORY}px; }}
  #browser .bar {{ height:44px; display:flex; align-items:center; gap:9px; padding:0 16px; background:#1a1a1a; }}
  #browser .bar i {{ width:13px; height:13px; border-radius:50%; background:#444; }}
  #browser .url {{ margin-left:16px; flex:1; height:28px; border-radius:8px; background:#0c0c0c; color:#aaa; font:500 15px/28px {FONT}; padding-left:14px; }}
  #browser img {{ display:block; width:100%; }}
  #typer {{ position:absolute; left:{IN_X + 2}px; top:{IN_Y + 2}px; width:{IN_W - 4}px; height:{IN_H - 4}px; border-radius:7px;
    background:#151515; color:#fff; font:600 14px/{IN_H - 4}px {FONT}; padding-left:10px; white-space:nowrap; opacity:0; }}
  #caret {{ display:inline-block; width:2px; height:15px; background:{ACC}; vertical-align:middle; margin-left:1px; }}
  #go {{ position:absolute; left:{round(BW * 1113 / 1440)}px; top:{44 + round(BH * 343 / 900)}px; width:{round(BW * 48 / 1440)}px;
    height:{round(BW * 48 / 1440)}px; border-radius:50%; background:{ACC}; opacity:0; box-shadow:0 0 30px {ACC}; }}
  #browser-tag {{ position:absolute; left:50%; top:840px; transform:translateX(-50%); padding:18px 36px; border-radius:999px;
    border:3px dashed {ACC}; background:rgba(4,18,12,.85); color:#fff; font:800 44px/1 {FONT}; white-space:nowrap; }}""")
s = SCENES["browser"][0]
tl.append(f"tl.fromTo('#browser', {{rotationX:28, rotationY:-22, scale:0.6, y:260, opacity:0}}, "
          f"{{rotationX:0, rotationY:0, scale:1, y:0, opacity:1, duration:0.45, ease:'power3.out'}}, {q(s)});")
tl.append(f"tl.to('#browser', {{scale:2.25, x:{540 - BX - ORX}, duration:0.45, ease:'power3.inOut'}}, {q(s + 0.45)});")
tl.append(f"tl.set('#typer', {{opacity:1}}, {q(s + 0.75)});")
tl.append(f"tl.from('#typer .ch', {{display:'none', duration:0.01, stagger:0.045}}, {q(s + 0.78)});")
tl.append(f"tl.to('#browser', {{scale:2.4, duration:0.4, ease:'power2.inOut'}}, {q(s + 1.0)});")
tl.append(f"tl.fromTo('#go', {{opacity:0, scale:1}}, {{opacity:0.9, scale:1.5, duration:0.12, yoyo:true, repeat:1}}, {q(s + 1.15)});")
tl.append(f"tl.from('#browser-tag', {{opacity:0, scale:0.6, duration:0.3, ease:'back.out(1.8)'}}, {q(s + 0.55)});")
sfx += [("whoosh", s), ("click", s + 1.15)]

# ---------- C. Slot list: tính năng chạy như máy slot ----------
feats = [("✦", "Kinetic Titles"), ("▤", "Lower-thirds"), ("Aa", "Phụ đề theo lời"), ("▣", "Picture-in-Picture"),
         ("▲", "Data Charts"), ("⇆", "Transitions"), ("♪", "Sound FX"), ("◎", "Zoom nhấn")]
ROW = 120
rows = "".join(f'<div class="row"><span class="ic">{i}</span><span class="nm">{html.escape(n)}</span><span class="bd">FREE</span></div>'
               for i, n in feats)
host("slot", f"""
  <div id="slot-head">Tất cả trong 1 framework</div>
  <div id="slot-win"><div id="slot-list">{rows}</div></div>
  <div id="slot-sel"></div>
  <div id="slot-price">$0</div>""", f"""
  #slot-head {{ position:absolute; left:0; right:0; top:260px; text-align:center; color:#fff; font:800 50px/1 {FONT}; }}
  #slot-win {{ position:absolute; left:70px; top:330px; width:760px; height:{ROW * 5}px; overflow:hidden;
    -webkit-mask-image:linear-gradient(transparent, #000 25%, #000 75%, transparent); mask-image:linear-gradient(transparent, #000 25%, #000 75%, transparent); }}
  #slot-list {{ padding-top:{ROW * 2}px; }}
  #slot-list .row {{ height:{ROW - 22}px; margin-bottom:22px; display:flex; align-items:center; gap:24px; padding:0 26px; border-radius:30px;
    background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); }}
  #slot-list .ic {{ width:78px; height:78px; border-radius:20px; background:#1d2a25; color:{ACC}; display:flex; align-items:center;
    justify-content:center; font:900 38px/1 {FONT}; }}
  #slot-list .nm {{ flex:1; color:#fff; font:800 46px/1 {FONT}; white-space:nowrap; }}
  #slot-list .bd {{ padding:10px 18px; border-radius:12px; background:rgba(61,240,180,.16); color:{ACC}; font:900 26px/1 {FONT}; letter-spacing:.06em; }}
  #slot-sel {{ position:absolute; left:52px; top:{330 + ROW * 2 - 12}px; width:796px; height:{ROW - 22 + 24}px; border-radius:38px;
    border:5px solid {ACC}; box-shadow:0 0 40px rgba(61,240,180,.5); }}
  #slot-price {{ position:absolute; left:860px; top:{330 + ROW * 2 - 6}px; width:150px; height:{ROW - 10}px; border-radius:30px;
    background:{ACC}; color:#04120c; font:900 72px/{ROW - 10}px {FONT}; text-align:center; box-shadow:0 0 50px rgba(61,240,180,.6); }}""")
s = SCENES["slot"][0]
tl.append(f"tl.from('#slot-head', {{opacity:0, y:-20, duration:0.25}}, {q(s)});")
tl.append(f"tl.from('#slot-sel, #slot-price', {{scale:0.4, opacity:0, duration:0.35, ease:'back.out(2)', stagger:0.08}}, {q(s + 0.05)});")
for k, step in enumerate([1, 3, 6]):
    tl.append(f"tl.to('#slot-list', {{y:{-ROW * step}, duration:0.3, ease:'power3.inOut'}}, {q(s + 0.2 + k * 0.36)});")
    sfx.append(("click", s + 0.45 + k * 0.36))

# ---------- D. Thác chữ: công nghệ ----------
stack = ["HTML", "CSS", "GSAP", "LOTTIE", "THREE.JS", "TAILWIND", "→ MP4"]
host("stack", f"""
  <div id="stack-badge">OPEN SOURCE</div>
  <div id="stack">{''.join(f'<div class="it{" last" if i == len(stack) - 1 else ""}">{t}</div>' for i, t in enumerate(stack))}</div>""", f"""
  #stack-badge {{ position:absolute; left:50%; top:260px; transform:translateX(-50%); padding:14px 30px; border-radius:999px;
    background:{ACC}; color:#04120c; font:900 40px/1 {FONT}; letter-spacing:.04em; }}
  #stack {{ position:absolute; left:0; right:0; top:350px; text-align:center; }}
  #stack .it {{ color:#fff; font:900 78px/1.06 {FONT}; transform:skewX(-10deg); letter-spacing:-.01em; }}
  #stack .it.last {{ color:{ACC}; text-shadow:0 0 40px rgba(61,240,180,.7); }}""")
s = SCENES["stack"][0]
tl.append(f"tl.from('#stack-badge', {{scale:0, duration:0.3, ease:'back.out(2)'}}, {q(s)});")
tl.append(f"tl.from('#stack .it', {{opacity:0, y:30, scale:1.3, duration:0.18, ease:'power3.out', stagger:0.085}}, {q(s + 0.1)});")

# ---------- E. Gạch giá → $0 + đếm sao GitHub ----------
rnd = random.Random(7)
dots = "".join(f'<i class="pt" style="left:{rnd.randint(120, 960)}px;top:{rnd.randint(250, 700)}px;'
               f'width:{rnd.randint(4, 10)}px;height:{rnd.randint(4, 10)}px"></i>' for _ in range(28))
host("price", f"""
  <div id="old"><span>$299</span><small>/tháng</small><div id="strike"></div></div>
  <div id="glow"></div>{dots}
  <div id="zero">$0</div>
  <div id="stars">★ <span id="star-n">0</span> sao GitHub</div>""", f"""
  #old {{ position:absolute; left:0; right:0; top:280px; text-align:center; color:#cfd6d3; font:900 130px/1 {FONT}; }}
  #old small {{ font-size:48px; font-weight:700; }}
  #strike {{ position:absolute; left:250px; right:250px; top:62px; height:14px; border-radius:8px; background:#ff3b5c;
    transform:rotate(-8deg); transform-origin:left center; }}
  #glow {{ position:absolute; left:540px; top:560px; width:760px; height:760px; margin:-380px 0 0 -380px; border-radius:50%;
    background:radial-gradient(circle, rgba(61,240,180,.45), transparent 62%); opacity:0; }}
  .pt {{ position:absolute; border-radius:50%; background:{ACC}; opacity:0; box-shadow:0 0 12px {ACC}; }}
  #zero {{ position:absolute; left:0; right:0; top:400px; text-align:center; color:{ACC}; font:900 340px/1 {FONT};
    text-shadow:0 0 60px rgba(61,240,180,.8); opacity:0; }}
  #stars {{ position:absolute; left:0; right:0; top:800px; text-align:center; color:#fff; font:800 56px/1 {FONT}; opacity:0; }}
  #stars span {{ color:{ACC}; font-variant-numeric:tabular-nums; }}""")
s = SCENES["price"][0]
tl.append(f"tl.fromTo('#old', {{opacity:0, rotationX:60, scale:0.8}}, {{opacity:1, rotationX:0, scale:1, duration:0.3, ease:'power3.out'}}, {q(s)});")
tl.append(f"tl.fromTo('#strike', {{scaleX:0}}, {{scaleX:1, duration:0.2, ease:'power2.out'}}, {q(s + 0.3)});")
tl.append(f"tl.to('#old', {{opacity:0.25, y:-40, scale:0.7, duration:0.25, ease:'power2.in'}}, {q(s + 0.55)});")
tl.append(f"tl.fromTo('#zero', {{opacity:0, scale:2.6, filter:'blur(14px)'}}, {{opacity:1, scale:1, filter:'blur(0px)', duration:0.5, ease:'elastic.out(1,0.55)'}}, {q(s + 0.6)});")
tl.append(f"tl.to('#glow', {{opacity:1, duration:0.3}}, {q(s + 0.62)});")
tl.append(f"tl.fromTo('.pt', {{opacity:0, y:0}}, {{opacity:0.9, y:-90, duration:0.8, ease:'power1.out', stagger:0.012}}, {q(s + 0.62)});")
tl.append(f"tl.to('#stars', {{opacity:1, duration:0.2}}, {q(s + 0.8)});")
tl.append(f"(function(){{const o={{v:0}};tl.to(o, {{v:57476, duration:0.6, ease:'power2.out', "
          f"onUpdate:function(){{document.getElementById('star-n').textContent=Math.round(o.v).toLocaleString('en-US');}}}}, {q(s + 0.8)});}})();")
sfx += [("wrong", s + 0.3), ("whoosh", s + 0.55), ("digits", s + 0.8)]

# ---------- F. CTA: terminal + nút Playground ----------
cmd = "npx hyperframes init my-video"
host("cta", f"""
  <div id="term"><div class="bar"><i></i><i></i><i></i><span>Terminal</span></div>
    <div class="body"><span class="pr">$</span> {''.join(f'<span class="tc">{html.escape(c)}</span>' for c in cmd)}<span id="tcar"></span>
      <div id="tout">✓ Project created · mở Studio để sửa</div></div></div>
  <div id="play">Playground <b>›</b></div>""", f"""
  #term {{ position:absolute; left:70px; top:270px; width:940px; border-radius:22px; overflow:hidden; background:#0d1110;
    border:1px solid rgba(255,255,255,.16); box-shadow:0 30px 80px rgba(0,0,0,.6); }}
  #term .bar {{ height:54px; display:flex; align-items:center; gap:10px; padding:0 20px; background:#18201d; color:#8a9a94; font:600 24px/1 {FONT}; }}
  #term .bar i {{ width:16px; height:16px; border-radius:50%; background:#3a4642; }}
  #term .bar span {{ margin-left:14px; }}
  #term .body {{ padding:36px 34px 40px; color:#fff; font:700 46px/1.4 Menlo, monospace; white-space:nowrap; }}
  #term .pr {{ color:{ACC}; }}
  #tcar {{ display:inline-block; width:22px; height:46px; background:{ACC}; vertical-align:-6px; }}
  #tout {{ margin-top:14px; color:{ACC}; font:600 34px/1.3 {FONT}; opacity:0; }}
  #play {{ position:absolute; left:50%; top:710px; transform:translateX(-50%); padding:34px 64px; border-radius:999px;
    background:linear-gradient(90deg, {ACC}, #22d3ee); color:#04120c; font:900 72px/1 {FONT}; white-space:nowrap;
    box-shadow:0 0 70px rgba(61,240,180,.6); }}""")
s = SCENES["cta"][0]
tl.append(f"tl.from('#term', {{opacity:0, y:60, duration:0.3, ease:'power3.out'}}, {q(s)});")
tl.append(f"tl.from('#term .tc', {{display:'none', duration:0.01, stagger:0.022}}, {q(s + 0.25)});")
tl.append(f"tl.to('#tout', {{opacity:1, duration:0.2}}, {q(s + 0.95)});")
tl.append(f"tl.from('#play', {{scale:0, duration:0.4, ease:'back.out(2)'}}, {q(s + 0.4)});")
tl.append(f"tl.to('#play', {{scale:1.07, duration:0.25, yoyo:true, repeat:3, ease:'sine.inOut'}}, {q(s + 0.9)});")
sfx += [("click", s + 0.95)]

# ---------- Video: split ↔ full ----------
a, b = FULL
tl.append(f"tl.to('#video-wrap', {{top:0, height:{H}, duration:0.35, ease:'power3.inOut'}}, {q(a)});")
tl.append(f"tl.fromTo('#seam', {{opacity:1}}, {{opacity:0, duration:0.1}}, {q(a)});")
tl.append(f"tl.fromTo('#bg-video', {{scale:1}}, {{scale:1.1, duration:{b - a - 0.35:.2f}, ease:'none'}}, {q(a + 0.35)});")
tl.append(f"tl.to('#video-wrap', {{top:{SEAM}, height:{H - SEAM}, duration:0.35, ease:'power3.inOut'}}, {q(b - 0.1)});")
tl.append(f"tl.set('#bg-video', {{scale:1}}, {q(b + 0.25)});")
tl.append(f"tl.to('#seam', {{opacity:1, duration:0.1}}, {q(b + 0.25)});")
# zoom nhấn nhẹ vào mặt ở nửa dưới khi đổi cảnh
for t in (SCENES["price"][0] + 0.6, SCENES["cta"][0]):
    tl.append(f"tl.to('#bg-video', {{scale:1.12, duration:0.18, ease:'back.out(1.5)'}}, {q(t)});")
    tl.append(f"tl.to('#bg-video', {{scale:1, duration:0.3, ease:'power2.inOut'}}, {q(t + 0.7)});")
sfx += [("whoosh", a + 0.05), ("whoosh", b)]
# full-screen: pill viền nét đứt
hosts.append(f'<div id="full-pill-host" class="clip" data-start="{a + 0.2:.3f}" data-duration="{b - a - 0.3:.3f}" data-track-index="4">'
             f'<div id="full-pill">HTML <b>➜</b> VIDEO</div></div>')
css.append(f"""
  #full-pill-host {{ z-index:5; position:absolute; left:0; top:0; width:{W}px; height:{H}px; }}
  #full-pill {{ position:absolute; left:50%; top:270px; transform:translateX(-50%); padding:26px 54px; border-radius:999px; border:4px dashed {ACC};
    background:rgba(4,18,12,.75); color:#fff; font:900 78px/1 {FONT}; white-space:nowrap; box-shadow:0 0 50px rgba(61,240,180,.35); }}
  #full-pill b {{ color:{ACC}; }}""")
tl.append(f"tl.from('#full-pill', {{scale:0.3, opacity:0, duration:0.35, ease:'back.out(2)'}}, {q(a + 0.2)});")

# ---------- Phụ đề ----------
words = json.loads((WORK / "transcript.json").read_text())
for w in words:
    if w["text"].lower().startswith("mchiber"):
        w["text"] = "CIVAGO"
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if w["text"][-1] in ",." or len(cur) >= 4 or not nxt or nxt["start"] - w["end"] > 0.35:
        groups.append(cur)
        cur = []
caps = []
for gi, g in enumerate(groups):
    st = max(0, g[0]["start"] - 0.05)
    en = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else DURATION
    en = min(en, g[-1]["end"] + 0.8)
    top = 1330 if a <= st < b else SEAM
    spans = " ".join(f'<span class="cw{" kw" if w["text"].strip(",.").upper() in KEYWORDS else ""}" id="c{gi}w{wi}">'
                     f'{html.escape(w["text"].strip(",").upper())}</span>' for wi, w in enumerate(g))
    caps.append(f'<div class="cg" id="cg{gi}" style="top:{top}px">{spans}</div>')
    tl.append(f"tl.set('#cg{gi}', {{visibility:'visible'}}, {q(st)});")
    tl.append(f"tl.fromTo('#cg{gi}', {{scale:0.7, opacity:0}}, {{scale:1, opacity:1, duration:0.12, ease:'back.out(2)'}}, {q(st)});")
    for wi, w in enumerate(g):
        tl.append(f"tl.fromTo('#c{gi}w{wi}', {{color:'#ffffff'}}, {{color:'{ACC}', duration:0.05}}, {q(w['start'])});")
        if not w["text"].strip(",.").upper() in KEYWORDS:
            tl.append(f"tl.to('#c{gi}w{wi}', {{color:'#ffffff', duration:0.05}}, {q(max(w['end'], w['start'] + 0.12))});")
    if top != SEAM and en > b:   # câu bắt đầu lúc full màn hình -> về đường nối khi chia đôi lại
        tl.append(f"tl.set('#cg{gi}', {{top:{SEAM}}}, {q(b + 0.1)});")
    tl.append(f"tl.set('#cg{gi}', {{visibility:'hidden'}}, {q(en)});")
hosts.append(f'<div id="captions" class="clip" data-start="0" data-duration="{DURATION}" data-track-index="5">{"".join(caps)}</div>')
css.append(f"""
  #captions {{ z-index:6; position:absolute; left:0; top:0; width:{W}px; height:{H}px; pointer-events:none; }}
  #captions .cg {{ position:absolute; left:100px; right:170px; transform:translateY(-50%); text-align:center; visibility:hidden;
    font:900 70px/1.15 {FONT}; color:#fff; -webkit-text-stroke:12px #000; paint-order:stroke fill; text-shadow:0 6px 18px rgba(0,0,0,.6); }}
  #captions .cw {{ display:inline-block; }}""")

# ---------- Âm thanh ----------
SFX_LEN = {"pop": 0.552, "whoosh": 1.022, "click": 0.336, "digits": 0.7, "wrong": 0.6}
SFX_VOL = {"pop": 0.6, "whoosh": 0.9, "click": 0.9, "digits": 0.5, "wrong": 0.5}
SFX_GAIN = 0.85   # người dùng muốn SFX nhỏ hơn 15% (2026-10-23)
aud = []
if (PUB / "audio/music.m4a").exists():   # nhạc nền tuỳ chọn: người dùng tự bỏ file vào public/audio/
    aud.append(f'<audio id="music" src="audio/music.m4a" data-start="0" data-duration="{DURATION}" data-track-index="10" data-volume="0.8"></audio>')
# cue = (vai, mốc hình): bộ SFX tự neo whoosh/impact theo điểm to nhất, pop/click theo điểm bắt đầu
kit_tags = sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(11, 40), log=WORK / "sfx_cues.json")
if kit_tags is not None:
    aud += kit_tags
else:   # không đọc được assets/sfx/kit.json: bộ âm cũ trong public/audio/
    last = {}
    for i, (n, t) in enumerate(sorted(sfx, key=lambda e: e[1])):
        d = min(SFX_LEN[n], DURATION - t)
        tr = next(k for k in range(11, 40) if last.get(k, -1) <= t)
        last[tr] = t + d
        aud.append(f'<audio id="sfx{i:02d}" src="audio/{n}.m4a" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{tr}" data-volume="{SFX_VOL[n] * SFX_GAIN:.3f}"></audio>')
hosts += aud

fonts = "\n".join(f'@font-face {{ font-family:"Be Vietnam Pro"; src:url("fonts/BeVietnamPro-{n}.ttf"); font-weight:{wt}; font-display:block; }}'
                  for n, wt in (("Medium", 500), ("Bold", 700), ("ExtraBold", 800), ("Black", 900)))
NL = "\n"
index = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8" />
<style>
{fonts}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; font-family:"Be Vietnam Pro", sans-serif; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#050806; }}
#panel {{ position:absolute; left:0; top:0; width:{W}px; height:{SEAM}px;
  background:radial-gradient(ellipse 70% 60% at 50% 45%, rgba(61,240,180,.16), transparent 70%), linear-gradient(#060b09, #0a120e);
  background-color:#060b09; }}
#panel::after {{ content:""; position:absolute; inset:0; background-image:linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px); background-size:60px 60px; }}
#video-wrap {{ z-index:2; position:absolute; left:0; top:{SEAM}px; width:{W}px; height:{H - SEAM}px; overflow:hidden; }}
#video-wrap video {{ width:100%; height:100%; object-fit:cover; object-position:50% 22%; transform-origin:30% 35%; }}
#seam {{ z-index:2; position:absolute; left:0; top:{SEAM - 2}px; width:{W}px; height:4px; background:{ACC}; box-shadow:0 0 24px {ACC}; }}
.scene {{ z-index:3; position:absolute; left:0; top:0; width:{W}px; height:{SEAM}px; overflow:hidden; }}
{NL.join(css)}
</style></head>
<body>
<div id="stage" data-composition-id="talking-head-recut" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
  <div id="panel"></div>
  <div id="video-wrap"><video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{DURATION}" data-track-index="1"></video></div>
  <div id="seam"></div>
{NL.join(hosts)}
  <script src="vendor/gsap.min.js"></script>
  <script>
  (function () {{
    const tl = window.gsap.timeline({{ paused: true }});
    {(NL + '    ').join(tl)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["talking-head-recut"] = tl;
  }})();
  </script>
</div>
</body></html>
"""
(PUB / "index.html").write_text(index)
print(f"{len(SCENES)} cảnh, {len(groups)} cụm phụ đề, {len(sfx)} SFX")
