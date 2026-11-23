---
name: fx2
description: FX Pack 2-01 (10 hiệu ứng: dem-so, vong-tien-do, caption-karaoke, chu-giai-ma, ten-gach-chan, ten-co-nhan, thong-bao, terminal, cta-cuoi, may-quay-rec). Gắn hiệu ứng lên A-roll người nói (9:16) bằng các mẫu miễn phí trong registry HyperFrames (Apache-2.0) - caption karaoke, chữ giải mã, số đếm, vòng tiến độ, thông báo, terminal, thanh tên, dải tin, máy quay REC, lóe sáng, sóng chữ, CTA. Dùng chung với FX Pack (hiệu ứng chạy sau đầu). Trigger: /fx2 <a-roll.mp4> [mô tả hiệu ứng muốn gắn]
---

# fx2: hiệu ứng từ registry HyperFrames cho A-roll dọc

Bổ sung cho FX Pack (bộ `effects` gốc của Vibha Ramprakash, MIT, chuyên hiệu ứng chạy sau đầu).
fx2 phủ các nhóm FX Pack chưa có: caption, số liệu, giao diện, thanh tên, CTA, chuyển cảnh, look máy quay.
Mỗi hiệu ứng là một mẫu trong registry HyperFrames (Apache-2.0, © HeyGen). Mẫu được cài lúc build bằng `hyperframes add`,
rồi skill chỉnh chữ, màu và vị trí cho khung 1080x1920. Code registry không được chép vào plugin.

Người dùng thường không rành kỹ thuật: tự chạy lệnh, báo ngắn gọn.

## Quy trình

```bash
SK="${CLAUDE_SKILL_DIR}"
python3 -I "$SK/scripts/transcribe.py" transcribe <a-roll.mp4> -o transcript.json --language vi   # hoặc: srt <file.srt> -o transcript.json
python3 -I "$SK/scripts/build.py" <a-roll.mp4> plan.json <project_dir>     # cài mẫu + dựng index.html
cd <project_dir> && npx --yes hyperframes@0.9.69 snapshot --at <giữa mỗi hiệu ứng>   # xem contact-sheet
npx --yes hyperframes@0.9.69 check        # 0 error mới render
npx --yes hyperframes@0.9.69 render -o renders/out.mp4
```

1. **Lời thoại**: caption cần mốc từng từ. Dùng `scripts/transcribe.py` (cần ffmpeg + whisper-cli: `brew install whisper-cpp`, model `ggml-medium.bin` đặt qua `WHISPER_MODEL`) hoặc đưa file `.srt`.
   Whisper hay bịa ở đoạn im lặng ("subscribe", "Ghiền Mì Gõ"); clip câm thì tự viết `words`.
2. **Chọn hiệu ứng** theo lời thoại: con số → `dem-so`/`vong-tien-do`; liệt kê → `thong-bao`; lệnh, cài đặt → `terminal`;
   giới thiệu → `ten-gach-chan`; câu kết → `cta-cuoi`. Mỗi hiệu ứng 2.5–5s, tối đa 2 hiệu ứng cùng lúc và không chồng vùng.
3. **plan.json** (thời gian tính bằng giây trên A-roll):
```json
{"accent": "#ffd23f", "transcript": "transcript.json",
 "effects": [
   {"fx": "caption-karaoke", "start": 0.3, "end": 5.0},
   {"fx": "dem-so", "start": 0.5, "end": 3.5, "end_value": 250, "suffix": "K"},
   {"fx": "ten-gach-chan", "start": 5.2, "end": 10, "name": "Duy Nguyễn", "role": "Làm video bằng Claude"}
 ]}
```
4. Hiệu ứng có khung cố định (`dem-so`, `vong-tien-do`, `thong-bao`, `terminal`, `cta-cuoi`) đè lên đầu thì thêm `"box": [x, y, w, h]` (toạ độ trên khung 1080x1920) vào hiệu ứng đó để dời chỗ.
5. Soát contact-sheet: chữ không đè mặt, không ra ngoài vùng an toàn (y 170–1580), đủ tương phản trên áo sáng.
6. Render. Muốn kết hợp với FX Pack: chạy FX Pack trước (nó encode A-roll), đưa file ra của nó vào fx2.

## Hiệu ứng (10 trong 13)

| fx | Mẫu registry | Tham số (đều tuỳ chọn) |
|---|---|---|
| `caption-karaoke` | caption-pill-karaoke | lấy từ `transcript`; `words` để tự đặt |
| `chu-giai-ma` | caption-matrix-decode | như trên, `group_size` (mặc định 3 từ/cụm) |
| `dem-so` | count-up | `start_value`, `end_value`, `prefix`, `suffix` |
| `vong-tien-do` | conic-progress-ring | `progress` (0–100) |
| `thong-bao` | notification-stack | `titles`, `bodies` (ngăn bằng dấu phẩy, tối đa 5) |
| `terminal` | code-terminal-run | `command`, `outputs_list` (ngăn bằng `\|`) |
| `ten-gach-chan` | lt-accent-underline | `name`, `role` |
| `ten-co-nhan` | lt-kicker-name | `kicker`, `name` |
| `cta-cuoi` | cta-close | `action`, `button` |
| `may-quay-rec` | camcorder-hud | `date` |

Gói fx-pack-2-01 chỉ có 10 hiệu ứng trên. Các hiệu ứng khác (light-leak, song-do-dam, dai-tin) nằm ở gói khác của FX Pack 2; cả 13 hiệu ứng: `/plugin install fx-pack-2@claudewithduy`. Mô tả và cách ánh xạ nằm ở `recipes.json`. Thêm hiệu ứng mới: tìm bằng
`npx hyperframes catalog --query "<mô tả tiếng Anh>"`, cài thử, rồi viết recipe (box, vars, text, consts, children, css).

## Lưu ý kỹ thuật

- Mỗi lần dùng, build tạo một bản riêng `compositions/fx/fx<n>-<mẫu>.html` và đổi composition id (kể cả chuỗi id trong script),
  nên một mẫu có thể chạy nhiều lần với chữ khác nhau.
- Mẫu đời mới (count-up, cta-close, notification-stack, code-terminal-run, conic-progress-ring) nhận biến qua `data-variable-values`
  và co theo khung chứa (`cq` units). Mẫu khổ ngang 1920x1080 được đổi canvas sang 1080x1920 rồi chỉnh vị trí bằng CSS.
- Font Be Vietnam Pro (OFL) có sẵn trong `template/assets/fonts`. Riêng `song-do-dam` giữ font gốc vì hiệu ứng cần font biến thiên độ đậm.
