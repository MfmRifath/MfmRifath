"""Shared design system for every profile SVG: tokens, type, motion, primitives.

Modernist editorial, after the portfolio site: Archivo on an off-white ground,
near-mono ink with one red accent, a visible 12-column grid, 2px rules and no
corner radius.

Every asset is rendered twice, light and dark. An SVG shown through <img> sees
the OS colour scheme rather than GitHub's theme setting, so the README picks
the right file with <picture>, which GitHub does resolve against its theme.

Motion rule: an element's attributes are always its *resting* state, and
animations only supply the starting state (fill-mode `backwards`). Turning
motion off can then never leave something half-drawn -- reduced motion is a
single `animation:none`. Looping effects that should vanish at rest (ticks,
flashes) rest at opacity 0.

Stdlib only -- no pip install step in CI.
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from xml.sax.saxutils import escape

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
FAMILY = "Archivo"
FONT_STACK = "Archivo,'Helvetica Neue',Helvetica,Arial,sans-serif"
EASE = "cubic-bezier(.2,.8,.2,1)"


@dataclass(frozen=True)
class Theme:
    name: str
    suffix: str    # appended to the file name: "" or "-dark"
    bg: str        # paper
    surface: str   # sunken cells, empty heatmap days
    ink: str       # type and rules
    dim: str       # secondary type; >= 4.5:1 on bg
    hair: str      # hairlines and the visible grid
    acc: str       # the brand red: fills and large type
    acc_text: str  # the red for small type, where the brand red misses 4.5:1
    on_acc: str    # type set on an accent fill (large type only)


# Values from my-portfolio/src/index.css. The portfolio's hairlines are ink at
# 14-18% alpha; they are flattened onto the paper here so lines never stack
# into darker crossings.
LIGHT = Theme("light", "", bg="#F3F2F2", surface="#EAE9E9", ink="#201E1D", dim="#605D5D",
              hair="#D6D4D4", acc="#EC3013", acc_text="#AE1800", on_acc="#F3F2F2")
DARK = Theme("dark", "-dark", bg="#151413", surface="#201E1D", ink="#F3F2F2", dim="#9B9797",
             hair="#3D3C3B", acc="#EC3013", acc_text="#FF5A3D", on_acc="#FFFFFF")
THEMES = (LIGHT, DARK)

# Type at or above this size counts as large (WCAG: 3:1 suffices), so it may
# use the brand red; anything smaller gets acc_text.
LARGE = 24

# 12-column grid on a 1200 canvas: 48 outer margin, 24 gutters, 70 columns.
W = 1200
MARGIN = 48
GUTTER = 24
COL = (W - 2 * MARGIN - 11 * GUTTER) / 12


def col_x(i: float) -> float:
    """Left edge of column i (0-based); col_x(12) is the right margin."""
    if i >= 12:
        return W - MARGIN
    return MARGIN + i * (COL + GUTTER)


def num(v: float) -> str:
    """Compact number for attributes: 12.0 -> '12', 12.5 -> '12.5'."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


# --------------------------------------------------------------------------- type

@lru_cache(maxsize=None)
def _metrics() -> dict:
    """Advance widths per weight, in ems, written by the font subsetting step."""
    try:
        with open(os.path.join(FONT_DIR, "archivo-metrics.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def text_width(s: str, size: float, weight: int = 400, ls: float = 0.0) -> float:
    table = _metrics().get(str(weight)) or _metrics().get("400") or {}
    avg = table.get("_avg", 0.56)
    return sum(table.get(ch, avg) for ch in s) * size + ls * len(s)


def fit(text: str, width: float, size: float, weight: int = 400, ls: float = 0.0) -> str:
    """Truncate with an ellipsis so the text fits in `width` px."""
    if text_width(text, size, weight, ls) <= width:
        return text
    cut = text
    while cut and text_width(cut.rstrip() + "…", size, weight, ls) > width:
        cut = cut[:-1]
    return (cut.rstrip() or text[:1]) + "…"


def wrap(text: str, width: float, size: float, lines: int, weight: int = 400) -> list[str]:
    """Greedy word wrap into at most `lines` rows, ellipsising any overflow."""
    out: list[str] = []
    current = ""
    words = text.split()
    i = 0
    while i < len(words):
        candidate = f"{current} {words[i]}".strip()
        if text_width(candidate, size, weight) <= width:
            current = candidate
            i += 1
            continue
        if not current:  # a single word wider than the line
            current = words[i]
            i += 1
        out.append(current)
        current = ""
        if len(out) == lines:
            break
    if current and len(out) < lines:
        out.append(current)
    if not out:
        return []
    if i < len(words):
        out[-1] = fit(out[-1] + " " + " ".join(words[i:]), width, size, weight)
    return out


@lru_cache(maxsize=None)
def font_faces(weights: tuple[int, ...]) -> str:
    rules = []
    for w in weights:
        path = os.path.join(FONT_DIR, f"archivo-{w}.woff2")
        try:
            with open(path, "rb") as fh:
                data = base64.b64encode(fh.read()).decode("ascii")
        except FileNotFoundError:
            continue
        rules.append(
            f"@font-face {{ font-family:{FAMILY}; font-weight:{w}; font-style:normal; "
            f"src:url(data:font/woff2;base64,{data}) format('woff2'); }}"
        )
    return "\n".join(rules)


# ------------------------------------------------------------------------- motion

MOTION_CSS = f"""
@keyframes d-draw {{ from {{ transform:scaleX(0); }} }}
@keyframes d-reveal {{ from {{ opacity:0; transform:translateY(10px); }} }}
@keyframes d-rise {{ from {{ transform:translateY(115%); }} }}
@keyframes d-fade {{ from {{ opacity:0; }} }}
.draw {{ transform-box:fill-box; transform-origin:0 50%; animation:d-draw .9s {EASE} backwards; }}
.reveal {{ transform-box:fill-box; animation:d-reveal .7s {EASE} backwards; }}
.rise {{ transform-box:fill-box; animation:d-rise .8s {EASE} backwards; }}
.fade {{ animation:d-fade .6s ease-out backwards; }}
"""


def delay(ms: float) -> str:
    return f' style="animation-delay:{num(ms)}ms"' if ms else ""


# --------------------------------------------------------------------- primitives

def text(x: float, y: float, s: str, t: Theme, size: float = 14, weight: int = 400,
         fill: str | None = None, anchor: str = "start", ls: float = 0.0, caps: bool = False,
         cls: str = "", style: str = "", opacity: float | None = None) -> str:
    s = s.upper() if caps else s
    if fill == t.acc and size < LARGE:
        fill = t.acc_text
    parts = [f'<text x="{num(x)}" y="{num(y)}" font-size="{num(size)}"']
    if weight != 400:
        parts.append(f' font-weight="{weight}"')
    if anchor != "start":
        parts.append(f' text-anchor="{anchor}"')
    if ls:
        parts.append(f' letter-spacing="{num(ls)}"')
    parts.append(f' fill="{fill or t.ink}"')
    if opacity is not None:
        parts.append(f' opacity="{num(opacity)}"')
    if cls:
        parts.append(f' class="{cls}"')
    if style:
        parts.append(f' style="{style}"')
    parts.append(f">{escape(s)}</text>")
    return "".join(parts)


def label(x: float, y: float, s: str, t: Theme, fill: str | None = None,
          anchor: str = "start", size: float = 11, cls: str = "", style: str = "") -> str:
    """Small caps label: 11/600, tracked out."""
    return text(x, y, s, t, size=size, weight=600, fill=fill or t.dim, anchor=anchor,
                ls=1.6, caps=True, cls=cls, style=style)


def rule(x: float, y: float, w: float, t: Theme, weight: float = 2, color: str | None = None,
         ms: float | None = 0, cls: str = "") -> str:
    """Horizontal rule. `ms` is the draw-in delay; None draws it static."""
    klass = " ".join(c for c in ("draw" if ms is not None else "", cls) if c)
    k = f' class="{klass}"' if klass else ""
    return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(weight)}" '
            f'fill="{color or t.ink}"{k}{delay(ms or 0)}/>')


def vrule(x: float, y: float, h: float, t: Theme, weight: float = 1, color: str | None = None) -> str:
    return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(weight)}" height="{num(h)}" '
            f'fill="{color or t.hair}"/>')


def grid(h: float, t: Theme, top: float = 0, opacity: float = 0.6) -> str:
    """The visible modular grid: hairlines on every column edge."""
    xs = []
    for i in range(12):
        xs.append(col_x(i))
        xs.append(col_x(i) + COL)
    d = "".join(f"M{num(x)} {num(top)}V{num(h)}" for x in xs)
    return f'<path d="{d}" stroke="{t.hair}" stroke-width="1" opacity="{num(opacity)}"/>'


def box(x: float, y: float, w: float, h: float, title: str, sub: str, t: Theme,
        kind: str = "plain", size: float = 14) -> str:
    """Square node: 2px stroke, zero radius. kind: plain | ink | acc."""
    fill, stroke, fg = {
        "plain": (t.bg, t.ink, t.ink),
        "ink": (t.ink, t.ink, t.bg),
        "acc": (t.acc, t.acc, t.on_acc),
    }[kind]
    cx = x + w / 2
    out = [f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{fill}" '
           f'stroke="{stroke}" stroke-width="2"/>']
    if sub:
        out.append(text(cx, y + h / 2 - 2, fit(title, w - 16, size, 600), t, size=size, weight=600,
                        fill=fg, anchor="middle"))
        out.append(text(cx, y + h / 2 + 15, fit(sub, w - 16, 11), t, size=11,
                        fill=fg if kind != "plain" else t.dim, anchor="middle",
                        opacity=0.78 if kind != "plain" else None))
    else:
        out.append(text(cx, y + h / 2 + size * 0.36, title, t, size=size, weight=600, fill=fg,
                        anchor="middle"))
    return "\n".join(out)


def arrow(d: str, t: Theme, acc: bool = False, dashed: bool = False, head: bool = True) -> str:
    color = t.acc if acc else t.ink
    marker = f' marker-end="url(#{"ah-acc" if acc else "ah"})"' if head else ""
    dash = ' stroke-dasharray="6 6"' if dashed else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="miter"{dash}{marker}/>')


def split_text(x: float, y: float, words: list[tuple[str, str]], size: float, weight: int,
               clip_id: str, ms: float = 0, step: float = 110, ls: float = 0.0) -> str:
    """Display type revealed word by word, each word rising out of a mask.

    `words` is [(word, fill)]; consecutive words are set with a normal space
    unless the word starts with punctuation, which hugs its predecessor.
    """
    space = text_width(" ", size, weight)
    out, cx = [], x
    total = sum(text_width(w, size, weight, ls) for w, _ in words) + space * len(words)
    out.append(f'<clipPath id="{clip_id}"><rect x="{num(x - 4)}" y="{num(y - size * 1.0)}" '
               f'width="{num(total + 8)}" height="{num(size * 1.26)}"/></clipPath>')
    out.append(f'<g clip-path="url(#{clip_id})">')
    for i, (word, fill) in enumerate(words):
        if i and word[:1].isalnum():
            cx += space
        ls_attr = f' letter-spacing="{num(ls)}"' if ls else ""
        out.append(f'<text x="{num(cx)}" y="{num(y)}" font-size="{num(size)}" font-weight="{weight}"'
                   f'{ls_attr} fill="{fill}" class="rise"{delay(ms + i * step)}>{escape(word)}</text>')
        cx += text_width(word, size, weight, ls)
    out.append("</g>")
    return "\n".join(out)


def svg_doc(w: float, h: float, label_text: str, body: str, t: Theme, css: str = "",
            defs: str = "", grid_lines: bool = False, paper: bool = True) -> str:
    """Root element: embedded font, tokens, motion, reduced-motion guard.

    `paper=False` leaves the ground transparent so the asset sits directly on
    GitHub's own page colour (section headers, the stack table).
    """
    weights = tuple(sorted({400} | {int(m) for m in re.findall(r'font-weight="(\d+)"', body)}))
    grid_markup = grid(h, t) if grid_lines else ""
    ground = f'<rect width="{num(w)}" height="{num(h)}" fill="{t.bg}"/>' if paper else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(w)} {num(h)}" width="{num(w)}" height="{num(h)}" fill="none" role="img" aria-label="{attr(label_text)}" font-family="{attr(FONT_STACK)}">
<defs>
<style>
{font_faces(weights)}
text {{ font-family:{FONT_STACK}; font-feature-settings:"tnum" 1, "lnum" 1; }}
{MOTION_CSS}
{css}
@media (prefers-reduced-motion: reduce) {{
  * {{ animation:none !important; }}
}}
</style>
<marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{t.ink}"/></marker>
<marker id="ah-acc" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{t.acc}"/></marker>
{defs}
</defs>
{ground}
{grid_markup}
{body}
</svg>
"""


def write(path: str, svg: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
