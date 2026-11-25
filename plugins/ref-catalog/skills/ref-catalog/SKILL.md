---
name: ref-catalog
description: Luồng remake từ video tham khảo cho mọi ngách: soạn catalog tài nguyên đang có (bản đồ cho agent), tải video nguồn (link Facebook/TikTok/YouTube/Instagram hoặc file), Claude xem khung hình + nghe tiếng để phân tích, đối chiếu từng thành phần của nguồn với catalog (có / gần giống / thiếu), rồi lập kế hoạch remake theo cảnh và danh sách còn thiếu. Gói tổng quát từ meme-ref, cấu hình được nguồn, trường phân tích và thư mục tài nguyên. Trigger: `/ref-catalog init`, `/ref-catalog library`, `/ref-catalog add <link…>`, `/ref-catalog lib-src add <thư mục>`, `/ref-catalog doctor`, hoặc khi người dùng hỏi plugin đã cài đủ chưa / cần cập nhật gì, hoặc khi người dùng dán link video và muốn "phân tích video này", "mình có đủ tài nguyên làm lại không", "lập catalog tài nguyên", "còn thiếu gì".
---

# /ref-catalog: nguồn tham khảo → đối chiếu tài nguyên → remake

```
[1] Catalog tài nguyên  ──►  bản đồ: mình đang CÓ gì (library.json)
[2] Nguồn: tải + chuẩn bị ──►  video, khung hình, lời nói
[3] Phân tích + đối chiếu ──►  mỗi thành phần của nguồn: có / gần giống / thiếu (trỏ id trong bản đồ)
[4] Kế hoạch remake       ──►  theo cảnh: dùng tài nguyên nào, còn thiếu gì  →  GAPS.md
```

Catalog tài nguyên là **bước chuẩn bị**, làm trước: nó là bản đồ để agent biết mình có gì, nên đối chiếu mới có cơ sở và `match` luôn trỏ vào một `id` có thật.

Bố trí thư mục: **workspace** (nơi plugin ghi) và **nguồn tài nguyên** của người dùng (chỉ đọc, ở đâu cũng được, bao nhiêu cũng được):
```
~/kho-tham-khao/                  ← workspace (thư mục chạy lệnh, hoặc --ws)
├── config.json                   cấu hình: library.sources, niche (tuỳ chọn), Whisper, nhãn đối chiếu, trường phân tích
├── refs/R001/                    mỗi link một thư mục: video.mp4, meta.json, sheet_01..NN.jpg, audio.m4a,
│                                 transcript.json, analysis.json (Claude viết)
├── thumbs/                       ảnh đại diện + grid_NN.jpg của tài nguyên
├── library.json · LIBRARY.md     BẢN ĐỒ tài nguyên: id, nguồn, loại, thời lượng, desc, tags, note
├── catalog.json · CATALOG.md · catalog.csv   catalog các link đã phân tích (kèm độ phủ)
├── GAPS.md                       còn thiếu / gần giống, gom từ mọi link: danh sách đi tìm
└── tai-nguyen/                   (chỉ khi người dùng chưa có kho: lib-src new) video/ anh/ nhac/ sfx/ template/
~/Videos/broll/  ~/Music/ …       ← nguồn tài nguyên có sẵn (lib-src add), plugin chỉ đọc
```

`S=${CLAUDE_SKILL_DIR}/scripts/ref_catalog.py`, thêm `--ws <thư mục>` hoặc `REF_CATALOG_WS` (mặc định thư mục hiện tại). Cần python3 + Pillow, ffmpeg; `yt-dlp` khi tải link; `whisper-cli` + model ggml tuỳ chọn.

## 0. Kiểm tra máy + cấu hình (một lần)
**Lần đầu sau khi cài** (hoặc khi tải lỗi): `python3 $S doctor`. In hệ điều hành, từng công cụ ✓ có / ⚠ cũ hoặc tuỳ chọn / ✗ thiếu kèm phiên bản và lệnh cài đúng hệ điều hành (brew / apt / winget / pip), so yt-dlp và plugin với bản mới nhất. Dòng cuối: `SẴN SÀNG`, `CHẠY ĐƯỢC, nên cập nhật: …` hoặc `THIẾU: …`. Có ✗ thì báo người dùng lệnh cài và dừng; ⚠ yt-dlp cũ thì đề nghị cập nhật trước khi tải (link hay lỗi vì bản cũ). Không tự cài khi người dùng chưa đồng ý.

`python3 $S init <thư mục>` (chưa có `config.json` thì làm trước), rồi:
- **Nguồn tài nguyên: hỏi người dùng, đừng tự đoán.** `python3 $S lib-src` cho biết đã có nguồn nào. Chưa có thì hỏi trước khi làm gì khác: *"Tài nguyên bạn đang có (clip, b-roll, ảnh, nhạc, template…) nằm ở thư mục nào? Bao nhiêu thư mục cũng được, chủ đề gì cũng được."* Mỗi thư mục: `python3 $S lib-src add <thư-mục> label=<tên ngắn>` (ví dụ `label=broll-du-lich`, `label=nhac`). Đừng tự lấy thư mục hiện tại hay một thư mục `library/` có sẵn làm kho khi người dùng chưa xác nhận. Người dùng nói chưa có kho: đề nghị `python3 $S lib-src new` (tạo `tai-nguyen/` trong workspace với video/ anh/ nhac/ sfx/ template/ và thêm làm nguồn) để sau này bỏ thứ tìm được theo GAPS.md vào; lần này đối chiếu ghi toàn `thiếu` (match = null), nói rõ trong báo cáo. Plugin chỉ đọc các thư mục này, không chép, không ghi vào.
- `niche` (tuỳ chọn): một dòng về kênh để chấm "vì sao ăn" sát hơn. Trống thì đánh giá chung, không bắt buộc hỏi.
- `library.extensions`, `match_labels` **theo thứ tự [khớp đúng, thay được, thiếu]** (mặc định `có / gần giống / thiếu`).
- `analysis.fields`: các trường phân tích `{key,label,type,hint}`, đổi theo ngách. `push` bắt buộc đủ khoá. Giữ `matches` và `remake_plan` nếu muốn đối chiếu + lập kế hoạch.
- `transcribe`, `sources.cookies_browser`.

## 1. Soạn catalog tài nguyên (bản đồ)
```bash
python3 $S lib-src            # các nguồn đã chỉ định (thêm: lib-src add <thư-mục> label=…, tạo mới: lib-src new, bỏ: lib-src rm <label>)
python3 $S library            # quét mọi nguồn, thumbs, lưới có tên, thêm mục mới vào library.json
python3 $S lib-check          # mục nào chưa mô tả
python3 $S lib-set <id> "desc=…" "tags=a,b" "note=…"
```
Xem **từng** `thumbs/grid_NN.jpg` (tên in dưới mỗi ô) rồi `lib-set` mô tả thật cho mọi mục chưa có: chủ thể, hành động, nền, độ dài, lưu ý ("nhân vật nhỏ", "đã dùng ở video X"). Mô tả dựa trên hình; tiếng chưa nghe thì ghi "chưa nghe". Chạy lại `library` mỗi khi thêm/xoá tệp hoặc thêm nguồn (mục cũ giữ nguyên mô tả; tệp mất đánh dấu `missing_file`, không còn được đối chiếu). Trùng tên tệp giữa hai thư mục thì id thêm tên thư mục cha. Bản đồ thiếu mô tả thì kết quả đối chiếu không đáng tin: `lib-check` phải sạch trước bước 3.

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

Tìm được tài nguyên thiếu: bỏ vào một thư mục nguồn (hoặc `lib-src add` thư mục mới), chạy lại `library`, `lib-set`, rồi phân tích lại nguồn cũ nếu muốn cập nhật độ phủ.

## Lưu ý
- Dữ liệu nằm hết trong workspace; không gửi gì lên dịch vụ ngoài việc `yt-dlp` tải link và Whisper chạy trên máy.
- `catalog.csv` mở bằng Excel/Google Sheet khi cần chia sẻ hoặc lọc.
- Chỉ tải video bạn có quyền dùng làm tham khảo, đừng đăng lại nguyên bản.
