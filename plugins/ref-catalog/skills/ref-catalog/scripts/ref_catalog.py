#!/usr/bin/env python3
"""ref-catalog: luồng nguồn tham khảo -> tải -> phân tích -> đối chiếu với tài nguyên hiện có -> kế hoạch remake.
Catalog tài nguyên (library.json) là BẢN ĐỒ để agent đối chiếu nguồn với những gì bạn đang có.

  Lần đầu sau khi cài:
  ref_catalog.py doctor                    kiểm tra máy: hệ điều hành, công cụ đã có/thiếu, bản nào cần cập nhật, lệnh cài
  Bước 1, soạn catalog tài nguyên (làm trước):
  ref_catalog.py lib-src                   liệt kê các nguồn tài nguyên đã chỉ định
  ref_catalog.py lib-src add <thư-mục> [label=…]   thêm một nguồn (thư mục ở đâu cũng được, chủ đề gì cũng được)
  ref_catalog.py lib-src rm <thư-mục|label>        bỏ một nguồn
  ref_catalog.py lib-src new [thư-mục]     chưa có kho: tạo sẵn thư mục tài nguyên (video/ anh/ nhac/ sfx/ template/) và thêm làm nguồn
  ref_catalog.py library [--all]           quét mọi nguồn: thumbs, lưới có tên, thêm mục mới vào library.json
  ref_catalog.py lib-set <id> desc=… tags=a,b note=…   ghi mô tả/tag cho một tài nguyên (Claude điền sau khi xem lưới)
  ref_catalog.py lib-check                 tài nguyên nào chưa mô tả (bản đồ chưa đủ dùng)
  Bước 2-4, nguồn:
  ref_catalog.py init [thư-mục]            tạo workspace (config.json, refs/)
  ref_catalog.py add <link|file>…          thêm nguồn, tải, cắt khung, nghe tiếng -> in ID
  ref_catalog.py fetch <ID>                chạy lại bước tải/chuẩn bị tư liệu
  ref_catalog.py push <ID>                 kiểm analysis.json (match phải trỏ id có thật trong catalog), ghi catalog nguồn
  ref_catalog.py set <ID> khoá=giá_trị…    sửa thủ công (status, note…)
  ref_catalog.py list                      bảng nguồn + độ phủ tài nguyên (có/gần giống/thiếu)
  ref_catalog.py gaps                      gom mọi thứ còn thiếu/gần giống từ các nguồn -> GAPS.md (danh sách đi tìm)
  ref_catalog.py export                    xuất CATALOG.md + catalog.csv
Workspace: --ws <thư mục> hoặc biến REF_CATALOG_WS, mặc định thư mục hiện tại.
Cần: python3 + Pillow, ffmpeg/ffprobe, yt-dlp (chỉ khi tải từ link), whisper-cli + model (tuỳ chọn).
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLS, ROWS = 4, 3
FONTS = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def die(msg):
    sys.exit("Lỗi: " + msg)


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, **kw)
    except FileNotFoundError:
        die(f"thiếu lệnh '{cmd[0]}', cần cài trước")


def font(size):
    from PIL import ImageFont
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


class WS:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.cfg_f = self.root / "config.json"
        if not self.cfg_f.exists():
            die(f"chưa có {self.cfg_f}. Chạy: ref_catalog.py init {self.root}")
        self.cfg = json.loads(self.cfg_f.read_text())
        self.refs = self.root / "refs"
        self.db_f = self.root / "catalog.json"
        self.db = json.loads(self.db_f.read_text()) if self.db_f.exists() else {}

    def save(self):
        self.db_f.write_text(json.dumps(self.db, ensure_ascii=False, indent=2))

    def fields(self):
        return self.cfg.get("analysis", {}).get("fields", [])

    def next_id(self):
        n = [int(p.name[1:]) for p in self.refs.glob("R[0-9]*") if p.name[1:].isdigit()]
        return f"R{(max(n) if n else 0) + 1:03d}"


def open_ws(args):
    root = os.environ.get("REF_CATALOG_WS", ".")
    if "--ws" in args:
        i = args.index("--ws")
        root = args[i + 1]
        del args[i:i + 2]
    return WS(root)


# ---------- tải + chuẩn bị tư liệu ----------
def download(url, out, cookies):
    base = ["yt-dlp", "-f", "bv*+ba/b", "--merge-output-format", "mp4", "--no-playlist", "--write-info-json",
            "-o", str(out / "video.%(ext)s"), url]
    r = run(base)
    if r.returncode and cookies:
        r = run(base[:1] + ["--cookies-from-browser", cookies] + base[1:])
    if r.returncode:
        die("tải thất bại: " + ((r.stderr or r.stdout).strip().splitlines() or ["?"])[-1] +
            ". Reel riêng tư thì tải file về rồi 'add <file>'.")
    f = out / "video.info.json"
    info = json.loads(f.read_text()) if f.exists() else {}
    f.unlink(missing_ok=True)
    keys = ["title", "description", "uploader", "uploader_url", "channel", "view_count", "like_count", "comment_count",
            "timestamp", "upload_date", "webpage_url", "extractor"]
    return {k: info[k] for k in keys if info.get(k) is not None}


def probe(f):
    j = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                        "-of", "json", str(f)]).stdout or "{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    return {"duration": round(float(j.get("format", {}).get("duration", 0) or 0), 2), "width": v.get("width"),
            "height": v.get("height"), "has_audio": any(s.get("codec_type") == "audio" for s in j.get("streams", []))}


def scene_cuts(f):
    err = run(["ffmpeg", "-i", str(f), "-vf", "select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"]).stderr
    return [round(float(x.split("pts_time:")[1].split()[0]), 2) for x in err.splitlines() if "pts_time:" in x]


def contact_sheets(f, out, dur):
    """Khung đều theo thời gian, lưới 4x3, mỗi ô in mốc giây (ghép bằng Pillow vì ffmpeg nhiều máy thiếu drawtext)."""
    from PIL import Image, ImageDraw
    for old in out.glob("sheet_*.jpg"):
        old.unlink()
    fps = min(2.0, max(0.5, 48 / max(dur, 1)))
    with tempfile.TemporaryDirectory() as tmp:
        r = run(["ffmpeg", "-y", "-v", "error", "-i", str(f), "-vf", f"fps={fps},scale=320:-2", "-q:v", "3", f"{tmp}/f_%04d.jpg"])
        if r.returncode:
            die("cắt khung hình lỗi: " + r.stderr[-300:])
        frames = sorted(Path(tmp).glob("f_*.jpg"))
        per, fnt = COLS * ROWS, font(22)
        for s in range(0, len(frames), per):
            imgs = [Image.open(p) for p in frames[s:s + per]]
            w, h = imgs[0].size
            sheet = Image.new("RGB", (COLS * (w + 4), ROWS * (h + 4)), "black")
            d = ImageDraw.Draw(sheet)
            for i, im in enumerate(imgs):
                x, y = (i % COLS) * (w + 4), (i // COLS) * (h + 4)
                sheet.paste(im, (x, y))
                d.rectangle([x, y, x + 78, y + 30], fill="black")
                d.text((x + 6, y + 3), f"{(s + i) / fps:.1f}s", font=fnt, fill="yellow")
            sheet.save(out / f"sheet_{s // per + 1:02d}.jpg", quality=85)


def transcribe(audio, out, cfg):
    t = cfg.get("transcribe", {})
    model = Path(t.get("model", "")).expanduser()
    if t.get("engine") != "whisper-cli" or not shutil.which("whisper-cli") or not model.exists():
        print("  (bỏ qua nghe tiếng: không có whisper-cli/model, xem config.transcribe)")
        return
    with tempfile.TemporaryDirectory() as tmp:
        wav = f"{tmp}/a.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(audio), "-ar", "16000", "-ac", "1", wav])
        r = run(["whisper-cli", "-m", str(model), "-l", t.get("language", "auto"), "-f", wav, "-np", "-ojf", "-of", f"{tmp}/t"])
        j = Path(f"{tmp}/t.json")
        if r.returncode or not j.exists():
            print("  ⚠ Whisper lỗi:", (r.stderr or "")[-200:])
            return
        words = []
        for seg in json.loads(j.read_text()).get("transcription", []):
            words.append({"t": seg.get("timestamps", {}).get("from"), "text": seg.get("text", "").strip()})
        (out / "transcript.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))


def fetch(ws, rid, src=None):
    out = ws.refs / rid
    out.mkdir(parents=True, exist_ok=True)
    meta_f, video = out / "meta.json", out / "video.mp4"
    meta = json.loads(meta_f.read_text()) if meta_f.exists() else {"source": src}
    src = src or meta.get("source")
    if not video.exists():
        if src and Path(src).expanduser().exists():
            shutil.copy2(Path(src).expanduser(), video)
        else:
            meta |= download(src, out, ws.cfg.get("sources", {}).get("cookies_browser"))
    meta |= probe(video)
    if not meta.get("width"):
        die("file không có hình (chỉ có tiếng): cần bản video")
    meta["cuts"] = scene_cuts(video)
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(min(1.0, meta["duration"] / 2)), "-i", str(video),
         "-frames:v", "1", "-vf", "scale=360:-2", str(out / "thumb.jpg")])
    contact_sheets(video, out, meta["duration"])
    if meta["has_audio"]:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-c:a", "aac", "-b:a", "160k", str(out / "audio.m4a")])
        transcribe(out / "audio.m4a", out, ws.cfg)
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    rec = ws.db.setdefault(rid, {"id": rid, "added": str(date.today()), "status": "Chưa phân tích"})
    rec |= {"link": meta.get("webpage_url") or meta.get("source"), "uploader": meta.get("uploader") or meta.get("channel"),
            "views": meta.get("view_count"), "duration": meta["duration"], "dir": str(out.relative_to(ws.root))}
    ws.save()
    sheets = sorted(p.name for p in out.glob("sheet_*.jpg"))
    print(json.dumps({"id": rid, "dir": str(out), "duration": meta["duration"], "cuts": meta["cuts"], "sheets": sheets,
                      "transcript": (out / "transcript.json").exists()}, ensure_ascii=False))


# ---------- catalog ----------
def push(ws, rid):
    f = ws.refs / rid / "analysis.json"
    if not f.exists():
        die(f"chưa có {f}. Claude phải viết analysis.json trước khi push")
    a = json.loads(f.read_text())
    missing = [x["key"] for x in ws.fields() if x["key"] not in a or a[x["key"]] in ("", None, [], {})]
    if missing:
        die("analysis.json thiếu khoá (hoặc để trống, chỗ nào không rõ thì ghi \"(không rõ)\"): " + ", ".join(missing))
    labels = ws.cfg.get("library", {}).get("match_labels", ["có", "gần giống", "thiếu"])
    ids = lib_ids(ws)
    errs = []
    for i, m in enumerate(a.get("matches", [])):
        if not isinstance(m, dict) or m.get("status") not in labels:
            errs.append(f"matches[{i}].status phải thuộc {labels}")
        elif m["status"] == labels[-1]:
            if m.get("match"):
                errs.append(f"matches[{i}]: status '{labels[-1]}' thì match phải để null")
        elif not ids:
            errs.append("chưa có catalog tài nguyên (library.json): chạy 'library' + mô tả trước khi đối chiếu")
            break
        elif m.get("match") not in ids:
            errs.append(f"matches[{i}].match '{m.get('match')}' không có trong catalog tài nguyên (id phải khớp library.json)")
    for i, s_ in enumerate(a.get("remake_plan", [])):
        use = s_.get("use") if isinstance(s_, dict) else None
        if use and use not in ids:
            errs.append(f"remake_plan[{i}].use '{use}' không có trong catalog tài nguyên")
        if isinstance(s_, dict) and not use and not s_.get("gap"):
            errs.append(f"remake_plan[{i}]: không có 'use' thì phải ghi 'gap' (thiếu gì)")
    if errs:
        die("; ".join(errs))
    cov = {l: sum(1 for m in a.get("matches", []) if m.get("status") == l) for l in labels}
    rec = ws.db.setdefault(rid, {"id": rid, "added": str(date.today())})
    rec |= {x["key"]: a[x["key"]] for x in ws.fields()} | {"status": "Đã phân tích", "coverage": cov}
    ws.save()
    export(ws)
    gaps(ws)
    print(f"đã ghi {rid}: độ phủ {cov}")
    und = [k for k, v in lib_db(ws)[1].items() if not v.get("desc") and not v.get("missing_file")]
    if und:
        print(f"⚠ catalog tài nguyên còn {len(und)} mục chưa mô tả ({', '.join(und[:5])}…): độ phủ trên có thể sai")


def flat(v):
    if isinstance(v, list):
        return " / ".join(json.dumps(i, ensure_ascii=False) if isinstance(i, (dict, list)) else str(i) for i in v)
    return "" if v is None else str(v)


def export(ws):
    keys = ["id", "link", "uploader", "views", "duration", "status", "added", "coverage"] + [x["key"] for x in ws.fields()] + ["note"]
    rows = [ws.db[k] for k in sorted(ws.db)]
    with open(ws.root / "catalog.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for r in rows:
            w.writerow([flat(r.get(k)) for k in keys])
    L = [f"# {ws.cfg.get('name', 'Catalog nguồn')}", "", f"{len(rows)} nguồn. Tạo bởi ref-catalog, đừng sửa tay (sửa bằng `set`/`push`).", ""]
    for r in rows:
        L += [f"## {r['id']}: {flat(r.get('summary'))[:80] or r.get('link') or ''}", "",
              f"- Link: {r.get('link') or ''}", f"- Trạng thái: {r.get('status')} · {r.get('duration')}s · {r.get('uploader') or ''}" + (f" · độ phủ: {r['coverage']}" if r.get("coverage") else "")]
        for x in ws.fields():
            if x["key"] != "summary" and r.get(x["key"]) not in (None, "", []):
                L.append(f"- **{x['label']}**: {flat(r[x['key']])}")
        L.append("")
    (ws.root / "CATALOG.md").write_text("\n".join(L))


def lib_db(ws):
    f = ws.root / "library.json"
    return f, (json.loads(f.read_text()) if f.exists() else {})


def lib_ids(ws):
    return {k for k, v in lib_db(ws)[1].items() if not v.get("missing_file")}


AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
IMAGE = {".png", ".jpg", ".jpeg", ".webp"}


def lib_sources(ws):
    """Các nguồn tài nguyên [{path, label}]. Hỗ trợ cấu hình cũ 'dir' (một thư mục trong workspace)."""
    lc = ws.cfg.get("library", {})
    src = [dict(x) for x in lc.get("sources", []) if x.get("path")]
    if not src and lc.get("dir") and (ws.root / lc["dir"]).exists():
        src = [{"path": lc["dir"], "label": lc["dir"]}]
    for x in src:
        pth = Path(x["path"]).expanduser()
        x["abs"] = pth if pth.is_absolute() else (ws.root / pth).resolve()
        x.setdefault("label", x["abs"].name)
    return src


def lib_src(ws, a):
    lc = ws.cfg.setdefault("library", {})
    src = lc.setdefault("sources", [])
    if not a:
        cur = lib_sources(ws)
        if not cur:
            print("chưa chỉ định nguồn tài nguyên nào. Hỏi người dùng tài nguyên nằm ở đâu rồi: lib-src add <thư-mục> [label=…]")
        for x in cur:
            print(f"{x['label']}\t{x['abs']}\t{'' if x['abs'].exists() else '(không tồn tại)'}")
        return
    op = a.pop(0)
    if op == "add":
        if not a:
            die("thiếu thư mục: lib-src add <thư-mục> [label=…]")
        pth = Path(a.pop(0)).expanduser().resolve()
        if not pth.is_dir():
            die(f"không thấy thư mục {pth}")
        label = next((kv.split("=", 1)[1] for kv in a if kv.startswith("label=")), pth.name)
        if any(Path(x["path"]).expanduser().resolve() == pth for x in src):
            die(f"{pth} đã có trong nguồn")
        src.append({"path": str(pth), "label": label})
        print(f"đã thêm nguồn '{label}': {pth}. Chạy 'library' để quét.")
    elif op == "new":
        pth = Path(a[0]).expanduser().resolve() if a else ws.root / "tai-nguyen"
        for sub in ("video", "anh", "nhac", "sfx", "template"):
            (pth / sub).mkdir(parents=True, exist_ok=True)
        if not any(Path(x["path"]).expanduser().resolve() == pth for x in src):
            src.append({"path": str(pth), "label": pth.name})
        print(f"đã tạo thư mục tài nguyên {pth} (video/ anh/ nhac/ sfx/ template/) và thêm làm nguồn '{pth.name}'. "
              f"Bỏ tài nguyên vào đó (kể cả thứ tìm được theo GAPS.md) rồi chạy 'library'.")
    elif op == "rm":
        key = a[0] if a else die("thiếu thư mục hoặc label")
        keep = [x for x in src if x.get("label") != key and Path(x["path"]).expanduser().resolve() != Path(key).expanduser().resolve()]
        if len(keep) == len(src):
            die(f"không có nguồn '{key}'")
        lc["sources"] = keep
        print(f"đã bỏ nguồn '{key}'. Chạy 'library' để cập nhật (mục cũ được đánh dấu missing_file).")
    else:
        die("lib-src [add <thư-mục> [label=…] | new [thư-mục] | rm <thư-mục|label>]")
    ws.cfg_f.write_text(json.dumps(ws.cfg, ensure_ascii=False, indent=2) + "\n")


def library(ws, force):
    from PIL import Image, ImageDraw
    lc = ws.cfg.get("library", {})
    src = lib_sources(ws)
    if not src:
        die("chưa chỉ định nguồn tài nguyên. Hỏi người dùng tài nguyên (clip, ảnh, nhạc, template…) nằm ở thư mục nào, "
            "có thể nhiều thư mục, chủ đề nào cũng được, rồi chạy: lib-src add <thư-mục> [label=…]. "
            "Người dùng chưa có kho thì bỏ qua bước này: mọi thành phần của nguồn sẽ là 'thiếu'.")
    ext = {e.lower() for e in lc.get("extensions", [".mp4"])}
    out = ws.root / "thumbs"
    found = []  # (path, label)
    for x in src:
        if not x["abs"].exists():
            print(f"⚠ bỏ qua nguồn '{x['label']}': không thấy {x['abs']}")
            continue
        for p in sorted(x["abs"].rglob("*")):
            if p.suffix.lower() in ext and p.is_file() and out not in p.parents and not any(q.startswith(".") for q in p.parts):
                found.append((p, x["label"]))
    if not found:
        die(f"không có tệp nào trong các nguồn ({', '.join(str(x['abs']) for x in src)}), đuôi {sorted(ext)}")
    # id = tên tệp; trùng tên giữa các thư mục thì thêm tên thư mục cha
    stems = [p.stem for p, _ in found]
    items = []
    for p, label in found:
        i = p.stem if stems.count(p.stem) == 1 else f"{p.parent.name}-{p.stem}"
        items.append((i, p, label))
    ids = [i for i, _, _ in items]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        die(f"trùng tên tệp kể cả khi thêm tên thư mục (id phải duy nhất): {sorted(dup)}")
    out.mkdir(exist_ok=True)
    W = H = 300
    for i, p, _ in items:
        t = out / f"{i}.jpg"
        if t.exists() and not force:
            continue
        if p.suffix.lower() in AUDIO:
            continue  # nhạc/âm thanh: không có hình, lưới chỉ in tên
        if p.suffix.lower() in IMAGE:
            im = Image.open(p).convert("RGB")
            im.thumbnail((W, H))
            im.save(t, quality=85)
        else:
            dur = probe(p)["duration"]
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur * 0.4:.2f}", "-i", str(p), "-frames:v", "1", "-vf",
                 f"scale={W}:{H}:force_original_aspect_ratio=decrease", str(t)])
    for old in out.glob("grid_*.jpg"):
        old.unlink()
    c, r_, fnt = 5, 4, font(15)
    per = c * r_
    for g in range(0, len(items), per):
        sheet = Image.new("RGB", (c * W, r_ * (H + 22)), "white")
        d = ImageDraw.Draw(sheet)
        for k, (i, p, _) in enumerate(items[g:g + per]):
            x, y = (k % c) * W, (k // c) * (H + 22)
            if (out / f"{i}.jpg").exists():
                im = Image.open(out / f"{i}.jpg")
                sheet.paste(im, (x + (W - im.width) // 2, y))
            else:
                d.text((x + W // 2 - 30, y + H // 2 - 10), "(âm thanh)", font=fnt, fill="gray")
            d.text((x + 4, y + H + 3), i[:38], font=fnt, fill="black")
        sheet.save(out / f"grid_{g // per + 1:02d}.jpg", quality=80)
    f, db = lib_db(ws)
    new = 0
    for i, p, label in items:
        sfx = p.suffix.lower()
        kind = "ảnh" if sfx in IMAGE else "âm thanh" if sfx in AUDIO else "video"
        info = {"file": str(p), "source": label, "kind": kind}
        if kind != "ảnh":
            info["duration"] = probe(p)["duration"]
        if i not in db:
            db[i] = {"desc": "", "tags": [], "note": ""}
            new += 1
        db[i] |= info
        db[i].pop("missing_file", None)
    for k in db:
        if k not in ids:
            db[k]["missing_file"] = True
    f.write_text(json.dumps(db, ensure_ascii=False, indent=2))
    lib_md(ws)
    by = {}
    for _, _, label in items:
        by[label] = by.get(label, 0) + 1
    print(f"{len(items)} tệp từ {len(by)} nguồn ({', '.join(f'{k}: {v}' for k, v in by.items())}) -> {out} "
          f"({(len(items) + per - 1) // per} lưới), {new} mục mới trong library.json, "
          f"{sum(1 for v in db.values() if not v['desc'] and not v.get('missing_file'))} mục chưa mô tả (chạy lib-check)")


def lib_md(ws):
    _, db = lib_db(ws)
    db = {k: v for k, v in db.items() if not v.get("missing_file")}
    L = ["# Catalog tài nguyên", "", f"{len(db)} mục. Sinh từ library.json (sửa bằng `lib-set`, đừng sửa tay). "
         "Agent dùng `id` ở đầu mỗi dòng khi đối chiếu (`matches[].match`).", ""]
    for k in sorted(db, key=lambda k: (db[k].get("source", ""), k)):
        v = db[k]
        if v.get("missing_file"):
            continue
        tg = ", ".join(v.get("tags", []))
        L.append(f"- `{k}` [{v.get('kind')}{', ' + str(v['duration']) + 's' if v.get('duration') else ''}]: "
                 f"{v.get('desc') or '(chưa mô tả)'}" + (f" · nguồn: {v['source']}" if v.get("source") else "") + (f" · tag: {tg}" if tg else "") + (f" · ⚠ {v['note']}" if v.get("note") else ""))
    (ws.root / "LIBRARY.md").write_text("\n".join(L) + "\n")


def lib_set(ws, a):
    f, db = lib_db(ws)
    k = a.pop(0)
    if k not in db:
        die(f"không có tài nguyên '{k}' trong library.json")
    for kv in a:
        key, _, val = kv.partition("=")
        if key == "desc":
            db[k]["desc"] = val
        elif key == "tags":
            db[k]["tags"] = [t.strip() for t in val.split(",") if t.strip()]
        elif key == "note":
            db[k]["note"] = val
        else:
            die(f"khoá lạ '{key}' (desc, tags, note)")
    f.write_text(json.dumps(db, ensure_ascii=False, indent=2))
    lib_md(ws)


def lib_check(ws):
    _, db = lib_db(ws)
    db = {k: v for k, v in db.items() if not v.get("missing_file")}
    if not db:
        die("chưa có catalog tài nguyên: chỉ định nguồn bằng 'lib-src add <thư-mục>' rồi chạy 'library'")
    todo = [k for k, v in sorted(db.items()) if not v.get("desc")]
    print(f"{len(db) - len(todo)}/{len(db)} mục đã mô tả" + ("" if not todo else ". Chưa mô tả: " + ", ".join(todo)))


def gaps(ws):
    labels = ws.cfg.get("library", {}).get("match_labels", ["có", "gần giống", "thiếu"])
    rows = {}
    for rid, r in sorted(ws.db.items()):
        for m in r.get("matches", []):
            if isinstance(m, dict) and m.get("status") in labels[1:]:
                rows.setdefault((m["status"], m.get("desc", "")), []).append((rid, m.get("match") or ""))
    L = ["# Còn thiếu / gần giống", "", "Gom từ catalog nguồn. Làm hoặc tìm bản đúng rồi `library` + `lib-set` để bản đồ đầy lên.", ""]
    for st in labels[1:]:
        L += [f"## {st}", ""]
        for (s_, desc), refs in sorted(rows.items(), key=lambda x: -len(x[1])):
            if s_ == st:
                L.append(f"- {desc} (cần ở {len(refs)} nguồn: {', '.join(r for r, _ in refs)})" +
                         (f", tạm dùng `{refs[0][1]}`" if refs[0][1] else ""))
        L.append("")
    (ws.root / "GAPS.md").write_text("\n".join(L))
    print(f"GAPS.md: {sum(len(v) for v in rows.values())} mục từ {len({r for v in rows.values() for r, _ in v})} nguồn")


# ---------- doctor: kiểm tra máy ----------
PLUGIN_JSON_URL = "https://raw.githubusercontent.com/duynguyeenx96/claudewithduy/main/plugins/ref-catalog/.claude-plugin/plugin.json"


def _fetch_json(url):
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ref-catalog-doctor"}), timeout=4) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _ver(v):
    return tuple(int(x) for x in "".join(c if c.isdigit() or c == "." else " " for c in v).split()[0].split(".") if x) if v else ()


def doctor(ws_root):
    import platform
    osname = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}.get(platform.system(), platform.system())
    mac, win = osname == "macOS", osname == "Windows"
    inst = (lambda pkg_brew, pkg_apt, pkg_win: f"brew install {pkg_brew}" if mac else f"winget install {pkg_win}" if win
            else f"sudo apt install {pkg_apt}")
    rows, missing, stale = [], [], []

    def row(ok, name, ver, note=""):
        rows.append(("✓" if ok is True else "⚠" if ok == "warn" else "✗", name, ver, note))

    print(f"Hệ điều hành: {osname} {platform.mac_ver()[0] if mac else platform.release()} ({platform.machine()})")
    py = sys.version.split()[0]
    row(sys.version_info >= (3, 9), "python3", py, "" if sys.version_info >= (3, 9) else "cần 3.9 trở lên")
    try:
        import PIL
        row(True, "Pillow", PIL.__version__)
    except ImportError:
        row(False, "Pillow", "-", f"{sys.executable} -m pip install Pillow")
        missing.append("Pillow")
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool):
            v = (run([tool, "-version"]).stdout.split("\n") or [""])[0].split(" ")[2] if run([tool, "-version"]).stdout else "?"
            row(True if (_ver(v) or (99,))[0] >= 5 else "warn", tool, v, "" if (_ver(v) or (99,))[0] >= 5 else "bản cũ, nên cập nhật")
        else:
            row(False, tool, "-", inst("ffmpeg", "ffmpeg", "Gyan.FFmpeg"))
            missing.append(tool)
    if shutil.which("yt-dlp"):
        v = run(["yt-dlp", "--version"]).stdout.strip()
        latest = (_fetch_json("https://pypi.org/pypi/yt-dlp/json") or {}).get("info", {}).get("version")
        try:
            age = (date.today() - date(*[int(x) for x in v.split(".")[:3]])).days
        except Exception:
            age = None
        real = os.path.realpath(shutil.which("yt-dlp"))
        how = ("brew upgrade yt-dlp" if "/Cellar/" in real or "homebrew" in real.lower()
               else "pip install -U yt-dlp" if "python" in real.lower() or "site-packages" in real or "/.local/" in real
               else "winget upgrade yt-dlp.yt-dlp" if win else "yt-dlp -U")
        if latest and _ver(latest) > _ver(v):
            row("warn", "yt-dlp", v, f"có bản mới {latest}: {how} (YouTube/TikTok hay đổi, bản cũ dễ tải lỗi)")
            stale.append("yt-dlp")
        elif not latest and age is not None and age > 60:
            row("warn", "yt-dlp", v, f"đã {age} ngày, nên cập nhật: {how}")
            stale.append("yt-dlp")
        else:
            row(True, "yt-dlp", v, "bản mới nhất" if latest else "")
    else:
        row(False, "yt-dlp", "-", "brew install yt-dlp" if mac else "winget install yt-dlp.yt-dlp" if win else "pip install -U yt-dlp")
        missing.append("yt-dlp")
    cfg = {}
    if (ws_root / "config.json").exists():
        cfg = json.loads((ws_root / "config.json").read_text())
    model = Path(cfg.get("transcribe", {}).get("model") or json.loads((HERE.parent / "config.example.json").read_text())["transcribe"]["model"]).expanduser()
    if shutil.which("whisper-cli"):
        row(True if model.exists() else "warn", "whisper-cli", "có", "" if model.exists() else
            f"thiếu model {model.name}: tải về {model} (huggingface.co/ggerganov/whisper.cpp), không có vẫn chạy được nhưng không nghe lời")
    else:
        row("warn", "whisper-cli (tuỳ chọn)", "-", ("brew install whisper-cpp" if mac else "build whisper.cpp") +
            "; không có thì chỉ phân tích bằng khung hình")
    here_v = json.loads((HERE.parent.parent.parent / ".claude-plugin" / "plugin.json").read_text()).get("version", "?") \
        if (HERE.parent.parent.parent / ".claude-plugin" / "plugin.json").exists() else "?"
    remote = (_fetch_json(PLUGIN_JSON_URL) or {}).get("version")
    if remote and _ver(remote) > _ver(here_v):
        row("warn", "plugin ref-catalog", here_v, f"có bản {remote}: chạy /plugin rồi cập nhật ref-catalog")
        stale.append("plugin")
    else:
        row(True, "plugin ref-catalog", here_v, "bản mới nhất" if remote else "(không kiểm tra được bản mới: offline?)")
    w = max(len(r[1]) for r in rows)
    for mark, name, ver, note in rows:
        print(f"  {mark} {name.ljust(w)}  {ver:<12} {note}".rstrip())
    if cfg:
        src = lib_sources(WS(ws_root))
        print(f"Workspace: {ws_root} · {len(src)} nguồn tài nguyên" + ("" if src else " (chưa chỉ định: lib-src add <thư-mục> hoặc lib-src new)"))
    else:
        print(f"Workspace: chưa có ở {ws_root} (chạy init)")
    if missing:
        print("THIẾU: " + ", ".join(missing) + ". Cài theo lệnh ở trên rồi chạy lại doctor.")
    elif stale:
        print("CHẠY ĐƯỢC, nên cập nhật: " + ", ".join(stale))
    else:
        print("SẴN SÀNG")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = a.pop(0)
    if cmd == "doctor":
        root = os.environ.get("REF_CATALOG_WS", ".")
        if "--ws" in a:
            root = a[a.index("--ws") + 1]
        doctor(Path(root).expanduser().resolve())
        return
    if cmd == "init":
        root = Path(a[0] if a else ".").expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        if not (root / "config.json").exists():
            shutil.copy(HERE.parent / "config.example.json", root / "config.json")
        (root / "refs").mkdir(exist_ok=True)
        print(f"workspace: {root}\nChỉ định nguồn tài nguyên: 'lib-src add <thư-mục> [label=…]' (bao nhiêu thư mục cũng được), "
              f"rồi 'library'. Sửa {root / 'config.json'} nếu cần (Whisper, các trường phân tích).")
        return
    ws = open_ws(a)
    if cmd == "add":
        if not a:
            die("thiếu link/file")
        for src in a:
            dup = next((k for k, v in ws.db.items() if v.get("link") == src), None)
            if dup:
                print(f"{src} đã có: {dup}")
                continue
            fetch(ws, ws.next_id(), src)
        if not lib_sources(ws):
            print("⚠ chưa chỉ định nguồn tài nguyên: hỏi người dùng tài nguyên nằm ở thư mục nào (có thể nhiều thư mục) "
                  "rồi 'lib-src add <thư-mục> label=…' + 'library'. Chưa có kho thì đối chiếu sẽ ra toàn 'thiếu'.")
    elif cmd == "fetch":
        fetch(ws, a[0])
    elif cmd == "push":
        push(ws, a[0])
    elif cmd == "set":
        rid = a.pop(0)
        rec = ws.db.setdefault(rid, {"id": rid})
        for kv in a:
            k, _, v = kv.partition("=")
            rec[k] = v
        ws.save()
        export(ws)
    elif cmd == "list":
        for k in sorted(ws.db):
            r = ws.db[k]
            cv = r.get("coverage")
            print(f"{k}\t{r.get('status', '')}\t{r.get('duration', '')}s\t{'/'.join(str(v) for v in cv.values()) if cv else '-'}\t{flat(r.get('summary'))[:60] or r.get('link', '')}")
    elif cmd == "export":
        export(ws)
        print("đã xuất CATALOG.md + catalog.csv")
    elif cmd == "lib-src":
        lib_src(ws, a)
    elif cmd == "library":
        library(ws, "--all" in a)
    elif cmd == "lib-set":
        lib_set(ws, a)
    elif cmd == "lib-check":
        lib_check(ws)
    elif cmd == "gaps":
        gaps(ws)
    else:
        die(f"lệnh lạ: {cmd}. Xem --help")


if __name__ == "__main__":
    main()
