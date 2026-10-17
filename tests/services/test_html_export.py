import datetime
import tempfile
import unittest
from pathlib import Path

from app.model.member_list import MemberList
from app.model.race_day import RaceDay
from app.model.sailor import Sailor
from app.services.html_export import export_race_day_html, race_day_filename, race_day_html

MEMBERS = MemberList([Sailor("   03", "DF95", "Rosie", "Keel", "RMBC")])
PAGE = dict(club_title="RMBC <club>", competition_title="DF95 2026", members=MEMBERS,
            clubs=["RMBC"], generated=datetime.datetime(2026, 10, 16, 19, 45))


def day(name: str, rows, boat_class: str = "DF95") -> RaceDay:
    return RaceDay.from_table(name, ["Race A", "Race B"], rows, boat_class)


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

    def test_names_use_the_days_classes_and_the_clubs(self):
        self.assertNotIn("Rosie Keel", race_day_html(day("d", [["3"]], "IOM"), **PAGE))
        open_day = race_day_html(day("d", [["3"]], ""), **PAGE, classes=["IOM", "DF95"])
        self.assertIn("Rosie Keel", open_day)
        self.assertIn("<h2>d &middot; IOM, DF95</h2>", open_day)
        page = race_day_html(day("d", [["3", "3"]]), **{**PAGE, "clubs": ["Other"]})
        self.assertNotIn("Rosie Keel", page)

    def test_export_makes_folder_and_replaces_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "out" / "DF95_2026"
            path = export_race_day_html(folder, day("Race day 1", [["3", ""], ["99", "3"]]), **PAGE)
            self.assertEqual(path, folder / "Race_day_1.html")
            export_race_day_html(folder, day("Race day 1", [["3", "3"]]), **PAGE)
            self.assertNotIn('"sail">99<', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
