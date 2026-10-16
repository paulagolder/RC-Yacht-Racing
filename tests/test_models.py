import unittest

from app.models import (
    MAX_COLUMNS,
    MAX_RACE_DAYS,
    MAX_ROWS,
    Competition,
    RaceDay,
    column_label,
    default_columns,
    letters,
    next_cell_position,
)


class LettersTests(unittest.TestCase):
    def test_letters(self):
        self.assertEqual([letters(n) for n in (1, 2, 26, 27, 28, 52, 53)],
                         ["A", "B", "Z", "AA", "AB", "AZ", "BA"])

    def test_column_label(self):
        self.assertEqual(column_label(1), "Race A")
        self.assertEqual(default_columns(3), ["Race A", "Race B", "Race C"])


class NextCellTests(unittest.TestCase):
    def test_moves_down_the_column(self):
        self.assertEqual(next_cell_position(0, 2, 5, 4), (1, 2, False))

    def test_adds_a_row_at_the_bottom_while_growth_is_allowed(self):
        self.assertEqual(next_cell_position(4, 1, 5, 4), (5, 1, True))

    def test_wraps_to_next_column_when_table_is_full(self):
        self.assertEqual(next_cell_position(MAX_ROWS - 1, 1, MAX_ROWS, 4), (0, 2, False))

    def test_wraps_from_last_column_to_first(self):
        self.assertEqual(next_cell_position(MAX_ROWS - 1, 3, MAX_ROWS, 4), (0, 0, False))


class RaceDayTests(unittest.TestCase):
    def test_needs_a_name(self):
        for bad in ("", "   ", None):
            with self.assertRaises(ValueError):
                RaceDay(bad)

    def test_name_is_stripped(self):
        self.assertEqual(RaceDay("  Day 1 ").name, "Day 1")

    def test_pads_short_rows_and_stringifies(self):
        day = RaceDay("d", ["A", "B", "C"], [["x"], [1, 2]])
        self.assertEqual(day.rows, [["x", "", ""], ["1", "2", ""]])

    def test_drops_trailing_empty_rows_but_keeps_inner_ones(self):
        day = RaceDay("d", ["A", "B"], [["a", ""], ["", ""], ["b", ""], ["", " "], ["", ""]])
        self.assertEqual(day.rows, [["a", ""], ["", ""], ["b", ""]])

    def test_too_many_columns(self):
        with self.assertRaises(ValueError):
            RaceDay("d", [f"c{i}" for i in range(MAX_COLUMNS + 1)])

    def test_no_columns(self):
        with self.assertRaises(ValueError):
            RaceDay("d", [])

    def test_too_many_rows(self):
        with self.assertRaises(ValueError):
            RaceDay("d", ["A"], [[str(i)] for i in range(MAX_ROWS + 1)])

    def test_extra_text_beyond_columns_is_an_error_but_extra_blanks_are_not(self):
        with self.assertRaises(ValueError):
            RaceDay("d", ["A", "B"], [["1", "2", "3"]])
        self.assertEqual(RaceDay("d", ["A", "B"], [["1", "2", " "]]).rows, [["1", "2"]])

    def test_failed_set_table_leaves_old_table_unchanged(self):
        day = RaceDay("d", ["A", "B"], [["1", "2"]])
        with self.assertRaises(ValueError):
            day.set_table(["A", "B"], [["1", "2", "oops"]])
        self.assertEqual((day.columns, day.rows), (["A", "B"], [["1", "2"]]))

    def test_default_columns_are_not_shared_between_days(self):
        a, b = RaceDay("a"), RaceDay("b")
        a.columns.append("extra")
        self.assertNotIn("extra", b.columns)


class CompetitionTests(unittest.TestCase):
    def test_title(self):
        self.assertEqual(Competition(" DF95 ", 2026).title, "DF95 2026")

    def test_validation(self):
        for cls, year in (("", 2026), ("  ", 2026), ("DF95", "2026"), ("DF95", 1800),
                          ("DF95", 3000), ("DF95", True), ("DF95", 2026.5)):
            with self.subTest(cls=cls, year=year):
                with self.assertRaises(ValueError):
                    Competition(cls, year)

    def test_at_most_15_race_days(self):
        comp = Competition("DF95", 2026)
        for _ in range(MAX_RACE_DAYS):
            comp.add_race_day()
        with self.assertRaises(ValueError):
            comp.add_race_day()
        self.assertEqual(len(comp.race_days), MAX_RACE_DAYS)

    def test_default_names_are_unique_after_deleting(self):
        comp = Competition("DF95", 2026)
        for _ in range(3):
            comp.add_race_day()
        comp.remove_race_day(0)               # leaves "Race day 2", "Race day 3"
        new = comp.add_race_day()
        self.assertEqual(len({d.name for d in comp.race_days}), 3)
        self.assertNotIn(new.name, ("Race day 2", "Race day 3"))

    def test_rename(self):
        comp = Competition("DF95", 2026)
        comp.add_race_day()
        comp.rename_race_day(0, "  Spring open ")
        self.assertEqual(comp.race_days[0].name, "Spring open")
        with self.assertRaises(ValueError):
            comp.rename_race_day(0, " ")
        self.assertEqual(comp.race_days[0].name, "Spring open")


if __name__ == "__main__":
    unittest.main()
