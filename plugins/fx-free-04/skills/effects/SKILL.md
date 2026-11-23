---
name: effects
description: FX Free 04 · Thẻ & danh sách. Add one of 10 talking-head video effects: todo, checklist, apple-toggles, the-bill, lineup, tier-list, glass-widgets, messages, comment-box, tap. Effects track the speaker's face and can sit behind their head. Use when the user types /effects, names one of these effects, or asks for this kind of effect. Tiếng Việt: "hiệu ứng", "checklist trên video", "thẻ tin nhắn", "nút follow", "tier list".
---

> Đọc `README.md` cạnh file này trước (lệnh chạy, phông tiếng Việt, vùng an toàn).

# FX Free 04 · Thẻ & danh sách (10 hiệu ứng)

Gói này nằm trong bộ FX Free của Claude with Duy (6 gói, 59 hiệu ứng, miễn phí). Gói này chỉ có 10 hiệu ứng bên dưới.
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
   {"effects": [{"fx": "todo", "start": 3.2, "end": 6.0}]}
   ```
2. Check frames first (fast): `$PY custom/fx_vi.py --plan <plan.json> <video> <folder>/check.png --still 4.5`, using the middle of each effect. Look at the PNGs yourself. Fix the text, timing or options if something looks off (covers the face, cut off by the edge, unreadable).
3. Render: `$PY custom/fx_vi.py --plan <plan.json> <video> <video-name>_effects.mp4`. The output keeps their original audio. It renders at 1080p by default; add `--width 2160` for 4K (slower).
4. Tell them where the file is. Remind them in one line to watch it before posting: it drafts, they approve.

A single effect needs no plan: `$PY custom/fx_vi.py todo <video> <out.mp4> --start 3 --end 6 --text "..." --opt key=value`.
Always run `custom/fx_vi.py` (Vietnamese text works), never `scripts/fx.py` directly.

## The 10 effects
| # | `fx` name | What it does | Options (all optional) |
|---|---|---|---|
| 1 | `todo` | A checklist card beside your head ticks off as you talk | `text` (items with `\|`), `ticks` (video seconds with `\|`), `title` |
| 2 | `checklist` | A Claude task list under your chin: each step spins, then ticks green | `text` (`step::meta\|...`), `title` |
| 3 | `apple-toggles` | An iPhone settings card under your chin flips its switches on, one line at a time | `text` (rows with `\|`), `ticks` (seconds with `\|`), `color` |
| 4 | `the-bill` | Prints your instructions like a receipt into the wall above your head | `text` (lines joined with `\|`) |
| 5 | `lineup` | Numbered tiles fan out in an arc above your head | `text` (tile names joined with `\|`) |
| 6 | `tier-list` | A tier list drops in and Claude flies into S tier | `title`, `item`, `others` |
| 7 | `glass-widgets` | Frosted glass widgets and mini artifacts float around your head, plus an Edited by Claude pill | `text` (big number), `name`, `handle`, `look` (`simple` for the 3-widget version) |
| 8 | `messages` | iMessage notifications pop in one after another, creamy glass with a soft glow, stacking up above the bottom of the frame | `text` (messages with `\|`), `title` (default Messages), `y` |
| 9 | `comment-box` | An Instagram comment bar types a word and posts it | `text` (default EFFECTS) |
| 10 | `tap` | A Follow button pops up and flips to Following | `at` (video second of the flip), `x`, `y` (0 to 1), `color` |

**Named looks** (same effect, a fancier look; they don't add to the count):
- `apple-toggles` now sits above you, tucked behind your head, with a gentle zoom (`pos=below` for the old under-the-chin card; `overlap`, `zoom`).

## Rules
- Never cover the face. Everything either goes behind the person or avoids the face by itself; if a check frame still shows text over the face, move it (`x`, `y`) or shorten the text.
- Effects run in the order listed. Put camera effects first when they overlap others.
- Zoom never goes past 2x, so the video stays sharp.
- This skill adds visuals only. Sound effects and captions are up to the user.

## Các gói FX Free khác
- `fx-free-01` · Camera & ánh sáng: locked-on, lean-in, slow-push, over-the-shoulder-zoom, spotlight, moody, swipe, rabbit-hole, cinema, cinema-v1
- `fx-free-02` · Chữ sau đầu: backdrop-word, huge-strike, crayon-write, red-collage, pastel-word, led-sign, match-cut, spotlight-type, spotlight-neon, cover-star
- `fx-free-03` · Ảnh & reels quanh đầu: noise, orbit, carousel-spin, fan-build, profile-wall, place-in-grid, phone-fan, check-pills, headline-wall, gold-collage
- `fx-free-05` · Số liệu & dựng: liquid-glass-graph, split-graph, split-graph-v1, timeline, wave-trim, select-resize, editor, countdown-flip, broll-split
- `fx-free-06` · Nhãn & điểm nhấn: tape-label, scribble, pause-point, reject-stamp, uninstall, reel-frame, shortcut-rain, headline-box, split-headline, dot-reveal
Cài thêm gói: `/plugin install fx-free-0N@claudewithduy` (đã thêm marketplace `duynguyeenx96/claudewithduy`).
