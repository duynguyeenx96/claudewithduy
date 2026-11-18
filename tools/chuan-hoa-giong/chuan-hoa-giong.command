#!/bin/bash
# Bấm đúp để chạy. Lần đầu: chuột phải, chọn Mở để qua cảnh báo bảo mật của macOS.
cd "$(dirname "$0")"
PORT="${PORT:-8769}"
for c in python3 ffmpeg; do
  command -v "$c" >/dev/null || { echo "Thiếu '$c'. Cài: brew install ${c/python3/python} rồi chạy lại."; read -r -p "Enter để đóng"; exit 1; }
done
(sleep 1; open "http://localhost:$PORT") &
PORT="$PORT" exec python3 server.py
