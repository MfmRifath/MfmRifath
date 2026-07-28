#!/usr/bin/env python3
"""Generate the profile's analytics SVGs from the GitHub GraphQL API.

Renders five animated cards into assets/generated/ using the same neon palette
as assets/hero.svg, so the profile owns its own analytics instead of depending
on third-party card services that go down.

Usage:
    GH_TOKEN=<token> python scripts/gen_stats.py [--login MfmRifath] [--out assets/generated]
    python scripts/gen_stats.py --exclude-lang "Jupyter Notebook" --exclude-lang HTML

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
SUNKEN = "#080c22"
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

# Monospace advance width as a fraction of font-size. Used to size the typing
# reveal and to truncate text that would overrun its tile.
CHAR_W = 0.6

# Lines cycled by the tagline strip. Edit freely; the animation re-times itself.
TAGLINE = [
    "fine-tuning Llama 3 with QLoRA for Tamil-medium physics",
    "hybrid RAG -- retrieval beats a bigger model",
    "LangGraph agents + Bayesian Knowledge Tracing",
]

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
    pinnedItems(first: 4, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name description url stargazerCount forkCount
          primaryLanguage { name }
        }
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
        name description url stargazerCount forkCount
        primaryLanguage { name }
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


@dataclass
class Repo:
    name: str
    description: str
    url: str
    stars: int
    forks: int
    language: str


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
    showcase: list[Repo] = field(default_factory=list)
    showcase_source: str = "MOST STARRED"


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


def to_repo(node: dict) -> Repo:
    lang = node.get("primaryLanguage") or {}
    return Repo(
        name=node["name"],
        description=(node.get("description") or "").strip(),
        url=node["url"],
        stars=node["stargazerCount"],
        forks=node["forkCount"],
        language=lang.get("name") or "—",
    )


def collect(token: str, login: str, exclude_langs: frozenset[str] = frozenset()) -> Stats:
    """Page through the user's repositories, accumulating stars and languages."""
    cursor = None
    stats: Stats | None = None
    every_repo: list[Repo] = []
    pinned: list[Repo] = []

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
            pinned = [to_repo(n) for n in user["pinnedItems"]["nodes"] if n]

        for node in user["repositories"]["nodes"]:
            stats.stars += node["stargazerCount"]
            every_repo.append(to_repo(node))
            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in exclude_langs:
                    continue
                stats.languages[name] = stats.languages.get(name, 0) + edge["size"]

        page = user["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]

    # Respect the profile's own pinned selection. Falling back to most-starred
    # otherwise, minus the profile repo itself -- "Config files for my GitHub
    # profile" is a wasted showcase tile -- and breaking star ties toward repos
    # that actually carry a description.
    fallback = [r for r in every_repo if r.name.casefold() != login.casefold()]
    fallback.sort(key=lambda r: (r.stars, bool(r.description)), reverse=True)
    stats.showcase = pinned or fallback[:4]
    stats.showcase_source = "PINNED" if pinned else "MOST STARRED"
    return stats


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0k", "k")
    return str(n)


def fit(text: str, width: float, size: float) -> str:
    """Truncate to what fits in `width` px at `size` px monospace."""
    limit = max(1, int(width / (size * CHAR_W)))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def wrap(text: str, width: float, size: float, lines: int) -> list[str]:
    """Greedy word wrap into at most `lines` rows, ellipsising any overflow."""
    limit = max(1, int(width / (size * CHAR_W)))
    out: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            out.append(current)
        current = word
        if len(out) == lines:
            break
    if current and len(out) < lines:
        out.append(current)
    if not out:
        return []
    consumed = len(" ".join(out))
    if consumed < len(text):
        out[-1] = fit(out[-1] + " " + text[consumed:].strip(), width, size)
    return out[:lines]


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
        x, y = 30 + col * 187, 78 + row * 88
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
            f'      <text x="30" y="{y + 11}" font-size="12.5" fill="{TEXT}">{escape(fit(lang, 132, 12.5))}</text>\n'
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
    css = (
        "@keyframes grow { from { transform:scaleX(0); } to { transform:scaleX(1); } } "
        ".grow { transform:scaleX(0); animation: grow .85s cubic-bezier(.2,.8,.2,1) forwards; }"
    )
    return shell(w, h, "> lang --top", "\n".join(body), extra_css=css)


def render_repos(s: Stats) -> str:
    """Two-by-two showcase of pinned repos, or the most-starred as fallback."""
    w, h = 1200, 344
    tile_w, tile_h = 560, 118
    body = []

    for i, repo in enumerate(s.showcase[:4]):
        col, row = i % 2, i // 2
        x = 30 + col * (tile_w + 20)
        y = 68 + row * (tile_h + 18)
        accent = ACCENTS[i % len(ACCENTS)]

        body.append(f'    <g class="rise" style="animation-delay:{i * 90}ms">')
        body.append(
            f'      <rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" rx="7" '
            f'fill="{PANEL}" stroke="{accent}" stroke-opacity=".34"/>'
        )
        body.append(
            f'      <text x="{x + 20}" y="{y + 31}" font-size="15" font-weight="700" fill="{accent}" '
            f'filter="url(#neon)">{escape(fit(repo.name, tile_w - 40, 15))}</text>'
        )

        desc_lines = wrap(repo.description or "No description.", tile_w - 40, 11.5, 2)
        for j, line in enumerate(desc_lines):
            body.append(
                f'      <text x="{x + 20}" y="{y + 54 + j * 17}" font-size="11.5" '
                f'fill="{MUTED}">{escape(line)}</text>'
            )

        fy = y + tile_h - 18
        body.append(f'      <circle cx="{x + 25}" cy="{fy - 4}" r="5" fill="{accent}"/>')
        body.append(
            f'      <text x="{x + 37}" y="{fy}" font-size="11.5" fill="{TEXT}">'
            f"{escape(fit(repo.language, 160, 11.5))}</text>"
        )
        body.append(
            f'      <text x="{x + tile_w - 20}" y="{fy}" text-anchor="end" font-size="11.5" '
            f'fill="{MUTED}">★ {repo.stars}   ⎇ {repo.forks}</text>'
        )
        body.append("    </g>")

    body.append(
        f'    <text x="30" y="{h - 20}" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"// {s.showcase_source} · {human(s.stars)} STARS ACROSS {s.repos} REPOS</text>"
    )
    return shell(w, h, "> ls ./repos --showcase", "\n".join(body))


def render_activity(s: Stats) -> str:
    """Contribution heatmap. Cells are grouped per column so one delay drives
    seven rects -- a left-to-right wave at a fraction of the markup."""
    weeks = 53
    cell, gap = 17, 4
    w = 60 + weeks * (cell + gap)
    h = 190

    days = s.calendar[-weeks * 7:]
    peak = max((c for _, c in days), default=0) or 1

    body = []
    for col in range(0, (len(days) + 6) // 7):
        chunk = days[col * 7:(col + 1) * 7]
        if not chunk:
            continue
        x = 32 + col * (cell + gap)
        body.append(f'    <g class="cell" style="animation-delay:{col * 16}ms">')
        for row, (_, count) in enumerate(chunk):
            y = 62 + row * (cell + gap)
            if count == 0:
                fill, opacity = PANEL, "1"
            else:
                ratio = count / peak
                fill = CYAN if ratio < 0.34 else (PURPLE if ratio < 0.67 else MAGENTA)
                opacity = f"{0.42 + ratio * 0.58:.2f}"
            glow = ' filter="url(#neon)"' if count >= peak * 0.8 else ""
            body.append(
                f'      <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{fill}" opacity="{opacity}"{glow}/>'
            )
        body.append("    </g>")

    legend_x = w - 226
    body.append(f'    <text x="{legend_x - 44}" y="{h - 20}" font-size="10.5" fill="{DIM}" letter-spacing="1.4">LESS</text>')
    for i, (c, o) in enumerate([(PANEL, "1"), (CYAN, ".5"), (CYAN, ".85"), (PURPLE, ".9"), (MAGENTA, "1")]):
        body.append(f'    <rect x="{legend_x + i * 22}" y="{h - 31}" width="15" height="15" rx="3" fill="{c}" opacity="{o}"/>')
    body.append(f'    <text x="{legend_x + 122}" y="{h - 20}" font-size="10.5" fill="{DIM}" letter-spacing="1.4">MORE</text>')
    body.append(
        f'    <text x="32" y="{h - 20}" font-size="11" fill="{DIM}" letter-spacing="1.4">'
        f"// {human(s.contributions)} CONTRIBUTIONS</text>"
    )

    # Transform only -- animating to `opacity:inherit` would resolve against the
    # parent group and flatten each cell's per-intensity opacity attribute.
    css = (
        "@keyframes pop { from { transform:scale(.35); } to { transform:scale(1); } } "
        ".cell { transform-box:fill-box; transform-origin:center; animation: pop .4s ease-out backwards; }"
    )
    return shell(w, h, "> contrib --calendar", "\n".join(body), extra_css=css)


def render_tagline(lines: list[str] = None, hold: float = 3.6) -> str:
    """Terminal strip that types each line in turn, then cycles.

    The reveal is a background-coloured rect sliding right off the text, rather
    than an animated clip-path -- plain translateX is the widest-supported thing
    that does the job, and the strip has its own opaque ground to slide over.
    """
    lines = lines or TAGLINE
    w, h = 1200, 62
    size = 16
    prompt_x, baseline = 34, 38
    total = hold * len(lines)
    type_dur = 1.5

    keyframes, body = [], []
    for i, line in enumerate(lines):
        text_w = len(line) * size * CHAR_W
        start = i * hold
        p_start = start / total * 100
        p_typed = (start + type_dur) / total * 100
        p_end = (start + hold) / total * 100
        # steps(1,end) on the wrapper keeps each line hard on/off, no crossfade.
        keyframes.append(
            f"      @keyframes show{i} {{ 0%,{p_start:.3f}% {{ opacity:0; }} "
            f"{p_start:.3f}%,{p_end - 0.001:.3f}% {{ opacity:1; }} {p_end:.3f}%,100% {{ opacity:0; }} }}"
        )
        keyframes.append(
            f"      @keyframes type{i} {{ 0%,{p_start:.3f}% {{ transform:translateX(0); }} "
            f"{p_typed:.3f}%,100% {{ transform:translateX({text_w:.1f}px); }} }}"
        )
        body.append(
            f'    <g style="animation:show{i} {total}s steps(1,end) infinite">\n'
            f'      <text x="{prompt_x + 22}" y="{baseline}" font-size="{size}" fill="{TEXT}">{escape(line)}</text>\n'
            f'      <g style="animation:type{i} {total}s linear infinite" transform="translate({prompt_x + 22} 0)">\n'
            f'        <rect x="-10" y="{baseline - 14}" width="9" height="18" fill="{CYAN}" filter="url(#tg)"/>\n'
            f'        <rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>\n'
            f"      </g>\n"
            f"    </g>"
        )

    reduced = ", ".join(f"[style*='show{i}'], [style*='type{i}']" for i in range(len(lines)))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none" role="img" aria-label="{escape(' / '.join(lines))}">
  <defs>
    <style>
{chr(10).join(keyframes)}
      @keyframes cur {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.2; }} }}
      .cur {{ animation: cur 1.1s steps(1,end) infinite; }}
      @media (prefers-reduced-motion: reduce) {{
        {reduced} {{ animation: none !important; }}
        .cur {{ animation: none; }}
      }}
    </style>
    <filter id="tg" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="strip"><rect width="{w}" height="{h}" rx="8"/></clipPath>
  </defs>

  <g clip-path="url(#strip)" font-family="{MONO}">
    <rect width="{w}" height="{h}" fill="{BG}"/>
    <text class="cur" x="{prompt_x - 12}" y="{baseline}" font-size="{size}" font-weight="700" fill="{CYAN}" filter="url(#tg)">&gt;</text>

{chr(10).join(body)}

    <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="8" fill="none" stroke="{BORDER}" stroke-width="2"/>
  </g>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--login", default=os.environ.get("GH_LOGIN", "MfmRifath"))
    parser.add_argument("--out", default="assets/generated")
    parser.add_argument(
        "--exclude-lang",
        action="append",
        default=[],
        metavar="NAME",
        help="Language to leave out of the breakdown. Repeatable. Worth considering "
             "for Jupyter Notebook, whose byte count includes base64 cell output.",
    )
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN (or GITHUB_TOKEN) to a token with public_repo / read:user scope.")

    stats = collect(token, args.login, frozenset(args.exclude_lang))
    os.makedirs(args.out, exist_ok=True)

    for name, svg in (
        ("stats.svg", render_stats(stats)),
        ("languages.svg", render_languages(stats)),
        ("repos.svg", render_repos(stats)),
        ("activity.svg", render_activity(stats)),
        ("tagline.svg", render_tagline()),
    ):
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        print(f"wrote {path}  ({len(svg) / 1024:.0f} KB)")

    print(
        f"{stats.name}: {stats.commits} commits, {stats.stars} stars, "
        f"{stats.repos} repos, {stats.contributions} contributions, "
        f"showcase={[r.name for r in stats.showcase]}"
    )


if __name__ == "__main__":
    main()
