---
name: xoa-logo
description: Xoá dấu sao Gemini/Veo (logo sparkle ở góc dưới phải) trên ảnh và video từ Gemini, Google Flow, Veo, chạy ngay trên máy bằng gwr. Dùng khi người dùng kéo/dán đường dẫn ảnh hoặc video vào và muốn "xoá logo Gemini", "xoá watermark Veo/Flow", "bỏ dấu sao", hoặc gõ `/xoa-logo-gemini:xoa-logo <file…>`. Nhận nhiều file hoặc cả thư mục.
---

# /xoa-logo: xoá dấu sao Gemini/Veo

Người dùng thường **kéo file vào terminal** (đường dẫn tự dán vào, có thể có dấu nháy hoặc `\ ` trước khoảng trắng) hoặc dán đường dẫn. Lấy mọi đường dẫn ảnh/video trong tin nhắn, kể cả thư mục.

`S=${CLAUDE_SKILL_DIR}/scripts`

1. **Cài (lần đầu, tự kiểm tra lại mỗi lần, rất nhanh nếu đã cài):** `bash $S/setup.sh`. Dòng cuối `READY …` thì đi tiếp. `NEED_NODE` / `NEED_FFMPEG`: báo người dùng đúng lệnh cài trong dòng đó rồi dừng, không tự cài khi chưa được đồng ý.
2. **Xoá:** `python3 $S/xoa_logo.py "<file1>" "<file2>" …` (thư mục cũng được; `--out <thư-mục>` nếu người dùng muốn để kết quả chỗ khác). Đặt mỗi đường dẫn trong dấu nháy kép. Ảnh vài giây, video 20-40 giây mỗi file: chạy lệnh với timeout dài (10 phút) cho video.
3. **Video: xem góc logo.** Mỗi video `✓` có dòng `xem góc logo: <ảnh>`. Mở ảnh đó (hàng trên bản gốc, hàng dưới bản đã xoá, 5 mốc). Video Veo/Flow thường còn **một dấu sao nhỏ nhấp nháy** chéo xuống bên phải chỗ dấu lớn, gwr không xoá dấu này.
   - Hàng dưới còn dấu sao nhỏ, góc là nền trơn (tường, vải, trời, không có cạnh hay vật đi qua ô đó): `python3 $S/xoa_logo.py sao-nho "<file gốc>" "<file _sach>"`, rồi mở lại ảnh góc mới in ra để chắc đã sạch.
   - Góc có cạnh rõ hoặc vật/tay đi ngang ô dấu nhỏ: **không** chạy `sao-nho` (delogo để lại vết nhoè hình ô vuông). Báo người dùng dấu sao nhỏ còn lại và vì sao.
   - Hàng dưới sạch: thôi.
4. **Báo lại** ngắn, bằng ngôn ngữ người dùng đang viết (thường là tiếng Việt), kể cả các dòng trạng thái giữa chừng: mỗi file `✓` (đường dẫn file kết quả `<tên>_sach.<đuôi>`, nằm cạnh file gốc; có xoá thêm dấu sao nhỏ không), `–` không thấy logo nên giữ nguyên, `✗` lỗi kèm lý do thật. Không mở file kết quả trừ khi được bảo.

## Lưu ý
- Chỉ xoá dấu sao **nhìn thấy được** của Gemini/Veo (góc dưới phải; dấu nhỏ nhấp nháy của Veo xoá bằng `sao-nho` khi nền trơn). Không xoá SynthID (dấu ẩn trong điểm ảnh) và không xoá logo của hãng khác.
- File gốc không bị sửa; kết quả không ghi đè bản cũ (`_sach2`, `_sach3`…).
- Mọi thứ chạy trên máy, không tải file lên đâu. Chỉ dùng cho ảnh/video của chính người dùng.
- gwr cố định phiên bản 1.0.46 (đã audit, commit ddd67a7), sharp 0.35.5; cài bằng `npm ci --ignore-scripts`.
