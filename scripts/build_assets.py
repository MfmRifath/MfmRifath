#!/usr/bin/env python3
"""Build the profile's static SVGs, each in a light and a dark variant.

Everything here is content that changes by hand, not by data: hero, marquee,
section headers, the two architecture diagrams, the stack table and the contact
block. Data-driven cards live in gen_stats.py. Both share scripts/design.py.

Usage:
    python scripts/build_assets.py [--out assets]
"""

from __future__ import annotations

import argparse
import os

import design as d
from design import Theme, col_x, num
from gen_stats import TAGLINE

# --------------------------------------------------------------------- content

HERO_FOCUS = [
    ("LLM fine-tuning", "QLoRA · Llama 3 · PEFT"),
    ("RAG & agents", "LangGraph · hybrid retrieval"),
    ("Real-time ML", "Kafka · FastAPI · MLflow"),
    ("Final year", "BSc SE · Univ. of Ruhuna"),
]

SECTIONS = [
    ("about", "About", "whoami"),
    ("tuition", "AI Tuition Master", "final-year project · runtime"),
    ("fraudshield", "FraudShield", "real-time ML · score path"),
    ("work", "Selected work", "2024 — 2026"),
    ("stack", "Stack", "tools I ship with"),
    ("activity", "Activity", "rebuilt daily by CI"),
    ("contact", "Contact", "open to work · Nov 2026"),
]

# Bold items are the daily drivers; the rest is range.
STACK = [
    ("AI / ML", ["*Python", "*PyTorch", "*Hugging Face", "*QLoRA / PEFT", "Llama 3", "Hybrid RAG",
                 "LightGBM", "TensorFlow"]),
    ("Agents", ["*LangGraph", "*LangChain", "OpenAI SDK", "Claude API", "AutoGen"]),
    ("Streaming / MLOps", ["*Kafka / Avro", "*Redis", "*MLflow", "Prefect", "Prometheus", "Grafana"]),
    ("Backend", ["*FastAPI", "Django", "Spring Boot", "Node.js", "Java"]),
    ("Data", ["*PostgreSQL", "MySQL", "SQLite", "MongoDB", "Firebase"]),
    ("Mobile / Web", ["*Flutter", "*React", "*TypeScript", "Dart", "Android", "Tailwind",
                      "Shopify / Liquid"]),
    ("Infra", ["*Docker", "*GitHub Actions", "Vercel", "Git", "Linux", "Postman"]),
    ("Security", ["Kali Linux", "TryHackMe", "Wireshark", "Burp Suite"]),
]

EMAIL = "mmfmrifath@gmail.com"


# ------------------------------------------------------------------------ hero

def render_hero(t: Theme) -> str:
    w, h = 1200, 440
    b = []

    b.append(d.label(col_x(0), 52, "AI Engineer", t, fill=t.ink))
    b.append(d.label(col_x(4), 52, "Colombo, LK — UTC+5:30", t))
    b.append(d.label(col_x(8), 52, "Tamil · English · Sinhala", t))
    b.append(d.label(col_x(12), 52, "Profile — 2026", t, anchor="end"))
    b.append(d.rule(col_x(0), 68, col_x(12) - col_x(0), t, ms=0))

    b.append(d.split_text(col_x(0) - 6, 214, [("Rifath", t.ink), ("MFM", t.ink), (".", t.acc)],
                          size=132, weight=800, clip_id="hero-name", ms=200, step=120, ls=-4))

    # Availability block, right-hand columns.
    x = col_x(9) + 30
    b.append(f'<g class="reveal"{d.delay(700)}>')
    b.append(f'<rect x="{num(x)}" y="108" width="12" height="12" fill="{t.acc}"/>')
    b.append(d.label(x + 22, 119, "Open to work", t, fill=t.ink))
    b.append(d.text(x, 146, "AI / ML engineering roles", t, size=15, weight=600))
    b.append(d.text(x, 166, "from November 2026", t, size=15, fill=t.dim))
    b.append("</g>")

    b.append(d.text(col_x(0), 278,
                    "Retrieval-augmented, agentic and real-time ML systems — "
                    "where the data pipeline is the hard part.",
                    t, size=19, fill=t.dim, cls="reveal", style="animation-delay:650ms"))

    b.append(d.rule(col_x(0), 314, col_x(12) - col_x(0), t, ms=500))
    for i, (title, sub) in enumerate(HERO_FOCUS):
        x = col_x(i * 3)
        if i:
            b.append(d.vrule(x - d.GUTTER / 2, 330, 84, t))
        b.append(f'<g class="reveal"{d.delay(800 + i * 90)}>')
        b.append(d.label(x, 346, f"{i + 1:02d}", t, fill=t.acc))
        b.append(d.text(x, 378, title, t, size=21, weight=600))
        b.append(d.text(x, 402, sub, t, size=13, fill=t.dim))
        b.append("</g>")
    b.append(d.rule(col_x(0), 426, col_x(12) - col_x(0), t, weight=1, color=t.hair, ms=None))

    return d.svg_doc(w, h, "Rifath MFM — AI engineer. LLM fine-tuning, RAG and agents, real-time ML. "
                     "Open to AI/ML engineering roles from November 2026.",
                     "\n".join(b), t, grid_lines=True)


# --------------------------------------------------------------------- marquee

def render_marquee(t: Theme, lines: list[str] | None = None) -> str:
    """Accent band scrolling the tagline lines, as on the portfolio."""
    # 19px/800 is "large" type, where white on the brand red clears WCAG's 3:1.
    w, h = 1200, 60
    size, weight, ls = 19, 800, 1.2
    gap, sq = 26, 9  # space either side of the square separator, square size
    lines = [ln.replace(" -- ", " — ").upper() for ln in (lines or TAGLINE)]
    widths = [d.text_width(s, size, weight, ls) for s in lines]
    unit_w = sum(widths) + len(lines) * (2 * gap + sq)
    reps = max(1, int(-(-w // unit_w)))  # enough copies to cover the band
    shift = unit_w * reps
    duration = max(20.0, shift / 50)  # ~50 px/s regardless of copy length

    def strip(x0: float) -> list[str]:
        out, x = [], x0
        for _ in range(reps):
            for s, sw in zip(lines, widths):
                out.append(d.text(x, 38, s, t, size=size, weight=weight, ls=ls, fill=t.on_acc))
                x += sw + gap
                out.append(f'<rect x="{num(x)}" y="{num(h / 2 - sq / 2)}" width="{sq}" height="{sq}" '
                           f'fill="{t.on_acc}"/>')
                x += sq + gap
        return out

    b = [f'<rect width="{w}" height="{h}" fill="{t.acc}"/>', '<g class="marq">']
    b += strip(24)
    b += strip(24 + shift)
    b.append("</g>")
    css = (f"@keyframes marq {{ to {{ transform:translateX(-{num(shift)}px); }} }} "
           f".marq {{ animation:marq {num(duration)}s linear infinite; }}")
    return d.svg_doc(w, h, " · ".join(lines), "\n".join(b), t, css=css)


# --------------------------------------------------------------------- section

def render_section(index: int, title: str, caption: str, t: Theme) -> str:
    w, h = 1200, 96
    b = [
        d.split_text(col_x(0), 58, [(f"{index:02d}", t.acc)], size=40, weight=800,
                     clip_id=f"sec-n{index}", ms=0),
        d.split_text(col_x(1), 58, [(title, t.ink)], size=40, weight=800,
                     clip_id=f"sec-t{index}", ms=90, ls=-0.8),
        d.label(col_x(12), 54, caption, t, anchor="end", cls="fade", style="animation-delay:300ms"),
        d.rule(col_x(0), 78, col_x(12) - col_x(0), t, ms=150),
    ]
    return d.svg_doc(w, h, f"{index:02d} — {title}", "\n".join(b), t, paper=False)


# ----------------------------------------------------------------------- stack

def render_stack(t: Theme) -> str:
    size = 17
    item_x = col_x(3)
    item_w = col_x(12) - item_x
    row_pad, line_h = 22, 28
    b, y = [], 0

    b.append(d.label(col_x(0), 30, "Category", t))
    b.append(d.label(item_x, 30, "Tools — bold: daily drivers", t))
    y = 44
    b.append(d.rule(col_x(0), y, col_x(12) - col_x(0), t, ms=0))
    y += 2

    for i, (cat, items) in enumerate(STACK):
        # Lay items out greedily, measuring each with its own weight.
        rows: list[list[tuple[str, bool]]] = [[]]
        cursor = 0.0
        sep_w = d.text_width("  ·  ", size)
        for raw in items:
            bold = raw.startswith("*")
            name = raw.lstrip("*")
            wdt = d.text_width(name, size, 600 if bold else 400)
            need = wdt + (sep_w if rows[-1] else 0)
            if rows[-1] and cursor + need > item_w:
                rows.append([])
                cursor, need = 0.0, wdt
            rows[-1].append((name, bold))
            cursor += need

        top = y
        block_h = row_pad * 2 + line_h * (len(rows) - 1) + 12
        base = top + row_pad + 13
        b.append(f'<g class="reveal"{d.delay(120 + i * 70)}>')
        b.append(d.label(col_x(0), base - 2, f"{i + 1:02d}", t, fill=t.acc))
        b.append(d.text(col_x(0) + 34, base, cat, t, size=15, weight=600))
        for r, row in enumerate(rows):
            spans = []
            for j, (name, bold) in enumerate(row):
                if j:
                    spans.append(f'<tspan fill="{t.dim}">  ·  </tspan>')
                fill = t.ink if bold else t.dim
                weight = ' font-weight="600"' if bold else ""
                spans.append(f'<tspan fill="{fill}"{weight}>{d.escape(name)}</tspan>')
            b.append(f'<text x="{num(item_x)}" y="{num(base + r * line_h)}" font-size="{size}" '
                     f'xml:space="preserve">{"".join(spans)}</text>')
        b.append("</g>")
        y = top + block_h
        last = i == len(STACK) - 1
        b.append(d.rule(col_x(0), y, col_x(12) - col_x(0), t,
                        weight=2 if last else 1, color=None if last else t.hair,
                        ms=None if not last else 300))
        y += 2

    h = y + 24
    label = "Stack — " + "; ".join(f"{c}: " + ", ".join(i.lstrip("*") for i in items)
                                    for c, items in STACK)
    return d.svg_doc(1200, h, label, "\n".join(b), t, paper=False)


# --------------------------------------------------------------------- contact

def render_contact(t: Theme) -> str:
    w, h = 1200, 300
    b = [
        d.split_text(col_x(0) - 4, 132, [("Let’s", t.ink), ("talk", t.ink), (".", t.acc)],
                     size=104, weight=800, clip_id="talk", ms=0, step=110, ls=-3),
        d.text(col_x(0), 194, EMAIL, t, size=28, weight=600, cls="reveal",
               style="animation-delay:350ms"),
    ]
    x = col_x(8)
    b.append(f'<g class="reveal"{d.delay(500)}>')
    b.append(f'<rect x="{num(x)}" y="62" width="12" height="12" fill="{t.acc}"/>')
    b.append(d.label(x + 22, 73, "Available", t, fill=t.ink))
    b.append(d.text(x, 104, "AI / ML engineering roles", t, size=17, weight=600))
    b.append(d.text(x, 128, "From November 2026", t, size=15, fill=t.dim))
    b.append(d.text(x, 150, "Colombo · remote-friendly · UTC+5:30", t, size=15, fill=t.dim))
    b.append("</g>")
    b.append(d.rule(col_x(0), 228, col_x(12) - col_x(0), t, ms=250))
    b.append(d.text(col_x(0), 262,
                    "If the retrieval layer is the hard part, I want to hear about it.",
                    t, size=15, fill=t.dim, cls="fade", style="animation-delay:600ms"))
    b.append(d.label(col_x(12), 262, "Rifath MFM — 2026", t, anchor="end"))
    return d.svg_doc(w, h, f"Let's talk. {EMAIL}. Open to AI/ML engineering roles from November 2026.",
                     "\n".join(b), t, grid_lines=True)


# -------------------------------------------------------------------- diagrams

FLASH_CSS = (
    "@keyframes flash { 0% { opacity:0; } 3% { opacity:1; } 14% { opacity:0; } 100% { opacity:0; } } "
    "@keyframes tick { 0% { offset-distance:0%; opacity:0; } 3% { opacity:1; } "
    "45% { offset-distance:100%; opacity:1; } 48%,100% { offset-distance:100%; opacity:0; } } "
    ".flash { animation:flash var(--dur) linear infinite; } "
    ".tick { offset-rotate:0deg; animation:tick var(--dur) linear infinite; }"
)


def flash(x: float, y: float, w: float, h: float, t: Theme, at: float, dur: float) -> str:
    """Accent frame that lights up as the tick passes. Rests invisible."""
    return (f'<rect x="{num(x - 3)}" y="{num(y - 3)}" width="{num(w + 6)}" height="{num(h + 6)}" '
            f'fill="none" stroke="{t.acc}" stroke-width="4" opacity="0" class="flash" '
            f'style="--dur:{num(dur)}s;animation-delay:{num(at)}s"/>')


def tick_at(x: float, start: float, end: float, dur: float) -> float:
    """Seconds into the cycle at which the tick passes x on a horizontal run.
    The tick covers its path in the first 45% of the cycle (see FLASH_CSS)."""
    return (x - start) / (end - start) * dur * 0.45


def tick(path: str, t: Theme, dur: float, at: float = 0) -> str:
    return (f'<rect x="-5" y="-5" width="10" height="10" fill="{t.acc}" opacity="0" class="tick" '
            f"style=\"--dur:{num(dur)}s;offset-path:path('{path}');animation-delay:{num(at)}s\"/>")


def render_tuition(t: Theme) -> str:
    w, h = 1200, 520
    y0, bh = 202, 56          # main row
    cy = y0 + bh / 2
    dur = 6.0                  # one pass of the tick along the main row
    span_start, span_end = 118, 1082

    def at(x: float) -> float:
        return tick_at(x, span_start, span_end, dur)

    b = [d.label(col_x(0), 40, "Runtime — grounded retrieval · fine-tuned generation · "
                 "adaptive sequencing", t)]

    tools = [(140, "Retriever", "hybrid BM25 + dense"),
             (230, "Solver agent", "step decomposition"),
             (320, "Multimodal", "physics figure retrieval")]

    # Connectors first so boxes sit on top of them.
    b.append(d.arrow(f"M188 {num(cy)}H226", t, acc=True))
    b.append(d.arrow(f"M368 {num(cy)}H416", t, acc=True))
    b.append(d.arrow(f"M392 {num(cy)}V140H416", t))
    b.append(d.arrow(f"M392 {num(cy)}V320H416", t))
    b.append(d.arrow(f"M598 {num(cy)}H646", t, acc=True))
    b.append(d.arrow("M598 140H622V222", t, head=False))
    b.append(d.arrow("M598 320H622V238", t, head=False))
    b.append(d.arrow(f"M788 {num(cy)}H826", t, acc=True))
    b.append(d.arrow(f"M968 {num(cy)}H1010", t, acc=True))
    b.append(d.arrow("M508 400V350", t))                          # vector store -> multimodal
    b.append(d.arrow(f"M1082 {num(y0 + bh)}V398", t))             # answer -> BKT
    b.append(d.arrow(f"M828 425H808V480H118V{num(y0 + bh + 4)}", t, dashed=True))
    b.append(d.label(128, 472, "Feedback loop — next question from live mastery", t))

    b.append(d.box(48, y0, 140, bh, "Student", "Tamil / English", t))
    b.append(d.box(228, y0, 140, bh, "LangGraph", "router", t, kind="ink"))
    for y, title, sub in tools:
        b.append(d.box(418, y - bh / 2, 180, bh, title, sub, t))
    b.append(d.box(648, y0, 140, bh, "Llama 3", "QLoRA fine-tune", t, kind="acc"))
    b.append(d.box(828, y0, 140, bh, "Groundedness", "+ citation check", t))
    b.append(d.box(1012, y0, 140, bh, "Answer", "or refuse / re-retrieve", t))
    b.append(d.box(418, 400, 180, 50, "Vector store", "Tamil physics corpus", t))
    b.append(d.box(828, 400, 324, 50, "Bayesian Knowledge Tracing", "mastery estimate → next question", t))

    for x, bw in ((48, 140), (228, 140), (648, 140), (828, 140), (1012, 140)):
        b.append(flash(x, y0, bw, bh, t, at(x + bw / 2), dur))
    b.append(flash(418, 230 - bh / 2, 180, bh, t, at(508), dur))
    b.append(tick(f"M118 {num(cy)}H1082", t, dur))

    b.append(d.rule(col_x(0), 500, col_x(12) - col_x(0), t, ms=None))
    return d.svg_doc(w, h, "AI Tuition Master architecture: student to LangGraph router; retriever, "
                     "solver agent and multimodal tools; QLoRA-tuned Llama 3; groundedness check; "
                     "answer; Bayesian knowledge tracing feeds the next question back to the student.",
                     "\n".join(b), t, css=FLASH_CSS, grid_lines=True)


def render_fraudshield(t: Theme) -> str:
    w, h = 1200, 540
    dur = 5.0
    b = []

    # Lanes.
    lanes = [(84, "01 Serve"), (226, "02 Stream"), (352, "03 Learn")]
    for y, name in lanes:
        b.append(d.label(48, y, name, t, fill=t.acc))
    b.append(d.rule(48, 210, 794, t, weight=1, color=t.hair, ms=None))
    b.append(d.rule(48, 336, 794, t, weight=1, color=t.hair, ms=None))

    # Connectors.
    b.append(d.arrow("M188 148H226", t, acc=True))
    b.append(d.arrow("M628 148H666", t, acc=True))
    b.append(d.arrow("M744 176V258", t))
    b.append(d.arrow("M668 286H522", t))
    b.append(d.label(595, 276, "stream processor", t, anchor="middle", size=10))
    b.append(d.arrow("M428 260V200", t))
    b.append(d.text(440, 238, "pipelined fetch · 10 ms budget", t, size=11, fill=t.dim))
    b.append(d.arrow("M744 312V378", t))
    b.append(d.arrow("M668 406H622", t))
    b.append(d.arrow("M418 406H392", t))
    b.append(d.arrow("M228 406H208V174H226", t, acc=True))
    b.append(f'<text transform="translate(200 290) rotate(-90)" text-anchor="middle" font-size="10" '
             f'font-weight="600" letter-spacing="1.6" fill="{t.acc}">HOT RELOAD</text>')

    # Serve row.
    b.append(d.box(48, 120, 140, 56, "Transaction", "card event", t))
    b.append(f'<rect x="228" y="100" width="400" height="96" fill="{t.bg}" stroke="{t.ink}" stroke-width="2"/>')
    b.append(d.text(244, 124, "FastAPI  /score", t, size=15, weight=600))
    b.append(d.label(612, 123, "LightGBM 500 × 63", t, anchor="end", size=10))
    b.append(d.rule(228, 136, 400, t, weight=1, color=t.hair, ms=None))
    stages = ["rules", "LightGBM", "calibrate", "cost policy"]
    for i, s in enumerate(stages):
        x = 228 + i * 100
        if i:
            b.append(d.vrule(x, 136, 60, t))
        b.append(d.text(x + 50, 172, s, t, size=13, anchor="middle"))
        b.append(d.label(x + 50, 154, f"{i + 1:02d}", t, anchor="middle", size=9, fill=t.acc))

    # Decision: cycles while animated, shows all three at rest.
    b.append(f'<rect x="668" y="120" width="152" height="56" fill="{t.bg}" stroke="{t.ink}" stroke-width="2"/>')
    b.append(d.text(744, 145, "Approve · Review · Block", t, size=11, weight=600, anchor="middle",
                    cls="dstatic"))
    states = [("Approve", t.bg, t.ink, t.ink), ("Review", t.ink, t.ink, t.bg), ("Block", t.acc, t.acc, t.on_acc)]
    for i, (word, fill, stroke, fg) in enumerate(states):
        b.append(f'<g class="dcycle" opacity="0" style="animation-delay:{num(i * 3 - 9 + 1.6)}s">'
                 f'<rect x="668" y="120" width="152" height="56" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                 + d.text(744, 147, word.upper(), t, size=16, weight=800, anchor="middle", ls=1.5, fill=fg)
                 + "</g>")
    b.append(d.text(744, 165, "+ 3 reason codes", t, size=11, fill=t.dim, anchor="middle"))

    # Stream + learn rows.
    b.append(d.box(338, 260, 180, 52, "Redis", "online features", t))
    b.append(d.box(668, 260, 152, 52, "Redpanda", "tx · decisions · labels", t))
    b.append(d.box(668, 380, 152, 52, "Drift job", "Evidently · PSI", t))
    b.append(d.box(420, 380, 200, 52, "Retrain → gate", "+ analyst labels · Prefect", t))
    b.append(d.box(228, 380, 162, 52, "MLflow", "champion / challenger", t, kind="acc"))

    b.append(flash(48, 120, 140, 56, t, tick_at(118, 118, 744, dur), dur))
    b.append(flash(228, 100, 400, 96, t, tick_at(428, 118, 744, dur), dur))
    b.append(flash(668, 120, 152, 56, t, tick_at(744, 118, 744, dur) - 0.1, dur))
    b.append(tick("M118 148H744", t, dur))

    # Measured column.
    mx, mw = col_x(9), col_x(12) - col_x(9)
    b.append(d.vrule(mx - d.GUTTER, 70, 400, t))
    b.append(d.label(mx, 84, "Measured — reports/", t, fill=t.ink))
    b.append(d.rule(mx, 96, mw, t, ms=200))
    measured = [("6.6 ms", "p95 single-request scoring"),
                ("100.6 req/s", "load test · 0 failed · p95 14 ms"),
                ("0 failed", "Redis killed mid-load · back in 2 s"),
                ("199 MiB", "one-container demo at 50 tx/s")]
    for i, (value, caption) in enumerate(measured):
        y = 98 + i * 92
        b.append(f'<g class="reveal"{d.delay(300 + i * 90)}>')
        b.append(d.text(mx, y + 48, value, t, size=36, weight=800, ls=-0.8,
                        fill=t.acc if i == 0 else t.ink))
        b.append(d.text(mx, y + 72, caption, t, size=13, fill=t.dim))
        b.append("</g>")
        b.append(d.rule(mx, y + 90, mw, t, weight=1, color=t.hair, ms=None))

    b.append(d.rule(col_x(0), 474, col_x(12) - col_x(0), t, ms=None))
    b.append(d.text(col_x(0), 502, "Model quality is pending the real-data training run. Serving numbers "
                    "use a production-size synthetic model; every figure is written by a make target.",
                    t, size=12.5, fill=t.dim))

    css = FLASH_CSS + (
        " @keyframes dcy { 0% { opacity:0; } 1.5% { opacity:1; } 31% { opacity:1; } 33.3%,100% { opacity:0; } }"
        " @keyframes hide { from, to { opacity:0; } }"
        " .dcycle { animation:dcy 9s linear infinite; }"
        " .dstatic { animation:hide 1s linear infinite; }"
    )
    return d.svg_doc(w, h, "FraudShield architecture: transactions scored by FastAPI (rules, LightGBM, "
                     "calibration, cost policy) into approve, review or block with three reason codes; "
                     "decisions stream through Redpanda into Redis online features; a drift job triggers "
                     "retraining behind a promotion gate and an MLflow champion/challenger hot reload. "
                     "Measured: 6.6 ms p95 scoring; 100.6 req/s with 0 failures; 0 failures with Redis "
                     "killed; 199 MiB demo container.", "\n".join(b), t, css=css, grid_lines=True)


# ------------------------------------------------------------------------ main

def build(out: str) -> list[str]:
    jobs = [("hero", render_hero), ("marquee", render_marquee), ("stack", render_stack),
            ("contact", render_contact), ("tuition-master", render_tuition),
            ("fraudshield", render_fraudshield)]
    for i, (slug, title, caption) in enumerate(SECTIONS, start=1):
        jobs.append((f"section-{i:02d}-{slug}",
                     lambda t, i=i, title=title, caption=caption: render_section(i, title, caption, t)))
    written = []
    for name, fn in jobs:
        for t in d.THEMES:
            path = os.path.join(out, f"{name}{t.suffix}.svg")
            d.write(path, fn(t))
            written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=os.path.join(d.ROOT, "assets"))
    args = parser.parse_args()
    for path in build(args.out):
        print(f"wrote {os.path.relpath(path, d.ROOT)}  ({os.path.getsize(path) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
