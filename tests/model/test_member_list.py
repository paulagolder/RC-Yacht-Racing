import unittest

from app.model.boat_class import class_key
from app.model.member_list import MemberList
from app.model.sail_number import format_sail_number, sail_key, sort_key
from app.model.sailor import Sailor

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
CAT = Sailor("   12", "VICTORIA", "Cat", "Brown", "RMBC")
DAN = Sailor("   05", "DF95", "Dan", "Moor", "Other club")


class PersonTests(unittest.TestCase):
    def test_person_key_ignores_case_and_spacing(self):
        self.assertEqual(Sailor("1", "df 95", "Paul ", "GUTTERIDGE").person_key,
                         Sailor("2", "DF95", "paul", "Gutteridge").person_key)

    def test_tag_defaults_to_the_initials(self):
        self.assertEqual(Sailor("29", "DF95", "Paul", "Golder").tag, "PG")
        self.assertEqual(Sailor("29", "DF95", "Paul", "Golder", tag=" pag ").tag, "PAG")
        self.assertEqual(Sailor("1", "DF95", "", "Cher").tag, "C")
        self.assertIsNotNone(Sailor("1", "DF95", "A", "B", tag="TOOLONG").problem())
        self.assertIsNotNone(Sailor("1", "DF95", "A", "B", tag="A/B").problem())


class SailNumberTests(unittest.TestCase):
    def test_keys(self):
        self.assertEqual([sail_key(s) for s in ("   01", "1", "001", " x1 ", "0")],
                         ["1", "1", "1", "X1", "0"])
        self.assertEqual(class_key(" df 95 "), "DF95")

    def test_sort_numbers_first_in_number_order(self):
        self.assertEqual(sorted(["10", "X1", "2", "   03"], key=sort_key), ["2", "   03", "10", "X1"])

    def test_format(self):
        self.assertEqual(format_sail_number("1"), "   01")
        self.assertEqual(format_sail_number("01"), "   01")
        self.assertEqual(format_sail_number("123"), "  123")


class SailorTests(unittest.TestCase):
    def test_name_and_number(self):
        self.assertEqual((ANN.name, ANN.number), ("Ann Smith", "12"))

    def test_problem(self):
        self.assertIsNone(ANN.problem())
        self.assertIsNotNone(Sailor("1", "DF95", "", "").problem())
        self.assertIsNotNone(Sailor("  ", "DF95", "A", "B").problem())
        self.assertIsNotNone(Sailor("1", " ", "A", "B").problem())


class MemberListTests(unittest.TestCase):
    def setUp(self):
        self.members = MemberList([ANN, BOB, CAT])

    def test_find_ignores_case_spaces_and_leading_zeros(self):
        self.assertEqual(self.members.find(" 12 ", "df 95"), ANN)
        self.assertEqual(self.members.find("12", "Victoria"), CAT)
        self.assertEqual(self.members.find("7", "DF95"), BOB)
        self.assertEqual(self.members.find("007", "DF95"), BOB)
        self.assertIsNone(self.members.find("7", "VICTORIA"))

    def test_find_from_clubs(self):
        members = MemberList([ANN, DAN])
        self.assertEqual(members.find("5", "DF95"), DAN)
        self.assertEqual(members.find("5", "DF95", []), DAN)              # no clubs: any club
        self.assertIsNone(members.find("5", "DF95", ["RMBC"]))
        self.assertEqual(members.find("5", "DF95", ["RMBC", "other CLUB"]), DAN)
        self.assertEqual(members.find("12", "DF95", ["rmbc"]), ANN)

    def test_boat_classes(self):
        self.assertEqual(self.members.boat_classes(), ["DF95", "VICTORIA"])

    def test_check(self):
        members = MemberList([ANN, BOB])
        self.assertIsNone(members.check(CAT))
        self.assertIn("Ann Smith", members.check(Sailor("12", "df95", "New", "One")))
        self.assertIsNone(members.check(Sailor("12", "DF95", "Ann", "S"), ignore=0))
        self.assertIsNotNone(members.check(Sailor("1", "DF95", "", "")))

    def test_tags_must_tell_apart_sailors_with_the_same_sail_number(self):
        golder = Sailor("   29", "DF95", "Paul", "Golder")                        # tag PG
        members = MemberList([golder])
        clash = members.check(Sailor("   29", "DF65", "Paul", "Gutteridge"))       # also PG
        self.assertIn("tag PG", clash)
        self.assertIsNone(members.check(Sailor("   29", "DF65", "Paul", "Gutteridge", tag="PGU")))
        self.assertIsNone(members.check(Sailor("   29", "DF65", "Paul", "Golder")))   # same sailor
        self.assertIsNone(members.check(Sailor("   30", "DF65", "Paul", "Gutteridge")))

    def test_add_replace_remove(self):
        members = MemberList([ANN])
        members.add(BOB)
        self.assertEqual(members.find("7", "DF95"), BOB)
        with self.assertRaises(ValueError):
            members.add(Sailor("07", "DF95", "Other", "Bob"))
        members.replace(1, Sailor("   08", "DF95", "Bob", "Jones"))
        self.assertIsNone(members.find("7", "DF95"))
        self.assertIsNotNone(members.find("8", "DF95"))
        with self.assertRaises(ValueError):
            members.replace(1, Sailor("12", "DF95", "Bob", "Jones"))   # Ann's number
        self.assertEqual(members.remove(0), ANN)
        self.assertIsNone(members.find("12", "DF95"))
        self.assertEqual(len(members), 1)

    def test_list_is_copied(self):
        sailors = [ANN]
        MemberList(sailors).add(BOB)
        self.assertEqual(sailors, [ANN])


if __name__ == "__main__":
    unittest.main()
