import tempfile
import unittest
from pathlib import Path

from app.models import DEFAULT_COLUMNS, DEFAULT_ROWS, MAX_COLUMNS
from app.settings import DEFAULT_TITLE, PROPERTIES_FILE, load_settings


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
                         (DEFAULT_TITLE, DEFAULT_ROWS, DEFAULT_COLUMNS))
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
                         (DEFAULT_TITLE, DEFAULT_ROWS, MAX_COLUMNS))

    def test_output_folder(self):
        self.assertEqual(load_settings(self.dir).output_dir,
                         Path.home() / "Documents" / "raceresult_output")
        self.write("<properties><output_folder>/srv/results</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, Path("/srv/results"))

    def test_broken_file_uses_defaults(self):
        self.write("<properties><title>")
        self.assertEqual(load_settings(self.dir).title, DEFAULT_TITLE)


if __name__ == "__main__":
    unittest.main()
