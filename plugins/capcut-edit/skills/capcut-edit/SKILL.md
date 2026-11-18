---
name: capcut-edit
description: Auto-edit một project CapCut (macOS) theo tên - nghe lời thoại, xem frame, rồi thêm text theo lời thoại + vài SFX đơn giản (glitch/thumbnail chỉ khi được yêu cầu, KHÔNG zoom). Chỉ dùng hiệu ứng FREE. Trigger: /capcut-edit <tên project> [yêu cầu thêm]
---

# /capcut-edit

Tự động edit project CapCut trên máy bằng cách sửa trực tiếp file draft JSON.

## Usage

```
/capcut-edit Ugreen stand                          # edit mặc định: text theo lời thoại + vài SFX đơn giản
/capcut-edit Gor  quảng cáo kính cường lực, tông vàng
/capcut-edit ClipTrieuView  chỉ thêm text, không SFX
```

Phần sau tên project là brief/style tuỳ chọn. Nếu tên có khoảng trắng mà không rõ đâu là tên → chạy `list` và khớp với tên project dài nhất.

## Script

`python3 ${CLAUDE_SKILL_DIR}/scripts/capcut.py <cmd>` (gọi là `CC` bên dưới)

| cmd | việc |
|---|---|
| `list` | liệt kê project (tên → folder) |
| `inspect "<tên>"` | tracks/segments, compound, text/anim/transition hiện có, CapCut có đang chạy, các copy draft có đồng bộ không |
| `transcribe "<tên>"` | dựng lại audio đúng timeline (đệ quy compound clip, speed, volume) → whisper-cli tiếng Việt, timestamp = thời gian timeline |
| `frames "<tên>" OUTDIR` | 1 frame / clip của main track → `OUTDIR/grid.jpg` + bảng thời gian |
| `effects` | hiệu ứng đã xác nhận FREE + đã tải trong cache |
| `apply "<tên>" plan.json` | đóng CapCut → backup → áp plan → ghi mọi copy draft → mở lại CapCut |
| `restore "<tên>" BACKUP_DIR` | khôi phục từ backup |

Backup tự động tại `~/Movies/CapCut/capcut-edit-backups/<folder>-<timestamp>/`.

## Workflow

1. `CC list` → xác định đúng project (nếu nhiều kết quả khớp, hỏi lại user). **Không đoán** – lần trước từng sửa nhầm project.
2. `CC inspect` → nắm độ dài, các cú cắt (cut points), clip scale, video có voice không, đã có text/SFX chưa.
3. `CC transcribe` → lời thoại theo timeline. Nếu báo WARNING missing source → báo user (text vẫn làm được nhưng thời gian căn theo cut).
4. `CC frames ... <scratchpad>/frames` → Read `grid.jpg` để hiểu nội dung + chọn vị trí text (né mặt người / sản phẩm).
5. Viết plan JSON (mẫu: `scripts/example_plan.json`) vào scratchpad. Nguyên tắc:
   - **Text**: ngắn, bám lời thoại, 1 câu / đoạn nói, từ khoá highlight. Bắt đầu ~0.1–0.2s sau cut, kết thúc trước cut kế tiếp. Không trùng thời gian giữa các text. **Không để tràn viền**: mỗi dòng ≤ 12–14 ký tự ở size 10–12 (CTA dài thì xuống dòng thay vì để 1 dòng ~20 ký tự); script tự thu nhỏ khi size × số ký tự dòng dài nhất > 150.
   - **Thumbnail**: chỉ thêm khi user yêu cầu (text tên sản phẩm cỡ lớn 0–0.6s, text đầu tiên bắt đầu từ 0.6s).
   - **Vị trí y** (canvas -1..1, dương = lên trên): 0.55 (trên) khi phần dưới có tay/sản phẩm; -0.40 (dưới) khi phần trên là mặt người; CTA ở 0.0. Tránh |y| > 0.75 (UI TikTok).
   - **Style** theo sản phẩm: tech/decor → highlight cyan `#00E5FF`, animation nhanh (0.3s); đồ tiêu dùng/ưu đãi → vàng `#FFD400`.
   - **SFX** (thư mục `~/Documents/Nhạc/71 SFX PACK`): ít và đơn giản – vài whoosh ở cut quan trọng (start = cut - 0.25), accent cho giá/CTA. Không gắn SFX cho mọi text. Có voice → vol 0.35–0.5; không voice → 0.5–0.8. Mỗi `group` là 1 track; cùng group không được chồng nhau.
   - **Zoom**: KHÔNG dùng – không đưa key `zoom` vào plan (user chê keyframe zoom).
   - **Transition glitch**: chỉ khi user yêu cầu. `Mix` (vertical glitch) 0.3s ở 3–5 cut quan trọng. Không đặt ở cut < 0.8s.
6. `CC apply "<tên>" plan.json` → báo user kết quả + đường dẫn backup.

## SFX hay dùng (đã đo điểm bắt đầu âm thanh → dùng `off`)

| file | off | len | dùng cho |
|---|---|---|---|
| `whoosh_kopdinh.wav` | 0.25 | 0.6 | chuyển cảnh |
| `fast-whoosh-118248.mp3` | 0 | 0.6–0.8 | chuyển cảnh |
| `clean-fast-swooshaiff-14784.mp3` | 0 | 0.8 | chuyển cảnh |
| `mixkit-hard-pop-click-2364.wav` | 0 | 0.4 | text pop |
| `keyboard press.mp3` | 0 | 0.39 | text Typewriter |
| `UI Data Loading Sound Effect.mp3` | 0.24 | 1.2 | intro tech |
| `Digital counting.mp3` | 0.66 | 1.2 | số liệu / % |
| `Display Digits 2.wav` / `3.wav` | 0 | 0.35–0.8 | giá, glitch |
| `camera-shutter-6305.mp3` | 0 | 0.34 | flash / cắt nhanh |
| `chaching.mp3` | 0 | 1.4 | giá / mua |
| `correct sfx.mp3` | 0 | 1.2 | ưu điểm / quà tặng |
| `wrong answer.mp3` | 0 | 1.3 | "đắt quá", vấn đề |
| `mouse click.mp3` | 0 | 0.34 | bấm giỏ hàng / CTA |
| `ES_Riser Suction 5 - SFX Producer.mp3` | 0 | 2.9 | build-up trước reveal |

## Quy tắc bắt buộc

- **KHÔNG dùng SFX `Game Menu Select Sound Effect.mp3`** (user chê rẻ tiền). Không rải tiếng pop cho mọi text – chỉ dùng SFX ở vài điểm nhấn.
- **CHỈ dùng hiệu ứng FREE.** Đã xác nhận free: Typewriter (text in), Blur Fade (text out), Mix (transition glitch), Slow Fade (transition). Animation khác → dùng keyframe (`"in": "pop"` hoặc `"slide"`), free 100%. Không thêm DeepGlow / text template / effect chưa xác nhận. Muốn dùng hiệu ứng mới → chạy `CC effects`, chỉ dùng cái có `is_vip=0`.
- **Đóng CapCut trước khi ghi** (script tự quit; nếu không quit được → nhờ user đóng). CapCut đang mở sẽ ghi đè thay đổi.
- Script ghi đồng thời `draft_info.json`, `.bak`, `template-2.tmp` ở root và `Timelines/<main>/`. Nếu root và main timeline lệch nhau → script dừng, nhờ user mở timeline chính rồi đóng CapCut.
- Không xoá / đổi tên project. Không đụng các timeline phụ.
- File cache `Resources/combination/*_audio.m4a` bị CapCut mã hoá – không đọc trực tiếp; `transcribe` tự dựng lại từ file nguồn.

## Ghi chú kỹ thuật

- Đơn vị thời gian trong draft: micro-giây. Keyframe video: `time_offset` theo **source time** (`source_start + t*speed`); keyframe text: tính từ đầu segment.
- Keyframe property: `KFTypeScaleX` (uniform scale), `KFTypePositionX/Y`, `KFTypeRotation`, `KFTypeGlobalAlpha`.
- Transition gắn vào `extra_material_refs` của segment **đứng trước** cut.
- Text material: `content` là JSON `{"styles":[{range, fill, strokes, size, bold, font}], "text"}`; range tính theo ký tự Python.
- Templates (text/audio/transition segment + materials kèm theo) nằm ở `scripts/templates.json`.

## Báo cáo cho user

Bảng text (thời gian + nội dung), danh sách SFX, hiệu ứng nào bị skip (vì không free / chưa tải), đường dẫn backup, và nhắc user mở CapCut kiểm tra (chưa xem render được).

## Cài đặt (gói chia sẻ)

- Chỉ macOS + CapCut bản desktop. Cần `whisper-cli` + model tiếng Việt để bước `transcribe` chạy.
- Thư mục SFX mặc định `~/Documents/Nhạc/71 SFX PACK` là của tác giả, **không kèm trong gói**. Trỏ về thư mục SFX của bạn bằng biến `CAPCUT_SFX_DIR`; không có thì bước SFX tự bỏ qua. Bảng "SFX hay dùng" ở trên chỉ đúng với bộ của tác giả.
- Hiệu ứng chỉ dùng được khi đã tải trong cache CapCut của máy bạn (`CC effects` liệt kê).
