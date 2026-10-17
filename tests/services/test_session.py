import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.model.competition import Competition
from app.model.limits import MAX_RACE_DAYS
from app.model.race_day import RaceDay
from app.services.session import CompetitionSession
from app.storage.competition_store import load_competition
from app.storage.errors import StorageError


def day(name: str, columns, rows) -> RaceDay:
    return RaceDay.from_table(name, columns, rows)


def df95() -> Competition:
    return Competition("DF95 2026", 2026, ["DF95"])


class SessionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "DF95_2026.xml"
        self.session = CompetitionSession.create(df95(), self.path)

    def on_disk(self) -> Competition:
        return load_competition(self.path)

    def test_create_writes_the_file(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(self.on_disk(), df95())

    def test_open_existing(self):
        self.session.add_race_day(day("Day 1", ["A"], [["x"]]))
        reopened = CompetitionSession.open(self.path)
        self.assertEqual(reopened.competition, self.session.competition)

    def test_add_update_delete_are_saved_immediately(self):
        index = self.session.add_race_day(day("Day 1", ["A", "B"], [["12", "7"]]))
        self.assertEqual(index, 0)
        self.assertEqual(self.on_disk(), self.session.competition)

        self.session.update_race_day(0, day("Day one", ["A", "B"], [["12", "7"], ["7", "12"]]))
        self.assertEqual(self.on_disk().race_days[0].name, "Day one")
        self.assertEqual(len(self.on_disk().race_days[0].rows), 2)

        self.session.delete_race_day(0)
        self.assertEqual(self.on_disk().race_days, [])

    def test_failed_saves_are_rolled_back_in_memory(self):
        self.session.add_race_day(day("Day 1", ["A"], [["1"]]))
        self.session.add_race_day(day("Day 2", ["A"], [["2"]]))
        snapshot = [(d.name, d.columns, d.rows) for d in self.session.competition.race_days]

        with mock.patch("app.services.session.save_competition",
                        side_effect=StorageError("disk full")):
            with self.assertRaises(StorageError):
                self.session.add_race_day(day("Day 3", ["A"], [["3"]]))
            with self.assertRaises(StorageError):
                self.session.update_race_day(0, day("Changed", ["A", "B"], [["x", "y"]]))
            with self.assertRaises(StorageError):
                self.session.delete_race_day(0)

        self.assertEqual([(d.name, d.columns, d.rows) for d in self.session.competition.race_days],
                         snapshot)

    def test_open_normalises_the_classes_to_ids(self):
        self.path.write_text('<competition year="2026" name="Vic 65" classes="Victoria, DF 65,df65"/>',
                             encoding="utf-8")
        session = CompetitionSession.open(self.path)
        self.assertEqual(session.competition.classes, ["df65", "victoria"])
        self.assertEqual(session.class_names, ["DF65", "Victoria"])

    def test_open_keeps_unknown_classes_as_written(self):
        self.path.write_text('<competition year="2026" name="IOM" classes="IOM,Victoria"/>',
                             encoding="utf-8")
        session = CompetitionSession.open(self.path)
        self.assertEqual(session.competition.classes, ["IOM", "Victoria"])
        self.assertEqual(session.class_names, ["IOM", "Victoria"])

    def test_cannot_exceed_race_day_limit(self):
        for _ in range(MAX_RACE_DAYS):
            self.session.add_race_day(day(self.session.competition.next_race_day_name(), ["A"], []))
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.session.add_race_day(day("One too many", ["A"], []))
        self.assertEqual(len(self.session.competition.race_days), MAX_RACE_DAYS)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
