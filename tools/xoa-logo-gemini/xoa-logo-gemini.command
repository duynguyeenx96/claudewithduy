#!/bin/bash
# Bấm đúp để chạy. Lần đầu: chuột phải, chọn Mở để qua cảnh báo bảo mật của macOS.
cd "$(dirname "$0")"
PORT="${PORT:-8768}"
for c in python3 node npm; do
  command -v "$c" >/dev/null || { echo "Thiếu '$c'. Cài Python 3 và Node.js rồi chạy lại."; read -r -p "Enter để đóng"; exit 1; }
done
[ -d node_modules/@pilio ] || npm install --ignore-scripts || { echo "npm install lỗi"; read -r -p "Enter để đóng"; exit 1; }
(sleep 1; open "http://localhost:$PORT") &
PORT="$PORT" exec python3 server.py
