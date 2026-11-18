# Vùng an toàn video 9:16 (1080×1920)

Áp dụng cho mọi video dọc 9:16 dựng bằng skill này (kể cả thumbnail frame đầu).
Đo từ ảnh chụp TikTok trên iPhone có Dynamic Island (2026-11-01): chip "Muốn sửa? Chat lại" ở top ~100px bị
Dynamic Island + giờ/pin che, card ở ~170px bị thanh tìm kiếm đè. Reels/Shorts có vùng che tương tự.

| Vùng | Toạ độ (px ở 1080×1920) | Bị che bởi |
|---|---|---|
| Trên | y < 250 | giờ, Dynamic Island, pin, thanh tìm kiếm / tab "Đang follow · Dành cho bạn" |
| Dưới | y > 1500 | tên kênh, mô tả, nhạc, banner "tăng lượt xem", thanh tiến trình |
| Hai bên | x < 70, x > 1010 | máy màn dài (19.5:9) phóng video cho kín chiều cao nên cắt ~50px mỗi bên |
| Cột nút phải | x > 900 khi y 850–1500 | avatar, tim, bình luận, lưu, chia sẻ |

**Quy tắc**
- Chữ, chip, sticker, logo, số liệu, CTA, phụ đề: nằm hết trong khung `x 70–1010, y 250–1500`, không lấn cột nút phải.
  Tính cả phần chữ to ra khi animate (scale/pop) và dấu tiếng Việt ở dòng trên cùng.
- Phụ đề: đáy dòng cuối ≤ 1500 → `top` mặc định 1380px (2 dòng 66px vẫn vừa); tâm ≤ 0.76 × 1920.
- Ngoài vùng an toàn chỉ được để nền, ảnh/video, người, vật trang trí không có chữ (vd mèo meme đứng sát đáy là được).
- Thumbnail frame đầu cũng theo vùng này (lưới trang cá nhân còn cắt 3:4, tức chỉ thấy y ~240–1680).

**Kiểm tra:** sau khi snapshot, vẽ vùng che lên ảnh rồi xem:
```bash
python3 "$SK/scripts/safezone.py" <ảnh hoặc thư mục snapshot> [-o <thư mục ra>]
```
Ảnh ra có vùng đỏ = bị UI che; chữ nào chạm vùng đỏ thì dời vào trong rồi snapshot lại.
