#!/usr/bin/env python3
"""Custom effects on top of claude-video-effects (MIT). Reuses its person matte (MediaPipe),
face tracking (YuNet), compositing helpers and video I/O; adds Japanese-text effects.

  cinema       : B&W person + soft brand-yellow circle + big Japanese headline + film grain
  split-graph  : top card with an animated 7-bar chart, person in the bottom 55%

Usage (run with the venv python, from any folder; this folder must stay ASCII-only):
  python fx_custom.py cinema      in.mp4 out.mp4 --start 0 --end 3 --text "映画みたいな|演出に"
  python fx_custom.py split-graph in.mp4 out.mp4 --start 0 --end 4 --text "リール再生数 TOP7"
  python fx_custom.py cinema in.mp4 check.png --still 0.1,1.5,2.9      (PNG check frames)
Options (--opt key=value):
  cinema      : palette=red|lemon  bg=beige|room  kicker=DOCUMENTARY  watermark=CINEMA|same|none  char_step=0.045  grain=0.035  push=1.035  out=0
  split-graph : palette=neon|lemon  values=20,15,12,8,5,4,3  unit=万  height=0.45  head_at=0.30  zoom=1.0  out=0
  (v1 looks kept as cinema-v1 / split-graph-v1)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import fx  # noqa: E402  (the skill's engine: matte, face tracker, helpers, main())
from fx import (effect, clamp, ease_out, ease_back, text_img, lines_fit, font, comp, place,  # noqa: E402
                camera, shift, cached, rrect, shadowed)
import numpy as np  # noqa: E402
import cv2  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

# Japanese fonts (LINE Seed JP ExtraBold; Noto Sans JP variable as fallback)
_JP = os.path.join(fx.ROOT, 'fonts', 'LINESeedJP-ExtraBold.ttf')
if not os.path.exists(_JP): _JP = r'C:\Windows\Fonts\NotoSansJP-VF.ttf'
fx.FONT['jp'] = _JP
fx.FONT['jpui'] = _JP

LEMON = (245, 213, 71)
INK = (30, 27, 24)
BEIGE_C, BEIGE_E = (251, 247, 238), (233, 222, 203)


def solid_glow(alpha_img, color, radius, strength=1.0):
    """Glow as a solid colour with only the alpha blurred (no dark fringes from transparent black)."""
    a = alpha_img.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
    g = Image.new('RGBA', alpha_img.size, tuple(color) + (255,)); g.putalpha(a); return g


def jp_text(s, size, fill=INK, glow=(255, 251, 238), glow_r=None):
    f = font('jp', size); bb = f.getbbox(s); pad = int(size * 0.35) + 4
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), s, font=f, fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow: out = Image.alpha_composite(out, solid_glow(m, glow, glow_r or size * 0.09, 1.6))
    t = Image.new('RGBA', (w, h), tuple(fill) + (255,)); t.putalpha(m)
    return Image.alpha_composite(out, t)


def split_lines(s):
    return [x for x in str(s).replace('\\n', '|').replace('\n', '|').split('|') if x.strip()]


def out_k(c, e):
    o = float(e.o.get('out', 0) or 0)
    return clamp((e.d - c.lt) / o) if o > 0 else 1.0


# ---------------------------------------------------------------- cinema
_bgc = {}
def beige_bg(W, H, cen=BEIGE_C, edge=BEIGE_E):
    k = (W, H, cen, edge)
    if k not in _bgc:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.clip(np.sqrt(((xx - W * 0.5) / (W * 0.9)) ** 2 + ((yy - H * 0.38) / (H * 0.75)) ** 2), 0, 1)[..., None]
        _bgc[k] = (np.float32(cen) * (1 - d) + np.float32(edge) * d) / 255.0
    return _bgc[k]


# cinema palettes: bg centre/edge, disc top/bottom, halo, headline ink/glow, watermark, kicker text, kicker bars, vignette
CINEMA_PAL = {
    'red': dict(bgc=(50, 13, 22), bge=(10, 3, 6), dtop=(168, 50, 74), dbot=(94, 11, 30), halo=(139, 26, 53), halo_a=200,
                ink=(250, 243, 230), glow=(94, 11, 30), wm=(122, 34, 54), kick=(214, 182, 170), kbar=(168, 50, 74), vig=0.35),
    'lemon': dict(bgc=BEIGE_C, bge=BEIGE_E, dtop=(255, 228, 105), dbot=(242, 199, 52), halo=(255, 226, 110), halo_a=150,
                  ink=INK, glow=(255, 251, 238), wm=(205, 168, 72), kick=(120, 104, 70), kbar=LEMON, vig=0.22),
}


def _film_lut():
    x = np.linspace(0, 1, 256, dtype=np.float32)
    x = np.clip((x - 0.5) * 1.22 + 0.5, 0, 1)
    x = x * 0.55 + (x * x * (3 - 2 * x)) * 0.45          # soft S-curve
    x = 0.035 + x * 0.94                                   # lifted blacks, rolled highlights
    lut = np.clip(x[:, None] * np.float32([1.0, 0.988, 0.965]), 0, 1)  # faint warm silver tone
    return lut.reshape(256, 1, 3).astype(np.float32)
_LUT = _film_lut()


def film_bw(img):
    g = (cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) * 255 + 0.5).clip(0, 255).astype(np.uint8)
    return _LUT[g, 0]


def sun_disc(R, top=(255, 228, 105), bot=(242, 199, 52), halo_col=(255, 226, 110), halo_a=150):
    g = int(R * 0.35); S = 2 * (R + g)
    hm = Image.new('L', (S, S), 0)
    ImageDraw.Draw(hm).ellipse([g * 0.5, g * 0.5, S - g * 0.5, S - g * 0.5], fill=halo_a)
    halo = solid_glow(hm, halo_col, g * 0.45)
    disc = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    grad = Image.new('RGBA', (S, S))
    top, bot = np.float32(top), np.float32(bot)
    t = np.linspace(0, 1, S, dtype=np.float32)[:, None, None]
    arr = np.repeat(top * (1 - t) + bot * t, S, axis=1)
    grad = Image.fromarray(np.dstack([arr, np.full((S, S, 1), 255, np.float32)]).astype(np.uint8), 'RGBA')
    mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).ellipse([g, g, S - g, S - g], fill=255)
    grad.putalpha(mask.filter(ImageFilter.GaussianBlur(1.5))); disc = grad
    return Image.alpha_composite(halo, disc)


_grain = {}
def grain(c, amt):
    key = (c.W, c.H)
    if key not in _grain:
        rng = np.random.default_rng(7); h, w = c.H // 2, c.W // 2
        _grain[key] = [cv2.resize(rng.normal(0, 1, (h, w)).astype(np.float32), (c.W, c.H), interpolation=cv2.INTER_LINEAR) for _ in range(8)]
    g = _grain[key][int(c.t * c.fps) % 8]
    lum = cv2.cvtColor(c.img.astype(np.float32), cv2.COLOR_RGB2GRAY)
    w = 0.35 + 2.6 * lum * (1 - lum)
    c.img += (g * w * amt)[..., None]


def head_top(c):
    x0, x1 = int(max(0, c.fx - c.fw * 0.6)), int(min(c.W, c.fx + c.fw * 0.6))
    rows = np.where((c.m[:, x0:x1] > 0.5).mean(1) > 0.15)[0]
    return float(rows[0]) if len(rows) else c.fy - c.fw * 1.0


def cinema_layout(c, e, lines):
    """Pick the free area for the title: above the head if there is room, else the wider side."""
    W, H = c.W, c.H; safe = H * 0.075; top = head_top(c)
    avail = top - safe - H * 0.025
    kick = 0.032 * W
    if avail > H * 0.15:
        size = lines_fit(lines, W * 0.86, 'jp', int(W * 0.16))
        size = int(min(size, (avail - kick * 1.8) / (len(lines) * 1.1)))
        return dict(mode='top', size=size, x=W / 2, y=safe, kick=kick)
    left = c.fx - c.fw * 0.85 > W - (c.fx + c.fw * 0.85)
    span = (c.fx - c.fw * 0.85 - W * 0.06) if left else (W - c.fx - c.fw * 0.85 - W * 0.06)
    size = lines_fit(lines, max(W * 0.2, span), 'jp', int(W * 0.13))
    x = W * 0.06 if left else c.fx + c.fw * 0.85
    return dict(mode='left' if left else 'right', size=size, x=x, y=max(safe, c.fy - c.fw * 1.6), kick=kick)


@effect('cinema-v1', '(v1) documentary cover: B&W person, a glowing lemon circle behind, a big Japanese headline punching in, film grain')
def fx_cinema(c, e):
    W, H = c.W, c.H; lt = c.lt; ko = out_k(c, e)
    orig = c.img.copy()
    camera(c, 1 + (float(e.o.get('push', 1.035)) - 1) * clamp(lt / max(e.d, 0.1)), c.fx, c.fy)
    m = c.m[..., None]
    person = film_bw(c.img)
    if e.o.get('bg', 'beige') == 'room':
        bg = cv2.GaussianBlur(fx.grade(c.img, 'moody'), (0, 0), 6) * 0.42
    else:
        bg = beige_bg(W, H).copy()
    # soft contact shadow around the person so she separates from the backdrop
    sh = cv2.GaussianBlur(c.m, (0, 0), W * 0.018)[..., None]
    bg = bg * (1 - 0.22 * sh)
    base = c.img; c.img = bg
    R = int(W * 0.40)
    disc = cached(e, 'disc', lambda: sun_disc(R))
    s = 0.55 + 0.45 * ease_back(clamp((lt - 0.04) / 0.36))
    place(c, disc, c.fx, c.fy + c.fw * 0.35, s, 0, clamp(lt / 0.12))
    c.img = c.img * (1 - m) + person * m
    k = clamp(lt / 0.18)
    c.img = orig * (1 - k) + c.img * k
    fx.vignette(c, 0.22 * k)
    # headline
    lines = split_lines(e.o.get('text', '映画みたいな|演出に'))
    L = cached(e, 'lay', lambda: cinema_layout(c, e, lines))
    size, x, y = L['size'], L['x'], L['y']
    kicker = e.o.get('kicker', 'DOCUMENTARY')
    if kicker:
        kim = cached(e, 'kim', lambda: fx.tracked(kicker, L['kick'], 'uib', (120, 104, 70), L['kick'] * 0.32))
        kk = ease_out((lt - 0.05) / 0.25)
        bar = rrect(W * 0.05, max(4, W * 0.006), 3, LEMON + (255,))
        if L['mode'] == 'top':
            place(c, kim, x, y + kim.height / 2, 1, 0, kk * ko, guard=True)
            place(c, bar, x - kim.width / 2 - bar.width * 0.7, y + kim.height / 2, kk, 0, kk * ko, guard=True)
            place(c, bar, x + kim.width / 2 + bar.width * 0.7, y + kim.height / 2, kk, 0, kk * ko, guard=True)
        else:
            place(c, bar, x + bar.width / 2, y + kim.height / 2, kk, 0, kk * ko, guard=True)
            place(c, kim, x + bar.width * 1.3 + kim.width / 2, y + kim.height / 2, 1, 0, kk * ko, guard=True)
        y += kim.height * 1.05
    for j, ln in enumerate(lines):
        im = cached(e, ('ln', j), lambda: jp_text(ln, size))
        p = clamp((lt - 0.06 - 0.07 * j) / 0.30)
        if p <= 0: y += size * 1.1; continue
        sc = 1.32 - 0.32 * ease_back(p)
        dx = (1 - ease_out(p)) * W * 0.10 * (-1 if j % 2 == 0 else 1)
        cx = (x if L['mode'] == 'top' else x + im.width / 2) + dx
        place(c, im, cx, y + size * 0.55, sc, 0, clamp(p * 2.5) * ko, guard=True)
        y += size * 1.1
    grain(c, float(e.o.get('grain', 0.035)) * k)
    if ko < 1: c.img = orig * (1 - ko) + c.img * ko


# ---------------------------------------------------------------- split-graph
def draw_chart(W, ch, lt, vals, unit, title, ko):
    lay = Image.new('RGBA', (W, int(ch)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, -60, W - 1, ch - 1], int(W * 0.055), fill=(252, 250, 245, 255))
    # title (small)
    ts = int(W * 0.036); ty = ch * 0.135
    tk = clamp((lt - 0.15) / 0.25)
    r = ts * 0.22
    d.ellipse([W * 0.075, ty + ts * 0.5 - r, W * 0.075 + 2 * r, ty + ts * 0.5 + r], fill=LEMON + (int(255 * tk),))
    d.text((W * 0.075 + 2 * r + ts * 0.4, ty), title, font=font('jp', ts), fill=(110, 100, 88, int(255 * tk)))
    # chart geometry
    n = len(vals); x0, x1 = W * 0.075, W * 0.925; slot = (x1 - x0) / n; bw = slot * 0.62
    base = ch * 0.865; top = ch * 0.38; vmax = max(vals)
    d.line([x0, base, x1, base], fill=(222, 214, 200, int(255 * tk)), width=3)
    for j, v in enumerate(vals):
        t0 = 0.35 + j * 0.165
        p = ease_out((lt - t0) / 0.45)
        cx = x0 + slot * (j + 0.5)
        ls = int(W * 0.03)
        la = clamp((lt - t0) / 0.15)
        lab = f'{j + 1}位'
        d.text((cx - font('jp', ls).getlength(lab) / 2, base + ls * 0.45), lab, font=font('jp', ls),
               fill=((150, 128, 60) if j == 0 else (165, 155, 142)) + (int(255 * la),))
        if p <= 0: continue
        h = (base - top) * v / vmax * p
        col = LEMON if j == 0 else (226, 216, 199)
        if j == 0:
            gm = Image.new('L', lay.size, 0)
            ImageDraw.Draw(gm).rounded_rectangle([cx - bw / 2 - 6, base - h - 6, cx + bw / 2 + 6, base], int(bw * 0.22), fill=150)
            lay.alpha_composite(solid_glow(gm, (255, 220, 90), W * 0.018))
            d = ImageDraw.Draw(lay)
        if h > 2:
            d.rounded_rectangle([cx - bw / 2, base - h, cx + bw / 2, base], int(min(bw * 0.22, h / 2)), fill=col + (255,))
            d.rectangle([cx - bw / 2, base - min(h / 2, bw * 0.22), cx + bw / 2, base], fill=col + (255,))
        # counting number
        num = str(int(round(v * p)))
        ns = int(W * (0.068 if j == 0 else 0.054)); us = int(ns * 0.5)
        fn, fu = font('jp', ns), font('jp', us)
        wn, wu = fn.getlength(num), fu.getlength(unit)
        nx = cx - (wn + wu) / 2; ny = base - h - ns * 1.18
        a = int(255 * clamp(p * 3))
        ink = INK if j == 0 else (92, 84, 74)
        d.text((nx, ny), num, font=fn, fill=ink + (a,))
        d.text((nx + wn + 2, ny + ns - us * 1.02), unit, font=fu, fill=ink + (a,))
    return lay


@effect('split-graph-v1', '(v1) top card with a 7-bar chart that grows bar by bar with counting numbers; you move to the bottom 55%')
def fx_split_graph(c, e):
    W, H = c.W, c.H; lt = c.lt; ko = out_k(c, e)
    k = ease_out(lt / 0.4) * ko
    ch = H * float(e.o.get('height', 0.45))
    z = float(e.o.get('zoom', 1.0))
    if z > 1.001: camera(c, 1 + (z - 1) * k, c.fx, c.fy)
    fy0 = cached(e, 'fy0', lambda: c.fy)
    target = ch + (H - ch) * float(e.o.get('head_at', 0.30))
    shift(c, (target - fy0) * k)
    vals = [float(v) for v in str(e.o.get('values', '20,15,12,8,5,4,3')).split(',')]
    title = e.o.get('text', 'リール再生数 TOP7')
    lay = draw_chart(W, ch, lt, vals, e.o.get('unit', '万'), title, ko)
    lay = shadowed(lay, int(W * 0.02), int(W * 0.008), 70)
    pad = (lay.width - W) // 2
    comp(c, lay, -pad, -ch * (1 - k) - pad)


# ================================================================ v2 (flashier)
import math  # noqa: E402


def char_img(ch, size, fill=INK, glow=(255, 251, 238)):
    """One glyph on a fixed-height box (consistent baseline), with a clean light glow."""
    f = font('jp', size); asc, desc = f.getmetrics(); pad = int(size * 0.3)
    w, h = int(f.getlength(ch)) + 2 * pad, asc + desc + 2 * pad
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad, pad), ch, font=f, fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow: out = Image.alpha_composite(out, solid_glow(m, glow, size * 0.09, 1.6))
    t = Image.new('RGBA', (w, h), tuple(fill) + (255,)); t.putalpha(m)
    return Image.alpha_composite(out, t)


def outline_text(s, size, color, sw, kind='jp'):
    f = font(kind, size); bb = f.getbbox(s, stroke_width=sw); pad = sw + 6
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad; pos = (pad - bb[0], pad - bb[1])
    outer = Image.new('L', (w, h), 0); ImageDraw.Draw(outer).text(pos, s, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    inner = Image.new('L', (w, h), 0); ImageDraw.Draw(inner).text(pos, s, font=f, fill=255)
    a = np.clip(np.asarray(outer, np.int16) - np.asarray(inner, np.int16), 0, 255).astype(np.uint8)
    im = Image.new('RGBA', (w, h), tuple(color) + (255,)); im.putalpha(Image.fromarray(a)); return im


def pop_bounce(p):
    """0 -> 1.15 -> 1.0"""
    if p <= 0: return 0.0
    if p < 0.55: return 1.15 * ease_out(p / 0.55)
    return 1.15 - 0.15 * fx.ease_inout((p - 0.55) / 0.45)


@effect('cinema', 'documentary cover v2: B&W person, glowing lemon circle, per-character bouncy Japanese headline over a drifting ghost watermark')
def fx_cinema2(c, e):
    W, H = c.W, c.H; lt = c.lt; ko = out_k(c, e)
    P = CINEMA_PAL.get(e.o.get('palette', 'red'), CINEMA_PAL['red'])
    orig = c.img.copy()
    camera(c, 1 + (float(e.o.get('push', 1.035)) - 1) * clamp(lt / max(e.d, 0.1)), c.fx, c.fy)
    m = c.m[..., None]
    person = film_bw(c.img)
    if e.o.get('bg', 'beige') == 'room':
        bg = cv2.GaussianBlur(fx.grade(c.img, 'moody'), (0, 0), 6) * 0.42
    else:
        bg = beige_bg(W, H, P['bgc'], P['bge']).copy()
    sh = cv2.GaussianBlur(c.m, (0, 0), W * 0.018)[..., None]
    c.img = bg * (1 - 0.22 * sh)
    lines = split_lines(e.o.get('text', '映画みたいな|演出に'))
    L = cached(e, 'lay', lambda: cinema_layout(c, e, lines))
    size, x, y = L['size'], L['x'], L['y']
    kicker = e.o.get('kicker', 'DOCUMENTARY')
    kick_h = L['kick'] * 1.6 if kicker else 0
    # (1) ghost watermark: huge outlined copy, low opacity, slow parallax drift, behind the person
    wm = e.o.get('watermark', 'CINEMA')
    wk = clamp((lt - 0.02) / 0.35)
    if wm and wm != 'none':
        block_top = y + kick_h * 0.6; block_h = len(lines) * size * 1.1 + kick_h * 0.4
        if wm == 'same':  # ghost of the same Japanese words, bigger, offset
            for j, ln in enumerate(lines):
                gim = cached(e, ('wm', j), lambda: outline_text(ln, int(size * 1.25), P['wm'], max(3, int(size * 0.03))))
                drift = W * 0.05 * (lt / 3.0) * (1 if j % 2 == 0 else -1)
                gx = (x if L['mode'] == 'top' else x + gim.width / 2) + W * 0.05 - drift
                gy = block_top + size * (0.75 + 1.1 * j) + size * 0.25
                place(c, gim, gx, gy, 1.0, 0, 0.30 * wk * ko, behind=True)
        else:  # one huge outlined English word filling the title block
            def mk():
                sz = int(block_h * 1.25)
                while sz > 20 and font('anton', sz).getlength(wm) > W * 1.08: sz = int(sz * 0.95)
                return outline_text(wm, sz, P['wm'], max(3, int(sz * 0.018)), 'anton')
            gim = cached(e, 'wmA', mk)
            drift = W * 0.06 * (lt / 3.0)
            gx = (W / 2 if L['mode'] == 'top' else x + gim.width / 2) + W * 0.03 - drift + (1 - ease_out(wk)) * W * 0.06
            gy = block_top + block_h / 2 + math.sin(lt * 1.2) * size * 0.05
            place(c, gim, gx, gy, 1.0 + 0.015 * math.sin(lt * 0.9), 0, 0.5 * wk * ko, behind=True)
    R = int(W * 0.40)
    disc = cached(e, 'disc', lambda: sun_disc(R, P['dtop'], P['dbot'], P['halo'], P['halo_a']))
    s = 0.55 + 0.45 * ease_back(clamp((lt - 0.04) / 0.36))
    place(c, disc, c.fx, c.fy + c.fw * 0.35 + math.sin(lt * 1.6) * W * 0.004, s, 0, clamp(lt / 0.12))
    c.img = c.img * (1 - m) + person * m
    k = clamp(lt / 0.18)
    c.img = orig * (1 - k) + c.img * k
    fx.vignette(c, P['vig'] * k)
    if kicker:
        kim = cached(e, 'kim', lambda: fx.tracked(kicker, L['kick'], 'uib', P['kick'], L['kick'] * 0.32))
        kk = ease_out((lt - 0.05) / 0.25)
        bar = rrect(W * 0.05, max(4, W * 0.006), 3, P['kbar'] + (255,))
        if L['mode'] == 'top':
            place(c, kim, x, y + kim.height / 2, 1, 0, kk * ko, guard=True)
            place(c, bar, x - kim.width / 2 - bar.width * 0.7, y + kim.height / 2, kk, 0, kk * ko, guard=True)
            place(c, bar, x + kim.width / 2 + bar.width * 0.7, y + kim.height / 2, kk, 0, kk * ko, guard=True)
        else:
            place(c, bar, x + bar.width / 2, y + kim.height / 2, kk, 0, kk * ko, guard=True)
            place(c, kim, x + bar.width * 1.3 + kim.width / 2, y + kim.height / 2, 1, 0, kk * ko, guard=True)
        y += kim.height * 1.05
    # (2) per-character bouncy pop, then a gentle continuous wave (never static)
    f = font('jp', size); gi = 0
    step = float(e.o.get('char_step', 0.045))
    for j, ln in enumerate(lines):
        lw = f.getlength(ln)
        x0 = (x - lw / 2) if L['mode'] == 'top' else x
        cy0 = y + size * 0.55; cum = 0.0
        for ch in ln:
            adv = f.getlength(ch)
            if ch.strip():
                im = cached(e, ('ch', size, ch), lambda: char_img(ch, size, P['ink'], P['glow']))
                p = clamp((lt - 0.10 - step * gi) / 0.34)
                if p > 0:
                    sc = pop_bounce(p) * (1 + 0.018 * math.sin(lt * 2.4 + gi * 0.55))
                    dy = -(1 - ease_out(p)) * size * 0.45 + math.sin(lt * 2.0 + gi * 0.6) * size * 0.022
                    place(c, im, x0 + cum + adv / 2, cy0 + dy, sc, 0, clamp(p * 4) * ko, guard=True)
            cum += adv; gi += 1
        y += size * 1.1
    grain(c, float(e.o.get('grain', 0.035)) * k)
    if ko < 1: c.img = orig * (1 - ko) + c.img * ko


# ---------------------------------------------------------------- split-graph v2
VIVID = (255, 212, 0)


def spring(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 1 - math.exp(-6 * u) * math.cos(3 * math.pi * u)


def grad_bar(w, h, top, bot, r):
    w, h = max(2, int(w)), max(2, int(h))
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = np.repeat(np.float32(top) * (1 - t) + np.float32(bot) * t, w, axis=1)
    im = Image.fromarray(np.dstack([arr, np.full((h, w, 1), 255, np.float32)]).astype(np.uint8), 'RGBA')
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m); r = int(min(r, h / 2, w / 2))
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); d.rectangle([0, h // 2, w - 1, h - 1], fill=255)
    im.putalpha(m); return im, m


def crown(s, col=VIVID):
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(s * 0.08, s * 0.82), (s * 0.08, s * 0.32), (s * 0.3, s * 0.56), (s * 0.5, s * 0.18), (s * 0.7, s * 0.56), (s * 0.92, s * 0.32), (s * 0.92, s * 0.82)]
    d.polygon(pts, fill=col + (255,)); d.rectangle([s * 0.08, s * 0.76, s * 0.92, s * 0.9], fill=(240, 160, 0, 255))
    for px, py in [(s * 0.08, s * 0.3), (s * 0.5, s * 0.15), (s * 0.92, s * 0.3)]:
        d.ellipse([px - s * 0.07, py - s * 0.07, px + s * 0.07, py + s * 0.07], fill=(255, 240, 150, 255))
    return Image.alpha_composite(solid_glow(im.split()[3], (255, 225, 80), s * 0.08, 1.2), im)


_crown = {}
def cached_crown(s):
    if s not in _crown: _crown[s] = crown(s)
    return _crown[s]


OTHER = [((255, 168, 64), (255, 205, 130)), ((255, 178, 96), (255, 214, 158)), ((252, 190, 128), (253, 221, 178)),
         ((248, 198, 150), (250, 226, 196)), ((240, 204, 166), (246, 228, 204)), ((234, 208, 178), (243, 230, 212))]

_sg = {}
def card_bg(W, h, lt):
    """Warm cream card with a drifting soft light and a diagonal shine sweep."""
    key = (W, h)
    if key not in _sg:
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        base = np.repeat(np.float32((255, 252, 242)) * (1 - t) + np.float32((255, 241, 214)) * t, W, axis=1)
        base = Image.fromarray(np.dstack([base, np.full((h, W, 1), 255, np.float32)]).astype(np.uint8), 'RGBA')
        bs = int(W * 0.9); bm = Image.new('L', (bs, bs), 0); ImageDraw.Draw(bm).ellipse([bs * 0.2, bs * 0.2, bs * 0.8, bs * 0.8], fill=120)
        blob = solid_glow(bm, (255, 220, 90), bs * 0.12)
        sw = int(W * 0.16); sm = Image.new('L', (sw * 3, int(h * 1.6)), 0)
        ImageDraw.Draw(sm).rectangle([sw, 0, sw * 2, sm.height], fill=90)
        shine = solid_glow(sm, (255, 255, 255), sw * 0.35).rotate(-24, Image.BICUBIC, expand=True)
        mask = Image.new('L', (W, h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, -100, W - 1, h - 1], int(W * 0.055), fill=255)
        _sg[key] = (base, blob, shine, mask)
    base, blob, shine, mask = _sg[key]
    im = base.copy()
    big = Image.new('RGBA', (W + 2 * blob.width, h + 2 * blob.height), (0, 0, 0, 0))
    bx = W * (0.55 + 0.3 * math.sin(lt * 0.9)) - blob.width / 2; by = h * (0.45 + 0.2 * math.cos(lt * 0.7)) - blob.height / 2
    big.alpha_composite(blob, (int(bx + blob.width), int(by + blob.height)))
    ph = ((lt - 0.4) % 1.8) / 1.8; sx = int(-shine.width + (W + shine.width) * ph)
    big.alpha_composite(shine, (int(sx + blob.width), int(blob.height - (shine.height - h) / 2)))
    im.alpha_composite(big.crop((blob.width, blob.height, blob.width + W, blob.height + h)))
    im.putalpha(mask); return im


def draw_chart2(W, ch, lt, vals, unit, title, ext):
    h = int(ch + ext)
    lay = card_bg(W, h, lt); d = ImageDraw.Draw(lay)
    oy = ext
    ts = int(W * 0.036); ty = oy + ch * 0.135; tk = clamp((lt - 0.15) / 0.25); r = ts * 0.22
    d.ellipse([W * 0.075, ty + ts * 0.5 - r, W * 0.075 + 2 * r, ty + ts * 0.5 + r], fill=VIVID + (int(255 * tk),))
    d.text((W * 0.075 + 2 * r + ts * 0.4, ty), title, font=font('jp', ts), fill=(130, 98, 60, int(255 * tk)))
    n = len(vals); x0, x1 = W * 0.075, W * 0.925; slot = (x1 - x0) / n; bw = slot * 0.64
    base = oy + ch * 0.865; top = oy + ch * 0.42; vmax = max(vals)
    d.line([x0, base, x1, base], fill=(238, 214, 176, int(255 * tk)), width=3)
    for j, v in enumerate(vals):
        t0 = 0.30 + j * 0.13; u = (lt - t0) / 0.6
        cx = x0 + slot * (j + 0.5); ls = int(W * 0.03); la = clamp(u * 4)
        lab = f'{j + 1}位'
        d.text((cx - font('jp', ls).getlength(lab) / 2, base + ls * 0.45), lab, font=font('jp', ls),
               fill=((225, 140, 0) if j == 0 else (190, 150, 110)) + (int(255 * la),))
        if u <= 0: continue
        sp = spring(u); bh = (base - top) * v / vmax * sp
        if bh > 3:
            if j == 0:
                done = clamp((u - 0.6) / 0.3)
                pulse = 0.5 + 0.5 * math.sin((lt - t0) * 2 * math.pi * 1.1)
                gm = Image.new('L', lay.size, 0)
                ImageDraw.Draw(gm).rounded_rectangle([cx - bw / 2 - 10, base - bh - 10, cx + bw / 2 + 10, base], int(bw * 0.25), fill=int(200 * (0.6 + 0.4 * pulse * done)))
                lay.alpha_composite(solid_glow(gm, (255, 210, 0), W * (0.02 + 0.012 * pulse * done)))
                bar, bm = grad_bar(bw, bh, (255, 232, 70), (255, 196, 0), bw * 0.24)
                if lt - t0 > 0.5:  # glint: a diagonal white band sweeping the bar
                    gp = ((lt - t0 - 0.5) % 1.4) / 1.4
                    gl = Image.new('L', bar.size, 0); gx = -bw - bh * 0.5 + (bw * 2 + bh * 0.5) * gp
                    ImageDraw.Draw(gl).polygon([(gx, bh), (gx + bw * 0.35, bh), (gx + bw * 0.35 + bh * 0.5, 0), (gx + bh * 0.5, 0)], fill=170)
                    gl = Image.fromarray(np.minimum(np.asarray(gl), np.asarray(bm)))
                    bar.alpha_composite(solid_glow(gl, (255, 255, 245), 3))
            else:
                bar, _ = grad_bar(bw, bh, OTHER[min(j - 1, 5)][0], OTHER[min(j - 1, 5)][1], bw * 0.24)
            lay.alpha_composite(bar, (int(cx - bw / 2), int(base - bh)))
            d = ImageDraw.Draw(lay)
        cnt = v * clamp(ease_out(u / 0.75))
        bump = math.sin(math.pi * clamp((u - 0.72) / 0.3)) if u > 0.72 else 0.0
        ns = int(W * (0.074 if j == 0 else 0.056) * (1 + 0.28 * bump)); us = int(ns * 0.5)
        fn, fu = font('jp', ns), font('jp', us); num = str(int(round(cnt)))
        wn, wu = fn.getlength(num), fu.getlength(unit)
        nx = cx - (wn + wu) / 2; ny = base - bh - ns * 1.16
        a = int(255 * clamp(u * 4)); ink = INK if j == 0 else (150, 82, 20)
        d.text((nx, ny), num, font=fn, fill=ink + (a,))
        d.text((nx + wn + 2, ny + ns - us * 1.02), unit, font=fu, fill=ink + (a,))
        if j == 0:
            ck = clamp((u - 0.75) / 0.35)
            if ck > 0:
                cs = int(W * 0.075 * ease_back(ck)) + 2
                cr = cached_crown(int(W * 0.075)).resize((cs, cs), Image.BILINEAR)
                cr = cr.rotate(math.sin(lt * 3) * 6, Image.BICUBIC, expand=True)
                lay.alpha_composite(cr, (int(cx - cr.width / 2), int(ny - cr.height * 0.82)))
                for sx, sy, ph in [(-0.75, 0.15, 0.0), (0.8, 0.35, 0.33), (-0.55, 0.7, 0.66)]:
                    tw = 0.5 + 0.5 * math.sin((lt * 2.2 + ph) * 2 * math.pi)
                    ss = int(W * 0.04 * (0.4 + 0.6 * tw) * ck)
                    if ss > 6:
                        lay.alpha_composite(fx.star(ss, (255, 250, 220)), (int(cx + sx * bw - ss / 2), int(base - bh * (1 - sy) - ss / 2)))
            d = ImageDraw.Draw(lay)
    return lay


# ---------------------------------------------------------------- split-graph neon palette
PINK, CYAN = (255, 46, 147), (25, 230, 255)

_ng = {}
def neon_card_bg(W, h, lt):
    key = (W, h)
    if key not in _ng:
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        base = np.repeat(np.float32((30, 18, 48)) * (1 - t) + np.float32((14, 10, 26)) * t, W, axis=1)
        base = Image.fromarray(np.dstack([base, np.full((h, W, 1), 255, np.float32)]).astype(np.uint8), 'RGBA')
        bs = int(W * 0.8); bm = Image.new('L', (bs, bs), 0); ImageDraw.Draw(bm).ellipse([bs * 0.2, bs * 0.2, bs * 0.8, bs * 0.8], fill=70)
        bp, bc = solid_glow(bm, PINK, bs * 0.13), solid_glow(bm, CYAN, bs * 0.13)
        sw = int(W * 0.14); sm = Image.new('L', (sw * 3, int(h * 1.6)), 0)
        ImageDraw.Draw(sm).rectangle([sw, 0, sw * 2, sm.height], fill=38)
        shine = solid_glow(sm, (255, 255, 255), sw * 0.35).rotate(-24, Image.BICUBIC, expand=True)
        mask = Image.new('L', (W, h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, -100, W - 1, h - 1], int(W * 0.055), fill=255)
        _ng[key] = (base, bp, bc, shine, mask)
    base, bp, bc, shine, mask = _ng[key]
    P = bp.width
    big = Image.new('RGBA', (W + 2 * P, h + 2 * P + shine.height), (0, 0, 0, 0))
    big.alpha_composite(bp, (int(P + W * (0.22 + 0.18 * math.sin(lt * 0.8)) - P / 2), int(P + h * (0.35 + 0.15 * math.cos(lt * 0.9)) - P / 2)))
    big.alpha_composite(bc, (int(P + W * (0.80 + 0.15 * math.cos(lt * 0.7)) - P / 2), int(P + h * (0.65 + 0.15 * math.sin(lt * 1.1)) - P / 2)))
    ph = ((lt - 0.4) % 1.8) / 1.8; sx = int(-shine.width + (W + shine.width) * ph)
    big.alpha_composite(shine, (P + sx, int(P - (shine.height - h) / 2)) if P - (shine.height - h) / 2 >= 0 else (P + sx, 0))
    im = base.copy(); im.alpha_composite(big.crop((P, P, P + W, P + h)))
    im.putalpha(mask); return im


def neon_crown(s):
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(s * 0.08, s * 0.82), (s * 0.08, s * 0.32), (s * 0.3, s * 0.56), (s * 0.5, s * 0.18), (s * 0.7, s * 0.56), (s * 0.92, s * 0.32), (s * 0.92, s * 0.82)], fill=(255, 255, 255, 255))
    for px, py in [(s * 0.08, s * 0.3), (s * 0.5, s * 0.15), (s * 0.92, s * 0.3)]:
        d.ellipse([px - s * 0.07, py - s * 0.07, px + s * 0.07, py + s * 0.07], fill=(255, 255, 255, 255))
    d.rectangle([s * 0.08, s * 0.74, s * 0.92, s * 0.9], fill=PINK + (255,))
    return Image.alpha_composite(solid_glow(im.split()[3], PINK, s * 0.09, 1.8), im)


_ncr = {}
def draw_chart_neon(W, ch, lt, vals, unit, title, ext):
    h = int(ch + ext)
    lay = neon_card_bg(W, h, lt); d = ImageDraw.Draw(lay)
    oy = ext
    ts = int(W * 0.036); ty = oy + ch * 0.135; tk = clamp((lt - 0.15) / 0.25); r = ts * 0.22
    d.ellipse([W * 0.075, ty + ts * 0.5 - r, W * 0.075 + 2 * r, ty + ts * 0.5 + r], fill=PINK + (int(255 * tk),))
    d.text((W * 0.075 + 2 * r + ts * 0.4, ty), title, font=font('jp', ts), fill=(226, 218, 240, int(255 * tk)))
    n = len(vals); x0, x1 = W * 0.075, W * 0.925; slot = (x1 - x0) / n; bw = slot * 0.62
    base = oy + ch * 0.865; top = oy + ch * 0.42; vmax = max(vals)
    d.line([x0, base, x1, base], fill=(96, 80, 130, int(255 * tk)), width=3)
    gp, gc, g1, gn = (Image.new('L', lay.size, 0) for _ in range(4))
    bars, nums = [], []
    for j, v in enumerate(vals):
        t0 = 0.30 + j * 0.13; u = (lt - t0) / 0.6
        cx = x0 + slot * (j + 0.5); ls = int(W * 0.03); la = clamp(u * 4)
        lab = f'{j + 1}位'
        d.text((cx - font('jp', ls).getlength(lab) / 2, base + ls * 0.45), lab, font=font('jp', ls),
               fill=(PINK if j == 0 else (176, 166, 206)) + (int(255 * la),))
        if u <= 0: continue
        bh = (base - top) * v / vmax * spring(u)
        if j == 0:
            done = clamp((u - 0.6) / 0.3); pulse = 0.5 + 0.5 * math.sin((lt - t0) * 2 * math.pi * 1.2)
            gl, cols, gmask, gval = 1, ((255, 120, 200), (255, 20, 140)), g1, int(255 * (0.7 + 0.3 * pulse * done))
        elif j % 2 == 1:
            cols, gmask, gval = ((150, 248, 255), (0, 196, 236)), gc, 150
        else:
            cols, gmask, gval = ((255, 150, 210), (236, 50, 150)), gp, 150
        if bh > 3:
            ImageDraw.Draw(gmask).rounded_rectangle([cx - bw / 2 - 6, base - bh - 6, cx + bw / 2 + 6, base], int(bw * 0.25), fill=gval)
            bars.append((j, cx, bh, cols, t0))
        nums.append((j, v, u, cx, bh))
    pulse1 = 0.5 + 0.5 * math.sin((lt - 0.30) * 2 * math.pi * 1.2)
    lay.alpha_composite(solid_glow(gp, PINK, W * 0.018))
    lay.alpha_composite(solid_glow(gc, CYAN, W * 0.018))
    lay.alpha_composite(solid_glow(g1, PINK, W * (0.026 + 0.014 * pulse1), 1.4))
    for j, cx, bh, cols, t0 in bars:
        bar, bm = grad_bar(bw, bh, cols[0], cols[1], bw * 0.24)
        if j == 0 and lt - t0 > 0.5:  # glint sweep
            gp_ = ((lt - t0 - 0.5) % 1.4) / 1.4
            g = Image.new('L', bar.size, 0); gx = -bw - bh * 0.5 + (bw * 2 + bh * 0.5) * gp_
            ImageDraw.Draw(g).polygon([(gx, bh), (gx + bw * 0.35, bh), (gx + bw * 0.35 + bh * 0.5, 0), (gx + bh * 0.5, 0)], fill=190)
            g = Image.fromarray(np.minimum(np.asarray(g), np.asarray(bm)))
            bar.alpha_composite(solid_glow(g, (255, 255, 255), 3))
        lay.alpha_composite(bar, (int(cx - bw / 2), int(base - bh)))
    d = ImageDraw.Draw(lay)
    for j, v, u, cx, bh in nums:
        cnt = v * clamp(ease_out(u / 0.75))
        bump = math.sin(math.pi * clamp((u - 0.72) / 0.3)) if u > 0.72 else 0.0
        ns = int(W * (0.076 if j == 0 else 0.056) * (1 + 0.28 * bump)); us = int(ns * 0.5)
        fn, fu = font('jp', ns), font('jp', us); num = str(int(round(cnt)))
        wn, wu = fn.getlength(num), fu.getlength(unit)
        nx = cx - (wn + wu) / 2; ny = base - bh - ns * 1.16; a = int(255 * clamp(u * 4))
        if j == 0:
            gd = ImageDraw.Draw(gn); gd.text((nx, ny), num, font=fn, fill=a); gd.text((nx + wn + 2, ny + ns - us * 1.02), unit, font=fu, fill=a)
        d.text((nx, ny), num, font=fn, fill=(255, 255, 255, a))
        d.text((nx + wn + 2, ny + ns - us * 1.02), unit, font=fu, fill=(255, 255, 255, a))
        if j == 0:
            num1 = (nx, ny, wn, ns, us, fn, fu, num, a)
            ck = clamp((u - 0.75) / 0.35)
            if ck > 0:
                cs = int(W * 0.075 * ease_back(ck)) + 2
                key = int(W * 0.075)
                if key not in _ncr: _ncr[key] = neon_crown(key)
                cr = _ncr[key].resize((cs, cs), Image.BILINEAR).rotate(math.sin(lt * 3) * 6, Image.BICUBIC, expand=True)
                crown_at = (int(cx - cr.width / 2), int(ny - cr.height * 0.8), cr)
                for sx, sy, ph in [(-0.78, 0.12, 0.0), (0.82, 0.32, 0.33), (-0.6, 0.66, 0.66), (0.7, 0.85, 0.15)]:
                    tw = 0.5 + 0.5 * math.sin((lt * 2.2 + ph) * 2 * math.pi)
                    ss = int(W * 0.045 * (0.35 + 0.65 * tw) * ck)
                    if ss > 6: lay.alpha_composite(fx.star(ss, (255, 245, 252)), (int(cx + sx * bw - ss / 2), int(base - bh * (1 - sy) - ss / 2)))
                lay.alpha_composite(crown_at[2], crown_at[:2])
    if any(j == 0 for j, *_ in nums):
        glow = solid_glow(gn, PINK, W * 0.012, 1.5)
        under = lay.copy(); lay = Image.alpha_composite(under, glow)
        nx, ny, wn, ns, us, fn, fu, num, a = num1
        d = ImageDraw.Draw(lay)
        d.text((nx, ny), num, font=fn, fill=(255, 255, 255, a))
        d.text((nx + wn + 2, ny + ns - us * 1.02), unit, font=fu, fill=(255, 255, 255, a))
    return lay

@effect('split-graph', 'v2: card pops in with overshoot, bars spring up with bounce, counting numbers pop, glowing vivid No.1 bar with glint, crown and sparkles')
def fx_split_graph2(c, e):
    W, H = c.W, c.H; lt = c.lt; ko = out_k(c, e)
    kc = ease_back(clamp(lt / 0.45)) * ko; kv = ease_out(lt / 0.4) * ko
    ch = H * float(e.o.get('height', 0.45)); ext = int(H * 0.08)
    z = float(e.o.get('zoom', 1.0))
    if z > 1.001: camera(c, 1 + (z - 1) * kv, c.fx, c.fy)
    fy0 = cached(e, 'fy0', lambda: c.fy)
    target = ch + (H - ch) * float(e.o.get('head_at', 0.30))
    shift(c, (target - fy0) * kv)
    vals = [float(v) for v in str(e.o.get('values', '20,15,12,8,5,4,3')).split(',')]
    draw = draw_chart2 if e.o.get('palette', 'neon') == 'lemon' else draw_chart_neon
    lay = draw(W, ch, lt, vals, e.o.get('unit', '万'), e.o.get('text', 'リール再生数 TOP7'), ext)
    lay = shadowed(lay, int(W * 0.022), int(W * 0.01), 85)
    pad = (lay.width - W) // 2
    comp(c, lay, -pad, -ext - ch * (1 - kc) - pad)



# ================================================================ 11本目 v2 additions (2026-10-28)
# editor         : detailed video-editing-software UI around you (viewer, inspector, tools, multi-track timeline, waveforms, playhead)
# spotlight-type : spotlight darkening + crisp Japanese word typed in one character at a time, kept clear of the hair
def _mono(sz): return font('mono', sz)
def _ui(sz): return font('uim', sz)
def _uib(sz): return font('uib', sz)
ED_RED = (232, 62, 52)


def _wave(n, seed, smooth=3, base=0.25):
    rnd = np.random.default_rng(seed); a = rnd.random(n)
    k = np.ones(smooth) / smooth; a = np.convolve(a, k, 'same'); env = 0.55 + 0.45 * np.sin(np.linspace(0, 9, n) + seed) ** 2
    return np.clip(base + a * env, 0.05, 1.0)


def _editor_panel(W):
    """Static timeline panel (RGBA), width W, height 780."""
    PH = 780; im = Image.new('RGBA', (W, PH), (19, 16, 17, 246)); d = ImageDraw.Draw(im)
    d.line([(0, 0), (W, 0)], fill=ED_RED + (255,), width=3)
    tabs = ['Edit', 'Color', 'Audio', 'Export']; x = 24
    for j, t in enumerate(tabs):
        f = _uib(28) if j == 0 else _ui(28); w = f.getlength(t)
        d.text((x, 34), t, font=f, fill=(255, 255, 255, 255) if j == 0 else (150, 144, 140, 255), anchor='lm')
        if j == 0: d.rounded_rectangle([x, 54, x + w, 58], 2, fill=ED_RED + (255,))
        x += w + 40
    d.rounded_rectangle([W - 300, 31, W - 120, 37], 3, fill=(70, 62, 62, 255)); d.ellipse([W - 230, 23, W - 208, 45], fill=(235, 230, 226, 255))
    d.text((W - 100, 34), '1:1', font=_mono(24), fill=(170, 164, 160, 255), anchor='lm')
    RY = 70; d.rectangle([0, RY, W, RY + 46], fill=(28, 24, 25, 255))
    HX = 150
    for k in range(0, 60):
        xx = HX + k * 30
        if xx > W: break
        major = k % 5 == 0
        d.line([(xx, RY + (8 if major else 28)), (xx, RY + 46)], fill=(120, 112, 110, 255), width=2 if major else 1)
        if major: d.text((xx + 6, RY + 16), f'00:{10 + k // 5:02d}', font=_mono(20), fill=(170, 164, 160, 255), anchor='lm')
    rows = [('V3', 66, 'title'), ('V2', 84, 'broll'), ('V1', 96, 'main'), ('A1', 76, 'voice'), ('A2', 76, 'music'), ('A3', 60, 'sfx')]
    y = RY + 54; geo = []
    for name, h, kind in rows:
        d.rectangle([0, y, HX - 6, y + h], fill=(32, 28, 29, 255))
        d.text((18, y + h / 2), name, font=_uib(28), fill=(235, 230, 226, 255), anchor='lm')
        d.ellipse([70, y + h / 2 - 9, 92, y + h / 2 + 9], outline=(150, 144, 140, 255), width=2); d.ellipse([78, y + h / 2 - 3, 84, y + h / 2 + 3], fill=(150, 144, 140, 255))
        d.rounded_rectangle([104, y + h / 2 - 4, 124, y + h / 2 + 11], 3, outline=(150, 144, 140, 255), width=2); d.arc([107, y + h / 2 - 14, 121, y + h / 2 + 2], 180, 360, fill=(150, 144, 140, 255), width=2)
        d.line([(HX, y + h + 3), (W, y + h + 3)], fill=(40, 35, 36, 255), width=1)
        geo.append((name, y, h, kind)); y += h + 6
    return im, geo, PH


def _clips_layer(W, geo, thumb):
    HX = 150; layers = []
    for ti, (name, y, h, kind) in enumerate(geo):
        L = Image.new('RGBA', (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        if kind == 'main':
            for a, b, lab in [(HX + 6, 520, 'dreamina-01.mp4'), (526, 860, 'dreamina-02.mp4'), (866, W + 40, 'dreamina-01.mp4')]:
                d.rounded_rectangle([a, 2, b, h - 2], 8, fill=(150, 34, 32, 255), outline=(255, 110, 96, 255), width=2)
                tw = thumb.width; x = a + 4
                while x + 8 < min(b, W) - 4:
                    t = thumb.crop((0, 0, int(min(tw, min(b, W) - 4 - x)), thumb.height)); L.alpha_composite(t, (int(x), 30)); x += tw + 2
                d.rectangle([a + 2, 2, b - 2, 26], fill=(150, 34, 32, 255)); d.text((a + 10, 14), lab, font=_mono(18), fill=(255, 235, 230, 255), anchor='lm')
        elif kind == 'broll':
            for a, b, lab in [(300, 470, 'city.mov'), (640, 780, 'cafe.mov'), (930, W + 40, 'desk.mov')]:
                d.rounded_rectangle([a, 4, b, h - 4], 8, fill=(40, 120, 140, 255), outline=(120, 220, 235, 255), width=2)
                d.text((a + 10, 20), lab, font=_mono(18), fill=(230, 250, 255, 255), anchor='lm')
                for q in range(int((min(b, W) - a - 16) / 46)): d.rectangle([a + 8 + q * 46, 34, a + 50 + q * 46, h - 10], fill=(70, 160, 178, 255))
        elif kind == 'title':
            for a, b, lab in [(200, 430, 'T  Title 01'), (560, 720, 'T  Lower 3rd'), (880, 1040, 'T  Logo')]:
                d.rounded_rectangle([a, 6, b, h - 6], 8, fill=(196, 104, 40, 255), outline=(255, 180, 110, 255), width=2)
                d.text((a + 12, h / 2), lab, font=_uib(22), fill=(255, 245, 235, 255), anchor='lm')
        elif kind in ('voice', 'music'):
            col = (52, 168, 96) if kind == 'voice' else (70, 110, 210); lab = 'VO_take3.wav' if kind == 'voice' else 'BGM_main.mp3'
            spans = [(HX + 6, 600), (630, W + 40)] if kind == 'voice' else [(HX + 6, W + 40)]
            wv = _wave(400, 3 if kind == 'voice' else 8, 3 if kind == 'voice' else 6, 0.15 if kind == 'voice' else 0.35)
            for a, b in spans:
                d.rounded_rectangle([a, 3, b, h - 3], 8, fill=tuple(int(v * 0.45) for v in col) + (255,), outline=col + (255,), width=2)
                cy = h / 2 + 8
                for xx in range(int(a) + 6, int(min(b, W)) - 4, 4):
                    amp = wv[(xx // 4) % len(wv)] * (h * 0.32)
                    d.line([(xx, cy - amp), (xx, cy + amp)], fill=tuple(min(255, int(v * 1.5)) for v in col) + (255,), width=2)
                d.text((a + 10, 14), lab, font=_mono(17), fill=(235, 245, 235, 255), anchor='lm')
        elif kind == 'sfx':
            for a, b, lab in [(240, 340, 'whoosh'), (520, 600, 'pop'), (760, 860, 'click'), (960, 1050, 'riser')]:
                d.rounded_rectangle([a, 4, b, h - 4], 8, fill=(120, 60, 150, 255), outline=(200, 140, 240, 255), width=2)
                d.text((a + 8, h / 2), lab, font=_mono(17), fill=(245, 235, 255, 255), anchor='lm')
        layers.append((L, y))
    return layers


def _top_bar(W, title='Project 11 · Timeline 01'):
    im = Image.new('RGBA', (W, 74), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 0, W - 20, 73], 20, fill=(24, 20, 21, 235), outline=(255, 255, 255, 30), width=2)
    d.ellipse([44, 27, 64, 47], fill=ED_RED + (255,)); d.text((80, 37), title, font=(font('jp', 28) if any(ord(ch) > 0x2E7F for ch in title) else _uib(28)), fill=(240, 235, 232, 255), anchor='lm')
    d.text((W - 230, 37), '4K · 30p', font=_mono(22), fill=(170, 164, 160, 255), anchor='rm')
    d.rounded_rectangle([W - 210, 14, W - 40, 60], 23, fill=ED_RED + (255,)); d.text((W - 125, 37), 'Export', font=_uib(26), fill=(255, 255, 255, 255), anchor='mm')
    return im


def _viewer_frame(W, vh):
    im = Image.new('RGBA', (W, vh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 130, 40, W - 130, vh - 120; L = 46; col = (255, 255, 255, 150)
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y), (x + sx * L, y)], fill=col, width=3); d.line([(x, y), (x, y + sy * L)], fill=col, width=3)
    d.text((x0 + 10, y0 + 30), 'VIEWER', font=_mono(20), fill=(255, 255, 255, 170), anchor='lm')
    d.text((x1 - 10, y0 + 30), 'Fit 100%', font=_mono(20), fill=(255, 255, 255, 170), anchor='rm')
    return im


def _transport(W, tc, lt):
    im = Image.new('RGBA', (W, 92), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 0, W - 20, 91], 22, fill=(20, 17, 18, 225), outline=(255, 255, 255, 28), width=2)
    cx = 60; wc = (230, 225, 222, 255)
    d.polygon([(cx, 46), (cx + 20, 32), (cx + 20, 60)], fill=wc); d.polygon([(cx + 20, 46), (cx + 40, 32), (cx + 40, 60)], fill=wc)
    d.ellipse([cx + 62, 20, cx + 114, 72], fill=ED_RED + (255,)); d.rectangle([cx + 80, 34, cx + 86, 58], fill=(255, 255, 255, 255)); d.rectangle([cx + 91, 34, cx + 97, 58], fill=(255, 255, 255, 255))
    d.polygon([(cx + 136, 32), (cx + 156, 46), (cx + 136, 60)], fill=wc); d.polygon([(cx + 156, 32), (cx + 176, 46), (cx + 156, 60)], fill=wc)
    d.text((W - 50, 46), tc, font=_mono(40), fill=(255, 255, 255, 255), anchor='rm')
    sx0, sx1 = 270, W - 390; d.rounded_rectangle([sx0, 43, sx1, 49], 3, fill=(80, 72, 72, 255))
    p = clamp(0.3 + lt * 0.15); xp = sx0 + (sx1 - sx0) * p
    d.rounded_rectangle([sx0, 43, xp, 49], 3, fill=ED_RED + (255,)); d.ellipse([xp - 10, 36, xp + 10, 56], fill=(255, 255, 255, 255))
    return im


def _toolbar():
    im = Image.new('RGBA', (84, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im); wc = (230, 225, 222, 255)
    d.rounded_rectangle([0, 0, 83, 419], 22, fill=(22, 18, 19, 225), outline=(255, 255, 255, 30), width=2)
    d.rounded_rectangle([12, 170, 71, 250], 14, fill=ED_RED + (255,))
    d.polygon([(30, 30), (30, 70), (40, 60), (48, 74), (54, 71), (47, 57), (60, 57)], fill=wc)
    d.line([(26, 150), (58, 112)], fill=wc, width=5); d.ellipse([20, 140, 34, 154], outline=wc, width=3)
    d.line([(42, 186), (42, 234)], fill=(255, 255, 255, 255), width=4); d.polygon([(30, 190), (54, 190), (42, 206)], fill=(255, 255, 255, 255))
    d.text((42, 290), 'T', font=_uib(44), fill=wc, anchor='mm')
    d.ellipse([24, 352, 52, 380], outline=wc, width=4); d.line([(50, 378), (62, 392)], fill=wc, width=5)
    return im


def _inspector(lt):
    w, h = 300, 440; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=(22, 18, 19, 228), outline=(255, 255, 255, 30), width=2)
    d.text((22, 34), 'Inspector', font=_uib(28), fill=(245, 240, 236, 255), anchor='lm')
    d.text((w - 22, 34), 'Color', font=_ui(22), fill=ED_RED + (255,), anchor='rm')
    d.line([(20, 62), (w - 20, 62)], fill=(255, 255, 255, 40), width=1)
    rows = [('Exposure', 0.62, '+0.4'), ('Contrast', 0.71, '+18'), ('Saturation', 0.38, '-12'), ('Temp', 0.66, '5600K'), ('Vignette', 0.55, '35')]
    for j, (lab, v, val) in enumerate(rows):
        y = 96 + j * 70; p = ease_out((lt - 0.35 - 0.1 * j) / 0.6); vv = 0.5 + (v - 0.5) * p
        d.text((22, y), lab, font=_ui(22), fill=(200, 194, 190, 255), anchor='lm'); d.text((w - 22, y), val, font=_mono(20), fill=(245, 240, 236, 255), anchor='rm')
        d.rounded_rectangle([22, y + 22, w - 22, y + 28], 3, fill=(70, 62, 62, 255))
        d.rounded_rectangle([22, y + 22, 22 + (w - 44) * vv, y + 28], 3, fill=ED_RED + (255,))
        d.ellipse([22 + (w - 44) * vv - 10, y + 15, 22 + (w - 44) * vv + 10, y + 35], fill=(255, 255, 255, 255))
    return im


@effect('editor', 'a detailed video-editor UI around you: viewer + transport + timecode, tool bar, inspector sliders, 6-track timeline with thumbnails, waveforms and a moving playhead')
def fx_editor(c, e):
    W, H = c.W, c.H; lt = c.lt; k = ease_out(lt / 0.5)
    m = c.m[..., None]
    lum = (c.img @ np.float32([0.299, 0.587, 0.114]))[..., None]
    bg = np.clip(lum * np.float32([1.0, 0.36, 0.33]) * 0.8, 0, 1); you = np.clip(c.img * np.float32([1.04, 0.9, 0.86]), 0, 1)
    c.img = c.img * (1 - k) + (you * m + bg * (1 - m)) * k
    thumb = cached(e, 'th', lambda: Image.fromarray((np.clip(cv2.resize(c.img, (38, 64), interpolation=cv2.INTER_AREA), 0, 1) * 255).astype(np.uint8)).convert('RGBA'))
    fy0 = cached(e, 'fy0', lambda: c.fy)
    shift(c, (H * 0.30 - fy0) * k)
    panel, geo, PH = cached(e, 'pan', lambda: _editor_panel(W))
    clips = cached(e, 'clips', lambda: _clips_layer(W, geo, thumb))
    PY = H - PH + 60
    VY0, VY1 = int(H * 0.15), PY - 8
    dimk = 0.55 * k
    c.img[:VY0] *= (1 - dimk)
    bar = cached(e, 'bar', lambda: _top_bar(W, e.o.get('text', 'Project 11 · Timeline 01')))
    comp(c, bar, 0, VY0 - bar.height + 60 - (1 - k) * 120, k)
    vf = cached(e, 'vf', lambda: _viewer_frame(W, VY1 - VY0))
    comp(c, vf, 0, VY0 + 40, k)
    fr = int(lt * 30); tc = f'00:00:{12 + fr // 30:02d}:{fr % 30:02d}'
    tp = _transport(W, tc, lt)
    comp(c, tp, 0, VY1 - tp.height - 10, k)
    tb = cached(e, 'tb', _toolbar)
    comp(c, tb, 22 - (1 - ease_out((lt - 0.1) / 0.45)) * 160, VY0 + 140, k)
    ins = _inspector(lt)
    comp(c, ins, W - ins.width - 22 + (1 - ease_out((lt - 0.15) / 0.45)) * 340, VY0 + 140, k)
    py = PY + (1 - ease_out(lt / 0.45)) * PH
    comp(c, panel, 0, py)
    for ti, (L, ly) in enumerate(clips):
        kk = ease_out((lt - 0.15 - 0.07 * ti) / 0.45)
        if kk <= 0: continue
        comp(c, L, (1 - kk) * W * 0.6, py + ly, clamp(kk * 1.5))
    px = 190 + (W - 300) * clamp(lt / max(0.5, e.d)) * 0.95
    top = py + 70; bot = py + PH
    ph = Image.new('RGBA', (60, int(bot - top) + 30), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph)
    glow = Image.new('RGBA', ph.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).line([(30, 10), (30, ph.height)], fill=ED_RED + (200,), width=10)
    ph.alpha_composite(glow.filter(ImageFilter.GaussianBlur(5)))
    pd.line([(30, 10), (30, ph.height)], fill=(255, 255, 255, 255), width=3)
    pd.polygon([(16, 0), (44, 0), (44, 16), (30, 28), (16, 16)], fill=ED_RED + (255,))
    pa = clamp((lt - 0.3) / 0.2)
    comp(c, ph, px - 30, top, pa)
    tcl = text_img(tc[3:], 22, 'mono', (255, 255, 255))
    bub = rrect(tcl.width + 8, tcl.height - 6, 8, ED_RED + (255,)); bub.alpha_composite(tcl, (4, -3))
    comp(c, bub, px - bub.width / 2, top - bub.height - 2, pa)


@effect('spotlight-type', 'spotlight darkening + a crisp Japanese word typed in left to right, one character at a time, above the head')
def fx_spotlight_type(c, e):
    class _E: pass
    e2 = _E(); e2.o = {k: v for k, v in e.o.items() if k != 'text'}; e2.o.setdefault('push', '1.03'); e2.d = e.d; e2.state = e.state.setdefault('sp', {})
    fx.fx_spotlight(c, e2)
    word = e.o.get('text', '人工知能'); W, H = c.W, c.H
    col = fx.rgb(e.o.get('color'), (255, 226, 190)); glowc = fx.rgb(e.o.get('glow'), (255, 140, 80))
    def head_top():
        m = c.m; cols = slice(max(0, int(c.fx - c.fw)), int(c.fx + c.fw)); rows = np.where((m[:, cols] > 0.5).mean(1) > 0.15)[0]
        return float(rows[0]) if len(rows) else c.fy - c.fw * 1.2
    ht = cached(e, 'ht', head_top)
    def glyphs():
        top_lim = H * 0.16; avail = ht - 60 - top_lim
        size = int(min(W * 0.82 / len(word), avail * 0.9, 230))
        f = font('jp', size); out = []; asc, desc = f.getmetrics(); pad = int(size * 0.4)
        for ch in word:
            w, h = int(f.getlength(ch)) + 2 * pad, asc + desc + 2 * pad
            m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad, pad), ch, font=f, fill=255)
            sw = max(3, size // 34)
            st = Image.new('L', (w, h), 0); ImageDraw.Draw(st).text((pad, pad), ch, font=f, fill=255, stroke_width=sw, stroke_fill=255)
            im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            im = Image.alpha_composite(im, solid_glow(st, glowc, size * 0.18, 1.3))
            im = Image.alpha_composite(im, solid_glow(st, glowc, size * 0.05, 1.6))
            edge = Image.new('RGBA', (w, h), (90, 30, 14, 255)); edge.putalpha(st); im = Image.alpha_composite(im, edge)
            body = Image.new('RGBA', (w, h), tuple(col) + (255,)); body.putalpha(m); im = Image.alpha_composite(im, body)
            out.append((im, int(f.getlength(ch)), h))
        return out, size
    gl, size = cached(e, 'gl', glyphs)
    total = sum(adv for _, adv, _ in gl); x = W / 2 - total / 2
    cy = ht - 60 - size * 0.55
    t0 = float(e.o.get('type_at', 0.2)); step = float(e.o.get('step', 0.17))
    k = clamp(c.lt / 0.3) * clamp((e.d - c.lt) / 0.2)
    for i, (im, adv, h) in enumerate(gl):
        p = (c.lt - t0 - i * step) / 0.16
        if p > 0:
            s = 1.2 - 0.2 * ease_out(p); a = clamp(p * 1.6) * k
            place(c, im, x + adv / 2, cy, s, 0, a)
        x += adv


# ---------------------------------------------------------------- spotlight-neon (11本目 draft2, premium neon / glowing-glass title)
def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

_FLICK = [0.0, 0.85, 0.1, 0.6, 0.0, 1.0, 0.45, 1.0]   # per 0.04 s while a letter switches on

def _neon_assets(c, e, word):
    W, H = c.W, c.H
    kind = e.o.get('font', 'montb')
    m = c.m; cols = slice(max(0, int(c.fx - c.fw)), int(c.fx + c.fw)); rows = np.where((m[:, cols] > 0.5).mean(1) > 0.12)[0]
    head_top = float(rows[0]) if len(rows) else c.fy - c.fw * 1.2
    top_lim = H * 0.155; bottom = head_top - float(e.o.get('gap', 70))
    size = 400
    while size > 40:
        f = font(kind, size); bb = f.getbbox(word)
        if f.getlength(word) <= W * 0.8 and (bb[3] - bb[1]) <= (bottom - top_lim): break
        size = int(size * 0.96)
    f = font(kind, size); bb = f.getbbox(word); tw = f.getlength(word); th = bb[3] - bb[1]
    x0 = W / 2 - tw / 2; y_text = bottom - th - bb[1]          # baseline-free top-left for draw
    pad = int(size * 1.8); bx0, by0 = 0, int(max(0, y_text + bb[1] - pad)); bx1, by1 = W, int(min(H, y_text + bb[3] + pad))
    BW, BH = bx1 - bx0, by1 - by0
    letters = []
    fy_ = np.arange(BH, dtype=np.float32); feather = (np.clip(fy_ / (BH * 0.18), 0, 1) * np.clip((BH - fy_) / (BH * 0.18), 0, 1))[:, None, None] ** 1.5
    white = np.float32([1.0, 0.97, 0.92]); edge_c = np.float32([1.0, 0.52, 0.30]); inner_c = np.float32([0.851, 0.467, 0.341])
    bloom1 = np.float32([1.0, 0.58, 0.34]); bloom2 = np.float32([0.85, 0.36, 0.22])
    for i, ch in enumerate(word):
        if ch == ' ': continue
        im = Image.new('L', (BW, BH), 0)
        ImageDraw.Draw(im).text((x0 + f.getlength(word[:i]) - bx0, y_text - by0), ch, font=f, fill=255)
        a = np.asarray(im, np.float32) / 255
        dist = cv2.distanceTransform((a > 0.5).astype(np.uint8), cv2.DIST_L2, 5); md = max(1.0, float(dist.max()))
        core = _smooth(dist / md, 0.32, 0.92)[..., None]
        face = (edge_c * (1 - core) + white * core)
        rim = np.clip(cv2.GaussianBlur(a, (0, 0), size * 0.018) - a, 0, 1)[..., None] * inner_c * 1.6   # thin inner/outer edge glow
        b1 = cv2.GaussianBlur(a, (0, 0), size * 0.05)[..., None] * bloom1 * 0.75
        b2 = cv2.GaussianBlur(a, (0, 0), size * 0.22)[..., None] * bloom2 * 0.75
        b3 = cv2.GaussianBlur(a, (0, 0), size * 0.6)[..., None] * bloom2 * 0.45
        ext = np.zeros_like(a); E = max(3, int(size * 0.045))
        for k in range(1, E + 1):
            M = np.float32([[1, 0, k * 0.35], [0, 1, k]]); ext = np.maximum(ext, cv2.warpAffine(a, M, (BW, BH)))
        ext = np.clip(ext - a, 0, 1)
        sh = cv2.GaussianBlur(cv2.warpAffine(a, np.float32([[1, 0, size * 0.05], [0, 1, size * 0.09]]), (BW, BH)), (0, 0), size * 0.05)
        letters.append(dict(a=a[..., None], face=face, glow=((b1 + b2 + b3 + rim) * feather * (1 - 0.9 * a[..., None])).astype(np.float32), ext=ext[..., None], sh=sh[..., None]))
    # wide light spill on the wall around the whole word
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    cy_ = (y_text + bb[1] + th / 2) - by0
    spill = np.exp(-(((xx - W / 2) / (tw * 0.75)) ** 2 + ((yy - cy_) / (th * 1.5)) ** 2))[..., None] * bloom2 * 0.32 * feather
    return dict(letters=letters, box=(bx0, by0, bx1, by1), spill=spill, size=size)

@effect('spotlight-neon', 'room goes dark, a premium neon / glowing-glass word switches on letter by letter behind you, with bloom, wall spill and depth')
def fx_spotlight_neon(c, e):
    class _E: pass
    e2 = _E(); e2.o = {k: v for k, v in e.o.items() if k not in ('text', 'font')}; e2.o.setdefault('push', '1.03'); e2.d = e.d; e2.state = e.state.setdefault('sp', {})
    fx.fx_spotlight(c, e2)
    word = e.o.get('text', 'Claude')
    A = cached(e, 'neon', lambda: _neon_assets(c, e, word))
    bx0, by0, bx1, by1 = A['box']
    img = c.img[by0:by1, bx0:bx1]; behind = (1 - c.m[by0:by1, bx0:bx1])[..., None]
    t0 = float(e.o.get('type_at', 0.35)); step = float(e.o.get('step', 0.13)); kout = clamp((e.d - c.lt) / 0.2)
    Is = []
    for i, L in enumerate(A['letters']):
        u = c.lt - t0 - i * step
        if u < 0: Is.append(0.0); continue
        j = int(u / 0.04)
        I = _FLICK[j] if j < len(_FLICK) else 0.97 + 0.03 * math.sin(c.lt * 23 + i * 1.7)
        Is.append(I * kout)
    if not any(v > 0 for v in Is) and c.lt < t0: return
    on = [i for i in range(len(A['letters'])) if c.lt >= t0 + i * step]
    meanI = sum(Is) / max(1, len(Is))
    img += A['spill'] * meanI * behind
    for i in on:
        L = A['letters'][i]; I = Is[i]
        img *= 1 - L['sh'] * 0.55 * behind                                        # soft drop shadow on the wall
        ea = L['ext'] * 0.95 * behind; ecol = np.float32([0.16, 0.07, 0.05]) + np.float32([0.5, 0.22, 0.1]) * I
        img[:] = img * (1 - ea) + ecol * ea                                        # glass depth / extrusion
        fa = L['a'] * behind
        unlit = np.float32([0.32, 0.24, 0.21])
        col = unlit * (1 - I) + L['face'] * I
        img[:] = img * (1 - fa) + col * fa
        img += L['glow'] * I * behind
    c.img[by0:by1, bx0:bx1] = np.clip(img, 0, 1.0)


# ---------------------------------------------------------------- gold-collage (11本目 draft2 scene 7; red-collage restyled in metallic gold)
G_DARK, G_HI, G_MID = (140, 106, 31), (242, 210, 122), (184, 134, 43)

def _gold_word(word, size, kind):
    f = font(kind, size); pad = int(size * 0.5)
    xs, x = [], 0.0
    for i, ch in enumerate(word): xs.append(f.getlength(word[:i]))
    tw = f.getlength(word); asc, desc = f.getmetrics(); h = asc + desc + 2 * pad
    out = []
    for i, ch in enumerate(word):
        w = int(f.getlength(ch)) + 2 * pad
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad, pad), ch, font=f, fill=255)
        st = Image.new('L', (w, h), 0); ImageDraw.Draw(st).text((pad, pad), ch, font=f, fill=255, stroke_width=max(2, size // 70), stroke_fill=255)
        a = np.asarray(m, np.float32) / 255; sa = np.asarray(st, np.float32) / 255
        bb = f.getbbox(word); top, bot = pad + bb[1], pad + bb[3]
        t = np.clip((np.arange(h, dtype=np.float32) - top) / max(1, bot - top), 0, 1)[:, None]
        # 3-stop metallic gradient: dark -> highlight (at 45%) -> mid, plus a thin bright line just under the top edge
        c0, c1, c2 = (np.float32(v) / 255 for v in (G_DARK, G_HI, G_MID))
        g = np.where(t < 0.45, c0 + (c1 - c0) * (t / 0.45)[..., None] if False else 0, 0)
        lo = (t / 0.45)[..., None]; hi = ((t - 0.45) / 0.55)[..., None]
        grad = np.where(t[..., None] < 0.45, c0 * (1 - lo) + c1 * lo, c1 * (1 - np.clip(hi, 0, 1)) + c2 * np.clip(hi, 0, 1))
        grad = np.broadcast_to(grad, (h, w, 3)).copy()
        # bevel: lighten near top-left edges, darken near bottom-right edges (from the glyph's own gradient)
        gy = cv2.Sobel(cv2.GaussianBlur(a, (0, 0), size * 0.012), cv2.CV_32F, 0, 1, ksize=3); gx = cv2.Sobel(cv2.GaussianBlur(a, (0, 0), size * 0.012), cv2.CV_32F, 1, 0, ksize=3)
        bev = np.clip(-(gx + gy) * 0.9, -0.35, 0.45)[..., None]
        grad = np.clip(grad + bev * 0.6, 0, 1)
        edge = np.clip(sa - a, 0, 1)[..., None]
        glow = (cv2.GaussianBlur(a, (0, 0), size * 0.12) * 0.75 + cv2.GaussianBlur(a, (0, 0), size * 0.035) * 0.5)[..., None]
        out.append(dict(a=a[..., None], sa=sa[..., None], grad=grad.astype(np.float32), edge=edge, glow=glow.astype(np.float32), x=xs[i] - pad, w=w, h=h))
    return out, tw, h, pad, f.getbbox(word)

@effect('gold-collage', 'black-and-white you over a deep black-brown room, a giant metallic gold word staggered in behind you with a shine sweep and bloom, kinetic lines beside you')
def fx_gold_collage(c, e):
    W, H = c.W, c.H; k = fx.ramp(c, e, 0.15, 0); al = fx.fade(c, e)
    kind = e.o.get('font', 'uib'); word = e.o.get('text', 'Claude')
    # make room above the head: slide the picture down a little
    fy0 = cached(e, 'fy0', lambda: c.fy)
    shift(c, H * float(e.o.get('drop', 0.10)) * ease_out(c.lt / 0.35))
    m = c.m[..., None]
    bw = fx.grade(c.img, 'bw')
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    base = np.float32([0.02, 0.016, 0.012]) * (1 - yy) + np.float32([0.24, 0.15, 0.08]) * yy
    room = base + bw * np.float32([0.16, 0.12, 0.08])
    c.img = c.img * (1 - k) + (bw * m + room * (1 - m)) * k
    fx.vignette(c, 0.4 * k)
    def build():
        head = c.m; cols = slice(max(0, int(c.fx - c.fw)), int(c.fx + c.fw)); rows = np.where((head[:, cols] > 0.5).mean(1) > 0.12)[0]
        ht = float(rows[0]) if len(rows) else c.fy - c.fw * 1.2
        ht += H * float(e.o.get('drop', 0.10)) * (1 - ease_out(c.lt / 0.35))  # final head position after the slide
        size = 600
        while size > 40:
            f = font(kind, size); bb = f.getbbox(word)
            if f.getlength(word) <= W * 0.94 and (bb[3] - bb[1]) <= (ht - 30 - H * 0.155): break
            size = int(size * 0.96)
        g = _gold_word(word, size, kind)
        return g, ht, size
    (glyphs, tw, gh, pad, bb), ht, size = cached(e, 'gw', build)
    x0 = W / 2 - tw / 2; ytop = ht - 30 - (bb[3]) - pad      # glyph box top so the letters' bottom sits 30px above the hair
    sweep = -0.3 + 1.6 * clamp((c.lt - 0.55) / 0.9)            # specular sweep position (0..1 across the word)
    behind = 1 - c.m
    for i, G in enumerate(glyphs):
        u = c.lt - 0.12 - i * 0.07
        if u <= 0: break
        p = ease_out(u / 0.3); s = 1.25 - 0.25 * p; a_ = clamp(u / 0.12) * al
        gx = x0 + G['x']; gw_, gh_ = G['w'], G['h']
        sw, sh_ = int(gw_ * s), int(gh_ * s); X = int(gx + gw_ / 2 - sw / 2); Y = int(ytop + gh_ / 2 - sh_ / 2 - (1 - p) * H * 0.03)
        rs = (lambda arr: arr if s < 1.001 else cv2.resize(arr, (sw, sh_), interpolation=cv2.INTER_LINEAR).reshape(sh_, sw, -1))
        A, SA, GR, ED, GL = rs(G['a']), rs(G['sa']), rs(G['grad']), rs(G['edge']), rs(G['glow'])
        hh, ww = A.shape[:2]
        xa, ya, xb, yb = max(0, X), max(0, Y), min(W, X + ww), min(H, Y + hh)
        if xb <= xa or yb <= ya: continue
        sl = (slice(ya - Y, yb - Y), slice(xa - X, xb - X)); bh = behind[ya:yb, xa:xb, None] * a_
        reg = c.img[ya:yb, xa:xb]
        # sweep highlight in word space
        xx = (np.arange(xa, xb, dtype=np.float32)[None, :] - x0 + (np.arange(ya, yb, dtype=np.float32)[:, None] - ytop) * 0.35) / max(1, tw)
        band = np.exp(-((xx - sweep) / 0.06) ** 2)[..., None]
        col = np.clip(GR[sl] + band * 0.55, 0, 1)
        reg += GL[sl] * np.float32([0.95, 0.72, 0.30]) * 0.55 * bh                       # golden bloom
        reg[:] = reg * (1 - ED[sl] * bh) + np.float32([0.30, 0.20, 0.05]) * ED[sl] * bh   # thin dark-gold outline
        reg[:] = reg * (1 - A[sl] * bh) + col * A[sl] * bh
    # kinetic lines beside you (as red-collage), gold middle line
    lines = e.o.get('lines', 'MOTION|GRAPHICS|BY CLAUDE.').split('|')
    lsz = cached(e, 'sz', lambda: lines_fit(lines, W * 0.8, 'uib', int(W * 0.13)))
    y = max(H * 0.55, c.fy + c.fw * 1.55)
    for j, ln in enumerate(lines):
        im = cached(e, ('l', j), lambda: text_img(ln, lsz, 'uib', G_HI if j == 1 else (255, 255, 255), shadow=8))
        kk = clamp((c.lt - 0.45 - 0.13 * j) / 0.16)
        if kk > 0: place(c, im, W * 0.05 + im.width / 2, y + im.height / 2, 1.4 - 0.4 * ease_out(kk), 0, kk * al, guard=True)
        y += lsz * 1.0
    tag = cached(e, 'tag', lambda: text_img(e.o.get('tag', 'REC  ·  GOLD EDITION'), W * 0.027, 'mono', G_HI))
    place(c, tag, W * 0.07 + tag.width / 2, H * 0.935, alpha=al * k, guard=True)

if __name__ == '__main__':
    fx.main()
