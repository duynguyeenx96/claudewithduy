#!/usr/bin/env python3
"""fx2 build: A-roll + plan.json -> HyperFrames project with registry effects laid over it.

  python3 -I build.py <aroll.mp4> <plan.json> <project_dir> [--no-transcode]

plan.json:
  {"accent": "#ffd23f", "font": "Be Vietnam Pro",
   "effects": [{"fx": "dem-so", "start": 1.0, "end": 4.0, "end_value": 250, "suffix": "K"}, ...]}

Each `fx` name maps to a recipe in ../recipes.json. A recipe names a HyperFrames registry item
(Apache-2.0, installed on demand with `hyperframes add`), where it sits on the 1080x1920 frame,
and how plan fields become that item's variables, element text, JS constants or CSS.
Every effect gets its own patched copy of the item, so the same fx can run twice with different text.
"""
import html, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
HF = os.environ.get("FX2_HF", "hyperframes@0.9.69")
W, H = 1080, 1920


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe_duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def fill(tpl, fx):
    """'{text}' -> fx['text']; a value that is exactly '{key}' keeps the plan value's type."""
    if isinstance(tpl, str):
        m = re.fullmatch(r"\{(\w+)\}", tpl)
        if m:
            return fx.get(m.group(1), "")
        return re.sub(r"\{(\w+)\}", lambda m: str(fx.get(m.group(1), "")), tpl)
    if isinstance(tpl, list):
        return [fill(x, fx) for x in tpl]
    if isinstance(tpl, dict):
        return {k: fill(v, fx) for k, v in tpl.items()}
    return tpl


def replace_children(s, attr, new):
    """Replace the inner HTML of the first element carrying `attr` (e.g. 'data-slot="content"')."""
    m0 = re.search(r"<(\w+)\b[^<>]*%s[^<>]*>" % re.escape(attr), s)   # inside a real tag, not a comment
    if not m0:
        return s, 0
    open_end, tag = m0.end(), m0.group(1)
    depth, j = 1, open_end
    pat = re.compile(r"<(/?)%s\b[^>]*>" % tag)
    while depth:
        m = pat.search(s, j)
        if not m:
            return s, 0
        depth += -1 if m.group(1) else 1
        j = m.end()
    close_start = m.start()
    return s[:open_end] + new + s[close_start:], 1


def words_for(fx, plan, pdir):
    """Words inside the effect window, times relative to effect start. Source: fx.words or plan.transcript."""
    ws = fx.get("words")
    if ws is None and plan.get("transcript"):
        allw = json.load(open(os.path.join(pdir, plan["transcript"]) if not os.path.isabs(plan["transcript"])
                              else plan["transcript"], encoding="utf8"))
        t0, t1 = float(fx["start"]), float(fx["start"]) + fx["dur"]
        ws = [{"text": w["text"], "start": round(w["start"] - t0, 3), "end": round(w["end"] - t0, 3)}
              for w in allw if t0 <= w["start"] < t1]
    ws = ws or []
    groups, size = [], int(fx.get("group_size", 3))
    for k in range(0, len(ws), size):
        g = ws[k:k + size]
        nxt = ws[k + size]["start"] if k + size < len(ws) else fx["dur"]
        groups.append({"wordStart": k, "wordEnd": k + len(g) - 1, "start": g[0]["start"],
                       "end": round(max(g[-1]["end"] + 0.25, min(nxt, g[-1]["end"] + 0.6)), 3)})
    return ws, groups


def patch(src, recipe, fx, inst_id, base_id):
    s = src
    for attr, new in fill(recipe.get("children", {}), fx).items():
        s, n = replace_children(s, attr, new)
        if not n:
            print(f"  ! {recipe['item']}: no element [{attr}]")
    # unique composition id per instance
    s = s.replace(f'data-composition-id="{base_id}"', f'data-composition-id="{inst_id}"')
    # any quoted literal of the id (timeline keys, `var compositionId = "..."`)
    s = re.sub(r'(["\']){}\1'.format(re.escape(base_id)), lambda m: m.group(1) + inst_id + m.group(1), s)
    # element text by id
    for el_id, txt in fill(recipe.get("text", {}), fx).items():
        s, n = re.subn(r'(<(\w+)[^>]*\bid="%s"[^>]*>)(.*?)(</\2>)' % re.escape(el_id),
                       lambda m: m.group(1) + html.escape(str(txt)) + m.group(4), s, count=1, flags=re.S)
        if not n:
            print(f"  ! {recipe['item']}: no element #{el_id}")
    # top-level JS constants:  var NAME = <literal>;
    for name, val in fill(recipe.get("consts", {}), fx).items():
        lit = json.dumps(val, ensure_ascii=False)
        s, n = re.subn(r'((?:var|const|let)\s+%s\s*=\s*)(\[.*?\]|\{.*?\}|"[^"]*"|\'[^\']*\'|[^;\n]+)(;)' % name,
                       lambda m: m.group(1) + lit + m.group(3), s, count=1, flags=re.S)
        if not n:
            print(f"  ! {recipe['item']}: no constant {name}")
    # literal string swaps (last resort for hard-coded copy)
    for a, b in fill(recipe.get("replace", []), fx):
        s = s.replace(a, b)
    # canvas size for landscape blocks
    if recipe.get("canvas"):
        cw, ch = recipe["canvas"]
        s = s.replace('data-width="1920"', f'data-width="{cw}"').replace('data-height="1080"', f'data-height="{ch}"')
        s = s.replace("width: 1920px", f"width: {cw}px").replace("height: 1080px", f"height: {ch}px")
    css = fill(recipe.get("css", ""), fx)
    if css:
        tag = f"<style data-fx2>{css}</style>"
        if "</template>" in s:
            # template primitives: style must live inside the cloned root
            s = re.sub(r"(</div>\s*</template>)", tag + r"\n\1", s, count=1)
        elif "</head>" in s:
            s = s.replace("</head>", tag + "\n</head>", 1)
        else:
            s = tag + "\n" + s
    return s


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    aroll, plan_path, pdir = os.path.abspath(a[0]), os.path.abspath(a[1]), os.path.abspath(a[2])
    plan = json.load(open(plan_path, encoding="utf8"))
    recipes = json.load(open(os.path.join(SKILL, "recipes.json"), encoding="utf8"))["recipes"]
    os.makedirs(os.path.join(pdir, "assets"), exist_ok=True)
    os.makedirs(os.path.join(pdir, "compositions", "fx"), exist_ok=True)

    # project files
    for f in ("hyperframes.json", "package.json"):
        dst = os.path.join(pdir, f)
        if not os.path.exists(dst):
            shutil.copy(os.path.join(SKILL, "template", f), dst)

    shutil.copytree(os.path.join(SKILL, "template", "assets"), os.path.join(pdir, "assets"), dirs_exist_ok=True)

    # A-roll -> 1080x1920 30fps h264 + aac (one encode; the render is the only other one)
    clip = os.path.join(pdir, "assets", "aroll.mp4")
    if "--no-transcode" in a:
        shutil.copy(aroll, clip)
    elif not os.path.exists(clip) or os.path.getmtime(clip) < os.path.getmtime(aroll):
        sh(["ffmpeg", "-v", "error", "-y", "-i", aroll, "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30",
            "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", clip])
    dur = round(probe_duration(clip), 3)

    # install the registry items this plan needs
    effects = plan["effects"]
    for fx in effects:
        if fx["fx"] not in recipes:
            sys.exit(f"unknown fx '{fx['fx']}'. Known: {', '.join(sorted(recipes))}. "
                     "Gói con fx-pack-2-0N chỉ có một phần; đủ 13 hiệu ứng: /plugin install fx-pack-2@claudewithduy")
    items = sorted({recipes[fx["fx"]]["item"] for fx in effects})
    missing = [i for i in items if not os.path.exists(os.path.join(pdir, recipes_path(recipes, i)))]
    if missing:
        print("hyperframes add", " ".join(missing))
        sh(["npx", "--yes", HF, "add", *missing, "--no-clipboard", "--json"], cwd=pdir, stdout=subprocess.DEVNULL)

    accent = plan.get("accent", "#ffd23f")
    font = plan.get("font", "Be Vietnam Pro")
    hosts = []
    for n, fx in enumerate(effects):
        r = recipes[fx["fx"]]
        fx = {"accent": accent, "font": font, **r.get("defaults", {}), **fx}
        start = float(fx["start"])
        length = round(float(fx.get("end", start + r.get("dur", 3))) - start, 3)
        fx["dur"] = length
        if r.get("words"):
            fx["words"], fx["groups"] = words_for(fx, plan, pdir)
        for k, v in r.get("derive", {}).items():   # html snippets built from '|' lists
            fx[k] = "".join(v.replace("{item}", html.escape(x.strip())) for x in str(fx.get(k + "_list", "")).split("|") if x.strip())
        base_id = r.get("id", r["item"])
        inst_id = f"fx{n}-{r['item']}"
        src = open(os.path.join(pdir, recipes_path(recipes, r["item"])), encoding="utf8").read()
        out_rel = f"compositions/fx/{inst_id}.html"
        open(os.path.join(pdir, out_rel), "w", encoding="utf8").write(patch(src, r, fx, inst_id, base_id))

        x, y, bw, bh = fx.get("box") or fill(r.get("box", [0, 0, W, H]), fx)  # plan có thể đặt "box" riêng
        attrs = {
            "data-composition-id": inst_id, "data-composition-src": out_rel,
            "data-start": start, "data-duration": length, "data-track-index": n + 1,
            "data-width": bw, "data-height": bh,
        }
        vars_ = fill(r.get("vars", {}), fx)
        if vars_:
            attrs["data-variable-values"] = json.dumps(vars_, ensure_ascii=False)
        style = (f"position:absolute;left:{x}px;top:{y}px;width:{bw}px;height:{bh}px;z-index:{10 + n};"
                 f"--accent:{accent};--brand:{accent};--font-display:'{font}',sans-serif;--fg:#fff;"
                 + fill(r.get("host_css", ""), fx))
        a_txt = " ".join(f'{k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items())
        hosts.append(f'      <div id="{inst_id}" class="fx" {a_txt} style="{style}"></div>  <!-- {fx["fx"]} -->')
        print(f"  {start:5.2f}-{start + length:5.2f}  {fx['fx']:18s} <- {r['item']}")

    page = open(os.path.join(SKILL, "template", "index.html"), encoding="utf8").read()
    page = page.replace("__DUR__", str(dur)).replace("<!--FX-->", "\n".join(hosts))
    open(os.path.join(pdir, "index.html"), "w", encoding="utf8").write(page)
    print(f"index.html · {dur}s · {len(effects)} effects")


def recipes_path(recipes, item):
    kind = next((r.get("kind") for r in recipes.values() if r["item"] == item), "component")
    return f"compositions/{item}.html" if kind == "block" else f"compositions/components/{item}.html"


if __name__ == "__main__":
    main()
