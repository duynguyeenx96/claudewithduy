#!/usr/bin/env python3
"""Tách các gói FX thành gói nhỏ ~10 hiệu ứng (gói đủ vẫn giữ):
  fx-pack-1 (59, claude-video-effects) -> fx-pack-1-01..06 theo chủ đề
  fx-pack-2 (13, registry HyperFrames) -> fx-pack-2-01 (10 đầu), fx-pack-2-02 (3 còn lại)

Nguồn duy nhất vẫn là plugins/fx-pack-1/skills/effects: sửa engine ở đó rồi chạy lại file này.
Mỗi gói là bản chép đủ engine (git lưu file trùng 1 lần), thêm pack.json để fx_vi.py chỉ mở các hiệu ứng của gói.
Dùng: python3 tools/split_fx_pack.py
"""
import json, os, re, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / 'plugins/fx-pack-1/skills/effects'
SKIP = {'.venv', '__pycache__', '.DS_Store', 'sfx', 'SKILL.md', 'README.md'}

PACKS = [
    ('01', 'Camera & ánh sáng', 'Máy quay bám mặt, đẩy vào, tắt đèn, chỉnh màu điện ảnh',
     ['locked-on', 'lean-in', 'slow-push', 'over-the-shoulder-zoom', 'spotlight', 'moody', 'swipe', 'rabbit-hole', 'cinema', 'cinema-v1']),
    ('02', 'Chữ sau đầu', 'Chữ khổng lồ nằm sau lưng người nói: rơi xuống, gạch, viết sáp, đèn LED, neon, bìa tạp chí',
     ['backdrop-word', 'huge-strike', 'crayon-write', 'red-collage', 'pastel-word', 'led-sign', 'match-cut', 'spotlight-type', 'spotlight-neon', 'cover-star']),
    ('03', 'Ảnh & reels quanh đầu', 'Ảnh, reels, bìa video bay quanh, xếp sau, xoè quạt, lấp tường',
     ['noise', 'orbit', 'carousel-spin', 'fan-build', 'profile-wall', 'place-in-grid', 'phone-fan', 'check-pills', 'headline-wall', 'gold-collage']),
    ('04', 'Thẻ & danh sách', 'Thẻ giao diện trên video: checklist, công tắc iPhone, hoá đơn, tier list, tin nhắn, comment, nút Follow',
     ['todo', 'checklist', 'apple-toggles', 'the-bill', 'lineup', 'tier-list', 'glass-widgets', 'messages', 'comment-box', 'tap']),
    ('05', 'Số liệu & dựng', 'Biểu đồ, số đếm, timeline dựng, sóng âm, đồng hồ lật, B-roll',
     ['liquid-glass-graph', 'split-graph', 'split-graph-v1', 'timeline', 'wave-trim', 'select-resize', 'editor', 'countdown-flip', 'broll-split']),
    ('06', 'Nhãn & điểm nhấn', 'Băng dính, vẽ nguệch ngoạc, mũi tên dừng hình, con dấu, glitch, mưa phím, tiêu đề, hiện từ chấm',
     ['tape-label', 'scribble', 'pause-point', 'reject-stamp', 'uninstall', 'reel-frame', 'shortcut-rain', 'headline-box', 'split-headline', 'dot-reveal']),
]

# 8 hiệu ứng thêm (custom/fx_custom.py) không có dòng trong bảng SKILL.md gốc
EXTRA_ROWS = {
    'cinema': ('Documentary cover: B&W you, a glowing circle behind, a big headline bouncing in letter by letter over a drifting watermark, film grain',
               '`text` (lines with `\\|`), `palette` (`red`, `lemon`), `bg` (`beige`, `room`), `kicker`, `watermark`'),
    'cinema-v1': ('Older look of cinema: B&W you, a glowing circle, a big headline punching in, film grain', '`text`, `palette`'),
    'split-graph': ('A top card pops in with a 7-bar chart that springs up, numbers count, the No.1 bar glows with a crown; you move to the bottom half',
                    '`text` (title), `values` (7 numbers with `,`), `unit`, `palette` (`neon`, `lemon`)'),
    'split-graph-v1': ('Older look of split-graph: bars grow one by one with counting numbers', '`text`, `values`, `unit`'),
    'editor': ('A full video-editor screen around you: viewer, timecode, tools, inspector sliders, a 6-track timeline with a moving playhead', '`text` (title)'),
    'spotlight-type': ('The room goes dark and a crisp word types itself in above your head, one letter at a time', '`text`, `color`, `step` (seconds per letter), `type_at`'),
    'spotlight-neon': ('The room goes dark and a glowing neon word switches on letter by letter behind you, with bloom and wall spill', '`text`, `step` (seconds per letter), `type_at`'),
    'gold-collage': ('Black and white you over a dark room, a giant metallic gold word staggers in behind you with a shine sweep, kinetic lines beside you', '`text`, `lines` (with `\\|`), `tag`'),
}
NAMED_LOOKS = {  # dòng "Named looks" của SKILL gốc -> gói chứa hiệu ứng cha
    'spotlight': 'glitter-spotlight', 'cover-star': 'cover-star', 'liquid-glass-graph': 'liquid-glass-graph', 'apple-toggles': 'apple-toggles'}


def source_rows():
    rows = {}
    for line in (SRC / 'SKILL.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$', line)
        if m: rows[m.group(1)] = (m.group(2), m.group(3))
    rows['countdown-flip'] = rows.get('countdown-flip') or rows.get('countdown')
    rows.update(EXTRA_ROWS)
    return rows


def looks_block():
    txt = (SRC / 'SKILL.md').read_text(encoding='utf-8')
    blk = txt.split('**Named looks**', 1)[1].split('Aliases work too', 1)[0]
    items = re.findall(r'^- (.*)$', blk, re.M)
    out = {}
    for it in items:
        for parent in NAMED_LOOKS:
            if f'`{parent}`' in it.split(':')[0] or it.startswith(f'`{NAMED_LOOKS[parent]}`'):
                out.setdefault(parent, []).append(it); break
    return out


SKILL_TMPL = '''---
name: effects
description: FX Pack 1-{num} · {title}. Add one of {n} talking-head video effects: {names}. Effects track the speaker's face and can sit behind their head. Use when the user types /effects, names one of these effects, or asks for this kind of effect. Tiếng Việt: "hiệu ứng", {vi}.
---

> Đọc `README.md` cạnh file này trước (lệnh chạy, phông tiếng Việt, vùng an toàn).

# FX Pack 1-{num} · {title} ({n} hiệu ứng)

Gói này nằm trong bộ FX Pack 1 của Claude with Duy (59 hiệu ứng miễn phí, chia 6 gói; gói đủ 59 là `fx-pack-1`). Gói này chỉ có {n} hiệu ứng bên dưới.
Người dùng nhắc tới hiệu ứng không có ở đây: nói nó nằm trong gói nào (xem cuối file) và cách cài, đừng cố làm thay bằng hiệu ứng khác.

The user is usually not technical. Keep replies short and friendly, do the work for them, and never ask them to run commands themselves.
All paths below are relative to this skill's folder: `${{CLAUDE_SKILL_DIR}}`. Use the absolute path in commands.

## 1. First run: set up (once)
Run `bash "${{CLAUDE_SKILL_DIR}}/scripts/setup.sh"`. Its last line is `READY <python>` (the first time takes 1 to 3 minutes; every FX pack shares this setup, so later packs are instant). Call that python `PY` and use it for every command below.
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
   {{"effects": [{{"fx": "{ex}", "start": 3.2, "end": 6.0}}]}}
   ```
2. Check frames first (fast): `$PY custom/fx_vi.py --plan <plan.json> <video> <folder>/check.png --still 4.5`, using the middle of each effect. Look at the PNGs yourself. Fix the text, timing or options if something looks off (covers the face, cut off by the edge, unreadable).
3. Render: `$PY custom/fx_vi.py --plan <plan.json> <video> <video-name>_effects.mp4`. The output keeps their original audio. It renders at 1080p by default; add `--width 2160` for 4K (slower).
4. Tell them where the file is. Remind them in one line to watch it before posting: it drafts, they approve.

A single effect needs no plan: `$PY custom/fx_vi.py {ex} <video> <out.mp4> --start 3 --end 6 --text "..." --opt key=value`.
Always run `custom/fx_vi.py` (Vietnamese text works), never `scripts/fx.py` directly.

## The {n} effects
| # | `fx` name | What it does | Options (all optional) |
|---|---|---|---|
{rows}
{looks}
## Rules
- Never cover the face. Everything either goes behind the person or avoids the face by itself; if a check frame still shows text over the face, move it (`x`, `y`) or shorten the text.
- Effects run in the order listed. Put camera effects first when they overlap others.
- Zoom never goes past 2x, so the video stays sharp.
- This skill adds visuals only. Sound effects and captions are up to the user.

## Các gói FX Pack 1 khác
{others}
Cài thêm gói: `/plugin install fx-pack-1-0N@claudewithduy`, hoặc cả 59 hiệu ứng: `/plugin install fx-pack-1@claudewithduy` (đã thêm marketplace `duynguyeenx96/claudewithduy`).
'''

VI = {'01': '"zoom vào mặt", "tắt đèn chỉ còn người", "chỉnh màu điện ảnh"', '02': '"chữ sau lưng", "chữ to sau đầu", "chữ neon", "bìa tạp chí"',
      '03': '"ảnh xoay quanh đầu", "reels bay quanh", "tường ảnh"', '04': '"checklist trên video", "thẻ tin nhắn", "nút follow", "tier list"',
      '05': '"biểu đồ kính", "số liệu", "timeline dựng", "đồng hồ đếm ngược"', '06': '"băng dính chữ", "con dấu", "mũi tên", "vẽ nguệch ngoạc"'}


def main():
    rows, looks = source_rows(), looks_block()
    allnames = [n for p in PACKS for n in p[3]]
    assert len(allnames) == len(set(allnames)) == 59, len(allnames)
    where = {n: f'fx-pack-1-{p[0]}' for p in PACKS for n in p[3]}
    lic = (SRC / 'LICENSE').read_text(encoding='utf-8')
    for num, title, blurb, names in PACKS:
        dst = REPO / f'plugins/fx-pack-1-{num}'
        if dst.exists(): shutil.rmtree(dst)
        sk = dst / 'skills/effects'
        shutil.copytree(SRC, sk, ignore=lambda d, fs: [f for f in fs if f in SKIP])
        (sk / 'pack.json').write_text(json.dumps({'name': f'fx-pack-1-{num}', 'title': title, 'effects': names,
                                                  'others': {k: v for k, v in where.items() if k not in names}},
                                                 ensure_ascii=False, indent=1), encoding='utf-8')
        tbl = '\n'.join(f'| {i} | `{n}` | {rows[n][0]} | {rows[n][1]} |' for i, n in enumerate(names, 1))
        lk = [it for n in names for it in looks.get(n, [])]
        lkb = ('\n**Named looks** (same effect, a fancier look; they don\'t add to the count):\n' + '\n'.join(f'- {x}' for x in lk) + '\n') if lk else ''
        others = '\n'.join(f'- `fx-pack-1-{p[0]}` · {p[1]}: ' + ', '.join(p[3]) for p in PACKS if p[0] != num)
        (sk / 'SKILL.md').write_text(SKILL_TMPL.format(num=num, title=title, n=len(names), names=', '.join(names), vi=VI[num],
                                                       ex=names[0], rows=tbl, looks=lkb, others=others), encoding='utf-8')
        readme = (SRC / 'README.md').read_text(encoding='utf-8')
        readme = re.sub(r'^# .*$', f'# FX Pack 1-{num} · {title} ({len(names)} hiệu ứng)', readme, count=1, flags=re.M)
        readme = readme.replace('Nguồn: skill', f'Một trong 6 gói tách từ FX Pack 1 (59 hiệu ứng, gói đủ là `fx-pack-1`). Gói này: {", ".join(names)}.\n\nNguồn: skill', 1)
        (sk / 'README.md').write_text(readme, encoding='utf-8')
        (dst / '.claude-plugin').mkdir(parents=True)
        (dst / '.claude-plugin/plugin.json').write_text(json.dumps({
            'name': f'fx-pack-1-{num}', 'version': '1.0.0',
            'description': f'FX Pack 1-{num} · {title}: {len(names)} hiệu ứng cho video người nói. {blurb}.',
            'author': {'name': 'Claude with Duy'},
            'homepage': f'https://github.com/duynguyeenx96/claudewithduy/tree/main/plugins/fx-pack-1-{num}',
            'repository': 'https://github.com/duynguyeenx96/claudewithduy', 'license': 'MIT'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        assert (sk / 'LICENSE').read_text(encoding='utf-8') == lic
        print(f'fx-pack-1-{num}: {len(names)} hiệu ứng')


FX2 = REPO / 'plugins/fx-pack-2'


def split_fx2(size=10):
    import copy
    rec = json.loads((FX2 / 'skills/fx2/recipes.json').read_text(encoding='utf-8'))
    names = list(rec['recipes'])
    chunks = [names[i:i + size] for i in range(0, len(names), size)]
    skill = (FX2 / 'skills/fx2/SKILL.md').read_text(encoding='utf-8')
    for k, part in enumerate(chunks, 1):
        num = f'{k:02d}'; name = f'fx-pack-2-{num}'; dst = REPO / f'plugins/{name}'
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(FX2, dst, ignore=lambda d, fs: [f for f in fs if f in {'node_modules', '__pycache__', '.DS_Store'}])
        r2 = copy.deepcopy(rec); r2['recipes'] = {n: rec['recipes'][n] for n in part}
        (dst / 'skills/fx2/recipes.json').write_text(json.dumps(r2, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        sk = skill
        sk = re.sub(r'^\| `([\w-]+)` \|.*\n', lambda m: m.group(0) if m.group(1) in part else '', sk, flags=re.M)
        sk = sk.replace('## Hiệu ứng (13, đợt 1)', f'## Hiệu ứng ({len(part)} trong 13)')
        others = [n for n in names if n not in part]
        sk = sk.replace('Danh sách đầy đủ, mô tả và cách ánh xạ nằm ở `recipes.json`.',
                        f'Gói {name} chỉ có {len(part)} hiệu ứng trên. Các hiệu ứng khác ({", ".join(others)}) nằm ở gói khác của FX Pack 2; '
                        f'cả 13 hiệu ứng: `/plugin install fx-pack-2@claudewithduy`. Mô tả và cách ánh xạ nằm ở `recipes.json`.')
        sk = re.sub(r'^description: (.*)$', lambda m: f'description: FX Pack 2-{num} ({len(part)} hiệu ứng: {", ".join(part)}). ' + m.group(1), sk, count=1, flags=re.M)
        (dst / 'skills/fx2/SKILL.md').write_text(sk, encoding='utf-8')
        pj = json.loads((FX2 / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        pj.update(name=name, description=f'FX Pack 2-{num}: {len(part)} hiệu ứng HyperFrames miễn phí cho A-roll dọc ({", ".join(part)}).',
                  homepage=f'https://github.com/duynguyeenx96/claudewithduy/tree/main/plugins/{name}')
        (dst / '.claude-plugin/plugin.json').write_text(json.dumps(pj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{name}: {len(part)} hiệu ứng')


if __name__ == '__main__':
    main()
    split_fx2()
