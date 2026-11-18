#!/usr/bin/env bash
# Cài một lần cho /tool-video. Chạy lại không sao.
# Dòng cuối khi xong: "READY <python>". Dùng python đó cho mọi script của skill.
# venv nằm ở $CLAUDE_PLUGIN_DATA/venv khi cài dạng plugin (giữ qua các lần update), không thì .venv cạnh skill.
# Các dòng NEED_* là phần còn thiếu; NEED_FFMPEG / NEED_NODE / NEED_PYTHON chặn, NEED_WHISPER chỉ là tuỳ chọn.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/venv}"
VENV="${VENV:-$SKILL/.venv}"
missing=0

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "NEED_FFMPEG: Mac: brew install ffmpeg | Windows: winget install ffmpeg | Linux: sudo apt install ffmpeg"; missing=1
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npx >/dev/null 2>&1; then
  echo "NEED_NODE: cài Node.js 22+ (nodejs.org), HyperFrames chạy bằng npx"; missing=1
fi
if ! command -v whisper-cli >/dev/null 2>&1; then
  echo "NEED_WHISPER: (tuỳ chọn) Mac: brew install whisper-cpp. Không có thì phải đưa script/.srt kèm A-roll"
fi
[ "$missing" = 1 ] && exit 1

pybin() { if [ -x "$VENV/bin/python" ]; then echo "$VENV/bin/python"; else echo "$VENV/Scripts/python.exe"; fi; }
if [ -x "$(pybin)" ] && "$(pybin)" -c "import numpy, PIL" 2>/dev/null; then echo "READY $(pybin)"; exit 0; fi

PY=""
for v in python3.12 python3.13 python3.11 python3.10 python3 python py; do
  if command -v "$v" >/dev/null 2>&1 && "$v" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then PY="$v"; break; fi
done
mkdir -p "$(dirname "$VENV")"
if [ -n "$PY" ]; then
  "$PY" -m venv "$VENV"
  "$(pybin)" -m pip install -q --upgrade pip
  "$(pybin)" -m pip install -q -r "$SKILL/requirements.txt"
elif command -v uv >/dev/null 2>&1; then
  uv venv -q -p 3.12 "$VENV"
  uv pip install -q -p "$(pybin)" -r "$SKILL/requirements.txt"
else
  echo "NEED_PYTHON: cài Python 3.10 trở lên (python.org/downloads) rồi chạy lại"; exit 1
fi
"$(pybin)" -c "import numpy, PIL" && echo "READY $(pybin)"
