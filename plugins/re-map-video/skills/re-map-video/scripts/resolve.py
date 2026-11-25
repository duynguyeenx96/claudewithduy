#!/usr/bin/env python3
"""Resolve a project name or Google Maps link to {name, lat, lon}.

Usage:
  python3 -I resolve.py "https://maps.app.goo.gl/XXXX"
  python3 -I resolve.py "Tên dự án, Quận/Thành phố"
  python3 -I resolve.py --nearby <lat> <lon> "Vincom" "Bệnh viện" ...   # geocode candidate POIs near a point
"""
import json, math, re, subprocess, sys, time, urllib.parse, urllib.request

UA = "re-map-video/0.1 (local video tool)"


def from_link(url):
    final = url
    if "goo.gl" in url or "g.co" in url:
        out = subprocess.run(["curl", "-sIL", "-m", "30", url], capture_output=True, text=True).stdout
        locs = re.findall(r"(?im)^location:\s*(\S+)", out)
        if locs:
            final = locs[-1]
    final = urllib.parse.unquote(final)
    name = None
    m = re.search(r"/place/([^/@]+)", final)
    if m:
        name = m.group(1).replace("+", " ")
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final)  # exact place pin
    if not m:
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final)  # map viewport centre
    if not m:
        m = re.search(r"[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)", final)
    if not m:
        sys.exit(f"could not find coordinates in {final}")
    return {"name": name, "lat": float(m.group(1)), "lon": float(m.group(2)), "url": final}


def photon(q, near=None, limit=3):
    """Fallback geocoder (Komoot Photon, OSM data) for networks where Nominatim is blocked or down."""
    params = {"q": q, "limit": limit}
    if near:
        params["lat"], params["lon"] = near
    u = "https://photon.komoot.io/api/?" + urllib.parse.urlencode(params)
    feats = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30))["features"]
    out = []
    for f in feats:
        p = f["properties"]
        if p.get("countrycode", "VN") != "VN":
            continue
        lon, lat = f["geometry"]["coordinates"]
        parts = [p.get(k) for k in ("name", "housenumber", "street", "district", "city", "state")]
        out.append({"lat": lat, "lon": lon, "display_name": ", ".join(x for x in parts if x)})
    return out


def nominatim(q, near=None, limit=3):
    params = {"q": q, "format": "json", "limit": limit, "countrycodes": "vn"}
    if near:
        la, lo = near
        params["viewbox"] = f"{lo-0.35},{la+0.3},{lo+0.35},{la-0.3}"
    u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    try:
        res = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30))
    except OSError:  # DNS blocked by some ISPs, rate limit, outage
        return photon(q, near, limit)
    time.sleep(1.1)  # Nominatim policy: 1 req/s
    return res


def main():
    a = sys.argv[1:]
    if a and a[0] == "--nearby":
        la, lo = float(a[1]), float(a[2])
        for q in a[3:]:
            for r in nominatim(q, (la, lo)):
                y, x = float(r["lat"]), float(r["lon"])
                d = math.hypot((y - la) * 111, (x - lo) * 111 * math.cos(math.radians(la)))
                print(f"{q[:26]:26s} {d:5.1f}km {y:.5f},{x:.5f} {r['display_name'][:90]}")
        return
    s = " ".join(a)
    if s.startswith("http"):
        print(json.dumps(from_link(s), ensure_ascii=False))
    else:
        r = nominatim(s)
        if not r:
            sys.exit("not found — ask the user for a Google Maps link")
        print(json.dumps({"name": s, "lat": float(r[0]["lat"]), "lon": float(r[0]["lon"]), "display": r[0]["display_name"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
