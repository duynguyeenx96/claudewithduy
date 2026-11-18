# glide: người trượt êm sang một bên, chữ hiện cạnh đầu, vài câu chữ lớn sau đầu

**Hợp với:** vlog / nói chuyện dài (30s–2 phút) ngồi trước camera trong phòng, series cá nhân (hành trình aff), review nhẹ nhàng.
**Khác `depth`:** `depth` đổi kiểu khung mỗi ~3s (whip blur, tường chữ, card) cho quảng cáo ngắn. `glide` ít chuyển động, chậm, đọc dễ.
**Mẫu tham khảo:** reel quảng cáo Vids.app (FB `share/r/1MszqtECK4`): người đổi khung kèm chữ ở phía còn trống, từ khoá có vòng elip vẽ tay.
**Bản dựng mẫu:** `templates/glide/build.py` (clip test C013 hành trình aff, 2026-10-28, bản v4 người dùng duyệt nhịp).
Phần riêng của clip đó trong file: bảng `FIX`/`PAIRS` sửa chính tả, danh sách `SIDE`, các lệnh `big(...)`/`chip(...)`, `ORIGIN` (vị trí mặt).

**Bảng màu:** như `depth`, tính từ màu phòng: `python3 $SK/scripts/palette.py public/aroll.mp4 --json palette.json`;
video > 20s dùng `splitcomp`. Từ khoá cạnh đầu xen kẽ `accent` và một màu vàng ấm (#ffd84a).

**Chuẩn bị footage:** như `depth` (xoay/tonemap, tách người `npx hyperframes remove-background ... --quality best`, kiểm tra khung nền xanh lá).
Đo vị trí mặt trên khung 1080×1920 → `ORIGIN` (transform-origin của cả hai lớp cam, vd `660px 1120px`).

**Lớp:** `#cam-bg` (aroll) → chữ lớn `.behind` → `#cam-fg` (person.webm) → `#leak` → chữ cạnh đầu / chip `#fronts` → phụ đề.
Hai lớp cam luôn tween cùng nhau (`CAMS`).

## Chuyển động người (đã chỉnh qua 3 lần bị chê)
- **Chỉ di chuyển lớn khi có lý do:** chữ cạnh đầu xuất hiện → trượt lệch sang một bên; vào câu chữ lớn sau đầu → về toàn cảnh.
  Không đổi khung theo từng cụm lời (bản v3 51 lần/96s: "dịch chuyển quá nhiều và nhanh, chóng mặt").
- Trượt **0.8s `power2.inOut`**, bắt đầu trước mốc ~0.35s. Không cắt khung tức thì (bản cắt thẳng bị chê "không thấy move"), không blur.
- Hết chữ thì **đứng yên tại chỗ**, lần sau trượt thẳng sang vị trí mới (không trượt đi rồi trượt về).
- Giữa các lần di chuyển chỉ zoom vào rất chậm (+1.5%). Chỗ cắt A-roll: nhích zoom +4% / về 0 trong 0.5s, không dời chỗ.
- Khung: toàn `1.0`, trung `1.12`, lệch `1.28`. Không cận quá ~1.3 khi A-roll 1080p (mềm hình).
- **Giới hạn để mép video không lộ:** với tâm mặt `ox` px, `x ∈ [-(1080-ox)(s-1), ox(s-1)]`. Không zoom nhỏ hơn khung gốc khi đang lệch.
  Mặt lệch phải trong khung gốc thì lệch trái được ít → chữ bên phải đặt chéo phía trên đầu thay vì ngang tầm đầu.
- Mục tiêu: ~15 lần di chuyển / 96s.

## Chữ
- **Chữ cạnh đầu (~9s một lần, ~10 lần / 96s):** đi cặp với khung lệch: người lệch trái → chữ bên phải; lệch phải → chữ bên trái, sát đầu.
  Dòng nhỏ trắng (44px) hiện trước, từ khoá lớn (Be Vietnam Pro 900, ≤118px, rộng ≤430px) bật `back.out` đúng lúc nói,
  vòng elip SVG vẽ dần quanh từ khoá. Nội dung lấy từ lời nói, 1 ý chính.
- **Chữ lớn sau đầu (Anton):** chỉ ~5–6 câu đinh (con số, câu chốt), đầu che một phần dưới chữ. Số thì đếm lên (`toLocaleString('vi-VN')`).
  Cỡ theo `fit(..., ratio=0.58)`; chữ nhỏ (< 380px) đặt cao hơn để đầu không che quá nửa.
- **Chip:** ít, **chỉ có chữ**: không chấm, không ✕/✓, không emoji/icon đứng trước (người dùng ghét kiểu "AI slop").
- Phụ đề cụm ≤ 4 từ, `top` 1380px (đáy ≤ 1500, xem vùng an toàn trong SKILL.md), từ đang nói màu accent.
- Không dùng: tường chữ lặp, card thu nhỏ footage, whip blur, sticker.

## Âm thanh, hiệu ứng
- Light-leak (`#leak`, radial trắng→cyan, `mix-blend-mode:screen`) chỉ 2 lần ở chỗ chuyển đoạn lớn.
- SFX: `pop` nhỏ khi từ khoá bật, `impact` cho 1–2 câu chữ lớn; `SFX_GAIN = 0.5`. Nhạc nền 0.22 (lặp + fade cuối).

## Duyệt
`PREVIEW=30 python3 build.py` dựng 30s đầu để render thử nhịp chuyển động trước khi render cả video.
