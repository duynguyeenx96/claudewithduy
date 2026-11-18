# split: đồ hoạ nửa trên, người nói nửa dưới

**Hợp với:** giới thiệu website / sản phẩm ra mắt, tin công nghệ nhanh, khi muốn mặt người nói luôn hiện.
**Mẫu:** https://youtube.com/shorts/2xIHR81Z8ik · **Bản dựng mẫu:** `templates/split/build.py` (demo HyperFrames).

**Bảng màu:** `mint` (#0b0d10 / #3df0b4, mặc định) · `violet` (#0d0b14 / #a78bfa) · `amber` (#100d08 / #ffb020).

**Bố cục:** đường seam ở 960px. Nửa trên nền tối có lưới chấm mờ + glow accent; nửa dưới A-roll crop mặt.
Ở các câu nhấn (hook, giá, CTA) A-roll bung ra full khung 1–1.5s rồi thu về. Phụ đề nằm ngay trên seam
(khi full thì dời xuống dưới cằm bằng `tl.set` top).

**Cảnh có sẵn:** burst chữ + tia sáng · trình duyệt zoom vào trang thật · slot machine quay chữ · chồng card xếp tầng ·
số đếm (toLocaleString có dấu phẩy) · CTA nút bấm + con trỏ.

**Chuyển cảnh:** quét ngang theo accent, glitch nhẹ 2 frame, whoosh. **Nhạc:** trap/phonk nhẹ.
