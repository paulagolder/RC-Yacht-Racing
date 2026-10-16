import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.models import MAX_RACE_DAYS, Competition, previous_cell_position
from app.session import CompetitionSession
from app.storage import StorageError, load_competition


class PreviousCellTests(unittest.TestCase):
    def test_up_the_column(self):
        self.assertEqual(previous_cell_position(3, 1, 5, 4), (2, 1))

    def test_wraps_to_bottom_of_previous_column(self):
        self.assertEqual(previous_cell_position(0, 2, 5, 4), (4, 1))

    def test_wraps_from_first_column_to_last(self):
        self.assertEqual(previous_cell_position(0, 0, 5, 4), (4, 3))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "DF95_2026.xml"
        self.session = CompetitionSession.create(Competition("DF95", 2026), self.path)

    def on_disk(self) -> Competition:
        return load_competition(self.path)

    def test_create_writes_the_file(self):
        self.assertTrue(self.path.exists())
        self.assertEqual(self.on_disk(), Competition("DF95", 2026))

    def test_open_existing(self):
        self.session.add_race_day("Day 1", ["A"], [["x"]])
        reopened = CompetitionSession.open(self.path)
        self.assertEqual(reopened.competition, self.session.competition)

    def test_add_update_delete_are_saved_immediately(self):
        index = self.session.add_race_day("Day 1", ["Helm", "Pts"], [["Ann", "1"]])
        self.assertEqual(index, 0)
        self.assertEqual(self.on_disk(), self.session.competition)

        self.session.update_race_day(0, "Day one", ["Helm", "Pts"], [["Ann", "1"], ["Bob", "2"]])
        self.assertEqual(self.on_disk().race_days[0].name, "Day one")
        self.assertEqual(len(self.on_disk().race_days[0].rows), 2)

        self.session.delete_race_day(0)
        self.assertEqual(self.on_disk().race_days, [])

    def test_invalid_add_changes_nothing(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.session.add_race_day("Day 1", ["A"], [["1", "2"]])      # row too wide
        self.assertEqual(self.session.competition.race_days, [])
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_update_is_rolled_back(self):
        self.session.add_race_day("Day 1", ["A", "B"], [["1", "2"]])
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.session.update_race_day(0, "  ", ["A", "B"], [["9", "9"]])   # blank name
        day = self.session.competition.race_days[0]
        self.assertEqual((day.name, day.columns, day.rows), ("Day 1", ["A", "B"], [["1", "2"]]))
        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_saves_are_rolled_back_in_memory(self):
        self.session.add_race_day("Day 1", ["A"], [["1"]])
        self.session.add_race_day("Day 2", ["A"], [["2"]])
        snapshot = [(d.name, d.columns, d.rows) for d in self.session.competition.race_days]

        with mock.patch("app.session.save_competition", side_effect=StorageError("disk full")):
            with self.assertRaises(StorageError):
                self.session.add_race_day("Day 3", ["A"], [["3"]])
            with self.assertRaises(StorageError):
                self.session.update_race_day(0, "Changed", ["A", "B"], [["x", "y"]])
            with self.assertRaises(StorageError):
                self.session.delete_race_day(0)

        self.assertEqual([(d.name, d.columns, d.rows) for d in self.session.competition.race_days],
                         snapshot)

    def test_cannot_exceed_race_day_limit(self):
        for _ in range(MAX_RACE_DAYS):
            self.session.add_race_day(self.session.competition.next_race_day_name(), ["A"], [])
        with self.assertRaises(ValueError):
            self.session.add_race_day("One too many", ["A"], [])
        self.assertEqual(len(self.session.competition.race_days), MAX_RACE_DAYS)
        self.assertEqual(len(self.on_disk().race_days), MAX_RACE_DAYS)


if __name__ == "__main__":
    unittest.main()
