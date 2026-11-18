#!/usr/bin/env python3
"""Soát "vùng chết" của video đã render: đoạn mà hình gần như không đổi, người xem dễ lướt.

  python3 deadzones.py <video.mp4> [--win 3] [--json out.json]

Đo độ khác nhau giữa các khung liên tiếp (ffmpeg signalstats YDIF, 10 khung/giây, ảnh thu nhỏ), gộp theo từng giây,
rồi báo các cửa sổ --win giây có chuyển động dưới 35% mức trung vị của cả video. 3 giây đầu (hook) soát riêng: phải động hơn trung vị.
Chỉ là gợi ý chỗ nên thêm đồ hoạ / zoom / cắt: người nói ngồi yên có chủ ý thì bỏ qua.
"""
import argparse
import json
import re
import statistics
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--win", type=int, default=3)
ap.add_argument("--json")
a = ap.parse_args()

err = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", a.video, "-an", "-vf",
                      "fps=10,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YDIF", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
v = [float(x) for x in re.findall(r"YDIF=([0-9.]+)", err)]
sec = [sum(v[i:i + 10]) / len(v[i:i + 10]) for i in range(0, len(v), 10)]
if len(sec) < a.win + 1:
    raise SystemExit("video quá ngắn để soát")
med = statistics.median(sec) or 0.01
zones = []
for s in range(0, len(sec) - a.win + 1):
    m = sum(sec[s:s + a.win]) / a.win
    if m < 0.35 * med:
        if zones and s <= zones[-1][1]:
            zones[-1][1] = s + a.win
        else:
            zones.append([s, s + a.win])
hook = sum(sec[:3]) / 3
out = {"seconds": len(sec), "median": round(med, 3), "hook": round(hook / med, 2), "dead": zones}
print(f"{a.video}: {len(sec)}s, chuyển động trung vị {med:.2f}")
print(f"hook 3s đầu: {hook / med:.2f} lần trung vị" + (" -> yếu, nên có chuyển động / đồ hoạ ngay giây đầu" if hook < med else ""))
for s, e in zones:
    print(f"vùng chết {s}s-{e}s: hình gần như đứng yên")
if not zones:
    print("không có vùng chết")
if a.json:
    json.dump(out, open(a.json, "w"), indent=1)
