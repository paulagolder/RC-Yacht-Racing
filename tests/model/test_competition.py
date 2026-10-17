import unittest

from app.model.competition import Competition
from app.model.limits import MAX_RACE_DAYS
from app.model.race_day import RaceDay


def add_days(comp: Competition, count: int) -> None:
    for _ in range(count):
        comp.add_race_day(RaceDay(comp.next_race_day_name()))


class CompetitionTests(unittest.TestCase):
    def test_title(self):
        self.assertEqual(Competition(" DF95 ", 2026).title, "DF95 2026")

    def test_validation(self):
        for cls, year in (("", 2026), ("  ", 2026), ("DF95", "2026"), ("DF95", 1800),
                          ("DF95", 3000), ("DF95", True), ("DF95", 2026.5)):
            with self.subTest(cls=cls, year=year):
                with self.assertRaises(ValueError):
                    Competition(cls, year)

    def test_too_many_race_days_given(self):
        with self.assertRaises(ValueError):
            Competition("DF95", 2026, [RaceDay(f"d{i}") for i in range(MAX_RACE_DAYS + 1)])

    def test_at_most_15_race_days(self):
        comp = Competition("DF95", 2026)
        add_days(comp, MAX_RACE_DAYS)
        self.assertTrue(comp.is_full)
        with self.assertRaises(ValueError):
            comp.add_race_day(RaceDay("One too many"))
        self.assertEqual(len(comp.race_days), MAX_RACE_DAYS)

    def test_add_returns_the_index(self):
        comp = Competition("DF95", 2026)
        self.assertEqual(comp.add_race_day(RaceDay("a")), 0)
        self.assertEqual(comp.add_race_day(RaceDay("b")), 1)

    def test_default_names_are_unique_after_deleting(self):
        comp = Competition("DF95", 2026)
        add_days(comp, 3)
        comp.remove_race_day(0)               # leaves "Race day 2", "Race day 3"
        name = comp.next_race_day_name()
        self.assertNotIn(name, ("Race day 2", "Race day 3"))

    def test_replace_and_remove(self):
        comp = Competition("DF95", 2026)
        add_days(comp, 2)
        spring = RaceDay("Spring open")
        comp.replace_race_day(0, spring)
        self.assertIs(comp.race_days[0], spring)
        self.assertIs(comp.remove_race_day(0), spring)
        self.assertEqual([d.name for d in comp.race_days], ["Race day 2"])


if __name__ == "__main__":
    unittest.main()
