#!/usr/bin/env python3
"""Soát plan trước khi dựng (fx_vi.py tự gọi khi có --plan). Claude with Duy, 2026-11-25.

Người xem không biết tên hiệu ứng, họ chỉ thấy động tác lặp lại, nên luật đếm theo HỌ HÌNH ẢNH (catalog.md mục 4).
- Tự sửa (ghi lại vào plan, in ra để báo người dùng): họ "zoom vào mặt" tối đa 2 lần mỗi phút và không liền nhau;
  lần thừa thì hạ: lean-in/locked-on/headline-box -> zoom=1 (giữ chữ, máy đứng yên), spotlight -> push=1.0, slow-push -> bỏ.
- Cảnh báo (agent tự sửa): họ khác quá 2 lần mỗi phút, hai hiệu ứng liền nhau cùng họ, hiệu ứng quá ngắn/dài.
Dùng riêng: python plan_check.py plan.json
"""
import json, math, subprocess, sys

FAMILY = {
    'zoom': ['lean-in', 'slow-push', 'locked-on', 'headline-box', 'over-the-shoulder-zoom'],
    'tắt đèn': ['spotlight', 'spotlight-type', 'spotlight-neon', 'led-sign'],
    'đổi màu': ['moody', 'swipe', 'cinema', 'cinema-v1', 'red-collage', 'gold-collage', 'timeline'],
    'chữ bật lên': ['backdrop-word', 'huge-strike', 'crayon-write', 'match-cut', 'pastel-word', 'cover-star'],
    'thẻ giao diện': ['screenshot', 'todo', 'checklist', 'apple-toggles', 'the-bill', 'messages', 'comment-box', 'tap', 'glass-widgets',
                      'liquid-glass-graph', 'split-graph', 'split-graph-v1', 'tier-list', 'lineup'],
    'ảnh quanh đầu': ['noise', 'orbit', 'carousel-spin', 'fan-build', 'profile-wall', 'phone-fan', 'place-in-grid', 'headline-wall', 'check-pills'],
    'nhãn, dấu': ['tape-label', 'scribble', 'pause-point', 'reject-stamp', 'uninstall', 'reel-frame', 'shortcut-rain', 'select-resize'],
    'chuyển cảnh lớn': ['rabbit-hole', 'dot-reveal', 'split-headline', 'editor', 'broll-split', 'wave-trim'],
}
FAM_OF = {fx: fam for fam, lst in FAMILY.items() for fx in lst}
ZOOM_DEFAULT = {'lean-in': 1.45, 'slow-push': 1.6, 'locked-on': 1.35, 'headline-box': 1.3}


def _f(v, d):
    try: return float(v)
    except (TypeError, ValueError): return d


def family(e):
    """Họ hình ảnh thật của một hiệu ứng, tính cả tuỳ chọn (lean-in zoom=1 là chữ bật lên, không phải zoom)."""
    fx = e['fx']
    if fx in ZOOM_DEFAULT and _f(e.get('zoom'), ZOOM_DEFAULT[fx]) <= 1.02:
        return 'chữ bật lên' if fx == 'lean-in' else 'nhãn, dấu' if fx == 'locked-on' else FAM_OF.get(fx, fx)
    return FAM_OF.get(fx, fx)


def is_zoom(e):
    if family(e) == 'zoom': return True
    return e['fx'] == 'spotlight' and _f(e.get('push'), 1.1) > 1.02  # spotlight đẩy máy nhẹ: người xem vẫn thấy là zoom


def check(effects, duration=None):
    """Trả (plan đã sửa, các dòng đã sửa, các dòng cảnh báo). Mức cho phép tính theo độ dài video: 2 lần mỗi phút
    (họ "chữ bật lên" 3 lần, vì các con số bắt buộc dồn về đây sau khi zoom bị hạ)."""
    effs = sorted((dict(e) for e in effects), key=lambda e: float(e['start']))
    fixes, warns = [], []
    dur = duration or max((float(e['end']) for e in effs), default=60)
    budget = max(2, round(2 * dur / 60))
    used, last_zoom_end, keep = 0, -1e9, []
    for e in effs:
        t = f"{float(e['start']):.1f}s {e['fx']}"
        if is_zoom(e):
            adjacent = keep and is_zoom(keep[-1]) and float(e['start']) - last_zoom_end < 6
            if used >= budget or adjacent:
                why = f'họ zoom đã đủ {budget} lần' if used >= budget else 'liền ngay sau một lần zoom khác'
                if e['fx'] in ('lean-in', 'locked-on', 'headline-box'):
                    e['zoom'] = 1; fixes.append(f'{t}: hạ zoom=1, giữ chữ ({why})')
                elif e['fx'] == 'spotlight':
                    e['push'] = 1.0; fixes.append(f'{t}: push=1.0, không đẩy máy ({why})')
                elif e['fx'] == 'slow-push':
                    fixes.append(f'{t}: bỏ ({why})'); continue
                else:
                    warns.append(f'{t}: {why}, cân nhắc bỏ hoặc đổi hiệu ứng khác họ')
            if is_zoom(e): used += 1; last_zoom_end = float(e['end'])
        keep.append(e)
    counts = {}
    for i, e in enumerate(keep):
        fam = family(e); counts[fam] = counts.get(fam, 0) + 1
        d = float(e['end']) - float(e['start'])
        lim = 6.5 if e['fx'] == 'screenshot' else 4.5
        if d < 1.2: warns.append(f"{float(e['start']):.1f}s {e['fx']}: chỉ {d:.1f}s, ngắn quá khó thấy (1.5–4s)")
        if d > lim: warns.append(f"{float(e['start']):.1f}s {e['fx']}: dài {d:.1f}s (nên ≤ {lim:g}s)")
        if i and family(keep[i - 1]) == fam and fam != 'zoom' and not (keep[i - 1]['fx'] in ('slow-push',) or e['fx'] in ('slow-push',)):
            warns.append(f"{float(e['start']):.1f}s {e['fx']}: liền sau {keep[i - 1]['fx']} cùng họ '{fam}', người xem thấy lặp")
    for fam, n in counts.items():
        cap = max(3, round(3 * dur / 60)) if fam == 'chữ bật lên' else budget
        if fam != 'zoom' and n > cap:
            warns.append(f"họ '{fam}' dùng {n} lần (tối đa {cap}): bỏ bớt câu ít quan trọng, giữ thông tin bắt buộc")
    return keep, fixes, warns


def duration(video):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], capture_output=True, text=True)
        return float(out.stdout.strip())
    except Exception:
        return None


def run(path, video=None):
    plan = json.load(open(path, encoding='utf-8'))
    effects = plan.get('effects', plan) if isinstance(plan, dict) else plan
    fixed, fixes, warns = check(effects, duration(video) if video else None)
    if fixes:
        out = {'effects': fixed} if isinstance(plan, dict) else fixed
        json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for f in fixes: print('Soát plan, đã sửa:', f, flush=True)
    for w in warns: print('Soát plan, cảnh báo:', w, flush=True)
    if fixes or warns: print('(báo người dùng các chỗ đã sửa; cảnh báo thì sửa plan rồi chạy lại)', flush=True)
    return fixes, warns


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
