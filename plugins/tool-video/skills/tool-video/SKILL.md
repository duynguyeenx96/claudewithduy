---
name: tool-video
description: Dựng short 9:16 giới thiệu / review một tool (AI, web, app, phần mềm làm video…) từ A-roll người nói + tư liệu thật (quay màn hình, ảnh chụp, file kết quả) bằng HyperFrames, với nhiều concept hình ảnh khác nhau (ui, split, screen, tutorial, terminal, retro, notebook, ranking, versus, depth, glide, fxreel) để mỗi tool một kiểu, không lặp. Trigger: `/tool-video <a-roll.mp4> [flags]`, hoặc khi người dùng muốn "làm video review/giới thiệu tool X", "đổi concept khác".
---

# /tool-video: A-roll + tư liệu thật về tool → short 9:16 có motion graphics

```
/tool-video <a-roll.mp4> --tool "<Tên tool>" [--concept <tên>|auto] [--purpose review|aff] [--palette <tên>] [--materials <thư mục>] [--url <trang tool>] [--screen <bản quay>] [--face-pos bottom|top]
            [--edit <edit.json>] [--cover <thumb.png>] [--script <file.txt>] [--srt <file.srt>] [--voice <file.wav>] [--music <file>] [--no-cut] [--dry] [--help]
/tool-video --concepts            # xem danh sách concept
/tool-video --help
```

Người dùng thường không rành kỹ thuật: tự chạy lệnh cho họ, báo ngắn gọn, không bắt họ gõ lệnh.

## `--help` và `--concepts`

Có `--help`/`-h`, hoặc **không có tham số**: trả lời **nguyên văn** khối dưới, không chạy lệnh nào, rồi dừng.

````markdown
**/tool-video**: short 9:16 giới thiệu/review tool từ A-roll của bạn + tư liệu thật, mỗi tool một concept

**Cách gọi**
```
/tool-video ~/Movies/flow.mp4 --tool "Google Flow"                    # tự chọn concept, không lặp 2 video gần nhất
/tool-video ~/Movies/flow.mp4 --tool "Google Flow" --concept screen   # chọn concept
/tool-video ~/Movies/a.mp4 --tool "Kling" --concept versus --palette sport --dry
/tool-video --concepts                                                # xem các concept
```

**Chuẩn bị** trong `tool-video/<tên-tool>/` ở thư mục đang mở (skill tự tạo; đổi chỗ bằng biến `TOOL_VIDEO_HOME`):
| Thư mục / file | Bỏ gì vào |
|---|---|
| `aroll/` | clip bạn nói, **có tiếng**, 9:16 (hoặc truyền đường dẫn trực tiếp) |
| `materials/` | quay màn hình thao tác thật, ảnh chụp, video/ảnh kết quả tool tạo ra |
| `script.txt` hoặc `.srt` | lời thoại (để sửa phụ đề cho đúng); không có thì Whisper tự nghe |
| `notes.md` | tuỳ chọn: điểm muốn nhấn, giá, link, thứ **không** được nói |

**Flag**
| Flag | Tác dụng |
|---|---|
| `--tool "<tên>"` | tên tool (đặt tên thư mục, chữ trên màn hình) |
| `--concept <tên>` | `ui`, `split`, `screen`, `tutorial`, `terminal`, `retro`, `notebook`, `ranking`, `versus`, `depth`, `glide`, `fxreel`, `auto` (mặc định) |
| `--purpose <review\|aff>` | `review` (mặc định): review tool/app/phần mềm. `aff`: video bán sản phẩm |
| `--palette <tên>` | bảng màu của concept (xem `--concepts`) |
| `--materials <thư mục>` | tư liệu ở chỗ khác `materials/` |
| `--screen <file>` | concept `tutorial`: bản quay màn hình ngang (không truyền thì lấy video ngang trong `materials/`) |
| `--face-pos <bottom\|top>` | concept `tutorial`: ô mặt dưới (mặc định) hoặc trên màn hình |
| `--url <link>` | trang chính thức: chụp màn hình + lấy video giới thiệu công khai làm tư liệu |
| `--edit <edit.json>` | bản đã duyệt: transcript sửa, đoạn giữ, kiểu phụ đề, khung (xem mục 4) |
| `--cover <thumb.png>` | thumbnail gắn vào frame đầu ngay khi render |
| `--script <file>` / `--srt <file>` | lời thoại chuẩn / phụ đề có sẵn (bỏ qua Whisper) |
| `--voice <file.wav>` | A-roll không có tiếng: dùng file giọng thu/đọc riêng (khẩu hình sẽ không khớp) |
| `--music <file>` | nhạc nền (bạn tự chọn bài có quyền dùng); không có thì video không nhạc |
| `--no-cut` | giữ nguyên A-roll, không tự cắt khoảng lặng / chỗ nói vấp |
| `--dry` | chỉ dựng + chụp khung để duyệt, chưa render |

**Nguyên tắc:** chỉ đưa lên màn hình tính năng/giao diện/con số **có trong tư liệu hoặc trang chính thức**, không bịa UI.
Thành phẩm: `tool-video/<tên>/output/<tên>-<concept>.mp4`.
````

Có `--concepts`: in **nguyên văn** bảng dưới rồi dừng.

````markdown
| Concept | Trông như thế nào | Hợp với | Bảng màu |
|---|---|---|---|
| `ui` | card giao diện trắng bo góc trồi lên trên mặt, chip đen, khung chat gõ prompt | tool AI có ô prompt/chat | `lime` `sky` `peach` |
| `split` | đồ hoạ nền tối nửa trên, mặt nửa dưới, bung full ở câu nhấn | website/sản phẩm ra mắt, tin công nghệ | `mint` `violet` `amber` |
| `screen` | quay màn hình trong khung laptop/điện thoại, zoom theo con trỏ, mặt trong bong bóng tròn | tutorial từng bước (cần quay màn hình) | `graphite` `cream` `grape` |
| `tutorial` | quay màn hình ngang rộng hết khung, mặt trong ô vuông trên/dưới, phụ đề đối diện ô mặt | tutorial quay màn hình 16:9 đăng khung dọc | `sun` `volt` `ice` |
| `terminal` | cửa sổ terminal, gõ lệnh, log chạy, glitch | tool dev, CLI, AI agent, tự động hoá | `matrix` `dracula` `amber` |
| `retro` | Windows 95: cửa sổ bật chồng, hộp thoại lỗi, thanh cài đặt | tool vui, meme, "ngày xưa vs giờ" | `win95` `mac` `vapor` |
| `notebook` | trang sổ, polaroid dán băng keo, nét bút vẽ dần, sticky note | workflow nhiều bước, mẹo, tool ghi chú | `paper` `kraft` `chalk` |
| `ranking` | số khổng lồ đếm ngược, card từng tool, bảng xếp hạng/tier list | top 3/5 tool, tổng hợp | `gold` `neon` `tier` |
| `versus` | chia đôi màn hình, VS, bảng điểm, thanh trượt trước/sau | so 2 tool, trước/sau | `fight` `clean` `sport` |
| `glide` | người trượt êm sang một bên, chữ + từ khoá vòng elip cạnh đầu, chip chỉ có chữ | vlog/nói chuyện dài, series cá nhân | tính từ màu phòng (như `depth`) |
| `fxreel` | showreel "21 hiệu ứng trong 20 giây": mỗi hiệu ứng ~1s chạy ngay trên người, cột checklist trái, CTA comment | khoe năng lực dựng/AI, hook mạnh | `forest` |
| `depth` | chữ khổng lồ nằm sau người (tách nền), đổi kiểu khung mỗi ~3s bằng whip-zoom, neon script | ngồi nói trong phòng, hook mạnh, quảng cáo app | `complement` `splitcomp` `triad` `analog` `mono` |
````

## 0. Cài đặt (lần đầu) và biến dùng chung

```bash
SK="${CLAUDE_SKILL_DIR}"                                  # thư mục skill này (đường dẫn tuyệt đối)
bash "$SK/scripts/setup.sh"                                # dòng cuối: READY <python> → gọi là PY
T="${TOOL_VIDEO_HOME:-$PWD/tool-video}"                    # nơi chứa các tool; history.json ở đây
export TOOL_VIDEO_SK="$SK"                                 # build.py đọc biến này để tìm scripts/ và bộ SFX
```
- `NEED_FFMPEG` / `NEED_NODE`: cài giúp người dùng (Mac: `brew install ffmpeg node`; Windows: `winget install ffmpeg OpenJS.NodeJS`), rồi chạy lại setup.
- `NEED_WHISPER` chỉ là tuỳ chọn: không có thì cần `--script`/`--srt`. Model mặc định `~/.cache/hyperframes/whisper/models/ggml-medium.bin`
  (đổi bằng `WHISPER_MODEL`; `npx hyperframes transcribe <file> --model medium` tải sẵn model này).
- HyperFrames chạy bằng `npx hyperframes …` (lần đầu tự tải).
- Mọi lệnh `python3 $SK/scripts/…` bên dưới chạy bằng `$PY` nếu script cần numpy/Pillow (`vendor/editatlas`, `tutorial`); script khác chạy được bằng python3 thường.

## Thư mục

```
$T/<slug>/                     slug = tên tool viết thường, gạch ngang (google-flow)
├── aroll/  materials/  script.txt  notes.md
├── work/<concept>/            build.py, public/, transcript.json, facts.md
└── output/<slug>-<concept>.mp4
$T/history.json                [{"tool", "concept", "palette", "date", "output"}]: để không lặp concept
```

## 1. Kiểm tra đầu vào

- Không có `--tool`: lấy từ tên thư mục / tên file, không đoán được thì hỏi.
- A-roll: `ffprobe` (kích thước, fps, thời lượng) và `ffmpeg -af volumedetect`. **mean_volume < -60 dB = không có tiếng**:
  - có `--voice <file.wav>` → dùng file đó làm giọng (`public/voice.wav`), chép lời từ file giọng. Khẩu hình sẽ không khớp: báo người dùng.
  - không có → dừng, báo "clip không có tiếng, xuất lại kèm audio hoặc đưa file giọng bằng `--voice`". **Không** chạy Whisper trên clip câm (nó bịa chữ).
- Xem keyframe A-roll (contact sheet ~12 khung): vị trí mặt, chữ đã chèn sẵn, đoạn hỏng. Clip có chữ cháy sẵn thì chỉ lấy đoạn sạch.
- Re-encode A-roll sang h264 1080×1920 30fps (`object-fit: cover`, giữ mặt ở giữa) vào `public/aroll.mp4`, **giữ chất lượng gốc**:
  `-c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p -c:a aac -b:a 256k` (không dùng crf 18+, không scale xuống).
  Clip gốc đã đúng 1080×1920 thì không scale/crop lại.
  Sẽ tự cắt (mục 4, không có `--edit`/`--no-cut`/`--voice`): chép lời **clip gốc** trước, rồi gộp cắt + re-encode thành **một** lần encode
  (trim/atrim + concat theo `keep`, cùng thông số trên). Không encode A-roll hai lần.
- **Hiệu ứng trên người nói (tuỳ chọn):** người dùng xin "chữ sau lưng", "tắt đèn chỉ còn người", "biển LED", "thông báo tin nhắn"…
  → dùng plugin **fx-pack** cùng kệ (`/plugin install fx-pack@claudewithduy`, skill `effects`): đọc `README.md` và `SKILL.md` của nó.
  Chưa cài thì báo người dùng một dòng, làm tiếp không có hiệu ứng. fx-pack là **lần encode A-roll duy nhất**: chạy trên clip đã cắt lời, ra thẳng `public/aroll.mp4` (crf 12).
  Xuất khung kiểm (`--still`) cho từng hiệu ứng trước; chữ lọt ngoài `x 70–1010, y 250–1500` hoặc che mặt thì dời / đổi hiệu ứng. Đoạn có hiệu ứng thì build.py không chồng thêm chữ.

## 2. Tư liệu và sự thật (bắt buộc)

Video "animation đẹp nhưng nhiều cái chưa đúng sự thật" là lỗi nặng nhất. Vì vậy:
- Gom tư liệu từ `materials/`, và nếu có `--url`: chụp trang bằng headless Chrome (`--screenshot`, `--dump-dom` để tìm link
  video giới thiệu công khai; link thư mục thường 404, chỉ link file đầy đủ tải được). Tải về `materials/web/`.
- Viết `work/<concept>/facts.md`: mỗi dòng một sự thật sẽ lên màn hình (tên tính năng, tên model, giá, giới hạn) + **nguồn** (file tư liệu hoặc URL).
  Không có nguồn → không đưa lên màn hình. Lời người dùng tự nói trong A-roll là nguồn hợp lệ cho lời của họ, nhưng chữ/giao diện minh hoạ vẫn phải khớp tư liệu.
- Giao diện tool: dùng **ảnh chụp/quay thật**; nếu dựng lại bằng HTML (để animate) thì chép đúng bố cục, nhãn nút, tên model từ ảnh chụp, không thêm nút không có.
- Kết quả tool: chỉ dùng video/ảnh mà tool thật tạo ra (của người dùng hoặc showcase chính thức).
- Logo thương hiệu (TikTok, Facebook, Shopee…): chỉ dùng file người dùng đưa vào `materials/`, không tự vẽ hay tải logo khác.

## 3. Chọn concept

- `--concept <tên>`: dùng luôn. `auto` (mặc định): chọn theo bảng `--concepts` (cột "Hợp với") **và** bỏ 2 concept dùng gần nhất trong `$T/history.json`.
  `screen`, `tutorial` cần có quay màn hình trong tư liệu (`tutorial`: khung ngang, thay bước re-encode ở mục 1 bằng `scripts/tutorial_prep.py`); `versus`/`ranking` cần ≥ 2 thứ để so.
- Đọc `$SK/concepts/<concept>.md`: bảng màu, bố cục, thành phần, chuyển cảnh, nhạc. Không có `--palette` thì chọn bảng màu chưa dùng cho concept đó gần đây.
  `depth`: bảng màu tính từ màu phòng quay (`$SK/scripts/palette.py`, nhóm phối màu theo vòng tròn màu); không có `--palette` thì chọn theo mood (mặc định `complement`).
- Báo người dùng 1 dòng: concept + bảng màu đã chọn và lý do.

## 4. Transcript và nhịp

**Có `--edit <edit.json>`**: người dùng đã duyệt, **không** tự chọn lại đoạn cắt hay sửa chữ.
- `keep`: danh sách `[start, end]` (giây, theo clip gốc `source`) → cắt và nối đúng các đoạn này, theo thứ tự.
- `words`: `{text, start, end, orig}` theo clip gốc. `text == ""` = bỏ khỏi phụ đề. Đổi mốc sang timeline đã cắt rồi ghi `transcript.json`. Bỏ qua bước Whisper.
- `captions`: `hl` (màu từ đang nói), `fg`, `size` (px ở 1080), `per` (số từ/cụm), `case` (`upper`|`normal`), `pos` (tâm dòng = pos × 1920; > 0.76 thì kẹp về 0.76).
- `frame`: `x` (tâm khung theo chiều ngang clip gốc, 0–1), `widen` (1 = khung 9:16 cao hết clip; >1 = khung rộng hơn, đặt giữa trên nền mờ của chính clip),
  `zoom` (punch-in ở chỗ cắt: `none` 1.0, `light` 1.0–1.06, `medium` 1.03–1.15), `layout` (`split` | `dim` cho cảnh đồ hoạ lớn),
  `speed` (≠1: tăng tốc cả hình và tiếng lúc cắt A-roll: `setpts=PTS/<speed>` + `atempo=<speed>`; chia mọi mốc của `words`/`keep` cho `speed`).
- `notes.md` là yêu cầu thêm của người dùng cho lượt dựng này: làm theo, trừ khi trái với `--edit`.

Chép lời (`$SK/scripts/transcribe.py`, ra mảng `[{text, start, end}]`):
- Có `--srt`: `python3 $SK/scripts/transcribe.py srt <file.srt> -o transcript.json`.
- Có tiếng: `python3 $SK/scripts/transcribe.py transcribe <clip> -o transcript.raw.json` (whisper.cpp + DTW, mốc từng từ; in cảnh báo từ rơi vào khoảng lặng).
- Có `--voice`: transcribe file giọng.

**Tự cắt khoảng lặng + nói vấp** (mặc định khi có tiếng và không có `--edit`/`--no-cut`/`--voice`). Script lấy từ herk-edit-kit (MIT, `scripts/cuts/LICENSE`),
đã vá cho tiếng Việt; chỉ dùng chế độ lập kế hoạch (không `--video --apply`), video cắt ở bước re-encode duy nhất (mục 1).
```bash
C=$SK/scripts/cuts; W=work/<concept>/cuts   # raw.json = transcript Whisper của clip gốc (mảng từ, giờ clip gốc)
python3 $C/snap_words.py $W/raw.json <clip gốc> -o $W/snapped.json   # BẮT BUỘC: kéo mốc từ về đúng mép tiếng nói (RMS 50ms, -42 dB)
node $C/cut-silences.mjs $W/snapped.json --gap 0.8 --out-dir $W   # chỉ cắt khoảng nghỉ > 0.8s → giữ hơi thở 0.14–0.24s
node $C/find-cut-candidates.mjs $W/snapped.json --out-dir $W      # nói lặp từ/cụm ("đây là đây là"), nói hỏng rồi nói lại câu
```
- Không snap thì cắt cụt chữ đầu câu: DTW đặt đầu từ trễ 0.1–0.3s, và có thể đặt từ đầu clip vào giữa khoảng lặng.
- Bộ dò chỉ bắt được lỗi nói giống hệt; câu nói lại có đổi chữ phải tự đọc transcript tìm thêm. Đặt cuối mỗi đoạn cắt tay ~60ms trước `start` (đã snap) của chữ được giữ.
- `--gap 0.55` (mặc định của script) cắt cả nghỉ giữa câu → chỗ cắt mỗi ~1s, đầu nhảy liên tục, trông giật. Dùng 0.8.
  `apply-cuts.mjs` tự bỏ đoạn giữ < 0.25s (tránh sót 1 frame giữa hai chỗ cắt → nháy hình).
- Mỗi chỗ cắt (mốc = cộng dồn độ dài `keep_ranges`) đổi cỡ khung A-roll tức thì, xen kẽ 1.0 ↔ ~1.06 (không blur), để bước nhảy trông như chủ ý.
- Sau khi encode, **chép lời lại `public/aroll.mp4`** và so với transcript dự kiến: thiếu chữ đầu câu = điểm cắt sai, sửa rồi encode lại.
- **Luôn đo độ to giọng** (`ffmpeg -nostats -i <cắt.mp4> -af ebur128 -f null - 2>&1 | grep 'I:'`). Lệch quá 1 LU khỏi -16 LUFS (clip điện thoại thường -25…-40) thì
  `python3 $SK/scripts/loudnorm.py <cắt.mp4> public/aroll.mp4` (loudnorm 2 lượt về -16 LUFS, `-c:v copy`, không encode lại hình).
  Mức đỉnh lúc thu đúng không có nghĩa là đủ to, độ to phải chuẩn hoá ở bước này. Giọng gốc dưới -35 LUFS: báo người dùng (nâng lên sẽ lộ tiếng nền, nên thu gần mic hơn).
  Chạy từng bước riêng, kiểm tra file ra rồi mới làm bước sau (chuỗi shell gộp dễ chạy tiếp trên file cũ khi một bước hỏng).
- Đọc `$W/snapped.cut-candidates.md`, **tự duyệt từng đề xuất theo ngữ cảnh**: giữ láy/nhấn mạnh cố ý ("rất rất", "từ từ", "dần dần", "luôn luôn"),
  cắt lặp vô ý và bản nói hỏng (giữ bản sau). Không chắc thì giữ, không cắt cho đủ chỉ tiêu.
- Gộp vùng xoá của `$W/snapped.silence-edl.json` (`delete_ranges`) + các đề xuất đã duyệt thành `$W/all-cuts.json` (`{"cuts":[{start,end,reason}]}`, giờ clip gốc), rồi
  `node $C/apply-cuts.mjs $W/snapped.json --cuts $W/all-cuts.json --out-dir $W` → `snapped.mistakes-edl.json` (`keep_ranges`, giờ clip gốc) +
  `snapped.mistakes-transcript.json` (từ đã dời sang timeline sau cắt; dùng file chép lời lại sau encode làm `transcript.raw.json` vì mốc chuẩn hơn).
- Mốc kết thúc từ của Whisper DTW là ước lượng (≤ start+0.6s, cắt ở khoảng lặng -40 dB): clip có nhạc/ồn nền thì cắt ít đi, không bao giờ cắt vào lời.
- Báo người dùng 1 dòng: bỏ bao nhiêu giây khoảng lặng + từng chỗ nói vấp đã cắt (giờ gốc, câu bị bỏ). Clip đã gọn thì 0 chỗ cắt là bình thường.
- Sửa chính tả/tên riêng theo `script.txt` (Whisper hay nghe sai tên model, số), giữ nguyên `start`/`end`.
- Lập bảng beat trong `build.py`: mỗi câu/ý → một cảnh của concept, ghi mốc theo từ trong transcript. Quy tắc:
  - Hook ≤ 2s đầu phải có chuyển động lớn + chữ to. Cứ 1.5–2.5s có một thay đổi hình (cảnh mới, pop, zoom).
  - Mặt người nói hiện ≥ 35% thời lượng (hook, câu cảm xúc, CTA); phần còn lại đồ hoạ được che mặt.
  - Mỗi lần mặt quay lại: zoom punch 1.08–1.18 khác lần trước.

## 5. Dựng `work/<concept>/build.py`

- Bản mẫu chạy được ở `$SK/templates/`: `ui`, `split` (copy rồi thay cảnh/mốc); `glide` (đọc `concepts/glide.md` trước, thay phần riêng của clip);
  `tutorial`, `fxreel` (đọc concept tương ứng, chỉ sửa phần CẤU HÌNH); `depth` có `templates/depth/index.html` (composition mẫu, viết build.py sinh ra index.html theo đúng bố cục đó).
  Concept khác: viết build.py mới **cùng cấu trúc**: danh sách `tl` (GSAP), `sfx`, `css`, `hosts`; hàm `q()` làm tròn mốc theo frame, `scene()`, `pop()`; cuối file ghi `public/index.html`.
  Đầu mọi build.py: `SK = os.environ["TOOL_VIDEO_SK"]; sys.path.insert(0, os.path.join(SK, "scripts"))` (bản mẫu đã có). Chạy: `TOOL_VIDEO_SK="$SK" $PY build.py`.
- `public/`: `cp -r $SK/assets/vendor public/`, font `mkdir -p public/fonts && cp $SK/assets/fonts/BeVietnamPro-*.ttf public/fonts/`.
  Nhạc nền chỉ khi có `--music`: `mkdir -p public/audio && ffmpeg -i <nhạc> -c:a aac -b:a 192k public/audio/music.m4a` (concept `glide`/`tutorial` dùng `music_loop.m4a`:
  `ffmpeg -stream_loop -1 -i public/audio/music.m4a -t <độ dài> -c copy public/audio/music_loop.m4a`). Không có file nhạc thì bản mẫu tự bỏ track nhạc.
- **SFX**: bộ âm CC0 kèm skill ở `$SK/assets/sfx/` (`kit.json`, nguồn từng file trong `LICENSES.md`), 17 vai: whoosh, pop, click, tick, typing, impact, riser,
  glitch, ding, paper, rip, slice, shutter, cash, magic, chat, error; mỗi vai 3–6 bản cùng họ.
  Dùng qua `$SK/scripts/sfxkit.py`: `sfx_tags(sfx, PUB, DURATION, SFX_GAIN, tracks=range(32, 60), log=WORK / "sfx_cues.json")` trả list thẻ `<audio>`.
  Mọi bản mẫu đã gọi hàm này; build.py mới cũng phải dùng, không tự chép file âm. Bộ âm riêng cùng định dạng: đặt `TOOL_VIDEO_SFX=<thư mục có kit.json>`.
  kit.json cho mỗi vai `vol` (impact 0.50 > slice 0.36 > whoosh/rip 0.32 > riser/ding/paper 0.25 > pop/chat 0.22 > click 0.20 > tick/typing 0.16, đã hạ cho video có giọng nói),
  `anchor` và mỗi file có `dur`, `peak_t`. Cue ghi **mốc hình**, không ghi mốc bắt đầu âm:
  `start` = âm bắt đầu đúng mốc (pop, click, ding); `peak` = điểm to nhất rơi đúng mốc (whoosh, impact, slice, rip); `end` = riser **kết** đúng cú chốt.
  Loại cue → vai: trượt/chuyển cảnh → whoosh; hiện ra → pop; bấm → click; tăng dần → riser; reveal → impact (to nhất); lỗi/công nghệ → glitch; UI nhỏ → tick.
  Một âm mỗi cue, xoay vòng các bản, một file không quá 2 lần / video; vật thật trên hình dùng tiếng thật (giấy → paper/rip, tiền → cash, máy ảnh → shutter).
  Giữ ít SFX và hệ số `SFX_GAIN = 0.85`. Không lấy thêm âm từ Mixkit/Pixabay vào bộ này (giấy phép cấm phân phối lại).
- Composition: `#stage` có `data-composition-id`, `data-duration`, `data-fps="30"`, `data-width="1080"`, `data-height="1920"`;
  mỗi clip có class `clip` + `data-start`/`data-duration`/`data-track-index`; timeline GSAP **paused**, gán vào `window.__timelines`.
- Âm thanh: giọng (A-roll hoặc voice.wav) volume 1, nhạc 0.3–0.35, SFX theo vol của vai nhân `SFX_GAIN`.
- `font-family` luôn để `"Be Vietnam Pro"` đầu tiên (font khác thường thiếu dấu tiếng Việt). Font trang trí (pixel, mono, viết tay) chỉ dùng cho chữ không dấu hoặc đã kiểm tra có dấu.
- Phụ đề: cụm 2–5 từ, từ đang nói đổi màu accent, `top` 1380px (dời lên nếu đè đồ hoạ), hàng phụ đề `left:100px; right:170px`.

**Vùng an toàn (bắt buộc, `$SK/SAFE_ZONE.md`):** TikTok/Reels che y < 250 (giờ, Dynamic Island, thanh tìm kiếm), y > 1500 (tên kênh, mô tả, nhạc),
~70px mỗi bên và cột nút phải x > 900 ở y 850–1500. Mọi chữ, chip, sticker, logo, số liệu, CTA, phụ đề phải nằm trong
`x 70–1010, y 250–1500` (tính cả lúc scale/pop và dấu tiếng Việt), không lấn cột nút phải. Ngoài vùng này chỉ để nền, ảnh/video, người, hoạ tiết không chữ.

**Đồ hoạ lớn** (b-roll ảnh/điện thoại, bảng/biểu đồ): ưu tiên **chia đôi màn hình** (đồ hoạ nửa trên, A-roll dời xuống nửa dưới bằng transform `y`, phụ đề nằm ở đường chia;
xem bản mẫu `split`), hoặc phủ tối A-roll ~78%. **Không** dùng nền đen đặc full màn.
**Đường chia phải mềm, không kẻ vạch cứng:** `FEATHER = 180`; nền đồ hoạ và lớp cảnh kéo xuống `SEAM + FEATHER/2`,
lớp cảnh `mask-image: linear-gradient(to bottom, #000 calc(100% - FEATHER), transparent)`, video nửa dưới bắt đầu từ `SEAM - FEATHER/2` với
`mask-image: linear-gradient(to bottom, transparent 0, #000 FEATHER)`; chỗ vạch cũ chỉ còn dải sáng radial màu accent ~22%.

**Cỡ đồ hoạ (sticker, chip, icon, tick, emoji):** giữ nhỏ gọn, không chiếm không gian của người nói.
Sticky/chip: chữ 44–60px (hook tối đa ~68px), padding ~18×26px; icon/tick/checkbox ≤ 48px. Số liệu/giá chính là thứ duy nhất được to.
Tổng đồ hoạ cùng lúc ≤ ~30% chiều cao khung, ≤ 1 sticker lớn + 1 note mỗi cảnh. Snapshot thấy che mặt/tay/sản phẩm thì nhỏ lại, không dời đi chỗ khác.

**Mục đích aff (`--purpose aff`):** video bán sản phẩm, không phải review tool. Tên sản phẩm + giá (nếu có trong notes.md/lời thoại) nhấn ở hook
và một lần nữa khi nhắc tên; tính năng được nhắc trong lời thoại thành checklist/chip ngắn; cuối video là CTA giỏ hàng/mã giảm giá/đặt hàng
(đúng theo lời thoại, không bịa giá, khuyến mãi, thông số). Không dùng khung "UI/app" giả; ưu tiên concept hợp đồ vật (notebook, split, ranking, versus).

**Lỗi đã gặp:**
- GSAP `scale`/`x` trên phần tử căn giữa bằng `translateX(-50%)` làm mất căn giữa → bọc trong hàng `left:0; right:0; text-align:center`.
- Đếm số mất dấu phẩy → tween object proxy rồi `toLocaleString`.
- Phụ đề kẹt giữa mặt khi A-roll đổi bố cục → `tl.set` lại `top` ở mốc chuyển.
- Mặt to/thấp (quay cận) → chữ phải xuống dưới cằm; snapshot từng cảnh để kiểm tra.

## 6. Kiểm tra, render

```bash
cd work/<concept> && TOOL_VIDEO_SK="$SK" $PY build.py && python3 $SK/scripts/add_cover.py public [<cover>] && npx hyperframes lint public
npx hyperframes snapshot public --at <giữa mỗi cảnh, phẩy ngăn cách> --no-end   # xem contact-sheet*.jpg
```
Cover: có `--cover` thì truyền file đó cho `add_cover.py` (chép thành `public/cover.png`, gắn đúng 1 frame ở t=0).
Lượt dựng mới không có `--cover` thì `rm -f public/cover.png` trước. Lượt chỉnh tiếp cứ chạy `add_cover.py public` (build.py ghi lại index.html nên phải gắn lại).
**Không** gắn cover bằng ffmpeg sau render, **không** nén lại file mp4 đã render (mỗi lần encode lại là mất chất lượng).
Render luôn `--crf 12`. **Không** thêm `--video-frame-format png` (A-roll tối đi ~2.5% độ sáng).
Vẽ vùng an toàn lên từng khung: `python3 $SK/scripts/safezone.py public/snapshots` → xem `public/snapshots/safe-sheet.jpg`: chữ/chip/logo chạm vùng đỏ là sai, dời vào trong.
Xem ảnh: không đè mặt quá 1s ngoài chủ ý, không tràn khung, dấu tiếng Việt đúng font, chữ đọc được trên nền. Sửa → snapshot lại.
`--dry`: dừng, gửi đường dẫn contact sheet.

```bash
PRODUCER_BROWSER_GPU_MODE=hardware npx hyperframes render public -o ../../output/<slug>-<concept>.mp4 --fps 30 --crf 12
```
Không ghi đè thành phẩm cũ: trùng tên thì thêm `-v2`, `-v3`. Kiểm tra `volumedetect` (mean ≈ -16…-22 dB), xem 1–2 khung của file mp4.
Đo độ to trên mp4 đã render (chỉ đo, **không** master lại file): `ffmpeg -nostats -i out.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12`
→ mục tiêu ≈ -16 LUFS, true peak < -1 dBFS. Lệch nhiều thì chỉnh volume nhạc/SFX trong build.py rồi render lại.

**Soát bản render (bắt buộc sau mỗi lần render):**
```bash
$PY $SK/vendor/editatlas/video-check/scripts/check.py <out.mp4> --out work/<concept>/check1 --loudness -16 --expect 1080x1920 --fps 30 \
  [--holds <a-b,…> đoạn đứng hình có chủ ý] [--flashes <t,…> khung chớp có chủ ý]
```
In lỗi dạng `P0/P1/P2 t=… mã: mô tả -> cách sửa` + `findings.png`, `overview_NN.png`. Mở `findings.png`: lỗi thật thì sửa **trong build.py** rồi render lại
(không vá file mp4), chạy lại với `--before work/<concept>/check1/check.json --out …/check2` để thấy cái gì đã hết, cái gì mới.
Soát thêm vùng chết: `python3 $SK/scripts/deadzones.py <out.mp4>` → đoạn ≥3s hình gần như đứng yên và hook 3s đầu yếu; có thì thêm đồ hoạ / zoom ở đó (người nói ngồi yên có chủ ý thì bỏ qua).
Tối đa 3 vòng; P1 `loudness` do giọng gốc nhỏ thì sửa ở bước loudnorm A-roll, không master lại mp4. Khung chuyển cảnh nửa trong suốt = fade đè lên hiệu ứng kế: cho cắt thẳng (`fade=0`).
Người dùng cho phép dùng subagent: đưa agent **chỉ** các sheet + 1 câu mục đích video (không đưa kế hoạch), theo brief trong `$SK/vendor/editatlas/video-check/references/review-guide.md`.

**Làm lại theo video mẫu** (người dùng gửi reel tham khảo): sau khi render, so với mẫu
`$PY $SK/vendor/editatlas/video-breakdown/scripts/compare.py <mẫu.mp4> <out.mp4> --out work/<concept>/compare` → khác biệt lớn nhất trước + `compare.png`.
Chỉ có nghĩa khi hai video cùng kịch bản/nhịp; xem ảnh trước khi kết luận.
Phân tích mẫu trước khi dựng: `…/video-breakdown/scripts/analyze.py <mẫu.mp4> --out work/bd` (nhịp cắt, chuyển cảnh, chữ vào/ra); `text_look.py` đo màu/cỡ chữ.
Các script này chép từ github.com/EditAtlas/skills (Apache-2.0, xem `vendor/editatlas/README.md`); không gọi dịch vụ EditAtlas.

Ghi thêm một dòng vào `$T/history.json`.

Báo người dùng: đường dẫn video, concept/bảng màu, những chỗ dựng lại giao diện bằng HTML (để họ soát sự thật), giới hạn (vd khẩu hình không khớp khi dùng `--voice`).
