#!/usr/bin/env bash
# Linux (và macOS qua terminal): bash start.sh
cd "$(dirname "$0")"
PORT="${PORT:-8769}"
for c in python3 ffmpeg; do command -v "$c" >/dev/null || { echo "Thiếu '$c'. Cài rồi chạy lại."; exit 1; }; done

(sleep 1; xdg-open "http://localhost:$PORT" 2>/dev/null || open "http://localhost:$PORT" 2>/dev/null) &
PORT="$PORT" exec python3 server.py
