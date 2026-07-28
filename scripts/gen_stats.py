#!/usr/bin/env python3
"""Generate the profile's analytics SVGs from the GitHub GraphQL API.

Renders three animated cards into assets/generated/ using the same neon
palette as assets/hero.svg, so the profile owns its own analytics instead of
depending on third-party card services that go down.

Usage:
    GH_TOKEN=<token> python scripts/gen_stats.py [--login MfmRifath] [--out assets/generated]

Stdlib only -- no pip install step in CI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from xml.sax.saxutils import escape

API = "https://api.github.com/graphql"

# Palette lifted from assets/hero.svg so every card reads as one system.
BG = "#05060f"
PANEL = "#0b1030"
BORDER = "#16204a"
CYAN = "#00f0ff"
MAGENTA = "#ff2bd6"
PURPLE = "#7c4dff"
GREEN = "#39ff88"
YELLOW = "#ffd21e"
TEXT = "#e6f6ff"
MUTED = "#8ea0d0"
DIM = "#3f4d78"

ACCENTS = [CYAN, MAGENTA, PURPLE, GREEN, YELLOW, "#ff6633"]
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    login
    name
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(
      first: 100
      after: $cursor
      ownerAffiliations: OWNER
      isFork: false
      orderBy: { field: PUSHED_AT, direction: DESC }
    ) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


@dataclass
class Stats:
    login: str
    name: str
    followers: int = 0
    commits: int = 0
    prs: int = 0
    issues: int = 0
    contributions: int = 0
    repos: int = 0
    stars: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    calendar: list[tuple[str, int]] = field(default_factory=list)


def graphql(token: str, variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats-generator",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        sys.exit(f"GitHub API returned {exc.code}: {exc.read().decode(errors='replace')[:400]}")
    except urllib.error.URLError as exc:
        sys.exit(f"Could not reach the GitHub API: {exc.reason}")

    if payload.get("errors"):
        sys.exit(f"GraphQL errors: {json.dumps(payload['errors'])[:400]}")
    return payload["data"]


def collect(token: str, login: str) -> Stats:
    """Page through the user's repositories, accumulating stars and languages."""
    cursor = None
    stats: Stats | None = None

    while True:
        user = graphql(token, {"login": login, "cursor": cursor})["user"]
        if user is None:
            sys.exit(f"No such GitHub user: {login}")

        if stats is None:
            contrib = user["contributionsCollection"]
            cal = contrib["contributionCalendar"]
            stats = Stats(
                login=user["login"],
                name=user["name"] or user["login"],
                followers=user["followers"]["totalCount"],
                commits=contrib["totalCommitContributions"],
                prs=contrib["totalPullRequestContributions"],
                issues=contrib["totalIssueContributions"],
                contributions=cal["totalContributions"],
                repos=user["repositories"]["totalCount"],
                calendar=[
                    (day["date"], day["contributionCount"])
                    for week in cal["weeks"]
                    for day in week["contributionDays"]
                ],
            )

        for node in user["repositories"]["nodes"]:
            stats.stars += node["stargazerCount"]
            for edge in node["languages"]["edges"]:
                stats.languages[edge["node"]["name"]] = (
                    stats.languages.get(edge["node"]["name"], 0) + edge["size"]
                )

        page = user["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            return stats
        cursor = page["endCursor"]


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0k", "k")
    return str(n)


def shell(width: int, height: int, title: str, body: str, extra_css: str = "") -> str:
    """Wrap card content in the shared frame: bezel, corner brackets, scanlines."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" fill="none" role="img" aria-label="{escape(title)}">
  <defs>
    <style>
      @keyframes rise {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
      @keyframes sweep {{ from {{ transform:translateX(-260px); }} to {{ transform:translateX({width + 40}px); }} }}
      @keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.15; }} }}
      .rise {{ opacity:0; animation: rise .55s cubic-bezier(.2,.8,.2,1) forwards; }}
      .sweep {{ animation: sweep 5s linear infinite; }}
      .blink {{ animation: blink 1.5s steps(1,end) infinite; }}
      {extra_css}
      @media (prefers-reduced-motion: reduce) {{
        .rise, .sweep, .blink, .grow, .cell {{ animation: none; }}
        .rise, .cell {{ opacity:1; transform:none; }}
        .grow {{ transform: scaleX(1); }}
      }}
    </style>
    <linearGradient id="cy" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CYAN}"/><stop offset="100%" stop-color="{PURPLE}"/>
    </linearGradient>
    <linearGradient id="swp" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{CYAN}" stop-opacity=".5"/>
      <stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.4" fill="#0a1430" opacity=".55"/>
    </pattern>
    <filter id="neon" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="card"><rect width="{width}" height="{height}" rx="10"/></clipPath>
  </defs>

  <g clip-path="url(#card)" font-family="{MONO}">
    <rect width="{width}" height="{height}" fill="{BG}"/>
    <rect class="blink" x="22" y="21" width="9" height="9" fill="{CYAN}" filter="url(#neon)"/>
    <text x="42" y="30" font-size="13" font-weight="700" letter-spacing="2.5" fill="{CYAN}" filter="url(#neon)">{escape(title)}</text>
    <rect x="22" y="44" width="{width - 44}" height="1.4" fill="url(#cy)" opacity=".55"/>

{body}

    <rect width="{width}" height="{height}" fill="url(#scan)" opacity=".45"/>
    <g class="sweep"><rect x="-260" y="0" width="260" height="{height}" fill="url(#swp)" opacity=".12"/></g>
    <g stroke="{CYAN}" stroke-width="2" fill="none" filter="url(#neon)">
      <path d="M12 34V12h22M{width - 34} 12h22v22M{width - 12} {height - 34}v22h-22M34 {height - 12}H12v-22"/>
    </g>
    <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="none" stroke="{BORDER}" stroke-width="2"/>
  </g>
</svg>
"""


def render_stats(s: Stats) -> str:
    w, h = 600, 260
    cells = [
        ("COMMITS", human(s.commits), CYAN),
        ("STARS", human(s.stars), MAGENTA),
        ("REPOS", human(s.repos), PURPLE),
        ("PULL REQS", human(s.prs), GREEN),
        ("ISSUES", human(s.issues), YELLOW),
        ("FOLLOWERS", human(s.followers), CYAN),
    ]
    body = []
    for i, (label, value, color) in enumerate(cells):
        col, row = i % 3, i // 3
        x = 30 + col * 187
        y = 78 + row * 88
        body.append(
            f'    <g class="rise" style="animation-delay:{i * 70}ms">\n'
            f'      <rect x="{x}" y="{y - 24}" width="172" height="68" rx="6" fill="{PANEL}" stroke="{color}" stroke-opacity=".38"/>\n'
            f'      <text x="{x + 15}" y="{y + 5}" font-size="27" font-weight="700" fill="{color}" filter="url(#neon)">{value}</text>\n'
            f'      <text x="{x + 15}" y="{y + 28}" font-size="10.5" letter-spacing="2" fill="{MUTED}">{label}</text>\n'
            f"    </g>"
        )

    body.append(
        f'    <text x="30" y="{h - 22}" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"// {human(s.contributions)} CONTRIBUTIONS IN THE LAST YEAR</text>"
    )
    body.append(
        f'    <text x="{w - 30}" y="{h - 22}" text-anchor="end" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"{date.today().isoformat()}</text>"
    )
    return shell(w, h, "> gh --stats", "\n".join(body))


def render_languages(s: Stats, top: int = 6) -> str:
    w, h = 600, 260
    ranked = sorted(s.languages.items(), key=lambda kv: kv[1], reverse=True)[:top]
    if not ranked:
        return shell(w, h, "> lang --top", f'    <text x="30" y="140" font-size="13" fill="{MUTED}">no language data</text>')

    total = sum(size for _, size in ranked) or 1
    body = []
    for i, (lang, size) in enumerate(ranked):
        pct = size / total * 100
        color = ACCENTS[i % len(ACCENTS)]
        y = 76 + i * 29
        bar_w = max(2.0, pct / 100 * 350)
        body.append(
            f'    <g class="rise" style="animation-delay:{i * 80}ms">\n'
            f'      <text x="30" y="{y + 11}" font-size="12.5" fill="{TEXT}">{escape(lang)}</text>\n'
            f'      <rect x="170" y="{y + 1}" width="350" height="12" rx="6" fill="{PANEL}"/>\n'
            f'      <rect class="grow" x="170" y="{y + 1}" width="{bar_w:.1f}" height="12" rx="6" fill="{color}" '
            f'filter="url(#neon)" style="transform-origin:170px 0;animation-delay:{i * 80 + 120}ms"/>\n'
            f'      <text x="{w - 30}" y="{y + 11}" text-anchor="end" font-size="11.5" fill="{color}">{pct:.1f}%</text>\n'
            f"    </g>"
        )

    body.append(
        f'    <text x="30" y="{h - 22}" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"// BY BYTES ACROSS {s.repos} OWNED REPOS, FORKS EXCLUDED</text>"
    )
    css = "@keyframes grow { from { transform:scaleX(0); } to { transform:scaleX(1); } } " \
          ".grow { transform:scaleX(0); animation: grow .85s cubic-bezier(.2,.8,.2,1) forwards; }"
    return shell(w, h, "> lang --top", "\n".join(body), extra_css=css)


def render_activity(s: Stats) -> str:
    """Contribution heatmap; cells fade in on a diagonal wave."""
    weeks = 53
    cell, gap = 17, 4
    w = 60 + weeks * (cell + gap)
    h = 190

    days = s.calendar[-weeks * 7:]
    peak = max((c for _, c in days), default=0) or 1

    body = []
    for idx, (day, count) in enumerate(days):
        col, row = idx // 7, idx % 7
        x = 32 + col * (cell + gap)
        y = 62 + row * (cell + gap)
        if count == 0:
            fill, opacity = PANEL, "1"
        else:
            ratio = count / peak
            fill = CYAN if ratio < 0.34 else (PURPLE if ratio < 0.67 else MAGENTA)
            opacity = f"{0.42 + ratio * 0.58:.2f}"
        glow = ' filter="url(#neon)"' if count >= peak * 0.8 else ""
        body.append(
            f'    <rect class="cell" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{fill}" opacity="{opacity}"{glow} style="animation-delay:{col * 14 + row * 6}ms">'
            f"<title>{day}: {count} contributions</title></rect>"
        )

    legend_x = w - 226
    body.append(f'    <text x="{legend_x - 44}" y="{h - 20}" font-size="10.5" fill="{DIM}" letter-spacing="1.4">LESS</text>')
    for i, (c, o) in enumerate([(PANEL, "1"), (CYAN, ".5"), (CYAN, ".85"), (PURPLE, ".9"), (MAGENTA, "1")]):
        body.append(f'    <rect x="{legend_x + i * 22}" y="{h - 31}" width="15" height="15" rx="3" fill="{c}" opacity="{o}"/>')
    body.append(f'    <text x="{legend_x + 122}" y="{h - 20}" font-size="10.5" fill="{DIM}" letter-spacing="1.4">MORE</text>')
    body.append(
        f'    <text x="32" y="{h - 20}" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"// {human(s.contributions)} CONTRIBUTIONS</text>"
    )

    # Animate transform only -- animating to `opacity:inherit` would resolve against
    # the parent group and flatten each cell's per-intensity opacity attribute.
    css = "@keyframes pop { from { transform:scale(.35); } to { transform:scale(1); } } " \
          ".cell { transform-box:fill-box; transform-origin:center; animation: pop .4s ease-out backwards; }"
    return shell(w, h, "> contrib --calendar", "\n".join(body), extra_css=css)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--login", default=os.environ.get("GH_LOGIN", "MfmRifath"))
    parser.add_argument("--out", default="assets/generated")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN (or GITHUB_TOKEN) to a token with public_repo / read:user scope.")

    stats = collect(token, args.login)
    os.makedirs(args.out, exist_ok=True)

    for name, svg in (
        ("stats.svg", render_stats(stats)),
        ("languages.svg", render_languages(stats)),
        ("activity.svg", render_activity(stats)),
    ):
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        print(f"wrote {path}")

    print(
        f"{stats.name}: {stats.commits} commits, {stats.stars} stars, "
        f"{stats.repos} repos, {stats.contributions} contributions"
    )


if __name__ == "__main__":
    main()
