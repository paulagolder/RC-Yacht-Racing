import tempfile
import unittest
from pathlib import Path

from app.model.limits import DEFAULT_RACES, DEFAULT_ROWS, MAX_RACES
from app.storage.settings_store import (
    DATA_DIR,
    DEFAULT_TITLE,
    PROPERTIES_FILE,
    SYSTEM_FOLDER,
    find_data_dir,
    load_settings,
)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / ".pyraceresults"

    def write(self, text: str) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / PROPERTIES_FILE).write_text(text, encoding="utf-8")

    def test_creates_folder_and_default_file(self):
        settings = load_settings(self.dir)
        self.assertTrue((self.dir / PROPERTIES_FILE).exists())
        self.assertEqual((settings.title, settings.default_rows, settings.default_columns),
                         (DEFAULT_TITLE, DEFAULT_ROWS, DEFAULT_RACES))
        self.assertEqual(settings.data_dir, self.dir)

    def test_reads_values(self):
        self.write("<properties><title>RMBC</title><default_rows>8</default_rows>"
                   "<default_columns>3</default_columns></properties>")
        settings = load_settings(self.dir)
        self.assertEqual((settings.title, settings.default_rows, settings.default_columns),
                         ("RMBC", 8, 3))

    def test_bad_values_fall_back_or_are_limited(self):
        self.write("<properties><title> </title><default_rows>lots</default_rows>"
                   "<default_columns>99</default_columns></properties>")
        settings = load_settings(self.dir)
        self.assertEqual((settings.title, settings.default_rows, settings.default_columns),
                         (DEFAULT_TITLE, DEFAULT_ROWS, MAX_RACES))

    def test_output_folder(self):
        self.assertEqual(load_settings(self.dir).output_dir,
                         Path.home() / "Documents" / "raceresult_output")
        absolute = Path(self._tmp.name) / "results"      # with its drive letter on Windows
        self.write(f"<properties><output_folder>{absolute}</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, absolute)

    def test_relative_output_folder_is_beside_the_data_folder(self):
        self.write("<properties><output_folder>results</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, self.dir.parent / "results")

    def test_portable_copy_uses_its_system_folder(self):
        program = Path(self._tmp.name) / "RC-Yacht-Racing"
        self.assertEqual(find_data_dir(program), DATA_DIR)            # no system folder
        (program / SYSTEM_FOLDER).mkdir(parents=True)
        data_dir = find_data_dir(program)
        self.assertEqual(data_dir, program / SYSTEM_FOLDER)
        settings = load_settings(data_dir)
        self.assertEqual(settings.output_folder, "output")
        self.assertEqual(settings.output_dir, program / "output")      # beside the program
        self.assertIn("<output_folder>output</output_folder>",
                      (data_dir / PROPERTIES_FILE).read_text(encoding="utf-8"))

    def test_broken_file_uses_defaults(self):
        self.write("<properties><title>")
        self.assertEqual(load_settings(self.dir).title, DEFAULT_TITLE)


if __name__ == "__main__":
    unittest.main()
