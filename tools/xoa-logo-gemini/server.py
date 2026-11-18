"""Xoá logo Gemini (http://localhost:8768): kéo-thả ảnh (hoặc video) có dấu sao Gemini/Veo, xoá bằng CLI `gwr` chạy cục bộ.

Dùng bản gwr cố định phiên bản trong package.json (@pilio/gemini-watermark-remover 1.0.46). Ảnh ~2-3s, video 20-40s.
Chỉ xoá dấu sao nhìn thấy được; gwr không thấy dấu thì giữ nguyên ảnh. Kết quả lưu ở watermark-tool/output/ (tự xoá sau 7 ngày, bản gốc tải lên trong input/ sau 1 ngày: autoclean.py).

python3 server.py
"""
import json
import os
import re
import shutil
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
CLI = HERE / "node_modules/@pilio/gemini-watermark-remover/bin/gwr.mjs"
IN = HERE / "input"
OUT = HERE / "output"
PORT = int(os.environ.get("PORT", 8768))
IMG = {".png", ".jpg", ".jpeg", ".webp"}
VID = {".mp4", ".mov", ".webm", ".m4v"}
CTYPE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".m4v": "video/mp4"}
SKIP = {"no-watermark-detected": "không thấy logo Gemini, ảnh giữ nguyên"}


def node() -> str | None:
    return shutil.which("node") or next((p for p in ("/opt/homebrew/bin/node", "/usr/local/bin/node") if Path(p).exists()), None)


def safe_name(name: str) -> str:
    stem, ext = os.path.splitext(Path(name).name)
    stem = re.sub(r"[^\w.\- ]+", "_", stem, flags=re.UNICODE).strip() or "file"
    return stem[:80] + ext.lower()


def check(name: str) -> tuple[str, str]:
    """Tên file an toàn + đường dẫn node; báo lỗi trước khi nhận file tải lên."""
    name = safe_name(name)
    ext = Path(name).suffix
    if ext not in IMG | VID:
        raise ValueError(f"không hỗ trợ đuôi {ext or '(trống)'}: chỉ nhận ảnh png/jpg/webp hoặc video mp4/mov/webm")
    exe = node()
    if not exe or not CLI.exists():
        raise ValueError("chưa cài gwr: chạy `npm install --ignore-scripts` trong thư mục này")
    return name, exe


def bitrate_args(src: Path) -> list[str]:
    """gwr mặc định xuất video 12 Mbps bất kể nguồn. Nguồn cao hơn thì xin bitrate bằng nguồn + 25% để không tụt chất lượng."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=bit_rate:format=bit_rate",
                            "-of", "json", str(src)], capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout)
        bps = int((j.get("streams") or [{}])[0].get("bit_rate") or j.get("format", {}).get("bit_rate") or 0)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    mbps = min(80, round(bps * 1.25 / 1e6, 1))
    return ["--video-bitrate-mbps", str(mbps)] if mbps > 12 else []


def remove(name: str, exe: str, src: Path) -> dict:
    ext = Path(name).suffix
    stem = Path(name).stem
    dst = OUT / f"{stem}_clean{ext}"
    i = 2
    while dst.exists():
        dst = OUT / f"{stem}_clean{i}{ext}"
        i += 1
    OUT.mkdir(exist_ok=True)
    r = subprocess.run([exe, str(CLI), "remove", str(src), "--output", str(dst), "--overwrite", "--json",
                        *(bitrate_args(src) if ext in VID else [])],
                       capture_output=True, text=True, timeout=900 if ext in VID else 120)
    if r.returncode:
        dst.unlink(missing_ok=True)
        raise ValueError("gwr lỗi: " + ((r.stderr or r.stdout).strip().splitlines() or ["không rõ"])[-1][:200])
    try:
        meta = json.loads(r.stdout.strip().splitlines()[-1]).get("meta") or {}
    except (ValueError, IndexError):
        meta = {}
    applied = meta.get("applied", ext in VID)
    reason = meta.get("skipReason")
    if not applied and not dst.exists():
        shutil.copyfile(src, dst)
    return {"name": name, "out": dst.name, "src": src.name, "applied": bool(applied),
            "note": "" if applied else SKIP.get(reason, reason or "gwr không xoá gì")}


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

    def file(self, folder: Path, name: str, download=False):
        p = (folder / unquote(name)).resolve()
        if p.parent != folder.resolve() or not p.is_file():
            return self.send(404, {"error": "không thấy file"})
        size = p.stat().st_size
        start, end = 0, size - 1
        rng = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range") or "")
        if rng and (rng[1] or rng[2]) and size:   # video cần Range để tua (Safari bắt buộc)
            start = int(rng[1]) if rng[1] else max(0, size - int(rng[2]))
            end = min(int(rng[2]), size - 1) if rng[1] and rng[2] else size - 1
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                return self.end_headers()
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", CTYPE.get(p.suffix.lower(), "application/octet-stream"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(end - start + 1))
        if download:
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(p.name)}")
        self.end_headers()
        with p.open("rb") as f:   # đọc từng khúc: video vài trăm MB không nằm trong RAM
            f.seek(start)
            left = end - start + 1
            while left > 0 and (chunk := f.read(min(1 << 20, left))):
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                left -= len(chunk)

    def do_GET(self):
        if not localguard.ok(self):
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path.startswith("/out/"):
            return self.file(OUT, u.path[5:], "dl" in q)
        if u.path.startswith("/in/"):
            return self.file(IN, u.path[4:])
        if u.path == "/api/health":
            return self.send(200, {"ok": True, "gwr": CLI.exists() and bool(node())})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if not localguard.ok(self):
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/api/remove":
                n = int(self.headers.get("Content-Length") or 0)
                if not n or n > 500 * 1024 * 1024:
                    raise ValueError("file rỗng hoặc quá 500MB")
                name, exe = check(q.get("name", ["file.png"])[0])
                IN.mkdir(exist_ok=True)
                src = IN / f"{time.strftime('%Y%m%d-%H%M%S')}_{name}"
                with src.open("wb") as f:   # ghi thẳng ra đĩa, không giữ cả file trong RAM
                    left = n
                    while left:
                        chunk = self.rfile.read(min(left, 1 << 20))
                        if not chunk:
                            src.unlink(missing_ok=True)
                            raise ValueError("tải lên bị ngắt giữa chừng")
                        f.write(chunk)
                        left -= len(chunk)
                return self.send(200, remove(name, exe, src))
            if u.path == "/api/reveal":
                reveal(OUT if OUT.exists() else HERE)
                return self.send(200, {"ok": True})
            self.send(404, {"error": "not found"})
        except subprocess.TimeoutExpired:
            self.send(500, {"error": "gwr chạy quá lâu, đã dừng"})
        except Exception as e:  # noqa: BLE001
            self.send(400, {"error": str(e)})


if __name__ == "__main__":
    print(f"Xoá logo Gemini: http://localhost:{PORT}")
    autoclean.start({IN: 1, OUT: autoclean.KEEP_DAYS})
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
