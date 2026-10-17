import datetime
import unittest

from app.model.competition import Competition, safe_file_name, split_list
from app.model.limits import MAX_RACE_DAYS
from app.model.race_day import RaceDay, default_races


def comp(**changes) -> Competition:
    details = dict(name="Victoria DF65 2026", year=2026, classes=["DF65", "Victoria"],
                   clubs=["RMBC"], race_count=24, directory="Victoria2026")
    details.update(changes)
    return Competition(**details)


def day(name: str) -> RaceDay:
    return RaceDay(name, default_races(2))


def add_days(competition: Competition, count: int) -> None:
    for _ in range(count):
        competition.add_race_day(day(competition.next_race_day_name()))


class HelperTests(unittest.TestCase):
    def test_split_list(self):
        self.assertEqual(split_list(" df65, victoria ,,"), ["df65", "victoria"])
        self.assertEqual(split_list(""), [])

    def test_safe_file_name(self):
        self.assertEqual(safe_file_name("DF65 / IOM 2026", "x"), "DF65_IOM_2026")
        self.assertEqual(safe_file_name("../..", "x"), "x")


class CompetitionTests(unittest.TestCase):
    def test_details(self):
        c = comp(name="  Victoria_df65_competition_2026 ", classes=[" df65", "victoria", "DF 65"],
                 clubs=["RMBC", "rmbc", " "])
        self.assertEqual(c.title, "Victoria_df65_competition_2026")
        self.assertEqual(c.classes, ["df65", "victoria"])           # repeats and blanks dropped
        self.assertEqual(c.clubs, ["RMBC"])
        self.assertEqual((c.race_count, c.directory), (24, "Victoria2026"))

    def test_optional_details(self):
        c = Competition("DF95 2026", 2026, ["DF95"])
        self.assertEqual((c.clubs, c.race_count, c.directory), ([], None, "DF95_2026"))

    def test_directory_is_a_single_safe_folder_name(self):
        self.assertEqual(comp(directory="../../etc").directory, "etc")
        self.assertEqual(comp(directory=" ").directory, "Victoria_DF65_2026")

    def test_validation(self):
        for changes in ({"name": " "}, {"year": "2026"}, {"year": 1800}, {"year": True},
                        {"year": 2026.5}, {"classes": []}, {"classes": [" "]},
                        {"race_count": 0}, {"race_count": "24"}, {"race_count": True}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    comp(**changes)

    def test_has_class_ignores_case_and_spaces(self):
        self.assertTrue(comp().has_class("df 65"))
        self.assertFalse(comp().has_class("IOM"))

    def test_at_most_15_race_days(self):
        c = comp()
        add_days(c, MAX_RACE_DAYS)
        self.assertTrue(c.is_full)
        with self.assertRaises(ValueError):
            c.add_race_day(day("One too many"))
        self.assertEqual(len(c.race_days), MAX_RACE_DAYS)
        with self.assertRaises(ValueError):
            comp(race_days=[day(f"d{i}") for i in range(MAX_RACE_DAYS + 1)])

    def test_add_returns_the_index(self):
        c = comp()
        self.assertEqual(c.add_race_day(day("a")), 0)
        self.assertEqual(c.add_race_day(day("b")), 1)

    def test_default_names_are_unique_after_deleting(self):
        c = comp()
        add_days(c, 3)
        c.remove_race_day(0)               # leaves "Race day 2", "Race day 3"
        self.assertNotIn(c.next_race_day_name(), ("Race day 2", "Race day 3"))

    def test_default_name_from_the_date(self):
        c = comp()
        date = datetime.date(2026, 10, 10)
        self.assertEqual(c.next_race_day_name(date), "Race Day 10-10-2026")
        c.add_race_day(RaceDay(c.next_race_day_name(date), date=date))
        self.assertEqual(c.next_race_day_name(date), "Race Day 10-10-2026 (2)")

    def test_replace_and_remove(self):
        c = comp()
        add_days(c, 2)
        spring = day("Spring open")
        c.replace_race_day(0, spring)
        self.assertIs(c.race_days[0], spring)
        self.assertIs(c.remove_race_day(0), spring)
        self.assertEqual([d.name for d in c.race_days], ["Race day 2"])

    def test_with_details_keeps_the_race_days(self):
        c = comp()
        add_days(c, 1)
        c.add_race_day(day("DF65 day"))
        changed = c.with_details(comp(name="Renamed", race_count=None))
        self.assertEqual((changed.name, changed.race_count), ("Renamed", None))
        self.assertEqual(changed.race_days, c.race_days)
        self.assertTrue(changed.same_details(comp(name="Renamed", race_count=None)))
        self.assertFalse(changed.same_details(c))
        self.assertEqual(c.with_details(comp(classes=["victoria"])).race_days, c.race_days)


if __name__ == "__main__":
    unittest.main()
