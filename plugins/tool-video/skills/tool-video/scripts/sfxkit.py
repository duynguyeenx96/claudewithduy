"""Đặt SFX từ bộ âm CC0 của skill (assets/sfx/kit.json, nguồn ở assets/sfx/LICENSES.md) cho mọi build.py của tool-video.

    import os, sys; sys.path.insert(0, os.path.join(os.environ["TOOL_VIDEO_SK"], "scripts"))
    from sfxkit import sfx_tags
    tags = sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(32, 60), log=WORK / "sfx_cues.json")
    if tags is None: ...khối âm cũ của bản mẫu (không đọc được kit.json)

Cue = (vai, mốc hình[, số bản]). Mốc hình là lúc sự việc xảy ra trên màn hình, không phải lúc âm bắt đầu:
  anchor start: âm bắt đầu đúng mốc (pop, click, ding, chat, error)
  anchor peak : điểm to nhất rơi đúng mốc (whoosh, impact, slice, rip), âm phát sớm hơn peak_t
  anchor end  : âm kết đúng mốc (riser)
Không ghi số bản thì xoay vòng các bản của vai (một file không lặp liên tiếp). Mức to = vol của vai × gain.
"""
import json
import os
from pathlib import Path

SFXDIR = Path(os.environ.get("TOOL_VIDEO_SFX") or Path(__file__).resolve().parents[1] / "assets" / "sfx")   # TOOL_VIDEO_SFX: bộ âm riêng cùng định dạng
# tên cue cũ / vai chưa có trong kit -> vai gần nhất
ALIAS = {"wrong": "error", "digits": "typing", "typing": "tick", "chat": "pop", "paper": "whoosh", "rip": "whoosh", "slice": "whoosh",
         "shutter": "click", "cash": "ding", "magic": "ding", "ding": "pop", "glitch": "whoosh", "error": "click", "tick": "click"}


def load_kit():
    f = SFXDIR / "kit.json"
    return json.loads(f.read_text()) if f.exists() else None


def sfx_tags(sfx, pub, duration, gain=0.85, tracks=range(200, 260), log=None, vol=None):
    """Trả về list thẻ <audio> (None nếu không có kit.json). vol: {vai: hệ số} ghi đè mức của kit cho riêng video này."""
    kit = load_kit()
    if kit is None:
        return None
    out = Path(pub) / "sfx"
    out.mkdir(exist_ok=True)
    tags, rows, last, turn = [], [], {}, {}
    for n, cue in enumerate(sorted(sfx, key=lambda e: e[1])):
        role, t = cue[0], cue[1]
        seen = set()
        while role not in kit and role in ALIAS and role not in seen:
            seen.add(role)
            role = ALIAS[role]
        if role not in kit:
            continue
        r = kit[role]
        if len(cue) > 2:
            f = r["files"][cue[2] % len(r["files"])]
        else:
            f = r["files"][turn.get(role, 0) % len(r["files"])]
            turn[role] = turn.get(role, 0) + 1
        src = SFXDIR / f["file"]
        dst = out / src.name
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
        start = max(0.0, t - {"peak": f["peak_t"], "end": f["dur"]}.get(r["anchor"], 0))
        d = min(f["dur"] + 0.05, duration - start)
        if d <= 0.05:
            continue
        tr = next(k for k in tracks if last.get(k, -1) <= start)
        last[tr] = start + d
        v = (vol or {}).get(cue[0], r["vol"]) * gain
        rows.append({"t": round(t, 3), "start": round(start, 3), "role": cue[0], "file": src.name, "title": f.get("title", ""), "vol": round(v, 3)})
        tags.append(f'<audio id="sfx{n:02d}" src="sfx/{src.name}" data-start="{start:.3f}" data-duration="{d:.3f}" '
                    f'data-track-index="{tr}" data-volume="{v:.3f}"></audio>')
    if log:
        Path(log).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    return tags
