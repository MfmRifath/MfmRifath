#!/usr/bin/env python3
"""Generate the profile's analytics SVGs from the GitHub GraphQL API.

Renders four cards into assets/generated/, each in a light and a dark variant,
in the editorial system defined by scripts/design.py. The profile owns its own
analytics instead of depending on third-party card services that go down.

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
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

import design as d
from design import LIGHT, Theme, num

API = "https://api.github.com/graphql"

# Lines scrolled by the marquee band (built by build_assets.py). Edit freely;
# the scroll re-times itself to the copy length.
TAGLINE = [
    "real-time fraud scoring -- p95 6.6 ms, champion/challenger MLOps",
    "fine-tuning Llama 3 with QLoRA for Tamil-medium physics",
    "hybrid RAG -- retrieval beats a bigger model",
    "Kafka + Avro streams with retry and dead letter queues",
]

# Showcase used when nothing is pinned on the profile, in this order. The note
# stands in for a missing GitHub description; a real description always wins.
# Names that no longer resolve to an owned repo are skipped.
FEATURED = [
    ("FraudShield", "Real-time card-fraud scoring: streaming features, a champion/challenger "
                    "MLOps loop and drift-triggered retraining."),
    ("TalentScout-AI", ""),
    ("kafka-order-pipeline", "Kafka order stream in Avro with real-time aggregation, "
                             "backoff retry and a dead letter queue."),
    ("ai-engineering-roadmap", ""),
]

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    login
    name
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    pinnedItems(first: 4, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name description url stargazerCount forkCount pushedAt
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
        name description url stargazerCount forkCount pushedAt
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
    pushed: str = ""  # YYYY-MM-DD of the last push, blank if unknown


@dataclass
class Stats:
    login: str
    name: str
    followers: int = 0
    commits: int = 0
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
        pushed=(node.get("pushedAt") or "")[:10],
    )


def pick_showcase(pinned: list[Repo], every_repo: list[Repo], login: str,
                  featured: list[tuple[str, str]] = FEATURED) -> tuple[list[Repo], str]:
    """Pinned repos if any, else the FEATURED list, else the most starred."""
    if pinned:
        return pinned[:4], "PINNED"

    by_name = {r.name.casefold(): r for r in every_repo}
    chosen = []
    for name, note in featured:
        repo = by_name.get(name.casefold())
        if repo:
            if not repo.description and note:
                repo = replace(repo, description=note)
            chosen.append(repo)
    if chosen:
        return chosen[:4], "FEATURED"

    # Minus the profile repo itself -- "Config files for my GitHub profile" is
    # a wasted tile -- and breaking star ties toward repos with a description.
    fallback = [r for r in every_repo if r.name.casefold() != login.casefold()]
    fallback.sort(key=lambda r: (r.stars, bool(r.description)), reverse=True)
    return fallback[:4], "MOST STARRED"


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

    stats.showcase, stats.showcase_source = pick_showcase(pinned, every_repo, login)
    return stats


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0k", "k")
    return str(n)


def longest_streak(calendar: list[tuple[str, int]]) -> int:
    best = run = 0
    for _, count in calendar:
        run = run + 1 if count else 0
        best = max(best, run)
    return best


def active_days(calendar: list[tuple[str, int]]) -> int:
    return sum(1 for _, count in calendar if count)


# --------------------------------------------------------------------- cards

CARD_W, CARD_H = 600, 308
INNER = CARD_W - 2 * d.MARGIN


def card_head(left: str, right: str, t: Theme, w: float = CARD_W) -> list[str]:
    return [
        d.label(d.MARGIN, 38, left, t, fill=t.ink),
        d.label(w - d.MARGIN, 38, right, t, anchor="end"),
        d.rule(d.MARGIN, 52, w - 2 * d.MARGIN, t, ms=0),
    ]


def render_stats(s: Stats, t: Theme = LIGHT) -> str:
    # PR and issue counts sit near zero for solo work; calendar-derived
    # numbers say more about cadence.
    cells = [
        ("Commits", human(s.commits)),
        ("Stars", human(s.stars)),
        ("Repos", human(s.repos)),
        ("Active days", human(active_days(s.calendar))),
        ("Best streak", f"{longest_streak(s.calendar)}d"),
        ("Followers", human(s.followers)),
    ]
    cw, rh, top = INNER / 3, 100, 56
    b = card_head("GitHub — last 12 months", date.today().isoformat(), t)
    for i, (name, value) in enumerate(cells):
        c, r = i % 3, i // 3
        x = d.MARGIN + c * cw
        y = top + r * rh
        tx = x if c == 0 else x + 20
        if c:
            b.append(d.vrule(x, y + 16, rh - 32, t))
        b.append(f'<g class="reveal"{d.delay(100 + i * 70)}>')
        b.append(d.text(tx, y + 60, value, t, size=44, weight=800, ls=-1.2,
                        fill=t.acc if i == 0 else t.ink))
        b.append(d.label(tx, y + 82, name, t))
        b.append("</g>")
    b.append(d.rule(d.MARGIN, top + rh, INNER, t, weight=1, color=t.hair, ms=None))
    b.append(d.rule(d.MARGIN, top + 2 * rh + 4, INNER, t, ms=300))
    b.append(d.label(d.MARGIN, CARD_H - 22,
                     f"{human(s.contributions)} contributions in the last year", t))
    b.append(d.label(CARD_W - d.MARGIN, CARD_H - 22, f"@{s.login}", t, anchor="end"))
    label = ", ".join(f"{v} {n.lower()}" for n, v in cells)
    return d.svg_doc(CARD_W, CARD_H, f"GitHub stats: {label}", "\n".join(b), t)


def render_languages(s: Stats, t: Theme = LIGHT, top: int = 6) -> str:
    ranked = sorted(s.languages.items(), key=lambda kv: kv[1], reverse=True)[:top]
    b = card_head("Languages — by bytes", f"{s.repos} repos · forks excluded", t)
    if not ranked:
        b.append(d.text(d.MARGIN, 150, "No language data", t, size=15, fill=t.dim))
        return d.svg_doc(CARD_W, CARD_H, "Languages: no language data", "\n".join(b), t)

    total = sum(size for _, size in ranked) or 1
    tints = [1, .82, .6, .42, .27, .16]
    x = float(d.MARGIN)
    for i, (_, size) in enumerate(ranked):
        seg = size / total * INNER
        fill = t.acc if i == 0 else t.ink
        opacity = 1 if i == 0 else tints[i]
        b.append(f'<rect x="{num(x)}" y="72" width="{num(max(seg - 2, 1))}" height="18" '
                 f'fill="{fill}" opacity="{num(opacity)}" class="draw"{d.delay(150 + i * 80)}/>')
        x += seg

    rows = []
    for i, (lang, size) in enumerate(ranked):
        pct = size / total * 100
        y = 126 + i * 27
        fill = t.acc if i == 0 else t.ink
        opacity = 1 if i == 0 else tints[i]
        b.append(f'<g class="reveal"{d.delay(250 + i * 60)}>')
        b.append(f'<rect x="{d.MARGIN}" y="{y - 10}" width="10" height="10" fill="{fill}" '
                 f'opacity="{num(opacity)}"/>')
        b.append(d.text(d.MARGIN + 22, y, d.fit(lang, 300, 15), t, size=15))
        b.append(d.text(CARD_W - d.MARGIN, y, f"{pct:.1f}%", t, size=15, weight=600, anchor="end"))
        b.append("</g>")
        if i < len(ranked) - 1:
            b.append(d.rule(d.MARGIN, y + 9, INNER, t, weight=1, color=t.hair, ms=None))
        rows.append(f"{lang} {pct:.1f}%")
    return d.svg_doc(CARD_W, CARD_H, "Top languages by bytes: " + ", ".join(rows), "\n".join(b), t)


REPO_TOP, REPO_ROW = 56, 104


def render_repos(s: Stats, t: Theme = LIGHT) -> str:
    """Editorial list of pinned, featured or most-starred repos."""
    w = 1200
    shown = s.showcase[:4]
    h = REPO_TOP + max(1, len(shown)) * REPO_ROW + 52
    name_x = d.col_x(1)
    desc_w = d.col_x(9) - name_x - d.GUTTER

    b = card_head("Featured repositories",
                  f"{human(s.stars)} stars across {s.repos} repos", t, w=w)
    for i, repo in enumerate(shown):
        y = REPO_TOP + i * REPO_ROW
        b.append(f'<g class="reveal"{d.delay(120 + i * 90)}>')
        b.append(d.text(d.MARGIN, y + 46, f"{i + 1:02d}", t, size=28, weight=800, fill=t.acc))
        b.append(d.text(name_x, y + 44, d.fit(repo.name, desc_w, 24, 600), t, size=24, weight=600,
                        ls=-0.3))
        if repo.pushed:
            b.append(d.label(w - d.MARGIN, y + 42, f"Pushed {repo.pushed}", t, anchor="end"))
        for j, line in enumerate(d.wrap(repo.description or "No description.", desc_w, 15, 2)):
            b.append(d.text(name_x, y + 70 + j * 20, line, t, size=15, fill=t.dim))
        meta = f"{repo.language}  ·  {plural(repo.stars, 'star')}  ·  {plural(repo.forks, 'fork')}"
        b.append(d.label(w - d.MARGIN, y + 70, meta, t, anchor="end", fill=t.ink))
        b.append("</g>")
        last = i == len(shown) - 1
        b.append(d.rule(d.MARGIN, y + REPO_ROW - 2, w - 2 * d.MARGIN, t,
                        weight=2 if last else 1, color=None if last else t.hair,
                        ms=300 if last else None, cls="rowrule"))

    b.append(d.label(d.MARGIN, h - 20, f"Showcase — {s.showcase_source}", t))
    b.append(d.label(w - d.MARGIN, h - 20, "github.com/" + s.login, t, anchor="end"))
    names = ", ".join(r.name for r in shown) or "none"
    return d.svg_doc(w, h, f"Featured repositories ({s.showcase_source.lower()}): {names}",
                     "\n".join(b), t)


ACT_WEEKS, ACT_CELL, ACT_GAP = 53, 16, 4
ACT_STEP = ACT_CELL + ACT_GAP
# Right-aligned so the last column lands exactly on the right margin; the
# weekday labels take the space left over on the left.
ACT_LEFT = 1200 - d.MARGIN - (ACT_WEEKS * ACT_STEP - ACT_GAP)
ACT_TOP = 92


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render_activity(s: Stats, t: Theme = LIGHT) -> str:
    """Contribution heatmap. Cells are grouped per column so one delay drives
    seven rects -- a left-to-right wave at a fraction of the markup."""
    weeks, cell, step, left, top = ACT_WEEKS, ACT_CELL, ACT_STEP, ACT_LEFT, ACT_TOP
    w = 1200
    grid_bottom = top + 7 * step - ACT_GAP
    h = grid_bottom + 64

    # Place each day by its real weekday, Sunday on top as GitHub draws it, so
    # a calendar that starts mid-week does not shear every row by a day. The
    # window is anchored on the last day so it never spills into a 54th column.
    days = s.calendar
    columns: dict[int, list[tuple[int, int]]] = {}
    month_at: dict[int, str] = {}
    if days:
        last = date.fromisoformat(days[-1][0])
        origin = last - timedelta(days=(last.weekday() + 1) % 7 + (weeks - 1) * 7)
        days = [(day, c) for day, c in days if date.fromisoformat(day) >= origin]
    peak = max((c for _, c in days), default=0) or 1
    if days:
        for day, count in days:
            dd = date.fromisoformat(day)
            col = (dd - origin).days // 7
            columns.setdefault(col, []).append(((dd.weekday() + 1) % 7, count))
            if dd.day <= 7 and (dd.weekday() + 1) % 7 == 0:
                month_at[col] = dd.strftime("%b")

    b = card_head("Contributions — last 12 months",
                  f"{plural(active_days(days), 'active day')} · best streak "
                  f"{plural(longest_streak(days), 'day')}", t, w=w)

    last_label = -9
    for col in sorted(month_at):
        if col - last_label >= 3 and col <= weeks - 2:
            b.append(d.label(left + col * step, top - 12, month_at[col], t))
            last_label = col
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b.append(d.label(left - 10, top + row * step + 12, name, t, anchor="end", size=10))

    def shade(count: int) -> tuple[str, str]:
        if count == 0:
            return t.surface, "1"
        ratio = count / peak
        if ratio >= 0.8:
            return t.acc, "1"
        return t.ink, (".25" if ratio < 0.25 else ".5" if ratio < 0.5 else ".78")

    for col in sorted(columns):
        x = left + col * step
        b.append(f'<g class="fade"{d.delay(col * 14)}>')
        for row, count in columns[col]:
            fill, opacity = shade(count)
            b.append(f'<rect x="{x}" y="{top + row * step}" width="{cell}" height="{cell}" '
                     f'fill="{fill}" opacity="{opacity}"/>')
        b.append("</g>")

    b.append(d.rule(d.MARGIN, grid_bottom + 18, w - 2 * d.MARGIN, t, weight=1, color=t.hair, ms=None))
    legend_x = w - d.MARGIN - 5 * 21 - 44
    b.append(d.label(legend_x - 10, h - 20, "Less", t, anchor="end"))
    for i, (fill, opacity) in enumerate([(t.surface, "1"), (t.ink, ".25"), (t.ink, ".5"),
                                         (t.ink, ".78"), (t.acc, "1")]):
        b.append(f'<rect x="{legend_x + i * 21}" y="{h - 31}" width="15" height="15" '
                 f'fill="{fill}" opacity="{opacity}"/>')
    b.append(d.label(w - d.MARGIN, h - 20, "More", t, anchor="end"))
    b.append(d.label(d.MARGIN, h - 20,
                     f"{human(s.contributions)} contributions in the last year", t))
    return d.svg_doc(w, h, f"Contribution heatmap: {human(s.contributions)} contributions in the "
                     f"last year, {active_days(days)} active days", "\n".join(b), t)


RENDERERS = (
    ("stats", render_stats),
    ("languages", render_languages),
    ("repos", render_repos),
    ("activity", render_activity),
)


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
    for name, render in RENDERERS:
        for t in d.THEMES:
            path = os.path.join(args.out, f"{name}{t.suffix}.svg")
            svg = render(stats, t)
            d.write(path, svg)
            print(f"wrote {path}  ({len(svg) / 1024:.0f} KB)")

    print(
        f"{stats.name}: {stats.commits} commits, {stats.stars} stars, "
        f"{stats.repos} repos, {stats.contributions} contributions, "
        f"showcase={[r.name for r in stats.showcase]}"
    )


if __name__ == "__main__":
    main()
