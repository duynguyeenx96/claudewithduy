#!/usr/bin/env python3
"""Chạy claude-video-effects (MIT) với chữ TIẾNG VIỆT đủ dấu. Viết theo cách của fx_jp.py (motion-studio-15).

Các phông gốc Archivo Black (bold), Instrument Serif (serif), Permanent Marker (hand) KHÔNG có dấu tiếng Việt.
Khi chữ có dấu, file này tự đổi sang phông tương đương có dấu (chữ tiếng Anh giữ nguyên phông gốc):
  bold  -> SVN-Gilroy Black     serif -> Playfair Display Italic     hand -> TF Whispers
Phông lấy từ thư viện của người dùng (biến FONT_LIB, mặc định D:\\EDIT VIDEO CLAUDE\\TU-LIEU\\FONT); thiếu thì dùng Montserrat kèm skill.
Cũng nạp các hiệu ứng thêm trong custom/fx_custom.py (cinema, split-graph, editor, spotlight-neon, gold-collage ...),
và cho các hiệu ứng đó vẽ chữ bằng phông có dấu thay cho phông tiếng Nhật.

Dùng y như scripts/fx.py (python là .venv\\Scripts\\python.exe):
  python custom/fx_vi.py backdrop-word in.mp4 out.mp4 --start 1 --end 3.5 --text "ĐẠO"
  python custom/fx_vi.py --plan plan.json in.mp4 out.mp4
  python custom/fx_vi.py red-collage in.mp4 check.png --start 0 --end 3 --text "BUÔNG" --still 1.5
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, HERE)
from PIL import ImageDraw, ImageFont  # noqa: E402

# phông có dấu lấy từ thư mục fonts/ của gói (FONT_LIB để đổi thư mục)
LIB = os.environ.get('FONT_LIB', os.path.join(ROOT, 'fonts'))
_FALLBACK = os.path.join(ROOT, 'fonts', 'Montserrat.ttf')


def _pick(*cands):
    return next((p for p in cands if p and os.path.exists(p)), _FALLBACK)


VN_BOLD = _pick(os.path.join(LIB, 'BeVietnamPro-Black.ttf'))
VN_SERIF = _pick(os.path.join(ROOT, 'fonts', 'PlayfairDisplay-Italic.ttf'))
VN_HAND = _pick(os.path.join(LIB, 'DancingScript.ttf'), VN_BOLD)
# phông gốc thiếu dấu -> phông thay thế
_SUB = {'ArchivoBlack-Regular.ttf': VN_BOLD, 'InstrumentSerif-Italic.ttf': VN_SERIF,
        'PermanentMarker-Regular.ttf': VN_HAND}
_cache = {}


def _has_vn(s):
    # chữ Latin có dấu (Latin-1 Supplement tới Latin Extended Additional): đủ để nhận ra tiếng Việt
    try: return any(0xC0 <= ord(ch) <= 0x1EFF for ch in str(s))
    except Exception: return False


def _vn_like(f):
    p = getattr(f, 'path', None)
    if not p or not hasattr(f, 'size'): return f
    sub = _SUB.get(os.path.basename(str(p)))
    if not sub: return f
    k = (sub, int(f.size))
    if k not in _cache: _cache[k] = ImageFont.truetype(sub, int(f.size))
    return _cache[k]


_orig_text = ImageDraw.ImageDraw.text
def _vn_text(self, xy, text, fill=None, font=None, *a, **k):
    if font is not None and _has_vn(text): font = _vn_like(font)
    return _orig_text(self, xy, text, fill, font, *a, **k)
ImageDraw.ImageDraw.text = _vn_text
for _m in ('getbbox', 'getlength', 'getmask2', 'getmask'):
    _o = getattr(ImageFont.FreeTypeFont, _m)
    def _w(self, text, *a, _o=_o, **k):
        if _has_vn(text):
            g = _vn_like(self)
            if g is not self: return _o(g, text, *a, **k)
        return _o(self, text, *a, **k)
    setattr(ImageFont.FreeTypeFont, _m, _w)

import fx  # noqa: E402
try:
    import fx_custom  # noqa: E402,F401  (đăng ký hiệu ứng thêm của motion-studio-15)
    fx.FONT['jp'] = VN_BOLD  # các hiệu ứng thêm vốn dùng phông tiếng Nhật -> dùng phông có dấu tiếng Việt
except Exception as e:  # thiếu file vẫn chạy được 51 hiệu ứng gốc
    print(f'(bỏ qua fx_custom: {e})', file=sys.stderr)
try:
    import fx_image  # noqa: E402,F401  (screenshot: ảnh người dùng đưa, tuỳ chọn)
except Exception as e:
    print(f'(bỏ qua fx_image: {e})', file=sys.stderr)

# Gói tách nhỏ (fx-pack-N-0M): pack.json ở gốc skill giới hạn các hiệu ứng có trong gói.
_PACK = os.path.join(ROOT, 'pack.json')
if os.path.exists(_PACK):
    import json
    _p = json.load(open(_PACK, encoding='utf-8'))
    _keep = set(_p['effects']) | set(_p.get('bonus', []))  # bonus: chuyển động máy kèm theo mọi gói
    _where = _p.get('others', {})  # tên hiệu ứng -> gói chứa nó
    for _k in list(fx.EFFECTS):
        if _k not in _keep: del fx.EFFECTS[_k]
    _main = fx.main
    def _pack_main():
        try: _main()
        except SystemExit as e:
            m = str(e.code or '')
            if m.startswith('Unknown effect'):
                n = m.split("'")[1]
                hint = f" Hiệu ứng này nằm trong gói {_where[n]}." if n in _where else ''
                sys.exit(f"Gói {_p['name']} không có hiệu ứng '{n}'.{hint} Chạy --list để xem {len(fx.EFFECTS)} hiệu ứng của gói này.")
            raise
    fx.main = _pack_main

if __name__ == '__main__':
    if '--plan' in sys.argv:  # soát luật họ hình ảnh, tự hạ zoom thừa (custom/plan_check.py)
        import plan_check
        _i = sys.argv.index('--plan'); _pos = [x for j, x in enumerate(sys.argv[1:], 1) if not x.startswith('--') and j != _i + 1 and not sys.argv[j - 1] in ('--still', '--width', '--start', '--end', '--text', '--images', '--opt')]
        plan_check.run(sys.argv[_i + 1], _pos[0] if _pos else None)
    fx.main()
