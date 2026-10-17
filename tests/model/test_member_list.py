import unittest

from app.model.boat_class import class_key
from app.model.member_list import MemberList
from app.model.race import Race
from app.model.sail_number import format_sail_number, sail_key, sort_key
from app.model.sailor import Sailor

ANN = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")
BOB = Sailor("   07", "DF95", "Bob", "Jones", "RMBC")
CAT = Sailor("   12", "VICTORIA", "Cat", "Brown", "RMBC")


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

    def test_boat_classes(self):
        self.assertEqual(self.members.boat_classes(), ["DF95", "VICTORIA"])

    def test_check(self):
        members = MemberList([ANN, BOB])
        self.assertIsNone(members.check(CAT))
        self.assertIn("Ann Smith", members.check(Sailor("12", "df95", "New", "One")))
        self.assertIsNone(members.check(Sailor("12", "DF95", "Ann", "S"), ignore=0))
        self.assertIsNotNone(members.check(Sailor("1", "DF95", "", "")))

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

    def test_check_races(self):
        races = [Race("A", ["12", "99", "012"]), Race("B", ["7", "", "12"])]
        problems = self.members.check_races(races, "DF95")
        self.assertEqual([(r, c) for r, c, _ in problems], [(1, 0), (2, 0)])
        self.assertIn("99", problems[0][2])
        self.assertIn("row 1", problems[1][2])      # 12 repeated in the first race

    def test_check_races_in_table_order(self):
        races = [Race("A", ["", "99"]), Race("B", ["98"])]
        problems = self.members.check_races(races, "DF95")
        self.assertEqual([(r, c) for r, c, _ in problems], [(0, 1), (1, 0)])


if __name__ == "__main__":
    unittest.main()
