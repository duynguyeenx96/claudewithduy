"""Tự dọn file cũ trong thư mục input / output / preview của các tool kéo-thả, để không đầy ổ dần.

    autoclean.start({IN: 1, OUT: 7})     # số ngày giữ cho từng thư mục; dọn lúc khởi động rồi mỗi giờ một lần

Chỉ xoá file thường nằm trực tiếp trong thư mục (không đụng thư mục con, file ẩn), tính theo giờ sửa cuối.
Xoá hẳn, không qua Thùng rác: đây chỉ là bản sao / kết quả đã tải về. Đổi số ngày giữ kết quả bằng env KEEP_DAYS (0 = không dọn).
"""
import os
import threading
import time
from pathlib import Path

KEEP_DAYS = float(os.environ.get("KEEP_DAYS", 7))


def sweep(rules: dict[Path, float]) -> int:
    n, now = 0, time.time()
    for folder, days in rules.items():
        if days <= 0 or not folder.is_dir():
            continue
        for f in folder.iterdir():
            try:
                if f.is_file() and not f.is_symlink() and not f.name.startswith(".") and now - f.stat().st_mtime > days * 86400:
                    f.unlink()
                    n += 1
            except OSError:
                pass
    return n


def start(rules: dict[Path, float], every: float = 3600):
    def loop():
        while True:
            n = sweep(rules)
            if n:
                print(f"autoclean: đã xoá {n} file cũ", flush=True)
            time.sleep(every)
    threading.Thread(target=loop, daemon=True).start()
