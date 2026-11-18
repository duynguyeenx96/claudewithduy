# fxreel: "21 hiệu ứng trong 20 giây", mỗi hiệu ứng ~1s ngay trên người nói

**Hợp với:** khoe năng lực dựng / AI (Claude dựng), hook mạnh, kéo comment nhận quà ("Comment EDIT để nhận").
**Mẫu tham khảo:** reel "20 video effects in 20 seconds, built by Claude" (Facebook, 26s, 1:1, 2026-11-13).
Người ngồi trong phòng, đọc liền một mạch tên 20 hiệu ứng, mỗi tên ~1s; cột checklist đánh dấu dần; hiệu ứng thứ 9 là CTA comment
(dài ~2.5s, card comment + 3 dòng chữ trắng); kết bằng "tan biến": người tan thành hạt, còn lại ghế trống.
**Bản mẫu:** `templates/fxreel/build.py` (test IMG_7781, 2026-11-13). Chỉ sửa phần CẤU HÌNH.

**Bảng màu `forest`:** panel `#12281d`, chữ trắng, nhấn `#e6ff5c`, giấy `#f1ece1`. Đổi trong CẤU HÌNH (`PANEL_BG`, `INK`, `ACCENT`, `PAPER`).

## Chuẩn bị
- `public/aroll.mp4` (1080×1920) + `public/person.webm`: `npx hyperframes remove-background public/aroll.mp4 -o public/person.webm --quality best`.
- `public/plate.jpg` (tuỳ chọn, nên có): khung trống không người, cùng góc máy. Có thì "tan biến" để lại ghế trống như mẫu;
  không có thì nền bị làm mờ + tối để bóng người trong A-roll chìm đi (kém hơn).
  Người dùng quay plate chung clip (đọc xong đứng dậy ra khỏi khung, quay tiếp 3s): lấy khung cách cuối 0.5s
  `ffmpeg -sseof -0.5 -i <clip> -frames:v 1 -vf scale=1080:1920 public/plate.jpg`, rồi cắt A-roll kết thúc ~0.4s sau chữ "biến"
  (bỏ đoạn đứng dậy) ngay ở bước encode duy nhất. Xem plate.jpg trước: còn người / bóng người thì lùi thêm.
- `transcript.json` (mảng từ): build.py dò cụm `say` của từng hiệu ứng để đặt mốc bắt đầu; dò thấy < 70% thì chia đều thời lượng.
  Người đọc khác chữ thì sửa cụm `say` hoặc sửa transcript, không sửa nhãn.
- CẤU HÌNH: `FACE` (tâm mặt), `HEAD_TOP` (đỉnh đầu), `BODY` (hộp thân cho hạt), lấy từ 1 khung A-roll. Sai `FACE` thì khung con trỏ, vòng chữ,
  tháp nhãn, lấy nét lệch khỏi đầu.

## Bố cục lớp
`#world` (3D, cho "bung lớp") chứa `#cam-bg` (aroll) → `#behind` (đồ hoạ sau người) → `#cam-fg` (person.webm) → `#front` (đồ hoạ trước + panel).
`#over` nằm trên cùng cho cảnh phủ toàn màn hình (lặn vào chữ, nhát chém, tờ tiền, khung truyện, lên báo, xé giấy).
Video phụ (bản sao người, bản sao A-roll) chỉ chạy trong khoảng của hiệu ứng: `data-start = data-media-start = t0` để khớp khẩu hình.

## 21 hiệu ứng (khoá → làm gì)
| Khoá | Nhãn | Làm gì | Cần |
|---|---|---|---|
| cursor | Con trỏ AI | con trỏ "Claude" kéo khung chọn quanh đầu, số kích thước đếm lên | |
| clones | Nhân bản | 4 bản sao người hiện hai bên, sau người thật | matte |
| dial | Mặt đồng hồ | nền giấy quét vào, mặt đồng hồ chữ "ngày" xoay sau người | matte |
| keys | Bàn phím | bàn phím iOS trồi lên, gõ tên hiệu ứng, phím sáng theo chữ | |
| orbit | Vòng chữ | chữ xoay quanh đầu, nửa sau chui ra sau đầu | matte |
| matrix | Ma trận | nền đen mưa code xanh, người phủ xanh + scanline | matte |
| wall | Tường bài đăng | lưới thumbnail lấp dần từ quanh người, số bài đếm lên | matte |
| dive | Lặn vào chữ | giấy phủ màn hình, chữ khoét lộ video, zoom xuyên vào chữ cái đầu | |
| comment | Comment EDIT | card comment gõ chữ khoá, reply của kênh, 3 dòng CTA | |
| explode | Bung lớp | cả khung nghiêng 3D, nền / người / đồ hoạ tách thành lớp | matte |
| sketch | Chữ phác thảo | nền giấy kẻ dòng, chữ viết tay vẽ nét rồi tô | matte |
| slice | Nhát chém | vệt sáng chéo, khung tách đôi lệch nhau rồi ghép lại | |
| tags | Tháp nhãn | nhãn 5 hiệu ứng trước rơi chồng lên đầu, bị hất đi | |
| focus | Đổi nét | nền nhoè, khung lấy nét quanh mặt, rồi đổi nét sang nền | matte |
| note | Tờ tiền | mặt người trong tờ tiền khắc xanh, mệnh giá đếm lên | |
| voice | Tin nhắn thoại | bong bóng voice note, sóng âm chạy, thời gian chạy | |
| impact | Khung truyện | nền giấy tia tốc độ, người đen trắng kiểu manga, chữ "BÙM!" rung | matte |
| dolly | Dolly zoom | nền thu lại trong khi người phóng to (vertigo) | matte |
| press | Lên báo | trang báo xoay vào, tiêu đề = TITLE, ảnh người halftone | |
| tear | Xé giấy | tờ giấy rơi xuống phủ, xé đôi lộ video | |
| blow | Tan biến | người tan thành hạt bay sang phải | matte, nên có plate |

Muốn bỏ / đổi thứ tự / thêm hiệu ứng: sửa `EFFECTS`. Hiệu ứng trong `WIDE` tạm ẩn cột checklist (che rộng màn hình).
Thêm hiệu ứng mới: viết hàm `fx_<khoá>(i, t0, t1[, label])` cùng kiểu (đẩy HTML vào `behind`/`front`/`over`, tween vào `tl`, âm vào `sfx`);
cần nhãn thì thêm khoá vào `LABELED`.

## Quy tắc
- Cột checklist chỉ có chữ (không chấm, icon, ✓ trước chữ). Mục đang nói = nền trắng chữ tối; đã qua = mờ 45%.
- Không phụ đề: checklist chính là phụ đề (người đọc đúng nhãn).
- Mọi chữ trong vùng an toàn `x 70–1010, y 250–1500`; CTA tránh cột nút phải (`right:180px`).
- Lời CTA ("+40 hiệu ứng nữa", "gửi bạn rồi nhé") phải là thứ người dùng thật sự gửi được; hỏi trước khi dùng.
- SFX: mỗi hiệu ứng tối đa 1–2 âm từ bộ SFX của skill `assets/sfx/kit.json` (mức + điểm neo theo vai, xoay vòng bản; cue = `(vai, mốc hình[, số bản])`), `SFX_GAIN = 0.85`.
  Tiếng thật theo vật: tờ tiền → cash, lên báo / phác thảo → paper, xé giấy → rip, nhát chém → slice, đổi nét → shutter, comment / voice → chat, tan biến → magic.
- Hiệu ứng phủ kín màn hình mà hiệu ứng kế cũng phủ kín (ma trận → tường): `show(..., fade=0)` để không lọt một khung nửa trong suốt.
- Đã kiểm tra trên 1 khung mỗi hiệu ứng (2026-11-13). Chưa render bản đầy đủ: lần đầu render nên xem kỹ "bung lớp" (3D), "lặn vào chữ" và hạt "tan biến".
