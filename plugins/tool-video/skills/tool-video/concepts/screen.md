# screen: quay màn hình là nhân vật chính

**Hợp với:** khi có **bản quay màn hình thật** (đúng sự thật nhất): tutorial "làm X trong 3 bước", demo thao tác, review tính năng mới.
**Cần:** `materials/` có ≥ 1 file quay màn hình (.mov/.mp4). Không có thì dùng concept khác.

**Bảng màu:** `graphite` (nền #18181b, accent #22d3ee, mặc định) · `cream` (nền #f3efe6, accent #e4572e) · `grape` (nền #1e1033, accent #f472b6).

**Bố cục:** khung thiết bị (MacBook/cửa sổ trình duyệt hoặc iPhone tuỳ tỉ lệ bản quay) chiếm 70% trên, nền màu trơn + nhiễu hạt.
A-roll thu thành **bong bóng tròn** 300px góc dưới trái, viền accent 6px; câu hook và CTA thì bong bóng phóng ra full khung.
Số bước "01 / 02 / 03" chữ to mảnh ở góc trên.

**Thành phần:**
- **Zoom theo con trỏ:** đọc vị trí click trong bản quay (xem frame), zoom 1.6–2.2× vào vùng đó, ease `power3.inOut` 0.5s,
  giữ tới khi xong thao tác rồi lùi ra. Không zoom liên tục, chỉ ở chỗ có thao tác đáng xem.
- **Spotlight:** phủ đen 55% toàn khung, khoét vùng đang nói tới (mask bo góc) + viền accent nhấp nháy.
- **Nhãn chú thích:** pill accent có mũi tên cong chỉ vào nút/ô, chữ ≤ 4 từ.
- **Tăng tốc:** đoạn chờ (render, loading) chạy 4–8× kèm nhãn "⏩ x8" và đồng hồ quay.
- **Kết quả:** khung kết quả trượt ra từ khung thiết bị, phóng to full khung 1.5s.

**Chuyển cảnh:** trượt khung thiết bị sang trái/phải giữa các bước + click/whoosh. **Nhạc:** lo-fi/chill, 0.3.
