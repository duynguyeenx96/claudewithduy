#!/usr/bin/env python3
"""Build map data + assets for a re-map-video project.

Usage: python3 -I build_data.py <project_dir>
Reads  <project_dir>/project.json
Writes <project_dir>/assets/map/*.jpg, assets/photos/*, assets/data.js

Free data sources only:
  - ESRI World Imagery tiles (attribution: "Esri, Maxar, Earthstar Geographics")
  - OSRM public demo router (driving distance + route geometry)
  - Overpass API (Metro line geometry, optional)
"""
import json, math, os, sys, time, io, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

UA = {"User-Agent": "re-map-video/0.1 (local video tool)"}


def commons_thumb(url, w=1280):
    """upload.wikimedia.org/wikipedia/commons/a/ab/F.jpg -> thumb 1280px (friendlier to rate limits)."""
    pre = "https://upload.wikimedia.org/wikipedia/commons/"
    if url.startswith(pre) and "/thumb/" not in url:
        rest = url[len(pre):].split("?")[0]
        return f"{pre}thumb/{rest}/{w}px-{rest.split('/')[-1]}"
    return url
TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
REF_Z = 17


def get(url, timeout=40, data=None):
    req = urllib.request.Request(url, headers=UA, data=data)
    for i in range(4):
        try:
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:  # noqa
            if i == 3:
                raise
            time.sleep((8 if "429" in str(e) else 1.5) * (i + 1))


# ---------- web mercator ----------
def px(lat, lon, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


class Frame:
    """Local metric frame: X east (m), Z south (m), origin = project."""

    def __init__(self, lat, lon):
        self.cx, self.cy = px(lat, lon, REF_Z)
        self.mpp = 156543.03392 * math.cos(math.radians(lat)) / 2 ** REF_Z

    def m(self, lat, lon):
        x, y = px(lat, lon, REF_Z)
        return [round((x - self.cx) * self.mpp, 1), round((y - self.cy) * self.mpp, 1)]

    def px_to_m(self, x, y, z):
        f = 2 ** (REF_Z - z)
        return (x * f - self.cx) * self.mpp, (y * f - self.cy) * self.mpp


def mosaic(name, lat, lon, z, half_tiles_x, half_tiles_y, outdir, frame, cache):
    x0, y0 = px(lat, lon, z)
    tx0, ty0 = int(x0 // 256) - half_tiles_x, int(y0 // 256) - half_tiles_y
    nx, ny = half_tiles_x * 2, half_tiles_y * 2
    jobs = [(z, ty0 + j, tx0 + i, i, j) for j in range(ny) for i in range(nx)]

    def fetch(job):
        z_, y_, x_, i, j = job
        p = os.path.join(cache, f"{z_}_{y_}_{x_}.jpg")
        if not os.path.exists(p):
            open(p, "wb").write(get(TILE.format(z=z_, y=y_, x=x_)))
        return i, j, p

    img = Image.new("RGB", (nx * 256, ny * 256), (40, 52, 40))
    with ThreadPoolExecutor(8) as ex:
        for i, j, p in ex.map(fetch, jobs):
            try:
                img.paste(Image.open(p).convert("RGB"), (i * 256, j * 256))
            except Exception:
                pass
    fn = f"{name}.jpg"
    img.save(os.path.join(outdir, fn), quality=86)
    left, top = frame.px_to_m(tx0 * 256, ty0 * 256, z)
    right, bottom = frame.px_to_m((tx0 + nx) * 256, (ty0 + ny) * 256, z)
    print(f"  {name}: z{z} {nx}x{ny} tiles")
    return {"src": f"assets/map/{fn}", "x0": round(left), "z0": round(top), "x1": round(right), "z1": round(bottom), "level": z}


def osrm(a, b):
    u = f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
    r = json.loads(get(u))["routes"][0]
    return r["distance"] / 1000, r["duration"] / 60, r["geometry"]["coordinates"]


def simplify(pts, tol):
    """Douglas-Peucker on [x,z] metres."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz) or 1
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dz * pts[i][0] - dx * pts[i][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return simplify(pts[: idx + 1], tol)[:-1] + simplify(pts[idx:], tol)
    return [a, b]


def metro_line(bbox, frame, a_ll, b_ll):
    """Fetch subway ways, order points along A->B, bin-average into one polyline."""
    q = f'[out:json][timeout:50];way["railway"~"subway|light_rail"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});out geom;'
    for mirror in ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
                   "https://overpass.kumi.systems/api/interpreter"]:
        try:
            d = json.loads(get(mirror, timeout=70, data=urllib.parse.urlencode({"data": q}).encode()))
            break
        except Exception as e:
            print("  overpass fail", mirror, e)
    else:
        return None
    A, B = frame.m(*a_ll), frame.m(*b_ll)
    vx, vz = B[0] - A[0], B[1] - A[1]
    L2 = vx * vx + vz * vz
    pts = []
    for w in d["elements"]:
        for g in w.get("geometry", []):
            p = frame.m(g["lat"], g["lon"])
            t = ((p[0] - A[0]) * vx + (p[1] - A[1]) * vz) / L2
            if -0.02 <= t <= 1.02:
                pts.append((t, p))
    if not pts:
        return None
    pts.sort()
    bins = 400
    out = []
    for k in range(bins):
        sel = [p for t, p in pts if k / bins <= t < (k + 1) / bins]
        if sel:
            out.append([round(sum(p[0] for p in sel) / len(sel)), round(sum(p[1] for p in sel) / len(sel))])
    return out


def main():
    pdir = sys.argv[1]
    cfg = json.load(open(os.path.join(pdir, "project.json"), encoding="utf8"))
    lat0, lon0 = cfg["center"]
    frame = Frame(lat0, lon0)
    mapdir = os.path.join(pdir, "assets", "map")
    photodir = os.path.join(pdir, "assets", "photos")
    cache = os.path.join(pdir, ".tilecache")
    for d in (mapdir, photodir, cache):
        os.makedirs(d, exist_ok=True)

    speed = cfg.get("city_speed_kmh", 35)
    pois = []
    print("routes…")
    for p in cfg["pois"]:
        km, mins, coords = osrm((lat0, lon0), (p["lat"], p["lon"]))
        mins = max(mins, km / speed * 60)  # OSRM is free-flow; floor at city speed
        route = simplify([frame.m(c[1], c[0]) for c in coords], 6)
        q = dict(p)
        q.update(pos=frame.m(p["lat"], p["lon"]), km=round(km, 1), min=int(round(mins)), route=route,
                 dist=round(math.hypot(*frame.m(p["lat"], p["lon"])) ))
        if "km_override" in p:
            q["km"] = p["km_override"]
        if "min_override" in p:
            q["min"] = p["min_override"]
        pois.append(q)
        print(f"  {p['id']}: {q['km']} km ~{q['min']} min, {len(route)} pts")
        time.sleep(1)

    print("photos…")
    for q in pois:
        if q.get("photo"):
            ext = ".jpg"
            fn = f"{q['id']}{ext}"
            dst = os.path.join(photodir, fn)
            if not os.path.exists(dst):
                import subprocess
                raw = subprocess.run(["curl", "-sfL", "-m", "60", "-A", UA["User-Agent"], commons_thumb(q["photo"])],
                                     capture_output=True, check=True).stdout
                im = Image.open(io.BytesIO(raw)).convert("RGB")
                time.sleep(3)
                # center-crop to 16:10 card
                w, h = im.size
                tw, th = (w, int(w / 1.6)) if w / h < 1.6 else (int(h * 1.6), h)
                l, t = (w - tw) // 2, (h - th) // 2
                im.crop((l, t, l + tw, t + th)).resize((960, 600), Image.LANCZOS).save(dst, quality=88)
            q["photo_src"] = f"assets/photos/{fn}"

    print("tiles…")
    lats = [lat0] + [p["lat"] for p in cfg["pois"]]
    lons = [lon0] + [p["lon"] for p in cfg["pois"]]
    clat, clon = (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2
    span_km = max((max(lats) - min(lats)) * 111, (max(lons) - min(lons)) * 111 * math.cos(math.radians(lat0)))
    layers = []
    # backdrop + regional base, sized to the spread of POIs
    layers.append(mosaic("z11", clat, clon, 11, 3, 3, mapdir, frame, cache))
    zb = 13 if span_km < 30 else 12
    hb = 5 if span_km < 30 else 4
    layers.append(mosaic(f"z{zb}", clat, clon, zb, hb, hb, mapdir, frame, cache))
    layers.append(mosaic("z15_center", lat0, lon0, 15, 6, 6, mapdir, frame, cache))
    layers.append(mosaic("z17_center", lat0, lon0, 17, 4, 4, mapdir, frame, cache))
    for q in pois:
        if q["dist"] < 9000:
            layers.append(mosaic(f"z17_{q['id']}", q["lat"], q["lon"], 17, 4, 4, mapdir, frame, cache))
        else:
            layers.append(mosaic(f"z14_{q['id']}", q["lat"], q["lon"], 14, 3, 3, mapdir, frame, cache))
            layers.append(mosaic(f"z16_{q['id']}", q["lat"], q["lon"], 16, 4, 4, mapdir, frame, cache))
    layers.sort(key=lambda l: l["level"])

    metro = None
    if cfg.get("metro"):
        print("metro…")
        m = cfg["metro"]
        b = m["bbox"]
        metro = {"label": m.get("label", "METRO SỐ 1"), "pts": metro_line(b, frame, m["from"], m["to"])}
        print("  metro pts:", len(metro["pts"] or []))

    data = {k: cfg[k] for k in cfg if k not in ("pois", "metro")}
    data.update(pois=pois, layers=layers, metro=metro, mpp=frame.mpp)
    with open(os.path.join(pdir, "assets", "data.js"), "w", encoding="utf8") as f:
        f.write("window.RE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print("wrote assets/data.js")


if __name__ == "__main__":
    main()
