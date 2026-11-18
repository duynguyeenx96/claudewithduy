#!/usr/bin/env python3
"""Vẽ vùng bị UI TikTok/Reels/Shorts che lên ảnh snapshot 9:16 để soát chữ có lọt ra ngoài không (xem SAFE_ZONE.md).

python3 safezone.py <ảnh.png|thư mục> [-o thư-mục-ra]   → <tên>.safe.png (+ safe-sheet.jpg nếu nhiều ảnh)
"""
import argparse
import sys
from pathlib import Path

W, H = 1080, 1920
TOP, BOTTOM, SIDE = 250, 1500, 70
RAIL = (900, 850, 1500)     # cột nút phải: x > 900 khi 850 ≤ y ≤ 1500

# vùng che (x0, y0, x1, y1) ở 1080×1920
ZONES = [(0, 0, W, TOP), (0, BOTTOM, W, H), (0, TOP, SIDE, BOTTOM), (W - SIDE, TOP, W, BOTTOM), (RAIL[0], RAIL[1], W - SIDE, RAIL[2])]


def overlay(src: Path, dst: Path):
    from PIL import Image, ImageDraw
    im = Image.open(src).convert("RGB")
    kx, ky = im.width / W, im.height / H
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x0, y0, x1, y1 in ZONES:
        d.rectangle([x0 * kx, y0 * ky, x1 * kx, y1 * ky], fill=(255, 40, 40, 70))
    d.rectangle([SIDE * kx, TOP * ky, (W - SIDE) * kx, BOTTOM * ky], outline=(255, 40, 40, 255), width=max(2, round(3 * kx)))
    out = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    out.save(dst)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    src = Path(a.src)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"} and ".safe." not in p.name
                   and "contact" not in p.name) if src.is_dir() else [src]
    files = [p for p in files if _portrait(p)]
    if not files:
        sys.exit("không có ảnh 9:16 nào (contact sheet không dùng được, đưa ảnh từng khung)")
    out_dir = Path(a.out) if a.out else (src if src.is_dir() else src.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = [overlay(p, out_dir / f"{p.stem}.safe.png") for p in files]
    for p in files:
        print(out_dir / f"{p.stem}.safe.png")
    if len(shots) > 1:
        from PIL import Image
        tw = 270; th = round(tw * H / W); cols = min(6, len(shots)); rows = -(-len(shots) // cols)
        sheet = Image.new("RGB", (cols * tw, rows * th), "#111")
        for i, s in enumerate(shots):
            sheet.paste(s.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
        sheet.save(out_dir / "safe-sheet.jpg", quality=88)
        print(out_dir / "safe-sheet.jpg")


def _portrait(p: Path) -> bool:
    from PIL import Image
    with Image.open(p) as im:
        return abs(im.width / im.height - W / H) < 0.02


if __name__ == "__main__":
    main()
