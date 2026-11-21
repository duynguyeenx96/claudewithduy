#!/usr/bin/env bash
# Cài giọng đọc ZeroTTS cho re-map-video (chỉ cần khi dùng AI voice). Chạy lại vô hại.
# Dòng cuối khi xong: "READY <python>" — dùng python đó để chạy tts.py.
# Venv nằm trong $CLAUDE_PLUGIN_DATA khi cài dạng plugin (không mất khi update), không thì cạnh skill trong .venv-tts.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/venv-tts}"
VENV="${VENV:-$SKILL/.venv-tts}"

pybin() { if [ -x "$VENV/bin/python" ]; then echo "$VENV/bin/python"; else echo "$VENV/Scripts/python.exe"; fi; }

if [ -x "$(pybin)" ] && "$(pybin)" -c "import zerotts" 2>/dev/null; then echo "READY $(pybin)"; exit 0; fi

PY=""
for v in python3.12 python3.11 python3.13 python3.10 python3 python py; do
  if command -v "$v" >/dev/null 2>&1 && "$v" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then PY="$v"; break; fi
done

mkdir -p "$(dirname "$VENV")"
if [ -n "$PY" ]; then
  "$PY" -m venv "$VENV"
  "$(pybin)" -m pip install -q --upgrade pip
  "$(pybin)" -m pip install -q zerotts
elif command -v uv >/dev/null 2>&1; then
  uv venv -q -p 3.12 "$VENV"
  uv pip install -q -p "$(pybin)" zerotts
else
  echo "NEED_PYTHON: cài Python 3.10 trở lên (python.org/downloads) rồi chạy lại"; exit 1
fi

"$(pybin)" -c "import zerotts" && echo "READY $(pybin)"
