# terminal: dân code / màn hình đen

**Hợp với:** tool cho dev, CLI, AI agent, tự động hoá (Claude Code, HyperFrames, n8n, Cursor), video "hack" năng suất.

**Bảng màu:** `matrix` (#0a0f0a, chữ #b6ffb0, accent #39ff14, mặc định) · `dracula` (#1e1f29, #f8f8f2, accent #bd93f9) · `amber` (#120c02, #ffcc66, accent #ff9f1c).
**Font:** JetBrains Mono / IBM Plex Mono cho code (kiểm tra có dấu tiếng Việt; chữ tiếng Việt vẫn dùng Be Vietnam Pro).

**Bố cục:** A-roll full khung bị phủ scanline + vignette nhẹ. Cửa sổ terminal (thanh tiêu đề 3 chấm) trượt lên chiếm 55% giữa,
nền mờ đục 90%. Phụ đề dạng dòng lệnh `> ...` có con trỏ █ nhấp nháy.

**Thành phần:**
- **Gõ lệnh:** từng ký tự (stagger 0.03s) + tiếng gõ phím, Enter thì log chạy nhanh (dòng xanh ✓, dòng vàng ⚠).
- **Thanh tiến trình ASCII** `[████████░░] 80%`, đồng hồ đếm giây.
- **Diff:** dòng đỏ `-` / xanh `+` trượt vào, highlight dòng quan trọng.
- **Cây thư mục** mọc dần, file mới nhấp nháy.
- **Hook:** màn hình glitch (dịch kênh RGB 3 frame) rồi hiện câu hook như output lỗi `ERROR: bạn vẫn đang làm tay?`.
- **CTA:** `$ npm i …` / `link ở bio` gõ ra, con trỏ nhấp nháy tới hết.

**Chuyển cảnh:** glitch cắt cứng, `clear` màn hình. **Nhạc:** synthwave / darksynth, 0.3. SFX: tiếng gõ phím, beep.
