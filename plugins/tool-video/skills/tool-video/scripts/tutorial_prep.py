#!/usr/bin/env python3
"""Chuẩn bị footage cho concept `tutorial`: mặt cắt vuông + quay màn hình cùng một timeline.

    python3 tutorial_prep.py --face a-roll.mp4 --screen screen.mov -o public/
        [--keep keep.json] [--offset auto|<giây>] [--crop cx,cy,size] [--no-bg]

--offset   giờ màn hình = giờ A-roll + offset. `auto` dò bằng tiếng của 2 file (cần cả 2 có tiếng),
           không đủ tiếng / độ tin cậy thấp thì dừng và yêu cầu nhập tay. Mặc định 0.
--keep     file JSON [[start,end],...] theo giờ A-roll gốc: cắt CẢ HAI video bằng cùng các đoạn này.
--crop     ô vuông trên A-roll gốc (tâm x, tâm y, cạnh, px). Không truyền thì dò mặt.

Ra: face.mp4 (vuông, có tiếng), screen.mp4 (giữ tỉ lệ gốc, tối đa rộng 2160), bg.mp4 (nền mờ độ phân giải thấp, chung timeline),
tutorial.json (kích thước + offset + crop, build.py đọc). Mỗi file chỉ encode một lần từ bản gốc, crf 12.
"""
import argparse
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ENC = ["-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p"]
FACE_OUT = 760          # cạnh file face.mp4: khung hiện ~380px, giữ gấp 2 cho nét
FPS = 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"lỗi: {' '.join(map(str, cmd))[:300]}\n{r.stderr[-800:]}")
    return r.stdout


def probe(path):
    out = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)]))
    v = next(s for s in out["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = int(next((d.get("rotation", 0) for d in v.get("side_data_list", []) if "rotation" in d), 0))
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"w": w, "h": h, "dur": float(out["format"]["duration"]),
            "audio": any(s["codec_type"] == "audio" for s in out["streams"]),
            "transfer": v.get("color_transfer", "")}


def detect_face(path, dur):
    """Haar cascade trên ~24 khung, lấy trung vị; nới cạnh theo độ xê dịch để không cắt mất đầu."""
    import cv2
    cap = cv2.VideoCapture(str(path))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    hits = []
    for i in range(24):
        cap.set(cv2.CAP_PROP_POS_MSEC, (i + 0.5) / 24 * dur * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        H, W = fr.shape[:2]
        k = 720 / max(W, H)
        small = cv2.cvtColor(cv2.resize(fr, None, fx=k, fy=k), cv2.COLOR_BGR2GRAY)
        faces = casc.detectMultiScale(small, 1.1, 6, minSize=(50, 50))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            hits.append(((x + w / 2) / k, (y + h / 2) / k, w / k))
    cap.release()
    if len(hits) < 4:
        sys.exit(f"chỉ thấy mặt ở {len(hits)}/24 khung: truyền --crop cx,cy,size")
    cx, cy, fw = (statistics.median(h[i] for h in hits) for i in range(3))
    drift = max(max(abs(h[0] - cx) for h in hits), max(abs(h[1] - cy) for h in hits)) if len(hits) > 1 else 0
    drift = min(drift, fw)   # 1 khung dò sai không được làm ô to gấp đôi
    return cx, cy + 0.18 * fw, max(2.3 * fw, 1.7 * fw + 2 * drift), len(hits), drift


def busiest_window(path):
    """Cửa sổ tỉ lệ 9:8 có nhiều chi tiết + thay đổi nhất của bản quay, để 2 dải nền không rơi vào vùng trống phẳng."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frames = []
    for i in range(12):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) / 12 * n))
        ok, f = cap.read()
        if ok:
            frames.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (216, 216 * f.shape[0] // f.shape[1])).astype(np.float32))
            H, W = f.shape[:2]
    cap.release()
    if not frames:
        raise SystemExit(f"không đọc được khung hình nào từ {path}")
    arr = np.stack(frames)
    score = np.abs(cv2.Laplacian(arr.mean(0), cv2.CV_32F)) + 3 * arr.std(0)   # chi tiết + chỗ có thay đổi theo thời gian
    h = score.shape[0] // 2
    w = min(score.shape[1], h * 9 // 8)
    ii = cv2.integral(score)
    best = max(((ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x]), x, y)
               for y in range(0, score.shape[0] - h + 1, 4) for x in range(0, score.shape[1] - w + 1, 4))
    k = W / score.shape[1]
    return int(best[1] * k) // 2 * 2, int(best[2] * k) // 2 * 2, int(w * k) // 2 * 2, int(h * k) // 2 * 2


def audio_offset(face, screen):
    """Trả (offset, độ tin cậy): giờ màn hình = giờ A-roll + offset, dò bằng tương quan chéo envelope âm lượng."""
    import numpy as np
    rate = 100

    def env(p):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:a:0", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                             capture_output=True).stdout
        a = np.frombuffer(raw, dtype=np.float32)
        n = len(a) // 80
        e = np.sqrt(np.mean(a[:n * 80].reshape(n, 80) ** 2, axis=1) + 1e-10)
        e = np.log(e)
        return (e - e.mean()) / (e.std() + 1e-9)

    a, b = env(face), env(screen)
    n = len(a) + len(b)
    corr = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)
    lags = np.fft.fftfreq(n, 1 / n).astype(int)
    i = int(np.argmax(corr))
    overlap = max(1, min(len(a), len(b)))
    return lags[i] / rate, float(corr[i] / overlap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--face", required=True)
    ap.add_argument("--screen", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--keep")
    ap.add_argument("--offset", default="0")
    ap.add_argument("--crop")
    ap.add_argument("--no-bg", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fi, si = probe(a.face), probe(a.screen)
    if not fi["audio"]:
        sys.exit("A-roll không có tiếng")
    if si["w"] <= si["h"]:
        sys.exit(f"bản quay màn hình {si['w']}x{si['h']} không phải khung ngang")
    for name, info in (("A-roll", fi), ("màn hình", si)):
        if info["transfer"] in ("arib-std-b67", "smpte2084"):
            print(f"cảnh báo: {name} là HDR ({info['transfer']}): nên tonemap trước, không thì màu sẽ nhạt")

    if a.offset == "auto":
        if not si["audio"]:
            sys.exit("bản quay màn hình không có tiếng nên không dò được offset: truyền --offset <giây> "
                     "(vỗ tay 1 cái lúc bắt đầu quay giúp đo dễ)")
        offset, conf = audio_offset(a.face, a.screen)
        print(f"offset dò được: {offset:+.2f}s (độ tin cậy {conf:.2f})")
        if conf < 0.3:
            sys.exit("độ tin cậy thấp (< 0.3), có thể 2 file không quay cùng lúc: kiểm tra và truyền --offset <giây>")
    else:
        offset = float(a.offset)

    if a.crop:
        cx, cy, side = map(float, a.crop.split(","))
    else:
        cx, cy, side, hits, drift = detect_face(a.face, fi["dur"])
        print(f"mặt: tâm ({cx:.0f},{cy:.0f}), ô {side:.0f}px, thấy ở {hits}/24 khung, xê dịch {drift:.0f}px")
    side = int(min(side, fi["w"], fi["h"])) // 2 * 2
    x = int(min(max(cx - side / 2, 0), fi["w"] - side)) // 2 * 2
    y = int(min(max(cy - side / 2, 0), fi["h"] - side)) // 2 * 2
    if side < 380:
        print(f"cảnh báo: ô mặt chỉ {side}px trên clip gốc, hiện ở 380px sẽ mềm")
    face_px = min(FACE_OUT, side)
    face_vf = f"crop={side}:{side}:{x}:{y},scale={face_px}:{face_px}:flags=lanczos,fps={FPS}"

    keep = json.loads(Path(a.keep).read_text()) if a.keep else [[0, fi["dur"]]]
    duration = sum(e - s for s, e in keep)
    sw = min(si["w"], 2160) // 2 * 2
    sh = round(sw * si["h"] / si["w"]) // 2 * 2

    with tempfile.TemporaryDirectory():
        n = len(keep)
        # A-roll: cắt + crop trong MỘT lần encode
        vf = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,{face_vf}[v{i}];[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}];"
                     for i, (s, e) in enumerate(keep))
        conc = "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
        run(["ffmpeg", "-y", "-v", "error", "-i", a.face, "-filter_complex", vf + conc, "-map", "[v]", "-map", "[a]", *ENC,
             "-c:a", "aac", "-b:a", "256k", str(out / "face.mp4")])

        # Màn hình: cùng các đoạn, dời theo offset; ngoài phạm vi bản quay thì giữ khung đứng yên
        parts = []
        for i, (s, e) in enumerate(keep):
            ss, ee = s + offset, e + offset
            pre = max(0.0, -ss)
            post = max(0.0, ee - si["dur"])
            ss, ee = max(ss, 0), min(ee, si["dur"])
            if ee <= ss:   # cả đoạn nằm ngoài bản quay: dừng ở khung sát nhất
                ss = min(max(ss, 0), max(si["dur"] - 0.1, 0))
                ee = ss + 0.1
                post = e - s - 0.1
                pre = 0
            pad = f",tpad=start_mode=clone:start_duration={pre:.3f}:stop_mode=clone:stop_duration={post:.3f}" if pre or post else ""
            parts.append(f"[0:v]trim={ss}:{ee},setpts=PTS-STARTPTS,scale={sw}:{sh}:flags=lanczos,fps={FPS}{pad}[s{i}];")
            if pre or post:
                print(f"đoạn {s:.1f}-{e:.1f}s: bản quay thiếu {pre + post:.1f}s, giữ khung đứng yên")
        conc = "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        run(["ffmpeg", "-y", "-v", "error", "-i", a.screen, "-filter_complex", "".join(parts) + conc, "-map", "[v]", *ENC,
             str(out / "screen.mp4")])

    if not a.no_bg:   # nền = chính bản quay làm mờ, KHÔNG lấy từ A-roll (mặt mờ hiện ở nền, người dùng đã chê); nhỏ, không đụng chất lượng khung chính
        wx, wy, ww, wh = busiest_window(out / "screen.mp4")
        print(f"nền: vùng nhiều chi tiết nhất của bản quay x {wx} y {wy} ({ww}x{wh})")
        # 2 dải cùng lấy vùng này, dải dưới lật lại cho khác dải trên; chỗ nối y 960 khuất sau màn hình
        run(["ffmpeg", "-y", "-v", "error", "-i", str(out / "screen.mp4"), "-an", "-filter_complex",
             f"[0:v]crop={ww}:{wh}:{wx}:{wy},scale=360:320,split[t][d];[d]vflip,hflip[f];[t][f]vstack,gblur=sigma=8,eq=saturation=1.35,format=yuv420p[v]",
             "-map", "[v]", "-c:v", "libx264", "-crf", "20", "-preset", "medium", str(out / "bg.mp4")])

    (out / "tutorial.json").write_text(json.dumps({
        "duration": round(probe(out / "face.mp4")["dur"], 3), "planned": round(duration, 3), "offset": offset,
        "screen_w": sw, "screen_h": sh, "crop": {"x": x, "y": y, "side": side}}, indent=1))
    print(f"xong: {duration:.1f}s, màn hình {sw}x{sh}, mặt {face_px}px → {out}")


if __name__ == "__main__":
    main()
