#!/usr/bin/env python3
"""Chép lời từng từ cho FX Pack 2 (caption bám từng từ).

  python3 transcribe.py transcribe <audio|video> -o transcript.json [--language vi]   # whisper-cli + DTW (mốc từng từ)
  python3 transcribe.py srt <file.srt|.vtt|.json> -o transcript.json                 # phụ đề có sẵn -> từng từ

Ra mảng [{text, start, end}] (giây). Cần ffmpeg và whisper-cli (whisper.cpp: `brew install whisper-cpp`).
Model: biến WHISPER_MODEL, mặc định ~/.cache/hyperframes/whisper/models/ggml-medium.bin
(`npx hyperframes transcribe <file> --model medium` tải sẵn model này, hoặc tải ggml-medium.bin từ huggingface.co/ggerganov/whisper.cpp).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", os.path.expanduser("~/.cache/hyperframes/whisper/models/ggml-medium.bin"))
# câu Whisper hay bịa ở đoạn im lặng
HALLUCINATION_RE = re.compile(r"subscribe|đăng ký kênh|ghiền mì gõ|hẹn gặp lại", re.IGNORECASE)
SRT_TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})")


def silences(audio: str, noise_db: int = -40, min_sec: float = 0.25) -> list[tuple[float, float]]:
    err = subprocess.run(["ffmpeg", "-i", audio, "-af", f"silencedetect=n={noise_db}dB:d={min_sec}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    return list(zip(starts, ends))


def transcribe_dtw(media: str, language: str = "vi") -> list[dict]:
    """whisper.cpp với căn thời gian DTW theo token (bám tiếng nói chuẩn hơn mốc theo đoạn). DTW cần -nfa (tắt flash attention)."""
    if not shutil.which("whisper-cli"):
        sys.exit("thiếu whisper-cli: macOS `brew install whisper-cpp`, nơi khác build whisper.cpp")
    if not Path(WHISPER_MODEL).exists():
        sys.exit(f"thiếu model {WHISPER_MODEL}: đặt WHISPER_MODEL=<ggml-medium.bin> hoặc chạy `npx hyperframes transcribe <file> --model medium` một lần")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", media, "-ac", "1", "-ar", "16000", wav], check=True)
        subprocess.run(["whisper-cli", "-m", WHISPER_MODEL, "-l", language, "-f", wav, "-np", "-nfa",
                        "-t", str(max(4, (os.cpu_count() or 4) - 2)),
                        "--dtw", "medium", "-ojf", "-of", os.path.join(tmp, "out")], check=True, capture_output=True)
        data = json.loads(Path(tmp, "out.json").read_text())
    words = []
    for seg in data["transcription"]:
        for tok in seg.get("tokens", []):
            text = tok["text"]
            if text.startswith("[_") or not text.strip():
                continue
            if text.startswith(" ") or not words:  # token bắt đầu bằng khoảng trắng = từ mới
                words.append({"text": text.strip(), "start": max(tok.get("t_dtw", 0), 0) / 100})
            else:
                words[-1]["text"] += text
    words = [w for w in words if w["text"] not in ".,!?"]
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else w["start"] + 0.6
        w["end"] = round(min(nxt, w["start"] + 0.6), 3)
        w["start"] = round(w["start"], 3)
    return words


def srt_words(text: str) -> list[dict]:
    """SRT/VTT theo câu -> từng từ, chia thời gian của cue theo độ dài từ (tiếng Việt: 1 từ = 1 âm tiết)."""
    words = []
    for block in re.split(r"\n\s*\n", text.replace("\r", "")):
        lines = block.strip().splitlines()
        idx = next((i for i, line in enumerate(lines) if SRT_TIME_RE.search(line)), None)
        if idx is None:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, SRT_TIME_RE.search(lines[idx]).groups())
        start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        tokens = " ".join(re.sub(r"<[^>]+>", "", line) for line in lines[idx + 1:]).split()
        if not tokens or end <= start:
            continue
        weights = [len(t) + 2 for t in tokens]
        total, t = sum(weights), start
        for tok, w in zip(tokens, weights):
            dur = (end - start) * w / total
            words.append({"text": tok, "start": round(t, 3), "end": round(t + dur, 3)})
            t += dur
    return words


def load_words(path: str) -> list[dict]:
    if Path(path).suffix.lower() in (".srt", ".vtt"):
        return srt_words(Path(path).read_text(encoding="utf-8-sig"))
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        data = data.get("words") or [w for seg in data.get("segments", []) for w in seg.get("words", [])]
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("transcribe")
    p.add_argument("media")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--language", default="vi")
    p = sub.add_parser("srt")
    p.add_argument("source")
    p.add_argument("-o", "--output", required=True)
    a = ap.parse_args()

    if a.cmd == "srt":
        words = load_words(a.source)
        Path(a.output).write_text(json.dumps(words, ensure_ascii=False, indent=1))
        print(f"{len(words)} từ -> {a.output}")
        return

    words = transcribe_dtw(a.media, a.language)
    # DTW chỉ cho mốc bắt đầu; mốc kết thúc ước lượng có thể tràn vào khoảng lặng sau câu -> cắt tại đầu khoảng lặng
    gaps = silences(a.media)
    for w in words:
        for s, e in gaps:
            if w["start"] < s < w["end"]:
                w["end"] = round(s, 3)
    Path(a.output).write_text(json.dumps(words, ensure_ascii=False, indent=1))
    print(" ".join(f"{w['text']}@{w['start']:.2f}" for w in words))
    bad = [w for w in words if any(s + 0.1 < w["start"] < e - 0.1 for s, e in gaps)]
    fake = [w for w in words if HALLUCINATION_RE.search(w["text"])]
    print(f"{len(words)} từ -> {a.output}; khoảng lặng: " + "  ".join(f"{s:.2f}-{e:.2f}" for s, e in gaps))
    if bad:
        print("⚠ từ rơi vào khoảng lặng (Whisper có thể bịa hoặc lệch mốc): " + ", ".join(f"{w['text']}@{w['start']:.2f}" for w in bad))
    if fake:
        print("⚠ câu Whisper hay bịa: " + ", ".join(w["text"] for w in fake))


if __name__ == "__main__":
    main()
