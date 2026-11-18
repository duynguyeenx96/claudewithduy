"""Bản mẫu concept ui (demo review Google Flow): A-roll người nói + mockup UI nền trắng. Có public/voice.wav (giọng thu riêng) thì
phát giọng đó và tắt tiếng A-roll; không có thì phát tiếng của A-roll.

python3 build.py   # dựng public/index.html
"""
import html
import json
from pathlib import Path

import sys
import os
SK = os.environ.get("TOOL_VIDEO_SK") or sys.exit("thiếu TOOL_VIDEO_SK: chạy TOOL_VIDEO_SK=<thư mục skill tool-video> python3 build.py")
sys.path.insert(0, os.path.join(SK, "scripts"))
from sfxkit import sfx_tags   # bộ SFX CC0 của skill: mức + điểm neo theo vai, xoay vòng bản
WORK = Path(__file__).parent
PUB = WORK / "public"
FPS, W, H = 30, 1080, 1920
DURATION = 22.6
FONT = '"Be Vietnam Pro", sans-serif'
LIME, INK, BLUE, PAPER = "#c6ff3d", "#111111", "#4c8df6", "#f5f5f2"
CAP_Y = 1380   # vùng an toàn: đáy phụ đề ≤ 1500 (SAFE_ZONE.md của skill)
AROLL = __import__("os").environ.get("AROLL", "aroll.mp4")

tl, sfx, css, hosts = [], [], [], []


def q(t):
    return f"{round(t * FPS) / FPS:.4f}"


def scene(sid, start, end, inner, style, track=3, enter="card"):
    hosts.append(f'<div id="{sid}" class="scene clip" data-start="{start:.4f}" data-duration="{end - start:.4f}" data-track-index="{track}">{inner}</div>')
    css.append(style)
    if enter == "card":
        tl.append(f"tl.fromTo('#{sid}', {{opacity:0, scale:1.06}}, {{opacity:1, scale:1, duration:0.22, ease:'power3.out'}}, {q(start)});")
        sfx.append(("whoosh", start + 0.04))
    if end < DURATION:
        tl.append(f"tl.to('#{sid}', {{opacity:0, scale:0.97, duration:0.14, ease:'power2.in'}}, {q(end - 0.14)});")


def chip(cid, label, icon, top, left=None, big=False):
    el = f'<span class="ci">{icon}</span>{html.escape(label)}</div>'
    if left is not None:
        return f'<div class="chip{" big" if big else ""}" id="{cid}" style="top:{top}px;left:{left}px;">' + el
    # căn giữa bằng hàng bọc ngoài: GSAP scale/x trên chip không đè mất translateX
    return (f'<div class="chip-row" style="top:{top}px"><div class="chip{" big" if big else ""}" id="{cid}" style="position:relative;">'
            + el + '</div>')


def pop(sel, at, sound=True):
    tl.append(f"tl.from('{sel}', {{scale:0, opacity:0, duration:0.35, ease:'back.out(2.2)'}}, {q(at)});")
    if sound:
        sfx.append(("pop", at))


css.append(f"""
  .chip {{ position:absolute; display:inline-flex; align-items:center; gap:16px; padding:18px 30px 18px 20px; border-radius:999px;
    background:rgba(17,17,17,.88); color:#fff; font:800 46px/1 {FONT}; white-space:nowrap; box-shadow:0 18px 40px rgba(0,0,0,.35);
    border:2px solid rgba(255,255,255,.12); }}
  .chip-row {{ position:absolute; left:0; right:0; text-align:center; }}
  .chip .ci {{ display:inline-flex; align-items:center; justify-content:center; width:66px; height:66px; border-radius:50%; background:{LIME};
    color:{INK}; font-size:36px; }}
  .chip.big {{ font-size:62px; padding:22px 40px 22px 24px; }}
  .chip.big .ci {{ width:84px; height:84px; font-size:46px; }}""")

# ---------- S1 Hook (0–2.14): người nói full + "KHOAN!" + chip ê-kíp bị gạch ----------
scene("s1", 0, 2.14, f"""
  <div id="khoan">KHOAN!</div>
  {chip('ekip', 'Ê-kíp quay dựng', '🎬', 1200)}
  <div id="ekip-x"></div>""", f"""
  #khoan {{ position:absolute; left:0; right:0; top:960px; text-align:center; font:900 230px/1 {FONT}; color:{LIME};
    letter-spacing:-.03em; -webkit-text-stroke:10px {INK}; paint-order:stroke fill; text-shadow:0 20px 50px rgba(0,0,0,.5); }}
  #ekip-x {{ position:absolute; left:270px; width:540px; top:1242px; height:16px; border-radius:8px; background:#ff3b4a;
    transform:rotate(-6deg); transform-origin:left center; }}""", enter="none")
tl.append(f"tl.fromTo('#khoan', {{scale:2.6, opacity:0}}, {{scale:1, opacity:1, duration:0.28, ease:'power4.out'}}, {q(0.02)});")
tl.append(f"tl.to('#khoan', {{opacity:0, y:-80, duration:0.2, ease:'power2.in'}}, {q(0.75)});")
pop("#ekip", 0.86)
tl.append(f"tl.fromTo('#ekip-x', {{scaleX:0}}, {{scaleX:1, duration:0.2, ease:'power2.out'}}, {q(1.86)});")
sfx += [("whoosh", 0.0), ("wrong", 1.86)]

# ---------- S2 (2.14–5.55): cửa sổ trình duyệt + video Flow + "Studio AI làm video" ----------
scene("s2", 2.14, 5.55, f"""
  <div class="paper"></div>
  <div id="brw"><div class="bar"><i></i><i></i><i></i><div class="url">flow.google.com</div></div>
    <div class="vid"><video src="hero.mp4" muted playsinline data-start="2.14" data-duration="3.41" data-track-index="7"></video>
      <div id="brw-dim"></div><div id="wordmark">Google Flow</div></div></div>
  <div id="s2-title"><div class="l1">Studio AI</div><div class="l2">làm video</div></div>
  {chip('s2-chip', 'ngay trên trình duyệt', '🌐', 1250)}""", f"""
  .paper {{ position:absolute; inset:0; background:{PAPER};
    background-image:radial-gradient(rgba(0,0,0,.09) 2px, transparent 2px); background-size:40px 40px; }}
  #brw {{ position:absolute; left:70px; top:260px; width:940px; border-radius:28px; overflow:hidden; background:#000;
    box-shadow:0 40px 90px -20px rgba(0,0,0,.45); border:1px solid rgba(0,0,0,.1); }}
  #brw .bar {{ height:56px; display:flex; align-items:center; gap:10px; padding:0 22px; background:#1b1b1b; }}
  #brw .bar i {{ width:14px; height:14px; border-radius:50%; background:#555; }}
  #brw .url {{ margin-left:18px; flex:1; height:34px; border-radius:10px; background:#0d0d0d; color:#bbb; font:500 20px/34px {FONT}; padding-left:16px; }}
  #brw .vid {{ position:relative; height:560px; }}
  #brw video {{ width:100%; height:100%; object-fit:cover; }}
  #brw-dim {{ position:absolute; inset:0; background:rgba(0,0,0,.45); opacity:0; }}
  #wordmark {{ position:absolute; left:0; right:0; top:50%; transform:translateY(-50%); text-align:center; color:#fff;
    font:700 120px/1 {FONT}; letter-spacing:-.02em; }}
  #s2-title {{ position:absolute; left:0; right:0; top:900px; text-align:center; color:{INK}; font:900 150px/0.98 {FONT}; letter-spacing:-.03em; }}
  #s2-title .l2 {{ display:inline-block; background:{LIME}; padding:0 24px 14px; border-radius:24px; margin-top:12px; }}
  #s2-chip {{ background:#fff; color:{INK}; border-color:rgba(0,0,0,.08); box-shadow:0 18px 40px -10px rgba(0,0,0,.2); }}""")
tl.append(f"tl.fromTo('#brw', {{y:200, rotationX:25, opacity:0}}, {{y:0, rotationX:0, opacity:1, duration:0.4, ease:'power3.out'}}, {q(2.14)});")
tl.append(f"tl.to('#brw-dim', {{opacity:1, duration:0.2}}, {q(2.42)});")
tl.append(f"tl.from('#wordmark', {{opacity:0, scale:0.7, filter:'blur(12px)', duration:0.35, ease:'power3.out'}}, {q(2.46)});")
tl.append(f"tl.from('#s2-title > div', {{opacity:0, y:60, duration:0.28, ease:'power3.out', stagger:0.45}}, {q(3.62)});")
pop("#s2-chip", 4.76)
sfx.append(("pop", 3.62))

# ---------- S3 (5.55–10.65): chat UI: gõ prompt, chọn Veo 3.1, lưới kết quả + âm thanh ----------
prompt = "Chú cá vàng nhảy trên bãi cát, nắng chiều, cinematic"
tiles = ["t-fish.mp4", "t-clay.mp4", "t-boy.mp4", "t-sun.mp4"]
TS = 360
tile_html = "".join(
    f'<div class="tile" id="tile{i}" style="left:{(i % 2) * (TS + 20)}px;top:{(i // 2) * (TS + 20)}px">'
    f'<div class="gen" id="gen{i}"><div class="spin"></div><span>Generating… <b id="pct{i}">0</b>%</span></div>'
    f'<video id="tv{i}" src="{f}" muted playsinline data-start="9.25" data-duration="1.40" data-track-index="{8 + i}"></video></div>'
    for i, f in enumerate(tiles))
models = [("Veo 3.1", "Video + âm thanh"), ("Gemini Omni", "Sửa bằng lời"), ("Nano Banana", "Ảnh")]
menu = "".join(f'<div class="mi" id="mi{i}"><b>{m}</b><span>{d}</span></div>' for i, (m, d) in enumerate(models))
scene("s3", 5.55, 10.65, f"""
  <div class="paper"></div>
  <div id="s3-head"><span class="dot"></span>Google Flow<span class="proj">· Project mới</span></div>
  <div id="hint">Bạn muốn tạo gì hôm nay?</div>
  <div id="ubub">{html.escape(prompt)}</div>
  <div id="grid">{tile_html}<div id="audio-badge"><span class="eq"><i></i><i></i><i></i><i></i><i></i></span>Có cả âm thanh</div></div>
  <div id="pbar"><div id="ptext">{''.join(f'<span class="pc">{html.escape(c)}</span>' for c in prompt)}<span id="pcar"></span></div>
    <div id="pmodel">Veo 3.1 <small>▾</small></div><div id="psend">↑</div></div>
  <div id="menu">{menu}</div>
  <svg id="cursor" viewBox="0 0 40 40" width="64" height="64"><path d="M6 3 L6 33 L14 25 L20 37 L25 35 L19 23 L30 23 Z" fill="#111" stroke="#fff" stroke-width="2.5"/></svg>""", f"""
  #s3-head {{ position:absolute; left:70px; top:260px; display:flex; align-items:center; gap:14px; color:{INK}; font:700 40px/1 {FONT}; }}
  #s3-head .dot {{ width:34px; height:34px; border-radius:10px; background:conic-gradient(#4285f4 0 25%, #ea4335 0 50%, #fbbc05 0 75%, #34a853 0); }}
  #s3-head .proj {{ color:#888; font-weight:500; }}
  #hint {{ position:absolute; left:0; right:0; top:780px; text-align:center; color:#9a9a94; font:700 64px/1.2 {FONT}; }}
  #ubub {{ position:absolute; right:70px; top:330px; max-width:820px; padding:22px 30px; border-radius:30px 30px 8px 30px; background:{INK};
    color:#fff; font:600 34px/1.3 {FONT}; opacity:0; }}
  #grid {{ position:absolute; left:{(W - TS * 2 - 20) // 2}px; top:480px; width:{TS * 2 + 20}px; height:{TS * 2 + 20}px; }}
  .tile {{ position:absolute; width:{TS}px; height:{TS}px; border-radius:28px; overflow:hidden; background:#e7e7e3; opacity:0;
    box-shadow:0 20px 40px -18px rgba(0,0,0,.35); }}
  .tile video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0; }}
  .gen {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:22px;
    color:#666; font:600 30px/1 {FONT};
    background:linear-gradient(110deg, #e7e7e3 30%, #f6f6f3 50%, #e7e7e3 70%); background-size:300% 100%; }}
  .spin {{ width:64px; height:64px; border-radius:50%; border:7px solid #cfcfca; border-top-color:{BLUE}; }}
  #audio-badge {{ position:absolute; left:24px; top:{TS - 96}px; display:inline-flex; align-items:center; gap:14px; padding:14px 24px;
    border-radius:999px; background:{LIME}; color:{INK}; font:800 34px/1 {FONT}; opacity:0; box-shadow:0 10px 30px rgba(0,0,0,.3); }}
  .eq {{ display:inline-flex; align-items:flex-end; gap:5px; height:34px; }}
  .eq i {{ width:7px; height:34px; border-radius:4px; background:{INK}; transform-origin:bottom; }}
  #pbar {{ position:absolute; left:70px; right:70px; top:1220px; height:132px; border-radius:40px; background:#fff; display:flex; align-items:center;
    gap:16px; padding:0 22px 0 38px; box-shadow:0 24px 60px -20px rgba(0,0,0,.3); border:1px solid rgba(0,0,0,.08); }}
  #ptext {{ flex:1; color:{INK}; font:500 32px/1.25 {FONT}; overflow:hidden; height:80px; }}
  #pcar {{ display:inline-block; width:3px; height:34px; background:{BLUE}; vertical-align:-6px; }}
  #pmodel {{ padding:16px 22px; border-radius:999px; background:#efefea; color:{INK}; font:700 30px/1 {FONT}; white-space:nowrap; }}
  #pmodel small {{ font-size:22px; color:#888; }}
  #psend {{ width:84px; height:84px; border-radius:50%; background:{INK}; color:#fff; font:800 44px/84px {FONT}; text-align:center; }}
  #menu {{ position:absolute; right:180px; top:900px; width:470px; padding:14px; border-radius:30px; background:#fff;
    box-shadow:0 30px 70px -20px rgba(0,0,0,.35); border:1px solid rgba(0,0,0,.08); opacity:0; transform-origin:70% 100%; }}
  .mi {{ display:flex; flex-direction:column; gap:6px; padding:18px 22px; border-radius:20px; }}
  .mi b {{ color:{INK}; font:800 36px/1 {FONT}; }}
  .mi span {{ color:#888; font:500 26px/1 {FONT}; }}
  #cursor {{ position:absolute; left:700px; top:1420px; opacity:0; }}""")
tl.append(f"tl.from('#pbar', {{y:220, opacity:0, duration:0.3, ease:'power3.out'}}, {q(5.6)});")
tl.append(f"tl.from('#pmodel', {{opacity:0, duration:0.01}}, {q(5.6)});")
tl.append(f"tl.from('#ptext .pc', {{display:'none', duration:0.01, stagger:0.013}}, {q(5.72)});")
# chọn model: con trỏ tới chip, mở menu, chọn Veo 3.1
tl.append(f"tl.to('#cursor', {{opacity:1, duration:0.1}}, {q(6.5)});")
tl.append(f"tl.to('#cursor', {{left:810, top:1270, duration:0.35, ease:'power2.inOut'}}, {q(6.5)});")
tl.append(f"tl.fromTo('#pmodel', {{scale:1}}, {{scale:0.9, duration:0.08, yoyo:true, repeat:1}}, {q(6.86)});")
tl.append(f"tl.fromTo('#menu', {{opacity:0, scale:0.6}}, {{opacity:1, scale:1, duration:0.25, ease:'back.out(1.8)'}}, {q(6.9)});")
tl.append(f"tl.to('#cursor', {{left:660, top:955, duration:0.28, ease:'power2.inOut'}}, {q(7.0)});")
tl.append(f"tl.to('#mi0', {{backgroundColor:'{LIME}', duration:0.1}}, {q(7.24)});")
tl.append(f"tl.to('#menu', {{opacity:0, scale:0.8, duration:0.15}}, {q(7.5)});")
tl.append(f"tl.to('#cursor', {{left:900, top:1280, duration:0.3, ease:'power2.inOut'}}, {q(7.55)});")
tl.append(f"tl.fromTo('#psend', {{scale:1}}, {{scale:0.8, duration:0.08, yoyo:true, repeat:1}}, {q(7.9)});")
tl.append(f"tl.to('#cursor', {{opacity:0, duration:0.15}}, {q(8.1)});")
sfx += [("click", 6.86), ("click", 7.24), ("click", 7.9)]
# gửi: prompt bay lên thành bong bóng, 4 ô Generating…, rồi lộ video
tl.append(f"tl.to('#ptext', {{opacity:0, duration:0.1}}, {q(7.95)});")
tl.append(f"tl.to('#hint', {{opacity:0, y:-40, duration:0.15}}, {q(7.95)});")
tl.append(f"tl.fromTo('#ubub', {{opacity:0, y:900, scale:0.7}}, {{opacity:1, y:0, scale:1, duration:0.4, ease:'power3.out'}}, {q(7.95)});")
tl.append(f"tl.to('.tile', {{opacity:1, duration:0.25, stagger:0.06}}, {q(8.04)});")
tl.append(f"tl.from('.tile', {{scale:0.6, duration:0.35, ease:'back.out(1.6)', stagger:0.06}}, {q(8.04)});")
tl.append(f"tl.fromTo('.gen', {{backgroundPosition:'100% 0'}}, {{backgroundPosition:'-100% 0', duration:1.2, ease:'none'}}, {q(8.04)});")
tl.append(f"tl.fromTo('.spin', {{rotation:0}}, {{rotation:540, duration:1.2, ease:'none'}}, {q(8.04)});")
tl.append(f"(function(){{const o={{v:0}};tl.to(o, {{v:100, duration:1.15, ease:'power1.in', onUpdate:function(){{"
          f"for(let i=0;i<4;i++){{const e=document.getElementById('pct'+i);if(e)e.textContent=Math.min(100,Math.round(o.v*(0.85+i*0.05)));}}}}}}, {q(8.1)});}})();")
for i in range(4):
    t = 9.25 + i * 0.08
    tl.append(f"tl.to('#gen{i}', {{opacity:0, duration:0.15}}, {q(t)});")
    tl.append(f"tl.to('#tv{i}', {{opacity:1, duration:0.15}}, {q(t)});")
    tl.append(f"tl.fromTo('#tile{i}', {{scale:0.92}}, {{scale:1, duration:0.3, ease:'back.out(2)'}}, {q(t)});")
sfx.append(("pop", 9.25))
tl.append(f"tl.fromTo('#audio-badge', {{opacity:0, scale:0.4}}, {{opacity:1, scale:1, duration:0.3, ease:'back.out(2)'}}, {q(9.95)});")
for k in range(5):
    tl.append(f"tl.fromTo('#audio-badge .eq i:nth-child({k + 1})', {{scaleY:0.25}}, {{scaleY:1, duration:{0.12 + k * 0.03:.2f}, yoyo:true, repeat:5, ease:'sine.inOut'}}, {q(9.95)});")

# ---------- S4 (10.65–11.90 người nói) + S4b (11.90–13.96): Gemini Omni sửa bằng lời ----------
scene("s4", 10.65, 11.90, chip("s4-chip", "Sửa bằng lời nói", "💬", 1150), "", enter="none")
pop("#s4-chip", 11.0)
scene("s4b", 11.90, 13.96, f"""
  <div class="paper dark"></div>
  {chip('omni', 'Gemini Omni', '✦', 260, big=True)}
  <div id="rf"><video src="refine.mp4" muted playsinline data-start="11.90" data-duration="2.06" data-track-index="7"></video></div>
  <div id="rf-bub">"Đổi cảnh sang hoàng hôn"</div>""", f"""
  .paper.dark {{ background:#0c0d0c; background-image:radial-gradient(rgba(255,255,255,.07) 2px, transparent 2px); background-size:40px 40px; }}
  #omni {{ background:#fff; color:{INK}; }}
  #rf {{ position:absolute; left:70px; top:440px; width:940px; height:529px; border-radius:30px; overflow:hidden;
    border:2px solid rgba(255,255,255,.18); box-shadow:0 40px 100px rgba(0,0,0,.6); }}
  #rf video {{ width:100%; height:100%; object-fit:cover; }}
  #rf-bub {{ position:absolute; right:180px; top:1030px; padding:24px 34px; border-radius:30px 30px 8px 30px; background:{LIME}; color:{INK};
    font:800 46px/1.2 {FONT}; }}""")
tl.append(f"tl.from('#omni', {{scale:0, opacity:0, duration:0.35, ease:'back.out(2)'}}, {q(12.1)});")
tl.append(f"tl.from('#rf', {{y:120, opacity:0, scale:0.9, duration:0.35, ease:'power3.out'}}, {q(11.95)});")
tl.append(f"tl.to('#rf', {{scale:1.06, duration:1.6, ease:'none'}}, {q(12.3)});")
pop("#rf-bub", 12.4)

# ---------- S5 (13.96–16.98 người nói): badge model + dải nhân vật đồng nhất ----------
strip = "".join(f'<img class="cf" id="cf{i}" src="img/clay{i}.jpg">' for i in range(3))
scene("s5", 13.96, 16.98, f"""
  {chip('b-veo', 'Veo 3.1', '🎬', 260, left=70)}
  {chip('b-omni', 'Gemini Omni', '✦', 260, left=500)}
  {chip('b-nano', 'Nano Banana', '🍌', 1090, big=True)}
  <div id="strip">{strip}<div id="strip-tag">✓ Cùng 1 nhân vật</div></div>""", f"""
  #b-veo, #b-omni {{ font-size:38px; padding:12px 26px 12px 14px; }}
  #b-veo .ci, #b-omni .ci {{ width:54px; height:54px; font-size:28px; }}
  #b-nano {{ background:{LIME}; color:{INK}; }}
  #b-nano .ci {{ background:{INK}; }}
  #strip {{ position:absolute; left:50%; top:1150px; transform:translateX(-50%); display:flex; gap:16px; padding:16px; border-radius:30px;
    background:rgba(17,17,17,.88); }}
  .cf {{ width:250px; height:250px; border-radius:20px; object-fit:cover; }}
  #strip-tag {{ position:absolute; left:50%; bottom:-34px; transform:translateX(-50%); padding:12px 24px; border-radius:999px; background:{LIME};
    color:{INK}; font:800 32px/1 {FONT}; white-space:nowrap; }}""", enter="none")
tl.append(f"tl.from('#b-veo, #b-omni', {{y:-60, opacity:0, duration:0.3, ease:'power3.out', stagger:0.1}}, {q(14.0)});")
pop("#b-nano", 14.68)
tl.append(f"tl.from('#strip', {{opacity:0, y:80, duration:0.3, ease:'power3.out'}}, {q(15.55)});")
tl.append(f"tl.from('.cf', {{scale:0.3, opacity:0, duration:0.3, ease:'back.out(2)', stagger:0.12}}, {q(15.6)});")
tl.append(f"tl.from('#strip-tag', {{scale:0, duration:0.3, ease:'back.out(2)'}}, {q(16.1)});")
sfx += [("pop", 15.6), ("pop", 16.1)]

# ---------- S6 (16.98–20.20): agent + kho tool ----------
tools = [("Type Overlays", -250, -340), ("Storyboard Studio", 260, -340), ("Image Editor", 0, -430), ("Mockup", -290, -520),
         ("Scout360", 290, -520), ("Video Resizer", -260, 340), ("Shader Effects", 260, 340), ("pixelBento", 0, 420)]
tool_html = "".join(f'<div class="tp" id="tp{i}" style="left:{540 + x}px;top:{800 + y}px">{n}</div>' for i, (n, x, y) in enumerate(tools))
plan = ["Kịch bản", "Nhân vật", "Cảnh quay"]
scene("s6", 16.98, 20.20, f"""
  <div class="paper"></div>
  {tool_html}
  <div id="core"><div class="dot"></div><div class="nm">Google Flow</div>
    <div id="agent"><span class="ci">✦</span>Agent lên kế hoạch</div>
    <div id="plan">{''.join(f'<div class="pl" id="pl{i}"><b>{i + 1}</b>{p}</div>' for i, p in enumerate(plan))}</div></div>
  <div id="newtool">＋ Tự build tool</div>""", f"""
  #core {{ position:absolute; left:50%; top:800px; transform:translate(-50%,-50%); width:620px; padding:44px 40px 40px; border-radius:40px; background:#fff;
    box-shadow:0 40px 90px -30px rgba(0,0,0,.4); border:1px solid rgba(0,0,0,.08); text-align:center; }}
  #core .dot {{ width:80px; height:80px; margin:0 auto 18px; border-radius:22px; background:conic-gradient(#4285f4 0 25%, #ea4335 0 50%, #fbbc05 0 75%, #34a853 0); }}
  #core .nm {{ color:{INK}; font:800 66px/1 {FONT}; letter-spacing:-.02em; }}
  #agent {{ display:inline-flex; align-items:center; gap:14px; margin-top:28px; padding:14px 28px 14px 14px; border-radius:999px; background:{INK};
    color:#fff; font:800 38px/1 {FONT}; }}
  #agent .ci {{ width:56px; height:56px; border-radius:50%; background:{LIME}; color:{INK}; display:inline-flex; align-items:center; justify-content:center; }}
  #plan {{ margin-top:26px; display:flex; flex-direction:column; gap:12px; text-align:left; }}
  .pl {{ display:flex; align-items:center; gap:18px; padding:14px 20px; border-radius:18px; background:#f1f1ec; color:{INK}; font:700 36px/1 {FONT}; }}
  .pl b {{ width:48px; height:48px; border-radius:50%; background:{LIME}; display:inline-flex; align-items:center; justify-content:center; font-size:28px; }}
  .tp {{ position:absolute; transform:translate(-50%,-50%); padding:18px 30px; border-radius:999px; background:#fff; color:{INK};
    font:700 36px/1 {FONT}; white-space:nowrap; border:2px solid {INK}; box-shadow:0 14px 30px -12px rgba(0,0,0,.3); }}
  #newtool {{ position:absolute; left:50%; top:1270px; transform:translateX(-50%); padding:24px 44px; border-radius:999px; background:{LIME};
    color:{INK}; font:900 54px/1 {FONT}; white-space:nowrap; box-shadow:0 20px 50px -10px rgba(120,160,0,.6); }}""")
tl.append(f"tl.from('#core', {{scale:0.6, opacity:0, duration:0.35, ease:'back.out(1.6)'}}, {q(17.0)});")
pop("#agent", 17.62)
tl.append(f"tl.from('.pl', {{x:-60, opacity:0, duration:0.22, ease:'power3.out', stagger:0.18}}, {q(17.95)});")
for i, (_n, x, y) in enumerate(tools):
    t = 19.05 + i * 0.06
    tl.append(f"tl.fromTo('#tp{i}', {{x:{-x * 0.8:.0f}, y:{-y * 0.8:.0f}, scale:0, opacity:0}}, {{x:0, y:0, scale:1, opacity:1, duration:0.4, ease:'back.out(1.4)'}}, {q(t)});")
    tl.append(f"tl.to('#tp{i}', {{y:{-12 if i % 2 else 12}, duration:0.6, ease:'sine.inOut', yoyo:true, repeat:1}}, {q(t + 0.4)});")
sfx.append(("pop", 19.05))
pop("#newtool", 19.6)

# ---------- S7 (20.20–21.25 người nói): lưu lại ----------
scene("s7", 20.20, 21.25, chip("save", "Lưu lại ngay", "🔖", 1120, big=True), "", enter="none")
pop("#save", 20.3)

# ---------- Outro (21.25–hết): 2 thanh lime khép lại ----------
scene("outro", 21.25, DURATION, """
  <div id="bar-t" class="ob"></div><div id="bar-b" class="ob"></div>
  <div id="out-in"><div class="dot"></div><div class="nm">Google Flow</div><div class="url">flow.google.com</div>
    <div class="cta">Thử ngay →</div></div>""", f"""
  .ob {{ position:absolute; left:0; width:{W}px; height:{H // 2 + 2}px; background:{LIME}; }}
  #bar-t {{ top:0; transform-origin:top; }}
  #bar-b {{ bottom:0; transform-origin:bottom; }}
  #out-in {{ position:absolute; left:0; right:0; top:620px; text-align:center; }}
  #out-in .dot {{ width:150px; height:150px; margin:0 auto 34px; border-radius:40px; background:{INK};
    background:conic-gradient(#4285f4 0 25%, #ea4335 0 50%, #fbbc05 0 75%, #34a853 0); }}
  #out-in .nm {{ color:{INK}; font:900 128px/1 {FONT}; letter-spacing:-.03em; }}
  #out-in .url {{ margin-top:20px; color:{INK}; font:700 52px/1 {FONT}; opacity:.75; }}
  #out-in .cta {{ display:inline-block; margin-top:50px; padding:26px 54px; border-radius:999px; background:{INK}; color:{LIME}; font:900 58px/1 {FONT}; }}""",
      track=6, enter="none")
tl.append(f"tl.fromTo('#bar-t, #bar-b', {{scaleY:0}}, {{scaleY:1, duration:0.32, ease:'power4.inOut'}}, {q(21.25)});")
tl.append(f"tl.from('#out-in > *', {{y:50, opacity:0, duration:0.3, ease:'power3.out', stagger:0.08}}, {q(21.55)});")
sfx += [("whoosh", 21.2), ("pop", 21.6)]

# ---------- Người nói: zoom nhấn ở mỗi lần quay lại / nối đoạn ----------
for t, s in ([(0.0, 1.18), (10.65, 1.1), (13.96, 1.1), (15.21, 1.12), (16.58, 1.08), (20.20, 1.12)] if AROLL == "aroll.mp4"
             else [(0.0, 1.18), (10.65, 1.1), (13.96, 1.1), (20.20, 1.12)]):
    tl.append(f"tl.fromTo('#aroll', {{scale:{s}}}, {{scale:1, duration:0.35, ease:'power3.out'}}, {q(t)});")

# ---------- Phụ đề (Whisper trên giọng TTS, sửa chính tả theo kịch bản) ----------
FIX = {"ekip": "ê-kíp", "VL3.1": "Veo 3.1", "Agent": "agent", "Khotune": "kho tool", '"Khoan,': "Khoan,", 'duyệt."': "duyệt."}
words = []
for w in json.loads((WORK / "transcript.raw.json").read_text()):
    t = FIX.get(w["text"], w["text"])
    if t == "bạn.Ảnh":
        words += [{"text": "bạn.", "start": w["start"], "end": 13.66}, {"text": "Ảnh", "start": 13.98, "end": 14.26}]
        continue
    words.append({**w, "text": t})
(WORK / "transcript.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
groups, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if w["text"][-1] in ",.!" or len(cur) >= 4 or not nxt:
        groups.append(cur)
        cur = []
caps = []
for gi, g in enumerate(groups):
    st = max(0, g[0]["start"] - 0.04)
    en = groups[gi + 1][0]["start"] - 0.04 if gi + 1 < len(groups) else DURATION
    en = min(en, g[-1]["end"] + 0.5, DURATION)
    spans = " ".join(f'<span class="cw" id="c{gi}w{wi}">{html.escape(w["text"].strip(",.!"))}</span>' for wi, w in enumerate(g))
    caps.append(f'<div class="cg" id="cg{gi}"><span class="cp">{spans}</span></div>')
    tl.append(f"tl.set('#cg{gi}', {{visibility:'visible'}}, {q(st)});")
    tl.append(f"tl.fromTo('#cg{gi}', {{scale:0.8, opacity:0}}, {{scale:1, opacity:1, duration:0.1, ease:'back.out(2)'}}, {q(st)});")
    for wi, w in enumerate(g):
        tl.append(f"tl.fromTo('#c{gi}w{wi}', {{color:'#ffffff'}}, {{color:'{LIME}', duration:0.04}}, {q(w['start'])});")
        tl.append(f"tl.to('#c{gi}w{wi}', {{color:'#ffffff', duration:0.04}}, {q(max(w['end'], w['start'] + 0.1))});")
    tl.append(f"tl.set('#cg{gi}', {{visibility:'hidden'}}, {q(en)});")
hosts.append(f'<div id="captions" class="clip" data-start="0" data-duration="{DURATION}" data-track-index="20">{"".join(caps)}</div>')
css.append(f"""
  #captions {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; z-index:20; pointer-events:none; }}
  #captions .cg {{ position:absolute; left:100px; right:170px; top:{CAP_Y}px; text-align:center; visibility:hidden; }}
  #captions .cp {{ display:inline-block; padding:16px 30px 20px; border-radius:26px; background:rgba(12,12,12,.9);
    font:900 64px/1.2 {FONT}; color:#fff; letter-spacing:-.01em; }}
  #captions .cw {{ display:inline-block; }}""")

# ---------- Âm thanh: giọng TTS + nhạc nền + SFX (footage tắt tiếng) ----------
SFX_LEN = {"pop": 0.552, "whoosh": 1.022, "click": 0.336, "wrong": 0.6}
SFX_VOL = {"pop": 0.45, "whoosh": 0.55, "click": 0.8, "wrong": 0.35}
SFX_GAIN = 0.85   # người dùng muốn SFX nhỏ hơn 15% (2026-10-23)
VOICE = "voice.wav" if (PUB / "voice.wav").exists() else AROLL
aud = [f'<audio id="voice" src="{VOICE}" data-start="0" data-duration="{DURATION}" data-track-index="30" data-volume="1"></audio>']
if (PUB / "audio/music.m4a").exists():   # nhạc nền tuỳ chọn: người dùng tự bỏ file vào public/audio/
    aud.append(f'<audio id="music" src="audio/music.m4a" data-start="0" data-duration="{DURATION}" data-track-index="31" data-volume="0.35"></audio>')
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
#stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
#video-wrap {{ position:absolute; inset:0; z-index:1; overflow:hidden; }}
#aroll {{ width:100%; height:100%; object-fit:cover; transform-origin:50% 30%; }}
.scene {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; overflow:hidden; z-index:3; }}
{NL.join(css)}
</style></head>
<body>
<div id="stage" data-composition-id="flow-review" data-start="0" data-duration="{DURATION}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
  <div id="video-wrap"><video id="aroll" src="{AROLL}" muted playsinline data-start="0" data-duration="{DURATION}" data-track-index="1"></video></div>
{NL.join(hosts)}
  <script src="vendor/gsap.min.js"></script>
  <script>
  (function () {{
    const tl = window.gsap.timeline({{ paused: true }});
    {(NL + '    ').join(tl)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["flow-review"] = tl;
  }})();
  </script>
</div>
</body></html>
"""
(PUB / "index.html").write_text(index)
print(f"{len(groups)} cụm phụ đề, {len(sfx)} SFX")
