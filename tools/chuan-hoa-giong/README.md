# Chuẩn hoá giọng

Kéo thả video vào trình duyệt, nhận file đã chuẩn hoá về -16 LUFS (ffmpeg `loudnorm` đo 2 lượt). Chạy hoàn toàn trên máy bạn, chỉ nghe ở 127.0.0.1.

Cần: Python 3, FFmpeg.

- macOS: bấm đúp `chuan-hoa-giong.command` (lần đầu: chuột phải, chọn Mở).
- Linux / Windows: `python3 server.py` rồi mở http://localhost:8769.
- Đổi cổng: biến `PORT`. Kết quả ở `output/` (tự xoá sau 7 ngày, đổi bằng `KEEP_DAYS`), bản gốc tải lên ở `input/` (xoá sau 1 ngày).
