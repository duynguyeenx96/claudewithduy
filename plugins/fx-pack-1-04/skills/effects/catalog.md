# Catalog: hiệu ứng nào cho câu nào

Dùng file này khi người dùng chỉ đưa video ("thêm hiệu ứng", "edit cho anh", "làm cho video sinh động") mà không nói giây nào, hiệu ứng gì.
Claude tự quyết hết, không hỏi lại. Chỉ hỏi khi thiếu thứ không đoán được (vd video không có lời và không rõ chủ đề).

Nguyên tắc gốc: **chọn từ ý của câu, không chọn từ hiệu ứng.** Đừng cầm sẵn một hiệu ứng rồi đi tìm câu để đặt vào.
Một hiệu ứng sai nghĩa còn tệ hơn không có hiệu ứng.

## 1. Quy trình tự dựng

0. **Tư liệu (tuỳ chọn):** người dùng đưa đường dẫn ảnh hoặc thư mục ảnh (ảnh chụp bài đăng, trang Facebook, bảng giá, tin nhắn…) thì dùng; không đưa thì bỏ qua, **không hỏi xin**.
   Mở từng ảnh ra xem để biết nó là gì. Ảnh nào khớp với một câu thoại (câu nhắc tới bài đăng, luật chơi, trang để follow…) thì dùng `screenshot` ở câu đó.
1. **Nghe:** `$PY scripts/words.py <video>` in từng câu kèm mốc. Sửa chữ nghe sai theo ngữ cảnh (tên riêng, tiếng lóng, "giveaway", số tiền) trước khi lấy làm chữ trên hình.
   **Nghe cách mở đầu và năng lượng của video** (mục 4, "Năng lượng"): mở mạnh, mở nhẹ hay mở bằng hành động; cả video nói nhanh, sôi nổi hay chậm, nhẹ nhàng.
   **Xác định mục đích video** trong một câu (vd "giveaway: quà gì, trị giá, cách chơi, hạn chót, follow ở đâu"; "bán hàng: sản phẩm, giá, ưu đãi, cách mua").
   **Liệt kê thông tin bắt buộc nhấn** (mục 4): chỉ những thông tin người xem **cần để hiểu hoặc làm theo** mục đích đó: giá/giá trị, ngày giờ, hạn chót, số giải, tên phần quà, cách tham gia, ưu đãi.
   Con số bên lề không phục vụ mục đích (làm fan mấy năm, đã đi bao nhiêu nơi, chuyện cá nhân) **không** bắt buộc, thường để trống. Nghe chưa rõ thì suy ra từ ngữ cảnh và cách nói số tiếng Việt
   ("1 triệu tư" = 1.400.000đ, "triệu rưỡi" = 1.500.000đ, "ba trăm k" = 300.000đ, "7 giờ tối" = 19H), đối chiếu với chữ trong ảnh tư liệu nếu có. Không bao giờ bỏ một thông tin chỉ vì nghe không rõ.
2. **Nhìn:** tạo một tấm ảnh tổng quan rồi mở xem:
   `ffmpeg -v error -y -i <video> -vf "fps=1/6,scale=240:-1,tile=6x2" -frames:v 1 <folder>/overview.jpg`
   Ghi lại: đầu ở cao hay thấp, tay/đồ vật có hay che ngực không, đoạn nào người quay đi chỗ khác.
3. **Lập bảng theo câu** (viết ra file `<tên video>_ideas.md`), mỗi câu một dòng: `mốc · câu (đã sửa) · loại ý · hiệu ứng hoặc — · chữ`.
   Loại ý lấy ở bảng mục 2. Câu thường, câu dẫn, câu chào: để `—`.
4. **Chọn hiệu ứng** theo mục 2 và mục 3, **chỉ trong số hiệu ứng gói này có** (`$PY custom/fx_vi.py --list`).
   Ý nào hợp nhất với hiệu ứng ở gói khác (xem `pack.json` → `others`): ghi lại để báo, đừng thay bằng hiệu ứng khác nghĩa.
5. **Soát luật** ở mục 4. Với từng hiệu ứng, hỏi: *"Tắt tiếng đi, hiệu ứng + chữ này cho người xem biết thêm điều họ cần không?"* Không thì bỏ.
   Mọi thông tin bắt buộc đã có hiệu ứng chưa? Rồi mới tới mật độ, chữ, khung hình; thừa thì cắt câu thường, không cắt thông tin bắt buộc.
6. **Khung kiểm → sửa → render** như SKILL.md mục 4.
7. **Báo người dùng** bằng bảng ngắn: `giây · hiệu ứng · vì sao (câu nào)`, cộng một dòng "gói khác có X hợp với đoạn Y" nếu có.
   Nêu rõ các thông tin bắt buộc đã nhấn, và con số nào là tự suy ra (để họ soát lại).

## 2. Loại ý → hiệu ứng (ưu tiên từ trái sang)

| Loại ý trong câu | Hiệu ứng hợp | Ghi chú |
|---|---|---|
| **Mở đầu mạnh** (câu hook: lời hứa, con số, câu hỏi gây tò mò, "dừng lại!", vào thẳng việc) | `lean-in` + `text`, `backdrop-word`, `split-headline`, `cover-star`, `cinema`, `led-sign`, `spotlight-neon`, `dot-reveal` | Chỉ khi người nói mở đầu mạnh thật. Chữ = ý hook rút gọn |
| **Mở đầu nhẹ** (chào hỏi, tâm sự, kể chậm, "hôm nay mình muốn kể…") | để trống, hoặc `slow-push` rất nhẹ (`zoom=1.15`) không chữ | Không dập hiệu ứng mạnh vào lời chào. Để người xem làm quen với người nói |
| **Mở đầu bằng hành động** (đang mở hộp, giơ sản phẩm, làm ngay) | để hình tự nói; cùng lắm `slow-push` | Hành động đã là hook |
| **Con số phục vụ mục đích video**: giá, giá trị quà, ưu đãi %, số giải/suất (**bắt buộc nhấn**) | `lean-in` với `text` = con số viết đầy đủ ("1.990.000đ", "5 SUẤT", "GIẢM 30%"), `liquid-glass-graph`, `select-resize`, `glass-widgets` | Chữ phải hiện đúng con số. Biểu đồ chỉ khi câu nói về tăng trưởng |
| **Hai con số liên quan**: trước/sau, tháng này/tháng trước | `over-the-shoulder-zoom`, `split-graph` | |
| **Thời gian, hạn chót, ngày giờ** (**bắt buộc nhấn**) | `spotlight` (chữ = ngày giờ), `lean-in` với `text`, `countdown-flip` | `countdown-flip` chỉ khi đúng là đếm ngược / sắp bắt đầu |
| **Câu nhắc tới thứ có trong ảnh tư liệu** (bài đăng, luật chơi, trang FB, bảng giá) | `screenshot`: `highlight` dòng chứa thông tin đang nói, `click` nút Theo dõi / Follow khi câu kêu gọi follow | Chỉ khi người dùng đưa ảnh. Vị trí dòng/nút lấy bằng `scripts/find_text.py` |
| **Phủ định, bác bỏ**: "không phải", "đừng", "sai" | `huge-strike`, `reject-stamp`, `uninstall` | Chữ = điều bị bác bỏ |
| **Từ khoá then chốt, bước ngoặt**: "nhưng", "bí mật là" | `lean-in`, `backdrop-word`, `crayon-write`, `spotlight-type`, `red-collage`, `gold-collage` | Chữ là cụm khoá (1–3 từ), không chép cả câu |
| **Cảm xúc, thân mật, lời cảm ơn** | thường để trống; nếu cần thì `slow-push` (zoom nhẹ, không chữ) | Không chữ, không khung ngắm, không con dấu |
| **Lời nói thêm bên lề, chuyện cá nhân** (làm fan mấy năm, kể lể, đùa) | **để trống** | Không phục vụ mục đích video thì không nhấn, kể cả khi có con số |
| **Chúc mừng, thành tích, mở quà** | `spotlight` với `look=sparkle`, `gold-collage`, `cover-star` | |
| **So sánh trước/sau, biến đổi** | `swipe`, `over-the-shoulder-zoom` | |
| **Liệt kê, các bước, tiêu chí** | `todo`, `checklist`, `check-pills`, `apple-toggles`, `the-bill`, `lineup`, `tier-list` | Mỗi mục là một ý đã nói; `ticks` khớp lúc nói từng mục |
| **Người nói tự giới thiệu** ("mình là X", "kênh của mình là…") | `locked-on` (chữ = tên/handle, không gì khác), `pastel-word`, `reel-frame` | Chỉ khi câu thật sự là lời giới thiệu |
| **Câu chốt ý chính của video** (kết luận, lời kêu gọi cuối) | `headline-box`, `cinema`, `slow-push` | Câu chốt phải là ý chính, không phải câu nói thêm ở cuối |
| **Kêu gọi follow / comment / nhắn tin** | `tap`, `comment-box`, `pastel-word`, `messages` | Chữ = đúng từ khoá họ bảo comment |
| **Khoan đã, chỉ vào chi tiết** | `pause-point` | |
| **Nội dung, kênh, portfolio của người nói** | `orbit`, `carousel-spin`, `fan-build`, `profile-wall`, `place-in-grid`, `phone-fan`, `headline-wall`, `noise` | Chỉ khi người dùng đưa ảnh/clip (`images`); không có thì bỏ |
| **Dựng video, công cụ, AI, phím tắt** | `editor`, `timeline`, `wave-trim`, `shortcut-rain`, `glass-widgets`, `tier-list` | |
| **Tin nóng, "ai cũng nói về X"** | `match-cut`, `headline-wall` | |
| **Rối, lún sâu, vòng lặp, "càng… càng…"** | `rabbit-hole` | Hiếm. Không dùng để kết video |
| **Hồi tưởng, quá khứ** | `moody` với `grade=bw` | |

## 3. Từng hiệu ứng: nghĩa · dùng khi · đừng dùng khi · chữ

| `fx` | Nó nói gì với người xem | Dùng khi | Đừng dùng khi | Chữ |
|---|---|---|---|---|
| `lean-in` | "Nghe này!" (giật zoom vào mặt), `text` bật lên trên đầu | con số, ngày giờ, từ khoá, câu đinh | câu thường; 2 lần liền nhau | con số đầy đủ, hoặc bỏ |
| `screenshot` | "Đây, nhìn tận mắt" (ảnh người dùng đưa hiện thành thẻ) | câu nhắc tới bài đăng, luật, trang, bảng giá có trong ảnh | không có ảnh; ảnh không liên quan câu | `highlight`, `click`, `click_text` (vd "Đang theo dõi") |
| `slow-push` | "Lại gần hơn" (đẩy chậm, nền mờ) | mở đầu (mạnh hay nhẹ đều được, nhẹ thì `zoom=1.15`), câu tâm sự, cảm ơn, câu quan trọng nói chậm | đoạn tay đang làm việc ở dưới khung | không |
| `locked-on` | "Đây là người này" (khung ngắm khoá vào mặt) | người nói **tự giới thiệu** tên/kênh | mọi câu khác: nói về người/vật khác, kể chuyện cá nhân, khoe thâm niên (vd "cảm ơn chị Lan đã gửi", "mình làm nghề 10 năm rồi") | **chỉ** tên/handle người nói, hoặc bỏ. Không bao giờ là một câu bình luận |
| `spotlight` | "Khoảnh khắc chính" (tắt đèn, còn người) | thông tin quan trọng nhất video: ngày giờ, giá, tên | quá 1 lần mỗi video | ngắn: "19H · 25/11", "2,4 TRIỆU" |
| `moody` | đổi không khí bằng màu | `warm` kỷ niệm/cảm động, `bw` quá khứ, `cool` nghiêm túc, `pop` vui | câu hào hứng mà dùng `moody` tối | không |
| `swipe` | "Trước và sau" | biến đổi, so sánh trước/sau | không có gì đổi | không |
| `rabbit-hole` | "Lún sâu, choáng" | đào sâu, vòng lặp, rối | câu kết, câu vui | không |
| `over-the-shoulder-zoom` | hai biểu đồ liên quan | hai con số đi cặp | chỉ có một số | `text` 2 nhãn, `to` 2 số |
| `cinema` / `cinema-v1` | "Bìa phim tài liệu" | hook kể chuyện, tiêu đề, câu chốt | video vui nhộn nhanh | tiêu đề 1–2 dòng ngắn |
| `backdrop-word` | "Từ khoá lớn" sau lưng | chủ đề, từ khoá then chốt | chữ dài > 10 ký tự | 1 từ |
| `huge-strike` | "Không phải cái này" | bác bỏ, phủ định | câu khẳng định | điều bị bác bỏ |
| `crayon-write` | nhấn từ khoá kiểu viết tay | từ khoá thân thiện, nhẹ | câu nghiêm túc | 1 từ |
| `red-collage` | tuyên ngôn mạnh + 3 ý | quan điểm mạnh có 3 vế | câu nhẹ | từ đỏ + 3 dòng ngắn |
| `pastel-word` | "Follow mình" kèm thẻ hồ sơ | CTA follow có tên/handle | không có handle | từ + `name`, `handle` |
| `led-sign` | biển hiệu sáng | khẩu hiệu, tên sự kiện, hook | câu thường | 1–2 dòng ngắn |
| `match-cut` | "Ai cũng nói về X" | chủ đề nóng trên báo | không phải tin tức | 1 từ |
| `spotlight-type` | chữ gõ dần trong bóng tối | câu hỏi, bí mật, suy nghĩ | | 1–2 từ |
| `spotlight-neon` | biển neon bật từng chữ | tên, thương hiệu, hook buổi tối | | 1 từ |
| `cover-star` | "Lên bìa tạp chí" | giới thiệu bản thân, thành tích, hook | câu thường | tiêu đề |
| `noise` | "Quá nhiều nội dung" | ngợp thông tin, nhiều video | không có `images` | không |
| `orbit` / `carousel-spin` / `fan-build` / `phone-fan` | nội dung của mình bay quanh | khoe nhiều video/sản phẩm | không có `images` | (phone-fan: 2 dòng) |
| `profile-wall` / `place-in-grid` | lưới kênh của mình | khoe kênh, lượt xem | không có `images` | nhãn, lượt xem |
| `check-pills` | chọn các tag | các lựa chọn, sở thích | | tag ngắn |
| `headline-wall` | các tiêu đề + tổng | "các video của tôi đạt…" | | `tiêu đề::meta`, tổng |
| `gold-collage` | sang, thành tích | thành tích, giá trị cao | | từ vàng + dòng phụ |
| `todo` / `checklist` | việc được tích dần | các bước, việc cần làm | dưới 2 mục | các mục, `ticks` lúc nói |
| `apple-toggles` | "Bật" từng thứ | bật tính năng, thói quen, cài đặt | | các dòng |
| `the-bill` | hoá đơn in ra | chi phí, yêu cầu, danh sách dài | | các dòng |
| `lineup` | top N đánh số | danh sách xếp thứ tự | tên dài | tên ngắn |
| `tier-list` | xếp hạng S/A/B | xếp hạng, đánh giá | | `title`, `item`, `others` |
| `glass-widgets` | widget kính + "Edited by Claude" | nói về AI/Claude, con số lớn | video không liên quan AI (pill tiếng Anh) | số lớn, tên |
| `messages` | tin nhắn hiện dần | khách nhắn, bạn bè hỏi | | các tin nhắn (đặt `title` tiếng Việt) |
| `comment-box` | comment một từ | "comment X để nhận…" | không có từ khoá | đúng từ khoá |
| `tap` | nút Follow → Following | CTA follow | | không (đặt `x=0.6`) |
| `liquid-glass-graph` | một chỉ số tăng | tăng trưởng, kết quả | số không tăng | nhãn, `from`, `to` |
| `split-graph` / `split-graph-v1` | 7 cột, cột 1 có vương miện | so sánh nhiều mục, theo ngày | | tiêu đề, `values` |
| `timeline` | hậu trường dựng phim | đang quay/dựng, hậu trường | | tiêu đề |
| `wave-trim` | cắt khoảng lặng | nói về cắt ghép, nói gọn | | không |
| `select-resize` | kéo số to lên | "gấp đôi", "x3" | | "2X" |
| `editor` | giao diện phần mềm dựng | nói về edit video | | tiêu đề |
| `countdown-flip` | 3, 2, 1 | sắp bắt đầu, ra mắt | chỉ là một ngày giờ | `from` |
| `broll-split` | ảnh sản phẩm + nhãn giá | sản phẩm có giá | không có `images` | nhãn giá |
| `tape-label` | dán nhãn lên người | gắn danh hiệu cho người nói, ý chốt ngắn | tay/vật che ngực | 2–4 từ |
| `scribble` | vẽ bậy vui | tự trào, hài | câu nghiêm túc | nhãn ngắn |
| `pause-point` | "Khoan, nhìn này" | chỉ vào chi tiết, "đây là tôi lúc…" | | nhãn |
| `reject-stamp` | con dấu đỏ | "SAI", "KHÔNG", bác bỏ mạnh | | 1 từ |
| `uninstall` | gỡ bỏ có glitch | bỏ thói quen, xoá app | | tên thứ bị bỏ |
| `reel-frame` | video thành thẻ reel | nói về kênh/video của mình, kết | | handle |
| `shortcut-rain` | mưa phím | mẹo phím tắt, công nghệ | | các phím |
| `headline-box` | tiêu đề 2 dòng | câu chốt, tiêu đề phần | | 2 dòng |
| `split-headline` | thẻ tiêu đề đẩy người xuống | hook kiểu tiêu đề báo | | 1–2 dòng + từ tô |
| `dot-reveal` | hình hiện từ chấm sáng | mở đầu, reveal | giữa video | không |

## 4. Luật

**Mật độ** (video người nói, giọng dẫn dắt):
- Khoảng 1 hiệu ứng mỗi 8–12 giây. Video 60s: 4–7 hiệu ứng. Thiếu ý hợp thì ít hơn cũng được: **câu không có ý đắt thì để trống.**
- Mở đầu theo đúng cách người nói mở (bảng mục 2): mở mạnh mới có hiệu ứng hook trong 3 giây đầu; mở nhẹ hoặc mở bằng hành động thì không ép.

**Năng lượng** (hiệu ứng phải hợp với người nói, không phải ngược lại):
- *Sôi nổi, nói nhanh:* 1 hiệu ứng mỗi 6–9s, được dùng họ mạnh (chữ bật, con dấu, tắt đèn, đèn LED).
- *Vừa, nói chuyện bình thường:* 1 hiệu ứng mỗi 8–12s, chủ yếu nhấn thông tin, ít hiệu ứng lớn.
- *Nhẹ nhàng, tâm sự, chậm:* 1 hiệu ứng mỗi 12–20s, hiệu ứng mềm (`slow-push` nhẹ, `crayon-write`, `moody` ấm, `spotlight-type`), tránh con dấu, glitch, giật zoom mạnh (`lean-in` thì hạ `zoom` còn 1.2 hoặc dùng `zoom=1`).
- Video đổi giọng giữa chừng (mở nhẹ, giữa hào hứng) thì theo từng đoạn.
- Hiệu ứng lớn (`spotlight`, `cinema`, `cover-star`, `red-collage`, `gold-collage`, `split-headline`, `swipe`, `rabbit-hole`, `editor`, `place-in-grid`) chiếm tối đa 1/3, mỗi cái tối đa 1 lần.
- Một hiệu ứng tối đa 2 lần mỗi video, không đặt liền nhau. Giữa hai hiệu ứng cách ít nhất 3 giây.
- **Đếm theo họ hình ảnh, không theo tên.** Người xem không biết tên hiệu ứng, họ chỉ thấy động tác lặp lại. Mỗi họ tối đa 2 lần trong video 60s, hai hiệu ứng liền nhau phải khác họ:
  - *Zoom vào mặt:* `lean-in` (zoom > 1), `slow-push`, `locked-on`, `headline-box`, `over-the-shoulder-zoom`, cả `push` của `spotlight` (đặt `push=1.0` nếu họ này đã đủ lượt).
  - *Tắt đèn:* `spotlight`, `spotlight-type`, `spotlight-neon`, `led-sign`.
  - *Đổi màu cả khung:* `moody`, `swipe`, `cinema`, `cinema-v1`, `red-collage`, `gold-collage`, `timeline`.
  - *Chữ bật lên:* `lean-in` với `zoom=1` (chỉ có chữ, máy quay đứng yên), `backdrop-word`, `huge-strike`, `crayon-write`, `match-cut`, `pastel-word`, `cover-star`.
  - *Thẻ giao diện:* `screenshot`, `todo`, `checklist`, `apple-toggles`, `the-bill`, `messages`, `comment-box`, `tap`, `glass-widgets`, `liquid-glass-graph`, `split-graph`, `tier-list`, `lineup`.
  - *Ảnh quanh đầu:* `noise`, `orbit`, `carousel-spin`, `fan-build`, `profile-wall`, `phone-fan`, `place-in-grid`, `headline-wall`, `check-pills`.
  - *Nhãn, dấu:* `tape-label`, `scribble`, `pause-point`, `reject-stamp`, `uninstall`, `reel-frame`, `shortcut-rain`, `select-resize`.
  - *Chuyển cảnh lớn:* `rabbit-hole`, `dot-reveal`, `split-headline`, `editor`, `broll-split`, `wave-trim`.
- Họ zoom đã đủ 2 lần mà còn con số phải nhấn: dùng `lean-in` với `zoom=1` và `text` (chữ bật lên, không zoom), hoặc `spotlight` với `push=1.0`.
- Mỗi hiệu ứng 1.5–4s. Bắt đầu sớm hơn từ khoá 0.1–0.2s, kết thúc ở cuối câu (không cắt giữa câu).

**Thông tin bắt buộc nhấn** (trên cả luật mật độ):
- Thông tin người xem cần cho mục đích video (giá/giá trị, ngày giờ, hạn chót, số giải, tên phần quà, cách tham gia, ưu đãi): **mỗi thông tin phải có một hiệu ứng làm nó hiện lên hình**, ngay lúc nói.
- Con số bên lề không phục vụ mục đích (thâm niên, chuyện cá nhân): không bắt buộc, mặc định để trống.
- Con số hiện bằng chữ (vd `lean-in` + `text`, `spotlight` + `text`, hoặc `screenshot` + `highlight` đúng dòng có con số). Chỉ zoom mà không có chữ là chưa đủ.
- Hai thông tin sát nhau (< 3s) thì gộp vào một hiệu ứng, vd chữ "19H · 25/11".

**Ảnh tư liệu (`screenshot`):**
- Là cảnh chèn nên được che mặt, mỗi lần 3–6s, tối đa khoảng 1/4 thời lượng video.
- Bắt đầu ngay khi câu nhắc tới nó; `hl_at` / `click_at` (giây tính từ lúc thẻ hiện) khớp đúng lúc nói dòng đó / lúc nói "follow".
- Tìm vị trí: `$PY scripts/find_text.py <ảnh> "<cụm chữ>"` in `x0,y0,x1,y1`; cụm vắt nhiều dòng thì `"đầu cụm|cuối cụm"`; không thấy thì `--all` để xem chữ đọc được.

**Chữ:**
- Chữ phải **thêm** thông tin (con số, ngày, tên, cụm khoá), không chép lại câu thoại.
- Con số trên hình viết dứt khoát, không "~", "khoảng", "tầm" ("2,4 TRIỆU", không "~2,4 TRIỆU"). Số nào tự suy ra thì nói trong phần báo cáo để người dùng soát.
- **Chủ thể của hiệu ứng phải là chủ thể của câu.** Khung ngắm vào mặt người nói thì chữ nói về người nói.
- Chữ sau đầu tối đa ~10–12 ký tự. Tiếng Việt có dấu đầy đủ, viết đúng chính tả.
- Hiệu ứng có chữ mặc định tiếng Anh ("Messages", "Edited by Claude"…): đặt `text`/`title` tiếng Việt; không đổi được thì cân nhắc bỏ.

**Khung hình:**
- **Không che mặt là luật cứng. Vùng giao diện là vùng nên tránh.** Khung kiểm khung dọc tô đỏ vùng giao diện điện thoại che:
  đỏ đậm = cấm (trên cùng ~5.5%: thanh trạng thái, Dynamic Island; sát đáy màn hình); đỏ nhạt = nên tránh (tab/tìm kiếm tới 13%, caption từ 78%, cột nút bên phải).
- Chữ lấn vào đỏ nhạt một chút là được, nhất là khi quay cận mặt: thà chữ chạm dải trên còn hơn tụt xuống che mặt hay nhỏ tới mức không đọc được. Không để chữ vào đỏ đậm.
- Chữ sau đầu tự đặt sát trên đỉnh đầu (tóc chỉ che chân chữ); chật thì lấn lên đỏ nhạt rồi mới thu nhỏ; quay cận sát tới mức trên đầu hết chỗ thì engine tự đưa chữ ra trước, dưới cằm. Khung kiểm vẫn thấy chữ khó đọc thì rút ngắn chữ.
- Tay hoặc đồ vật che ngực → tránh hiệu ứng đặt ở ngực/dưới cằm (`tape-label`, `checklist`, `liquid-glass-graph`, `apple-toggles` kiểu `pos=below`).
- Đầu cao sát mép trên → tránh hiệu ứng có chữ trên đầu (README → "Vùng an toàn").
- Người quay đi, mặt khuất → đừng dùng hiệu ứng bám mặt ở đoạn đó.
- Luôn xuất khung kiểm và tự xem trước khi render.
