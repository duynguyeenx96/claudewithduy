#!/usr/bin/env python3
"""Build data for a re-map-video *scale* project (quy mô dự án).

Usage: python3 -I build_scale.py <project_dir>
Reads  <project_dir>/project.json  ("mode": "scale")
Writes <project_dir>/assets/map/*.jpg, assets/data.js

Boundary / zones come from (in order):
  {"osm": "way/123"} | {"osm": "relation/456"}   OpenStreetMap polygon (main OSM API)
  {"coords": [[lat, lon], ...]}                   hand-traced (Google My Maps export, etc.)
  {"geojson": "assets/site.geojson"}              first Polygon / MultiPolygon outer ring

Everything shown as a measurement is computed here from the polygon
(area, length / width along the main axis, football-pitch count), so the
numbers on screen match the shape on screen. "area_ha" in project.json
overrides the headline area with the developer's official figure.
"""
import json, math, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_data import Frame, mosaic, get  # noqa: E402

PITCH = (105.0, 68.0)  # FIFA standard pitch, metres
def osm_ring(ref):
    """Polygon from the main OSM API (way/N or relation/N, outer ring)."""
    kind, oid = ref.split("/")
    d = json.loads(get(f"https://api.openstreetmap.org/api/0.6/{kind}/{oid}/full.json", timeout=60))["elements"]
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in d if e["type"] == "node"}
    ways = {e["id"]: e for e in d if e["type"] == "way"}
    if kind == "way":
        w = ways[int(oid)]
        return [nodes[n] for n in w["nodes"]], w.get("tags", {})
    rel = [e for e in d if e["type"] == "relation" and e["id"] == int(oid)][0]
    parts = [[nodes[n] for n in ways[m["ref"]]["nodes"]] for m in rel["members"] if m["type"] == "way" and m.get("role") == "outer"]
    ring = parts.pop(0)
    while parts:  # stitch outer ways end to end
        for i, w in enumerate(parts):
            if w[0] == ring[-1]:
                ring += w[1:]
            elif w[-1] == ring[-1]:
                ring += w[::-1][1:]
            else:
                continue
            parts.pop(i)
            break
        else:
            break
    return ring, rel.get("tags", {})


def load_ring(spec, pdir):
    if "osm" in spec:
        ring, tags = osm_ring(spec["osm"])
        time.sleep(1)
        return ring, tags.get("name")
    if "coords" in spec:
        return [tuple(c) for c in spec["coords"]], None
    if "geojson" in spec:
        g = json.load(open(os.path.join(pdir, spec["geojson"]), encoding="utf8"))
        feats = g.get("features", [g])
        for f in feats:
            geo = f.get("geometry", f)
            if geo["type"] == "Polygon":
                return [(c[1], c[0]) for c in geo["coordinates"][0]], f.get("properties", {}).get("name")
            if geo["type"] == "MultiPolygon":
                return [(c[1], c[0]) for c in geo["coordinates"][0][0]], f.get("properties", {}).get("name")
    sys.exit(f"bad polygon spec: {spec}")


def area(P):
    return abs(sum(P[i][0] * P[i - 1][1] - P[i - 1][0] * P[i][1] for i in range(len(P)))) / 2


def centroid(P):
    a = cx = cz = 0.0
    for i in range(len(P)):
        x0, z0 = P[i - 1]
        x1, z1 = P[i]
        c = x0 * z1 - x1 * z0
        a += c
        cx += (x0 + x1) * c
        cz += (z0 + z1) * c
    a *= 0.5
    return [round(cx / (6 * a), 1), round(cz / (6 * a), 1)] if a else P[0]


def inside(x, z, P):
    c = False
    for i in range(len(P)):
        x0, z0 = P[i - 1]
        x1, z1 = P[i]
        if (z0 > z) != (z1 > z) and x < (x1 - x0) * (z - z0) / (z1 - z0) + x0:
            c = not c
    return c


def main_axis(P):
    """Angle that minimises the bounding box (rotating calipers, brute force over edges)."""
    best = None
    for i in range(len(P)):
        dx, dz = P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]
        if dx == dz == 0:
            continue
        a = math.atan2(dz, dx)
        ca, sa = math.cos(a), math.sin(a)
        us = [x * ca + z * sa for x, z in P]
        vs = [-x * sa + z * ca for x, z in P]
        box = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or box < best[0]:
            best = (box, a, min(us), max(us), min(vs), max(vs))
    _, a, u0, u1, v0, v1 = best
    if (u1 - u0) < (v1 - v0):  # make u the long side
        a += math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        us = [x * ca + z * sa for x, z in P]
        vs = [-x * sa + z * ca for x, z in P]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    return a, u0, u1, v0, v1


def fmt_len(m):
    return f"~{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"~{int(round(m, -1))} m"


def main():
    pdir = sys.argv[1]
    cfg = json.load(open(os.path.join(pdir, "project.json"), encoding="utf8"))
    lat0, lon0 = cfg["center"]
    frame = Frame(lat0, lon0)
    mapdir, cache = os.path.join(pdir, "assets", "map"), os.path.join(pdir, ".tilecache")
    for d in (mapdir, cache):
        os.makedirs(d, exist_ok=True)

    print("boundary…")
    ring_ll, osm_name = load_ring(cfg["boundary"], pdir)
    if ring_ll[0] == ring_ll[-1]:
        ring_ll = ring_ll[:-1]
    B = [frame.m(la, lo) for la, lo in ring_ll]
    a_m2 = area(B)
    print(f"  {len(B)} pts · {a_m2 / 1e4:.1f} ha ({osm_name or 'no name'})")

    # main axis + dimension lines (drawn just outside the polygon)
    ang, u0, u1, v0, v1 = main_axis(B)
    ca, sa = math.cos(ang), math.sin(ang)
    W = lambda u, v: [round(u * ca - v * sa, 1), round(u * sa + v * ca, 1)]  # noqa: E731
    off = (v1 - v0) * 0.08
    dims = [
        {"a": W(u0, v1 + off), "b": W(u1, v1 + off), "m": round(u1 - u0), "label": fmt_len(u1 - u0)},
        {"a": W(u1 + off, v0), "b": W(u1 + off, v1), "m": round(v1 - v0), "label": fmt_len(v1 - v0)},
    ]
    print(f"  dims {dims[0]['label']} x {dims[1]['label']}")

    # football pitches on a grid aligned to the main axis, kept if the centre is inside
    pw, ph = PITCH
    cells = []
    u = u0 + pw / 2
    while u < u1:
        v = v0 + ph / 2
        while v < v1:
            c = W(u, v)
            if inside(c[0], c[1], B):
                cells.append(c)
            v += ph
        u += pw
    print(f"  {len(cells)} pitch cells drawn (area / pitch = {a_m2 / (pw * ph):.0f})")

    zones = []
    for z in cfg.get("zones", []):
        r, nm = load_ring(z, pdir)
        P = [frame.m(la, lo) for la, lo in r]
        zones.append({"label": z.get("label") or nm or "", "kind": z.get("kind", "zone"), "pts": P,
                      "c": centroid(P), "ha": round(area(P) / 1e4, 1)})
        print(f"  zone {zones[-1]['label']}: {zones[-1]['ha']} ha")

    print("tiles…")
    clat = sum(p[0] for p in ring_ll) / len(ring_ll)
    clon = sum(p[1] for p in ring_ll) / len(ring_ll)
    ext = max(u1 - u0, v1 - v0)  # metres
    mpp17 = frame.mpp
    def half(z, pad=1.6):
        tile_m = 256 * mpp17 * 2 ** (17 - z)
        return max(2, math.ceil(ext * pad / tile_m / 2))
    layers = [mosaic("z11", clat, clon, 11, 3, 3, mapdir, frame, cache),
              mosaic("z13", clat, clon, 13, 4, 4, mapdir, frame, cache)]
    for z in (15, 16, 17):
        h = half(z, 2.6 if z == 15 else 1.35)
        if h > 9:  # very large site: stop at the level that still fits a sane mosaic
            break
        layers.append(mosaic(f"z{z}", clat, clon, z, h, h, mapdir, frame, cache))
    layers.sort(key=lambda l: l["level"])

    shown_ha = cfg.get("area_ha") or round(a_m2 / 1e4, 1)
    data = {k: cfg[k] for k in cfg if k not in ("boundary", "zones")}
    data.update(boundary=B, centroid=centroid(B), area_ha_measured=round(a_m2 / 1e4, 1), area_ha=shown_ha,
                area_official=bool(cfg.get("area_ha")), pitches=round(shown_ha * 1e4 / (pw * ph)),
                axis=round(math.degrees(ang), 2), dims=dims, cells=cells, zones=zones, layers=layers,
                mpp=frame.mpp, pois=[])
    with open(os.path.join(pdir, "assets", "data.js"), "w", encoding="utf8") as f:
        f.write("window.RE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print("wrote assets/data.js")


if __name__ == "__main__":
    main()
