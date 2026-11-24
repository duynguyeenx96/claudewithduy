---
name: effects
description: FX Pack 1-03 · Ảnh & reels quanh đầu. Add one of 10 talking-head video effects: noise, orbit, carousel-spin, fan-build, profile-wall, place-in-grid, phone-fan, check-pills, headline-wall, gold-collage. Effects track the speaker's face and can sit behind their head. Use when the user types /effects, names one of these effects, or asks for this kind of effect. Tiếng Việt: "hiệu ứng", "ảnh xoay quanh đầu", "reels bay quanh", "tường ảnh".
---

> Đọc `README.md` cạnh file này trước (lệnh chạy, phông tiếng Việt, vùng an toàn).

# FX Pack 1-03 · Ảnh & reels quanh đầu (10 hiệu ứng)

Gói này nằm trong bộ FX Pack 1 của Claude with Duy (59 hiệu ứng miễn phí, chia 6 gói; gói đủ 59 là `fx-pack-1`). Gói này chỉ có 10 hiệu ứng bên dưới, cộng 3 hiệu ứng kèm theo (lean-in, slow-push, screenshot) (dùng chung mọi gói: điểm nhấn đặt được ở mọi câu, và thẻ ảnh khi người dùng đưa ảnh).
Người dùng nhắc tới hiệu ứng không có ở đây: nói nó nằm trong gói nào (xem cuối file) và cách cài, đừng cố làm thay bằng hiệu ứng khác.

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands themselves.
All paths below are relative to this skill's folder: `${CLAUDE_SKILL_DIR}`. Use the absolute path in commands.

## 1. First run: set up (once)
Run `bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"`. Its last line is `READY <python>` (the first time takes 1 to 3 minutes; every FX pack shares this setup, so later packs are instant). Call that python `PY` and use it for every command below.
- `NEED_FFMPEG`: install it for them. On a Mac: `brew install ffmpeg` (if `brew` is missing, tell them to install Homebrew from brew.sh first). On Windows: `winget install ffmpeg`.
- `NEED_PYTHON`: install Python 3.12 (Mac: `brew install python@3.12`, Windows: `winget install Python.Python.3.12`), then run setup again.

## 2. Get the video and the effect
- Video: the user drags the file into the chat, or gives a path. A vertical phone video works best.
- Images (optional): if they also give screenshots or photos (a post, their page, a price list), use them with `screenshot` where a line mentions them. Never ask for images; no images is fine.
- Effect: from `/effects <name>`, or from what they describe. Match their words to the table below. No effect named: choose them yourself with `catalog.md`.

## 3. Decide what goes where
- They name the effect and the moment ("lean-in on the word X", "when I say ..."): run `$PY scripts/words.py <video>` and use those times.
- They give only the video, an effect with no moment, or say "make it look good" / "thêm hiệu ứng": **read `catalog.md` next to this file and follow its auto-edit flow.** You decide which lines get an effect, which effect and what text, from the meaning of each line. Don't ask, and don't spread one effect over the whole clip.
- Short windows look best: 1.5 to 4 seconds per effect.

## 4. Draft, check, render
1. Write the plan next to their video as `<video-name>_effects.json`:
   ```json
   {"effects": [{"fx": "noise", "start": 3.2, "end": 6.0}]}
   ```
2. Check frames first (fast): `$PY custom/fx_vi.py --plan <plan.json> <video> <folder>/check.png --still 4.5`, using the middle of each effect. Look at the PNGs yourself. On a vertical video they show the phone UI in red: the top band (status bar, Dynamic Island, tabs, search), the caption band at the bottom and the button column on the right. Never cover the face (hard rule). Keep text out of the dark red; the light red is best avoided, but text may poke into it a little, e.g. in a close-up, rather than shrink or drop onto the face. Fix the text, timing or options if not.
Every `--plan` run first checks the plan (`custom/plan_check.py`): it counts effects by what the viewer sees, not by name (e.g. `lean-in`, `slow-push`, `locked-on` and a pushing `spotlight` are all "zoom into the face", max 2 per minute), fixes extra zooms itself (keeps the text, drops the zoom) and prints `Soát plan, đã sửa: …` / `Soát plan, cảnh báo: …`. Mention the fixes to the user; for warnings, change the plan and run again.
3. Render: `$PY custom/fx_vi.py --plan <plan.json> <video> <video-name>_effects.mp4`. The output keeps their original audio. It renders at 1080p by default; add `--width 2160` for 4K (slower).
4. Tell them where the file is, with a short table of what you chose (`second · effect · which line, why`). Remind them in one line to watch it before posting: it drafts, they approve.

A single effect needs no plan: `$PY custom/fx_vi.py noise <video> <out.mp4> --start 3 --end 6 --text "..." --opt key=value`.
Always run `custom/fx_vi.py` (Vietnamese text works), never `scripts/fx.py` directly.

## The 10 effects
| # | `fx` name | What it does | Options (all optional) |
|---|---|---|---|
| 1 | `noise` | Reels pile up behind your head, one every quarter second | `images` (folder of screenshots or clips), `size` |
| 2 | `orbit` | Your reels circle your head: in front at the bottom, behind at the top | `images`, `count`, `speed`, `size` |
| 3 | `carousel-spin` | Your reels spin around you in a 3D carousel, then slow to a stop | `images`, `count`, `size`, `turns` |
| 4 | `fan-build` | Your reel covers deal into a fan behind your head, one card at a time | `images` (folder of your covers), `count` (default 13) |
| 5 | `profile-wall` | Your reels grid fills the wall behind you while a counter ticks up | `images`, `count`, `label` |
| 6 | `place-in-grid` | You shrink into the centre tile of your 3x3 profile grid on frosted glass, then 8 reels pop in around you, one per frame, with Instagram view counts on every tile | `images` (folder of your reels or covers), `views` (9 counts with `\|`, the 9th is yours) |
| 7 | `phone-fan` | Your reels fan out like a hand of phones under a headline | `images`, `text` (lines with `\|`) |
| 8 | `check-pills` | Grid-paper room, reel boards behind you, a cursor clicks blue pills | `text` (pills with `\|`), `images` |
| 9 | `headline-wall` | Your own headlines pile up behind your head, then a total pops in front | `text` (`headline::meta\|...`), `total`, `label` |
| 10 | `gold-collage` | Black and white you over a dark room, a giant metallic gold word staggers in behind you with a shine sweep, kinetic lines beside you | `text`, `lines` (with `\|`), `tag` |
| + | `lean-in` | (kèm theo) A fast punch-in on one word, optionally a number or key phrase pops up above your head | `zoom` (default 1.45, max 2), `speed`, `text`, `color` |
| + | `slow-push` | (kèm theo) A slow cinematic push-in to your face while the room melts out of focus | `zoom` (default 1.6), `blur` |
| + | `screenshot` | (kèm theo) Your own screenshot (only when the user gives one) pops up as a card: it scrolls to the right spot, a highlighter marks a line, a cursor clicks a button | `image` (required), `highlight` and `click` (boxes from `scripts/find_text.py`), `hl_at`, `click_at`, `click_text`, `y` |

## Rules
- Never cover the face. Everything either goes behind the person or avoids the face by itself; if a check frame still shows text over the face, move it (`x`, `y`) or shorten the text.
- Effects run in the order listed. Put camera effects first when they overlap others.
- Zoom never goes past 2x, so the video stays sharp.
- This skill adds visuals only. Sound effects and captions are up to the user.

## Các gói FX Pack 1 khác
- `fx-pack-1-01` · Camera & ánh sáng: locked-on, lean-in, slow-push, over-the-shoulder-zoom, spotlight, moody, swipe, rabbit-hole, cinema, cinema-v1
- `fx-pack-1-02` · Chữ sau đầu: backdrop-word, huge-strike, crayon-write, red-collage, pastel-word, led-sign, match-cut, spotlight-type, spotlight-neon, cover-star
- `fx-pack-1-04` · Thẻ & danh sách: todo, checklist, apple-toggles, the-bill, lineup, tier-list, glass-widgets, messages, comment-box, tap
- `fx-pack-1-05` · Số liệu & dựng: liquid-glass-graph, split-graph, split-graph-v1, timeline, wave-trim, select-resize, editor, countdown-flip, broll-split
- `fx-pack-1-06` · Nhãn & điểm nhấn: tape-label, scribble, pause-point, reject-stamp, uninstall, reel-frame, shortcut-rain, headline-box, split-headline, dot-reveal
Cài thêm gói: `/plugin install fx-pack-1-0N@claudewithduy`, hoặc cả 59 hiệu ứng: `/plugin install fx-pack-1@claudewithduy` (đã thêm marketplace `duynguyeenx96/claudewithduy`).
