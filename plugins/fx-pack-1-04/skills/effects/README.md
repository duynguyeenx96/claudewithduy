# FX Pack 1-04 · Thẻ & danh sách (10 hiệu ứng)

Một trong 6 gói tách từ FX Pack 1 (59 hiệu ứng, gói đủ là `fx-pack-1`). Gói này: todo, checklist, apple-toggles, the-bill, lineup, tier-list, glass-widgets, messages, comment-box, tap.

Nguồn: skill `effects` ("claude-video-effects", MIT, © 2026 Vibha Ramprakash, xem `LICENSE`) + 8 hiệu ứng thêm trong `custom/fx_custom.py`.
Model: YuNet (MIT) và MediaPipe Selfie Segmenter (Apache-2.0), xem `models/NOTICE.md`. Phông trong `fonts/` đều OFL.
Chép ngày 2026-11-16 từ gói người dùng tải về. Chia sẻ lại cho người khác: giữ `LICENSE` và tên tác giả, không giới thiệu là của mình.

Tự dò mặt + tách người từng khung, nên chữ / ảnh chui được ra sau đầu mà không cần `person.webm`. Chỉ thêm hình, không thêm âm.

## Đã sửa so với bản gốc
- `scripts/fx.py`: xuất `crf 12` (đổi bằng `FX_CRF`), tiếng chép nguyên (`FX_AUDIO=aac` nếu nguồn không phải AAC). Đổi màu hai chiều thêm `accurate_rnd+full_chroma_int` và gắn nhãn bt709: bản gốc làm hình tối đi ~1.3% (Y 132.7 → 130.9) và để trống nhãn màu.
- `custom/fx_vi.py`: chữ có dấu tự đổi sang `fonts/` (BeVietnamPro-Black, PlayfairDisplay-Italic, DancingScript). **Luôn chạy file này**, không chạy `scripts/fx.py`.
- `SKILL.md`: bỏ mục riêng cho Windows. Bảng 51 hiệu ứng và tuỳ chọn vẫn ở đó.

## Chạy
```
FX=<thư mục skill>; PYFX=$(bash $FX/scripts/setup.sh | tail -1 | cut -d' ' -f2-)   # lần đầu tự tạo venv
$PYFX $FX/custom/fx_vi.py --list
$PYFX $FX/custom/fx_vi.py --plan plan.json <vào.mp4> check.png --still 1.6,4.5     # khung kiểm, ~2s mỗi khung
$PYFX $FX/custom/fx_vi.py --plan plan.json <vào.mp4> <ra.mp4>                       # ~4s máy cho 1s video
```
`plan.json`: `{"effects":[{"fx":"backdrop-word","start":2.0,"end":4.0,"text":"CLAUDE"}, ...]}`. Mỗi hiệu ứng 1.5–4s. Danh sách chữ nối bằng `|`.

## Ghép với video dựng bằng HyperFrames
FX Pack là một lần encode hình. Chạy nó lên clip người nói đã cắt lời **trước** khi dựng (đầu ra đưa vào làm A-roll),
không chạy lên mp4 đã render xong. Vùng có hiệu ứng thì không đặt thêm chữ / chip đè lên (một hệ chữ mỗi đoạn).

## Vùng an toàn (x 70–1010, y 250–1500; trong code: `SAFE` ở scripts/fx.py, khung kiểm tự tô đỏ vùng ngoài, tắt bằng `--no-guides`), soát trên clip thử 2026-11-16, đầu ở giữa khung
Vị trí đa số bám theo đầu: đầu càng cao thì thẻ "trên đầu" càng dễ vượt mép trên. **Luôn xuất khung kiểm trước khi render.**

- **Nằm trong vùng:** locked-on, orbit, lean-in, spotlight, moody, todo, shortcut-rain, scribble, broll-split, phone-fan, comment-box, match-cut,
  apple-toggles, led-sign, slow-push, over-the-shoulder-zoom, messages, tape-label, select-resize, wave-trim, huge-strike, crayon-write, fan-build,
  spotlight-type, spotlight-neon, dot-reveal, rabbit-hole, noise, carousel-spin.
- **Chữ vượt mép trên** (dời `y` / `lines_y`, hoặc chỉ dùng khi đầu thấp trong khung): the-bill, pause-point, uninstall, countdown-flip, cover-star,
  split-headline, headline-box, profile-wall, headline-wall, glass-widgets, timeline, cinema, cinema-v1, split-graph, split-graph-v1.
- **Chữ vượt mép dưới** (dưới y 1500, bị caption nền tảng che): swipe, reel-frame, reject-stamp, red-collage, gold-collage, pastel-word, check-pills,
  tier-list, checklist, liquid-glass-graph, glass-widgets (pill "Edited by Claude").
- **Vượt mép phải:** tap (nút Follow nằm trong cột nút nền tảng: đặt `x=0.6`), backdrop-word và lineup với chữ dài (rút chữ).
- **Phủ kín khung** (chấp nhận như một cảnh riêng): place-in-grid, editor.
- `messages` với đầu ở giữa khung che mất mặt ở giây thứ 1–2: dời bằng `y`.

Chữ mặc định của nhiều hiệu ứng là tiếng Anh ("TO DO", "Edited by Claude", "Following", "Messages"): truyền `text` / `title` tiếng Việt, cái nào không đổi được thì cân nhắc bỏ.
