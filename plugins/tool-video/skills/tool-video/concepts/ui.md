# ui: mockup giao diện nền trắng

**Hợp với:** tool AI có ô nhập prompt / chat (Google Flow, ChatGPT, Gemini, Kling…), review "tool này làm được gì".
**Mẫu:** https://youtube.com/shorts/RQck4CUKu5g · **Bản dựng mẫu:** `templates/ui/build.py` (demo Google Flow).

**Bảng màu (`--palette`)**
| tên | nền | chữ | accent |
|---|---|---|---|
| `lime` (mặc định) | #f5f5f2 | #111 | #c6ff3d |
| `sky` | #f4f7fb | #0f172a | #4c8df6 |
| `peach` | #fff6ef | #1c1917 | #ff7a45 |

**Bố cục:** A-roll full khung, các card UI trắng bo góc 36px + bóng mềm trồi lên từ giữa, che mặt trong lúc demo,
rút đi khi người nói quay lại. Chip đen bo tròn (icon tròn accent) nằm dưới cằm. Phụ đề trắng viền đen, `top` ~1380px (đáy ≤ 1500).

**Cảnh có sẵn:** hook chữ to "KHOAN!" + chip bị gạch · cửa sổ trình duyệt có video hero · khung chat: gõ prompt từng chữ,
menu chọn model, con trỏ click, ô "Generating…" → lưới video · chip tính năng · dải ảnh/clip trượt ngang · card agent +
pill tool bay quanh · chip "Lưu lại" · outro thanh accent đóng lại.

**Chuyển cảnh:** card scale 1.06→1 + whoosh; pop back.out(2.2) + pop; zoom punch A-roll 1.1–1.18 ở mỗi lần quay lại mặt.
**Nhạc:** pop/electronic vui, 0.35.
