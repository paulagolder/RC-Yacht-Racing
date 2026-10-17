import unittest

from app.model.limits import MAX_PLACES, MAX_RACES
from app.model.race import Race
from app.model.race_day import RaceDay, default_races


class RaceDayTests(unittest.TestCase):
    def test_needs_a_name(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                RaceDay(bad)

    def test_name_is_stripped(self):
        self.assertEqual(RaceDay("  Day 1 ").name, "Day 1")

    def test_default_races(self):
        self.assertEqual(RaceDay("d").columns, ["Race A", "Race B", "Race C", "Race D"])
        self.assertEqual([r.name for r in default_races(2)], ["Race A", "Race B"])

    def test_table_view_of_the_races(self):
        day = RaceDay("d", [Race("A", ["12", "7"]), Race("B", ["7"])])
        self.assertEqual(day.columns, ["A", "B"])
        self.assertEqual(day.rows, [["12", "7"], ["7", ""]])
        self.assertEqual(day.races[1].finishers, ["7", ""])          # races are made equal length

    def test_from_table(self):
        day = RaceDay.from_table("d", ["A", "B"], [["12", "7"], ["7", "12"]])
        self.assertEqual(day.races, [Race("A", ["12", "7"]), Race("B", ["7", "12"])])

    def test_pads_short_rows_and_stringifies(self):
        day = RaceDay.from_table("d", ["A", "B", "C"], [["x"], [1, 2]])
        self.assertEqual(day.rows, [["x", "", ""], ["1", "2", ""]])

    def test_drops_trailing_empty_rows_but_keeps_inner_ones(self):
        day = RaceDay.from_table("d", ["A", "B"],
                                 [["a", ""], ["", ""], ["b", ""], ["", " "], ["", ""]])
        self.assertEqual(day.rows, [["a", ""], ["", ""], ["b", ""]])

    def test_too_many_races(self):
        with self.assertRaises(ValueError):
            RaceDay.from_table("d", [f"c{i}" for i in range(MAX_RACES + 1)], [])
        with self.assertRaises(ValueError):
            RaceDay("d", default_races(MAX_RACES + 1))

    def test_no_races(self):
        with self.assertRaises(ValueError):
            RaceDay.from_table("d", [], [])
        with self.assertRaises(ValueError):
            RaceDay("d", [])

    def test_too_many_rows(self):
        with self.assertRaises(ValueError):
            RaceDay.from_table("d", ["A"], [[str(i)] for i in range(MAX_PLACES + 1)])
        self.assertEqual(len(RaceDay("d", [Race("A", ["1"] + [""] * MAX_PLACES)]).rows), 1)

    def test_extra_text_beyond_columns_is_an_error_but_extra_blanks_are_not(self):
        with self.assertRaises(ValueError):
            RaceDay.from_table("d", ["A", "B"], [["1", "2", "3"]])
        self.assertEqual(RaceDay.from_table("d", ["A", "B"], [["1", "2", " "]]).rows, [["1", "2"]])

    def test_failed_set_table_leaves_old_races_unchanged(self):
        day = RaceDay.from_table("d", ["A", "B"], [["1", "2"]])
        with self.assertRaises(ValueError):
            day.set_table(["A", "B"], [["1", "2", "oops"]])
        self.assertEqual((day.columns, day.rows), (["A", "B"], [["1", "2"]]))

    def test_default_races_are_not_shared_between_days(self):
        a, b = RaceDay("a"), RaceDay("b")
        a.races.append(Race("extra"))
        self.assertNotIn("extra", b.columns)

    def test_given_races_are_copied(self):
        race = Race("A", ["1"])
        day = RaceDay("d", [race])
        race.finishers.append("2")
        self.assertEqual(day.rows, [["1"]])


if __name__ == "__main__":
    unittest.main()
