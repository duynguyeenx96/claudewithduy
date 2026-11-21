#!/usr/bin/env python3
"""Vietnamese voiceover with ZeroTTS, after applying the shared pronunciation dict (~/.zerotts/voice_dict.json).

Usage (run with the Python that has `zerotts` installed):
  <python> -I tts.py <out_dir> <lines.json> [--voice baotrang] [--model ~/.cache/video-storyboard/ZeroTTS] [--dry]

lines.json: {"intro": "câu thoại…", "area": "…"}  ->  <out_dir>/vo_<key>.wav
--dry prints the text that will be spoken (after the dict) without synthesising.
As a module: `from voicedict import load_dict, normalize; normalize(text, load_dict())` (copy at ~/.zerotts/voicedict.py).

Model + voices: ZeroTTS model folder (has onnx/, voices/<name>/, voices/index.json).
Default ~/.cache/video-storyboard/ZeroTTS; override with --model or ZEROTTS_MODEL.
Voices: baotrang (nữ, tin tức), maichi (nữ, nhẹ nhàng), kimoanh (nữ, ấm), quangminh (nam, tin tức),
        giahuy (nam, trầm ấm), tiendat (nam, sôi nổi), huuduc (nam, điềm đạm), hamy (nữ, hoạt hình).
"""
import json, os, re, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# One shared pronunciation dict for every ZeroTTS job on this machine (override: ZEROTTS_DICT).
DICT = os.path.expanduser(os.environ.get("ZEROTTS_DICT", "~/.zerotts/voice_dict.json"))
SEED = os.path.join(SKILL, "voice_dict.seed.json")


def load_dict():
    """Shared dict; first run copies the seed that ships with the skill."""
    if not os.path.exists(DICT) and os.path.exists(SEED):
        os.makedirs(os.path.dirname(DICT), exist_ok=True)
        with open(SEED, encoding="utf8") as a, open(DICT, "w", encoding="utf8") as b:
            b.write(a.read())
    return json.load(open(DICT, encoding="utf8")) if os.path.exists(DICT) else {}
DIGITS = "không một hai ba bốn năm sáu bảy tám chín".split()


def read3(n, full):
    """0..999 in Vietnamese. full=True forces 'không trăm' / 'lẻ' (inside larger numbers)."""
    tr, ch, dv = n // 100, n // 10 % 10, n % 10
    out = []
    if tr or full:
        out += [DIGITS[tr], "trăm"]
    if ch == 0:
        if dv and (tr or full):
            out.append("lẻ")
    elif ch == 1:
        out.append("mười")
    else:
        out += [DIGITS[ch], "mươi"]
    if dv:
        if dv == 1 and ch > 1:
            out.append("mốt")
        elif dv == 5 and ch:
            out.append("lăm")
        elif dv == 4 and ch > 1:
            out.append("tư")
        else:
            out.append(DIGITS[dv])
    return out


def say_int(n):
    if n == 0:
        return "không"
    groups, scales = [], ["", "nghìn", "triệu", "tỷ"]
    while n:
        groups.append(n % 1000)
        n //= 1000
    words = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        words += read3(g, full=i < len(groups) - 1) + ([scales[i]] if scales[i] else [])
    return " ".join(words)


def say_num(s):
    s = s.replace(".", "")  # 43.500 -> 43500 (Vietnamese thousands dot)
    if "," in s:
        a, b = s.split(",", 1)
        return say_int(int(a)) + " phẩy " + (" ".join(DIGITS[int(c)] for c in b) if b.startswith("0") else say_int(int(b)))
    return say_int(int(s))


def normalize(text, d):
    for k, v in d.get("phrasing", {}).items():
        if not k.startswith("_"):
            text = text.replace(k, v)
    for k, v in sorted(d.get("words", {}).items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"(?<!\w){re.escape(k)}(?!\w)", v["say"], text)
    text = re.sub(r"[~≈]\s*", "khoảng ", text)
    text = re.sub(r"(\d[\d.]*(?:,\d+)?)\+", r"hơn \1", text)  # 70+ -> hơn 70
    text = text.replace("·", ",")
    units = sorted(d.get("units", {}).items(), key=lambda kv: -len(kv[0]))
    unit_re = "|".join(re.escape(u) for u, _ in units)
    umap = dict(units)
    text = re.sub(rf"(\d[\d.]*(?:,\d+)?)\s*({unit_re})(?!\w)", lambda m: f"{say_num(m.group(1))} {umap[m.group(2)]}", text)
    text = re.sub(r"\d[\d.]*(?:,\d+)?", lambda m: say_num(m.group(0)), text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    a = sys.argv[1:]
    opt = lambda k, dv: a[a.index(k) + 1] if k in a else dv  # noqa: E731
    out, lines_p = a[0], a[1]
    voice = opt("--voice", "baotrang")
    model = os.path.expanduser(opt("--model", os.environ.get("ZEROTTS_MODEL", "~/.cache/video-storyboard/ZeroTTS")))
    d = load_dict()
    print(f"dict: {DICT}")
    lines = {k: normalize(v, d) for k, v in json.load(open(lines_p, encoding="utf8")).items()}
    for k, v in lines.items():
        print(f"{k}: {v}")
    if "--dry" in a:
        return
    from zerotts import ZeroTTS
    tts = ZeroTTS.from_pretrained(model)
    os.makedirs(out, exist_ok=True)
    for k, v in lines.items():
        tts.save_audio(tts.synthesize(v, voice=voice), os.path.join(out, f"vo_{k}.wav"))
    print("done:", ", ".join(f"vo_{k}.wav" for k in lines))


if __name__ == "__main__":
    main()
