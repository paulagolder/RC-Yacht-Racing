import datetime
import unittest

from app.model.competition import Competition
from app.model.member_list import MemberList
from app.model.race import Race
from app.model.race_day import RaceDay
from app.model.sailor import Sailor
from app.services.report import competition_summary, summary_text
from app.services.scoring import competition_results

ANN = Sailor("   12", "DF65", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF65", "Bob", "Jones", "RMBC")
CAT = Sailor("   03", "VICTORIA", "Cat", "Brown", "RMBC")
MEMBERS = MemberList([ANN, BOB, CAT])
CLASSES = ["DF65", "Victoria"]


def competition() -> Competition:
    day1 = RaceDay("Day 1", [Race("A", ["12", "7", "3"]), Race("B", ["7", "12"]), Race("C")])
    day2 = RaceDay("Day 2", [Race("A", ["12", "99"])])
    return Competition("Vic 65 2026", 2026, ["df65", "victoria"], ["RMBC"], None, "",
                       [day1, day2])


def summary():
    comp = competition()
    return competition_summary(comp, competition_results(comp, MEMBERS, CLASSES), CLASSES)


class SummaryTests(unittest.TestCase):
    def test_counts(self):
        s = summary()
        self.assertEqual((len(s.days), s.races, s.races_sailed, s.finishes), (2, 4, 3, 7))
        self.assertEqual(s.competitors, 4)                        # 12, 07, 03 and 99
        self.assertEqual(s.by_class, {"DF65": 2, "Victoria": 1, "": 1})
        self.assertEqual([(d.name, d.races_sailed, d.boats, d.finishes) for d in s.days],
                         [("Day 1", 2, 3, 5), ("Day 2", 1, 2, 2)])

    def test_leaders_by_average_points(self):
        # 12: 4 points in 3 races; 07: 3 in 2; 99: 2 in 1; 03: 3 in 1, so 4th and not listed
        self.assertEqual([(l.place, l.sail_number, l.name, round(l.average, 2), l.races)
                          for l in summary().leaders],
                         [(1, "12", "Ann Smith", 1.33, 3), (2, "07", "Bob Jones", 1.5, 2),
                          (3, "99", "", 2.0, 1)])

    def test_qualified_only_with_a_race_count(self):
        self.assertIsNone(summary().qualified)
        comp = competition()
        comp.race_count = 2
        s = competition_summary(comp, competition_results(comp, MEMBERS, CLASSES), CLASSES)
        self.assertEqual(s.qualified, 2)                          # 12 and 07
        self.assertIn("Qualified:    2 with 2 races or more", summary_text(s))

    def test_text(self):
        text = summary_text(summary(), datetime.datetime(2026, 10, 17, 9, 30))
        self.assertIn("Vic 65 2026 - competition report", text)
        self.assertIn("2026 · DF65, Victoria · RMBC · every race counts", text)
        self.assertIn("Produced 17 October 2026 09:30", text)
        self.assertIn("Race days:    2 (of 15)", text)
        self.assertIn("Races sailed: 3 (of 4 in the tables)", text)
        self.assertIn("Competitors:  4 different sailors", text)
        self.assertIn("    not a club sailor: 1", text)
        self.assertIn("Day 1         2        3         5", text)
        self.assertIn("  1. 12 (DF65) Ann Smith: 1.33 over 3 races", text)
        self.assertIn("  3. 99: 2.00 over 1 race", text)
        self.assertNotIn("Qualified", text)

    def test_empty_competition(self):
        comp = Competition("New", 2026, ["df65"])
        text = summary_text(competition_summary(comp, competition_results(comp)))
        self.assertIn("No race days yet.", text)
        self.assertNotIn("Leading", text)


if __name__ == "__main__":
    unittest.main()
