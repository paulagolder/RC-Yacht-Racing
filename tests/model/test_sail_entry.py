import unittest

from app.model.boat_class import BoatClass
from app.model.member_list import MemberList
from app.model.race import Race
from app.model.sail_entry import SailEntry, SailResolver
from app.model.sailor import Sailor

DF65 = BoatClass("df65", "DF65", "65", "#")
DF95 = BoatClass("df95", "DF95", "95", "@")
VIC = BoatClass("victoria", "Victoria", "Va", "*")

ANN65 = Sailor("   12", "DF65", "Ann", "Smith", "RMBC")
ANN95 = Sailor("   12", "DF95", "Ann", "Smith", "RMBC")             # Ann's other boat, also 12
GALE = Sailor("   29", "DF95", "Paul", "Gale", "RMBC", "PAG")
GRUNDY = Sailor("   29", "VICTORIA", "Paul", "Grundy", "RMBC", "PGU")
BOB = Sailor("   07", "DF65", "Bob", "Jones", "RMBC")
CAT = Sailor("   12", "victoria", "Cat", "Brown", "RMBC")             # file names a class by its key
DAN = Sailor("   05", "DF65", "Dan", "Moor", "Other club")
MEMBERS = MemberList([ANN65, ANN95, GALE, GRUNDY, BOB, CAT, DAN])


def resolver(*classes: BoatClass, clubs=None) -> SailResolver:
    return SailResolver(MEMBERS, list(classes or (DF65, DF95, VIC)), clubs)


class ParseTests(unittest.TestCase):
    def test_parse(self):
        r = resolver()
        self.assertEqual(r.parse(" 12 "), SailEntry("12"))
        self.assertEqual(r.parse("12#"), SailEntry("12", "#"))
        self.assertEqual(r.parse("29/pag"), SailEntry("29", "", "PAG"))
        self.assertEqual(r.parse("12@ / as"), SailEntry("12", "@", "AS"))
        self.assertEqual(r.parse("X$"), SailEntry("X$"))          # $ is no eligible class's symbol
        self.assertEqual(SailEntry("12", "@", "AS").text, "12@/AS")


class CandidateTests(unittest.TestCase):
    def test_one_eligible_sailor(self):
        self.assertEqual(resolver().sailor("7"), BOB)
        self.assertEqual(resolver().sailor("007"), BOB)
        self.assertIsNone(resolver(DF95).sailor("7"))               # Bob is DF65 only

    def test_class_given_by_key_in_the_sailors_file(self):
        self.assertEqual(resolver(VIC).sailor("12"), CAT)
        self.assertEqual(resolver().class_name(CAT), "Victoria")

    def test_ambiguous_until_tagged(self):
        r = resolver()
        self.assertEqual(r.candidates("12"), [ANN65, ANN95, CAT])
        self.assertIsNone(r.sailor("12"))
        self.assertEqual(r.sailor("12#"), ANN65)
        self.assertEqual(r.sailor("12*"), CAT)
        self.assertEqual(r.sailor("29/PAG"), GALE)
        self.assertEqual(r.sailor("29/pgu"), GRUNDY)
        self.assertEqual(r.candidates("29/XX"), [])

    def test_clubs(self):
        self.assertEqual(resolver(clubs=["RMBC"]).candidates("5"), [])
        self.assertEqual(resolver().sailor("5"), DAN)


class ChoiceTests(unittest.TestCase):
    def test_different_sailors_get_a_sailor_tag(self):
        self.assertEqual(resolver().choices("29"), [("29/PAG", GALE), ("29/PGU", GRUNDY)])

    def test_the_same_sailor_gets_a_class_tag(self):
        self.assertEqual(resolver(DF65, DF95).choices("12"), [("12#", ANN65), ("12@", ANN95)])

    def test_mixed_choices_get_what_tells_them_apart(self):
        # Ann has 12 in DF65 and DF95 (tag AS for both), Cat has 12 in Victoria (CB)
        self.assertEqual(resolver().choices("12"), [("12#", ANN65), ("12@", ANN95), ("12/CB", CAT)])

    def test_no_choices_when_not_ambiguous(self):
        self.assertEqual(resolver().choices("7"), [])
        self.assertEqual(resolver().choices("12#"), [])
        self.assertEqual(resolver().choices("99"), [])

    def test_a_class_without_a_symbol_cannot_be_tagged(self):
        plain65, plain95 = BoatClass("df65", "DF65"), BoatClass("df95", "DF95")
        self.assertEqual(resolver(plain65, plain95).choices("12"), [("", ANN65), ("", ANN95)])


class CheckRacesTests(unittest.TestCase):
    def test_problems(self):
        races = [Race("A", ["7", "99", "12", "012#", "29/PAG"]), Race("B", ["12*", "", "7"])]
        problems = resolver().check_races(races)
        self.assertEqual([(r, c) for r, c, _ in problems], [(1, 0), (2, 0)])
        self.assertIn("Unrecognised sail '99'", problems[0][2])
        self.assertIn("Choose which", problems[1][2])

    def test_same_boat_twice(self):
        problems = resolver().check_races([Race("A", ["12#", "012#"])])
        self.assertEqual(problems, [(1, 0, "Sail '012#' is already in row 1 of this race.")])

    def test_same_sailor_in_two_boats(self):
        problems = resolver().check_races([Race("A", ["12#", "7", "12@"])])
        self.assertEqual(problems, [(2, 0, "Ann Smith is already sailing 12# in row 1 of this race.")])

    def test_unrecognised_names_the_classes_and_clubs(self):
        problems = resolver(DF65, clubs=["RMBC"]).check_races([Race("A", ["5"])])
        self.assertIn("no DF65 sailor from RMBC has it", problems[0][2])

    def test_no_members_no_checks(self):
        self.assertEqual(SailResolver(None, [DF65]).check_races([Race("A", ["99"])]), [])


if __name__ == "__main__":
    unittest.main()
