import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.model.competition import Competition
from app.model.race import Race
from app.model.race_day import RaceDay, default_races
from app.storage import competition_store
from app.storage.competition_store import (
    delete_competition,
    list_competitions,
    load_competition,
    save_competition,
    suggested_filename,
    update_competition_details,
)
from app.storage.errors import StorageError


def simple(boat_class: str, year: int) -> Competition:
    """A competition with one class, as a version 1 or 2 file with this class and year reads."""
    return Competition(f"{boat_class} {year}", year, [boat_class])


def table_day(name: str, columns, rows) -> RaceDay:
    return RaceDay.from_table(name, columns, rows)


def sample() -> Competition:
    comp = simple("DF95", 2026)
    comp.add_race_day(table_day("Race day 1", ["Race A", "Race B", "Race C"],
                                         [["12", "7", "3"], ["7", "3", "12"]]))
    comp.add_race_day(RaceDay("Second day"))          # left empty, open to the class
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
        comp = simple("Vic & <Co>", 2026)
        comp.add_race_day(table_day('Day "1" \'a\'', ["A"], [["  padded  "], ["a&b <c> é ü 日本"]]))
        save_competition(comp, self.path)
        self.assertEqual(load_competition(self.path), comp)

    def test_control_characters_are_removed_rather_than_corrupting_the_file(self):
        comp = simple("DF95", 2026)
        comp.add_race_day(table_day("Race day 1", ["A"], [["a\x00b\x0bc"]]))
        save_competition(comp, self.path)
        self.assertEqual(load_competition(self.path).race_days[0].rows, [["abc"]])

    def test_second_save_keeps_a_backup_and_leaves_no_temp_file(self):
        comp = sample()
        save_competition(comp, self.path)
        comp.race_days[0].set_table(["Race A"], [["Changed"]])
        save_competition(comp, self.path)
        backup = self.path.with_name(self.path.name + ".bak")
        self.assertEqual(load_competition(backup).race_days[0].rows[0][0], "12")
        self.assertEqual(load_competition(self.path).race_days[0].rows[0][0], "Changed")
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()),
                         [self.path.name, backup.name])

    def test_failed_save_leaves_the_original_untouched(self):
        save_competition(sample(), self.path)
        before = self.path.read_bytes()
        with mock.patch("app.storage.xml_file.os.replace", side_effect=PermissionError(13, "denied")):
            with self.assertRaises(StorageError):
                save_competition(simple("DF95", 2027), self.path)
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

    def test_missing_or_bad_details(self):
        for xml in ('<competition class="DF95"/>', '<competition class="DF95" year="abc"/>',
                    '<competition class="DF95" year="1500"/>', '<competition class=" " year="2026"/>',
                    '<competition year="2026" classes="DF65"/>',                  # no name
                    '<competition year="2026" name="x"/>',                        # no classes
                    '<competition year="2026" name="x" classes=" , "/>',
                    '<competition year="2026" name="x" classes="DF65" racecount="lots"/>',
                    '<competition year="2026" name="x" classes="DF65" racecount="0"/>'):
            with self.subTest(xml=xml):
                with self.assertRaises(StorageError):
                    load_competition(self.write(xml))

    def test_file_layout(self):
        comp = Competition("Victoria_df65_competition_2026", 2026, ["df65", "victoria"], ["RMBC"],
                           24, "Victoria2026")
        comp.add_race_day(RaceDay.from_table("Race day 1", ["Race A", "Race B"],
                                             [["12", "7"], ["", ""], ["7", ""]]))
        comp.add_race_day(RaceDay("Race day 2", default_races(1)))
        save_competition(comp, self.path)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn('<competition year="2026" name="Victoria_df65_competition_2026" racecount="24" '
                      'clubs="RMBC" directory="Victoria2026" classes="df65,victoria" version="3">', text)
        self.assertIn('  <raceday name="Race day 1">\n    <race name="Race A">\n'
                      '      <sail>12</sail>\n      <sail />\n      <sail>7</sail>\n    </race>', text)
        self.assertIn('    <race name="Race B">\n      <sail>7</sail>\n    </race>', text)
        self.assertIn('  <raceday name="Race day 2">\n    <race name="Race A" />', text)
        self.assertEqual(load_competition(self.path), comp)

    def test_optional_details_are_left_out(self):
        save_competition(simple("DF95", 2026), self.path)
        self.assertIn('<competition year="2026" name="DF95 2026" directory="DF95_2026" classes="DF95" '
                      'version="3" />', self.path.read_text(encoding="utf-8"))

    def test_reads_details(self):
        xml = ('<competition  year="2026"  name= "Victoria_df65_competition_2026" racecount = "24" '
               'clubs = "RMBC" directory = "Victoria2026" classes = "df65,victoria">'
               '<raceday name="d" class="victoria"><race name="A"><sail>3</sail></race></raceday>'
               '<raceday name="e"><race name="A"><sail>7</sail></race></raceday></competition>')
        comp = load_competition(self.write(xml))
        self.assertEqual((comp.name, comp.year, comp.classes, comp.clubs, comp.race_count,
                          comp.directory),
                         ("Victoria_df65_competition_2026", 2026, ["df65", "victoria"], ["RMBC"], 24,
                          "Victoria2026"))
        self.assertEqual([d.name for d in comp.race_days], ["d", "e"])     # class="..." ignored
        save_competition(comp, self.path)
        self.assertNotIn("class=", self.path.read_text(encoding="utf-8").replace("classes=", ""))

    def test_empty_race_and_competition(self):
        comp = simple("DF95", 2026)
        save_competition(comp, self.path)
        self.assertEqual(load_competition(self.path), comp)
        comp.add_race_day(RaceDay("Race day 1"))           # four races with no sails yet
        save_competition(comp, self.path)
        self.assertIn('<race name="Race A" />', self.path.read_text(encoding="utf-8"))
        self.assertEqual(load_competition(self.path), comp)

    def test_reads_race_layout(self):
        xml = ('<competition class="DF95" year="2026" version="2"><raceday name="d">'
               '<race name="A"><sail>12</sail><sail/><sail>7</sail></race>'
               '<race><sail>7</sail></race></raceday></competition>')
        comp = load_competition(self.write(xml))
        self.assertEqual((comp.name, comp.classes, comp.directory), ("DF95 2026", ["DF95"], "DF95_2026"))
        self.assertEqual(comp.race_days[0], RaceDay("d", [Race("A", ["12", "", "7"]),
                                                          Race("Race B", ["7", "", ""])]))

    def test_reads_version_1_table_layout(self):
        xml = ('<competition class="DF95" year="2026" version="1"><raceday name="d">'
               '<columns><column>A</column><column>B</column></columns>'
               '<row><cell>12</cell><cell>7</cell></row>'
               '<row><cell>7</cell><cell/></row></raceday></competition>')
        comp = load_competition(self.write(xml))
        self.assertEqual(comp.race_days[0].races, [Race("A", ["12", "7"]), Race("B", ["7", ""])])
        save_competition(comp, self.path)                  # saved in the new layout
        self.assertIn('version="3"', self.path.read_text(encoding="utf-8"))
        self.assertEqual(load_competition(self.path), comp)

    def test_race_day_without_races(self):
        xml = '<competition class="DF95" year="2026"><raceday name="d"/></competition>'
        with self.assertRaises(StorageError) as ctx:
            load_competition(self.write(xml))
        self.assertIn("Race day 1", str(ctx.exception))

    def test_too_many_race_days(self):
        day = '<raceday><race name="A"/></raceday>'
        xml = f'<competition class="DF95" year="2026">{day * 16}</competition>'
        with self.assertRaises(StorageError):
            load_competition(self.write(xml))

    def test_too_many_races_or_sails(self):
        races = '<race/>' * 7
        sails = '<race>' + '<sail>1</sail>' * 16 + '</race>'
        for day in (races, sails):
            xml = f'<competition class="DF95" year="2026"><raceday>{day}</raceday></competition>'
            with self.subTest(day=day[:20]):
                with self.assertRaises(StorageError):
                    load_competition(self.write(xml))

    def test_version_1_row_wider_than_columns(self):
        xml = ('<competition class="DF95" year="2026"><raceday name="d">'
               '<columns><column>A</column></columns>'
               '<row><cell>1</cell><cell>2</cell></row></raceday></competition>')
        with self.assertRaises(StorageError):
            load_competition(self.write(xml))

    def test_unnamed_race_day_gets_a_default_name(self):
        xml = '<competition class="DF95" year="2026"><raceday><race/></raceday></competition>'
        self.assertEqual(load_competition(self.write(xml)).race_days[0].name, "Race day 1")

    def test_oversized_file_is_refused(self):
        save_competition(sample(), self.path)
        with mock.patch.object(competition_store, "MAX_FILE_BYTES", 10):
            with self.assertRaises(StorageError):
                load_competition(self.path)

    def test_suggested_filename(self):
        self.assertEqual(suggested_filename(simple("DF95", 2026)), "DF95_2026.cxml")
        self.assertEqual(suggested_filename(simple("10 Rater/IOM", 2026)), "10_Rater_IOM_2026.cxml")
        self.assertEqual(suggested_filename(Competition("Victoria_df65_competition_2026", 2026, ["df65"])),
                         "Victoria_df65_competition_2026.cxml")

    def test_new_details_rename_the_file_and_backup(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        save_competition(sample(), old)                 # makes a .bak
        details = Competition("Spring series", 2026, ["IOM", "DF95"], ["RMBC"], 10, "spring")
        new = update_competition_details(old, details)
        self.assertEqual(new.name, "Spring_series.cxml")
        self.assertFalse(old.exists())
        self.assertFalse((self.dir / "DF95_2026.cxml.bak").exists())
        self.assertTrue((self.dir / "Spring_series.cxml.bak").exists())
        comp = load_competition(new)
        self.assertTrue(comp.same_details(details))
        self.assertEqual(len(comp.race_days), 2)

    def test_new_details_refused_if_file_exists(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        save_competition(simple("IOM", 2025), self.dir / "IOM_2025.cxml")
        with self.assertRaises(StorageError):
            update_competition_details(old, simple("IOM", 2025))
        self.assertEqual(len(load_competition(old).race_days), 2)      # untouched
        self.assertTrue(load_competition(old).same_details(simple("DF95", 2026)))

    def test_new_details_with_the_same_name_just_save(self):
        old = self.dir / "DF95_2026.cxml"
        save_competition(sample(), old)
        details = Competition("DF95 2026", 2026, ["DF95"], race_count=3)
        self.assertEqual(update_competition_details(old, details), old)
        self.assertEqual(load_competition(old).race_count, 3)

    def test_delete_keeps_file_out_of_list(self):
        path = self.dir / "DF95_2026.cxml"
        save_competition(sample(), path)
        kept = delete_competition(path)
        self.assertEqual(kept.name, "DF95_2026.cxml.deleted")
        self.assertFalse(path.exists())
        self.assertEqual(list_competitions(self.dir), [])
        self.assertEqual(len(load_competition(kept).race_days), 2)

    def test_list_competitions(self):
        save_competition(simple("IOM", 2025), self.dir / "IOM_2025.cxml")
        save_competition(sample(), self.dir / "DF95_2026.cxml")
        save_competition(simple("Victoria", 2026), self.dir / "Victoria_2026.cxml")
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
