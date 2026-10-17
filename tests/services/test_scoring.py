import unittest

from app.model.competition import Competition
from app.model.member_list import MemberList
from app.model.race_day import RaceDay
from app.model.sailor import Sailor
from app.services.scoring import competition_results

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
MEMBERS = MemberList([ANN, BOB])


def competition(*days: RaceDay) -> Competition:
    return Competition("DF95", 2026, list(days))


class CompetitionResultsTests(unittest.TestCase):
    def test_points_are_the_finishing_place(self):
        day = RaceDay.from_table("Race day 1", ["Race A", "Race B"], [["12", "7"], ["7", "12"], ["3", ""]])
        results = competition_results(competition(day), MEMBERS)
        by_sail = {r.sail_number: r for r in results.competitors}
        self.assertEqual((by_sail["12"].races, by_sail["12"].points), (2, 3))   # 1st + 2nd
        self.assertEqual((by_sail["07"].races, by_sail["07"].points), (2, 3))   # 2nd + 1st
        self.assertEqual((by_sail["3"].races, by_sail["3"].points), (1, 3))     # 3rd

    def test_totals_across_race_days(self):
        day1 = RaceDay.from_table("Race day 1", ["Race A"], [["12"], ["7"]])
        day2 = RaceDay.from_table("Race day 2", ["Race A"], [["7"]])
        results = competition_results(competition(day1, day2), MEMBERS)
        self.assertEqual(results.day_names, ["Race day 1", "Race day 2"])
        bob = next(r for r in results.competitors if r.sail_number == "07")
        ann = next(r for r in results.competitors if r.sail_number == "12")
        self.assertEqual((bob.day_points, bob.races, bob.points), ([2, 1], 2, 3))
        self.assertEqual((ann.day_points, ann.races, ann.points), ([1, None], 1, 1))

    def test_names_and_sail_number_forms(self):
        day = RaceDay.from_table("Race day 1", ["Race A", "Race B"], [["007", " 12 "], ["12", "7"]])
        results = competition_results(competition(day), MEMBERS)
        self.assertEqual([(r.sail_number, r.name, r.points) for r in results.competitors],
                         [("07", "Bob Jones", 3), ("12", "Ann Smith", 3)])

    def test_empty_cell_keeps_the_row_number_as_place(self):
        day = RaceDay.from_table("Race day 1", ["Race A"], [["12"], [""], ["7"]])
        results = competition_results(competition(day), MEMBERS)
        self.assertEqual([(r.sail_number, r.points) for r in results.competitors],
                         [("12", 1), ("07", 3)])                              # 12 is 1st, 07 is 3rd

    def test_fewest_points_first(self):
        day = RaceDay.from_table("Race day 1", ["Race A"], [["X1"], ["10"], ["2"]])
        results = competition_results(competition(day))
        self.assertEqual([(r.sail_number, r.name, r.points) for r in results.competitors],
                         [("X1", "", 1), ("10", "", 2), ("2", "", 3)])

    def test_equal_points_in_sail_number_order(self):
        day = RaceDay.from_table("Race day 1", ["Race A", "Race B"], [["10", "2"], ["2", "10"]])
        results = competition_results(competition(day))
        self.assertEqual([r.sail_number for r in results.competitors], ["2", "10"])

    def test_no_race_days(self):
        results = competition_results(competition(), MEMBERS)
        self.assertEqual((results.day_names, results.competitors), ([], []))


if __name__ == "__main__":
    unittest.main()
