#!/usr/bin/env python3
"""Unit tests for the profile card generator.

Run:  python -m unittest discover -s scripts -p "test_*.py" -v
"""

from __future__ import annotations

import random
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import design as d
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
        contributions=66,
        repos=43,
        stars=30,
        languages={"Python": 4_000_000, "Dart": 2_500_000, "TypeScript": 900_000},
        calendar=calendar,
        showcase=[
            g.Repo("S2O-Website", "Academy site", "https://x/1", 4, 1, "TypeScript", "2025-02-22"),
            g.Repo("NOVA-SCIENCE", "Online Learning Platform", "https://x/2", 2, 0, "Dart"),
            g.Repo("LearnWithUsama", "", "https://x/3", 2, 0, "Dart"),
            g.Repo("TalentScout-AI", "Evidence-based recruitment tool", "https://x/4", 1, 0, "Python"),
        ],
    )
    base.update(overrides)
    return g.Stats(**base)


def parse(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def rects(root: ET.Element, **attrs) -> list[ET.Element]:
    return [r for r in root.iter() if r.tag.endswith("rect")
            and all(r.get(k) == v for k, v in attrs.items())]


class TestHuman(unittest.TestCase):
    def test_formats_by_magnitude(self):
        cases = {0: "0", 7: "7", 999: "999", 1000: "1k", 1500: "1.5k",
                 24_000: "24k", 1_000_000: "1M", 1_200_000: "1.2M"}
        for raw, want in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(g.human(raw), want)


class TestCalendarMetrics(unittest.TestCase):
    def test_longest_streak_counts_consecutive_active_days(self):
        cal = [(str(i), c) for i, c in enumerate([1, 1, 0, 2, 3, 4, 0, 1])]
        self.assertEqual(g.longest_streak(cal), 3)
        self.assertEqual(g.active_days(cal), 6)

    def test_empty_calendar(self):
        self.assertEqual(g.longest_streak([]), 0)
        self.assertEqual(g.active_days([]), 0)


class TestPickShowcase(unittest.TestCase):
    repos = [
        g.Repo("MfmRifath", "Config files", "u", 9, 0, "Python"),
        g.Repo("Old-App", "Popular", "u", 5, 0, "Dart"),
        g.Repo("FraudShield", "", "u", 0, 0, "Python"),
        g.Repo("TalentScout-AI", "Real description", "u", 1, 0, "Python"),
    ]

    def test_pinned_wins(self):
        pinned = [self.repos[1]]
        self.assertEqual(g.pick_showcase(pinned, self.repos, "MfmRifath"), (pinned, "PINNED"))

    def test_featured_in_order_with_note_filling_blank_description(self):
        featured = [("talentscout-ai", "ignored note"), ("FraudShield", "fraud note"), ("Gone", "x")]
        chosen, source = g.pick_showcase([], self.repos, "MfmRifath", featured)
        self.assertEqual(source, "FEATURED")
        self.assertEqual([r.name for r in chosen], ["TalentScout-AI", "FraudShield"])
        self.assertEqual(chosen[0].description, "Real description")
        self.assertEqual(chosen[1].description, "fraud note")
        self.assertEqual(self.repos[2].description, "", "must not mutate the source repo")

    def test_falls_back_to_most_starred_without_profile_repo(self):
        chosen, source = g.pick_showcase([], self.repos, "MfmRifath", [("Gone", "")])
        self.assertEqual(source, "MOST STARRED")
        self.assertEqual(chosen[0].name, "Old-App")
        self.assertNotIn("MfmRifath", [r.name for r in chosen])


class TestLanguages(unittest.TestCase):
    def test_excluded_language_absent_from_card(self):
        self.assertIn("Jupyter Notebook",
                      g.render_languages(sample_stats(languages={"Python": 10, "Jupyter Notebook": 90})))
        self.assertNotIn("Jupyter Notebook",
                         g.render_languages(sample_stats(languages={"Python": 10})))

    def test_percentages_total_one_hundred(self):
        svg = g.render_languages(sample_stats(languages={"A": 1, "B": 1, "C": 2}))
        pcts = [float(p) for p in re.findall(r">(\d+\.\d)%<", svg)]
        self.assertAlmostEqual(sum(pcts), 100.0, places=1)

    def test_top_language_carries_the_accent(self):
        for t in d.THEMES:
            svg = g.render_languages(sample_stats(), t)
            first_bar = rects(parse(svg), y="72")[0]
            self.assertEqual(first_bar.get("fill"), t.acc)

    def test_empty_language_data_does_not_crash(self):
        svg = g.render_languages(sample_stats(languages={}))
        parse(svg)
        self.assertIn("No language data", svg)


class TestCards(unittest.TestCase):
    def setUp(self):
        self.stats = sample_stats()

    def test_every_card_in_every_theme_is_well_formed_and_labelled(self):
        for name, render in g.RENDERERS:
            for t in d.THEMES:
                with self.subTest(card=name, theme=t.name):
                    svg = render(self.stats, t)
                    root = parse(svg)
                    self.assertTrue(root.get("viewBox"))
                    self.assertEqual(root.get("role"), "img")
                    self.assertTrue(root.get("aria-label"))
                    self.assertIn("prefers-reduced-motion", svg)
                    self.assertIn(t.bg, svg)

    def test_heatmap_keeps_per_cell_intensity(self):
        """Regression: the intensity ramp once collapsed to one opacity."""
        cells = rects(parse(g.render_activity(self.stats)), width=str(g.ACT_CELL))
        self.assertGreater(len({(c.get("fill"), c.get("opacity")) for c in cells}), 3)

    def test_heatmap_fits_inside_card(self):
        """Regression: seven rows ran past the card, clipping Saturday and
        drawing cells over the legend."""
        root = parse(g.render_activity(self.stats))
        _, _, w, h = map(float, root.get("viewBox").split())
        cells = rects(root, width=str(g.ACT_CELL))
        self.assertTrue(cells)
        self.assertLessEqual(max(float(r.get("y")) for r in cells) + g.ACT_CELL, h - 40)
        self.assertLessEqual(max(float(r.get("x")) for r in cells) + g.ACT_CELL, w - d.MARGIN,
                             "grid must stop at the right margin")
        self.assertGreaterEqual(min(float(r.get("x")) for r in cells), d.MARGIN + 36,
                                "weekday labels need room left of the grid")

    def test_heatmap_places_days_by_weekday(self):
        start = date(2026, 1, 7)  # a Wednesday
        cal = [((start + timedelta(days=i)).isoformat(), 1) for i in range(10)]
        cells = rects(parse(g.render_activity(sample_stats(calendar=cal))), width=str(g.ACT_CELL))
        self.assertEqual(float(cells[0].get("y")), g.ACT_TOP + 3 * g.ACT_STEP,
                         "Wednesday belongs on row 3")

    def test_heatmap_never_exceeds_53_columns(self):
        start = date(2025, 10, 22)  # a Wednesday: 371 days span 54 calendar weeks
        cal = [((start + timedelta(days=i)).isoformat(), 1) for i in range(371)]
        cells = rects(parse(g.render_activity(sample_stats(calendar=cal))), width=str(g.ACT_CELL))
        self.assertEqual(len({c.get("x") for c in cells}), 53)

    def test_repo_footer_clears_rows(self):
        """Regression: the footer baseline once sat inside the bottom row."""
        root = parse(g.render_repos(self.stats))
        bottom = max(float(r.get("y")) for r in root.iter()
                     if r.tag.endswith("rect") and "rowrule" in (r.get("class") or ""))
        footer = [e for e in root.iter() if e.tag.endswith("text")
                  and (e.text or "").startswith("SHOWCASE")]
        self.assertGreater(float(footer[0].get("y")) - 11, bottom)

    def test_repo_descriptions_stay_inside_their_column(self):
        long = g.Repo("x", "word " * 80, "u", 0, 0, "Go")
        svg = g.render_repos(sample_stats(showcase=[long]))
        lines = [e.text for e in parse(svg).iter() if e.tag.endswith("text") and (e.text or "").startswith("word")]
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("…"))
        width = d.col_x(9) - d.col_x(1) - d.GUTTER
        for line in lines:
            self.assertLessEqual(d.text_width(line, 15), width + 0.5)

    def test_stats_card_shows_calendar_metrics(self):
        svg = g.render_stats(self.stats)
        self.assertIn("ACTIVE DAYS", svg)
        self.assertIn(f">{g.longest_streak(self.stats.calendar)}d<", svg)

    def test_counts_are_pluralised(self):
        self.assertEqual(g.plural(1, "star"), "1 star")
        self.assertEqual(g.plural(0, "star"), "0 stars")
        one = g.Repo("x", "d", "u", 1, 0, "Go")
        self.assertIn("1 STAR  ·  0 FORKS", g.render_repos(sample_stats(showcase=[one])))

    def test_repo_card_survives_missing_description(self):
        self.assertIn("No description.", g.render_repos(self.stats))

    def test_showcase_label_reports_actual_source(self):
        """Regression: a fallback list once still claimed PINNED."""
        self.assertIn("SHOWCASE — PINNED", g.render_repos(sample_stats(showcase_source="PINNED")))
        fallback = g.render_repos(sample_stats(showcase_source="MOST STARRED"))
        self.assertIn("SHOWCASE — MOST STARRED", fallback)
        self.assertNotIn("PINNED", fallback)

    def test_repo_card_escapes_hostile_metadata(self):
        nasty = g.Repo('a<b&c"d', "</text><script>x</script>", "https://x", 1, 0, "Go")
        svg = g.render_repos(sample_stats(showcase=[nasty]))
        parse(svg)
        self.assertNotIn("<script>", svg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
