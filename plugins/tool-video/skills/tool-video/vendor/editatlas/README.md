# vendor/editatlas

Chép từ https://github.com/EditAtlas/skills (Apache-2.0, commit `756826e58ea9e2bb7b77d0559a043c69da2cabca`), giữ nguyên, không sửa. Giấy phép: `LICENSE.txt`, ghi công: `NOTICE`.
Tên và logo "EditAtlas" không thuộc giấy phép Apache (mục 6).

- `video-check/scripts/check.py`: soát bản render (khung đen/trắng, đứng hình, khung lạ 1 frame, lặp khung, độ to, vỡ tiếng, hết tiếng sớm).
- `video-breakdown/scripts/`: `analyze.py` đo video mẫu, `compare.py` so bản làm lại với mẫu, `text_look.py` đo màu/cỡ chữ (bước gợi ý font tải CSS từ Google Fonts).

Không kèm: `fix_sound.py` (không master lại mp4 đã render), `report.py` (gọi dịch vụ EditAtlas).
