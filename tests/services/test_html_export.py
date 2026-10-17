import datetime
import tempfile
import unittest
from pathlib import Path

from app.model.member_list import MemberList
from app.model.race_day import RaceDay
from app.model.results import CURRENT, FINAL, CompetitorResult, Results
from app.model.sailor import Sailor
from app.services.html_export import (
    export_race_day_html,
    export_results_html,
    race_day_filename,
    race_day_html,
    results_html,
)

MEMBERS = MemberList([Sailor("   03", "DF95", "Rosie", "Keel", "RMBC")])
PAGE = dict(club_title="RMBC <club>", competition_title="DF95 2026", members=MEMBERS,
            classes=["DF95"], clubs=["RMBC"], generated=datetime.datetime(2026, 10, 16, 19, 45))


def day(name: str, rows) -> RaceDay:
    return RaceDay.from_table(name, ["Race A", "Race B"], rows)


class HtmlExportTests(unittest.TestCase):
    def test_filename(self):
        self.assertEqual(race_day_filename("Race day 1"), "Race_day_1.html")
        self.assertEqual(race_day_filename("Df95_10-10-2026"), "Df95_10-10-2026.html")
        self.assertEqual(race_day_filename("///"), "race_day.html")

    def test_page_contents(self):
        page = race_day_html(day("Day <1>", [["3", ""], ["99", "3"]]), **PAGE)
        self.assertIn("<h1>DF95 2026</h1>", page)
        self.assertIn("<h2>Day &lt;1&gt; &middot; DF95</h2>", page)     # text is escaped
        self.assertIn("RMBC &lt;club&gt; &middot; 16 October 2026 19:45", page)
        self.assertIn("<th>Row</th><th>Race A</th><th>Race B</th>", page)
        self.assertEqual(page.count('<span class="name">Rosie Keel</span>'), 2)
        self.assertIn('<td><span class="sail">99</span></td>', page)   # unknown: no name
        self.assertIn('<tr><td class="row">2</td>', page)

    def test_names_use_the_competitions_classes_and_clubs(self):
        self.assertNotIn("Rosie Keel", race_day_html(day("d", [["3"]]), **{**PAGE, "classes": ["IOM"]}))
        both = race_day_html(day("d", [["3"]]), **{**PAGE, "classes": ["IOM", "DF95"]})
        self.assertIn("Rosie Keel", both)
        self.assertIn("<h2>d &middot; IOM, DF95</h2>", both)
        page = race_day_html(day("d", [["3", "3"]]), **{**PAGE, "clubs": ["Other"]})
        self.assertNotIn("Rosie Keel", page)

    def test_export_makes_folder_and_replaces_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "out" / "DF95_2026"
            path = export_race_day_html(folder, day("Race day 1", [["3", ""], ["99", "3"]]), **PAGE)
            self.assertEqual(path, folder / "Race_day_1.html")
            export_race_day_html(folder, day("Race day 1", [["3", "3"]]), **PAGE)
            self.assertNotIn('"sail">99<', path.read_text(encoding="utf-8"))


RESULTS = Results(["Day 1", "Day 2"], 2, [
    CompetitorResult("12", "DF95", "Ann <Smith>", [1, None], [1], 1),
    CompetitorResult("7", "DF95", "", [2, 3], [2, 3], 5),
    CompetitorResult("3", "Victoria", "Cat Brown", [5, None], [5], 5),
], FINAL, left_out=1)
RESULTS_PAGE = dict(club_title="RMBC", competition_title="DF95 2026",
                    generated=datetime.datetime(2026, 10, 16, 19, 45))


class ResultsHtmlTests(unittest.TestCase):
    def test_places_share_equal_points(self):
        self.assertEqual(RESULTS.places(), [1, 2, 2])
        self.assertEqual(Results([]).places(), [])

    def test_page_contents(self):
        page = results_html(RESULTS, **RESULTS_PAGE)
        self.assertIn("<h1>DF95 2026</h1>", page)
        self.assertIn("<h2>Final results</h2>", page)
        self.assertIn("<th>Place</th><th>Sail numbers</th><th>Class</th><th>Name</th>"
                      "<th>Day 1</th><th>Day 2</th><th>Races</th><th>All races</th><th>Points</th>", page)
        self.assertIn("Only sailors who have sailed 2 races or more", page)
        self.assertIn("1 sailor has not sailed enough races yet.", page)
        self.assertIn("Ann &lt;Smith&gt;", page)
        self.assertIn('<tr><td class="row">1</td><td class="sail">12</td><td>DF95</td>'
                      '<td>Ann &lt;Smith&gt;</td><td class="num">1</td><td class="num"></td>', page)
        self.assertEqual(page.count('<td class="row">2</td>'), 2)

    def test_current_results_show_the_average(self):
        current = Results(RESULTS.day_names, 2, RESULTS.competitors[:2], CURRENT)
        page = results_html(current, **RESULTS_PAGE)
        self.assertIn("<h2>Current results</h2>", page)
        self.assertIn("<th>Races</th><th>Points</th><th>Average</th></tr>", page)
        self.assertIn('<td class="num">2</td><td class="num">5</td><td class="points">2.50</td>', page)
        self.assertIn("Ranked by average points per race sailed", page)

    def test_all_races_column_only_when_some_are_dropped(self):
        page = results_html(Results(["Day 1"], None, []), **RESULTS_PAGE)
        self.assertNotIn("All races", page)
        self.assertIn("No results yet.", page)

    def test_export_writes_one_file_per_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = export_results_html(Path(tmp) / "out", RESULTS, **RESULTS_PAGE)
            current = export_results_html(Path(tmp) / "out", Results([], None, [], CURRENT),
                                          **RESULTS_PAGE)
            self.assertEqual((final.name, current.name), ("results_final.html", "results_current.html"))
            self.assertIn("Cat Brown", final.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
