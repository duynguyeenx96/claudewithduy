"""Chuẩn hoá giọng A-roll về -16 LUFS (loudnorm 2 lượt), giữ nguyên hình (-c:v copy).

    python3 loudnorm.py in.mp4 out.mp4 [--target -16]
"""
import argparse
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--target", type=float, default=-16)
    a = ap.parse_args()
    base = f"loudnorm=I={a.target}:TP=-1.5:LRA=11"
    err = subprocess.run(["ffmpeg", "-nostats", "-i", a.src, "-vn", "-af", base + ":print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    flt = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-c:v", "copy", "-af", flt, "-ar", "48000",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", a.dst], check=True)
    print(f"{m['input_i']} LUFS -> {a.target} LUFS: {a.dst}")


if __name__ == "__main__":
    main()
