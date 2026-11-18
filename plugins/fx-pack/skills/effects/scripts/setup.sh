#!/usr/bin/env bash
# One-time setup for the effects skill. Safe to run again.
# Last line on success: "READY <path to python>" — use that python for every command.
# The venv lives in $CLAUDE_PLUGIN_DATA when installed as a plugin (survives plugin updates),
# otherwise next to the skill in .venv.
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/venv}"
VENV="${VENV:-$SKILL/.venv}"

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "NEED_FFMPEG: install ffmpeg first (Mac: brew install ffmpeg, Windows: winget install ffmpeg, Linux: sudo apt install ffmpeg)"; exit 1
fi

pybin() { if [ -x "$VENV/bin/python" ]; then echo "$VENV/bin/python"; else echo "$VENV/Scripts/python.exe"; fi; }

if [ -x "$(pybin)" ] && "$(pybin)" -c "import mediapipe, cv2, PIL, numpy" 2>/dev/null; then echo "READY $(pybin)"; exit 0; fi

PY=""
for v in python3.12 python3.11 python3.13 python3.10 python3 python py; do
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
  echo "NEED_PYTHON: install Python 3.10 or newer (python.org/downloads), then run this again"; exit 1
fi

"$(pybin)" -c "import mediapipe, cv2, PIL, numpy" && echo "READY $(pybin)"
