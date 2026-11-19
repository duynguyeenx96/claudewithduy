---
name: re-map-video
description: Làm video vị trí bất động sản dạng 3D map (9:16) từ tên dự án hoặc link Google Maps — bản đồ vệ tinh nghiêng 3D, camera bay tới từng tiện ích, pin + tuyến đường + thẻ ảnh + km/phút, Metro, CTA "Liên hệ báo giá". Có 3 chế độ âm thanh - nhạc nền, AI voice (full AI), hoặc A-roll sale nói thu nhỏ ở góc. Trigger: /re-map-video:re-map-video <tên dự án | link Google Maps> [yêu cầu thêm], hoặc khi người dùng muốn "làm video vị trí / liên kết vùng dự án".
---

# re-map-video — video vị trí dự án BĐS dạng 3D map

Output: project HyperFrames (Three.js + GSAP) → MP4 1080x1920, ~50–60s.
Phong cách: bản đồ vệ tinh, pin đỏ, nhãn xanh ngọc viền vàng, tiêu đề serif trắng/vàng.

Thư mục skill: `SK="${CLAUDE_SKILL_DIR}"` (đường dẫn tuyệt đối). Cần Python 3 + Pillow (`python3 -m pip install -r "$SK/requirements.txt"`), Node.js, FFmpeg.
- `scripts/resolve.py` — link/tên → toạ độ; `--nearby` để tra tiện ích quanh dự án
- `scripts/build_data.py` — OSRM route + km/phút, ảnh vệ tinh ESRI nhiều tầng zoom, Metro (Overpass), tải ảnh tiện ích → `assets/data.js`
- `scripts/make_html.py` — tính timing, chép template, chèn hero / A-roll / audio → `index.html`
- `template/` — composition (camera 3D, mây, pin, nhãn tự né chồng, thẻ ảnh, tiêu đề) + fonts OFL + mây

Dự án đặt tại `re-map-videos/<slug>/` trong thư mục làm việc hiện tại (hỏi nếu người dùng muốn chỗ khác).
Luôn chạy python với `-I`. Chạy HyperFrames qua `npx --yes hyperframes@<pin> ...` (xem package.json của project).

## Quy tắc nội dung (bắt buộc)

- **KHÔNG đưa mặt bằng căn hộ / mặt bằng tầng** vào video, kể cả khi tìm thấy trên mạng.
- Ảnh phối cảnh / logo dự án chỉ dùng ảnh **người dùng cung cấp** (`hero`). Không tự tải ảnh phối cảnh từ báo/web của chủ đầu tư; không vượt chặn anti-bot.
- Ảnh tiện ích: Wikimedia Commons (CC0/PD/CC BY/CC BY-SA) — ghi `credit`; credits hiện ở cảnh cuối. Không có ảnh mở → bỏ thẻ ảnh, chỉ để pin + nhãn.
- Km lấy từ OSRM (đường lái xe thực). Phút = max(OSRM, km / city_speed_kmh) — OSRM là tốc độ thông thoáng, quá lạc quan cho TP.HCM. Luôn hiển thị "~". Không chép số "5 phút tới…" từ tin môi giới.
- Xác minh tiện ích bằng toạ độ thật (tin rao hay sai: vd "cách Vincom 1 km" thực tế 6 km).

## Quy trình

1. **Toạ độ**: `python3 -I "$SK/scripts/resolve.py" "<link hoặc tên>"`. Link `maps.app.goo.gl` được theo redirect, lấy `!3d!4d` (pin chính xác). Tên không ra → xin link Google Maps.
2. **Tiện ích** (5–7 điểm, đa dạng nhóm): metro/ga, bệnh viện, trường/ĐH, TTTM, sân bay, trung tâm (Q1)… Tra bằng `"$SK/scripts/resolve.py" --nearby <lat> <lon> "tên 1" "tên 2"…`. Ưu tiên điểm gần (<8 km) + 1–2 điểm "liên vùng" xa. Thêm 1 dòng tìm hiểu dự án (WebSearch) để lấy tên phường, tagline nếu có — đánh dấu thông tin chưa kiểm chứng.
   Ảnh: tìm trên Commons API (`generator=search`, `prop=imageinfo`, `iiprop=url|extmetadata`), chọn ảnh ngoại thất rõ, ghi license.
3. **Scaffold**: `npx --yes hyperframes init <slug> --example blank --resolution portrait --non-interactive --skip-skills` trong `re-map-videos/`, rồi viết `project.json` (schema dưới). `.gitignore`: `.tilecache/`, `renders/`.
4. **Dữ liệu**: `python3 -I "$SK/scripts/build_data.py" <project>` (~1–2 phút, ~700 tile ESRI, cache ở `.tilecache/`).
5. **Lắp HTML**: `python3 -I "$SK/scripts/make_html.py" <project>`.
6. **Kiểm tra**: `lint` → `snapshot --at <giữa mỗi beat>` (xem contact-sheet) → `check` phải 0 error. Lỗi hay gặp: nhãn đè tiêu đề (culling đã có), pin bị thẻ ảnh che (camera close-up phải nhắm đúng POI).
7. **Render**: `npx --yes hyperframes@<pin> render -o renders/<slug>.mp4` (~1–3 phút cho 54s). Mở Studio preview trước khi render bản giao nếu người dùng muốn sửa tay.

## project.json

```json
{
  "name": "TÊN DỰ ÁN", "tagline": "…", "address": "Phường … · …",
  "center": [lat, lon], "cta": "LIÊN HỆ BÁO GIÁ", "outro_title": ["KẾT NỐI", "TRỌN VẸN"],
  "city_speed_kmh": 35,
  "timing": {"intro": 5, "beat": 7, "outro": 7},
  "hero": {"src": "assets/hero.jpg", "dur": 2.8},          // tuỳ chọn: ảnh phối cảnh do user đưa
  "music": {"src": "assets/audio/bgm.mp3", "volume": 0.5},   // tuỳ chọn
  "voiceover": [{"src": "assets/audio/vo_0.mp3", "start": 0.4}],
  "aroll": null,
  "pois": [
    {"id": "suoitien", "top": "GA METRO SỐ 1", "label": "BẾN XE SUỐI TIÊN", "short": "Ga Bến xe Suối Tiên",
     "lat": 10.8795, "lon": 106.814, "icon": "metro|hospital|school|shop|plane|city|home",
     "headline": ["KẾT NỐI", "METRO SỐ 1"], "photo": "<commons url>", "credit": "…", "dur": 7}
  ],
  "metro": {"label": "METRO SỐ 1", "bbox": [s, w, n, e], "from": [lat, lon], "to": [lat, lon]}   // tuỳ chọn
}
```
Headline 2 dòng, mỗi dòng ≤ 14 ký tự (font 96px, khung 888px). `label` ≤ 20 ký tự.

## Ba chế độ âm thanh

- **music** (mặc định): nhạc nền. Lấy nhạc qua `/media-use` (`media-use resolve --type bgm --intent "luxury real estate cinematic, calm piano + strings"`) — cần `npx hyperframes auth login` (miễn phí). Không có → render không tiếng, báo người dùng.
- **ai_voice** (full AI): viết 1 câu thoại / beat (intro, mỗi tiện ích, outro; ~12–18 từ, giọng tư vấn), tạo TTS tiếng Việt qua `/media-use` (voice) hoặc `npx hyperframes tts`. Đặt `pois[i].dur = max(7, độ dài câu + 1.2)` rồi khai `voiceover` với `start` = đầu beat + 0.4. Thêm nhạc nền volume 0.25.
- **aroll** (sale nói): user đưa clip quay dọc. `npx hyperframes transcribe <clip>` → tìm thời điểm sale nhắc từng tiện ích → điền
  `"aroll": {"src": "assets/aroll.mp4", "shape": "circle"|"rect", "beats": {"suoitien": 6.2, "hoanmy": 14.8, …}, "outro": 48.0}`.
  Tổng thời lượng = độ dài clip; mỗi beat chạy theo lời thoại. Khung người nói nằm góc phải-dưới (330px, viền vàng) phía trên vùng UI TikTok; tiếng lấy từ clip. Nếu clip có nền rối, có thể tách nền bằng `npx hyperframes remove-background`.

## Kỹ thuật (để sửa template)

- Hệ toạ độ: mét, gốc = dự án, X = đông, Z = nam (Web Mercator z17 × m/px). Layer ảnh = mặt phẳng Three.js, viền mềm bằng alphaMap; render theo `renderOrder` (không depth).
- Camera: keyframe {x, z, d, tilt, bearing}, nội suy easeInOutCubic, `d` nội suy theo log. Mỗi beat: pair shot (dự án + POI) → close-up POI (1.5 km gần / 3 km xa) → drift.
- Overlay (pin, nhãn, route SVG, metro, card, connector) chiếu 3D→2D mỗi frame trong `renderAt(t)`; được gọi bởi tween proxy của GSAP và sự kiện `hf-seek` — deterministic, không dùng clock.
- Kích thước nhãn đo 1 lần sau `document.fonts.ready` (lint cấm đo DOM trong callback); timeline đăng ký sau đó.
- Vùng an toàn 9:16: tiêu đề top 1040, brand top 160/right 120, card 240–740; nhãn bị ẩn nếu rơi vào vùng tiêu đề/brand hoặc chồng nhau.
