#!/usr/bin/env python3
"""Tests for the shared design system and the static asset builder.

Run:  python -m unittest discover -s scripts -p "test_*.py" -v
"""

from __future__ import annotations

import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

import build_assets as b
import design as d
import gen_stats as g
from test_gen_stats import sample_stats

FIELDS = ("bg", "surface", "ink", "dim", "hair", "acc", "acc_text", "on_acc")


def every_svg() -> list[tuple[str, str, str]]:
    """(name, light svg, dark svg) for every static asset and generated card."""
    stats = sample_stats()
    jobs = [("hero", b.render_hero), ("marquee", b.render_marquee), ("stack", b.render_stack),
            ("contact", b.render_contact), ("tuition", b.render_tuition),
            ("fraudshield", b.render_fraudshield),
            ("section", lambda t: b.render_section(3, "FraudShield", "caption", t))]
    jobs += [(name, lambda t, r=render: r(stats, t)) for name, render in g.RENDERERS]
    return [(name, fn(d.LIGHT), fn(d.DARK)) for name, fn in jobs]


def luminance(hex_color: str) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g_, b_ = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g_) + 0.0722 * channel(b_)


def contrast(a: str, b_: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b_)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class TestTokens(unittest.TestCase):
    def test_small_text_is_readable_in_both_themes(self):
        for t in d.THEMES:
            with self.subTest(theme=t.name):
                self.assertGreaterEqual(contrast(t.ink, t.bg), 7)
                self.assertGreaterEqual(contrast(t.dim, t.bg), 4.5)
                self.assertGreaterEqual(contrast(t.acc_text, t.bg), 4.5)
                # Brand red and type on it are reserved for large type (3:1).
                self.assertGreaterEqual(contrast(t.acc, t.bg), 3)
                self.assertGreaterEqual(contrast(t.on_acc, t.acc), 3)

    def test_small_accent_text_uses_the_readable_red(self):
        for t in d.THEMES:
            self.assertIn(f'fill="{t.acc_text}"', d.label(0, 0, "01", t, fill=t.acc))
            self.assertIn(f'fill="{t.acc}"', d.text(0, 0, "6.6 ms", t, size=36, fill=t.acc))

    def test_dark_values_are_unique(self):
        """The palette-swap test below needs an unambiguous dark -> light map."""
        values = [getattr(d.DARK, f) for f in FIELDS]
        self.assertEqual(len(values), len(set(values)))

    def test_grid_columns_span_the_canvas(self):
        self.assertEqual(d.col_x(0), d.MARGIN)
        self.assertAlmostEqual(d.col_x(11) + d.COL, d.W - d.MARGIN)


class TestMeasure(unittest.TestCase):
    def test_metrics_are_present(self):
        self.assertTrue(d._metrics(), "assets/fonts/archivo-metrics.json is missing")
        self.assertLess(d.text_width("iiii", 20), d.text_width("WWWW", 20),
                        "a proportional font should measure i narrower than W")

    def test_bold_is_wider(self):
        self.assertGreater(d.text_width("Rifath", 40, 800), d.text_width("Rifath", 40, 400))

    def test_fit_short_text_untouched(self):
        self.assertEqual(d.fit("Dart", 200, 12), "Dart")

    def test_fit_long_text_ellipsised_and_bounded(self):
        out = d.fit("x" * 300, 120, 12)
        self.assertTrue(out.endswith("…"))
        self.assertLessEqual(d.text_width(out, 12), 120)

    def test_fit_never_returns_empty(self):
        self.assertTrue(d.fit("something", 1, 12))

    def test_wrap_respects_budget_and_width(self):
        lines = d.wrap("word " * 200, 300, 14, 2)
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertLessEqual(d.text_width(line, 14), 300)

    def test_wrap_empty_and_short(self):
        self.assertEqual(d.wrap("", 300, 14, 2), [])
        self.assertEqual(d.wrap("Online Learning Platform", 400, 14, 2), ["Online Learning Platform"])

    def test_wrap_overlong_single_word_is_kept(self):
        self.assertEqual(len(d.wrap("x" * 200, 50, 14, 2)), 1)


class TestEverySvg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svgs = every_svg()

    def test_well_formed_labelled_and_motion_safe(self):
        for name, light, dark in self.svgs:
            for svg in (light, dark):
                with self.subTest(asset=name):
                    root = ET.fromstring(svg)
                    self.assertEqual(root.get("role"), "img")
                    self.assertTrue(root.get("aria-label"))
                    self.assertIn("prefers-reduced-motion", svg)

    def test_font_is_embedded(self):
        for name, light, _ in self.svgs:
            with self.subTest(asset=name):
                self.assertIn("data:font/woff2;base64,", light)

    def test_only_used_weights_are_embedded(self):
        _, marquee, _ = next(s for s in self.svgs if s[0] == "marquee")
        self.assertEqual(marquee.count("@font-face"), 2)  # 400 baseline + 600

    def test_no_external_requests(self):
        for name, light, dark in self.svgs:
            for svg in (light, dark):
                with self.subTest(asset=name):
                    urls = re.findall(r"https?://[^\s\"')]+", svg)
                    self.assertEqual(set(urls), {"http://www.w3.org/2000/svg"})
                    for ref in re.findall(r"url\(([^)]*)\)", svg):
                        self.assertTrue(ref.startswith(("#", "data:")), ref)

    def test_themes_differ_only_in_palette(self):
        for name, light, dark in self.svgs:
            with self.subTest(asset=name):
                to_light = {getattr(d.DARK, f): getattr(d.LIGHT, f) for f in FIELDS}
                pattern = re.compile("|".join(map(re.escape, to_light)))
                swapped = pattern.sub(lambda m: to_light[m.group(0)], dark)
                self.assertEqual(swapped, light)

    def test_tick_and_flash_rest_invisible(self):
        """Looping effects must vanish when motion is off, not freeze mid-flight."""
        for name, light, _ in self.svgs:
            for el in ET.fromstring(light).iter():
                cls = el.get("class") or ""
                if {"tick", "flash", "dcycle"} & set(cls.split()):
                    with self.subTest(asset=name, cls=cls):
                        self.assertEqual(el.get("opacity"), "0")


class TestMarquee(unittest.TestCase):
    def test_carries_every_line_and_escapes_markup(self):
        svg = b.render_marquee(d.LIGHT, ["alpha", "<b>bold</b> & co"])
        ET.fromstring(svg)
        self.assertIn("ALPHA", svg)
        self.assertNotIn("<B>", svg)

    def test_band_is_seamless(self):
        """Two identical strips, the second starting exactly one shift along,
        and the first strip covering the whole band."""
        svg = b.render_marquee(d.LIGHT, ["one", "two"])
        texts = [e for e in ET.fromstring(svg).iter() if e.tag.endswith("text")]
        half = len(texts) // 2
        self.assertEqual(len(texts), half * 2)
        shift = float(re.search(r"translateX\(-([\d.]+)px\)", svg).group(1))
        self.assertGreaterEqual(shift, 1200)
        for a, b_ in zip(texts[:half], texts[half:]):
            self.assertEqual(a.text, b_.text)
            self.assertAlmostEqual(float(b_.get("x")) - float(a.get("x")), shift, delta=0.02)


class TestBuild(unittest.TestCase):
    def test_build_is_deterministic_and_complete(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            first = b.build(one)
            b.build(two)
            self.assertEqual(len(first), (6 + len(b.SECTIONS)) * 2)
            for path in first:
                twin = os.path.join(two, os.path.basename(path))
                with open(path, "rb") as fa, open(twin, "rb") as fb:
                    self.assertEqual(fa.read(), fb.read(), os.path.basename(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
