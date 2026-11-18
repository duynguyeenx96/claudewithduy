"""Gắn thumbnail vào frame đầu ngay trong composition, để render một lần là có cover (không cần ffmpeg chạy lại cả video).

    python3 add_cover.py <public>            # dùng <public>/cover.png; không có file thì gỡ cover cũ
    python3 add_cover.py <public> thumb.png  # chép thumb.png thành <public>/cover.png rồi gắn

Chạy sau `build.py` (build.py ghi lại index.html nên mỗi lần build phải gắn lại). Chạy nhiều lần vẫn chỉ có một cover.
"""
import re
import shutil
import sys
from pathlib import Path

pub = Path(sys.argv[1])
if len(sys.argv) > 2:
    shutil.copy(sys.argv[2], pub / "cover.png")
html_path = pub / "index.html"
html = re.sub(r'\n?<img id="hf-cover"[^>]*>', "", html_path.read_text())
if (pub / "cover.png").exists():
    stage = re.search(r'<div id="stage"[^>]*>', html)
    if not stage:
        sys.exit("không thấy #stage trong index.html")
    fps = float(re.search(r'data-fps="([\d.]+)"', stage.group(0)).group(1))
    tag = (f'\n<img id="hf-cover" class="clip" src="cover.png" data-start="0" data-duration="{1 / fps - 0.0005:.4f}" data-track-index="999" '
           'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:9999">')
    html = html[:stage.end()] + tag + html[stage.end():]
    print("đã gắn cover vào frame đầu")
else:
    print("không có cover.png: bỏ cover")
html_path.write_text(html)
