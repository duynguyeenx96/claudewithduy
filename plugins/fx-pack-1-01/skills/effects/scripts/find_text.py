#!/usr/bin/env python3
"""Find where a phrase sits in a screenshot, for the `screenshot` effect's highlight= / click= options.

usage: python find_text.py image.png "Theo dõi"            -> box of that phrase
       python find_text.py image.png "Quà GA là 1 đôi|2400k" -> one box spanning from the first part to the last
       python find_text.py image.png --all                  -> every line the reader sees, with its box
Prints `x0,y0,x1,y1` as fractions 0-1 of the image (paste it straight into the plan).
Reads text with RapidOCR (installed on first use, ~30 MB). Accents and spaces are ignored when matching.
"""
import json, re, subprocess, sys, unicodedata
from PIL import Image


def norm(s):
    s = unicodedata.normalize('NFD', str(s).replace('đ', 'd').replace('Đ', 'D'))
    return re.sub(r'[^a-z0-9]', '', ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn').lower())


def read(path):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print('Installing the text reader (one time)...', file=sys.stderr, flush=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'rapidocr_onnxruntime'], check=True)
        from rapidocr_onnxruntime import RapidOCR
    res, _ = RapidOCR()(path)
    out = []
    for box, txt, score in res or []:
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        out.append({'text': txt, 'box': [min(xs), min(ys), max(xs), max(ys)], 'score': float(score)})
    return sorted(out, key=lambda r: (round(r['box'][1] / 12), r['box'][0]))


def locate(lines, phrase):
    """Box of `phrase` inside one line, narrowed to the matching characters."""
    q = norm(phrase)
    if not q: return None
    for ln in lines:
        t = norm(ln['text']); i = t.find(q)
        if i >= 0:
            x0, y0, x1, y1 = ln['box']; n = max(1, len(t))
            return [x0 + (x1 - x0) * i / n, y0, x0 + (x1 - x0) * (i + len(q)) / n, y1]
    # cụm dài vắt qua nhiều dòng: ghép các dòng liền nhau
    for a in range(len(lines)):
        acc = ''
        for b in range(a, min(a + 4, len(lines))):
            acc += norm(lines[b]['text'])
            if q in acc:
                bs = [l['box'] for l in lines[a:b + 1]]
                return [min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)]
    return None


def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    path, phrase = sys.argv[1], sys.argv[2]
    W, H = Image.open(path).size
    lines = read(path)
    frac = lambda b: ','.join(f'{v:.3f}' for v in (b[0] / W, b[1] / H, b[2] / W, b[3] / H))
    if phrase == '--all':
        for l in lines: print(f"{frac(l['box'])}  {l['text']}")
        return
    parts = [p for p in phrase.split('|') if p.strip()]
    boxes = [locate(lines, p) for p in parts]
    if any(b is None for b in boxes):
        miss = [p for p, b in zip(parts, boxes) if b is None]
        sys.exit(f"Không thấy {miss} trong ảnh. Chạy với --all để xem chữ đọc được, rồi thử một cụm ngắn hơn.")
    if len(boxes) > 1:  # từ đầu cụm thứ nhất tới hết cụm cuối: lấy trọn các dòng ở giữa
        ys = [b for b in boxes]
        inside = [l['box'] for l in lines if l['box'][1] >= min(b[1] for b in ys) - 2 and l['box'][3] <= max(b[3] for b in ys) + 2]
        box = [min(x[0] for x in inside + ys), min(b[1] for b in ys), max(x[2] for x in inside + ys), max(b[3] for b in ys)]
    else:
        box = boxes[0]
    print(frac(box))


if __name__ == '__main__':
    main()
