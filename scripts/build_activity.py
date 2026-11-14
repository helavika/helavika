"""Build the GitHub activity card (assets/activity-*.svg): a full-width pixel heatmap of the last
12 months plus streak stats, in the same look as the numbers row.

Data comes from the GitHub GraphQL API: with GITHUB_TOKEN set (the daily workflow) it calls the
API directly, otherwise it uses the local `gh` CLI.

Run: python3 scripts/build_activity.py    # needs fonttools, like build_banner.py
"""
import json
import os
import subprocess
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

from build_banner import FONTS, ROOT, THEMES, Face

USER = "helavika"
QUERY = """{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions
weeks{contributionDays{date contributionCount contributionLevel}}}}}}""" % USER

W, H = 1200, 388
PITCH, CELL = 20, 16
LEVELS = {  # GitHub's NONE / FIRST..FOURTH_QUARTILE, as moss shades
    "dark": ["#1c2013", "#34461a", "#557a1f", "#7fa82c", "#a8d43a"],
    "light": ["#dccfae", "#b9c48a", "#8fa24a", "#6a8424", "#4f6b12"],
}
LEVEL_INDEX = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": QUERY}).encode(),
                                     {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
        data = json.load(urllib.request.urlopen(req))
    else:
        data = json.loads(subprocess.check_output(["gh", "api", "graphql", "-f", f"query={QUERY}"]))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def stats(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current, i = 0, len(counts) - 1
    if counts[i] == 0:  # today not started yet: count from yesterday
        i -= 1
    while i >= 0 and counts[i]:
        current, i = current + 1, i - 1
    best = max(days, key=lambda d: d["contributionCount"])
    return current, longest, best


def build(theme, faces, cal):
    c = THEMES[theme]
    pixel, serif = faces["pixel"], faces["serif"]
    levels = LEVELS[theme]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    current, longest, best = stats(days)
    active = sum(1 for d in days if d["contributionCount"])

    x0, x1, y0, y1 = 10, W - 10, 10, H - 10
    out = [f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{c["panel"]}" stroke="{c["frame"]}" stroke-width="1.5"/>',
           f'<rect x="{x0 + 6}" y="{y0 + 6}" width="{x1 - x0 - 12}" height="{y1 - y0 - 12}" fill="none" stroke="{c["frame"]}" stroke-width="1"/>']
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        out.append(f'<rect x="{cx - 5}" y="{cy - 5}" width="10" height="10" transform="rotate(45 {cx} {cy})" fill="{c["frame"]}"/>')

    gx = (W - len(weeks) * PITCH + (PITCH - CELL)) / 2
    gy = 92

    # heading and legend
    head = "CONTRIBUTIONS · LAST 12 MONTHS"
    out.append(f'<path d="{pixel.path(head, 26, gx, 52)}" fill="{c["moss"]}"/>')
    lx = W - gx - 5 * (CELL - 2 + 4) - pixel.width("MORE", 18) - 10
    out.append(f'<path d="{pixel.path("LESS", 18, lx - pixel.width("LESS", 18) - 10, 49)}" fill="{c["muted"]}"/>')
    for i, col in enumerate(levels):
        out.append(f'<rect x="{lx + i * (CELL + 2):.1f}" y="36" width="{CELL - 2}" height="{CELL - 2}" fill="{col}"/>')
    out.append(f'<path d="{pixel.path("MORE", 18, lx + 5 * (CELL + 2) + 8, 49)}" fill="{c["muted"]}"/>')

    # month labels over the first week that starts in each month
    last_month = None
    for wi, w in enumerate(weeks):
        first = date.fromisoformat(w["contributionDays"][0]["date"])
        m = first.strftime("%b").upper()
        if m != last_month and first.day <= 7 and wi < len(weeks) - 1:
            out.append(f'<path d="{pixel.path(m, 21, gx + wi * PITCH, gy - 10)}" fill="{c["muted"]}"/>')
        last_month = m if first.day <= 7 else last_month

    # heatmap: columns appear left to right once, today's cell pulses
    today = days[-1]["date"]
    for wi, w in enumerate(weeks):
        cells = []
        for d in w["contributionDays"]:
            wd = (date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday on top, like GitHub
            fill = levels[LEVEL_INDEX.get(d["contributionLevel"], 0)]
            cls = ' class="today"' if d["date"] == today else ""
            cells.append(f'<rect{cls} x="{gx + wi * PITCH:.1f}" y="{gy + wd * PITCH}" width="{CELL}" height="{CELL}" fill="{fill}"/>')
        out.append(f'<g class="col" style="animation-delay:{wi * .025:.3f}s">{"".join(cells)}</g>')

    # stats row
    sy = gy + 7 * PITCH + 22
    out.append(f'<path d="M{x0 + 30} {sy}H{x1 - 30}" stroke="{c["frame"]}" stroke-width="1" stroke-dasharray="2 4"/>')
    best_day = date.fromisoformat(best["date"])
    cells = [(f'{cal["totalContributions"]:,}', "contributions", "in the last year"),
             (str(active), "active days", "with contributions"),
             (str(current), "current streak", "days in a row" if current != 1 else "day so far"),
             (str(longest), "longest streak", "days in a row" if longest != 1 else "day"),
             (str(best["contributionCount"]), "on the busiest day", best_day.strftime("%-d %B %Y"))]
    cw = (x1 - x0) / len(cells)
    for i, (num, l1, l2) in enumerate(cells):
        mid = x0 + cw * (i + .5)
        if i:
            out.append(f'<path d="M{x0 + cw * i:.1f} {sy + 18}V{y1 - 18}" stroke="{c["frame"]}" stroke-width="1" stroke-dasharray="2 4"/>')
        nw = pixel.width(num, 52)
        out.append(f'<path d="{pixel.path(num, 52, mid - nw / 2, sy + 52)}" fill="{c["moss"]}"/>')
        for j, line in enumerate((l1, l2)):
            lw = serif.width(line, 20)
            out.append(f'<path d="{serif.path(line, 20, mid - lw / 2, sy + 78 + j * 23)}" fill="{c["muted"]}"/>')

    label = escape(f'{cal["totalContributions"]} contributions in the last year, {active} active days, '
                   f'current streak {current} days, longest streak {longest} days, busiest day {best["contributionCount"]} on {best["date"]}')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <style>
    .col {{ animation: col .5s steps(3) both; }}
    @keyframes col {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    .today {{ stroke: {c["moss"]}; stroke-width: 2; animation: today 1.2s steps(1) infinite; }}
    @keyframes today {{ 50% {{ stroke-opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  {chr(10).join("  " + s for s in out).lstrip()}
</svg>
'''


if __name__ == "__main__":
    faces = {k: Face(k) for k in FONTS}
    cal = fetch()
    for theme in THEMES:
        out = ROOT / "assets" / f"activity-{theme}.svg"
        out.write_text(build(theme, faces, cal))
        print(f"wrote assets/activity-{theme}.svg ({out.stat().st_size // 1024} KB)")
