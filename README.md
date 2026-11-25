# Claude with Duy

Các skill và tool dựng video tách ra từ flow riêng, đóng gói để ai cũng cài được. Mọi thứ chạy trên máy người dùng.

## Skill (plugin cho Claude Code)

```
/plugin marketplace add duynguyeenx96/claudewithduy
/plugin install fx-pack-1@claudewithduy
```

| Plugin | Làm gì | Hệ điều hành |
|---|---|---|
| `ref-catalog` | Catalog tài nguyên, đối chiếu video tham khảo, kế hoạch remake | mọi HĐH |
| `xoa-logo-gemini` | Xoá dấu sao Gemini/Veo trên ảnh và video (kể cả dấu nhỏ nhấp nháy của Veo), kéo file vào là xong | mọi HĐH (cần Node.js, FFmpeg) |
| `fx-pack-1` | Đủ 59 hiệu ứng cho video người nói, bám theo mặt. Gói nhỏ `fx-pack-1-01` … `06` (~10 mỗi gói): Camera & ánh sáng, Chữ sau đầu, Ảnh & reels quanh đầu, Thẻ & danh sách, Số liệu & dựng, Nhãn & điểm nhấn | mọi HĐH |
| `fx-pack-2` | Đủ 13 hiệu ứng từ registry HyperFrames (caption, số liệu, thanh tên, CTA). Gói nhỏ `fx-pack-2-01` (10), `fx-pack-2-02` (3) | mọi HĐH (cần Node.js) |
| `capcut-edit` | Auto-edit project CapCut: text theo lời thoại, SFX | chỉ macOS |
| `re-map-video` | Video vị trí dự án BĐS 9:16 dạng bản đồ 3D từ tên dự án hoặc link Google Maps | mọi HĐH (cần Node.js, Python 3, FFmpeg) |

Cập nhật: `/plugin update`.

## Tool (kéo thả trên trình duyệt)

Tải `.zip` ở [Releases](https://github.com/duynguyeenx96/claudewithduy/releases/latest), giải nén, rồi:
macOS bấm đúp `*.command` · Windows bấm đúp `start.bat` · Linux `bash start.sh`.

| Tool | Làm gì | Cần |
|---|---|---|
| `chuan-hoa-giong` | Nâng tiếng nói về -16 LUFS, hình giữ nguyên | Python, FFmpeg |
| `xoa-logo-gemini` | Bản web kéo-thả cũ, chỉ xoá dấu sao lớn. Nên dùng plugin `xoa-logo-gemini` ở trên | Python, Node.js |

## Cấu trúc

```
.claude-plugin/marketplace.json   danh sách plugin
plugins/<tên>/                    mỗi plugin: .claude-plugin/plugin.json + skills/
tools/<tên>/                      tool web chạy local
site/                             trang giới thiệu (Astro), dữ liệu ở site/src/data/modules.json
```

## Làm việc thường ngày

- **Sửa skill:** sửa trong `plugins/<tên>/`, tăng `version` trong `plugin.json`, push. Người dùng `/plugin update` là có.
- **Sửa FX Pack:** sửa ở gói đủ (`plugins/fx-pack-1`, `plugins/fx-pack-2`), rồi `python3 tools/split_fx_pack.py` để sinh lại các gói nhỏ `fx-pack-N-0M`. Không sửa tay trong gói nhỏ.
- **Thêm plugin:** tạo `plugins/<tên>/`, thêm vào `marketplace.json`, thêm module vào `site/src/data/modules.json` (trường `skill.plugin`), chạy `claude plugin validate .`.
- **Ra bản tool:** `git tag tools-v1.0.1 && git push --tags`. CI tự zip và tạo Release.
- **Xem site:** `cd site && npm install && npm run dev`.
- **Deploy:** Cloudflare Pages nối repo, thư mục gốc `site`, lệnh `npm ci && npm run build`, output `dist`. Gắn domain trong mục Custom domains.

## Giấy phép

`fx-pack-1` và các gói nhỏ của nó gốc từ claude-video-effects (MIT, Vibha Ramprakash), giữ `LICENSE` khi chia sẻ lại. Model và phông kèm theo giấy phép riêng trong `models/NOTICE.md` và `fonts/`. `fx-pack-2` dùng mẫu registry HyperFrames (Apache-2.0, HeyGen), tải về lúc dựng, xem `NOTICE.md`.

