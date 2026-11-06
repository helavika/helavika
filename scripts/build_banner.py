"""Build the header (assets/banner-*.svg) and the numbers row (assets/impact-*.svg).

Look: illuminated manuscript meets retro game. A Celtic-braid frame, the name in a
gothic face, the four focus areas as pixel-font plaques that light up in turn, and a
dithered pixel-art castle (the same scene as the portfolio site) with flickering torches.

GitHub shows the SVG as an <img>, so no web fonts can load: every letter is converted
to a vector path with fontTools, and the castle is an embedded PNG.

Run:
  node scripts/render_castle.mjs     # only when the castle scene changes
  python3 scripts/build_banner.py    # needs fonttools (pip install fonttools)
"""
import base64
import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path.home() / ".cache" / "helavika-fonts"
FONTS = {  # Google Fonts (OFL), downloaded once into FONT_DIR
    "gothic": ("grenze.ttf", "ofl/grenzegotisch/GrenzeGotisch%5Bwght%5D.ttf", 700),
    "serif": ("garamond.ttf", "ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf", 600),
    "pixel": ("vt323.ttf", "ofl/vt323/VT323-Regular.ttf", None),
}

W, H = 1200, 400
NAME_FIRST, NAME_LAST = "Viktoria", "Shchypalkina"
ROLE = "Front-End & Marketing Technology Engineer"
FOCUS = ["Referral programs", "A/B testing", "Apple & Google Wallet", "AI agents"]

THEMES = {
    "dark": dict(bg="#0b0c08", panel="#12140d", ink="#e9dcbc", muted="#b3a684", moss="#a8d43a",
                 moss_dim="#5d7a1e", frame="#8fb52f", glow="#a8d43a", grain=".10",
                 fire="#ffb04a", fire_hot="#ffe9a0", fire_glow="#e0661c"),
    "light": dict(bg="#e8dcc0", panel="#f1e7cf", ink="#2a2116", muted="#6b5a42", moss="#4f6b12",
                  moss_dim="#8a9a5a", frame="#5a4a2c", glow="#c9a24a", grain=".14",
                  fire="#f3dca0", fire_hot="#fff6dc", fire_glow="#c08a3c"),
}

# castle plate: the 150x200 scene shown at 1.5x
PLATE_X, PLATE_Y, PLATE_S = 922, 50, 1.5
TORCHES = [(24, 178), (40, 186), (122, 188), (140, 182), (62, 192)]  # same as the portfolio scene
WINDOWS = [(101, 92), (107, 92), (104, 112), (74, 126), (126, 112), (103, 136), (86, 146), (117, 146)]


def font(key):
    fname, url, wght = FONTS[key]
    path = FONT_DIR / fname
    if not path.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/" + url, path)
    f = TTFont(path)
    if wght and "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": wght})
    return f


def kerning(f):
    """Pair kerning from the GPOS 'kern' feature (format 1 pairs and format 2 classes)."""
    pairs, classes = {}, []
    if "GPOS" not in f:
        return lambda a, b: 0
    table = f["GPOS"].table
    for lookup in table.LookupList.Lookup:
        subs = lookup.SubTable
        for st in subs:
            if lookup.LookupType == 9:
                st = st.ExtSubTable
            if getattr(st, "LookupType", 2) != 2 or not hasattr(st, "Format"):
                continue
            if st.Format == 1:
                for first, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for pv in ps.PairValueRecord:
                        v = getattr(pv.Value1, "XAdvance", 0) or 0
                        pairs.setdefault((first, pv.SecondGlyph), v)
            elif st.Format == 2:
                classes.append(st)

    def kern(a, b):
        if (a, b) in pairs:
            return pairs[(a, b)]
        for st in classes:
            if a not in st.Coverage.glyphs:
                continue
            c1 = st.ClassDef1.classDefs.get(a, 0)
            c2 = st.ClassDef2.classDefs.get(b, 0)
            v = getattr(st.Class1Record[c1].Class2Record[c2].Value1, "XAdvance", 0) or 0
            if v:
                return v
        return 0

    return kern


class Face:
    def __init__(self, key):
        self.f = font(key)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.kern = kerning(self.f)

    def glyphs(self, text):
        return [self.cmap.get(ord(ch), ".notdef") for ch in text]

    def advances(self, text, size):
        """x offset of every character boundary, so we can animate a reveal per letter."""
        s = size / self.upm
        names = self.glyphs(text)
        xs, x = [0.0], 0.0
        for i, g in enumerate(names):
            x += self.f["hmtx"][g][0] * s
            if i + 1 < len(names):
                x += self.kern(g, names[i + 1]) * s
            xs.append(x)
        return xs

    def width(self, text, size):
        return self.advances(text, size)[-1]

    def path(self, text, size, x, y):
        s = size / self.upm
        pen = SVGPathPen(self.gs)
        names = self.glyphs(text)
        for g, off in zip(names, self.advances(text, size)):
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + off, y)))
        return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.1f}".rstrip("0").rstrip("."), pen.getCommands())


def frame(c):
    in_w = W - 60 - ((W - 60) % 24)  # whole braid tiles between the corner rosettes
    in_h = H - 60 - ((H - 60) % 24)
    x0, y0 = (W - in_w) / 2, (H - in_h) / 2
    parts = []
    for y in (12, H - 24):
        parts.append(f'<g transform="translate({x0} {y})"><rect width="{in_w}" height="12" fill="url(#bh)"/></g>')
    for x in (12, W - 24):
        parts.append(f'<g transform="translate({x} {y0})"><rect width="12" height="{in_h}" fill="url(#bv)"/></g>')
    for cx, cy in ((18, 18), (W - 18, 18), (18, H - 18), (W - 18, H - 18)):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{c["frame"]}"/>'
                     f'<circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{c["frame"]}" stroke-width="1.5"/>')
    return "\n  ".join(parts)


def patterns(c):
    # patterns in userSpaceOnUse of the translated <g>, so tiles start exactly at each strip's corner
    return (f'<pattern id="bh" width="24" height="12" patternUnits="userSpaceOnUse">'
            f'<path d="M0 3.5C6 3.5 6 8.5 12 8.5S18 3.5 24 3.5M0 8.5C6 8.5 6 3.5 12 3.5S18 8.5 24 8.5M0 .75H24M0 11.25H24" '
            f'fill="none" stroke="{c["frame"]}" stroke-width="1.5"/></pattern>'
            f'<pattern id="bv" width="12" height="24" patternUnits="userSpaceOnUse">'
            f'<path d="M3.5 0C3.5 6 8.5 6 8.5 12S3.5 18 3.5 24M8.5 0C8.5 6 3.5 6 3.5 12S8.5 18 8.5 24M.75 0V24M11.25 0V24" '
            f'fill="none" stroke="{c["frame"]}" stroke-width="1.5"/></pattern>')


def castle(theme, c):
    png = (ROOT / "scripts" / f"castle-{theme}.png").read_bytes()
    w, h = 150 * PLATE_S, 200 * PLATE_S
    x, y = PLATE_X, PLATE_Y
    s = PLATE_S
    out = [
        f'<rect x="{x - 10}" y="{y - 10}" width="{w + 20}" height="{h + 20}" fill="{c["panel"]}" stroke="{c["frame"]}" stroke-width="1.5"/>',
        f'<rect x="{x - 5}" y="{y - 5}" width="{w + 10}" height="{h + 10}" fill="none" stroke="{c["frame"]}" stroke-width="1"/>',
        f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" style="image-rendering:pixelated" '
        f'href="data:image/png;base64,{base64.b64encode(png).decode()}"/>',
    ]
    for cx, cy in ((x - 10, y - 10), (x + w + 10, y - 10), (x - 10, y + h + 10), (x + w + 10, y + h + 10)):
        out.append(f'<rect x="{cx - 4}" y="{cy - 4}" width="8" height="8" transform="rotate(45 {cx} {cy})" fill="{c["frame"]}"/>')
    # torches: a warm glow and a flame that flicker over the still image
    for n, (tx, ty) in enumerate(TORCHES):
        gx, gy = x + (tx + .5) * s, y + (ty - 3) * s
        d = f"animation-delay:-{(n * .37) % 1.3:.2f}s"
        out.append(f'<circle class="glow" style="{d}" cx="{gx:.1f}" cy="{gy:.1f}" r="{9 * s:.1f}" fill="url(#torch)"/>')
        out.append(f'<g class="flame" style="{d}">'
                   f'<rect x="{x + (tx - 1) * s:.1f}" y="{y + (ty - 4) * s:.1f}" width="{3 * s:.1f}" height="{3 * s:.1f}" fill="{c["fire"]}"/>'
                   f'<rect x="{x + tx * s:.1f}" y="{y + (ty - 6) * s:.1f}" width="{s:.1f}" height="{3 * s:.1f}" fill="{c["fire_hot"]}"/></g>')
    for n, (wx, wy) in enumerate(WINDOWS):
        d = f"animation-delay:-{(n * .9) % 4:.2f}s"
        out.append(f'<rect class="win" style="{d}" x="{x + wx * s:.1f}" y="{y + wy * s:.1f}" width="{2 * s:.1f}" height="{3 * s:.1f}" fill="{c["fire_hot"]}"/>')
    return "\n  ".join(out)


def flourish(x, y, c):
    col = c["frame"]
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{col}" stroke-width="1.4" stroke-linecap="round">'
            f'<circle cx="2" cy="0" r="2" fill="{col}" stroke="none"/>'
            f'<path d="M6 0H96M96 0c6-8 14-8 16 0-2 6-8 5-8 1M96 0c6 8 14 8 16 0"/>'
            f'<path d="M120 -8l7 8-7 8-7-8z" fill="{col}" stroke="none"/>'
            f'<path d="M144 0c-6-8-14-8-16 0 2 6 8 5 8 1M144 0c-6 8-14 8-16 0M144 0H234"/>'
            f'<circle cx="238" cy="0" r="2" fill="{col}" stroke="none"/></g>')


def build(theme, faces):
    c = THEMES[theme]
    gothic, serif, pixel = faces["gothic"], faces["serif"], faces["pixel"]
    left, right = 74, PLATE_X - 48
    avail = right - left

    # name: as large as fits on one line
    full = f"{NAME_FIRST} {NAME_LAST}"
    size = min(96, 100 * avail / (gothic.width(full, 100) + 42))  # leave room for the caret
    name_y = 168
    first_w = gothic.width(NAME_FIRST + " ", size)
    name = (f'<path d="{gothic.path(NAME_FIRST, size, left, name_y)}" fill="{c["ink"]}"/>'
            f'<path d="{gothic.path(NAME_LAST, size, left + first_w, name_y)}" fill="{c["moss"]}"/>')
    stops = gothic.advances(full, size)
    reveal = ";".join(f"{v + 4:.1f}" for v in stops)
    caret_x = ";".join(f"{left + v + 8:.1f}" for v in stops)
    name_w = stops[-1]

    role_size = 31
    role = f'<path d="{serif.path(ROLE, role_size, left + 2, name_y + 52)}" fill="{c["ink"]}"/>'

    # focus plaques
    psize, pad, gap, ph = 25, 15, 14, 44
    widths = [pixel.width(t, psize) + 2 * pad for t in FOCUS]
    total = sum(widths) + gap * (len(FOCUS) - 1)
    if total > avail:
        k = (avail - gap * (len(FOCUS) - 1)) / (total - gap * (len(FOCUS) - 1))
        psize *= k
        widths = [pixel.width(t, psize) + 2 * pad * k for t in FOCUS]
    py = name_y + 116
    plaques, x = [], left
    for n, (t, w) in enumerate(zip(FOCUS, widths)):
        d = f"animation-delay:{n * .9:.1f}s"
        tw = pixel.width(t, psize)
        plaques.append(
            f'<g transform="translate({x:.1f} {py})">'
            f'<rect x="4" y="4" width="{w:.1f}" height="{ph}" fill="{c["moss_dim"]}"/>'
            f'<rect class="plq" style="{d}" width="{w:.1f}" height="{ph}" fill="{c["panel"]}" stroke="{c["moss"]}" stroke-width="2"/>'
            f'<path class="plt" style="{d}" d="{pixel.path(t, psize, (w - tw) / 2, ph / 2 + psize * .32)}" fill="{c["moss"]}"/>'
            f'</g>')
        x += w + gap

    label = escape(f"{full} — {ROLE}. " + " · ".join(FOCUS))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <defs>
    {patterns(c)}
    <radialGradient id="torch"><stop offset="0" stop-color="{c["fire_glow"]}" stop-opacity=".55"/><stop offset="1" stop-color="{c["fire_glow"]}" stop-opacity="0"/></radialGradient>
    <radialGradient id="halo" cx=".3" cy=".45" r=".6"><stop offset="0" stop-color="{c["glow"]}" stop-opacity=".07"/><stop offset="1" stop-color="{c["glow"]}" stop-opacity="0"/></radialGradient>
    <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.4 -.45"/></filter>
    <clipPath id="type"><rect x="{left - 6}" y="40" width="0" height="160">
      <animate attributeName="width" values="{reveal}" dur="1.9s" begin=".3s" calcMode="discrete" fill="freeze"/>
    </rect></clipPath>
    <style>
      .caret {{ animation: blink 1s steps(1) infinite; }}
      @keyframes blink {{ 50% {{ opacity: 0; }} }}
      .plq {{ animation: plq 3.6s ease-out infinite; }}
      .plt {{ animation: plt 3.6s ease-out infinite; }}
      @keyframes plq {{ 0%, 18% {{ fill: {c["moss"]}; }} 26%, 100% {{ fill: {c["panel"]}; }} }}
      @keyframes plt {{ 0%, 18% {{ fill: {c["bg"]}; }} 26%, 100% {{ fill: {c["moss"]}; }} }}
      .flame {{ animation: flame 1.3s steps(1) infinite; }}
      @keyframes flame {{ 0% {{ opacity: 1; }} 22% {{ opacity: .55; }} 41% {{ opacity: .95; }} 63% {{ opacity: .4; }} 80% {{ opacity: .85; }} }}
      .glow {{ animation: glow 1.3s ease-in-out infinite alternate; }}
      @keyframes glow {{ 0% {{ opacity: .6; }} 100% {{ opacity: 1; }} }}
      .win {{ opacity: 0; animation: win 4s steps(1) infinite; }}
      @keyframes win {{ 0%, 60% {{ opacity: 0; }} 70% {{ opacity: .7; }} 85% {{ opacity: .35; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>

  <rect width="{W}" height="{H}" fill="{c["bg"]}"/>
  <rect width="{W}" height="{H}" fill="url(#halo)"/>
  {frame(c)}

  <g clip-path="url(#type)">{name}</g>
  <rect class="caret" x="{left + name_w + 8:.1f}" y="{name_y - size * .62:.1f}" width="{size * .3:.1f}" height="{size * .62:.1f}" fill="{c["moss"]}">
    <animate attributeName="x" values="{caret_x}" dur="1.9s" begin=".3s" calcMode="discrete" fill="freeze"/>
  </rect>
  {role}
  {flourish(left + 2, name_y + 82, c)}
  {"".join(plaques)}

  {castle(theme, c)}

  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="{c["grain"]}" style="mix-blend-mode:overlay" pointer-events="none"/>
</svg>
'''


# numbers row (assets/impact-*.svg): a character-sheet strip under the header
STATS = [("7+", "years building", "referral programs"),
         ("4,000+", "projects delivered", "since 2019"),
         ("1,270", "A/B tests", "built and launched"),
         ("300+", "brands, from DTC", "to global retail"),
         ("4x", "monthly delivery", "with AI workflows")]
IH = 190


def build_impact(theme, faces):
    c = THEMES[theme]
    pixel, serif = faces["pixel"], faces["serif"]
    x0, x1, y0, y1 = 10, W - 10, 10, IH - 10
    cell = (x1 - x0) / len(STATS)
    out = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{c["panel"]}" stroke="{c["frame"]}" stroke-width="1.5"/>',
           f'<rect x="{x0 + 6}" y="{y0 + 6}" width="{x1 - x0 - 12}" height="{y1 - y0 - 12}" fill="none" stroke="{c["frame"]}" stroke-width="1"/>']
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        out.append(f'<rect x="{cx - 5}" y="{cy - 5}" width="10" height="10" transform="rotate(45 {cx} {cy})" fill="{c["frame"]}"/>')
    for i, (num, l1, l2) in enumerate(STATS):
        mid = x0 + cell * (i + .5)
        if i:
            out.append(f'<path d="M{x0 + cell * i:.1f} {y0 + 30}V{y1 - 30}" stroke="{c["frame"]}" stroke-width="1" stroke-dasharray="2 4"/>')
            out.append(f'<rect x="{x0 + cell * i - 3:.1f}" y="{IH / 2 - 3}" width="6" height="6" transform="rotate(45 {x0 + cell * i:.1f} {IH / 2})" fill="{c["frame"]}"/>')
        nw = pixel.width(num, 64)
        out.append(f'<path d="{pixel.path(num, 64, mid - nw / 2, 92)}" fill="{c["moss"]}"/>')
        for j, line in enumerate((l1, l2)):
            lw = serif.width(line, 19)
            out.append(f'<path d="{serif.path(line, 19, mid - lw / 2, 126 + j * 24)}" fill="{c["muted"]}"/>')
    label = escape(", ".join(f"{n} {a} {b}" for n, a, b in STATS))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{IH}" viewBox="0 0 {W} {IH}" role="img" aria-label="{label}">\n  '
            + "\n  ".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    faces = {k: Face(k) for k in FONTS}
    for theme in THEMES:
        out = ROOT / "assets" / f"banner-{theme}.svg"
        out.write_text(build(theme, faces))
        print(f"wrote assets/banner-{theme}.svg ({out.stat().st_size // 1024} KB)")
        out = ROOT / "assets" / f"impact-{theme}.svg"
        out.write_text(build_impact(theme, faces))
        print(f"wrote assets/impact-{theme}.svg ({out.stat().st_size // 1024} KB)")
