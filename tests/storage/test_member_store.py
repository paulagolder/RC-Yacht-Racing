import tempfile
import unittest
from pathlib import Path

from app.model.member_list import MemberList
from app.model.sailor import Sailor
from app.storage.errors import StorageError
from app.storage.member_store import MEMBERS_FILE, load_members, save_members

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
CAT = Sailor("   12", "VICTORIA", "Cat", "Brown", "RMBC")

EXAMPLE = """<sails>
<sail sailnumber="   01" boatclass="VICTORIA" forename="Polly" surname="Breeze" club="RMBC" />
<sail sailnumber="   02" boatclass="DF95" forename="Sam" surname="Tiller" club="RMBC" />
<sail sailnumber="   02" boatclass="VICTORIA" forename="Sam" surname="Tiller" club="RMBC" />
</sails>"""


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
        save_members(MemberList([BOB]), self.dir)
        text = (self.dir / MEMBERS_FILE).read_text(encoding="utf-8")
        self.assertIn('<sail sailnumber="   07" boatclass="DF95" forename="Bob" surname="Jones" '
                      'club="RMBC" tag="BJ" />', text)

    def test_tag_is_read_and_defaults_to_the_initials(self):
        (self.dir / MEMBERS_FILE).write_text(
            '<sails><sail sailnumber="29" boatclass="DF95" forename="Paul" surname="Gale" '
            'club="RMBC" tag="pag" /><sail sailnumber="23" boatclass="DF95" forename="Paul" '
            'surname="Grundy" club="RMBC" /></sails>', encoding="utf-8")
        self.assertEqual([s.tag for s in load_members(self.dir).sailors], ["PAG", "PG"])

    def test_round_trip_keeps_backup(self):
        save_members(MemberList([ANN]), self.dir)
        save_members(MemberList([ANN, BOB, CAT]), self.dir)
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
