#!/usr/bin/env python3
"""Lấy màu nền từ A-roll rồi tính 5 nhóm phối màu theo vòng tròn màu.

    python3 palette.py public/aroll.mp4 [--at 2] [--json palette.json]

Màu nền = trung bình vùng trên 30% khung (thường là tường sau lưng người nói).
Mỗi nhóm trả về base (nền tối, 60%), support (chữ chính, 30%), accent (màu nhấn, 10%), accent2.
"""
import argparse
import colorsys
import json
import subprocess
import sys

SCHEMES = {
    # tên: (độ lệch hue của accent, độ lệch hue của accent2, cảm giác)
    "complement": (180, 0, "tương phản mạnh nhất, giật mắt: hook, CTA"),  # accent2 = chính hue nền, sáng lên
    "splitcomp": (150, 210, "tương phản mạnh nhưng đỡ gắt, 2 màu nhấn luân phiên"),
    "triad": (120, 240, "vui, nhiều năng lượng: meme, tool vui"),
    "analog": (30, -30, "êm, liền mạch, sang: review nghiêm túc"),
    "mono": (0, 0, "tối giản, cao cấp: ít đồ hoạ"),
}


def sample(video: str, at: float) -> tuple[int, int, int]:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(at), "-i", video, "-frames:v", "1",
         "-vf", "crop=iw:ih*0.3:0:0,scale=1:1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return raw[0], raw[1], raw[2]


def hexc(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def build(rgb) -> dict:
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    hue = h * 360
    out = {"source": "#%02x%02x%02x" % rgb, "hue": round(hue), "schemes": {}}
    for name, (d1, d2, mood) in SCHEMES.items():
        if name == "mono":
            accent, accent2 = hexc(hue, 0.78, 0.9), hexc(hue, 0.62, 0.75)
        else:
            # màu nhấn: sáng, rất đậm (neon) để nổi trên nền tối
            accent, accent2 = hexc(hue + d1, 0.6, 1.0), hexc(hue + d2, 0.62, 0.95)
        out["schemes"][name] = {
            "base": hexc(hue, 0.12, max(s, 0.55)),      # nền tối cùng hue với phòng quay
            "support": hexc(hue, 0.95, 0.15),           # trắng ngả theo hue nền
            "accent": accent,
            "accent2": accent2,
            "mood": mood,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--at", type=float, default=2.0)
    ap.add_argument("--json")
    a = ap.parse_args()
    res = build(sample(a.video, a.at))
    if a.json:
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"nền {res['source']} (hue {res['hue']}°)")
    for k, v in res["schemes"].items():
        print(f"  {k:<10} base {v['base']}  support {v['support']}  accent {v['accent']}  accent2 {v['accent2']}  · {v['mood']}")


if __name__ == "__main__":
    sys.exit(main())
