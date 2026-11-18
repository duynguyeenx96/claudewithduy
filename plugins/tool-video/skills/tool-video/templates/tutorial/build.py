"""Concept tutorial: quay màn hình ngang đặt giữa khung 9:16, mặt trong ô vuông, phụ đề đối diện ô mặt.

Chạy scripts/tutorial_prep.py trước (ra public/face.mp4, screen.mp4, bg.mp4, tutorial.json), có transcript.json rồi:
    python3 build.py
Đổi phần CẤU HÌNH cho từng video, không cần sửa phần dưới.
"""
import html
import json
import os
from pathlib import Path

from PIL import ImageFont

import sys
import os
SK = os.environ.get("TOOL_VIDEO_SK") or sys.exit("thiếu TOOL_VIDEO_SK: chạy TOOL_VIDEO_SK=<thư mục skill tool-video> python3 build.py")
sys.path.insert(0, os.path.join(SK, "scripts"))
from sfxkit import sfx_tags   # bộ SFX CC0 của skill: mức + điểm neo theo vai, xoay vòng bản
WORK = Path(__file__).parent
PUB = WORK / "public"
FPS, W, H = 30, 1080, 1920

# ---------- CẤU HÌNH ----------
FACE_POS = os.environ.get("FACE_POS", "bottom")   # bottom: màn hình trên, mặt dưới | top: mặt trên, màn hình dưới
FACE_SIDE = os.environ.get("FACE_SIDE", "left")   # left | right (phụ đề luôn ở phía đối diện)
ACC = "#ffd84a"                 # sun #ffd84a | volt #c6ff3d | ice #5ac8ff
FG = "#ffffff"
CASE = "normal"                 # normal | upper
CAP_SIZE = 62                   # cỡ phụ đề tối đa
CAP_WORDS = 5                   # tối đa số từ mỗi cụm
CAP_LINES = 3                   # tối đa số dòng mỗi cụm
CAP_LEAD = 0.2                  # phụ đề sớm hơn mốc Whisper
ZOOMS = []                      # (bắt đầu, kết thúc, x 0-1, y 0-1, độ zoom): chỉ ở chỗ có thao tác đáng xem
STEPS = []                      # (bắt đầu, kết thúc, "Bước 1: Tạo project"): nhãn chỉ có chữ ở vùng trống, tuỳ chọn
MUSIC = 0.15                    # 0 = không nhạc
SFX_GAIN = 0.5
SFX_VOL = {"pop": 0.5}
BG_DIM = 0.25                   # độ phủ tối của nền 2 dải: cao quá thì nền tảng coi là viền đen, thấp quá thì khó đọc phụ đề
BG_DRIFT = 1.15                 # nền zoom rất chậm tới mức này: 2 dải luôn có chuyển động kể cả khi người ngồi yên
FIX = {}                        # sửa chính tả phụ đề: {"VL3.1": "Veo 3.1"}
# ------------------------------

info = json.loads((PUB / "tutorial.json").read_text())
DURATION = info["duration"]
SCREEN_H = round(W * info["screen_h"] / info["screen_w"])

SAFE_L, SAFE_R, SAFE_T, SAFE_B, RAIL_X, RAIL_Y = 70, 1010, 250, 1500, 900, 850   # SAFE_ZONE.md của skill
FACE, GAP = 380, 32
if FACE_POS == "bottom":
    FACE_Y = SAFE_B - FACE                 # đáy ô mặt không xuống dưới tên kênh/mô tả của TikTok
    SCREEN_Y = FACE_Y - GAP - SCREEN_H
    FREE_T, FREE_B = SAFE_T, SCREEN_Y - 20  # vùng trống cho nhãn bước
else:
    FACE_Y = SAFE_T
    SCREEN_Y = FACE_Y + FACE + GAP
    FREE_T, FREE_B = SCREEN_Y + SCREEN_H + 20, SAFE_B
FACE_X = SAFE_L if FACE_SIDE == "left" else (RAIL_X if FACE_Y + FACE > RAIL_Y else SAFE_R) - FACE
if FACE_SIDE == "left":
    CAP_L = FACE_X + FACE + 40
    CAP_R = RAIL_X if FACE_Y + FACE > RAIL_Y else SAFE_R
else:
    CAP_L, CAP_R = SAFE_L, FACE_X - 40
CAP_W = CAP_R - CAP_L
if SCREEN_Y < 0 or SCREEN_Y + SCREEN_H > H:
    raise SystemExit(f"bản quay cao {SCREEN_H}px không vừa bố cục")


def q(t):
    return f"{round(t * FPS) / FPS:.4f}"


def font(size):
    return ImageFont.truetype(str(PUB / "fonts/BeVietnamPro-Black.ttf"), size)


def wrap(words_, size):
    """Xếp dòng theo độ rộng thật của font; trả (dòng = list chỉ số từ) hoặc None nếu không vừa."""
    f, space = font(size), font(size).getlength(" ")
    lines, cur, cur_w = [], [], 0
    for i, t in enumerate(words_):
        w = f.getlength(t)
        if w > CAP_W:
            return None
        if cur and cur_w + space + w > CAP_W:
            lines.append(cur)
            cur, cur_w = [], 0
        cur_w += (space if cur else 0) + w
        cur.append(i)
    lines.append(cur)
    return lines if len(lines) <= CAP_LINES else None


def fit(words_):
    for size in range(CAP_SIZE, 39, -2):
        lines = wrap(words_, size)
        if lines:
            return size, lines
    return None, None


tl, sfx, hosts, css = [], [], [], []

# ---------- Phụ đề: cụm tách theo dấu câu / khoảng nghỉ / số từ, không vừa ô thì tách đôi ----------
words = json.loads((WORK / "transcript.json").read_text())
words = [w for w in words if w.get("text", "").strip()]
for w in words:
    w["text"] = FIX.get(w["text"], w["text"]).upper() if CASE == "upper" else FIX.get(w["text"], w["text"])
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if w["text"][-1] in ",.?!:" or len(cur) >= CAP_WORDS or not nxt or nxt["start"] - w["end"] > 0.35:
        groups.append(cur)
        cur = []
stack, final = list(groups), []
while stack:
    g = stack.pop(0)
    if fit([w["text"] for w in g])[0] or len(g) == 1:
        final.append(g)
    else:
        m = len(g) // 2
        stack[:0] = [g[:m], g[m:]]
groups = final

caps = []
for gi, g in enumerate(groups):
    size, lines = fit([w["text"] for w in g])
    if not size:
        raise SystemExit(f"từ quá dài cho cột phụ đề {CAP_W}px: {g[0]['text']}")
    st = max(0, g[0]["start"] - CAP_LEAD)
    en = groups[gi + 1][0]["start"] - CAP_LEAD if gi + 1 < len(groups) else DURATION
    en = min(en, g[-1]["end"] + 0.8, DURATION)
    rows = "".join("<div>" + " ".join(f'<span class="cw" id="c{gi}w{i}">{html.escape(g[i]["text"])}</span>' for i in ln) + "</div>" for ln in lines)
    caps.append(f'<div class="cg" id="cg{gi}"><div class="cb" style="font-size:{size}px">{rows}</div></div>')
    tl.append(f"tl.set('#cg{gi}', {{visibility:'visible'}}, {q(st)});")
    tl.append(f"tl.fromTo('#cg{gi} .cb', {{opacity:0, y:10}}, {{opacity:1, y:0, duration:0.12, ease:'power2.out'}}, {q(st)});")
    for i, w in enumerate(g):
        ws = max(0, w["start"] - CAP_LEAD)
        tl.append(f"tl.set('#c{gi}w{i}', {{color:'{ACC}'}}, {q(ws)});")
        nxt_s = g[i + 1]["start"] - CAP_LEAD if i + 1 < len(g) else en
        tl.append(f"tl.set('#c{gi}w{i}', {{color:'{FG}'}}, {q(max(ws + 1 / FPS, nxt_s))});")
    tl.append(f"tl.set('#cg{gi}', {{visibility:'hidden'}}, {q(en)});")

# ---------- Zoom màn hình: tâm là điểm thao tác nên mép video không bao giờ lộ ----------
for i, (s, e, x, y, z) in enumerate(ZOOMS):
    tl.append(f"tl.set('#v-screen', {{transformOrigin:'{x * 100:.1f}% {y * 100:.1f}%'}}, {q(s)});")
    tl.append(f"tl.to('#v-screen', {{scale:{z}, duration:0.6, ease:'power2.inOut'}}, {q(s)});")
    tl.append(f"tl.to('#v-screen', {{scale:1, duration:0.6, ease:'power2.inOut'}}, {q(e - 0.6)});")

# ---------- Nhãn bước: chỉ có chữ, không icon/số tròn ----------
for i, (s, e, text) in enumerate(STEPS):
    hosts.append(f'<div id="st{i}" class="step clip" data-start="{q(s)}" data-duration="{e - s:.4f}" data-track-index="{5 + i % 2}">{html.escape(text)}</div>')
    tl.append(f"tl.fromTo('#st{i}', {{opacity:0, y:12}}, {{opacity:1, y:0, duration:0.25, ease:'power2.out'}}, {q(s)});")
    sfx.append(("pop", s))
css.append(f".step {{ position:absolute; left:{SAFE_L}px; width:{SAFE_R - SAFE_L}px; top:{FREE_T}px; height:{max(FREE_B - FREE_T, 90)}px; "
           f"display:flex; align-items:center; justify-content:center; text-align:center; color:#fff; font:800 56px/1.2 'Be Vietnam Pro',sans-serif; }}")

if BG_DRIFT > 1 and (PUB / "bg.mp4").exists():
    tl.append(f"tl.fromTo('#v-bg', {{scale:1.0}}, {{scale:{BG_DRIFT}, duration:{DURATION}, ease:'none'}}, 0);")

# ---------- Âm thanh: tiếng nằm trong face.mp4 ----------
aud = [f'<audio id="voice" src="face.mp4" data-start="0" data-duration="{DURATION}" data-track-index="30" data-volume="1"></audio>']
if MUSIC and (PUB / "audio/music_loop.m4a").exists():   # nhạc nền tuỳ chọn (concepts/tutorial.md)
    aud.append(f'<audio id="music" src="audio/music_loop.m4a" data-start="0" data-duration="{DURATION}" data-track-index="31" data-volume="{MUSIC}"></audio>')
# cue = (vai, mốc hình): bộ SFX tự neo whoosh/impact theo điểm to nhất, pop/click theo điểm bắt đầu
kit_tags = sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(32, 60), log=WORK / "sfx_cues.json")
if kit_tags is not None:
    aud += kit_tags
else:   # không đọc được assets/sfx/kit.json: bộ âm cũ trong public/audio/
    for i, (n, t) in enumerate(sorted(sfx, key=lambda e: e[1])):
        aud.append(f'<audio id="sfx{i:02d}" src="audio/{n}.m4a" data-start="{t:.3f}" data-duration="0.5" data-track-index="{32 + i}" data-volume="{SFX_VOL[n] * SFX_GAIN:.3f}"></audio>')

NL = "\n"
fonts = "\n".join(f'@font-face {{ font-family:"Be Vietnam Pro"; src:url("fonts/BeVietnamPro-{n}.ttf"); font-weight:{wt}; font-display:block; }}'
                  for n, wt in (("ExtraBold", 800), ("Black", 900)))
bg = (f'<video id="v-bg" src="bg.mp4" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="0"></video><div id="bg-dim"></div>'
      if (PUB / "bg.mp4").exists() else "")
index = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8" />
<style>
{fonts}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; }}
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#101114; }}
#v-bg {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
#bg-dim {{ position:absolute; inset:0; background:rgba(10,11,14,{BG_DIM}); }}
#screen {{ position:absolute; left:0; top:{SCREEN_Y}px; width:{W}px; height:{SCREEN_H}px; overflow:hidden; box-shadow:0 18px 60px rgba(0,0,0,.5); }}
#v-screen {{ display:block; width:100%; height:100%; object-fit:cover; }}
#face {{ position:absolute; left:{FACE_X}px; top:{FACE_Y}px; width:{FACE}px; height:{FACE}px; overflow:hidden; border-radius:24px;
  box-shadow:0 12px 40px rgba(0,0,0,.45), 0 0 0 1px rgba(255,255,255,.14); }}
#v-face {{ display:block; width:100%; height:100%; object-fit:cover; }}
#captions {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; pointer-events:none; }}
#captions .cg {{ position:absolute; left:{CAP_L}px; width:{CAP_W}px; top:{FACE_Y}px; height:{FACE}px; display:flex; align-items:center; visibility:hidden; }}
#captions .cb {{ width:100%; color:{FG}; font-family:"Be Vietnam Pro",sans-serif; font-weight:900; line-height:1.22; letter-spacing:-.01em;
  text-align:{"left" if FACE_SIDE == "left" else "right"}; text-shadow:0 2px 4px rgba(0,0,0,.6), 0 4px 22px rgba(0,0,0,.75); }}
#captions .cw {{ display:inline-block; }}
{NL.join(css)}
</style></head>
<body>
<div id="stage" data-composition-id="tutorial" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
  {bg}
  <div id="screen"><video id="v-screen" src="screen.mp4" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="1"></video></div>
  <div id="face"><video id="v-face" src="face.mp4" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="2"></video></div>
  <div id="captions" class="clip" data-start="0" data-duration="{DURATION}" data-track-index="4">{"".join(caps)}</div>
{NL.join(hosts)}
{NL.join(aud)}
  <script src="vendor/gsap.min.js"></script>
  <script>
  (function () {{
    const tl = window.gsap.timeline({{ paused: true }});
    {(NL + '    ').join(tl)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["tutorial"] = tl;
  }})();
  </script>
</div>
</body></html>
"""
(PUB / "index.html").write_text(index)
print(f"{DURATION}s | màn hình y {SCREEN_Y}-{SCREEN_Y + SCREEN_H} | mặt x {FACE_X} y {FACE_Y}-{FACE_Y + FACE} | phụ đề x {CAP_L}-{CAP_R} ({CAP_W}px) | {len(groups)} cụm")
