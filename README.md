# Kệ Module

Các skill và tool dựng video tách ra từ flow riêng, đóng gói để ai cũng cài được. Mọi thứ chạy trên máy người dùng.

## Skill (plugin cho Claude Code)

```
/plugin marketplace add duynguyeenx96/ke-module
/plugin install fx-pack@ke-module
```

| Plugin | Làm gì | Hệ điều hành |
|---|---|---|
| `ref-catalog` | Catalog tài nguyên, đối chiếu video tham khảo, kế hoạch remake | mọi HĐH |
| `fx-pack` | 59 hiệu ứng cho video người nói, bám theo mặt | mọi HĐH |
| `capcut-edit` | Auto-edit project CapCut: text theo lời thoại, SFX | chỉ macOS |
| `tool-video` | Short 9:16 review / giới thiệu phần mềm từ A-roll và tư liệu thật, 12 concept, render bằng HyperFrames | mọi HĐH (cần Node.js, FFmpeg) |

Cập nhật: `/plugin update`.

## Tool (kéo thả trên trình duyệt)

Tải `.zip` ở [Releases](https://github.com/duynguyeenx96/ke-module/releases/latest), giải nén, rồi:
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
- **Thêm plugin:** tạo `plugins/<tên>/`, thêm vào `marketplace.json`, thêm module vào `site/src/data/modules.json` (trường `skill.plugin`), chạy `claude plugin validate .`.
- **Ra bản tool:** `git tag tools-v1.0.1 && git push --tags`. CI tự zip và tạo Release.
- **Xem site:** `cd site && npm install && npm run dev`.
- **Deploy:** Cloudflare Pages nối repo, thư mục gốc `site`, lệnh `npm ci && npm run build`, output `dist`. Gắn domain trong mục Custom domains.

## Giấy phép

`fx-pack` gốc từ claude-video-effects (MIT, Vibha Ramprakash), giữ `LICENSE` khi chia sẻ lại. Model và phông kèm theo giấy phép riêng trong `models/NOTICE.md` và `fonts/`.

`tool-video` kèm script của herk-edit-kit (MIT) và EditAtlas (Apache-2.0), bộ SFX CC0 (Kenney, Freesound) và phông Be Vietnam Pro (OFL), xem `plugins/tool-video/skills/tool-video/NOTICE.md`.
