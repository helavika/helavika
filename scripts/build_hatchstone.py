"""Build the Hatchstone showcase card (assets/hatchstone-*.svg) in the same look as the header.

Three phone screenshots of the game fan out on the left; the title, a short pitch, a few
stats and a "play" plaque sit on the right. Screenshots live in scripts/hatchstone/.

Run: python3 scripts/build_hatchstone.py    # needs fonttools, like build_banner.py
"""
import base64
from xml.sax.saxutils import escape

from build_banner import FONTS, ROOT, THEMES, Face, patterns

W, H = 1200, 520
SHOTS = [("title.jpg", -7, -128), ("egg.jpg", 7, 128), ("hatch.jpg", 0, 0)]  # back to front: file, tilt, x offset
PHONE_W, PHONE_H = 176, 352
FAN_CX, FAN_CY = 322, 252
KICKER = "MY INDIE GAME"
TITLE = "Hatchstone"
SUBTITLE = "Geodes & Glowlings"
PITCH = ["Crack open real geodes, hatch glowlings", "and raise them in a cozy cave nest."]
STATS = ["24 LEVELS", "17 GEODES", "26 GLOWLINGS"]
PLAY = "PLAY IN YOUR BROWSER"
SPARKLES = [(118, 92, 1.0), (520, 70, .8), (548, 430, 1.1), (76, 448, .7), (640, 96, .6), (1120, 120, .8), (1100, 452, .7)]


def frame(c):
    in_w = W - 60 - ((W - 60) % 24)
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


def phones(c):
    out = []
    for i, (fname, tilt, dx) in enumerate(SHOTS):
        data = base64.b64encode((ROOT / "scripts" / "hatchstone" / fname).read_bytes()).decode()
        x, y = -PHONE_W / 2, -PHONE_H / 2
        corners = "".join(
            f'<rect x="{cx - 4}" y="{cy - 4}" width="8" height="8" transform="rotate(45 {cx} {cy})" fill="{c["frame"]}"/>'
            for cx, cy in ((x - 10, y - 10), (-x + 10, y - 10), (x - 10, -y + 10), (-x + 10, -y + 10)))
        out.append(
            f'<g transform="translate({FAN_CX + dx} {FAN_CY + abs(dx) * .12:.0f}) rotate({tilt})">'
            f'<g class="bob" style="animation-delay:-{i * 1.1:.1f}s">'
            f'<rect x="{x - 4}" y="{y + 10}" width="{PHONE_W + 28}" height="{PHONE_H + 10}" fill="{c["moss_dim"]}" opacity=".35"/>'
            f'<rect x="{x - 10}" y="{y - 10}" width="{PHONE_W + 20}" height="{PHONE_H + 20}" fill="{c["panel"]}" stroke="{c["frame"]}" stroke-width="1.5"/>'
            f'<rect x="{x - 5}" y="{y - 5}" width="{PHONE_W + 10}" height="{PHONE_H + 10}" fill="none" stroke="{c["frame"]}" stroke-width="1"/>'
            f'<image x="{x}" y="{y}" width="{PHONE_W}" height="{PHONE_H}" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data}"/>'
            f'{corners}</g></g>')
    return "\n  ".join(out)


def sparkle(x, y, s, c, n):
    d = f"M0 -{9 * s:.1f}L{2.2 * s:.1f} -{2.2 * s:.1f} {9 * s:.1f} 0 {2.2 * s:.1f} {2.2 * s:.1f} 0 {9 * s:.1f} -{2.2 * s:.1f} {2.2 * s:.1f} -{9 * s:.1f} 0 -{2.2 * s:.1f} -{2.2 * s:.1f}Z"
    return (f'<g transform="translate({x} {y})"><path class="tw" style="animation-delay:-{n * .7 % 2.6:.1f}s" '
            f'd="{d}" fill="{c["moss"]}"/></g>')


def build(theme, faces):
    c = THEMES[theme]
    gothic, serif, pixel = faces["gothic"], faces["serif"], faces["pixel"]
    left, right = 640, W - 70
    avail = right - left
    parts = []

    # kicker with a small diamond rule on each side
    ks = 24
    kw = pixel.width(KICKER, ks)
    parts.append(f'<path d="{pixel.path(KICKER, ks, left, 112)}" fill="{c["moss"]}"/>')
    parts.append(f'<path d="M{left + kw + 14:.1f} 104H{right}" stroke="{c["frame"]}" stroke-width="1.2"/>'
                 f'<rect x="{right - 4}" y="100" width="8" height="8" transform="rotate(45 {right} 104)" fill="{c["frame"]}"/>')

    tsize = min(118, 100 * avail / gothic.width(TITLE, 100))
    parts.append(f'<path d="{gothic.path(TITLE, tsize, left - 2, 212)}" fill="{c["ink"]}"/>')
    parts.append(f'<path d="{serif.path(SUBTITLE, 30, left, 256)}" fill="{c["moss"]}"/>')
    for i, line in enumerate(PITCH):
        parts.append(f'<path d="{serif.path(line, 23, left, 302 + i * 30)}" fill="{c["muted"]}"/>')

    # stat plaques
    ps, pad, gap, ph, py = 22, 12, 12, 36, 362
    x = left
    for t in STATS:
        w = pixel.width(t, ps) + 2 * pad
        parts.append(f'<g transform="translate({x:.1f} {py})"><rect width="{w:.1f}" height="{ph}" fill="none" stroke="{c["moss_dim"]}" stroke-width="1.5"/>'
                     f'<path d="{pixel.path(t, ps, pad, ph / 2 + ps * .32)}" fill="{c["muted"]}"/></g>')
        x += w + gap

    # play plaque: lit, with a pixel arrow that nudges forward
    pls, plh, ply = 28, 52, 420
    tw = pixel.width(PLAY, pls)
    plw = tw + 84
    parts.append(f'<g transform="translate({left} {ply})">'
                 f'<rect x="5" y="5" width="{plw:.1f}" height="{plh}" fill="{c["moss_dim"]}"/>'
                 f'<rect class="play" width="{plw:.1f}" height="{plh}" fill="{c["moss"]}"/>'
                 f'<g class="arrow"><path d="M24 {plh / 2 - 11}L40 {plh / 2}L24 {plh / 2 + 11}Z" fill="{c["bg"]}"/></g>'
                 f'<path d="{pixel.path(PLAY, pls, 58, plh / 2 + pls * .32)}" fill="{c["bg"]}"/></g>')

    sparkles = "".join(sparkle(x, y, s, c, n) for n, (x, y, s) in enumerate(SPARKLES))
    label = escape(f"{TITLE}: {SUBTITLE}. My indie game. {' '.join(PITCH)} {', '.join(STATS).lower()}. Play in your browser.")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <defs>
    {patterns(c)}
    <radialGradient id="halo" cx=".25" cy=".5" r=".55"><stop offset="0" stop-color="{c["glow"]}" stop-opacity=".12"/><stop offset="1" stop-color="{c["glow"]}" stop-opacity="0"/></radialGradient>
    <filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.4 -.45"/></filter>
    <style>
      .bob {{ animation: bob 4.4s ease-in-out infinite; }}
      @keyframes bob {{ 50% {{ transform: translateY(-6px); }} }}
      .tw {{ animation: tw 2.6s steps(4) infinite; }}
      @keyframes tw {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
      .play {{ animation: play 2.4s steps(1) infinite; }}
      @keyframes play {{ 0%, 70% {{ fill: {c["moss"]}; }} 80%, 90% {{ fill: {c["glow"]}; }} }}
      .arrow {{ animation: arrow 1.2s steps(2) infinite; }}
      @keyframes arrow {{ 50% {{ transform: translateX(4px); }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>

  <rect width="{W}" height="{H}" fill="{c["bg"]}"/>
  <rect width="{W}" height="{H}" fill="url(#halo)"/>
  {frame(c)}
  {phones(c)}
  {sparkles}
  {"".join(parts)}

  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="{c["grain"]}" style="mix-blend-mode:overlay" pointer-events="none"/>
</svg>
'''


if __name__ == "__main__":
    faces = {k: Face(k) for k in FONTS}
    for theme in THEMES:
        out = ROOT / "assets" / f"hatchstone-{theme}.svg"
        out.write_text(build(theme, faces))
        print(f"wrote assets/hatchstone-{theme}.svg ({out.stat().st_size // 1024} KB)")
