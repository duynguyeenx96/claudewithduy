#!/usr/bin/env bash
# Cài một lần cho skill xoa-logo. Chạy lại được.
# Dòng cuối khi xong: "READY <thư mục gwr>". Thiếu gì thì dòng cuối bắt đầu bằng NEED_.
# Dạng plugin: thư viện nằm ở $CLAUDE_PLUGIN_DATA/deps (không mất khi update); chạy tay thì nằm cạnh skill trong .deps.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DEPS="${CLAUDE_PLUGIN_DATA:+$CLAUDE_PLUGIN_DATA/deps}"
DEPS="${DEPS:-$HERE/../.deps}"
GWR="$DEPS/node_modules/@pilio/gemini-watermark-remover/bin/gwr.mjs"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "NEED_NODE: cài Node.js 18 trở lên (Mac: brew install node, Windows: winget install OpenJS.NodeJS.LTS, Linux: sudo apt install nodejs npm) rồi chạy lại"; exit 1
fi
if [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 18 ]; then
  echo "NEED_NODE: Node.js $(node -v) quá cũ, cần 18 trở lên"; exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "NEED_FFMPEG: cài ffmpeg (Mac: brew install ffmpeg, Windows: winget install Gyan.FFmpeg, Linux: sudo apt install ffmpeg) rồi chạy lại"; exit 1
fi

# Chromium cho playwright (gwr dùng để xử lý video), tải một lần ~150 MB vào cache chung của playwright
has_chromium() { (cd "$DEPS" && node -e "const fs=require('fs');const p=require('playwright');process.exit(fs.existsSync(p.chromium.executablePath())?0:1)") 2>/dev/null; }

# Đã cài đúng phiên bản thì thôi
if [ -f "$GWR" ] && cmp -s "$HERE/package-lock.json" "$DEPS/package-lock.json" && has_chromium; then echo "READY $DEPS"; exit 0; fi

mkdir -p "$DEPS"
cp "$HERE/package.json" "$HERE/package-lock.json" "$DEPS/"
# --ignore-scripts: không chạy script cài đặt của gói; sharp dùng bản dựng sẵn theo hệ điều hành.
(cd "$DEPS" && npm ci --ignore-scripts --no-audit --no-fund --loglevel=error)
if ! has_chromium; then
  echo "đang tải Chromium cho phần xử lý video (một lần, khoảng 150 MB)…"
  (cd "$DEPS" && npx --no-install playwright install chromium) >/dev/null 2>&1 || echo "⚠ tải Chromium lỗi: ảnh vẫn xoá được, video thì chưa. Chạy lại setup khi có mạng."
fi
[ -f "$GWR" ] && node -e "require('$DEPS/node_modules/sharp')" 2>/dev/null && echo "READY $DEPS" || { echo "NEED_REINSTALL: cài thư viện lỗi, xoá $DEPS rồi chạy lại"; exit 1; }
