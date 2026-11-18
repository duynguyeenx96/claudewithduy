#!/usr/bin/env python3
"""CapCut (macOS) draft helper: inspect / transcribe / frames / effects / apply / restore.

Usage:
  capcut.py list
  capcut.py inspect   "<project name>"
  capcut.py transcribe "<project name>" [--model PATH]
  capcut.py frames    "<project name>" OUTDIR
  capcut.py effects
  capcut.py apply     "<project name>" plan.json
  capcut.py restore   "<project name>" BACKUP_DIR
"""
import copy, glob, hashlib, json, os, shutil, subprocess, sys, time, uuid

import numpy as np

HOME = os.path.expanduser("~")
DRAFTS = f"{HOME}/Movies/CapCut/User Data/Projects/com.lveditor.draft"
CACHE_FX = f"{HOME}/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/User Data/Cache/effect"
SFX_DIR = os.environ.get("CAPCUT_SFX_DIR", f"{HOME}/Documents/Nhạc/71 SFX PACK")
BACKUP_ROOT = f"{HOME}/Movies/CapCut/capcut-edit-backups"
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = json.loads(open(os.path.join(HERE, "templates.json")).read().replace("@HOME@", HOME))
WHISPER_MODELS = [
    f"{HOME}/Library/Containers/tech.lighton.media.VideoUtilsAppleNative/Data/Library/Application Support/CreatorUtils/WhisperModels/ggml-medium.bin",
    f"{HOME}/Library/Containers/maccatalyst.com.frontrow.vlog/Data/Documents/FlowWhisperModel/whisper_base_v1.bundle/ggml-base.bin",
]
S = 1_000_000
R = 16000

# Effects confirmed is_vip == "0" (free). Anything else -> use keyframe animations instead.
FREE_EFFECTS = {
    "Typewriter": "7210980292243231233",   # text in
    "Blur Fade": "7648935884636687624",    # text out
    "Mix": "6724845717472416269",          # transition (vertical glitch)
    "Slow Fade": "7626674915898445074",    # transition
}


def nid():
    return str(uuid.uuid4()).upper()


# ---------------------------------------------------------------- project lookup
def projects():
    meta = json.load(open(os.path.join(DRAFTS, "root_meta_info.json")))
    return [(x.get("draft_name"), x.get("draft_fold_path")) for x in meta.get("all_draft_store", [])]


def project_dir(name):
    hits = [p for n, p in projects() if n == name] or [p for n, p in projects() if n and n.lower() == name.lower()]
    if not hits:
        hits = [p for n, p in projects() if n and name.lower() in n.lower()]
    if len(hits) != 1:
        sys.exit(f"Project '{name}' -> {len(hits)} matches: {hits or [n for n, _ in projects()]}")
    return hits[0]


def main_timeline(pdir):
    pj = os.path.join(pdir, "Timelines/project.json")
    return json.load(open(pj))["main_timeline_id"] if os.path.exists(pj) else None


def draft_paths(pdir):
    """Every on-disk copy of the main timeline draft that must be kept in sync."""
    ps = [os.path.join(pdir, p) for p in ("draft_info.json", "draft_info.json.bak", "template-2.tmp")]
    mt = main_timeline(pdir)
    if mt:
        ps += [os.path.join(pdir, "Timelines", mt, p) for p in ("draft_info.json", "draft_info.json.bak", "template-2.tmp")]
    return [p for p in ps if os.path.exists(p)]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def load(pdir):
    return json.load(open(os.path.join(pdir, "draft_info.json")))


def capcut_running():
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0


def quit_capcut():
    if capcut_running():
        subprocess.run(["osascript", "-e", 'quit app "CapCut"'], capture_output=True)
        for _ in range(20):
            time.sleep(0.5)
            if not capcut_running():
                break
    if capcut_running():
        sys.exit("CapCut is still running - ask the user to close it, then retry.")


# ---------------------------------------------------------------- material helpers
def mat_index(mats):
    return {x["id"]: (k, x) for k, v in mats.items() if isinstance(v, list) for x in v if isinstance(x, dict) and "id" in x}


def all_drafts(mats, acc=None):
    acc = [] if acc is None else acc
    for dr in mats.get("drafts", []):
        acc.append(dr)
        all_drafts((dr.get("draft") or {}).get("materials", {}), acc)
    return acc


def seg_draft(seg, mats, top_mats, material=None):
    """Compound clip -> its sub-draft. Linked either by a drafts id in extra_material_refs, or (nested
    compounds) by a material path .../combination/<combination_id>_audio.m4a (that file is obfuscated)."""
    pools = all_drafts(mats) + all_drafts(top_mats)
    for r in seg["extra_material_refs"]:
        for dr in pools:
            if dr["id"] == r:
                return dr
    path = (material or {}).get("path") or ""
    if "/combination/" in path:
        cid = os.path.basename(path).split("_")[0]
        for dr in pools:
            if dr.get("combination_id") == cid:
                return dr
    return None


def fix_path(p, pdir):
    if p and p.startswith("##_draftpath_placeholder_"):
        p = pdir + p[p.index("_##") + 3:]
    return p


# ---------------------------------------------------------------- inspect
def cmd_inspect(name):
    pdir = project_dir(name)
    d = load(pdir)
    print("dir:", pdir)
    print("main timeline:", main_timeline(pdir), "| CapCut running:", capcut_running())
    print("copies in sync:", len({md5(p) for p in draft_paths(pdir) if p.endswith('.json')}) == 1)
    print("duration %.2fs canvas %s fps %s video_mute %s" % (d["duration"] / S, d["canvas_config"], d["fps"], d["config"].get("video_mute")))
    idx = mat_index(d["materials"])
    for ti, t in enumerate(d["tracks"]):
        print(f"TRACK {ti} {t['type']} ({len(t['segments'])} seg)")
        for s in t["segments"]:
            tr, st = s["target_timerange"], s.get("source_timerange") or {}
            k, m = idx.get(s["material_id"], ("?", {}))
            label = m.get("material_name") or m.get("name") or ""
            if k == "texts":
                label = json.loads(m["content"])["text"].replace("\n", " / ")
            extra = []
            if seg_draft(s, d["materials"], d["materials"]):
                extra.append("COMPOUND")
            if s.get("common_keyframes"):
                extra.append("kf")
            for r in s["extra_material_refs"]:
                kk, x = idx.get(r, (None, None))
                if kk == "material_animations" and x["animations"]:
                    extra.append("anim:" + ",".join(a["name"] for a in x["animations"]))
                if kk == "transitions":
                    extra.append("trans:" + x["name"])
            print("   %7.3f-%7.3f src %7.3f x%.2f vol %.2f | %s %s %s" % (
                tr["start"] / S, (tr["start"] + tr["duration"]) / S, (st.get("start") or 0) / S,
                s.get("speed") or 1, s.get("volume") or 0, k, label[:60], " ".join(extra)))
            if s.get("clip") and t["type"] == "video":
                print("              clip scale %.3f pos %s" % (s["clip"]["scale"]["x"], s["clip"]["transform"]))


# ---------------------------------------------------------------- audio render (for transcription)
_decoded = {}
MISSING = set()


def decode(path):
    if path not in _decoded:
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(R), "-f", "f32le", "-"],
                           capture_output=True)
        _decoded[path] = np.frombuffer(r.stdout, dtype=np.float32) if r.returncode == 0 and r.stdout else None
        if _decoded[path] is None:
            MISSING.add(path)
    return _decoded[path]


def tempo(a, sp):
    if abs(sp - 1) < 1e-3 or len(a) < 2:
        return a
    n = max(1, int(len(a) / sp))
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)


def render(draft, top_mats, pdir, depth=0):
    mats = draft["materials"]
    idx = mat_index(mats)
    end = max([draft.get("duration") or 0] + [sg["target_timerange"]["start"] + sg["target_timerange"]["duration"]
                                              for t in draft["tracks"] for sg in t["segments"]])
    out = np.zeros(int(end / S * R) + R, dtype=np.float32)
    main_video_done = False
    for t in draft["tracks"]:
        if t["type"] not in ("video", "audio"):
            continue
        is_main = t["type"] == "video" and not main_video_done
        if t["type"] == "video":
            main_video_done = True
        if is_main and depth == 0 and draft["config"].get("video_mute"):
            continue
        for s in t["segments"]:
            vol = s.get("volume", 1.0) or 0
            if vol <= 0:
                continue
            k, m = idx.get(s["material_id"], (None, {}))
            sp = s.get("speed") or 1.0
            st = (s.get("source_timerange") or {}).get("start", 0) / S
            tgt0, tdur = s["target_timerange"]["start"] / S, s["target_timerange"]["duration"] / S
            sub = seg_draft(s, mats, top_mats, m)
            if sub:
                arr = render(sub["draft"], top_mats, pdir, depth + 1)
            elif m.get("type") == "photo":
                continue
            else:
                arr = decode(fix_path(m.get("path", ""), pdir))
            if arr is None:
                continue
            piece = tempo(arr[int(st * R):int((st + tdur * sp) * R)], sp) * vol
            a = int(tgt0 * R)
            piece = piece[:max(0, len(out) - a)]
            out[a:a + len(piece)] += piece
    return out


def cmd_transcribe(name, model=None):
    pdir = project_dir(name)
    d = load(pdir)
    audio = render(d, d["materials"], pdir)[: int(d["duration"] / S * R)]
    peak = float(np.max(np.abs(audio))) or 1.0
    wav = os.path.join("/tmp" if not os.environ.get("TMPDIR") else os.environ["TMPDIR"], "capcut_timeline.wav")
    import wave
    w = wave.open(wav, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(R)
    w.writeframes((audio / peak * 0.9 * 32767).astype(np.int16).tobytes()); w.close()
    model = model or next((p for p in WHISPER_MODELS if os.path.exists(p)), None)
    if not model:
        sys.exit("No whisper ggml model found; pass --model PATH")
    for p in sorted(MISSING):
        print("# WARNING missing/undecodable source (its audio is silent in the transcript):", p, flush=True)
    print(f"# timeline audio: {wav} ({len(audio) / R:.1f}s), model: {os.path.basename(model)}", flush=True)
    subprocess.run(["whisper-cli", "-m", model, "-l", "vi", "-f", wav, "-np", "-ml", "45"], stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- frames
def leaf(seg, mats, top_mats, idx):
    """Resolve a (possibly compound) video segment to (path, source_time_of_its_middle)."""
    sub = seg_draft(seg, mats, top_mats)
    if sub:
        sd = sub["draft"]
        sidx = mat_index(sd["materials"])
        vt = next((t for t in sd["tracks"] if t["type"] == "video" and t["segments"]), None)
        return leaf(vt["segments"][0], sd["materials"], top_mats, sidx) if vt else (None, 0)
    k, m = idx.get(seg["material_id"], (None, {}))
    st = (seg.get("source_timerange") or {}).get("start", 0) / S
    return m.get("path"), st + seg["target_timerange"]["duration"] / S * (seg.get("speed") or 1) / 2


def cmd_frames(name, outdir):
    pdir = project_dir(name)
    d = load(pdir)
    os.makedirs(outdir, exist_ok=True)
    for f in glob.glob(os.path.join(outdir, "f*.jpg")):
        os.remove(f)
    idx = mat_index(d["materials"])
    vt = next(t for t in d["tracks"] if t["type"] == "video")
    for i, s in enumerate(vt["segments"]):
        path, t = leaf(s, d["materials"], d["materials"], idx)
        path = fix_path(path, pdir)
        tr = s["target_timerange"]
        print("%02d  %6.2f-%6.2f  %s @%.2f" % (i + 1, tr["start"] / S, (tr["start"] + tr["duration"]) / S, os.path.basename(path or "?"), t))
        if path and os.path.exists(path):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", path, "-frames:v", "1",
                            "-vf", "scale=-2:300", os.path.join(outdir, "f%02d.jpg" % (i + 1))])
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i", os.path.join(outdir, "f*.jpg"),
                    "-vf", "tile=4x%d" % ((len(vt["segments"]) + 3) // 4), os.path.join(outdir, "grid.jpg")])
    print("grid:", os.path.join(outdir, "grid.jpg"), "(order: left->right, top->bottom = clip numbers)")


# ---------------------------------------------------------------- effects
def fx_path(eid):
    hits = glob.glob(os.path.join(CACHE_FX, eid, "*"))
    hits = [h for h in hits if os.path.isdir(h)]
    return hits[0] if hits else None


def cmd_effects():
    print("Confirmed FREE effects (is_vip=0) and whether downloaded in cache:")
    for n, i in FREE_EFFECTS.items():
        print(f"  {n:10s} {i}  cached={bool(fx_path(i))}")
    print("\nOther effects seen in project key_value.json files:")
    seen = {}
    for f in glob.glob(os.path.join(DRAFTS, "*/key_value.json")):
        try:
            kv = json.load(open(f))
        except Exception:
            continue
        for v in kv.values():
            if isinstance(v, dict) and v.get("materialCategory") not in (None, "", "media", "music", "sound"):
                seen[(v.get("materialName"), str(v.get("materialId")))] = v.get("is_vip")
    for (n, i), vip in sorted(seen.items(), key=lambda x: str(x)):
        print(f"  {n} {i} is_vip={vip} cached={bool(fx_path(i))}")
    print("\nSFX pack:", SFX_DIR)


# ---------------------------------------------------------------- apply
class Draft:
    def __init__(self, d):
        self.d, self.M = d, d["materials"]

    def find(self, i):
        for k, v in self.M.items():
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, dict) and x.get("id") == i:
                        return k, x
        return None, None

    def add_refs(self, refs, empty_anim=True):
        ids = []
        for k, x in refs:
            y = copy.deepcopy(x); y["id"] = nid()
            if k == "material_animations" and empty_anim:
                y["animations"] = []
            self.M.setdefault(k, []).append(y); ids.append(y["id"])
        return ids

    def new_track(self, tpl):
        t = copy.deepcopy(tpl); t["id"] = nid(); t["segments"] = []
        self.d["tracks"].append(t)
        return t


def hex2rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def kf(t_us, val):
    return {"id": nid(), "curveType": "Line", "time_offset": int(t_us), "left_control": {"x": 0.0, "y": 0.0},
            "right_control": {"x": 0.0, "y": 0.0}, "values": [val], "string_value": "", "graphID": ""}


def kfl(ptype, pts):
    return {"id": nid(), "material_id": "", "property_type": ptype, "keyframe_list": [kf(t, v) for t, v in pts]}


def text_content(text, hl, size, font, color, hl_color, stroke):
    def st(rng, c, sz):
        return {"fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": c}}},
                "font": {"id": "", "path": font},
                "strokes": [{"content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": [0.0, 0.0, 0.0]}}, "width": stroke}],
                "range": rng, "size": sz, "bold": True, "useLetterColor": True}
    styles = []
    hls = hl if isinstance(hl, list) else ([hl] if hl else [])
    marks = sorted((text.index(h), text.index(h) + len(h)) for h in hls if h and h in text)
    pos = 0
    for a, b in marks:
        if a > pos:
            styles.append(st([pos, a], color, size))
        styles.append(st([a, b], hl_color, size)); pos = b
    if pos < len(text):
        styles.append(st([pos, len(text)], color, size))
    return json.dumps({"styles": styles, "text": text}, ensure_ascii=False)


def sfx_duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


MAX_LINE_WIDTH = 150  # size * chars of longest line; ~21 chars at size 13 overflowed the frame


def apply_plan(d, plan, pdir):
    D = Draft(d)
    M = D.M
    style = {"font": "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf", "color": "#FFFFFF",
             "highlight": "#FFD400", "size": 12.0, "y": 0.55, "stroke": 0.08, "in": "pop", "in_dur": 0.3,
             "out": "Blur Fade", "out_dur": 0.25}
    style.update(plan.get("style", {}))
    report = []

    # ---- remove existing text if asked
    if plan.get("clear_existing_text"):
        d["tracks"] = [t for t in d["tracks"] if t["type"] != "text"]

    # ---- texts
    texts = list(plan.get("texts", []))
    if plan.get("thumbnail"):
        th = plan["thumbnail"]
        texts.insert(0, {"start": 0.0, "end": th.get("dur", 0.6), "text": th["text"], "hl": th.get("hl"),
                         "size": th.get("size", 17.0), "y": th.get("y", 0.1), "in": "none",
                         "out": "Blur Fade", "out_dur": 0.15})
    if texts:
        ttrack = D.new_track(TPL["text_track"])
        for tx in texts:
            st = dict(style); st.update({k: v for k, v in tx.items() if v is not None})
            # keep text inside the 9:16 frame: cap size by the longest line (size x chars <= MAX_LINE_WIDTH)
            longest = max(len(l) for l in tx["text"].split("\n"))
            if float(st["size"]) * longest > MAX_LINE_WIDTH:
                st["size"] = round(MAX_LINE_WIDTH / longest, 1)
                report.append(f"shrunk text to size {st['size']}: {tx['text']!r}")
            mat = copy.deepcopy(TPL["text_material"]); mat["id"] = nid()
            mat.update(content=text_content(tx["text"], tx.get("hl"), float(st["size"]), st["font"],
                                             hex2rgb(st["color"]), hex2rgb(st["highlight"]), st["stroke"]),
                       font_size=float(st["size"]), font_path=st["font"], border_color="#000000", border_width=st["stroke"])
            M["texts"].append(mat)
            seg = copy.deepcopy(TPL["text_segment"]); seg["id"] = nid(); seg["material_id"] = mat["id"]
            dur = int((tx["end"] - tx["start"]) * S)
            seg["target_timerange"] = {"start": int(tx["start"] * S), "duration": dur}
            seg["clip"]["scale"] = {"x": 1.0, "y": 1.0}
            seg["clip"]["transform"] = {"x": float(st.get("x", 0.0)), "y": float(st["y"])}
            seg["extra_material_refs"] = D.add_refs(TPL["text_refs"])
            am = next(x for r in seg["extra_material_refs"] for k, x in [D.find(r)] if k == "material_animations")
            anims = []
            if st["in"] == "Typewriter":
                a = copy.deepcopy(TPL["animations"]["Typewriter"]); a["duration"] = int(float(st["in_dur"]) * S); anims.append(a)
            elif st["in"] == "pop":
                x0 = seg["clip"]["transform"]["x"]
                seg["common_keyframes"] = [
                    kfl("KFTypeScaleX", [(0, 0.6), (0.12 * S, 1.08), (0.22 * S, 1.0)]),
                    kfl("KFTypeGlobalAlpha", [(0, 0.0), (0.08 * S, 1.0)]),
                    kfl("KFTypePositionX", [(0, x0 + 0.04), (0.05 * S, x0 - 0.03), (0.10 * S, x0 + 0.015), (0.15 * S, x0)]),
                ]
            elif st["in"] == "slide":
                y0 = seg["clip"]["transform"]["y"]
                seg["common_keyframes"] = [
                    kfl("KFTypePositionY", [(0, y0 - 0.08), (0.2 * S, y0)]),
                    kfl("KFTypeGlobalAlpha", [(0, 0.0), (0.15 * S, 1.0)]),
                ]
            if st.get("out") == "Blur Fade":
                o = copy.deepcopy(TPL["animations"]["Blur Fade"]); o["duration"] = int(float(st["out_dur"]) * S)
                o["start"] = dur - o["duration"]; anims.append(o)
            am["animations"] = anims
            ttrack["segments"].append(seg)
        report.append(f"texts: {len(texts)}")

    # ---- SFX (each "group" gets its own audio track; segments in one group must not overlap)
    groups = {}
    mcache = {}
    for sx in plan.get("sfx", []):
        path = sx["file"] if os.path.isabs(sx["file"]) else os.path.join(SFX_DIR, sx["file"])
        if not os.path.exists(path):
            report.append(f"SKIP sfx (missing): {path}"); continue
        if path not in mcache:
            full = sfx_duration(path)
            m = copy.deepcopy(TPL["audio_material"])
            m.update(id=nid(), name=os.path.basename(path), path=path, duration=int(full * S), unique_id=uuid.uuid4().hex,
                     music_id=str(uuid.uuid4()), local_material_id=str(uuid.uuid4()))
            M.setdefault("audios", []).append(m); mcache[path] = (m["id"], full)
        mid, full = mcache[path]
        off = float(sx.get("off", 0)); ln = min(float(sx.get("len", full)), full - off)
        g = sx.get("group", "sfx")
        if g not in groups:
            groups[g] = D.new_track(TPL["audio_track"])
        seg = copy.deepcopy(TPL["audio_segment"]); seg["id"] = nid(); seg["material_id"] = mid
        seg["source_timerange"] = {"start": int(off * S), "duration": int(ln * S)}
        seg["target_timerange"] = {"start": int(float(sx["start"]) * S), "duration": int(ln * S)}
        seg["volume"] = seg["last_nonzero_volume"] = float(sx.get("vol", 0.5))
        seg["extra_material_refs"] = D.add_refs(TPL["audio_refs"])
        groups[g]["segments"].append(seg)
    for g, t in groups.items():
        t["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        for a, b in zip(t["segments"], t["segments"][1:]):
            if a["target_timerange"]["start"] + a["target_timerange"]["duration"] > b["target_timerange"]["start"]:
                b["target_timerange"]["start"] = a["target_timerange"]["start"] + a["target_timerange"]["duration"]
    if plan.get("sfx"):
        report.append(f"sfx: {len(plan['sfx'])} on {len(groups)} tracks")

    # ---- zoom keyframes on the main video track
    vt = next(t for t in d["tracks"] if t["type"] == "video")
    z = plan.get("zoom")
    if z:
        z = {"entry": 1.15, "entry_dur": 0.25, "step": 1.6, "punch": 1.10, "push": 1.06, **(z if isinstance(z, dict) else {})}
        FR = 1 / 30
        for s in vt["segments"]:
            base = s["clip"]["scale"]["x"]
            src0 = (s.get("source_timerange") or {}).get("start", 0)
            sp = s.get("speed") or 1.0
            Dd = s["target_timerange"]["duration"] / S
            pts = [(0, base * z["entry"]), (z["entry_dur"], base)] if z["entry"] else [(0, base)]
            if Dd > 1.5 * z["step"]:
                t, hi = z["step"], False
                while t < Dd - 0.6:
                    a, b = (z["punch"], 1.0) if hi else (1.0, z["punch"])
                    pts += [(t - FR, base * a), (t, base * b)]
                    hi = not hi; t += z["step"]
                pts.append((Dd, base * (z["punch"] if hi else 1.0)))
            else:
                pts.append((Dd, base * z["push"]))
            # video keyframe time_offset is in SOURCE time (µs)
            s["common_keyframes"] = [kfl("KFTypeScaleX", [(src0 + t * sp * S, v) for t, v in pts])]
        report.append(f"zoom keyframes: {len(vt['segments'])} clips")

    # ---- transitions (only free + cached ones)
    for trn in plan.get("transitions", []):
        name = trn.get("effect", "Mix")
        eid = FREE_EFFECTS.get(name)
        p = eid and fx_path(eid)
        if not p:
            report.append(f"SKIP transition {name}: not free-confirmed or not downloaded"); continue
        cut = float(trn["cut"])
        prev = min(vt["segments"], key=lambda s: abs((s["target_timerange"]["start"] + s["target_timerange"]["duration"]) / S - cut))
        if any(D.find(r)[0] == "transitions" for r in prev["extra_material_refs"]):
            prev["extra_material_refs"] = [r for r in prev["extra_material_refs"] if D.find(r)[0] != "transitions"]
        tr = copy.deepcopy(TPL["transition"])
        tr.update(id=nid(), name=name, effect_id=eid, resource_id=eid, path=p, duration=int(float(trn.get("dur", 0.3)) * S))
        M.setdefault("transitions", []).append(tr)
        prev["extra_material_refs"].append(tr["id"])
    if plan.get("transitions"):
        report.append(f"transitions: {len(plan['transitions'])} requested")

    for i, t in enumerate(d["tracks"]):
        for s in t["segments"]:
            s["track_render_index"] = i
    return report


def cmd_apply(name, plan_path):
    plan = json.load(open(plan_path))
    pdir = project_dir(name)
    quit_capcut()
    paths = draft_paths(pdir)
    sums = {md5(p) for p in paths if p.endswith("draft_info.json")}
    if len(sums) > 1:
        sys.exit("Root draft_info.json and main timeline copy differ - open the project's main timeline in CapCut, save, close, retry.")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bdir = os.path.join(BACKUP_ROOT, f"{os.path.basename(pdir)}-{stamp}")
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    shutil.copytree(pdir, bdir)
    d = load(pdir)
    report = apply_plan(d, plan, pdir)
    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    for p in paths:
        open(p, "w").write(out)
    print("\n".join(report))
    print("wrote", len(paths), "files; backup:", bdir)
    subprocess.run(["open", "-a", "CapCut"])


def cmd_restore(name, bdir):
    pdir = project_dir(name)
    quit_capcut()
    for p in draft_paths(pdir):
        rel = os.path.relpath(p, pdir)
        src = os.path.join(bdir, rel)
        if os.path.exists(src):
            shutil.copy2(src, p)
    print("restored from", bdir)
    subprocess.run(["open", "-a", "CapCut"])


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c = a[0]
    if c == "list":
        for n, p in projects():
            print(f"{n}  ->  {p}")
    elif c == "inspect":
        cmd_inspect(a[1])
    elif c == "transcribe":
        cmd_transcribe(a[1], a[a.index("--model") + 1] if "--model" in a else None)
    elif c == "frames":
        cmd_frames(a[1], a[2])
    elif c == "effects":
        cmd_effects()
    elif c == "apply":
        cmd_apply(a[1], a[2])
    elif c == "restore":
        cmd_restore(a[1], a[2])
    else:
        sys.exit(__doc__)
