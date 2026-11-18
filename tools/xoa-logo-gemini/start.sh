#!/usr/bin/env bash
# Linux (và macOS qua terminal): bash start.sh
cd "$(dirname "$0")"
PORT="${PORT:-8768}"
for c in python3 node npm; do command -v "$c" >/dev/null || { echo "Thiếu '$c'. Cài rồi chạy lại."; exit 1; }; done
[ -d node_modules/@pilio ] || npm install --ignore-scripts || { echo "npm install lỗi"; exit 1; }
(sleep 1; xdg-open "http://localhost:$PORT" 2>/dev/null || open "http://localhost:$PORT" 2>/dev/null) &
PORT="$PORT" exec python3 server.py
