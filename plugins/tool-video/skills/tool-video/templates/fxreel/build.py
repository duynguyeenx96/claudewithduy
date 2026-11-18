"""Concept fxreel (xem concepts/fxreel.md): "21 hiệu ứng trong 20 giây", mỗi hiệu ứng ~1s chạy ngay trên người nói,
cột checklist bên trái đánh dấu dần, giữa video là CTA "Comment EDIT".
Mẫu tham khảo: reel "20 video effects in 20 seconds, built by Claude" (2026-11-13).

Chỉ sửa phần CẤU HÌNH. Cần trong public/: aroll.mp4, person.webm (npx hyperframes remove-background),
tuỳ chọn plate.jpg (khung trống không người, cho hiệu ứng "tan biến"/"dolly"), transcript.json (mảng từ {text,start,end}).
Không có transcript thì chia đều thời lượng. Dựng: python3 build.py && npx hyperframes lint public
"""
import html
import json
import math
import os
import random
import re
import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).parent
PUB = WORK / "public"
W, H, FPS = 1080, 1920, 30

# ======================= CẤU HÌNH =======================
FACE = (640, 960)        # tâm mặt trong khung 1080x1920 (xem 1 khung A-roll)
HEAD_TOP = 730           # đỉnh đầu (y)
BODY = (330, 700, 980, 1900)   # hộp thân người (x0, y0, x1, y1) cho hạt "tan biến"
TITLE = ("21 hiệu ứng trong 20 giây", "Claude dựng")
KEYWORD = "EDIT"         # chữ người xem comment để nhận
CTA = (f"Comment {KEYWORD}", "để nhận bộ hiệu ứng", "+40 hiệu ứng nữa")
PAPER_NAME, PAPER_DATE = "Nhật Báo Reel", "SỐ ĐẶC BIỆT · THỨ SÁU 13/11/2026"
NOTE_VALUE = 500000
PANEL_BG, INK, ACCENT, PAPER = "#12281d", "#ffffff", "#e6ff5c", "#f1ece1"

# (khoá hiệu ứng, nhãn trên checklist = câu người nói, cụm để dò mốc trong transcript)
EFFECTS = [
    ("cursor",  "Con trỏ AI",      "con trỏ"),
    ("clones",  "Nhân bản",        "nhân bản"),
    ("dial",    "Mặt đồng hồ",     "đồng hồ"),
    ("keys",    "Bàn phím",        "bàn phím"),
    ("orbit",   "Vòng chữ",        "vòng chữ"),
    ("matrix",  "Ma trận",         "ma trận"),
    ("wall",    "Tường bài đăng",  "tường"),
    ("dive",    "Lặn vào chữ",     "lặn"),
    ("comment", f"Comment {KEYWORD}", "comment"),
    ("explode", "Bung lớp",        "bung"),
    ("sketch",  "Chữ phác thảo",   "phác thảo"),
    ("slice",   "Nhát chém",       "chém"),
    ("tags",    "Tháp nhãn",       "tháp"),
    ("focus",   "Đổi nét",         "đổi nét"),
    ("note",    "Tờ tiền",         "tờ tiền"),
    ("voice",   "Tin nhắn thoại",  "tin nhắn"),
    ("impact",  "Khung truyện",    "truyện"),
    ("dolly",   "Dolly zoom",      "dolly"),
    ("press",   "Lên báo",         "lên báo"),
    ("tear",    "Xé giấy",         "xé"),
    ("blow",    "Tan biến",        "tan biến"),
]
# Hiệu ứng che rộng màn hình: cột checklist tạm ẩn
WIDE = {"keys", "comment", "dial", "dive", "explode", "sketch", "slice", "note", "impact", "press", "tear", "wall", "matrix"}
SFX_GAIN = 0.85
MUSIC_VOL = 0.3
# =========================================================

FONT = '"Be Vietnam Pro", sans-serif'
FX, FY = FACE
ORIGIN = f"{FX}px {FY}px"
rnd = random.Random(7)
tl, sfx, behind, front, over, vids = [], [], [], [], [], []
_track = [10]


def q(t):
    return f"{round(t * FPS) / FPS:.4f}"


def esc(s):
    return html.escape(s)


def track():
    _track[0] += 1
    return _track[0]


def video(vid, src, t0, t1, style="", cls=""):
    """Video phụ (bản sao A-roll / người) chỉ chạy trong khoảng hiệu ứng, khớp giờ với A-roll gốc."""
    return (f'<video id="{vid}" class="{cls}" src="{src}" muted playsinline style="{style}" data-start="{q(t0)}" '
            f'data-duration="{q(t1 - t0)}" data-media-start="{q(t0)}" data-track-index="{track()}"></video>')


def show(sel, t0, t1, fade=0.12):
    tl.append(f"tl.set('{sel}', {{autoAlpha:1}}, {q(t0)});")
    if fade <= 0:   # cắt thẳng: không để lại khung nửa trong suốt giữa hai hiệu ứng (video-check: one_frame_flash)
        tl.append(f"tl.set('{sel}', {{autoAlpha:0}}, {q(t1)});")
    else:
        tl.append(f"tl.to('{sel}', {{autoAlpha:0, duration:{fade}}}, {q(t1 - fade)});")


# ---------- Mốc thời gian: dò cụm trong transcript, không có thì chia đều ----------
DURATION = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(PUB / "aroll.mp4")], capture_output=True, text=True).stdout.strip())
if os.environ.get("PREVIEW"):
    DURATION = min(DURATION, float(os.environ["PREVIEW"]))


def norm(s):
    return re.sub(r"[^\w]", "", s.lower())


starts = None
tp = WORK / "transcript.json"
if tp.exists():
    words = json.loads(tp.read_text())
    found, after = [], 0.0
    for _, _, say in EFFECTS:
        toks = [norm(t) for t in say.split()]
        hit = next((words[k]["start"] for k in range(len(words) - len(toks) + 1) if words[k]["start"] >= after
                    and all(norm(words[k + j]["text"]).startswith(toks[j]) for j in range(len(toks)))), None)
        found.append(hit)
        after = hit or after
    if sum(f is not None for f in found) >= len(EFFECTS) * 0.7:
        starts = found
        for i, s in enumerate(starts):   # cụm không thấy: nội suy giữa hai mốc thấy được
            if s is None:
                prev = next((starts[j] for j in range(i - 1, -1, -1) if starts[j] is not None), 0.0)
                nxt = next((starts[j] for j in range(i + 1, len(starts)) if starts[j] is not None), DURATION)
                starts[i] = prev + (nxt - prev) / 2
        starts = [max(0.0, s - 0.08) for s in starts]
if starts is None:
    step = DURATION / len(EFFECTS)
    starts = [i * step for i in range(len(EFFECTS))]
SPANS = [(starts[i], starts[i + 1] if i + 1 < len(starts) else DURATION) for i in range(len(starts))]


# ======================= HIỆU ỨNG =======================
def fx_cursor(i, t0, t1):
    bx, by, bw, bh = FX - 200, HEAD_TOP - 70, 400, 480
    front.append(f'''<div id="cu{i}" class="fx">
  <div id="cu{i}-box" class="cu-box" style="left:{bx}px;top:{by}px;width:{bw}px;height:{bh}px">
    <i style="left:-11px;top:-11px"></i><i style="right:-11px;top:-11px"></i><i style="left:-11px;bottom:-11px"></i><i style="right:-11px;bottom:-11px"></i>
  </div>
  <div id="cu{i}-size" class="cu-size" style="left:{bx}px;top:{by - 62}px">0 × 0</div>
  <div id="cu{i}-ptr" class="cu-ptr"><svg width="46" height="56" viewBox="0 0 23 28"><path d="M1 1 L1 22 L7 17 L11 27 L15 25 L11 16 L19 16 Z" fill="#fff" stroke="#111" stroke-width="1.6"/></svg>
    <span>Claude</span></div>
</div>''')
    show(f"#cu{i}", t0, t1)
    tl.append(f"tl.fromTo('#cu{i}-ptr', {{x:{bx + 260}, y:{by + bh + 260}}}, {{x:{bx}, y:{by}, duration:0.25, ease:'power2.out'}}, {q(t0)});")
    tl.append(f"tl.to('#cu{i}-ptr', {{x:{bx + bw}, y:{by + bh}, duration:0.4, ease:'power2.inOut'}}, {q(t0 + 0.27)});")
    tl.append(f"tl.fromTo('#cu{i}-box', {{scaleX:0.02, scaleY:0.02, autoAlpha:0}}, {{scaleX:1, scaleY:1, autoAlpha:1, duration:0.4, ease:'power2.inOut'}}, {q(t0 + 0.27)});")
    tl.append(f"(() => {{ const o={{v:0}}, el=document.getElementById('cu{i}-size'); tl.fromTo(o, {{v:0}}, {{v:1, duration:0.4, ease:'power2.inOut', "
              f"onUpdate:() => {{ el.textContent = Math.round({bw}*o.v) + ' × ' + Math.round({bh}*o.v); }}}}, {q(t0 + 0.27)}); }})();")
    sfx.append(("click", t0 + 0.27))


def fx_clones(i, t0, t1):
    offs = [-430, -215, 215, 430]
    els = []
    for k, dx in enumerate(offs):
        els.append(f'<div class="clone" id="cl{i}-{k}" style="transform:translateX({dx}px) scale(0.86)">'
                   f'{video(f"clv{i}-{k}", "person.webm", t0, t1, "filter:brightness(.82)")}</div>')
    behind.append(f'<div id="cl{i}" class="fx">{"".join(els)}</div>')
    show(f"#cl{i}", t0, t1)
    for k, dx in enumerate(sorted(offs, key=abs)):
        idx = offs.index(dx)
        tl.append(f"tl.fromTo('#cl{i}-{idx}', {{x:0, opacity:0}}, {{x:{dx}, opacity:1, duration:0.3, ease:'back.out(1.6)'}}, {q(t0 + k * 0.07)});")
        sfx.append(("pop", t0 + k * 0.07))


def fx_dial(i, t0, t1):
    cx, cy, r = FX, FY - 40, 560
    nums = "".join(f'<text x="{cx + (r - 90) * math.sin(math.radians(k * 30)):.0f}" y="{cy - (r - 90) * math.cos(math.radians(k * 30)) + 30:.0f}" '
                   f'text-anchor="middle">{k if k else 12}</text>' for k in range(12))
    ticks = "".join(f'<line x1="{cx + r * math.sin(math.radians(k * 6)):.1f}" y1="{cy - r * math.cos(math.radians(k * 6)):.1f}" '
                    f'x2="{cx + (r - (34 if k % 5 == 0 else 16)) * math.sin(math.radians(k * 6)):.1f}" '
                    f'y2="{cy - (r - (34 if k % 5 == 0 else 16)) * math.cos(math.radians(k * 6)):.1f}"/>' for k in range(60))
    days = "".join(f'<text x="{cx + (r - 190) * math.sin(math.radians(k * 60 + 15)):.0f}" y="{cy - (r - 190) * math.cos(math.radians(k * 60 + 15)):.0f}" '
                   f'class="dd" text-anchor="middle" transform="rotate({k * 60 + 15} {cx + (r - 190) * math.sin(math.radians(k * 60 + 15)):.0f} '
                   f'{cy - (r - 190) * math.cos(math.radians(k * 60 + 15)):.0f})">ngày</text>' for k in range(6))
    behind.append(f'''<div id="dl{i}" class="fx paper" data-layout-allow-occlusion>
  <svg id="dl{i}-s" class="full" viewBox="0 0 {W} {H}"><g id="dl{i}-g" class="dial">
    <circle cx="{cx}" cy="{cy}" r="{r}"/><circle cx="{cx}" cy="{cy}" r="{r - 150}"/>{ticks}{nums}{days}</g></svg>
</div>''')
    tl.append(f"tl.set('#dl{i}', {{autoAlpha:1}}, {q(t0)});")
    tl.append(f"tl.fromTo('#dl{i}', {{clipPath:'polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)'}}, "
              f"{{clipPath:'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', duration:0.25, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"tl.fromTo('#dl{i}-g', {{rotation:40, svgOrigin:'{cx} {cy}'}}, {{rotation:-25, svgOrigin:'{cx} {cy}', duration:{t1 - t0:.2f}, ease:'power2.out'}}, {q(t0)});")
    tl.append(f"tl.to('#dl{i}', {{clipPath:'polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)', duration:0.18, ease:'power2.in'}}, {q(t1 - 0.18)});")
    tl.append(f"tl.set('#dl{i}', {{autoAlpha:0}}, {q(t1)});")
    sfx.append(("whoosh", t0 + 0.1))


def fx_keys(i, t0, t1, label):
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    keys = ""
    for r_, row in enumerate(rows):
        keys += f'<div class="kr" style="padding:0 {r_ * 26}px">' + "".join(f'<b id="k{i}-{c}">{c}</b>' for c in row) + "</div>"
    keys += '<div class="kr"><b class="wide2">123</b><b class="space">dấu cách</b><b class="wide2">xong</b></div>'
    word = label.lower()
    sugg = [word.split()[0], word, word.split()[-1] + "?"]
    front.append(f'''<div id="kb{i}" class="fx">
  <div class="kb-input" id="kb{i}-in"><span id="kb{i}-t"></span><i class="caret"></i></div>
  <div class="kb" id="kb{i}-k"><div class="kb-sug">{"".join(f'<span id="kb{i}-s{k}">{esc(s)}</span>' for k, s in enumerate(sugg))}</div>{keys}</div>
</div>''')
    show(f"#kb{i}", t0, t1)
    tl.append(f"tl.fromTo('#kb{i}-k', {{y:520}}, {{y:0, duration:0.25, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"tl.fromTo('#kb{i}-in', {{y:520}}, {{y:0, duration:0.25, ease:'power3.out'}}, {q(t0)});")
    n = len(label)
    span = max(0.3, (t1 - t0) - 0.45)
    tl.append(f"(() => {{ const s={json.dumps(label)}, o={{v:0}}, el=document.getElementById('kb{i}-t'); "
              f"tl.fromTo(o, {{v:0}}, {{v:{n}, duration:{span:.2f}, ease:'none', onUpdate:() => {{ el.textContent = s.slice(0, Math.round(o.v)); }}}}, {q(t0 + 0.25)}); }})();")
    base = "".join(c for c in __import__("unicodedata").normalize("NFD", label.lower()) if c.isascii() and c.isalpha())
    for k, c in enumerate(base[:10]):
        tk = t0 + 0.25 + span * (k + 0.5) / len(base)
        tl.append(f"tl.fromTo('#k{i}-{c}', {{backgroundColor:'#9aa0ab'}}, {{backgroundColor:'#ffffff', duration:0.12}}, {q(tk)});")
        if k % 2 == 0:
            sfx.append(("typing", tk))
    tl.append(f"tl.fromTo('#kb{i}-s1', {{backgroundColor:'rgba(255,255,255,0)'}}, {{backgroundColor:'#ffffff', duration:0.1}}, {q(t1 - 0.25)});")


def fx_orbit(i, t0, t1, label):
    txt = (label.upper() + " · ") * 2
    letters = [c for c in txt]
    n = len(letters)
    cx, cy, rx, ry = FX, HEAD_TOP + 70, 330, 80
    for layer, lst in (("b", behind), ("f", front)):
        spans = "".join(f'<span id="or{i}{layer}{k}">{esc(c)}</span>' for k, c in enumerate(letters))
        lst.append(f'<div id="or{i}{layer}" class="fx orbit" data-layout-allow-occlusion>{spans}</div>')
        show(f"#or{i}{layer}", t0, t1)
    tl.append(f"""(() => {{ const o={{a:0}}, n={n};
      const B=[...Array(n)].map((_,k)=>document.getElementById('or{i}b'+k)), F=[...Array(n)].map((_,k)=>document.getElementById('or{i}f'+k));
      const draw=()=>{{ for(let k=0;k<n;k++){{ const a=o.a+k*2*Math.PI/n, s=Math.sin(a), x={cx}+{rx}*Math.cos(a), y={cy}+{ry}*s-(x-{cx})*0.06;
        const sc=0.75+0.35*(s+1)/2, tf='translate('+x+'px,'+y+'px) translate(-50%,-50%) scale('+sc+') rotateY('+(-Math.cos(a)*30)+'deg)';
        B[k].style.transform=tf; F[k].style.transform=tf; F[k].style.opacity = s>0?1:0; B[k].style.opacity = s>0?0:0.75; }} }};
      draw(); tl.fromTo(o, {{a:0}}, {{a:{-2.2 * math.pi:.3f}, duration:{t1 - t0:.2f}, ease:'none', onUpdate:draw}}, {q(t0)}); }})();""")
    sfx.append(("whoosh", t0 + 0.12))


def fx_matrix(i, t0, t1):
    cols = []
    for c in range(18):
        chars = "".join(rnd.choice("01アイウエオカキクケコ{}<>=+*#$ABCDEF") + "<br>" for _ in range(40))
        cols.append(f'<div class="mx-col" id="mx{i}-{c}" style="left:{c * 60}px;opacity:{0.35 + rnd.random() * 0.6:.2f}">{chars}</div>')
    behind.append(f'<div id="mx{i}" class="fx mx" data-layout-allow-occlusion>{"".join(cols)}</div>')
    front.append(f'<div id="mx{i}-scan" class="fx scan"></div>')
    show(f"#mx{i}", t0, t1, 0)
    show(f"#mx{i}-scan", t0, t1, 0)
    for c in range(18):
        sp = 400 + rnd.random() * 700
        tl.append(f"tl.fromTo('#mx{i}-{c}', {{y:{-1200 - rnd.random() * 600:.0f}}}, {{y:'+={sp * (t1 - t0):.0f}', duration:{t1 - t0:.2f}, ease:'none'}}, {q(t0)});")
    tl.append(f"tl.set('#v-person', {{filter:'grayscale(1) sepia(1) hue-rotate(65deg) saturate(5) contrast(1.35) brightness(.95)'}}, {q(t0)});")
    tl.append(f"tl.set('#v-person', {{filter:'none'}}, {q(t1)});")
    sfx.append(("glitch", t0))


def thumbs():
    """6 khung A-roll nhỏ cho tường bài đăng (tạo 1 lần)."""
    out = []
    for k in range(6):
        p = PUB / f"wall{k}.jpg"
        if not p.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{DURATION * (k + 0.5) / 6:.2f}", "-i", str(PUB / "aroll.mp4"),
                            "-frames:v", "1", "-vf", "scale=180:-1", str(p)])
        out.append(p.name)
    return out


def fx_wall(i, t0, t1):
    imgs = thumbs()
    cols, rows, sz = 9, 16, 120
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    order = sorted(cells, key=lambda cr: math.hypot(cr[0] * sz + 60 - FX, cr[1] * sz + 60 - FY) + rnd.random() * 260)
    tiles = "".join(f'<i id="wl{i}-{c}-{r}" style="left:{c * sz}px;top:{r * sz}px;background-image:url({imgs[(c * 7 + r * 3) % 6]});'
                    f'filter:hue-rotate({rnd.randint(-40, 40)}deg) saturate(1.3)"></i>' for c, r in cells)
    behind.append(f'<div id="wl{i}" class="fx wall" data-layout-allow-occlusion>{tiles}</div>')
    front.append(f'<div id="wl{i}-c" class="fx wl-count"><span>BÀI ĐĂNG</span><b id="wl{i}-n">0</b></div>')
    show(f"#wl{i}", t0, t1)
    show(f"#wl{i}-c", t0, t1)
    span = (t1 - t0) * 0.75
    for k, (c, r) in enumerate(order):
        tl.append(f"tl.fromTo('#wl{i}-{c}-{r}', {{scale:0, opacity:0}}, {{scale:1, opacity:1, duration:0.12}}, {q(t0 + span * k / len(order))});")
    tl.append(f"(() => {{ const o={{v:0}}, el=document.getElementById('wl{i}-n'); tl.fromTo(o, {{v:0}}, {{v:1403, duration:{span:.2f}, ease:'power1.out', "
              f"onUpdate:() => {{ el.textContent = Math.round(o.v).toLocaleString('vi-VN'); }}}}, {q(t0)}); }})();")
    sfx.append(("riser", t1 - 0.1))


def fx_dive(i, t0, t1, label):
    word = label.split()[0].upper()   # "LẶN"
    over.append(f'''<div id="dv{i}" class="fx">
  <svg class="full" viewBox="0 0 {W} {H}"><defs><mask id="dv{i}-m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
    <rect width="{W}" height="{H}" fill="#fff"/><g id="dv{i}-g"><text id="dv{i}-t" x="{W / 2}" y="1240" text-anchor="middle" class="dv-t">{esc(word)}</text></g>
  </mask></defs><rect width="{W}" height="{H}" fill="{PAPER}" mask="url(#dv{i}-m)"/></svg>
</div>''')
    tl.append(f"tl.set('#dv{i}', {{autoAlpha:1}}, {q(t0)});")
    tl.append(f"""(() => {{ const g=document.getElementById('dv{i}-g'), t=document.getElementById('dv{i}-t'), o={{s:0.7}};
      let ox={W / 2}, oy=1000;
      try {{ const b=t.getBBox(); const L=t.getExtentOfChar ? t.getExtentOfChar(0) : b; ox=L.x+L.width*0.2; oy=L.y+L.height*0.62; }} catch(e) {{}}
      const draw=()=>g.setAttribute('transform','translate('+ox+' '+oy+') scale('+o.s+') translate('+(-ox)+' '+(-oy)+')');
      draw();
      tl.fromTo(o, {{s:0.7}}, {{s:1, duration:0.2, ease:'back.out(2)', onUpdate:draw}}, {q(t0)});
      tl.to(o, {{s:60, duration:{max(0.3, t1 - t0 - 0.3):.2f}, ease:'power4.in', onUpdate:draw}}, {q(t0 + 0.25)}); }})();""")
    tl.append(f"tl.set('#dv{i}', {{autoAlpha:0}}, {q(t1)});")
    sfx.append(("whoosh", t1 - 0.12))


def fx_comment(i, t0, t1):
    front.append(f'''<div id="cm{i}" class="fx">
  <div class="cm-card" id="cm{i}-a"><div class="cm-name">Bạn</div><div class="cm-line"><span id="cm{i}-t" class="cm-type">Viết bình luận...</span><span class="cm-btn">Đăng</span></div></div>
  <div class="cm-card reply" id="cm{i}-b"><div class="cm-name">Kênh</div><div class="cm-line">Gửi bạn rồi nhé, {esc(CTA[2])}</div></div>
  <div class="cta">{"".join(f'<div><span id="cm{i}-p{k}">{esc(s)}</span></div>' for k, s in enumerate(CTA))}</div>
</div>''')
    show(f"#cm{i}", t0, t1, 0.15)
    tl.append(f"tl.fromTo('#cm{i}-a', {{y:-140, opacity:0}}, {{y:0, opacity:1, duration:0.3, ease:'back.out(1.8)'}}, {q(t0)});")
    tl.append(f"(() => {{ const s={json.dumps(KEYWORD)}, o={{v:0}}, el=document.getElementById('cm{i}-t'); "
              f"tl.fromTo(o, {{v:0}}, {{v:s.length, duration:0.35, ease:'none', onUpdate:() => {{ const n=Math.round(o.v); el.textContent = n ? s.slice(0,n) : 'Viết bình luận...'; "
              f"el.style.color = n ? '#111' : '#888'; }}}}, {q(t0 + 0.3)}); }})();")
    tl.append(f"tl.fromTo('#cm{i}-b', {{y:-40, opacity:0}}, {{y:0, opacity:1, duration:0.25, ease:'power3.out'}}, {q(t0 + 0.75)});")
    sfx.append(("chat", t0))
    sfx.append(("ding", t0 + 0.75))
    for k in range(3):
        tk = t0 + 0.3 + k * min(0.3, (t1 - t0 - 0.5) / 3)
        tl.append(f"tl.fromTo('#cm{i}-p{k}', {{scale:0.4, opacity:0}}, {{scale:1, opacity:1, duration:0.25, ease:'back.out(2.4)'}}, {q(tk)});")


def fx_explode(i, t0, t1, label):
    front.append(f'<div id="ex{i}" class="fx ex-label" data-layout-allow-overflow>{esc(label.lower())}</div>')
    zs = {"#cam-bg": -320, "#behind": -160, "#cam-fg": 0, "#front": 180}
    d = t1 - t0
    tl.append(f"tl.to('#world', {{rotationY:-34, rotationX:10, scale:0.62, duration:0.3, ease:'power3.out'}}, {q(t0)});")
    for sel, z in zs.items():
        tl.append(f"tl.to('{sel}', {{z:{z}, duration:0.3, ease:'power3.out'}}, {q(t0)});")
        tl.append(f"tl.to('{sel}', {{z:0, duration:0.22, ease:'power2.in'}}, {q(t1 - 0.22)});")
    tl.append(f"tl.to('#world', {{rotationY:-20, duration:{max(0.1, d - 0.55):.2f}, ease:'none'}}, {q(t0 + 0.3)});")
    tl.append(f"tl.to('#world', {{rotationY:0, rotationX:0, scale:1, duration:0.22, ease:'power2.in'}}, {q(t1 - 0.22)});")
    tl.append(f"tl.fromTo('#ex{i}', {{autoAlpha:0, z:300}}, {{autoAlpha:1, z:300, duration:0.15}}, {q(t0 + 0.1)});")
    tl.append(f"tl.to('#ex{i}', {{autoAlpha:0, duration:0.12}}, {q(t1 - 0.2)});")
    sfx.append(("whoosh", t0 + 0.1))


def fx_sketch(i, t0, t1, label):
    a, b = (label.split(" ", 1) + [""])[:2]
    lines = "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(300, H, 70))
    behind.append(f'''<div id="sk{i}" class="fx paper" data-layout-allow-occlusion>
  <svg class="full" viewBox="0 0 {W} {H}"><g class="ruled">{lines}</g>
    <text id="sk{i}-a" x="140" y="400" class="sk sk-s">{esc(a.lower())}</text>
    <text id="sk{i}-b" x="{W / 2}" y="640" text-anchor="middle" class="sk sk-b">{esc(b.lower())}</text></svg>
</div>''')
    tl.append(f"tl.set('#sk{i}', {{autoAlpha:1}}, {q(t0)});")
    tl.append(f"tl.fromTo('#sk{i}', {{clipPath:'inset(0% 0% 100% 0%)'}}, {{clipPath:'inset(0% 0% 0% 0%)', duration:0.22, ease:'power3.out'}}, {q(t0)});")
    for k, (el, dt) in enumerate(((f"#sk{i}-a", 0.15), (f"#sk{i}-b", 0.35))):
        tl.append(f"tl.fromTo('{el}', {{strokeDashoffset:3000, fillOpacity:0}}, {{strokeDashoffset:0, duration:{max(0.3, t1 - t0 - 0.6):.2f}, ease:'power1.inOut'}}, {q(t0 + dt)});")
        tl.append(f"tl.to('{el}', {{fillOpacity:1, duration:0.2}}, {q(t1 - 0.4)});")
    tl.append(f"tl.to('#sk{i}', {{autoAlpha:0, duration:0.12}}, {q(t1 - 0.12)});")
    sfx.append(("paper", t0 + 0.05))


def fx_slice(i, t0, t1):
    a = f"polygon(0px 0px, {W}px 0px, {W}px 760px, 0px 1180px)"
    b = f"polygon(0px 1180px, {W}px 760px, {W}px {H}px, 0px {H}px)"
    over.append(f'''<div id="sl{i}" class="fx sl">
  <div class="sl-half" id="sl{i}-a" style="clip-path:{a}">{video(f"slv{i}a", "aroll.mp4", t0, t1)}</div>
  <div class="sl-half" id="sl{i}-b" style="clip-path:{b}">{video(f"slv{i}b", "aroll.mp4", t0, t1)}</div>
  <div class="sl-line" id="sl{i}-l"></div>
</div>''')
    show(f"#sl{i}", t0, t1, 0.05)
    ang = math.degrees(math.atan2(760 - 1180, W))
    tl.append(f"tl.set('#sl{i}-l', {{rotation:{ang:.2f}, transformOrigin:'0% 50%'}}, 0);")
    tl.append(f"tl.fromTo('#sl{i}-l', {{scaleX:0, opacity:1}}, {{scaleX:1, duration:0.12, ease:'power4.out'}}, {q(t0)});")
    tl.append(f"tl.to('#sl{i}-l', {{opacity:0, duration:0.15}}, {q(t0 + 0.15)});")
    tl.append(f"tl.fromTo('#sl{i}-a', {{x:0, y:0, rotation:0}}, {{x:-70, y:-50, rotation:-3, duration:0.3, ease:'power3.out'}}, {q(t0 + 0.12)});")
    tl.append(f"tl.fromTo('#sl{i}-b', {{x:0, y:0, rotation:0}}, {{x:70, y:50, rotation:2, duration:0.3, ease:'power3.out'}}, {q(t0 + 0.12)});")
    tl.append(f"tl.to(['#sl{i}-a','#sl{i}-b'], {{x:0, y:0, rotation:0, duration:0.2, ease:'power2.in'}}, {q(t1 - 0.22)});")
    sfx.append(("slice", t0 + 0.05))


def fx_tags(i, t0, t1):
    prev = [lab for _, lab, _ in EFFECTS[max(0, i - 5):i]][::-1]
    chips = "".join(f'<div class="tg" id="tg{i}-{k}" style="top:{HEAD_TOP - 30 - 70 * (k + 1)}px;transform:rotate({rnd.uniform(-6, 6):.1f}deg)">'
                    f'{esc(s)}</div>' for k, s in enumerate(prev))
    front.append(f'<div id="tg{i}" class="fx tgs">{chips}</div>')
    show(f"#tg{i}", t0, t1)
    for k in range(len(prev)):
        tl.append(f"tl.fromTo('#tg{i}-{k}', {{y:-900, x:{rnd.randint(-40, 40)}}}, {{y:0, x:0, duration:0.35, ease:'bounce.out'}}, {q(t0 + k * 0.09)});")
        sfx.append(("pop", t0 + k * 0.09 + 0.25)) if k % 2 == 0 else None
    tl.append(f"tl.to('#tg{i} .tg', {{x:700, rotation:40, duration:0.25, ease:'power2.in', stagger:0.03}}, {q(t1 - 0.3)});")


def fx_focus(i, t0, t1):
    s = 150
    corners = "".join(f'<i class="fc {c}"></i>' for c in ("tl", "tr", "bl", "br"))
    front.append(f'<div id="fo{i}" class="fx"><div class="fc-box" id="fo{i}-b" style="left:{FX - s}px;top:{FY - s - 40}px;width:{2 * s}px;height:{2 * s + 60}px">{corners}</div></div>')
    show(f"#fo{i}", t0, t1)
    tl.append(f"tl.fromTo('#fo{i}-b', {{scale:1.6, opacity:0}}, {{scale:1, opacity:1, duration:0.2, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"tl.fromTo('#v-bg', {{filter:'blur(0px)'}}, {{filter:'blur(16px)', duration:0.3, ease:'power2.out'}}, {q(t0)});")
    mid = t0 + (t1 - t0) * 0.6
    tl.append(f"tl.to('#v-bg', {{filter:'blur(0px)', duration:0.15}}, {q(mid)});")
    tl.append(f"tl.to('#v-person', {{filter:'blur(10px)', duration:0.15}}, {q(mid)});")
    tl.append(f"tl.to('#v-person', {{filter:'blur(0px)', duration:0.12}}, {q(t1 - 0.12)});")
    tl.append(f"tl.set(['#v-bg','#v-person'], {{filter:'none'}}, {q(t1)});")
    sfx.append(("shutter", t0 + 0.1))


def fx_note(i, t0, t1):
    v = video(f"ntv{i}", "aroll.mp4", t0, t1, f"transform-origin:{ORIGIN};transform:scale(1.7) translate({540 - FX}px,{860 - FY}px)")
    val = f"{NOTE_VALUE:,}".replace(",", ".")
    over.append(f'''<div id="nt{i}" class="fx note">
  <div class="nt-frame"><div class="nt-guil"></div>
    <div class="nt-corner" style="left:60px;top:40px">{val}</div><div class="nt-corner" style="right:60px;top:40px">{val}</div>
    <div class="nt-serial">AI 2026 1113 VN</div>
    <div class="nt-oval">{v}<div class="nt-eng"></div><div class="nt-tint"></div></div>
    <div class="nt-val" id="nt{i}-v">0</div>
    <div class="nt-sub">TỜ TIỀN CỦA CLAUDE</div>
    <div class="nt-corner" style="left:60px;bottom:40px">{val}</div><div class="nt-corner" style="right:60px;bottom:40px">{val}</div>
  </div>
</div>''')
    show(f"#nt{i}", t0, t1, 0.1)
    tl.append(f"tl.fromTo('#nt{i} .nt-frame', {{scale:1.25, rotation:-8}}, {{scale:1, rotation:0, duration:0.3, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"(() => {{ const o={{v:0}}, el=document.getElementById('nt{i}-v'); tl.fromTo(o, {{v:0}}, {{v:{NOTE_VALUE}, duration:{max(0.3, t1 - t0 - 0.3):.2f}, ease:'power2.out', "
              f"onUpdate:() => {{ el.textContent = Math.round(o.v).toLocaleString('vi-VN'); }}}}, {q(t0 + 0.1)}); }})();")
    sfx.append(("cash", t0 + 0.1))


def fx_voice(i, t0, t1, label):
    bars = "".join(f'<i id="vn{i}-{k}"></i>' for k in range(30))
    front.append(f'''<div id="vn{i}" class="fx"><div class="vn" id="vn{i}-b">
  <div class="vn-play"><svg width="34" height="34" viewBox="0 0 10 10"><path d="M2 1 L9 5 L2 9 Z" fill="#fff"/></svg></div>
  <div class="vn-wave">{bars}</div><div class="vn-time" id="vn{i}-t">0:00</div></div>
  <div class="vn-label">{esc(label)}</div></div>''')
    show(f"#vn{i}", t0, t1)
    tl.append(f"tl.fromTo('#vn{i}-b', {{scale:0.3, opacity:0, transformOrigin:'0% 50%'}}, {{scale:1, opacity:1, duration:0.25, ease:'back.out(2)'}}, {q(t0)});")
    tl.append(f"""(() => {{ const o={{p:0}}, bs=[...Array(30)].map((_,k)=>document.getElementById('vn{i}-'+k)), tt=document.getElementById('vn{i}-t');
      const draw=()=>{{ bs.forEach((b,k)=>{{ const h=14+46*Math.abs(Math.sin(k*0.9+o.p*9)*Math.sin(k*0.37+o.p*4)); b.style.height=h+'px';
        b.style.background = k/30 < o.p ? '{ACCENT}' : 'rgba(255,255,255,.55)'; }}); tt.textContent='0:0'+Math.min(9,Math.floor(o.p*{t1 - t0:.2f}*3)); }};
      draw(); tl.fromTo(o, {{p:0}}, {{p:1, duration:{t1 - t0:.2f}, ease:'none', onUpdate:draw}}, {q(t0)}); }})();""")
    sfx.append(("chat", t0, 1))


def fx_impact(i, t0, t1, label):
    rays = []
    for k in range(64):
        a = 2 * math.pi * k / 64 + rnd.uniform(-0.03, 0.03)
        w = rnd.uniform(0.006, 0.02)
        r0 = rnd.uniform(380, 560)
        p = [(FX + r0 * math.cos(a), FY - 60 + r0 * math.sin(a)), (FX + 2200 * math.cos(a - w), FY + 2200 * math.sin(a - w)),
             (FX + 2200 * math.cos(a + w), FY + 2200 * math.sin(a + w))]
        rays.append(f'<polygon points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in p)}"/>')
    word = {"Khung truyện": "BÙM!"}.get(label, label.upper())
    over.append(f'''<div id="im{i}" class="fx im">
  <svg class="full" viewBox="0 0 {W} {H}"><g fill="#111">{"".join(rays)}</g></svg>
  <div class="im-p" id="im{i}-p">{video(f"imv{i}", "person.webm", t0, t1, "filter:url(#thr)")}</div>
  <div class="im-word" id="im{i}-w">{esc(word)}</div>
</div>''')
    show(f"#im{i}", t0, t1, 0.05)
    tl.append(f"tl.fromTo('#im{i}-p', {{scale:1.15}}, {{scale:1.05, duration:{t1 - t0:.2f}, ease:'power2.out'}}, {q(t0)});")
    tl.append(f"tl.fromTo('#im{i}-w', {{scale:2.2, opacity:0}}, {{scale:1, opacity:1, duration:0.18, ease:'power4.out'}}, {q(t0 + 0.08)});")
    for k in range(5):
        tl.append(f"tl.to('#im{i}', {{x:{rnd.choice([-14, 14, -9, 9])}, y:{rnd.choice([-10, 10, -6, 6])}, duration:0.03}}, {q(t0 + 0.1 + k * 0.04)});")
    tl.append(f"tl.to('#im{i}', {{x:0, y:0, duration:0.03}}, {q(t0 + 0.32)});")
    sfx.append(("impact", t0 + 0.03))


def fx_dolly(i, t0, t1):
    d = t1 - t0
    tl.append(f"tl.set(CAMS, {{scale:1.3}}, {q(t0)});")
    tl.append(f"tl.to('#cam-bg', {{scale:1.0, duration:{d - 0.1:.2f}, ease:'power1.inOut'}}, {q(t0)});")
    tl.append(f"tl.to('#cam-fg', {{scale:1.45, duration:{d - 0.1:.2f}, ease:'power1.inOut'}}, {q(t0)});")
    tl.append(f"tl.set(CAMS, {{scale:1}}, {q(t1)});")
    sfx.append(("riser", t1 - 0.05))


def fx_press(i, t0, t1):
    v = video(f"prv{i}", "aroll.mp4", t0, t1, f"transform-origin:{ORIGIN};transform:scale(1.35) translate({540 - FX}px,{760 - FY}px)")
    filler = ("Hiệu ứng được dựng hoàn toàn bằng code, mỗi cảnh một giây, người nói chỉ cần đọc tên. "
              "Lớp chữ nằm sau người, lớp đồ hoạ nằm trước, khung hình đổi liên tục để giữ mắt người xem. ") * 3
    over.append(f'''<div id="pr{i}" class="fx press"><div class="pr-page" id="pr{i}-p">
  <div class="pr-mast">{esc(PAPER_NAME)}</div>
  <div class="pr-rule">{esc(PAPER_DATE)}</div>
  <div class="pr-head">{esc(TITLE[0].upper())}</div>
  <div class="pr-sub">{esc(TITLE[1])}.</div>
  <div class="pr-body"><div class="pr-col">{esc(filler)}</div>
    <div class="pr-photo">{v}<div class="pr-dots"></div></div><div class="pr-col">{esc(filler)}</div></div>
</div></div>''')
    show(f"#pr{i}", t0, t1, 0.08)
    tl.append(f"tl.fromTo('#pr{i}-p', {{scale:0.05, rotation:-720}}, {{scale:1, rotation:-2, duration:0.4, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"tl.to('#pr{i}-p', {{scale:1.06, rotation:0, duration:{max(0.1, t1 - t0 - 0.45):.2f}, ease:'none'}}, {q(t0 + 0.4)});")
    sfx.append(("paper", t0))
    sfx.append(("impact", t0 + 0.38, 2))


def fx_tear(i, t0, t1, label):
    pts = []
    y = 0
    while y < H:
        pts.append((W / 2 + rnd.uniform(-38, 38), y))
        y += rnd.uniform(40, 90)
    pts.append((W / 2, H))
    edge = ", ".join(f"{x:.0f}px {y:.0f}px" for x, y in pts)
    redge = ", ".join(f"{x:.0f}px {y:.0f}px" for x, y in reversed(pts))
    left = f"polygon(0px 0px, {edge}, 0px {H}px)"
    right = f"polygon({W}px 0px, {W}px {H}px, {redge})"
    lines = "".join(f'<line x1="0" y1="{yy}" x2="{W}" y2="{yy}"/>' for yy in range(300, H, 70))
    sheet = f'<svg class="full" viewBox="0 0 {W} {H}"><g class="ruled">{lines}</g></svg><div class="tr-word">{esc(label.upper())}</div>'
    over.append(f'''<div id="tr{i}" class="fx">
  <div class="tr-half paper" id="tr{i}-l" style="clip-path:{left}">{sheet}</div>
  <div class="tr-half paper" id="tr{i}-r" style="clip-path:{right}">{sheet}</div>
</div>''')
    show(f"#tr{i}", t0, t1, 0.05)
    tl.append(f"tl.fromTo(['#tr{i}-l','#tr{i}-r'], {{y:-{H}}}, {{y:0, duration:0.2, ease:'power3.out'}}, {q(t0)});")
    rip = t0 + max(0.35, (t1 - t0) * 0.45)
    tl.append(f"tl.to('#tr{i}-l', {{x:-760, rotation:-12, duration:{t1 - rip:.2f}, ease:'power2.in', transformOrigin:'0% 100%'}}, {q(rip)});")
    tl.append(f"tl.to('#tr{i}-r', {{x:760, rotation:12, duration:{t1 - rip:.2f}, ease:'power2.in', transformOrigin:'100% 100%'}}, {q(rip)});")
    sfx.append(("paper", t0))
    sfx.append(("rip", rip + 0.08))


def fx_blow(i, t0, t1):
    plate = (PUB / "plate.jpg").exists()
    x0, y0, x1, y1 = BODY
    cols = ["#5e4330", "#7a5a43", "#c9997c", "#e0b394", "#2a2a2a", "#3a5bd9"]
    parts = []
    for k in range(170):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        s = rnd.uniform(5, 15)
        parts.append((k, x, y, s, rnd.choice(cols)))
    front.append(f'<div id="bw{i}" class="fx">' + "".join(
        f'<i id="bw{i}-{k}" class="pt" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.0f}px;height:{s:.0f}px;background:{c}"></i>'
        for k, x, y, s, c in parts) + "</div>")
    if plate:
        behind.append(f'<div id="bwp{i}" class="fx"><img src="plate.jpg" class="full" style="object-fit:cover"></div>')
        show(f"#bwp{i}", t0 + 0.05, DURATION + 1)
    else:   # chưa có khung trống: làm mờ + tối nền để bóng người trong A-roll chìm đi
        tl.append(f"tl.to('#v-bg', {{filter:'blur(28px) brightness(.55)', duration:0.3}}, {q(t0)});")
    d = t1 - t0
    tl.append(f"tl.set('#bw{i}', {{autoAlpha:1}}, {q(t0)});")
    tl.append(f"tl.fromTo('#cam-fg', {{'--m':'-30%'}}, {{'--m':'130%', duration:{d * 0.8:.2f}, ease:'power1.in'}}, {q(t0)});")
    for k, x, y, s, c in parts:
        st = t0 + d * 0.8 * (x - x0) / (x1 - x0)
        tl.append(f"tl.fromTo('#bw{i}-{k}', {{opacity:0, x:0, y:0}}, {{opacity:1, duration:0.04}}, {q(st)});")
        tl.append(f"tl.to('#bw{i}-{k}', {{x:{rnd.uniform(220, 640):.0f}, y:{rnd.uniform(-420, -60):.0f}, rotation:{rnd.randint(-180, 180)}, "
                  f"opacity:0, duration:{rnd.uniform(0.5, 0.9):.2f}, ease:'power1.out'}}, {q(st + 0.04)});")
    sfx.append(("magic", t0 + 0.05, 1))


FX_FN = {k[3:]: v for k, v in list(globals().items()) if k.startswith("fx_")}
LABELED = {"keys", "orbit", "dive", "explode", "sketch", "voice", "impact", "tear"}

for i, ((key, label, _), (t0, t1)) in enumerate(zip(EFFECTS, SPANS)):
    t1 = min(t1, DURATION)
    if t1 - t0 < 0.3:
        continue
    fn = FX_FN[key]
    fn(i, t0, t1, label) if key in LABELED else fn(i, t0, t1)

# ---------- Tiêu đề hook ----------
hook_end = SPANS[min(1, len(SPANS) - 1)][1]
front.append(f'<div id="title" class="fx title"><div><span>{esc(TITLE[0])}</span></div><div><span class="t2">{esc(TITLE[1])}</span></div></div>')
tl.append("tl.set('#title', {autoAlpha:1}, 0);")
tl.append("tl.fromTo('#title span', {y:30, opacity:0}, {y:0, opacity:1, duration:0.3, stagger:0.12, ease:'power3.out'}, 0);")
tl.append(f"tl.to('#title', {{autoAlpha:0, duration:0.2}}, {q(hook_end - 0.2)});")

# ---------- Cột checklist (chỉ chữ, không chấm/icon trước chữ) ----------
rows = "".join(f'<div class="pi" id="pi{k}">{esc(lab)}</div>' for k, (_, lab, _) in enumerate(EFFECTS))
panel = (f'<div id="panel"><div class="ph"><span>VIDEO NÀY</span><b id="pcount">00/{len(EFFECTS):02d}</b></div>{rows}'
         f'<div class="pf">{esc(CTA[2])}</div></div>')
for k, (t0, t1) in enumerate(SPANS):
    tl.append(f"tl.set('#pi{k}', {{backgroundColor:'{INK}', color:'{PANEL_BG}', opacity:1}}, {q(t0)});")
    tl.append(f"tl.set('#pi{k}', {{backgroundColor:'rgba(0,0,0,0)', color:'{INK}', opacity:0.45}}, {q(t1)});")
    tl.append(f"tl.set('#pcount', {{textContent:'{k + 1:02d}/{len(EFFECTS):02d}'}}, {q(t0)});")
    hide = EFFECTS[k][0] in WIDE
    tl.append(f"tl.to('#panel', {{autoAlpha:{0 if hide else 1}, duration:0.1}}, {q(t0)});")
tl.append(f"tl.to('#panel', {{autoAlpha:1, duration:0.2}}, {q(hook_end)});") if EFFECTS[1][0] not in WIDE else None

# ---------- Âm thanh ----------
# Bộ SFX qua scripts/sfxkit.py của skill. Cue = (vai, mốc hình[, số bản]); neo start / peak / end theo vai.
SK = os.environ.get("TOOL_VIDEO_SK") or sys.exit("thiếu TOOL_VIDEO_SK: chạy TOOL_VIDEO_SK=<thư mục skill tool-video> python3 build.py")
sys.path.insert(0, os.path.join(SK, "scripts"))
from sfxkit import sfx_tags
aud = [f'<audio id="voice" src="aroll.mp4" data-start="0" data-duration="{DURATION}" data-track-index="1" data-volume="1"></audio>']
if (PUB / "audio" / "music.m4a").exists():
    aud.append(f'<audio id="music" src="audio/music.m4a" data-start="0" data-duration="{DURATION}" data-track-index="2" data-volume="{MUSIC_VOL}"></audio>')
kit_tags = sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(200, 260), log=WORK / "sfx_cues.json")
if kit_tags is None:
    raise SystemExit("thiếu assets/sfx/kit.json trong thư mục skill: cài lại plugin tool-video")
aud += kit_tags

# ---------- Ghi index.html ----------
fonts = "\n".join([
    '@font-face { font-family:"Anton"; src:url("fonts/Anton.ttf"); font-display:block; }',
    '@font-face { font-family:"Dancing Script"; src:url("fonts/DancingScript.ttf"); font-weight:400 700; font-display:block; }',
    '@font-face { font-family:"Playfair Display"; src:url("fonts/PlayfairDisplay.ttf"); font-weight:400 900; font-display:block; }',
    '@font-face { font-family:"JetBrains Mono"; src:url("fonts/JetBrainsMono.ttf"); font-weight:100 800; font-display:block; }',
] + [f'@font-face {{ font-family:"Be Vietnam Pro"; src:url("fonts/BeVietnamPro-{n}.ttf"); font-weight:{wt}; font-display:block; }}'
     for n, wt in (("Medium", 500), ("Bold", 700), ("ExtraBold", 800), ("Black", 900))])
NL = "\n"
CSS = f"""
{fonts}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#0b1410; font-family:{FONT}; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#0b1410; perspective:1700px; }}
#world {{ position:absolute; inset:0; transform-style:preserve-3d; transform-origin:540px 960px; }}
.layer {{ position:absolute; inset:0; transform-style:preserve-3d; }}
.cam {{ position:absolute; inset:0; transform-origin:{ORIGIN}; }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#cam-fg {{ --m:-30%; -webkit-mask-image:linear-gradient(100deg, transparent calc(var(--m) - 12%), #000 calc(var(--m) + 12%));
  mask-image:linear-gradient(100deg, transparent calc(var(--m) - 12%), #000 calc(var(--m) + 12%)); }}
.fx {{ position:absolute; inset:0; visibility:hidden; opacity:0; pointer-events:none; }}
.full {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; }}
.paper {{ background:{PAPER}; }}
.ruled line {{ stroke:rgba(60,90,140,.18); stroke-width:2; }}
/* cursor */
.cu-box {{ position:absolute; border:3px solid {ACCENT}; transform-origin:0 0; box-shadow:0 0 0 1px rgba(0,0,0,.35); }}
.cu-box i {{ position:absolute; width:22px; height:22px; background:#fff; border:3px solid {ACCENT}; }}
.cu-size {{ position:absolute; padding:8px 16px; border-radius:10px; background:{ACCENT}; color:#111; font:700 34px/1 "JetBrains Mono", {FONT}; }}
.cu-ptr {{ position:absolute; left:0; top:0; }}
.cu-ptr span {{ position:absolute; left:40px; top:46px; padding:8px 18px; border-radius:22px; background:#111; color:#fff; font:700 32px/1 {FONT}; white-space:nowrap; }}
/* clones */
.clone {{ position:absolute; inset:0; transform-origin:{FX}px 1900px; }}
.clone video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
/* dial */
.dial circle {{ fill:none; stroke:#2b2620; stroke-width:4; }}
.dial line {{ stroke:#2b2620; stroke-width:4; }}
.dial text {{ font:400 92px "Playfair Display", serif; fill:#2b2620; }}
.dial text.dd {{ font:italic 400 58px "Playfair Display", serif; fill:#8a7b66; }}
/* keyboard */
.kb {{ position:absolute; left:70px; width:820px; top:1050px; height:440px; padding:14px 10px; border-radius:30px; background:#cfd3da;
  box-shadow:0 -10px 40px rgba(0,0,0,.35); }}
.kb-sug {{ display:flex; justify-content:space-around; height:62px; align-items:center; border-bottom:1px solid #b8bcc4; margin-bottom:10px; }}
.kb-sug span {{ padding:8px 18px; border-radius:12px; font:500 34px/1 {FONT}; color:#222; }}
.kr {{ display:flex; justify-content:center; gap:10px; margin-bottom:12px; }}
.kr b {{ flex:0 0 70px; height:72px; border-radius:12px; background:#fff; box-shadow:0 2px 0 #8e939b; font:500 36px/72px {FONT}; color:#111; text-align:center; }}
.kr b.wide2 {{ flex-basis:130px; font-size:28px; background:#adb2bb; }}
.kr b.space {{ flex-basis:430px; font-size:28px; color:#555; }}
.kb-input {{ position:absolute; left:70px; width:820px; top:930px; height:96px; padding:0 30px; border-radius:48px; background:#fff;
  display:flex; align-items:center; font:500 46px/1 {FONT}; color:#111; box-shadow:0 8px 30px rgba(0,0,0,.3); }}
.caret {{ display:inline-block; width:4px; height:52px; background:#2f7cf6; margin-left:4px; }}
/* orbit */
.orbit span {{ position:absolute; left:0; top:0; font:400 86px/1 "Anton", {FONT}; color:{ACCENT}; text-shadow:0 4px 18px rgba(0,0,0,.5); }}
/* matrix */
.mx {{ background:#020805; overflow:hidden; }}
.mx-col {{ position:absolute; top:0; width:60px; text-align:center; font:600 46px/1.15 "JetBrains Mono", monospace; color:#38ff7a; text-shadow:0 0 12px #38ff7a; }}
.scan {{ background:repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 3px, transparent 3px 7px); }}
/* wall */
.wall {{ background:#0b0b0b; }}
.wall i {{ position:absolute; width:116px; height:116px; margin:2px; background-size:cover; background-position:center; border-radius:6px; opacity:.8; }}
.wl-count {{ text-align:center; top:270px; bottom:auto; height:120px; }}
.wl-count span {{ display:block; font:700 30px/1 "JetBrains Mono", {FONT}; color:#fff; letter-spacing:6px; }}
.wl-count b {{ display:block; margin-top:8px; font:800 84px/1 "JetBrains Mono", {FONT}; color:{ACCENT}; text-shadow:0 4px 20px rgba(0,0,0,.7); }}
/* dive */
.dv-t {{ font:400 760px "Anton", {FONT}; fill:#000; }}
/* comment */
.cm-card {{ position:absolute; left:110px; width:720px; padding:20px 28px; border-radius:26px; background:#fff; box-shadow:0 10px 34px rgba(0,0,0,.35); }}
.cm-card {{ top:290px; }}
.cm-card.reply {{ top:470px; left:190px; width:640px; background:#f0f2f5; }}
.cm-name {{ font:800 32px/1.2 {FONT}; color:#111; }}
.cm-line {{ display:flex; justify-content:space-between; align-items:center; gap:20px; font:500 38px/1.3 {FONT}; color:#222; }}
.cm-type {{ color:#888; }}
.cm-btn {{ padding:8px 20px; border-radius:16px; background:#1877f2; color:#fff; font:700 30px/1 {FONT}; }}
.cta {{ position:absolute; left:100px; right:180px; top:1170px; text-align:center; }}
.cta div {{ margin-bottom:12px; }}
.cta span {{ display:inline-block; padding:12px 28px; border-radius:18px; background:#fff; color:#111; font:900 56px/1.15 {FONT}; box-shadow:0 8px 26px rgba(0,0,0,.35); }}
/* explode */
.ex-label {{ text-align:center; top:300px; font:italic 700 150px/1 "Playfair Display", serif; color:#fff; text-shadow:0 8px 30px rgba(0,0,0,.6); }}
/* sketch */
.sk {{ fill:#7a1f2b; stroke:#7a1f2b; stroke-width:3; stroke-dasharray:3000; fill-opacity:0; }}
.sk-s {{ font:700 110px "Dancing Script", cursive; }}
.sk-b {{ font:700 250px "Dancing Script", cursive; }}
/* slice */
.sl {{ background:#050505; }}
.sl-half {{ position:absolute; inset:0; }}
.sl-half video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.sl-line {{ position:absolute; left:0; top:1178px; width:1200px; height:6px; background:#fff; box-shadow:0 0 30px 8px rgba(255,255,255,.8); }}
/* tags */
.tg {{ position:absolute; left:{FX - 200}px; width:400px; text-align:center; padding:12px 0; border-radius:16px; background:#111; color:#fff;
  font:700 40px/1.1 "Be Vietnam Pro", sans-serif; border:3px solid {ACCENT}; }}
/* focus */
.fc-box {{ position:absolute; }}
.fc {{ position:absolute; width:60px; height:60px; border:6px solid #fff; }}
.fc.tl {{ left:0; top:0; border-right:0; border-bottom:0; }} .fc.tr {{ right:0; top:0; border-left:0; border-bottom:0; }}
.fc.bl {{ left:0; bottom:0; border-right:0; border-top:0; }} .fc.br {{ right:0; bottom:0; border-left:0; border-top:0; }}
/* banknote */
.note {{ background:#0b1410; }}
.nt-frame {{ position:absolute; left:80px; right:80px; top:270px; bottom:410px; border-radius:20px; background:#e8eedf; border:14px double #2f5d46;
  box-shadow:inset 0 0 0 10px #e8eedf, inset 0 0 0 14px #2f5d46; overflow:hidden; }}
.nt-guil {{ position:absolute; inset:0; opacity:.35; background:repeating-radial-gradient(circle at 50% 45%, #2f5d46 0 1px, transparent 1px 9px); }}
.nt-corner {{ position:absolute; font:700 54px/1 "Playfair Display", serif; color:#2f5d46; }}
.nt-serial {{ position:absolute; left:0; right:0; top:130px; text-align:center; font:700 34px/1 "JetBrains Mono", monospace; color:#9c2b2b; letter-spacing:4px; }}
.nt-oval {{ position:absolute; left:50%; top:200px; width:560px; height:640px; margin-left:-280px; border-radius:50%; overflow:hidden;
  border:10px solid #2f5d46; box-shadow:0 0 0 8px #e8eedf, 0 0 0 12px #2f5d46; }}
.nt-oval video {{ position:absolute; left:-260px; top:-640px; width:1080px; height:1920px; object-fit:cover; filter:grayscale(1) contrast(1.7) brightness(1.08); }}
.nt-eng {{ position:absolute; inset:0; background:repeating-linear-gradient(-20deg, rgba(20,55,38,.55) 0 2px, transparent 2px 6px); mix-blend-mode:multiply; }}
.nt-tint {{ position:absolute; inset:0; background:#2f6b4f; mix-blend-mode:color; }}
.nt-val {{ position:absolute; left:0; right:0; top:880px; text-align:center; font:700 150px/1 "Playfair Display", serif; color:#1f3f30; }}
.nt-sub {{ position:absolute; left:0; right:0; top:1050px; text-align:center; font:700 38px/1 "Playfair Display", serif; color:#2f5d46; letter-spacing:6px; }}
/* voice note */
.vn {{ position:absolute; left:110px; top:300px; width:760px; height:130px; padding:0 30px; border-radius:65px; background:#1f2c34;
  display:flex; align-items:center; gap:22px; box-shadow:0 10px 34px rgba(0,0,0,.4); }}
.vn-play {{ flex:0 0 84px; height:84px; border-radius:50%; background:#00a884; display:flex; align-items:center; justify-content:center; }}
.vn-wave {{ flex:1; display:flex; align-items:center; gap:6px; height:80px; }}
.vn-wave i {{ display:block; width:9px; border-radius:5px; background:rgba(255,255,255,.55); }}
.vn-time {{ font:700 34px/1 "JetBrains Mono", monospace; color:#fff; }}
.vn-label {{ position:absolute; right:180px; top:450px; padding:10px 22px; border-radius:16px; background:rgba(0,0,0,.6); color:#fff; font:700 38px/1 {FONT}; }}
/* impact */
.im {{ background:#f4f0e6; overflow:hidden; }}
.im-p {{ position:absolute; inset:0; transform-origin:{ORIGIN}; }}
.im-p video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.im-word {{ position:absolute; left:0; right:0; top:1190px; text-align:center; font:400 280px/1 "Anton", {FONT}; color:#111;
  -webkit-text-stroke:10px #fff; paint-order:stroke fill; }}
/* press */
.press {{ background:#14110c; }}
.pr-page {{ position:absolute; left:70px; right:70px; top:250px; bottom:400px; padding:30px 34px; background:#efe8d8; color:#1a1712;
  box-shadow:0 20px 60px rgba(0,0,0,.6); overflow:hidden; }}
.pr-mast {{ text-align:center; font:900 100px/1.1 "Playfair Display", serif; border-bottom:4px double #1a1712; padding-bottom:10px; }}
.pr-rule {{ text-align:center; font:700 24px/1 "JetBrains Mono", monospace; letter-spacing:2px; padding:12px 0; border-bottom:2px solid #1a1712; }}
.pr-head {{ text-align:center; font:900 92px/1.05 "Playfair Display", serif; margin-top:22px; }}
.pr-sub {{ text-align:center; font:italic 400 52px/1.2 "Playfair Display", serif; margin:8px 0 20px; }}
.pr-body {{ display:flex; gap:22px; }}
.pr-col {{ flex:1; font:400 21px/1.35 "Playfair Display", serif; text-align:justify; height:560px; overflow:hidden; }}
.pr-photo {{ position:relative; flex:0 0 480px; height:560px; overflow:hidden; border:3px solid #1a1712; }}
.pr-photo video {{ position:absolute; left:-300px; top:-500px; width:1080px; height:1920px; object-fit:cover; filter:grayscale(1) contrast(1.6) brightness(1.1); }}
.pr-dots {{ position:absolute; inset:0; background:radial-gradient(circle, rgba(20,17,12,.55) 1.6px, transparent 2.2px) 0 0/7px 7px; mix-blend-mode:multiply; }}
/* tear */
.tr-half {{ position:absolute; inset:0; }}
.tr-word {{ position:absolute; left:0; right:0; top:820px; text-align:center; font:400 230px/1.1 "Anton", {FONT}; color:#1a1712; }}
/* blow */
.pt {{ position:absolute; border-radius:2px; opacity:0; }}
/* title */
.title {{ text-align:center; top:270px; }}
.title div {{ margin-bottom:12px; }}
.title span {{ display:inline-block; padding:12px 28px; border-radius:16px; background:#fff; color:#111; font:900 54px/1.15 {FONT}; }}
.title span.t2 {{ background:{ACCENT}; }}
/* panel */
#panel {{ position:absolute; left:70px; top:440px; width:300px; padding:18px 14px 16px; border-radius:24px; background:{PANEL_BG}; opacity:0; visibility:hidden;
  box-shadow:0 12px 40px rgba(0,0,0,.45); }}
.ph {{ display:flex; justify-content:space-between; padding:0 10px 12px; font:700 22px/1 "JetBrains Mono", monospace; color:rgba(255,255,255,.65); }}
.ph b {{ color:#fff; }}
.pi {{ padding:5px 12px; border-radius:10px; font:700 27px/1.25 {FONT}; color:{INK}; white-space:nowrap; }}
.pf {{ margin-top:12px; padding:10px 12px; border-radius:12px; background:{ACCENT}; color:#111; text-align:center; font:800 26px/1.1 {FONT}; }}
"""
index = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8" />
<style>{CSS}</style></head>
<body>
<svg width="0" height="0" style="position:absolute"><filter id="thr" color-interpolation-filters="sRGB">
  <feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 1 0"/>
  <feComponentTransfer><feFuncR type="discrete" tableValues="0.07 1 1"/><feFuncG type="discrete" tableValues="0.07 1 1"/>
  <feFuncB type="discrete" tableValues="0.07 1 1"/></feComponentTransfer></filter></svg>
<div id="stage" data-composition-id="fxreel" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
 <div id="world">
  <div id="cam-bg" class="cam"><video id="v-bg" src="aroll.mp4" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="3"></video></div>
  <div id="behind" class="layer" data-layout-allow-occlusion>{NL.join(behind)}</div>
  <div id="cam-fg" class="cam"><video id="v-person" src="person.webm" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="4"></video></div>
  <div id="front" class="layer">{NL.join(front)}
  {panel}</div>
 </div>
 <div id="over" class="layer">{NL.join(over)}</div>
{NL.join(aud)}
 <script src="vendor/gsap.min.js"></script>
 <script>
 (function () {{
   const tl = window.gsap.timeline({{ paused: true }});
   const CAMS = ["#cam-bg", "#cam-fg"];
   {(NL + '   ').join(tl)}
   window.__timelines = window.__timelines || {{}};
   window.__timelines["fxreel"] = tl;
 }})();
 </script>
</div>
</body></html>
"""
(PUB / "index.html").write_text(index)
print(f"{DURATION:.2f}s, {len(EFFECTS)} hiệu ứng, mốc {'transcript' if tp.exists() else 'chia đều'}, {len(sfx)} SFX, {_track[0] - 10} video phụ")
print("mốc:", ", ".join(f"{EFFECTS[k][0]}@{s:.2f}" for k, s in enumerate(starts)))
