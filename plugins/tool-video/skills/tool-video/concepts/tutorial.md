# tutorial: quay màn hình ngang trong khung 9:16, mặt trong ô vuông, phụ đề đối diện ô mặt

**Hợp với:** tutorial / demo thao tác quay màn hình 16:9 (hoặc tỉ lệ MacBook ~1.54:1), tận dụng hai dải đen trên/dưới.
**Khác `screen`:** `screen` có khung thiết bị, bong bóng tròn, spotlight, nhiều hiệu ứng. `tutorial` tĩnh và gọn: bố cục đứng yên cả video.
**Cần:** A-roll mặt **có tiếng** + bản quay màn hình khung ngang (`--screen`, không truyền thì lấy video ngang trong `materials/`). Không có bản quay thì dùng concept khác.
**Bản dựng mẫu:** `templates/tutorial/build.py` (chỉ sửa phần CẤU HÌNH), `scripts/tutorial_prep.py`.

**Bảng màu** (chỉ là màu từ đang nói, nền luôn tối): `sun` #ffd84a (mặc định) · `volt` #c6ff3d · `ice` #5ac8ff.

## Bố cục (1080×1920, tính tự động theo tỉ lệ bản quay)
- `FACE_POS=bottom` (mặc định, theo phác thảo của người dùng): màn hình rộng hết khung, ô mặt ngay dưới. Đáy ô mặt = y 1500.
- `FACE_POS=top`: ô mặt y 250–630, màn hình ngay dưới.
- Ô mặt 380×380 ở x 70, bo góc 24. Phụ đề căn giữa theo chiều dọc của ô mặt, ở phía đối diện theo trục X.
  `FACE_SIDE=right` đổi bên, nhưng ở `bottom` ô mặt nằm sát cột nút TikTok nên chỉ dùng khi có lý do.
- Cột phụ đề: `bottom` x 490–900 (né cột nút phải), `top` x 490–1010. Cụm ≤ 5 từ, ≤ 3 dòng, căn trái; đo độ rộng bằng font thật, từ dài thì tự giảm cỡ.
  `captions.pos` trong edit.json không áp dụng cho concept này; `hl`, `fg`, `case`, `size`, `per` vẫn áp dụng (`CAP_SIZE`, `CAP_WORDS`).
- Nền: **chính bản quay màn hình**, lấy vùng nhiều chi tiết nhất (2 dải cùng vùng, dải dưới lật lại; cắt cố định dễ rơi vào vùng terminal trống), làm mờ, phủ tối nhẹ (`BG_DIM`), zoom rất chậm (`BG_DRIFT`), để 2 dải trông như video chứ không phải viền đen mà Facebook có thể quét.
  **Không lấy nền từ A-roll:** mặt mờ hiện ở dải trên và sau phụ đề, thành nhiều khuôn mặt (người dùng chê 2026-11-05). Không dùng đen đặc, không phủ tối 78% (ra gần đen).
  Đo 2 dải trên mp4 sau render: phải có độ lệch sáng trong khung và khác biệt giữa các khung, không phẳng. Hai dải không để chữ ngoài vùng an toàn.

## Footage: một lần encode, hai video luôn cùng timeline
```bash
python3 $SK/scripts/tutorial_prep.py --face <a-roll> --screen <bản quay> -o public --offset auto [--keep keep.json] [--crop cx,cy,size]
```
- Chạy script này **thay** bước re-encode A-roll ở mục 1 của SKILL.md. Không chép thành `aroll.mp4` 1080×1920.
- `--keep`: `keep` của edit.json, hoặc `keep_ranges` khi tự cắt (mục 4). Phải qua script này để màn hình cắt đúng cùng các đoạn với mặt. Chép lời lại `public/face.mp4` để lấy transcript.
- `--offset auto` dò bằng tiếng của cả hai file (giờ màn hình = giờ A-roll + offset). Script dừng nếu bản quay không có tiếng hoặc độ tin cậy < 0.3: khi đó xem hai file và truyền `--offset <giây>`. Không đoán.
- Mặt dò tự động, ô vuông đứng yên cả video. Xem snapshot: thiếu đầu hoặc lệch thì truyền `--crop`.
- Bản quay ngắn hơn lời nói thì giữ khung đứng yên, script in rõ từng đoạn: báo lại cho người dùng.

## Chuyển động (người dùng thích gọn, xem `tool-video-minimal-graphics` trong memory)
- Không đổi bố cục, không punch-in, không whip, không sticker. Chỗ cắt A-roll không cần đổi cỡ.
- `ZOOMS`: chỉ zoom màn hình ở chỗ có thao tác đáng xem, 1.4–1.8×, 0.6s `power2.inOut`, giữ tới khi xong thao tác. Bản quay nhiều chữ nhỏ thì có zoom ở các chỗ chính; khung 1080 không đọc được chữ terminal.
- `STEPS`: nhãn bước tuỳ chọn ở dải trống (`bottom`: phía trên màn hình; `top`: phía dưới), chỉ có chữ, không số tròn/icon.
- Quy tắc "cứ 1.5–2.5s có thay đổi hình" và "mặt ≥ 35%" ở mục 4 của SKILL.md không áp dụng.

## Âm thanh
Giọng nằm trong `face.mp4`. Nhạc 0.15: `ffmpeg -stream_loop -1 -i public/audio/music.m4a -t <độ dài> -c copy public/audio/music_loop.m4a`. SFX chỉ `pop` nhỏ khi hiện nhãn bước.

## Kiểm tra
Snapshot của hyperframes bản mới nằm ở `public/.hyperframes/artifacts/snapshots/<id>/`, chạy `safezone.py` trên thư mục đó.
