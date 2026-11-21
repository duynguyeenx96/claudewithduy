---
name: re-map-video
description: Làm video bất động sản dạng 3D map (9:16) từ tên dự án hoặc link Google Maps — 2 kiểu: VỊ TRÍ (mặc định) và QUY MÔ dự án (viền khu đất vẽ trên ảnh vệ tinh, đếm diện tích, đo dài/rộng, quy ra số sân bóng, phân khu, bảng thông số). Kiểu vị trí: bản đồ vệ tinh nghiêng 3D, camera bay tới từng tiện ích, pin + tuyến đường + thẻ ảnh + km/phút, Metro, CTA "Liên hệ báo giá". Có 3 chế độ âm thanh - nhạc nền, AI voice (full AI), hoặc A-roll sale nói thu nhỏ ở góc. Trigger: /re-map-video:re-map-video <tên dự án | link Google Maps> [yêu cầu thêm], hoặc khi người dùng muốn "làm video vị trí / liên kết vùng dự án" hay "video quy mô / diện tích / ranh giới dự án, đất nền".
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
   Bản giao: nén lại Full HD 1080x1920 khoảng 40 MB/phút (render gốc ~200 MB/phút vì ảnh vệ tinh nhiều chi tiết):
   `ffmpeg -i renders/<slug>.mp4 -c:v libx264 -preset slow -crf 23 -maxrate 6M -bufsize 12M -pix_fmt yuv420p -c:a aac -b:a 160k -af loudnorm=I=-14:TP=-1.5:LRA=11 -movflags +faststart renders/<slug>_fhd.mp4`

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
- **Kịch bản thoại (ai_voice / aroll gợi ý)**: một mạch tư vấn, không đọc rời từng cảnh.
  - Intro = hook dạng câu hỏi về lợi thế lớn nhất (vd "Ở Dĩ An, nhưng vào trung tâm chỉ bằng một chuyến metro?").
  - Chọn 1 lợi thế xuyên suốt (metro, cao tốc, sông…) và quay lại nó ở điểm xa: không đọc "cách 21 km" trơ trọi mà nói cách đi nhanh
    (vd "lên metro ở Suối Tiên, khoảng 30 phút tới Bến Thành"). Đổi luôn `headline` + `sub` của beat đó cho khớp lời.
  - Mỗi tiện ích = 1 nhu cầu của người mua (con nhỏ/người già → bệnh viện; con đi học → trường; cuối tuần → TTTM; công tác → sân bay).
  - Ưu tiên nói phút thay vì km. Outro = tóm lợi thế + CTA hành động cụ thể ("Bình luận chữ giá, mình gửi bảng giá…").
  - Không bịa giá, tiến độ, pháp lý. Số liệu metro / cao tốc lấy từ nguồn công khai và báo người dùng kiểm lại.
  - Tên tiếng Anh: thử vài cách viết rồi nghe lại bằng Whisper (vd "Bcons" → viết "Bi-cons").
  - **Trước khi viết thoại: đọc từ điển phát âm dùng chung `~/.zerotts/voice_dict.json`** (cách viết tên riêng / viết tắt / đơn vị đã kiểm bằng Whisper; máy mới thì `tts.py` tự chép `voice_dict.seed.json` sang). Tên mới chưa có → thử 3–4 cách viết,
    gen, chép lại bằng Whisper, cách đúng thì **thêm vào `words` với `"verified": true`** để lần sau khỏi thử lại.
  - Giọng tiếng Việt offline: ZeroTTS. Gen bằng `scripts/tts.py` (tự áp dụng dict, đổi số/đơn vị ra chữ; `--dry` để xem câu sẽ đọc):
    `PYTTS=$(bash "$SK/scripts/setup_tts.sh" | tail -1 | sed 's/^READY //')` (lần đầu tạo venv riêng của plugin và cài `zerotts`; model + giọng tự tải từ Hugging Face `zeroweight-ai/ZeroTTS` lần chạy đầu), rồi
    `"$PYTTS" -I "$SK/scripts/tts.py" <project>/assets/audio <project>/vo_lines.json --voice baotrang`. Có sẵn model ở máy thì đặt `ZEROTTS_MODEL=<thư mục>`.
    Giọng: `baotrang` (nữ, tin tức), `maichi` (nữ, nhẹ nhàng), `kimoanh` (nữ, ấm), `quangminh` (nam, tin tức), `tiendat` (nam, sôi nổi)… Beat = max(6, độ dài câu + 0.9).
- **Nhạc nền không cần đăng nhập**: 3 bài FreePD (CC0) kèm gói ở `$SK/assets/music/`: `city-sunshine`, `happy-whistling-ukulele`, `inspiration` (nhịp nhanh, vui, mỗi bài 100s). Dùng 1 trong 3; `make_scale.py` nhận thẳng tên bài trong `"music": {"source": "city-sunshine"}`, còn `make_html.py` thì cắt bằng ffmpeg vào `assets/audio/bgm.m4a`. Người dùng đưa nhạc riêng thì dùng file đó. Cắt đúng tổng thời lượng, fade in 0.6s / out 2.5s. Có giọng đọc: `volume` 0.1 (nhạc thấp hơn giọng ~18 dB); chỉ nhạc: 0.5.
- `pois[i].sub` (tuỳ chọn) thay dòng phụ mặc định "tên · km · phút".
- **ai_voice** (full AI): viết 1 câu thoại / beat (intro, mỗi tiện ích, outro; ~12–18 từ, giọng tư vấn), tạo TTS bằng `scripts/tts.py` (ZeroTTS, xem trên). Đặt `pois[i].dur = max(7, độ dài câu + 1.2)` rồi khai `voiceover` với `start` = đầu beat + 0.4. Thêm nhạc nền volume 0.1.
- **aroll** (sale nói): user đưa clip quay dọc. `npx hyperframes transcribe <clip>` → tìm thời điểm sale nhắc từng tiện ích → điền
  `"aroll": {"src": "assets/aroll.mp4", "shape": "circle"|"rect", "beats": {"suoitien": 6.2, "hoanmy": 14.8, …}, "outro": 48.0}`.
  Tổng thời lượng = độ dài clip; mỗi beat chạy theo lời thoại. Khung người nói nằm góc phải-dưới (330px, viền vàng) phía trên vùng UI TikTok; tiếng lấy từ clip. Nếu clip có nền rối, có thể tách nền bằng `npx hyperframes remove-background`.

## Chế độ aroll_ui (sale đứng ở dự án nói, thỉnh thoảng hiện thông số)

Nguyên tắc: **người nói full khung phần lớn thời gian, mặt chỉ ở 2 vị trí** (full khung, hoặc ô vuông bo góc cố định góc phải khi cắt sang bản đồ).
Không đổi kiểu liên tục, không dời mặt khắp nơi, không zoom sát mặt. Mỗi lần nhắc tiện ích phải **thấy được thông tin** (ảnh, phút, km), không chỉ đổi hiệu ứng.

1. Bản đồ B-roll: dựng project bản đồ với timing khớp lời nói (beat = câu nhắc tiện ích), ẩn `#texts,#brand,#credits` (giữ thẻ ảnh, pin, tuyến)
   bằng `<style>…{display:none !important}</style>` rồi render → `assets/map.mp4`. Thời gian bản đồ = thời gian video.
2. A-roll dọc 1080x1920 → `assets/aroll.mp4` (giữ tiếng). Chép lời từng từ, tìm chỗ sale nhắc từng tiện ích.
3. `aroll_ui.json` (schema ở đầu `scripts/make_aroll_ui.py`):
   - `title` thẻ tên dự án lúc mở đầu.
   - `info` thẻ ảnh + kicker + tên + số phút + km, nằm trên đầu; người nói giữ nguyên. Dùng cho đa số tiện ích.
   - `cutaway` bản đồ full + bảng chữ trái + người nói trong ô bo góc phải. Chỉ 1–2 điểm mạnh nhất (vd Metro, đường về trung tâm).
   - `cta` nền tối dần + "Bình luận GIÁ" + nút. Phụ đề tự tắt khi CTA hiện.
   Số trên màn hình lấy từ data.js (OSRM), không lấy theo lời nói. `face` = tâm mặt trên A-roll.
4. `python3 -I "$SK/scripts/make_aroll_ui.py" <project>` → snapshot → render → nén Full HD. Render ~8 phút cho 56s (giải mã nhiều luồng video).

## Chế độ scale (quy mô dự án)

Dùng khi người dùng muốn nói về **độ lớn** của dự án / lô đất thay vì tiện ích xung quanh. Không cần tiện ích, không cần OSRM.
Cảnh: bay xuống → viền vàng vẽ quanh khu đất + nền tím + "DIỆN TÍCH x ha" đếm lên → 2 đường đo dài/rộng theo trục chính
→ khu đất lấp đầy ô sân bóng 105×68 m "≈ N SÂN BÓNG ĐÁ" → từng phân khu sáng lên (tuỳ chọn) → bảng thông số (tuỳ chọn) → CTA. ~45–50s.

1. **Ranh giới** (bắt buộc, không được tự vẽ ước chừng rồi ghi diện tích như số thật):
   - OSM: tìm way/relation chứa dự án (Overpass `is_in(lat,lon)` hoặc `way(around:500,…)[landuse][name]`), dùng `{"osm": "way/123"}`.
   - Không có trên OSM → xin người dùng: file KML/GeoJSON (Google My Maps → Xuất) hoặc danh sách toạ độ góc → `{"geojson": "assets/site.geojson"}` / `{"coords": [[lat, lon], …]}`.
   - Lô đất nền nhỏ (vài trăm m²) cũng dùng được: diện tích hiện ha có lẻ; muốn hiện m² thì đặt `headlines.area` và kiểm lại nhãn.
2. **Phân khu** (`zones`, 0–6 cái): polygon OSM có tên bên trong ranh giới (phân khu, công viên `kind: "park"`). Quá nhỏ (<1% tổng) thì bỏ, nhìn không rõ.
3. **Số liệu**: diện tích, kích thước, số sân bóng tính từ polygon. `area_ha` = số chủ đầu tư công bố (nếu có, ghi nguồn) — tiêu đề dùng số này, sân bóng quy đổi theo số này.
   `stats` (≤4 ô) chỉ lấy số có nguồn công khai, nguồn lệch nhau thì làm tròn xuống kiểu "70+". Không bịa giá, pháp lý, tiến độ.
4. `python3 -I "$SK/scripts/build_scale.py" <project>` → `python3 -I "$SK/scripts/make_scale.py" <project>` → snapshot (giữa mỗi cảnh) → check → render → nén như trên.

```json
{
  "mode": "scale", "name": "…", "tagline": "…", "address": "…", "kicker": "QUY MÔ ĐẠI ĐÔ THỊ",
  "center": [lat, lon],
  "boundary": {"osm": "way/1223373335"},
  "area_ha": 271,
  "zones": [{"osm": "way/…", "label": "Phân khu Beverly", "kind": "zone|park"}],
  "headlines": {"area": ["QUY MÔ", "271 HA"], "dims": [...], "pitch": [...], "zones": ["NHIỀU", "PHÂN KHU"]},
  "stats": [{"value": 36, "unit": "ha", "label": "Công viên trung tâm", "prefix": "", "suffix": ""}],
  "outro_title": ["QUY MÔ", "ĐẠI ĐÔ THỊ"], "cta": "LIÊN HỆ BÁO GIÁ",
  "credits_extra": "Số liệu dự án theo công bố của chủ đầu tư",
  "timing": {"intro": 4.5, "area": 6.5, "dims": 5.5, "pitch": 5.5, "zone": 2.6, "stats": 6, "outro": 6.5},
  "music": {"src": "assets/audio/bgm.m4a", "volume": 0.5}
}
```
Camera tự xoay để trục dài khu đất nằm dọc khung 9:16 và đặt khu đất ở nửa trên (chừa chỗ chữ). Voiceover: viết 1 câu / cảnh, chỉnh `timing` theo độ dài câu.

## Kỹ thuật (để sửa template)

- Hệ toạ độ: mét, gốc = dự án, X = đông, Z = nam (Web Mercator z17 × m/px). Layer ảnh = mặt phẳng Three.js, viền mềm bằng alphaMap; render theo `renderOrder` (không depth).
- Camera: keyframe {x, z, d, tilt, bearing}, nội suy easeInOutCubic, `d` nội suy theo log. Mỗi beat: pair shot (dự án + POI) → close-up POI (1.5 km gần / 3 km xa) → drift.
- Overlay (pin, nhãn, route SVG, metro, card, connector) chiếu 3D→2D mỗi frame trong `renderAt(t)`; được gọi bởi tween proxy của GSAP và sự kiện `hf-seek` — deterministic, không dùng clock.
- Kích thước nhãn đo 1 lần sau `document.fonts.ready` (lint cấm đo DOM trong callback); timeline đăng ký sau đó.
- Vùng an toàn 9:16: tiêu đề top 1040, brand top 160/right 120, card 240–740; nhãn bị ẩn nếu rơi vào vùng tiêu đề/brand hoặc chồng nhau.
