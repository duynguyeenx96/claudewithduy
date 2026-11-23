# Claude with Duy

Các skill và tool dựng video tách ra từ flow riêng, đóng gói để ai cũng cài được. Mọi thứ chạy trên máy người dùng.

## Skill (plugin cho Claude Code)

```
/plugin marketplace add duynguyeenx96/claudewithduy
/plugin install fx-free-01@claudewithduy
```

| Plugin | Làm gì | Hệ điều hành |
|---|---|---|
| `ref-catalog` | Catalog tài nguyên, đối chiếu video tham khảo, kế hoạch remake | mọi HĐH |
| `fx-free-01` … `fx-free-06` | 6 gói hiệu ứng miễn phí cho video người nói (59 hiệu ứng, ~10 mỗi gói), bám theo mặt: 01 Camera & ánh sáng, 02 Chữ sau đầu, 03 Ảnh & reels quanh đầu, 04 Thẻ & danh sách, 05 Số liệu & dựng, 06 Nhãn & điểm nhấn | mọi HĐH |
| `capcut-edit` | Auto-edit project CapCut: text theo lời thoại, SFX | chỉ macOS |
| `re-map-video` | Video vị trí dự án BĐS 9:16 dạng bản đồ 3D từ tên dự án hoặc link Google Maps | mọi HĐH (cần Node.js, Python 3, FFmpeg) |

Cập nhật: `/plugin update`.

## Tool (kéo thả trên trình duyệt)

Tải `.zip` ở [Releases](https://github.com/duynguyeenx96/claudewithduy/releases/latest), giải nén, rồi:
macOS bấm đúp `*.command` · Windows bấm đúp `start.bat` · Linux `bash start.sh`.

| Tool | Làm gì | Cần |
|---|---|---|
| `chuan-hoa-giong` | Nâng tiếng nói về -16 LUFS, hình giữ nguyên | Python, FFmpeg |
| `xoa-logo-gemini` | Xoá dấu sao Gemini/Veo nhìn thấy được | Python, Node.js |

## Cấu trúc

```
.claude-plugin/marketplace.json   danh sách plugin
plugins/<tên>/                    mỗi plugin: .claude-plugin/plugin.json + skills/
tools/<tên>/                      tool web chạy local
site/                             trang giới thiệu (Astro), dữ liệu ở site/src/data/modules.json
```

## Làm việc thường ngày

- **Sửa skill:** sửa trong `plugins/<tên>/`, tăng `version` trong `plugin.json`, push. Người dùng `/plugin update` là có.
- **Sửa FX Free:** sửa engine ở `plugins/fx-pack/skills/effects` (nguồn, không có trong marketplace), rồi `python3 tools/split_fx_pack.py` để sinh lại 6 gói.
- **Thêm plugin:** tạo `plugins/<tên>/`, thêm vào `marketplace.json`, thêm module vào `site/src/data/modules.json` (trường `skill.plugin`), chạy `claude plugin validate .`.
- **Ra bản tool:** `git tag tools-v1.0.1 && git push --tags`. CI tự zip và tạo Release.
- **Xem site:** `cd site && npm install && npm run dev`.
- **Deploy:** Cloudflare Pages nối repo, thư mục gốc `site`, lệnh `npm ci && npm run build`, output `dist`. Gắn domain trong mục Custom domains.

## Giấy phép

Các gói `fx-free-*` (nguồn `plugins/fx-pack`) gốc từ claude-video-effects (MIT, Vibha Ramprakash), giữ `LICENSE` khi chia sẻ lại. Model và phông kèm theo giấy phép riêng trong `models/NOTICE.md` và `fonts/`.

