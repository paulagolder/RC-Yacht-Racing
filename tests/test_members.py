import tempfile
import unittest
from pathlib import Path

from app.members import (
    MEMBERS_FILE,
    MemberList,
    Sailor,
    check_sailor,
    check_table,
    format_sail_number,
    load_members,
    save_members,
)
from app.storage import StorageError

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
CAT = Sailor("   12", "VICTORIA", "Cat", "Brown", "RMBC")

EXAMPLE = """<sails>
<sail sailnumber="   01" boatclass="VICTORIA" forename="Polly" surname="Breeze" club="RMBC" />
<sail sailnumber="   02" boatclass="DF95" forename="Sam" surname="Tiller" club="RMBC" />
<sail sailnumber="   02" boatclass="VICTORIA" forename="Sam" surname="Tiller" club="RMBC" />
</sails>"""


class MemberListTests(unittest.TestCase):
    def setUp(self):
        self.members = MemberList([ANN, BOB, CAT])

    def test_find_ignores_case_spaces_and_leading_zeros(self):
        self.assertEqual(self.members.find(" 12 ", "df 95"), ANN)
        self.assertEqual(self.members.find("12", "Victoria"), CAT)
        self.assertEqual(self.members.find("7", "DF95"), BOB)
        self.assertEqual(self.members.find("007", "DF95"), BOB)
        self.assertIsNone(self.members.find("7", "VICTORIA"))

    def test_sailor_name_and_number(self):
        self.assertEqual((ANN.name, ANN.number), ("Ann Smith", "12"))
        self.assertEqual(format_sail_number("1"), "   01")
        self.assertEqual(format_sail_number("01"), "   01")
        self.assertEqual(format_sail_number("123"), "  123")

    def test_check_table(self):
        rows = [["12", "7"], ["99", ""], ["012", "12"]]
        problems = check_table(rows, self.members, "DF95")
        self.assertEqual([(r, c) for r, c, _ in problems], [(1, 0), (2, 0)])
        self.assertIn("99", problems[0][2])
        self.assertIn("row 1", problems[1][2])      # 12 repeated in the first race

    def test_check_sailor(self):
        sailors = [ANN, BOB]
        self.assertIsNone(check_sailor(sailors, CAT))
        self.assertIn("Ann Smith", check_sailor(sailors, Sailor("12", "df95", "New", "One")))
        self.assertIsNone(check_sailor(sailors, Sailor("12", "DF95", "Ann", "S"), ignore=0))
        self.assertIsNotNone(check_sailor(sailors, Sailor("1", "DF95", "", "")))
        self.assertIsNotNone(check_sailor(sailors, Sailor("  ", "DF95", "A", "B")))


class MembersFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_missing_file_creates_empty_template(self):
        self.assertEqual(load_members(self.dir).sailors, [])
        self.assertTrue((self.dir / MEMBERS_FILE).exists())

    def test_reads_example_file(self):
        (self.dir / MEMBERS_FILE).write_text(EXAMPLE, encoding="utf-8")
        members = load_members(self.dir)
        self.assertEqual(len(members.sailors), 3)
        self.assertEqual(members.sailors[0], Sailor("   01", "VICTORIA", "Polly", "Breeze", "RMBC"))
        self.assertEqual(members.find("2", "DF95").name, "Sam Tiller")

    def test_saves_padding_and_attributes(self):
        save_members([BOB], self.dir)
        text = (self.dir / MEMBERS_FILE).read_text(encoding="utf-8")
        self.assertIn('<sail sailnumber="   07" boatclass="DF95" forename="Bob" surname="Jones" '
                      'club="RMBC" />', text)

    def test_round_trip_keeps_backup(self):
        save_members([ANN], self.dir)
        save_members([ANN, BOB, CAT], self.dir)
        self.assertEqual(load_members(self.dir).sailors, [ANN, BOB, CAT])
        self.assertTrue((self.dir / (MEMBERS_FILE + ".bak")).exists())

    def test_bad_files(self):
        path = self.dir / MEMBERS_FILE
        for text in ("<sails>", "<sailors/>",
                     '<sails><sail sailnumber="1" forename="X" /></sails>'):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(StorageError):
                load_members(self.dir)


if __name__ == "__main__":
    unittest.main()
