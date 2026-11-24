#!/usr/bin/env python3
"""Find when each word and each line is said, so effects land on the right moment.

usage: python words.py input.mp4
  prints one line per spoken phrase ("  12.34-15.60  text") and saves:
    input.words.json  every word with its time   [{"w", "s", "e"}]
    input.lines.json  the phrases                [{"s", "e", "text"}]
Uses faster-whisper (installed on first run, model "small", override with WHISPER_MODEL). On a Mac with mlx-whisper installed, that is used instead.
"""
import json, os, subprocess, sys

src = sys.argv[1]
base = os.path.splitext(src)[0]
words = []
try:
    import mlx_whisper
    r = mlx_whisper.transcribe(src, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', word_timestamps=True)
    words = [{'w': w['word'].strip(), 's': round(w['start'], 2), 'e': round(w['end'], 2)} for seg in r['segments'] for w in seg.get('words', [])]
except ImportError:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print('Installing the transcriber (one time, about 1 minute)...', flush=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper'], check=True)
        from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get('WHISPER_MODEL', 'small'), device='cpu', compute_type='int8')
    # Giải mã bằng ffmpeg rồi đưa mảng vào: để faster-whisper tự mở file thì nó dùng PyAV, mà av bản mới (>=15) đổi API làm hỏng.
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    segs, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True)
    words = [{'w': w.word.strip(), 's': round(w.start, 2), 'e': round(w.end, 2)} for s in segs for w in (s.words or [])]

# Gom từ thành câu: ngắt ở chỗ nghỉ >= 0.45s, ở dấu câu, hoặc khi câu đã dài 16 từ.
lines, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if nxt is None or nxt['s'] - w['e'] >= 0.45 or w['w'][-1:] in '.?!' or len(cur) >= 16:
        lines.append({'s': cur[0]['s'], 'e': cur[-1]['e'], 'text': ' '.join(x['w'] for x in cur)})
        cur = []

json.dump(words, open(base + '.words.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(lines, open(base + '.lines.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for l in lines: print(f"{l['s']:7.2f}-{l['e']:<7.2f} {l['text']}")
print(f'\n{len(lines)} lines, {len(words)} words. Word times: {base}.words.json  Lines: {base}.lines.json')
print('Speech recognition misses names and slang: fix the text from context before using it on screen.')
