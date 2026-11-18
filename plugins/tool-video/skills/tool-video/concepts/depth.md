# depth: chữ khổng lồ nằm sau người nói, đổi kiểu khung liên tục

**Hợp với:** A-roll ngồi/đứng nói trước camera trong phòng (nền tường đơn giản), hook mạnh, quảng cáo app/tool, aff.
**Mẫu tham khảo:** reel quảng cáo instories (chữ sau đầu + neon script), reel Cahroom Visuals (chữ theo từng từ kẹp giữa người và nền).
**Bản dựng mẫu:** `templates/depth/index.html` (bản test IMG_8267 người dùng đã duyệt "ok", 4 nhịp × 2.6s).

**Bảng màu = nhóm phối màu theo vòng tròn màu, tính từ chính màu phòng quay** (không dùng màu cố định):
`python3 $SK/scripts/palette.py public/aroll.mp4 --json palette.json` → mỗi nhóm có `base` / `support` / `accent` / `accent2`.

| Nhóm | Hue của màu nhấn | Cảm giác | Dùng khi |
|---|---|---|---|
| `complement` (mặc định) | đối diện màu nền (+180°) | giật mắt nhất | hook, CTA, quảng cáo |
| `splitcomp` | +150° và +210° | tương phản nhưng đỡ gắt, 2 màu nhấn luân phiên | video dài hơn 20s |
| `triad` | +120° và +240° | vui, nhiều năng lượng | tool vui, meme |
| `analog` | ±30° | êm, liền mạch, sang | review nghiêm túc |
| `mono` | cùng hue, chỉ đổi độ sáng | tối giản, cao cấp | ít đồ hoạ |

Quy tắc 60-30-10: footage/nền `base` ~60%, chữ chính `support` ~30%, `accent` ≤ 10% (một chữ script hoặc một dòng, sticker).
Nền lạnh (tím, xanh) thì accent nóng (vàng chanh, cam) để chữ nhảy ra trước. Chữ luôn đặt trên vùng tường tối, không đặt chữ sáng trên áo sáng.

**Chuẩn bị footage:**
- iPhone quay HDR (Dolby Vision / HLG, 10-bit, HEVC, xoay 90°): ffmpeg ở máy này **không có zscale** nên không tonemap được →
  `avconvert --preset PresetHighestQuality --source in.mov --output sdr.mov` (ra H.264 bt709, đã xoay đứng), rồi scale 1080×1920 crf 12.
- Tách người: `npx hyperframes remove-background public/aroll.mp4 -o public/person.webm --quality best` (CoreML, ~6 fps).
  Viền tóc sạch, không răng cưa như SAM2. Kiểm tra 1 khung ghép trên nền xanh lá trước khi dựng.

**Bố cục (3 lớp chồng):** `#cam-bg` (aroll.mp4) → lớp chữ `.behind` → `#cam-fg` (person.webm) → lớp chữ `.front`.
Hai lớp cam **luôn tween cùng nhau** (`[ "#cam-bg", "#cam-fg" ]`, cùng `transform-origin` ở mặt) để người và nền không lệch.
Chữ `.behind` cần `data-layout-allow-occlusion` (cố ý bị người che), chữ viền thì cho `color` = màu `base` (không để transparent, check báo lỗi).

**Nhịp:** đổi kiểu khung mỗi **2.5–3s**, chuyển bằng whip-zoom: `blur 16px + scale +0.08` trong 0.12s → đặt kiểu mới → hết blur trong 0.22s.
Có lời thoại thì đặt mốc đổi kiểu vào đầu câu/cụm (theo transcript), chữ sau người hiện đúng lúc nói từ đó.

**Kiểu khung có sẵn (luân phiên, không lặp 2 lần liền):**
- **punch-in**: zoom 1.22→1.32 sát mặt, 1 chữ Anton ~560px sau đầu (đầu che nửa dưới chữ), script `accent` phía trước ở ngực.
- **tường chữ**: khung rộng 1.0→1.06 nghiêng nhẹ, 6–7 dòng chữ lặp (đặc `support` xen viền `accent`) trượt ngược chiều, pill `accent` ở dưới.
- **card trước/sau**: footage thu vào card bo góc 70px (scale 0.62) trên nền gradient `base`, card "Trước" nhạt màu nghiêng bên cạnh, tag chấm đỏ/xanh.
- **2 dòng chồng**: full khung nghiêng -2°→0, dòng 1 `support` + dòng 2 `accent` sau đầu, sticker sao xoay chậm, script trắng phía dưới.

**Font:** Anton (chữ lớn, có dấu tiếng Việt), Dancing Script (script), Be Vietnam Pro Bold (pill, tag). Tải từ github google/fonts vào `public/fonts/`.
Chữ có dấu phía trên (Ỉ, Ố, Ứ…) cần `line-height ≥ 1.1` và cách mép trên ≥ 80px, không thì dấu bị cắt ("CHỈ" thành "CHÍ").

**Chuyển cảnh:** whip-zoom blur. **Nhạc:** trap/phonk hoặc hyperpop, SFX whoosh ở mỗi lần đổi kiểu (khi người dùng cho thêm SFX).

**Đừng lạm dụng (người dùng chê bản C013 hành trình aff, 2026-10-28: "cứng nhắc, sợ luôn"):** với vlog nói chuyện dài (> 30s),
không đổi kiểu mỗi 3s cả video. Chữ sau đầu chỉ cho ~5–6 câu đinh, giữa các câu đó là footage + phụ đề + chip nhỏ.
Không dùng whip-zoom blur, "tường chữ" lặp và "card trước/sau" cho series này. Bản mẫu 4 nhịp × 2.6s chỉ hợp quảng cáo ngắn.
