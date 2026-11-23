---
name: effects
description: FX Free 05 · Số liệu & dựng. Add one of 9 talking-head video effects: liquid-glass-graph, split-graph, split-graph-v1, timeline, wave-trim, select-resize, editor, countdown-flip, broll-split. Effects track the speaker's face and can sit behind their head. Use when the user types /effects, names one of these effects, or asks for this kind of effect. Tiếng Việt: "hiệu ứng", "biểu đồ kính", "số liệu", "timeline dựng", "đồng hồ đếm ngược".
---

> Đọc `README.md` cạnh file này trước (lệnh chạy, phông tiếng Việt, vùng an toàn).

# FX Free 05 · Số liệu & dựng (9 hiệu ứng)

Gói này nằm trong bộ FX Free của Claude with Duy (6 gói, 59 hiệu ứng, miễn phí). Gói này chỉ có 9 hiệu ứng bên dưới.
Người dùng nhắc tới hiệu ứng không có ở đây: nói nó nằm trong gói nào (xem cuối file) và cách cài, đừng cố làm thay bằng hiệu ứng khác.

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands themselves.
All paths below are relative to this skill's folder: `${CLAUDE_SKILL_DIR}`. Use the absolute path in commands.

## 1. First run: set up (once)
Run `bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"`. Its last line is `READY <python>` (the first time takes 1 to 3 minutes; every FX Free pack shares this setup, so later packs are instant). Call that python `PY` and use it for every command below.
- `NEED_FFMPEG`: install it for them. On a Mac: `brew install ffmpeg` (if `brew` is missing, tell them to install Homebrew from brew.sh first). On Windows: `winget install ffmpeg`.
- `NEED_PYTHON`: install Python 3.12 (Mac: `brew install python@3.12`, Windows: `winget install Python.Python.3.12`), then run setup again.

## 2. Get the video and the effect
- Video: the user drags the file into the chat, or gives a path. A vertical phone video works best.
- Effect: from `/effects <name>`, or from what they describe. Match their words to the table below. Unsure? Show them the list.

## 3. Find the timing
- If they say "on the word X" or "when I say ...", run `$PY scripts/words.py <video>` and use those times.
- If they give no timing, apply the effect for the whole clip, or ask which part (one short question).
- Short windows look best: 1.5 to 4 seconds per effect.

## 4. Draft, check, render
1. Write the plan next to their video as `<video-name>_effects.json`:
   ```json
   {"effects": [{"fx": "liquid-glass-graph", "start": 3.2, "end": 6.0}]}
   ```
2. Check frames first (fast): `$PY custom/fx_vi.py --plan <plan.json> <video> <folder>/check.png --still 4.5`, using the middle of each effect. Look at the PNGs yourself. Fix the text, timing or options if something looks off (covers the face, cut off by the edge, unreadable).
3. Render: `$PY custom/fx_vi.py --plan <plan.json> <video> <video-name>_effects.mp4`. The output keeps their original audio. It renders at 1080p by default; add `--width 2160` for 4K (slower).
4. Tell them where the file is. Remind them in one line to watch it before posting: it drafts, they approve.

A single effect needs no plan: `$PY custom/fx_vi.py liquid-glass-graph <video> <out.mp4> --start 3 --end 6 --text "..." --opt key=value`.
Always run `custom/fx_vi.py` (Vietnamese text works), never `scripts/fx.py` directly.

## The 9 effects
| # | `fx` name | What it does | Options (all optional) |
|---|---|---|---|
| 1 | `liquid-glass-graph` | A liquid glass card under your chin: a green graph climbs while the number counts up | `text` (label), `from`, `to` (e.g. `197K`, `59%`), `color` |
| 2 | `split-graph` | A top card pops in with a 7-bar chart that springs up, numbers count, the No.1 bar glows with a crown; you move to the bottom half | `text` (title), `values` (7 numbers with `,`), `unit`, `palette` (`neon`, `lemon`) |
| 3 | `split-graph-v1` | Older look of split-graph: bars grow one by one with counting numbers | `text`, `values`, `unit` |
| 4 | `timeline` | A dark red film grade with an editing timeline, a REC timecode and a glowing playhead | `text` (title), `sub`, `tc` |
| 5 | `wave-trim` | A dark panel above your head shows your voice; the red dotted silence on both ends collapses until only your words are left | none |
| 6 | `select-resize` | A blue selection box with handles grabs your number above your head and a cursor drags it bigger | `text` (default 2X) |
| 7 | `editor` | A full video-editor screen around you: viewer, timecode, tools, inspector sliders, a 6-track timeline with a moving playhead | `text` (title) |
| 8 | `countdown-flip` | A 3, 2, 1 flip clock above your head | `from` |
| 9 | `broll-split` | B-roll on top with a price-tag sticker, you below | `images`, `text` (tag) |

**Named looks** (same effect, a fancier look; they don't add to the count):
- `liquid-glass-graph` with `look=bento`: the climbing graph moves to a smoked glass screen behind your head, with glass bento tiles in front of you (a donut, a KPI, bars). `text`, `from`, `to`, `donut` (`29%::label`), `kpi` (`672K::label`), `bars` (`197\|140\|124::label`).

## Rules
- Never cover the face. Everything either goes behind the person or avoids the face by itself; if a check frame still shows text over the face, move it (`x`, `y`) or shorten the text.
- Effects run in the order listed. Put camera effects first when they overlap others.
- Zoom never goes past 2x, so the video stays sharp.
- This skill adds visuals only. Sound effects and captions are up to the user.

## Các gói FX Free khác
- `fx-free-01` · Camera & ánh sáng: locked-on, lean-in, slow-push, over-the-shoulder-zoom, spotlight, moody, swipe, rabbit-hole, cinema, cinema-v1
- `fx-free-02` · Chữ sau đầu: backdrop-word, huge-strike, crayon-write, red-collage, pastel-word, led-sign, match-cut, spotlight-type, spotlight-neon, cover-star
- `fx-free-03` · Ảnh & reels quanh đầu: noise, orbit, carousel-spin, fan-build, profile-wall, place-in-grid, phone-fan, check-pills, headline-wall, gold-collage
- `fx-free-04` · Thẻ & danh sách: todo, checklist, apple-toggles, the-bill, lineup, tier-list, glass-widgets, messages, comment-box, tap
- `fx-free-06` · Nhãn & điểm nhấn: tape-label, scribble, pause-point, reject-stamp, uninstall, reel-frame, shortcut-rain, headline-box, split-headline, dot-reveal
Cài thêm gói: `/plugin install fx-free-0N@claudewithduy` (đã thêm marketplace `duynguyeenx96/claudewithduy`).
