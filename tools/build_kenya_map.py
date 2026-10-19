"""Regenerate the locator panel of templates/core/_kenya_map.html.

    python tools/build_kenya_map.py path/to/geoBoundaries-KEN-ADM1.geojson

Shapes come from the geoBoundaries gbOpen KEN ADM1 set
(https://github.com/wmgeolab/geoBoundaries). Every county is drawn so the served
ones sit inside a country rather than floating as loose blobs; the served list
gets a thicker outline plus a clickable dot that drives the demo site feed in
_coverage.html. Run this whenever SERVED changes.
"""
import json
import math
import re
import sys

TPL = "templates/core/_kenya_map.html"
VIEW_W, VIEW_H = 168.0, 200.0
MARGIN = 6.0
TOL_PX = 0.75          # Douglas-Peucker tolerance, in SVG units
MIN_RING_AREA = 1.2    # drop rings smaller than this many px^2
LAT0 = 0.4             # cos() correction reference latitude for Kenya
ZOOMBOX = '<rect class="ken-map-zoombox" x="47.7" y="124.4" width="37.1" height="30.6" rx="2" />'

SERVED = [
    "Nairobi", "Kiambu", "Machakos", "Kajiado",
    "Garissa", "Lamu", "Mombasa", "Nyeri", "Murang'a", "Embu",
    "Taita Taveta", "Nakuru", "Uasin Gishu", "Kisumu", "Migori",
    "Turkana", "Marsabit", "Nandi", "Nyandarua",
]
# Counties the request named by town rather than county.
TOWN = {"Uasin Gishu": "Eldoret", "Marsabit": "Moyale"}

KX = math.cos(math.radians(LAT0))


def project(lon, lat):
    return (lon * KX, -lat)


def simplify(points, tol):
    """Iterative Douglas-Peucker."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        if last <= first + 1:
            continue
        x1, y1 = points[first]
        dx, dy = points[last][0] - x1, points[last][1] - y1
        norm = math.hypot(dx, dy)
        best, idx = -1.0, -1
        for i in range(first + 1, last):
            px, py = points[i]
            if norm == 0:
                dist = math.hypot(px - x1, py - y1)
            else:
                dist = abs((px - x1) * dy - (py - y1) * dx) / norm
            if dist > best:
                best, idx = dist, i
        if best > tol and idx > 0:
            keep[idx] = True
            stack.append((first, idx))
            stack.append((idx, last))
    return [p for p, k in zip(points, keep) if k]


def ring_area(poly):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:])) / 2.0


def centroid(poly):
    sxx = syy = sa = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        cross = x0 * y1 - x1 * y0
        sa += cross
        sxx += (x0 + x1) * cross
        syy += (y0 + y1) * cross
    if abs(sa) < 1e-9:
        return poly[0]
    return (sxx / (3 * sa), syy / (3 * sa))


def inside(poly, pt):
    x, y = pt
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if (y0 > y) != (y1 > y):
            hit ^= x < x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    return hit


def build(paths, dots):
    order = sorted(paths, key=lambda n: -len(paths[n]))
    lines = [
        '    <svg class="ken-map-svg ken-map-svg--locator" viewBox="0 0 168 200" role="group"',
        '         aria-label="Map of the %d Kenyan counties we work in. Each shaded county is a button '
        'that loads a simulated site feed."' % len(SERVED),
        "      <title>Kenya - the counties we work in</title>",
        '      <g class="ken-map-country">',
    ]
    for name in order:
        if name not in SERVED:
            lines.append('        <path d="%s" />' % paths[name])
    for name in order:
        if name in SERVED:
            lines.append('        <path class="ken-map-served" data-county="%s" d="%s" />' % (name, paths[name]))
    lines += ["      </g>", "      " + ZOOMBOX, '      <g class="ken-map-dots">']
    for name in order:
        if name not in SERVED:
            continue
        x, y = dots[name]
        label = "%s (%s)" % (name, TOWN[name]) if name in TOWN else name
        town = ' data-town="%s"' % TOWN[name] if name in TOWN else ""
        lines += [
            '        <g class="ken-map-dot" data-county="%s" data-label="%s"%s role="button" tabindex="0" '
            'aria-label="%s - show the simulated site feed">' % (name, label, town, label),
            "          <title>%s</title>" % label,
            '          <circle class="ken-map-dot-hit" cx="%s" cy="%s" r="5.4" />' % (x, y),
            '          <circle class="ken-map-dot-halo" cx="%s" cy="%s" r="5" />' % (x, y),
            '          <circle cx="%s" cy="%s" r="2.4" />' % (x, y),
            "        </g>",
        ]
    lines += ["      </g>", "    </svg>"]
    return "\n".join(lines)


def main(source):
    data = json.load(open(source, encoding="utf-8"))
    counties, all_pts = [], []
    for feat in data["features"]:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        proj = [[ [project(lon, lat) for lon, lat in ring] for ring in poly ] for poly in polys]
        for poly in proj:
            for ring in poly:
                all_pts.append(ring)
        counties.append((feat["properties"]["shapeName"], proj))

    flat = [p for ring in all_pts for p in ring]
    minx, maxx = min(p[0] for p in flat), max(p[0] for p in flat)
    miny, maxy = min(p[1] for p in flat), max(p[1] for p in flat)
    scale = min((VIEW_W - 2 * MARGIN) / (maxx - minx), (VIEW_H - 2 * MARGIN) / (maxy - miny))
    offx = (VIEW_W - (maxx - minx) * scale) / 2.0 - minx * scale
    offy = (VIEW_H - (maxy - miny) * scale) / 2.0 - miny * scale

    def to_svg(pt):
        return (round(pt[0] * scale + offx, 1), round(pt[1] * scale + offy, 1))

    paths, dots = {}, {}
    for name, polys in counties:
        rings, biggest = [], None
        for poly in polys:
            kept = []
            for ring in poly:
                svg = [to_svg(p) for p in simplify(ring, TOL_PX / scale)]
                if abs(ring_area(svg)) >= MIN_RING_AREA:
                    kept.append(svg)
            if kept:
                rings.extend(kept)
                area = abs(ring_area(kept[0]))
                if biggest is None or area > biggest[0]:
                    biggest = (area, kept[0])
        paths[name] = "".join("M" + "L".join("%s,%s" % p for p in ring) + "Z" for ring in rings)
        if name in SERVED:
            outer = biggest[1]
            dot = centroid(outer)
            if not inside(outer, dot):
                dot = outer[0]
            dots[name] = (round(dot[0], 1), round(dot[1], 1))

    missing = [n for n in SERVED if n not in paths]
    if missing:
        raise SystemExit("not in this shapefile: %s" % ", ".join(missing))

    raw = open(TPL, "rb").read().decode("utf-8").replace("\r\n", "\n")
    start = raw.index('<svg class="ken-map-svg ken-map-svg--locator"')
    end = raw.index("</svg>", start) + len("</svg>")
    out = raw[: raw[:start].rindex("\n")] + "\n" + build(paths, dots) + raw[end:]
    open(TPL, "wb").write(out.replace("\n", "\r\n").encode("utf-8"))
    print("wrote %d counties (%d served) to %s" % (len(paths), len(SERVED), TPL))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
