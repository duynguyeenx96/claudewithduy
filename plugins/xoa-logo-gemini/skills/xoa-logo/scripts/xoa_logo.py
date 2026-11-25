#!/usr/bin/env python3
"""Xoá dấu sao Gemini/Veo trên ảnh và video bằng gwr (@pilio/gemini-watermark-remover 1.0.46), chạy cục bộ.

  xoa_logo.py <file|thư-mục>… [--out <thư-mục>] [--deps <thư mục gwr>]
  xoa_logo.py sao-nho <file gốc> <file _sach>      (video Veo) xoá thêm dấu sao nhỏ nhấp nháy, ghi đè file _sach

Kết quả: <tên>_sach<đuôi> cạnh file gốc (hoặc trong --out). Không ghi đè file gốc, không ghi đè kết quả cũ.
gwr không thấy dấu sao thì giữ nguyên, báo "không thấy logo".
Ảnh: png jpg jpeg webp. Video: mp4 mov webm m4v.
Video Veo/Flow còn một dấu sao nhỏ nhấp nháy cạnh dấu lớn mà gwr không xoá. Sau mỗi video, script in đường dẫn ảnh
xem nhanh góc logo (5 mốc). Còn dấu nhỏ và góc là nền trơn thì chạy 'sao-nho': tìm chỗ dấu lớn vừa bị xoá (so khung
trước/sau), suy ra ô dấu nhỏ, xoá bằng delogo của ffmpeg. Góc có cạnh/vật đi qua thì delogo để lại vết nhoè: đừng dùng.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMG = {".png", ".jpg", ".jpeg", ".webp"}
VID = {".mp4", ".mov", ".webm", ".m4v"}
SKIP = {"no-watermark-detected": "không thấy logo Gemini, giữ nguyên"}


def die(msg):
    sys.exit("Lỗi: " + msg)


def deps_dir(arg):
    if arg:
        return Path(arg).expanduser()
    d = os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(d) / "deps" if d else HERE.parent / ".deps"


def bitrate_args(src):
    """gwr mặc định xuất video 12 Mbps. Nguồn cao hơn thì xin bằng nguồn + 25% để không tụt chất lượng."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=bit_rate:format=bit_rate",
                            "-of", "json", str(src)], capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout)
        bps = int((j.get("streams") or [{}])[0].get("bit_rate") or j.get("format", {}).get("bit_rate") or 0)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    mbps = min(80, round(bps * 1.25 / 1e6, 1))
    return ["--video-bitrate-mbps", str(mbps)] if mbps > 12 else []


CORNER = "crop=iw*0.35:ih*0.25:iw*0.65:ih*0.75"


def logo_box(src, dst):
    """Ô dấu sao lớn gwr đã xoá: lấy trung bình độ chênh trước/sau qua nhiều khung ở góc dưới phải (logo đứng yên nổi lên,
    nhiễu nén chìm xuống) rồi lấy khung bao. Trả (x, y, cạnh) theo toạ độ video, hoặc None."""
    import re
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(src), "-i", str(dst), "-filter_complex",
                        f"[0:v]{CORNER},format=gray[a];[1:v]{CORNER},format=gray[b];[a][b]blend=all_mode=difference,"
                        "tmix=frames=120,lut=y='if(gt(val,10),255,0)',bbox=min_val=200", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=300)
    boxes = re.findall(r"x1:(\d+) x2:(\d+) y1:(\d+) y2:(\d+)", r.stderr)
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                        str(src)], capture_output=True, text=True).stdout.strip().split(",")
    if not boxes or len(p) < 2:
        return None
    x1, x2, y1, y2 = map(int, boxes[-1])
    w, h = int(p[0]), int(p[1])
    side = max(x2 - x1, y2 - y1) + 1
    if not (12 <= side <= min(w, h) * 0.2) or abs((x2 - x1) - (y2 - y1)) > side * 0.35:
        return None  # không giống một dấu sao vuông: không đoán
    return int(w * 0.65) + x1, int(h * 0.75) + y1, side, w, h


def remove_small_star(src, dst):
    """Xoá dấu sao nhỏ nhấp nháy đi kèm logo Veo (lệch chéo xuống phải so với dấu lớn)."""
    b = logo_box(src, dst)
    if not b:
        return "không định vị được dấu sao lớn, bỏ qua bước dấu sao nhỏ"
    x, y, s, w, h = b
    cx, cy = x + s / 2 + 0.62 * s, y + s / 2 + 0.73 * s
    bw = round(1.35 * s)
    bx, by = max(1, round(cx - bw / 2)), max(1, round(cy - bw / 2))
    bw = min(bw, w - bx - 1, h - by - 1)
    if bw < 8:
        return "dấu sao nhỏ sát mép khung, bỏ qua"
    tmp = dst.with_name(dst.stem + ".tmp" + dst.suffix)
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(dst), "-vf", f"delogo=x={bx}:y={by}:w={bw}:h={bw}",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", str(tmp)], capture_output=True, text=True, timeout=900)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        return "xoá dấu sao nhỏ lỗi, giữ bản của gwr"
    tmp.replace(dst)
    return ""


def corner_preview(src, dst):
    """Ảnh xem nhanh góc logo: hàng trên bản gốc, hàng dưới bản đã xoá, 5 mốc thời gian. Lưu ở thư mục tạm."""
    import tempfile
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dst)],
                                   capture_output=True, text=True).stdout)
    except ValueError:
        return None
    out = Path(tempfile.gettempdir()) / f"xoa-logo-goc-{dst.stem}.jpg"
    times = [dur * k / 6 for k in range(1, 6)]
    ins, chains = [], []
    for row, f in enumerate((src, dst)):
        for k, t in enumerate(times):
            ins += ["-ss", f"{t:.2f}", "-i", str(f)]
            chains.append(f"[{row * 5 + k}:v]trim=end_frame=1,crop=iw*0.3:ih*0.18:iw*0.7:ih*0.82,scale=240:-2[v{row}{k}]")
    fc = ";".join(chains) + ";" + "".join(f"[v0{k}]" for k in range(5)) + "hstack=5[r0];" + \
        "".join(f"[v1{k}]" for k in range(5)) + "hstack=5[r1];[r0][r1]vstack[o]"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[o]", "-frames:v", "1", str(out)],
                       capture_output=True, text=True)
    return out if r.returncode == 0 and out.exists() else None


def target(src, out_dir):
    d = out_dir or src.parent
    dst = d / f"{src.stem}_sach{src.suffix.lower()}"
    i = 2
    while dst.exists():
        dst = d / f"{src.stem}_sach{i}{src.suffix.lower()}"
        i += 1
    return dst


def remove(src, out_dir, node, gwr):
    is_vid = src.suffix.lower() in VID
    dst = target(src, out_dir)
    t0 = time.time()
    r = subprocess.run([node, str(gwr), "remove", str(src), "--output", str(dst), "--overwrite", "--json",
                        *(bitrate_args(src) if is_vid else [])],
                       capture_output=True, text=True, timeout=900 if is_vid else 120)
    if r.returncode:
        dst.unlink(missing_ok=True)
        return False, f"✗ {src.name}: gwr lỗi: " + ((r.stderr or r.stdout).strip().splitlines() or ["không rõ"])[-1][:200]
    try:
        meta = json.loads(r.stdout.strip().splitlines()[-1]).get("meta") or {}
    except (ValueError, IndexError):
        meta = {}
    applied = meta.get("applied", is_vid)
    if not applied:
        dst.unlink(missing_ok=True)
        return True, f"– {src.name}: {SKIP.get(meta.get('skipReason'), meta.get('skipReason') or 'gwr không xoá gì')}"
    msg = f"✓ {src.name} → {dst} ({time.time() - t0:.1f}s)"
    if is_vid:
        pv = corner_preview(src, dst)
        if pv:
            msg += f"\n  xem góc logo (trên: gốc, dưới: đã xoá): {pv}"
    return True, msg


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    out_dir = deps = None
    if "--out" in a:
        i = a.index("--out")
        out_dir = Path(a[i + 1]).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        del a[i:i + 2]
    if "--deps" in a:
        i = a.index("--deps")
        deps = a[i + 1]
        del a[i:i + 2]
    if a and a[0] == "sao-nho":
        if len(a) < 3:
            die("sao-nho <file gốc> <file _sach>")
        src, dst = (Path(x.strip().strip("'\"")).expanduser().resolve() for x in a[1:3])
        note = remove_small_star(src, dst)
        if note:
            die(note)
        pv = corner_preview(src, dst)
        print(f"✓ đã xoá dấu sao nhỏ: {dst}" + (f"\n  xem góc logo (trên: gốc, dưới: đã xoá): {pv}" if pv else ""))
        return
    gwr = deps_dir(deps) / "node_modules/@pilio/gemini-watermark-remover/bin/gwr.mjs"
    node = shutil.which("node")
    if not node or not gwr.exists():
        die(f"chưa cài gwr: chạy 'bash {HERE / 'setup.sh'}' trước")
    files = []
    for x in a:
        p = Path(x.strip().strip("'\"").replace("\\ ", " ")).expanduser()
        if p.is_dir():
            files += sorted(q for q in p.iterdir() if q.suffix.lower() in IMG | VID and "_sach" not in q.stem)
        elif p.is_file():
            files.append(p)
        else:
            print(f"✗ không thấy file: {p}")
    files = [f for f in files if f.suffix.lower() in IMG | VID or print(f"✗ {f.name}: không hỗ trợ đuôi {f.suffix or '(trống)'}")]
    if not files:
        die("không có ảnh/video nào để xử lý (png jpg webp, mp4 mov webm m4v)")
    ok = done = 0
    for f in files:
        print(f"đang xử lý {f.name} ({'video' if f.suffix.lower() in VID else 'ảnh'})…", flush=True)
        good, msg = remove(f.resolve(), out_dir, node, gwr)
        print(msg, flush=True)
        ok += good
        done += msg.startswith("✓")
    print(f"xong: {done} file đã xoá logo, {ok - done} file không có logo, {len(files) - ok} lỗi")


if __name__ == "__main__":
    main()
