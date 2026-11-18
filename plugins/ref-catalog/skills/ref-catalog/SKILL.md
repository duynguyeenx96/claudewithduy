---
name: ref-catalog
description: Luồng remake từ video tham khảo cho mọi ngách: soạn catalog tài nguyên đang có (bản đồ cho agent), tải video nguồn (link Facebook/TikTok/YouTube/Instagram hoặc file), Claude xem khung hình + nghe tiếng để phân tích, đối chiếu từng thành phần của nguồn với catalog (có / gần giống / thiếu), rồi lập kế hoạch remake theo cảnh và danh sách còn thiếu. Gói tổng quát từ meme-ref, cấu hình được nguồn, trường phân tích và thư mục tài nguyên. Trigger: `/ref-catalog init`, `/ref-catalog library`, `/ref-catalog add <link…>`, hoặc khi người dùng dán link video và muốn "phân tích video này", "mình có đủ tài nguyên làm lại không", "lập catalog tài nguyên", "còn thiếu gì".
---

# /ref-catalog: nguồn tham khảo → đối chiếu tài nguyên → remake

```
[1] Catalog tài nguyên  ──►  bản đồ: mình đang CÓ gì (library.json)
[2] Nguồn: tải + chuẩn bị ──►  video, khung hình, lời nói
[3] Phân tích + đối chiếu ──►  mỗi thành phần của nguồn: có / gần giống / thiếu (trỏ id trong bản đồ)
[4] Kế hoạch remake       ──►  theo cảnh: dùng tài nguyên nào, còn thiếu gì  →  GAPS.md
```

Catalog tài nguyên là **bước chuẩn bị**, làm trước: nó là bản đồ để agent biết mình có gì, nên đối chiếu mới có cơ sở và `match` luôn trỏ vào một `id` có thật.

Workspace là một thư mục:
```
config.json     cấu hình: niche, cookie, Whisper, thư mục tài nguyên, nhãn đối chiếu, TRƯỜNG PHÂN TÍCH
library/        tài nguyên của bạn (clip, ảnh, nhạc…) + thumbs/ (ảnh đại diện, lưới có tên)
library.json    BẢN ĐỒ tài nguyên: id (= tên tệp không đuôi), loại, thời lượng, desc, tags, note
LIBRARY.md      bản đọc được của library.json
refs/R001/…     video.mp4, meta.json, sheet_NN.jpg, transcript.json, analysis.json
catalog.json, CATALOG.md, catalog.csv   catalog nguồn (kèm độ phủ từng nguồn)
GAPS.md         gom mọi thứ thiếu/gần giống từ các nguồn: danh sách đi tìm
```

`S=${CLAUDE_SKILL_DIR}/scripts/ref_catalog.py`, thêm `--ws <thư mục>` hoặc `REF_CATALOG_WS` (mặc định thư mục hiện tại). Cần python3 + Pillow, ffmpeg; `yt-dlp` khi tải link; `whisper-cli` + model ggml tuỳ chọn.

## 0. Cấu hình nguồn (một lần)
`python3 $S init <thư mục>` rồi sửa `config.json` cùng người dùng:
- `niche`: một dòng về kênh/ngách (dùng để chấm "vì sao ăn", đề xuất remake). Còn là dòng mẫu thì hỏi.
- `library`: thư mục tài nguyên, đuôi tệp, `match_labels` **theo thứ tự [khớp đúng, thay được, thiếu]** (mặc định `có / gần giống / thiếu`).
- `analysis.fields`: các trường phân tích `{key,label,type,hint}`, đổi theo ngách. `push` bắt buộc đủ khoá. Giữ `matches` và `remake_plan` nếu muốn đối chiếu + lập kế hoạch.
- `transcribe`, `sources.cookies_browser`.

## 1. Soạn catalog tài nguyên (bản đồ)
```bash
python3 $S library            # quét, thumbs, lưới có tên, thêm mục mới vào library.json
python3 $S lib-check          # mục nào chưa mô tả
python3 $S lib-set <id> "desc=…" "tags=a,b" "note=…"
```
Xem **từng** `library/thumbs/grid_NN.jpg` (tên in dưới mỗi ô) rồi `lib-set` mô tả thật cho mọi mục chưa có: chủ thể, hành động, nền, độ dài, lưu ý ("nhân vật nhỏ", "đã dùng ở video X"). Mô tả dựa trên hình; tiếng chưa nghe thì ghi "chưa nghe". Chạy lại `library` mỗi khi thêm/xoá tệp (mục cũ giữ nguyên mô tả). Bản đồ thiếu mô tả thì kết quả đối chiếu không đáng tin: `lib-check` phải sạch trước bước 3.

## 2. Thêm nguồn
`python3 $S add <link|file>…` → in ID (R001…), tải, cắt khung có mốc giây, nghe tiếng. Link trùng báo ID cũ. Tải lỗi thì báo lý do thật (riêng tư: nhờ người dùng tải file về rồi `add <file>`); không đoán nội dung khi chưa tải được.

## 3. Phân tích + đối chiếu (Claude tự xem)
Đọc trong `refs/<ID>/`: `meta.json` (thời lượng, mốc cắt, người đăng, view, caption) → **tất cả** `sheet_NN.jpg` (đọc nguyên văn chữ, nhận bố cục/nền/kiểu dựng) → `transcript.json` nếu có (Whisper hay bịa khi chỉ có nhạc/tiếng động: chỉ tin khi nhiều từ liền mạch, có nghĩa). Rồi mở `LIBRARY.md` và đối chiếu **từng thành phần** của nguồn (nhân vật, nền, nhạc, hiệu ứng) với bản đồ:
- `có`: đúng tài nguyên đó (cùng chủ thể, cùng hành động). `match` = id trong `library.json`.
- `gần giống`: khác tệp nhưng thay được. `match` = id tạm dùng.
- `thiếu`: không có. `match` = null, `desc` đủ chi tiết để người dùng đi tìm hoặc làm.

**Không bịa:** không rõ thì ghi `"(không rõ)"`; không điền số liệu không có trong `meta.json`; không bịa id.

Viết `refs/<ID>/analysis.json` (UTF-8) đúng các khoá trong `analysis.fields`, rồi:
```bash
python3 $S push <ID>
```
`push` từ chối nếu thiếu khoá, nhãn sai, `match` không phải id có thật, `thiếu` mà vẫn điền `match`, hoặc cảnh trong `remake_plan` không có `use` mà cũng không ghi `gap`. Sửa rồi push lại. Thành công thì in độ phủ `{có, gần giống, thiếu}` và cập nhật `CATALOG.md`, `catalog.csv`, `GAPS.md`.

## 4. Kế hoạch remake + báo cáo
`remake_plan` là danh sách cảnh `{scene, t, use, gap, note}`: cảnh nào dùng tài nguyên nào (`use` = id), cảnh nào còn trống (`gap`). Trả lời người dùng ngắn mỗi nguồn: hook, kịch bản (bảng cảnh), độ phủ, thiếu gì, độ khó remake. `python3 $S gaps` gom thiếu/gần giống của mọi nguồn để biết nên đi tìm gì trước (cái cần ở nhiều nguồn nhất). Dựng video thật không thuộc skill này: bàn giao `remake_plan` cho bước dựng, chỉ làm khi người dùng bảo.

Tìm được tài nguyên thiếu: bỏ vào `library/`, chạy lại `library`, `lib-set`, rồi phân tích lại nguồn cũ nếu muốn cập nhật độ phủ.

## Lưu ý
- Dữ liệu nằm hết trong workspace; không gửi gì lên dịch vụ ngoài việc `yt-dlp` tải link và Whisper chạy trên máy.
- `catalog.csv` mở bằng Excel/Google Sheet khi cần chia sẻ hoặc lọc.
- Chỉ tải video bạn có quyền dùng làm tham khảo, đừng đăng lại nguyên bản.
