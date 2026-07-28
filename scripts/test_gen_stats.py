#!/usr/bin/env python3
"""Unit tests for the profile card generator.

Run:  python -m unittest discover -s scripts -p "test_*.py" -v
"""

from __future__ import annotations

import random
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import gen_stats as g


def sample_stats(**overrides) -> g.Stats:
    random.seed(11)
    start = date.today() - timedelta(days=52 * 7 + 6)
    calendar = [
        ((start + timedelta(days=i)).isoformat(), random.choice([0, 0, 1, 3, 8, 21]))
        for i in range(53 * 7)
    ]
    base = dict(
        login="MfmRifath",
        name="Rifath MFM",
        followers=8,
        commits=58,
        prs=1,
        issues=0,
        contributions=66,
        repos=43,
        stars=30,
        languages={"Python": 4_000_000, "Dart": 2_500_000, "TypeScript": 900_000},
        calendar=calendar,
        showcase=[
            g.Repo("S2O-Website", "Academy site", "https://x/1", 4, 1, "TypeScript"),
            g.Repo("NOVA-SCIENCE", "Online Learning Platform", "https://x/2", 2, 0, "Dart"),
            g.Repo("LearnWithUsama", "", "https://x/3", 2, 0, "Dart"),
            g.Repo("TalentScout-AI", "Evidence-based recruitment tool", "https://x/4", 1, 0, "Python"),
        ],
    )
    base.update(overrides)
    return g.Stats(**base)


class TestHuman(unittest.TestCase):
    def test_formats_by_magnitude(self):
        cases = {0: "0", 7: "7", 999: "999", 1000: "1k", 1500: "1.5k",
                 24_000: "24k", 1_000_000: "1M", 1_200_000: "1.2M"}
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(g.human(raw), want)


class TestFit(unittest.TestCase):
    def test_short_text_untouched(self):
        self.assertEqual(g.fit("Dart", 200, 12), "Dart")

    def test_long_text_ellipsised_and_bounded(self):
        out = g.fit("x" * 300, 120, 12)
        self.assertTrue(out.endswith("…"))
        self.assertLessEqual(len(out), int(120 / (12 * g.CHAR_W)))

    def test_never_returns_empty_for_narrow_width(self):
        self.assertTrue(g.fit("something", 1, 12))


class TestWrap(unittest.TestCase):
    def test_respects_line_budget(self):
        self.assertLessEqual(len(g.wrap("word " * 200, 300, 11.5, 2)), 2)

    def test_empty_input_yields_no_lines(self):
        self.assertEqual(g.wrap("", 300, 11.5, 2), [])

    def test_keeps_short_description_on_one_line(self):
        self.assertEqual(g.wrap("Online Learning Platform", 400, 11.5, 2),
                         ["Online Learning Platform"])


class TestExcludeLanguages(unittest.TestCase):
    """collect() filters by name while accumulating, so exclusion must remove
    the language from the breakdown without disturbing star totals."""

    def test_excluded_language_absent_from_card(self):
        stats = sample_stats(languages={"Python": 10, "Jupyter Notebook": 90})
        svg = g.render_languages(stats)
        self.assertIn("Python", svg)
        self.assertIn("Jupyter Notebook", svg)

        filtered = sample_stats(languages={"Python": 10})
        self.assertNotIn("Jupyter Notebook", g.render_languages(filtered))

    def test_percentages_total_one_hundred(self):
        stats = sample_stats(languages={"A": 1, "B": 1, "C": 2})
        svg = g.render_languages(stats)
        pcts = [float(t.rstrip("%")) for t in
                __import__("re").findall(r">(\d+\.\d)%<", svg)]
        self.assertAlmostEqual(sum(pcts), 100.0, places=1)


class TestRenderersProduceValidSvg(unittest.TestCase):
    def setUp(self):
        self.stats = sample_stats()

    def _parse(self, svg: str) -> ET.Element:
        try:
            return ET.fromstring(svg)
        except ET.ParseError as exc:
            self.fail(f"not well-formed XML: {exc}")

    def test_every_card_is_well_formed(self):
        for name, svg in (
            ("stats", g.render_stats(self.stats)),
            ("languages", g.render_languages(self.stats)),
            ("repos", g.render_repos(self.stats)),
            ("activity", g.render_activity(self.stats)),
            ("tagline", g.render_tagline()),
        ):
            with self.subTest(card=name):
                root = self._parse(svg)
                self.assertTrue(root.get("viewBox"))
                self.assertEqual(root.get("role"), "img")
                self.assertTrue(root.get("aria-label"), "needs a label for screen readers")

    def test_every_card_guards_reduced_motion(self):
        for name, svg in (
            ("stats", g.render_stats(self.stats)),
            ("repos", g.render_repos(self.stats)),
            ("activity", g.render_activity(self.stats)),
            ("tagline", g.render_tagline()),
        ):
            with self.subTest(card=name):
                self.assertIn("prefers-reduced-motion", svg)

    def test_heatmap_keeps_per_cell_opacity(self):
        """Regression: animating to `opacity:inherit` resolved against the parent
        and flattened every intensity band to full opacity."""
        svg = g.render_activity(self.stats)
        self.assertNotIn("opacity:inherit", svg)
        opacities = {r.get("opacity") for r in self._parse(svg).iter()
                     if r.tag.endswith("rect") and r.get("opacity")}
        self.assertGreater(len(opacities), 2, "intensity ramp collapsed")

    def test_empty_language_data_does_not_crash(self):
        svg = g.render_languages(sample_stats(languages={}))
        self._parse(svg)
        self.assertIn("no language data", svg)

    def test_repo_card_survives_missing_description(self):
        svg = g.render_repos(sample_stats())
        self.assertIn("No description.", svg)

    def test_showcase_label_reports_actual_source(self):
        """Regression: the label was derived from `len(showcase) <= 4`, which is
        always true after slicing, so a fallback list still claimed PINNED."""
        pinned = sample_stats(showcase_source="PINNED")
        self.assertIn("// PINNED", g.render_repos(pinned))

        fallback = sample_stats(showcase_source="MOST STARRED")
        rendered = g.render_repos(fallback)
        self.assertIn("// MOST STARRED", rendered)
        self.assertNotIn("// PINNED", rendered)

    def test_repo_card_escapes_hostile_metadata(self):
        nasty = g.Repo('a<b&c"d', "</text><script>x</script>", "https://x", 1, 0, "Go")
        svg = g.render_repos(sample_stats(showcase=[nasty]))
        self._parse(svg)
        self.assertNotIn("<script>", svg)


class TestTagline(unittest.TestCase):
    def test_generates_one_cycle_per_line(self):
        svg = g.render_tagline(["alpha", "beta"])
        for i in range(2):
            self.assertIn(f"@keyframes show{i}", svg)
            self.assertIn(f"@keyframes type{i}", svg)
        self.assertNotIn("show2", svg)

    def test_keyframe_percentages_stay_in_range(self):
        import re
        svg = g.render_tagline(["one", "two", "three"])
        for pct in re.findall(r"(\d+\.\d+)%", svg):
            self.assertLessEqual(float(pct), 100.0)
            self.assertGreaterEqual(float(pct), 0.0)

    def test_escapes_markup_in_lines(self):
        svg = g.render_tagline(["<b>bold</b> & co"])
        ET.fromstring(svg)
        self.assertNotIn("<b>bold</b>", svg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
