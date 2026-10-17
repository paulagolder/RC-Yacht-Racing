import tempfile
import unittest
from pathlib import Path

from app.model.boat_class import DEFAULT_BOAT_CLASSES, BoatClass, BoatClassList
from app.storage.boat_class_store import (
    BOAT_CLASSES_FILE,
    boat_classes_or_defaults,
    load_boat_classes,
    save_boat_classes,
)
from app.storage.errors import StorageError

EXAMPLE = """<classes>
<boatclass  key="df65" fullname="DF65" cypher="65"  symbol="#" />
<boatclass  key="rg65" fullname="RG65" cypher="rg"  symbol="$" />
<boatclass  key="df95" fullname="DF95" cypher="95"  symbol="@" />
<boatclass  key="victoria" fullname="Victoria" cypher="Va"  symbol="*" />
</classes>"""

IOM = BoatClass("iom", "IOM", "IO", "!")


class BoatClassListTests(unittest.TestCase):
    def test_find_by_key_or_name(self):
        classes = BoatClassList(DEFAULT_BOAT_CLASSES)
        self.assertEqual(classes.find("df 95").symbol, "@")
        self.assertEqual(classes.find("VICTORIA").cypher, "Va")
        self.assertIsNone(classes.find("IOM"))

    def test_duplicates_and_missing_values_refused(self):
        classes = BoatClassList(DEFAULT_BOAT_CLASSES)
        for bad in (BoatClass("DF95", "Other", "x", "x"), BoatClass("x", "df 95", "x", "x"),
                    BoatClass("x", "X", "95", "x"), BoatClass("x", "X", "x", "@"),
                    BoatClass("", "X"), BoatClass("x", ""), BoatClass("x", "X", "", "ab")):
            with self.assertRaises(ValueError):
                classes.add(bad)
        classes.replace(2, BoatClass("df95", "DF95", "95", "%"))    # itself is not a duplicate
        self.assertEqual(classes.classes[2].symbol, "%")

    def test_normalise_to_ids_in_file_order(self):
        classes = BoatClassList(DEFAULT_BOAT_CLASSES)
        self.assertEqual(classes.normalise(["Victoria", " df 65", "DF65", ""]),
                         ["df65", "victoria"])
        self.assertEqual(classes.display_names(["df65", "victoria", "IOM"]), ["DF65", "Victoria", "IOM"])
        with self.assertRaises(ValueError) as ctx:
            classes.normalise(["DF65", "IOM", "Marblehead"])
        self.assertIn("IOM, Marblehead", str(ctx.exception))


class BoatClassesFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_missing_file_creates_defaults(self):
        self.assertEqual(load_boat_classes(self.dir).classes, DEFAULT_BOAT_CLASSES)
        self.assertTrue((self.dir / BOAT_CLASSES_FILE).exists())

    def test_reads_example_file(self):
        (self.dir / BOAT_CLASSES_FILE).write_text(EXAMPLE, encoding="utf-8")
        classes = load_boat_classes(self.dir)
        self.assertEqual(classes.classes, DEFAULT_BOAT_CLASSES)
        self.assertEqual(classes.names(), ["DF65", "RG65", "DF95", "Victoria"])

    def test_round_trip_keeps_backup(self):
        save_boat_classes(BoatClassList([IOM]), self.dir)
        save_boat_classes(BoatClassList([*DEFAULT_BOAT_CLASSES, IOM]), self.dir)
        self.assertEqual(load_boat_classes(self.dir).classes, [*DEFAULT_BOAT_CLASSES, IOM])
        self.assertTrue((self.dir / (BOAT_CLASSES_FILE + ".bak")).exists())
        text = (self.dir / BOAT_CLASSES_FILE).read_text(encoding="utf-8")
        self.assertIn('<boatclass key="iom" fullname="IOM" cypher="IO" symbol="!" />', text)

    def test_bad_files(self):
        path = self.dir / BOAT_CLASSES_FILE
        for text in ("<classes>", "<boats/>", '<classes><boatclass key="x" /></classes>'):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(StorageError):
                load_boat_classes(self.dir)
        self.assertEqual(boat_classes_or_defaults(self.dir).names(), ["DF65", "RG65", "DF95", "Victoria"])


if __name__ == "__main__":
    unittest.main()
