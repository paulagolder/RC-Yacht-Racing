import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import storage
from app.models import Competition
from app.storage import (
    StorageError,
    delete_competition,
    list_competitions,
    load_competition,
    rename_competition,
    save_competition,
    suggested_filename,
)


def sample() -> Competition:
    comp = Competition("DF95", 2026)
    day = comp.add_race_day()
    day.set_table(["Helm", "Sail", "Pts"], [["Ann", "12", "1"], ["Bob", "7", "2"]])
    comp.add_race_day("Second day")          # left empty
    return comp


class StorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.path = self.dir / "DF95_2026.xml"

    def write(self, text: str) -> Path:
        self.path.write_text(text, encoding="utf-8")
        return self.path

    def test_round_trip(self):
        original = sample()
        save_competition(original, self.path)
        loaded = load_competition(self.path)
        self.assertEqual(loaded, original)

    def test_round_trip_awkward_text(self):
        comp = Competition("Vic & <Co>", 2026)
        day = comp.add_race_day('Day "1" \'a\'')
        day.set_table(["A"], [["  padded  "], ["a&b <c> é ü 日本"]])
        save_competition(comp, self.path)
        self.assertEqual(load_competition(self.path), comp)

    def test_control_characters_are_removed_rather_than_corrupting_the_file(self):
        comp = Competition("DF95", 2026)
        comp.add_race_day().set_table(["A"], [["a\x00b\x0bc"]])
        save_competition(comp, self.path)
        self.assertEqual(load_competition(self.path).race_days[0].rows, [["abc"]])

    def test_second_save_keeps_a_backup_and_leaves_no_temp_file(self):
        comp = sample()
        save_competition(comp, self.path)
        comp.race_days[0].set_table(["Helm"], [["Changed"]])
        save_competition(comp, self.path)
        backup = self.path.with_name(self.path.name + ".bak")
        self.assertEqual(load_competition(backup).race_days[0].rows[0][0], "Ann")
        self.assertEqual(load_competition(self.path).race_days[0].rows[0][0], "Changed")
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()),
                         [self.path.name, backup.name])

    def test_failed_save_leaves_the_original_untouched(self):
        save_competition(sample(), self.path)
        before = self.path.read_bytes()
        with mock.patch("app.storage.os.replace", side_effect=PermissionError(13, "denied")):
            with self.assertRaises(StorageError):
                save_competition(Competition("DF95", 2027), self.path)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.path.with_name(self.path.name + ".tmp").exists())

    def test_save_to_missing_folder_is_a_storage_error(self):
        with self.assertRaises(StorageError):
            save_competition(sample(), self.dir / "nope" / "x.xml")

    def test_missing_file(self):
        with self.assertRaises(StorageError):
            load_competition(self.dir / "absent.xml")

    def test_not_xml(self):
        with self.assertRaises(StorageError):
            load_competition(self.write("this is not xml"))

    def test_wrong_root(self):
        with self.assertRaises(StorageError):
            load_competition(self.write("<other/>"))

    def test_missing_or_bad_class_and_year(self):
        for xml in ('<competition year="2026"/>', '<competition class="DF95"/>',
                    '<competition class="DF95" year="abc"/>',
                    '<competition class="DF95" year="1500"/>'):
            with self.subTest(xml=xml):
                with self.assertRaises(StorageError):
                    load_competition(self.write(xml))

    def test_race_day_without_columns(self):
        xml = '<competition class="DF95" year="2026"><raceday name="d"/></competition>'
        with self.assertRaises(StorageError) as ctx:
            load_competition(self.write(xml))
        self.assertIn("Race day 1", str(ctx.exception))

    def test_too_many_race_days(self):
        day = '<raceday><columns><column>A</column></columns></raceday>'
        xml = f'<competition class="DF95" year="2026">{day * 16}</competition>'
        with self.assertRaises(StorageError):
            load_competition(self.write(xml))

    def test_row_wider_than_columns(self):
        xml = ('<competition class="DF95" year="2026"><raceday name="d">'
               '<columns><column>A</column></columns>'
               '<row><cell>1</cell><cell>2</cell></row></raceday></competition>')
        with self.assertRaises(StorageError):
            load_competition(self.write(xml))

    def test_unnamed_race_day_gets_a_default_name(self):
        xml = ('<competition class="DF95" year="2026"><raceday>'
               '<columns><column>A</column></columns></raceday></competition>')
        self.assertEqual(load_competition(self.write(xml)).race_days[0].name, "Race day 1")

    def test_oversized_file_is_refused(self):
        save_competition(sample(), self.path)
        with mock.patch.object(storage, "MAX_FILE_BYTES", 10):
            with self.assertRaises(StorageError):
                load_competition(self.path)

    def test_suggested_filename(self):
        self.assertEqual(suggested_filename(Competition("DF95", 2026)), "DF95_2026.cxml")
        self.assertEqual(suggested_filename(Competition("10 Rater/IOM", 2026)), "10_Rater_IOM_2026.cxml")

    def test_rename_competition_moves_file_and_backup(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        save_competition(sample(), old)                 # makes a .bak
        new = rename_competition(old, "IOM", 2025)
        self.assertEqual(new.name, "IOM_2025.cxml")
        self.assertFalse(old.exists())
        self.assertFalse((self.dir / "DF95_2026.cxml.bak").exists())
        self.assertTrue((self.dir / "IOM_2025.cxml.bak").exists())
        comp = load_competition(new)
        self.assertEqual((comp.boat_class, comp.year, len(comp.race_days)), ("IOM", 2025, 2))

    def test_rename_refuses_to_overwrite_or_bad_values(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        save_competition(Competition("IOM", 2025), self.dir / "IOM_2025.cxml")
        with self.assertRaises(StorageError):
            rename_competition(old, "IOM", 2025)
        with self.assertRaises(StorageError):
            rename_competition(old, "IOM", 1066)
        self.assertEqual(len(load_competition(old).race_days), 2)      # untouched

    def test_rename_same_name_just_saves(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        self.assertEqual(rename_competition(old, "DF95", 2026), old)
        self.assertTrue(old.exists())

    def test_delete_keeps_file_out_of_list(self):
        path = self.dir / "DF95_2026.cxml"
        save_competition(sample(), path)
        kept = delete_competition(path)
        self.assertEqual(kept.name, "DF95_2026.cxml.deleted")
        self.assertFalse(path.exists())
        self.assertEqual(list_competitions(self.dir), [])
        self.assertEqual(len(load_competition(kept).race_days), 2)

    def test_list_competitions(self):
        save_competition(Competition("IOM", 2025), self.dir / "IOM_2025.cxml")
        save_competition(sample(), self.dir / "DF95_2026.cxml")
        save_competition(Competition("Victoria", 2026), self.dir / "Victoria_2026.cxml")
        (self.dir / "broken.cxml").write_text("<competition", encoding="utf-8")
        (self.dir / "properties.xml").write_text("<properties/>", encoding="utf-8")   # not listed
        found = list_competitions(self.dir)
        self.assertEqual([path.name for path, _, _ in found],
                         ["DF95_2026.cxml", "Victoria_2026.cxml", "IOM_2025.cxml", "broken.cxml"])
        self.assertEqual(len(found[0][1].race_days), 2)
        self.assertIsNone(found[3][1])
        self.assertIn("not valid XML", found[3][2])


if __name__ == "__main__":
    unittest.main()
