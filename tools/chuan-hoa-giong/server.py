"""Chuẩn hoá giọng (http://localhost:8769): kéo-thả clip nói bị bé, nâng về -16 LUFS mà không vỡ tiếng.

Kéo thanh âm lượng chỉ nhân cả đoạn lên: đỉnh nhọn chạm trần và vỡ trong khi giọng vẫn bé. Ở đây ffmpeg loudnorm đo 2 lượt,
ghìm đỉnh (true peak -1.5 dB) rồi mới nâng. Hình giữ nguyên (-c:v copy), chỉ tiếng được mã hoá lại (AAC 256k).
Kết quả ở loudness-tool/output/ (tự xoá sau 7 ngày), bản nghe thử (chỉ tiếng) ở loudness-tool/preview/ (1 ngày): autoclean.py.

python3 server.py
"""
import json
import os
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import autoclean  # noqa: E402
import localguard  # noqa: E402

def reveal(path):
    """Mở thư mục kết quả bằng trình quản lý file của hệ điều hành."""
    p = str(path)
    if sys.platform == "darwin":
        subprocess.run(["open", p])
    elif os.name == "nt":
        os.startfile(p)  # noqa: S606
    else:
        subprocess.run(["xdg-open", p])


HERE = Path(__file__).resolve().parent
IN, OUT, PRE = HERE / "input", HERE / "output", HERE / "preview"
PORT = int(os.environ.get("PORT", 8769))
VID = {".mp4", ".mov", ".m4v"}
AUD = {".wav", ".m4a", ".mp3", ".aac"}
TARGETS = {-14.0, -16.0}
# khử ồn nền trước khi nâng: cắt ù dưới 80 Hz + afftdn tự bám mức ồn (tn=1). Không EQ / nén: giữ nguyên chất giọng.
CLEAN = "highpass=f=80,afftdn=nr=10:nf=-30:tn=1,"
MAX = 8 * 1024 ** 3


def safe_name(name: str) -> str:
    stem, ext = os.path.splitext(Path(name).name)
    stem = re.sub(r"[^\w.\- ]+", "_", stem, flags=re.UNICODE).strip() or "file"
    return stem[:80] + ext.lower()


def ff(*args, timeout=1800) -> str:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin", *args], capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise ValueError("ffmpeg lỗi: " + (r.stderr.strip().splitlines() or ["không rõ"])[-1][:200])
    return r.stderr


def meter(path: Path) -> dict:
    """Độ to trung bình (LUFS), đỉnh thật (dBFS) và số mẫu chạm trần (vỡ tiếng) của file."""
    err = ff("-i", str(path), "-vn", "-af", "ebur128=peak=true:framelog=quiet,astats=metadata=0:measure_perchannel=0", "-f", "null", "-")
    i = re.findall(r"\bI:\s+(-?[0-9.]+) LUFS", err)
    tp = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", err)
    flat = re.findall(r"Flat factor:\s+([0-9.]+)", err)
    return {"lufs": float(i[-1]) if i else None, "peak": float(tp[-1]) if tp else None, "flat": float(flat[-1]) if flat else 0.0}


def normalize(name: str, src: Path, target: float, clean: bool = False) -> dict:
    ext = src.suffix
    stem = Path(name).stem
    out_ext = ext if ext in VID else ".m4a"
    dst = OUT / f"{stem}_chuan{out_ext}"
    k = 2
    while dst.exists():
        dst = OUT / f"{stem}_chuan{k}{out_ext}"
        k += 1
    for d in (OUT, PRE):
        d.mkdir(exist_ok=True)
    before = meter(src)
    if before["lufs"] is None or before["lufs"] < -65:
        raise ValueError("file không có tiếng (hoặc gần như im lặng), không có gì để chuẩn hoá")
    base = (CLEAN if clean else "") + f"loudnorm=I={target}:TP=-1.5:LRA=11"
    err = ff("-i", str(src), "-vn", "-af", base + ":print_format=json", "-f", "null", "-")
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    flt = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    video = ["-map", "0:v:0?", "-c:v", "copy"] if ext in VID else ["-vn"]
    ff("-y", "-i", str(src), "-map", "0:a:0", *video, "-af", flt, "-ar", "48000", "-c:a", "aac", "-b:a", "256k",
       "-map_metadata", "0", "-movflags", "+faststart", str(dst))
    after = meter(dst)
    pa, pb = PRE / f"{dst.stem}_goc.m4a", PRE / f"{dst.stem}_sau.m4a"
    ff("-y", "-i", str(src), "-vn", "-map", "0:a:0", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", str(pa))
    ff("-y", "-i", str(dst), "-vn", "-map", "0:a:0", "-c:a", "copy", str(pb))
    notes = []
    gain = target - before["lufs"]
    if before["flat"] > 0 or (before["peak"] is not None and before["peak"] >= -0.1):
        notes.append("File gốc đã vỡ tiếng sẵn (đỉnh chạm trần). Chuẩn hoá không chữa được phần đã vỡ: hãy dùng file thu gốc, chưa kéo âm lượng.")
    if before["lufs"] < -35:
        notes.append(f"Gốc rất bé ({before['lufs']:.1f} LUFS), nâng {gain:.0f} dB nên tiếng nền (quạt, phòng) cũng to lên theo. Lần sau để mic gần miệng hơn.")
    if clean:
        notes.append("Đã khử ồn nền. Nghe thử bản sau: giọng bị đục hoặc méo thì chạy lại, bỏ chọn khử ồn.")
    if before["lufs"] >= -35 and abs(gain) < 1:
        notes.append("Gốc đã gần đúng mức, gần như không đổi.")
    if after["lufs"] is not None and abs(after["lufs"] - target) > 1.5:
        notes.append(f"Chưa tới đích: ra {after['lufs']:.1f} LUFS thay vì {target:.0f}. Thường do đoạn nói quá ngắn hoặc nhiều khoảng lặng.")
    return {"name": name, "out": dst.name, "goc": pa.name, "sau": pb.name, "target": target, "clean": clean, "gain": round(gain, 1),
            "before": before, "after": after, "clipped": after["flat"] > 0, "notes": notes}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code=200, body=b"", ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def file(self, folder: Path, name: str, ctype: str, download=False):
        p = (folder / unquote(name)).resolve()
        if p.parent != folder.resolve() or not p.is_file():
            return self.send(404, {"error": "không thấy file"})
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(p.stat().st_size))
        if download:
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(p.name)}")
        self.end_headers()
        with p.open("rb") as f:
            while chunk := f.read(1 << 20):
                self.wfile.write(chunk)

    def do_GET(self):
        if not localguard.ok(self):
            return
        u = urlparse(self.path)
        if u.path == "/":
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path.startswith("/out/"):
            return self.file(OUT, u.path[5:], "application/octet-stream", True)
        if u.path.startswith("/pre/"):
            return self.file(PRE, u.path[5:], "audio/mp4")
        if u.path == "/api/health":
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if not localguard.ok(self):
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        src = None
        try:
            if u.path == "/api/normalize":
                n = int(self.headers.get("Content-Length") or 0)
                if not n or n > MAX:
                    raise ValueError("file rỗng hoặc quá 8GB")
                name = safe_name(q.get("name", ["clip.mp4"])[0])
                if Path(name).suffix not in VID | AUD:
                    raise ValueError(f"không hỗ trợ đuôi {Path(name).suffix or '(trống)'}: nhận mp4, mov, m4v, wav, m4a, mp3")
                target = float(q.get("target", ["-16"])[0])
                if target not in TARGETS:
                    raise ValueError("mức đích chỉ nhận -16 hoặc -14")
                IN.mkdir(exist_ok=True)
                src = IN / f"{time.strftime('%Y%m%d-%H%M%S')}_{name}"
                with src.open("wb") as f:   # ghi thẳng ra đĩa: clip 4K vài GB không nằm trong RAM
                    left = n
                    while left:
                        chunk = self.rfile.read(min(left, 1 << 20))
                        if not chunk:
                            raise ValueError("tải lên bị ngắt giữa chừng")
                        f.write(chunk)
                        left -= len(chunk)
                return self.send(200, normalize(name, src, target, q.get("clean", ["0"])[0] == "1"))
            if u.path == "/api/reveal":
                OUT.mkdir(exist_ok=True)
                reveal(OUT)
                return self.send(200, {"ok": True})
            self.send(404, {"error": "not found"})
        except subprocess.TimeoutExpired:
            self.send(500, {"error": "ffmpeg chạy quá lâu, đã dừng"})
        except Exception as e:  # noqa: BLE001
            self.send(400, {"error": str(e)})
        finally:
            if src is not None:
                src.unlink(missing_ok=True)   # bản tải lên chỉ là bản sao, file gốc của người dùng vẫn nguyên


if __name__ == "__main__":
    print(f"Chuẩn hoá giọng: http://localhost:{PORT}")
    autoclean.start({IN: 1, PRE: 1, OUT: autoclean.KEEP_DAYS})
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
