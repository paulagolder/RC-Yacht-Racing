import unittest

from app.model.boat_class import BoatClass
from app.model.competition import Competition
from app.model.member_list import MemberList
from app.model.race_day import RaceDay
from app.model.sailor import Sailor
from app.model.results import CURRENT, FINAL
from app.model.sail_entry import SailResolver
from app.services import scoring
from app.services.scoring import current_results, final_results

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
MEMBERS = MemberList([ANN, BOB])


def competition(*days: RaceDay, **details) -> Competition:
    details = {"name": "DF95 2026", "year": 2026, "classes": ["DF95", "IOM"], **details}
    return Competition(**details, race_days=list(days))


def competition_results(comp: Competition, members: MemberList | None = None,
                        classes: list[str] | None = None):
    """Scores comp, reading entries against members in comp's classes (or these)."""
    resolver = None
    if members is not None:
        boat_classes = [BoatClass(c.lower(), c) for c in (classes or comp.classes)]
        resolver = SailResolver(members, boat_classes, comp.clubs)
    return scoring.competition_results(comp, resolver)


def day(name: str, columns: list[str], rows) -> RaceDay:
    return RaceDay.from_table(name, columns, rows)


class CompetitionResultsTests(unittest.TestCase):
    def test_points_are_the_finishing_place(self):
        race_day = day("Race day 1", ["Race A", "Race B"], [["12", "7"], ["7", "12"], ["3", ""]])
        results = competition_results(competition(race_day), MEMBERS)
        by_sail = {r.sail_number: r for r in results.competitors}
        self.assertEqual((by_sail["12"].races, by_sail["12"].points), (2, 3))   # 1st + 2nd
        self.assertEqual((by_sail["07"].races, by_sail["07"].points), (2, 3))   # 2nd + 1st
        self.assertEqual((by_sail["3"].races, by_sail["3"].points), (1, 3))     # 3rd

    def test_totals_across_race_days(self):
        day1 = day("Race day 1", ["Race A"], [["12"], ["7"]])
        day2 = day("Race day 2", ["Race A"], [["7"]])
        results = competition_results(competition(day1, day2), MEMBERS)
        self.assertEqual(results.day_names, ["Race day 1", "Race day 2"])
        bob = next(r for r in results.competitors if r.sail_number == "07")
        ann = next(r for r in results.competitors if r.sail_number == "12")
        self.assertEqual((bob.day_points, bob.races, bob.points), ([2, 1], 2, 3))
        self.assertEqual((bob.day_races, ann.day_races), ([1, 1], [1, 0]))
        self.assertEqual((ann.day_points, ann.races, ann.points), ([1, None], 1, 1))

    def test_names_and_sail_number_forms(self):
        race_day = day("Race day 1", ["Race A", "Race B"], [["007", " 12 "], ["12", "7"]])
        results = competition_results(competition(race_day), MEMBERS)
        self.assertEqual([(r.sail_number, r.name, r.points) for r in results.competitors],
                         [("07", "Bob Jones", 3), ("12", "Ann Smith", 3)])

    def test_empty_cell_keeps_the_row_number_as_place(self):
        race_day = day("Race day 1", ["Race A"], [["12"], [""], ["7"]])
        results = competition_results(competition(race_day), MEMBERS)
        self.assertEqual([(r.sail_number, r.points) for r in results.competitors],
                         [("12", 1), ("07", 3)])                              # 12 is 1st, 07 is 3rd

    def test_fewest_points_first(self):
        race_day = day("Race day 1", ["Race A"], [["X1"], ["10"], ["2"]])
        results = competition_results(competition(race_day))
        self.assertEqual([(r.sail_number, r.name, r.points) for r in results.competitors],
                         [("X1", "", 1), ("10", "", 2), ("2", "", 3)])

    def test_equal_points_in_sail_number_order(self):
        race_day = day("Race day 1", ["Race A", "Race B"], [["10", "2"], ["2", "10"]])
        results = competition_results(competition(race_day))
        self.assertEqual([r.sail_number for r in results.competitors], ["2", "10"])

    def test_a_boat_takes_the_class_of_the_sailor(self):
        cat = Sailor("   09", "iom", "Cat", "Brown", "RMBC")    # shown as the competition writes it
        race_day = day("Race day 1", ["Race A"], [["9"], ["12"], ["99"]])
        results = competition_results(competition(race_day), MemberList([ANN, cat]))
        self.assertEqual([(r.sail_number, r.boat_class, r.name) for r in results.competitors],
                         [("09", "IOM", "Cat Brown"), ("12", "DF95", "Ann Smith"), ("99", "", "")])

    def test_only_sailors_from_the_clubs_are_named(self):
        dan = Sailor("   05", "DF95", "Dan", "Moor", "Other club")
        race_day = day("Race day 1", ["Race A"], [["12"], ["5"]])
        results = competition_results(competition(race_day, clubs=["RMBC"]), MemberList([ANN, dan]))
        self.assertEqual([r.name for r in results.competitors], ["Ann Smith", ""])

    def test_best_races_count(self):
        race_day = day("Race day 1", ["A", "B", "C"], [["12", "7", "7"], ["7", "12", "12"]])
        results = competition_results(competition(race_day, race_count=2), MEMBERS)
        self.assertEqual(results.race_count, 2)
        self.assertEqual([(r.sail_number, r.races, r.total, r.points, r.day_points)
                          for r in results.competitors],
                         [("07", 3, 4, 2, [4]), ("12", 3, 5, 3, [5])])    # worst race dropped

    def test_fewer_races_than_the_count(self):
        race_day = day("Race day 1", ["A"], [["12"], ["7"]])
        results = competition_results(competition(race_day, race_count=5), MEMBERS)
        self.assertEqual([(r.races, r.points) for r in results.competitors], [(1, 1), (1, 2)])

    def test_classes_by_full_name_find_the_sailors(self):
        race_day = day("Race day 1", ["Race A"], [["12"]])
        comp = competition(race_day, classes=["df95"])
        vic = Sailor("   12", "VICTORIA", "Vic", "Toria", "RMBC")
        results = competition_results(comp, MemberList([vic]), classes=["Victoria"])
        self.assertEqual([(r.boat_class, r.name) for r in results.competitors], [("Victoria", "Vic Toria")])

    def test_current_results_rank_by_average(self):
        # 12: 1st and 3rd (average 2); 7: 2nd only (average 2, fewer races); 3: 1st only
        day1 = day("Race day 1", ["A", "B"], [["12", "3"], ["7", ""], ["", "12"]])
        results = current_results(competition_results(competition(day1), MEMBERS))
        self.assertEqual(results.table, CURRENT)
        self.assertEqual([(r.sail_number, r.races, float(r.average)) for r in results.competitors],
                         [("3", 1, 1.0), ("12", 2, 2.0), ("07", 1, 2.0)])
        self.assertEqual(results.places(), [1, 2, 2])

    def test_final_results_only_boats_with_enough_races(self):
        day1 = day("Race day 1", ["A", "B", "C"], [["12", "7", "12"], ["7", "12", ""], ["3", "", ""]])
        results = final_results(competition_results(competition(day1, race_count=2), MEMBERS))
        self.assertEqual(results.table, FINAL)
        self.assertEqual([(r.sail_number, r.races, r.points) for r in results.competitors],
                         [("12", 3, 2), ("07", 2, 3)])               # 3 sailed once: left out
        self.assertEqual(results.left_out, 1)

    def test_a_sailors_boats_are_alternatives(self):
        paul = [Sailor("  440", "DF95", "Paul", "Grundy", "RMBC"),
                Sailor("   23", "DF95", "Paul", " grundy ", "RMBC")]   # name matched loosely
        day1 = day("Race day 1", ["A", "B"], [["440", "12"], ["12", "23"]])
        day2 = day("Race day 2", ["A"], [["23"]])
        results = competition_results(competition(day1, day2), MemberList([ANN, *paul]))
        self.assertEqual([(r.sail_numbers, r.name, r.races, r.points, r.day_points)
                          for r in results.competitors],
                         [("12", "Ann Smith", 2, 3, [3, None]),
                          ("440 / 23", "Paul Grundy", 3, 4, [3, 1])])

    def test_a_sailor_in_two_classes_is_one_competitor(self):
        paul = [Sailor("  440", "DF95", "Paul", "Grundy", "RMBC"),
                Sailor("   23", "IOM", "Paul", "Grundy", "RMBC")]
        day1 = day("Race day 1", ["A", "B"], [["440", "12"], ["12", "23"]])
        results = competition_results(competition(day1), MemberList([ANN, *paul]),
                                      classes=["DF95", "IOM"])
        grundy = next(r for r in results.competitors if r.name == "Paul Grundy")
        self.assertEqual((grundy.sail_numbers, grundy.boat_class, grundy.races, grundy.points),
                         ("440 / 23", "DF95 / IOM", 2, 3))
        self.assertEqual(len(results.competitors), 2)

    def test_tagged_entries_score_their_sailor(self):
        gale = Sailor("   29", "DF95", "Paul", "Gale", "RMBC", "PAG")
        grundy = Sailor("   29", "IOM", "Paul", "Grundy", "RMBC", "PGU")
        race_day = day("Race day 1", ["A"], [["29/PGU"], ["29/pag"], ["29"]])
        results = competition_results(competition(race_day), MemberList([gale, grundy]))
        self.assertEqual([(r.sail_numbers, r.boat_class, r.name, r.points) for r in results.competitors],
                         [("29", "IOM", "Paul Grundy", 1), ("29", "DF95", "Paul Gale", 2),
                          ("29", "", "", 3)])                 # untagged and ambiguous: unknown

    def test_no_race_days(self):
        results = competition_results(competition(), MEMBERS)
        self.assertEqual((results.day_names, results.competitors), ([], []))


if __name__ == "__main__":
    unittest.main()
