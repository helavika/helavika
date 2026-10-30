"""Build assets/banner-light.svg and assets/banner-dark.svg (keyboard ASMR: pastel keycaps pressing in turn).

Run: python3 scripts/build_banner.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 1200, 400
FONT = 'ui-rounded, "SF Pro Rounded", "Nunito", "Segoe UI", system-ui, sans-serif'

THEMES = {
    "light": dict(bg1="#FFF6FA", bg2="#F1ECFF", border="#EDE3F7", name="#2A1D45", role="#6E5D8A",
                  caret="#F472B6", plate="#EDE5FA", plate_edge="#E2D7F3", shadow=".14"),
    "dark": dict(bg1="#1E1733", bg2="#2A1E40", border="#3A2E52", name="#FFF1F8", role="#CDBDEB",
                 caret="#FFB3D4", plate="#161026", plate_edge="#3A2E52", shadow=".6"),
}

# (label, keycap top, keycap side, width); label None = blank filler key
KEYS = [
    ("✦", "#FBF7FF", "#D9CFEA", 84),
    ("Referral programs", "#FFC2DC", "#E58AB0", 250),
    ("A/B testing", "#D6C9FF", "#A08DE6", 170),
    ("Apple & Google Wallet", "#A6DCFF", "#62AEE0", 280),
    ("AI agents", "#FFE6B0", "#E2BC6E", 160),
    ("♡", "#FBF7FF", "#D9CFEA", 84),
]
KEY_H, KEY_DEPTH, GAP = 96, 12, 14
KEY_Y = 222
NAME = "Viktoria Shchypalkina"
NAME_X, NAME_Y, NAME_W = 80, 122, 700
CYCLE = 3.6  # seconds for one pass over the four labelled keys
STEP = 0.45  # delay between key presses


def keys_svg(c):
    total = sum(k[3] for k in KEYS) + GAP * (len(KEYS) - 1)
    x0 = (W - total) / 2
    pad = 16
    out = [f'<rect x="{x0 - pad:.0f}" y="{KEY_Y - pad}" width="{total + 2 * pad:.0f}" height="{KEY_H + KEY_DEPTH + 2 * pad}" '
           f'rx="30" fill="{c["plate"]}" stroke="{c["plate_edge"]}" stroke-width="2"/>']
    x = x0
    n = 0
    for label, top, side, w in KEYS:
        cx = w / 2
        filler = len(label) == 1
        delay = "" if filler else f' style="animation-delay:{n * STEP:.2f}s"'
        anim = "" if filler else " cap"
        burst = "" if filler else '<g class="burst"' + delay + '>' + "".join(
            f'<path d="M{cx + dx} {-pad - 4 - abs(dx) // 6} l{dx // 5} -12" stroke="{side}" stroke-width="4" stroke-linecap="round"/>'
            for dx in (-30, 0, 30)) + '</g>'
        text = (f'<text x="{cx}" y="{KEY_H / 2 + 2}" text-anchor="middle" class="{"glyph" if filler else "label"}" '
                f'fill="{side if filler else "#2A1D45"}">{escape(label)}</text>')
        out.append(f'''<g transform="translate({x:.0f} {KEY_Y})">
      <rect x="4" y="{KEY_DEPTH + 4}" width="{w - 8}" height="{KEY_H - 4}" rx="18" fill="#1A0F2E" opacity="{c["shadow"]}"/>
      {burst}
      <g class="k{anim}"{delay}>
        <rect width="{w}" height="{KEY_H}" rx="20" fill="{side}"/>
        <rect x="9" y="4" width="{w - 18}" height="{KEY_H - 20}" rx="15" fill="{top}"/>
        <rect x="16" y="8" width="{w - 32}" height="{(KEY_H - 20) / 2}" rx="11" fill="url(#shine)"/>
        {text}
      </g>
    </g>''')
        x += w + GAP
        n += 0 if filler else 1
    return "\n    ".join(out)


def build(theme):
    c = THEMES[theme]
    step = NAME_W / len(NAME)
    reveal = ";".join(f"{step * i:.1f}" for i in range(len(NAME) + 1))
    caret_x = ";".join(f"{NAME_X + step * i + 6:.1f}" for i in range(len(NAME) + 1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Viktoria Shchypalkina — Front-End &amp; Marketing Technology Engineer. Referral programs · A/B testing · Apple &amp; Google Wallet · AI agents">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="type"><rect x="{NAME_X - 4}" y="40" width="0" height="110">
      <animate attributeName="width" values="{reveal}" dur="1.9s" begin=".3s" calcMode="discrete" fill="freeze"/>
    </rect></clipPath>
    <style>
      text {{ font-family: {FONT}; }}
      .name {{ font-size: 62px; font-weight: 800; fill: {c["name"]}; letter-spacing: -1px; }}
      .role {{ font-size: 26px; font-weight: 600; fill: {c["role"]}; }}
      .label {{ font-size: 21px; font-weight: 800; }}
      .glyph {{ font-size: 28px; font-weight: 700; }}
      .cap {{ animation: press {CYCLE}s ease-out infinite; }}
      @keyframes press {{ 0%, 14%, 100% {{ transform: translateY(0); }} 4%, 7% {{ transform: translateY({KEY_DEPTH}px); }} }}
      .burst {{ opacity: 0; animation: burst {CYCLE}s ease-out infinite; }}
      @keyframes burst {{ 0%, 3% {{ opacity: 0; transform: translateY(6px); }} 6% {{ opacity: 1; transform: translateY(0); }} 16%, 100% {{ opacity: 0; transform: translateY(-8px); }} }}
      .caret {{ animation: blink 1s steps(1) infinite; }}
      @keyframes blink {{ 50% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .burst {{ opacity: 0; }} }}
    </style>
  </defs>

  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="30" fill="url(#bg)" stroke="{c["border"]}" stroke-width="2"/>

  <g clip-path="url(#type)"><text class="name" x="{NAME_X}" y="{NAME_Y}" textLength="{NAME_W}" lengthAdjust="spacingAndGlyphs">{NAME}</text></g>
  <rect class="caret" x="{NAME_X + NAME_W + 6}" y="{NAME_Y - 50}" width="5" height="60" rx="2.5" fill="{c["caret"]}">
    <animate attributeName="x" values="{caret_x}" dur="1.9s" begin=".3s" calcMode="discrete" fill="freeze"/>
  </rect>
  <text class="role" x="{NAME_X + 2}" y="{NAME_Y + 50}">Front-End &amp; Marketing Technology Engineer</text>

  {keys_svg(c)}
</svg>
'''


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    for theme in THEMES:
        (root / "assets" / f"banner-{theme}.svg").write_text(build(theme))
        print(f"wrote assets/banner-{theme}.svg")
