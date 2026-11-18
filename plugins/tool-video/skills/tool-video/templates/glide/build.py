"""Bản mẫu concept glide (xem concepts/glide.md), dựng từ clip test C013 hành trình aff (2026-10-28).
Người trượt êm sang một bên khi chữ cạnh đầu xuất hiện, vài câu chữ lớn sau đầu, chip chỉ có chữ.
Phần riêng của clip: FIX/PAIRS, SIDE, các lệnh big()/chip(), ORIGIN. Dựng thử: PREVIEW=30 python3 build.py"""
import html
import json
import re
from pathlib import Path

import sys
import os
SK = os.environ.get("TOOL_VIDEO_SK") or sys.exit("thiếu TOOL_VIDEO_SK: chạy TOOL_VIDEO_SK=<thư mục skill tool-video> python3 build.py")
sys.path.insert(0, os.path.join(SK, "scripts"))
from sfxkit import sfx_tags   # bộ SFX CC0 của skill: mức + điểm neo theo vai, xoay vòng bản
WORK = Path(__file__).parent
PUB = WORK / "public"
W, H, FPS = 1080, 1920, 30
CAP_Y = 1380   # vùng an toàn: đáy phụ đề ≤ 1500 (SAFE_ZONE.md của skill)
ORIGIN = "660px 1120px"   # mặt người nói trong khung 1080x1920

BASE, SUPPORT, ACCENT = "#2f230e", "#f4f3f0", "#33e4ff"   # splitcomp từ màu phòng (palette.json)
FONT = '"Be Vietnam Pro", sans-serif'

tl, sfx, behind, front = [], [], [], []


def q(t):
    return f"{round(t * FPS) / FPS:.4f}"


def esc(s):
    return html.escape(s)


def fit(text, cap, width=980, ratio=0.5):
    n = sum(0.28 if c == " " else 1 for c in text)
    return int(min(cap, width / (n * ratio)))


# ---------- Transcript: sửa chính tả theo bản đã duyệt (hanh-trinh-aff) ----------
FIX = {"Matrix.vn.": "Metric.vn.", "Matrix.vn": "Metric.vn", "G,": "Duy,", "G.": "Duy.", "đép,": "Dev,", "đép.": "Dev.",
       "đẳn,": "đặn,", "đẳng,": "đặn,", "call,": "kho,", "Quy": "Quý", "seo": "sale", "gió": "giỏ", "shopping,": "Shopee Video,",
       "shopping.": "Shopee Video.", "danh": "doanh", "mưu": "mua", "Mỗi": "Ai", "chỗ": "chút", "thiểu": "hiểu", "dầu,": "giàu,",
       "đẳn": "đặn", "Mũ": "Mua", "Qua": "qua", "Ling": "link", "12/11": "12/12"}
PAIRS = {("App", "Felix"): "Affiliate", ("App", "Valet"): "Affiliate", ("bình", "tử"): "điện tử"}
raw = json.loads((WORK / "transcript.raw.json").read_text())
words, i = [], 0
while i < len(raw):
    w = dict(raw[i])
    nxt = raw[i + 1]["text"] if i + 1 < len(raw) else ""
    key = next((k for k in PAIRS if w["text"] == k[0] and nxt.startswith(k[1])), None)
    if key:
        parts = PAIRS[key].split()
        tail = nxt[len(key[1]):]
        if len(parts) == 1:
            words.append({**w, "text": parts[0] + tail, "end": raw[i + 1]["end"]})
        else:
            words.append({**w, "text": parts[0]})
            words.append({**raw[i + 1], "text": parts[1] + tail})
        i += 2
        continue
    if w["text"] == "cho" and nxt.startswith("đơn"):
        w["text"] = "chốt"
    if w["text"] == "sau" and nxt.startswith("tháng"):
        w["text"] = "6"
    if w["text"] == "tự" and words and words[-1]["text"].startswith("mại"):
        w["text"] = "điện tử"
    if w["text"] == "được" and nxt.startswith("xem"):
        w["text"] = "để"
    w["text"] = FIX.get(w["text"], w["text"])
    words.append(w)
    i += 1
(WORK / "transcript.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
DURATION = float((WORK / "cuts" / "duration.txt").read_text())
if __import__("os").environ.get("PREVIEW"):   # PREVIEW=20 python3 build.py → dựng thử 20s đầu để duyệt chuyển động
    DURATION = min(DURATION, float(__import__("os").environ["PREVIEW"]))
BIG_SPANS = []


def norm(s):
    return re.sub(r"[^\w%]", "", s.lower())


def at(phrase, after=0.0, end=False):
    """Mốc của cụm từ trong transcript (start của từ đầu, hoặc end của từ cuối)."""
    toks = [norm(t) for t in phrase.split()]
    for k in range(len(words) - len(toks) + 1):
        if words[k]["start"] >= after and all(norm(words[k + j]["text"]).startswith(toks[j]) for j in range(len(toks))):
            return words[k + len(toks) - 1]["end"] if end else words[k]["start"]
    raise SystemExit(f"không thấy cụm '{phrase}' sau {after}s")


# ---------- Chữ lớn sau đầu: 6 câu đinh ----------
def big(bid, lines, t0, t1, count=None, hit=False):
    """lines: [(chữ, màu)], 1–2 dòng; đầu người che phần dưới."""
    sizes = [fit(txt, 520 if len(lines) == 1 else 300, ratio=0.58) for txt, _ in lines]
    total = sum(int(s * 1.12) for s in sizes)
    top = max(260, (870 if sizes[0] >= 380 else 790) - total)   # chữ nhỏ thì đặt cao hơn để đầu không che quá nửa
    els = []
    for k, ((txt, col), s) in enumerate(zip(lines, sizes)):
        els.append(f'<div class="big" id="{bid}-{k}" data-layout-allow-occlusion style="top:{top}px;font-size:{s}px;color:{col}">{esc(txt)}</div>')
        tl.append(f"tl.fromTo('#{bid}-{k}', {{y:40, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:'power3.out'}}, {q(t0 + k * 0.18)});")
        top += int(s * 1.12)
    behind.append(f'<div class="behind" id="{bid}" data-layout-allow-occlusion data-layout-allow-overflow>{"".join(els)}</div>')
    BIG_SPANS.append((t0, t1 + 0.35))
    tl.append(f"tl.set('#{bid}', {{opacity:1}}, {q(t0)});")
    tl.append(f"tl.to('#{bid}', {{opacity:0, duration:0.35, ease:'power1.in'}}, {q(t1)});")
    if count:
        n, tc = count
        tl.append(f"(() => {{ const o = {{v:0}}, el = document.getElementById('{bid}-0'); "
                  f"tl.fromTo(o, {{v:0}}, {{v:{n}, duration:0.9, ease:'power2.out', "
                  f"onUpdate:() => {{ el.textContent = Math.round(o.v).toLocaleString('vi-VN'); }}}}, {q(tc)}); }})();")
    if hit:
        sfx.append(("impact", t0))


# ---------- Chip nhỏ phía trên đầu (khi không có chữ lớn) hoặc bên trái mặt ----------
def chip(cid, text, t0, t1, top=300, left=None):
    """Chip chỉ có chữ: người dùng ghét icon/chấm/dấu ✕ đặt trước chữ (kiểu AI slop)."""
    el = f'<div class="chip" id="{cid}">{esc(text)}</div>'
    cls = "chip-row" if left is None else "chip-row left"
    pos = f"top:{top}px" if left is None else f"top:{top}px;left:{left}px"
    front.append(f'<div class="{cls}" style="{pos}">{el}</div>')
    tl.append(f"tl.fromTo('#{cid}', {{y:24, opacity:0}}, {{y:0, opacity:1, duration:0.35, ease:'power3.out'}}, {q(t0)});")
    tl.append(f"tl.to('#{cid}', {{opacity:0, duration:0.3}}, {q(min(t1, DURATION - 0.3))});")
    sfx.append(("pop", t0))


big("k1", [("1 TỶ", SUPPORT)], at("1 tỷ") - 0.1, at("online", end=True), hit=True)
t = at("291")
big("k2", [("291.000", SUPPORT), ("TỶ ĐỒNG", ACCENT)], t - 0.1, at("hiện nay", end=True), count=(291000, t))
big("k3", [("+44%", ACCENT)], at("44%") - 0.1, at("ngoái", end=True))
big("k4", [("ĐỦ LỚN", SUPPORT)], at("đủ lớn") - 0.1, at("thử", after=at("đủ lớn"), end=True) + 0.3)
t = at("Affiliate")
big("k5", [("AFFILIATE", SUPPORT)], t - 0.1, at("khách", after=t, end=True) + 0.2)
for k, (ph, txt) in enumerate([("nhập hàng", "Không cần nhập hàng"), ("kho", "Không cần kho"), ("chốt đơn", "Không phải chốt đơn")]):
    chip(f"a{k}", txt, at(ph, after=t), at("khách", after=t, end=True) + 0.2, top=270 + k * 96)   # vùng trần phía trên chữ AFFILIATE, không đè mặt
t = at("số thật")
big("k6", [("SỐ THẬT", ACCENT)], t - 0.1, at("thật", after=t, end=True) + 0.9, hit=True)

# ---------- Chữ cạnh đầu đi cặp với khung lệch (như reel Vids.app) ----------
# Người lệch trái → chữ bên phải, ngang tầm đầu; lệch phải → chữ bên trái. Chữ nhỏ trắng + từ khoá lớn có vòng elip vẽ dần.
# (cụm neo trong lời, chữ nhỏ, từ khoá lớn, từ để canh lúc bật từ khoá)
SIDE = [
    ("6 tháng", "6 tháng đầu năm", "Metric.vn", "Metric"),
    ("nói là nền", "ai cũng nói", "khó khăn", "khó"),
    ("mình là một", "mình là Duy", "Dev", "Dev"),
    ("ngoài giờ", "thử thêm", "ngoài giờ", "ngoài"),
    ("qua link", "mua qua link", "hoa hồng", "hoa"),
    ("Black", "11/11 · 12/12", "Black Friday", "Black"),
    ("rảnh", "thời gian rảnh", "buổi tối", "buổi"),
    ("công khai cách", "công khai", "cách làm", "cách"),
    ("mở giỏ", "chưa được mở", "giỏ Shopee", "giỏ"),
    ("theo dõi", "theo dõi", "hành trình", "theo"),
]
SIDE_COLORS = [ACCENT, "#ffd84a"]
forced = []   # (t, side, t_end)
for k, (anchor, small, key, key_at) in enumerate(SIDE):
    t0 = at(anchor) - 0.04
    try:
        tk = at(key_at, after=t0 - 0.3)
        tk = tk if tk - t0 < 2.0 else t0 + 0.35
    except SystemExit:
        tk = t0 + 0.35
    t1 = min(t0 + 3.0, tk + 1.6, DURATION - 0.2)
    side = "L" if k % 2 == 0 else "R"          # người lệch trái → chữ phải
    forced.append((t0, side, t1))
    sid = f"s{k:02d}"
    col = SIDE_COLORS[k % 2]
    size = int(min(118, 430 / (max(len(key), 4) * 0.56)))
    # lệch trái: mặt chỉ dịch được ít (mặt gốc nằm lệch phải) → chữ chéo trên-phải sát đỉnh đầu;
    # lệch phải: bên trái trống rộng → chữ ngang tầm đầu
    pos = "right:70px; top:470px; text-align:right" if side == "L" else "left:70px; top:730px; text-align:left"
    front.append(f'<div class="side" id="{sid}" style="{pos}"><div class="side-small" id="{sid}-a">{esc(small)}</div>'
                 f'<div class="side-key" id="{sid}-b" style="font-size:{size}px;color:{col}">{esc(key)}'
                 f'<svg viewBox="0 0 100 40" preserveAspectRatio="none"><path pathLength="1000" d="M8 22 C 10 4, 90 2, 94 18 C 97 34, 20 40, 6 26 C 2 18, 30 8, 60 9" '
                 f'stroke="{col}"/></svg></div></div>')
    dx = 40 if side == "L" else -40
    tl.append(f"tl.set('#{sid}', {{opacity:1}}, {q(t0)});")
    tl.append(f"tl.fromTo('#{sid}-a', {{opacity:0, x:{dx}}}, {{opacity:1, x:0, duration:0.35, ease:'power3.out'}}, {q(t0 + 0.15)});")
    tl.append(f"tl.fromTo('#{sid}-b', {{opacity:0, scale:0.5}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(2.2)'}}, {q(tk)});")
    tl.append(f"tl.fromTo('#{sid}-b path', {{strokeDashoffset:1000}}, {{strokeDashoffset:0, duration:0.5, ease:'power2.out'}}, {q(tk + 0.15)});")
    tl.append(f"tl.to('#{sid}', {{opacity:0, y:-20, duration:0.3, ease:'power2.in'}}, {q(t1)});")
    sfx.append(("pop", tk))

# ---------- Chuyển động người: ít và chậm (bản v3 bị chê "dịch chuyển quá nhiều và nhanh, chóng mặt") ----------
# Chỉ di chuyển lớn khi chữ cạnh đầu xuất hiện (lệch sang một bên) hoặc vào câu chữ lớn sau đầu (về toàn cảnh).
# Hết chữ thì đứng yên tại chỗ; chỗ cắt A-roll chỉ nhích zoom ±4% để che bước nhảy.
# Khung: (scale, x), x ∈ [-420(s-1), 660(s-1)] để mép video không lộ (tâm mặt 660px).
SHOTS = {"W": (1.0, 0), "M": (1.12, 0), "L": (1.28, -115), "R": (1.28, 180)}
MOVE, NUDGE = 0.8, 0.5
jumps = json.loads((WORK / "cuts" / "jumps.json").read_text())
moves = [(t, side) for t, side, _ in forced] + [(a0 - 0.05, "W") for a0, _ in BIG_SPANS]
moves = sorted(moves)
# hết chữ lớn mà chữ cạnh đầu sau đó còn xa (> 6s) thì về trung cảnh ở chỗ cắt A-roll kế tiếp
for a0, b0 in BIG_SPANS:
    nxt = min([t for t, _ in moves if t > b0] or [DURATION])
    j = next((tj for tj in jumps if b0 < tj < nxt - 2.5), None)
    if nxt - b0 > 6 and j:
        moves.append((j, "M"))
moves = sorted(moves)
timeline, cur = [], None
for t, name in moves:
    if name != cur:
        timeline.append((t, name))
        cur = name
events = sorted([(t, "move", n) for t, n in timeline] + [(tj, "nudge", None) for tj in jumps])
sc, x, nud = 1.0, 0, 0
tl.append("tl.set(CAMS, {scale:1.0, x:0}, 0);")
last_end = 0.0
for k, (t, kind, name) in enumerate(events):
    if kind == "move":
        sc, x = SHOTS[name]
        nud = 0
        start, dur = max(last_end, t - 0.35), MOVE
    else:
        if any(abs(t - tm) < MOVE for tm, _ in timeline):
            continue   # chỗ cắt trùng lúc đang trượt: đã được che
        nud = 0.04 if nud == 0 else 0   # không zoom nhỏ hơn khung gốc: khung lệch sẽ lộ mép video
        start, dur = max(last_end, t - 0.2), NUDGE
    tl.append(f"tl.to(CAMS, {{scale:{sc + nud:.3f}, x:{x}, duration:{dur}, ease:'power2.inOut'}}, {q(start)});")
    last_end = start + dur
    nxt = next((e[0] for e in events[k + 1:]), DURATION)
    hold = nxt - 0.4 - last_end
    if hold > 0.6:   # zoom vào rất chậm giữa hai lần di chuyển
        tl.append(f"tl.to(CAMS, {{scale:{sc + nud + 0.015:.3f}, duration:{hold:.2f}, ease:'none'}}, {q(last_end)});")
        last_end += hold
cuts_at = timeline

# ---------- Chớp sáng light-leak ở 2 lần đổi đoạn ----------
tl.append("tl.set('#leak', {opacity:0}, 0);")
for t in (at("Affiliate"), at("Mình không hứa")):
    tl.append(f"tl.to('#leak', {{opacity:0.85, duration:0.1, ease:'power2.out'}}, {q(t - 0.14)});")
    tl.append(f"tl.to('#leak', {{opacity:0, duration:0.35, ease:'power2.in'}}, {q(t)});")

# ---------- Phụ đề: cụm ≤ 4 từ, từ đang nói màu accent ----------
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if w["text"][-1] in ",.!?" or len(cur) >= 4 or not nxt or nxt["start"] - w["end"] > 0.5:
        groups.append(cur)
        cur = []
caps = []
for gi, g in enumerate(groups):
    st = max(0, g[0]["start"] - 0.04)
    en = groups[gi + 1][0]["start"] - 0.04 if gi + 1 < len(groups) else DURATION
    en = min(en, g[-1]["end"] + 0.5, DURATION)
    spans = " ".join(f'<span class="cw" id="c{gi}w{wi}">{esc(w["text"].strip(",.!?"))}</span>' for wi, w in enumerate(g))
    caps.append(f'<div class="cg" id="cg{gi}"><span class="cp">{spans}</span></div>')
    tl.append(f"tl.set('#cg{gi}', {{visibility:'visible'}}, {q(st)});")
    for wi, w in enumerate(g):
        tl.append(f"tl.fromTo('#c{gi}w{wi}', {{color:'#ffffff'}}, {{color:'{ACCENT}', duration:0.04}}, {q(w['start'])});")
        tl.append(f"tl.to('#c{gi}w{wi}', {{color:'#ffffff', duration:0.04}}, {q(max(w['end'], w['start'] + 0.1))});")
    tl.append(f"tl.set('#cg{gi}', {{visibility:'hidden'}}, {q(en)});")

# ---------- Âm thanh: giọng, nhạc nhỏ, SFX ít và nhỏ (series aff) ----------
SFX_VOL = {"pop": 0.35, "impact": 0.45}
SFX_GAIN = 0.5    # series aff: người dùng muốn SFX nhỏ (aff-02, 2026-10-25)
SFX_LEN = {"pop": 0.116, "impact": 0.273}
aud = [f'<audio id="voice" src="aroll.mp4" data-start="0" data-duration="{DURATION}" data-track-index="30" data-volume="1"></audio>']
if (PUB / "audio/music_loop.m4a").exists():   # nhạc nền tuỳ chọn: người dùng tự bỏ file vào public/audio/
    aud.append(f'<audio id="music" src="audio/music_loop.m4a" data-start="0" data-duration="{DURATION}" data-track-index="31" data-volume="0.22"></audio>')
# cue = (vai, mốc hình): bộ SFX tự neo whoosh/impact theo điểm to nhất, pop/click theo điểm bắt đầu
kit_tags = sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(32, 60), log=WORK / "sfx_cues.json")
if kit_tags is not None:
    aud += kit_tags
else:   # không đọc được assets/sfx/kit.json: bộ âm cũ trong public/audio/
    last = {}
    for i, (n, t) in enumerate(sorted(sfx, key=lambda e: e[1])):
        t = max(0.0, t)
        d = min(SFX_LEN[n], DURATION - t)
        tr = next(k for k in range(32, 60) if last.get(k, -1) <= t)
        last[tr] = t + d
        aud.append(f'<audio id="sfx{i:02d}" src="sfx/{n}.ogg" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{tr}" data-volume="{SFX_VOL[n] * SFX_GAIN:.3f}"></audio>')

fonts = "\n".join([
    '@font-face { font-family:"Anton"; src:url("fonts/Anton.ttf"); font-display:block; }',
] + [f'@font-face {{ font-family:"Be Vietnam Pro"; src:url("fonts/BeVietnamPro-{n}.ttf"); font-weight:{wt}; font-display:block; }}'
     for n, wt in (("Medium", 500), ("Bold", 700), ("ExtraBold", 800), ("Black", 900))])
NL = "\n"
index = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8" />
<style>
{fonts}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:{BASE}; font-family:{FONT}; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:{BASE}; }}
.cam {{ position:absolute; inset:0; transform-origin:{ORIGIN}; }}
.cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.behind {{ position:absolute; inset:0; opacity:0; }}
.big {{ position:absolute; left:0; right:0; text-align:center; font-family:"Anton", {FONT}; line-height:1.12; letter-spacing:4px; white-space:nowrap;
  text-shadow:0 6px 30px rgba(0,0,0,.25); }}
.chip-row {{ position:absolute; left:0; right:0; text-align:center; }}
.chip-row.left {{ right:auto; text-align:left; }}
.chip {{ display:inline-flex; align-items:center; gap:14px; padding:14px 26px; border-radius:40px; background:rgba(22,15,5,.78);
  color:#fff; font:700 42px/1.15 {FONT}; box-shadow:0 6px 22px rgba(0,0,0,.28); }}
#leak {{ position:absolute; inset:0; opacity:0; pointer-events:none; mix-blend-mode:screen;
  background:radial-gradient(70% 55% at 30% 35%, rgba(255,255,255,.95), rgba(140,240,255,.55) 45%, rgba(51,228,255,0) 75%); }}
.side {{ position:absolute; width:520px; opacity:0; }}
.side-small {{ font:700 44px/1.2 {FONT}; color:#fff; text-shadow:0 3px 14px rgba(0,0,0,.55); margin-bottom:6px; }}
.side-key {{ position:relative; display:inline-block; font-family:{FONT}; font-weight:900; line-height:1.15; letter-spacing:-1px;
  text-shadow:0 0 24px rgba(0,0,0,.35), 0 4px 16px rgba(0,0,0,.5); white-space:nowrap; }}
.side-key svg {{ position:absolute; left:-26px; right:-26px; top:-16px; bottom:-12px; width:calc(100% + 52px); height:calc(100% + 28px); overflow:visible; }}
.side-key path {{ fill:none; stroke-width:3.2; stroke-linecap:round; stroke-dasharray:1000; stroke-dashoffset:1000; vector-effect:non-scaling-stroke; }}
#fronts {{ position:absolute; inset:0; pointer-events:none; }}
#captions {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; pointer-events:none; }}
#captions .cg {{ position:absolute; left:100px; right:170px; top:{CAP_Y}px; text-align:center; visibility:hidden; }}
#captions .cp {{ display:inline-block; padding:14px 30px 18px; border-radius:26px; background:rgba(22,15,5,.85); font:900 60px/1.2 {FONT}; color:#fff; }}
#captions .cw {{ display:inline-block; }}
</style></head>
<body>
<div id="stage" data-composition-id="hanh-trinh-depth" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
  <div id="cam-bg" class="cam"><video id="v-bg" src="aroll.mp4" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="1"></video></div>
{NL.join(behind)}
  <div id="cam-fg" class="cam"><video id="v-person" src="person.webm" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="2"></video></div>
  <div id="leak"></div>
  <div id="fronts">{NL.join(front)}</div>
  <div id="captions" class="clip" data-start="0" data-duration="{DURATION}" data-track-index="20">{"".join(caps)}</div>
{NL.join(aud)}
  <script src="vendor/gsap.min.js"></script>
  <script>
  (function () {{
    const tl = window.gsap.timeline({{ paused: true }});
    const CAMS = ["#cam-bg", "#cam-fg"];
    {(NL + '    ').join(tl)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["hanh-trinh-depth"] = tl;
  }})();
  </script>
</div>
</body></html>
"""
(PUB / "index.html").write_text(index)
print(f"{DURATION}s, {len(cuts_at)} lần đổi khung, {len(SIDE)} chữ cạnh đầu, {len(behind)} câu chữ lớn, {len(front)} chip, {len(groups)} cụm phụ đề, {len(sfx)} SFX, {len(jumps)} chỗ cắt")
