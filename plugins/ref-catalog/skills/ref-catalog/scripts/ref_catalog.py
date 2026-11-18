#!/usr/bin/env python3
"""ref-catalog: luồng nguồn tham khảo -> tải -> phân tích -> đối chiếu với tài nguyên hiện có -> kế hoạch remake.
Catalog tài nguyên (library.json) là BẢN ĐỒ để agent đối chiếu nguồn với những gì bạn đang có.

  Bước 1, soạn catalog tài nguyên (làm trước):
  ref_catalog.py library [--all]           quét thư mục tài nguyên: thumbs, lưới có tên, thêm mục mới vào library.json
  ref_catalog.py lib-set <id> desc=… tags=a,b note=…   ghi mô tả/tag cho một tài nguyên (Claude điền sau khi xem lưới)
  ref_catalog.py lib-check                 tài nguyên nào chưa mô tả (bản đồ chưa đủ dùng)
  Bước 2-4, nguồn:
  ref_catalog.py init [thư-mục]            tạo workspace (config.json, refs/, library/)
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
    und = [k for k, v in lib_db(ws)[1].items() if not v.get("desc")]
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
    return set(lib_db(ws)[1])


def library(ws, force):
    from PIL import Image, ImageDraw
    lc = ws.cfg.get("library", {})
    lib = ws.root / lc.get("dir", "library")
    ext = {e.lower() for e in lc.get("extensions", [".mp4"])}
    items = sorted(p for p in lib.rglob("*") if p.suffix.lower() in ext and "thumbs" not in p.parts) if lib.exists() else []
    if not items:
        die(f"không có tệp nào trong {lib} (đuôi {sorted(ext)})")
    ids = [p.stem for p in items]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        die(f"trùng tên tệp (id phải duy nhất): {sorted(dup)}")
    out = lib / "thumbs"
    out.mkdir(exist_ok=True)
    W = H = 300
    for p in items:
        t = out / f"{p.stem}.jpg"
        if t.exists() and not force:
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
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
        for i, p in enumerate(items[g:g + per]):
            x, y = (i % c) * W, (i // c) * (H + 22)
            if (out / f"{p.stem}.jpg").exists():
                im = Image.open(out / f"{p.stem}.jpg")
                sheet.paste(im, (x + (W - im.width) // 2, y))
            d.text((x + 4, y + H + 3), p.stem[:38], font=fnt, fill="black")
        sheet.save(out / f"grid_{g // per + 1:02d}.jpg", quality=80)
    f, db = lib_db(ws)
    new = 0
    for p in items:
        kind = "ảnh" if p.suffix.lower() in {".png", ".jpg", ".jpeg"} else "video"
        info = {"file": str(p.relative_to(ws.root)), "kind": kind}
        if kind == "video":
            info["duration"] = probe(p)["duration"]
        if p.stem not in db:
            db[p.stem] = {"desc": "", "tags": [], "note": ""}
            new += 1
        db[p.stem] |= info
    gone = [k for k in db if k not in ids]
    for k in gone:
        db[k]["missing_file"] = True
    f.write_text(json.dumps(db, ensure_ascii=False, indent=2))
    lib_md(ws)
    print(f"{len(items)} tệp -> {out} ({(len(items) + per - 1) // per} lưới), {new} mục mới trong library.json, "
          f"{sum(1 for v in db.values() if not v['desc'])} mục chưa mô tả (chạy lib-check)")


def lib_md(ws):
    _, db = lib_db(ws)
    L = ["# Catalog tài nguyên", "", f"{len(db)} mục. Sinh từ library.json (sửa bằng `lib-set`, đừng sửa tay). "
         "Agent dùng `id` ở đầu mỗi dòng khi đối chiếu (`matches[].match`).", ""]
    for k in sorted(db):
        v = db[k]
        tg = ", ".join(v.get("tags", []))
        L.append(f"- `{k}` [{v.get('kind')}{', ' + str(v['duration']) + 's' if v.get('duration') else ''}]: "
                 f"{v.get('desc') or '(chưa mô tả)'}" + (f" · tag: {tg}" if tg else "") + (f" · ⚠ {v['note']}" if v.get("note") else ""))
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
    if not db:
        die("chưa có catalog tài nguyên, chạy 'library' trước")
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


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = a.pop(0)
    if cmd == "init":
        root = Path(a[0] if a else ".").expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        if not (root / "config.json").exists():
            shutil.copy(HERE.parent / "config.example.json", root / "config.json")
        (root / "refs").mkdir(exist_ok=True)
        (root / json.loads((root / "config.json").read_text()).get("library", {}).get("dir", "library")).mkdir(exist_ok=True)
        print(f"workspace: {root}\nSửa {root / 'config.json'} (niche, model Whisper, các trường phân tích) rồi chạy 'add <link>'")
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
