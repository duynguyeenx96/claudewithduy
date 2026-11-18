"""Kéo mốc từ của Whisper DTW ra khỏi khoảng lặng thật, trước khi cắt khoảng lặng.

DTW hay đặt từ đầu câu quá sớm (vd "Hơn"@0.38 trong khi 0-4.3s im lặng) và từ cuối câu quá muộn.
cut-silences tin mốc từ, nên từ nằm sai trong khoảng lặng làm nó cắt mất tiếng thật.

    python3 snap_words.py raw.json <media> -o raw.snapped.json [--noise -40] [--min 0.25]

Từ cuối câu (có dấu câu) -> luôn dời về ngay trước khoảng lặng; từ khác gần mép đầu (và còn chỗ sau từ trước) -> trước; còn lại -> ra sau nó.
Mốc kết thúc = min(start + 0.6, từ kế tiếp, khoảng lặng kế tiếp).
"""
import argparse
import json
import re
import subprocess


def silences(media, noise_db, min_sec, win=0.05):
    """Khoảng lặng theo năng lượng RMS từng 50ms. silencedetect xét đỉnh từng mẫu nên một tiếng click
    (-49 dB RMS) cũng cắt đôi khoảng lặng; RMS thì không, mà vẫn giữ được chữ ngắn ("Tất")."""
    sr = 48000
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", media, "-vn", "-ac", "1", "-ar", str(sr), "-af",
                          f"asetnsamples={int(sr * win)},astats=metadata=1:reset=1,"
                          "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    rms = [float(x) if x not in ("-inf", "inf", "nan") else -120.0
           for x in re.findall(r"RMS_level=(\S+)", out)]
    gaps, start = [], None
    for i, db in enumerate(rms + [0.0]):
        if db < noise_db and start is None:
            start = i
        elif db >= noise_db and start is not None:
            if (i - start) * win >= min_sec:
                gaps.append((round(start * win, 3), round(i * win, 3)))
            start = None
    return gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("media")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--noise", type=float, default=-42)
    ap.add_argument("--min", type=float, default=0.25)
    a = ap.parse_args()

    data = json.load(open(a.transcript))
    words = data if isinstance(data, list) else data["words"]
    gaps = silences(a.media, a.noise, a.min)
    moved = []
    for i, w in enumerate(words):
        gap = next(((s, e) for s, e in gaps if s <= w["start"] < e), None)
        if not gap:
            continue
        s, e = gap
        prev = words[i - 1]["start"] if i else None
        final = re.search(r"[.,!?;:]$", w["text"])
        if prev is not None and (final or (s - prev >= 0.25 and w["start"] - s <= e - w["start"])):
            new = max(prev + 0.1, s - 0.3)
        else:
            new = e
        moved.append(f"{w['text']}@{w['start']:.2f}->{new:.2f}")
        w["start"] = round(new, 3)
    # DTW đặt đầu từ trễ 0.1-0.3s: từ đầu tiên sau một khoảng lặng bắt đầu đúng lúc tiếng nói bắt đầu lại
    # (trừ 40ms cho phụ âm đầu nhỏ hơn ngưỡng), không thì cut-silences cắt cụt chữ ("Và đó" -> "đó").
    for s, e in gaps:
        i = next((i for i, w in enumerate(words) if w["start"] >= e - 0.05), None)
        if i is not None and words[i]["start"] - e < 0.6 and (i == 0 or words[i - 1]["start"] <= s):
            if abs(words[i]["start"] - (e - 0.04)) > 0.02:
                moved.append(f"{words[i]['text']}@{words[i]['start']:.2f}->{e - 0.04:.2f}")
            words[i]["start"] = round(max(e - 0.04, words[i - 1]["start"] + 0.05 if i else 0), 3)
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else w["start"] + 0.6
        sil = next((s for s, _ in gaps if s > w["start"]), w["start"] + 0.6)
        w["end"] = round(max(w["start"] + 0.05, min(w["start"] + 0.6, nxt, sil)), 3)
    json.dump(words, open(a.output, "w"), ensure_ascii=False, indent=1)
    print(f"{len(moved)} từ dời khỏi khoảng lặng: " + ", ".join(moved))


if __name__ == "__main__":
    main()
