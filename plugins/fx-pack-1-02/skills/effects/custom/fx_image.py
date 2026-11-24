#!/usr/bin/env python3
"""Hiệu ứng dùng ẢNH CỦA NGƯỜI DÙNG (tuỳ chọn: chỉ dùng khi họ đưa ảnh). Claude with Duy, 2026-11-24.

  screenshot : ảnh chụp màn hình hiện lên thành thẻ giữa khung, nền tối đi; ảnh dài thì tự cuộn tới chỗ cần xem;
               tuỳ chọn bút dạ vàng quét một dòng (highlight) và con trỏ bấm một nút (click), nút đổi chữ (click_text).

Options:
  image=<đường dẫn ảnh>              bắt buộc
  highlight=x0,y0,x1,y1              khung dòng cần tô, tỉ lệ 0-1 theo ảnh (lấy bằng scripts/find_text.py)
  hl_at=<giây trong hiệu ứng>        lúc bút dạ quét (mặc định 35% thời lượng)
  click=x0,y0,x1,y1                  khung nút cần bấm (find_text.py)
  click_at=<giây trong hiệu ứng>     lúc bấm (mặc định 55%)
  click_text="Đang theo dõi"         chữ mới của nút sau khi bấm (bỏ trống: nút chỉ tối lại)
  y=0.40  width=0.86  max_h=0.62     tâm dọc của thẻ, bề ngang và chiều cao tối đa (tỉ lệ khung)
Thẻ là cảnh chèn nên được phép che mặt: giữ 3-6 giây.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import fx  # noqa: E402
from fx import effect, clamp, ease_out, ease_back, ease_inout, place, cached, shadowed, cursor, font  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

HL = (255, 214, 10)


def _box(v):
    if v in (None, '', 'none'): return None
    p = [float(x) for x in str(v).replace(' ', '').split(',')]
    return p if len(p) == 4 else None


@effect('screenshot', 'your own screenshot pops up as a card: it scrolls, a highlighter marks a line, a cursor clicks a button')
def fx_screenshot(c, e):
    path = e.o.get('image')
    if not path or not os.path.exists(str(path)):
        sys.exit(f"screenshot: không thấy ảnh '{path}'. Truyền image=<đường dẫn ảnh người dùng đưa>.")
    W, H = c.W, c.H
    cw = int(W * float(e.o.get('width', 0.86)))

    def prep():
        src = Image.open(path).convert('RGB')
        fh = int(src.height * cw / src.width)
        return src.resize((cw, fh), Image.LANCZOS).convert('RGBA')
    img = cached(e, 'img', prep)
    full_h = img.height
    vh = min(full_h, int(H * float(e.o.get('max_h', 0.62))))
    hl, ck = _box(e.o.get('highlight')), _box(e.o.get('click'))
    hl_at = float(e.o.get('hl_at', e.d * 0.35)); ck_at = float(e.o.get('click_at', e.d * 0.55))

    # cuộn: ảnh dài hơn khung thì cuộn tới chỗ cần xem (dòng tô / nút bấm), không có thì cuộn đều từ trên xuống
    y_off = 0.0
    if full_h > vh:
        span = full_h - vh
        focus = hl or ck
        if focus:
            tgt = clamp((focus[1] + focus[3]) / 2 * full_h - vh * 0.45, 0, span)
            t_end = max(0.6, (hl_at if hl else ck_at) - 0.1)
            y_off = tgt * ease_inout((c.lt - 0.3) / max(0.2, t_end - 0.3))
        else:
            y_off = span * ease_inout((c.lt - 0.4) / max(0.5, e.d - 0.9))
    y_off = int(y_off)
    view = img.crop((0, y_off, cw, y_off + vh))
    d = ImageDraw.Draw(view, 'RGBA')

    def to_view(b):
        return b[0] * cw, b[1] * full_h - y_off, b[2] * cw, b[3] * full_h - y_off

    if hl and c.lt > hl_at:
        x0, y0, x1, y1 = to_view(hl); pad = (y1 - y0) * 0.12
        fr = ease_out((c.lt - hl_at) / 0.35)
        ov = Image.new('RGBA', view.size, (0, 0, 0, 0))  # lớp riêng: vẽ thẳng lên ảnh RGBA thì PIL đè chứ không pha màu
        ImageDraw.Draw(ov).rectangle([x0 - pad, y0 - pad, x0 - pad + (x1 - x0 + 2 * pad) * fr, y1 + pad], fill=HL + (95,))
        view.alpha_composite(ov); d = ImageDraw.Draw(view, 'RGBA')

    cur = None
    if ck:
        x0, y0, x1, y1 = to_view(ck); bx, by = (x0 + x1) / 2, (y0 + y1) / 2
        ph = (y1 - y0) * 0.3; x0, y0, x1, y1 = x0 - ph * 2.2, y0 - ph, x1 + ph, y1 + ph  # khung OCR chỉ ôm chữ: nới ra cho bằng nút
        if c.lt > ck_at and e.o.get('click_text'):
            bh = y1 - y0; d.rounded_rectangle([x0, y0, x1, y1], bh * 0.22, fill=(228, 230, 235, 255))
            f = font('uib', bh * 0.48); tx = str(e.o['click_text'])
            while f.getlength(tx) > (x1 - x0) * 0.92 and f.size > 8: f = font('uib', f.size * 0.92)
            d.text((bx, by), tx, font=f, fill=(28, 30, 33, 255), anchor='mm')
        elif c.lt > ck_at:
            d.rounded_rectangle([x0, y0, x1, y1], (y1 - y0) * 0.22, fill=(0, 0, 0, 70))
        t0 = ck_at - 0.65
        if c.lt > t0:
            k = ease_inout((c.lt - t0) / 0.6)
            sx, sy = cw * 0.92, vh * 0.98
            press = 0.82 if ck_at <= c.lt < ck_at + 0.14 else 1.0
            cur = (sx + (bx - sx) * k, sy + (by - sy) * k, press)
            if ck_at <= c.lt < ck_at + 0.45:  # gợn sóng lúc bấm
                r = (y1 - y0) * (0.4 + 1.6 * (c.lt - ck_at) / 0.45); a = int(150 * (1 - (c.lt - ck_at) / 0.45))
                d.ellipse([bx - r, by - r, bx + r, by + r], outline=(255, 255, 255, a), width=max(2, int(W / 300)))

    m = Image.new('L', view.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, vh - 1], int(W * 0.035), fill=255)
    view.putalpha(Image.fromarray(np.minimum(np.asarray(view.getchannel('A')), np.asarray(m))))
    if cur:
        ci = cursor(W * 0.05)
        if cur[2] != 1.0: ci = ci.resize((int(ci.width * cur[2]), int(ci.height * cur[2])))
        view.alpha_composite(ci, (int(min(cw - ci.width, max(0, cur[0] - 4))), int(min(vh - ci.height, max(0, cur[1] - 4)))))
    card_im = shadowed(view, 22, 12, 140)

    k_in = ease_back(c.lt / 0.35); out = clamp((e.d - c.lt) / 0.3)
    c.img *= 1 - 0.45 * clamp(c.lt / 0.25) * out  # nền tối đi cho dễ đọc
    cy = max(vh / 2 + H * 0.06, H * float(e.o.get('y', 0.40))) - (1 - out) * H * 0.05
    place(c, card_im, W / 2, cy, 0.9 + 0.1 * k_in, 0, clamp(c.lt / 0.15) * out)
