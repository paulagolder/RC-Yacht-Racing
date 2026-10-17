import unittest

from app.model.race import Race, letters, race_name


class RaceNameTests(unittest.TestCase):
    def test_letters(self):
        self.assertEqual([letters(n) for n in (1, 2, 26, 27, 28, 52, 53)],
                         ["A", "B", "Z", "AA", "AB", "AZ", "BA"])

    def test_race_name(self):
        self.assertEqual(race_name(1), "Race A")
        self.assertEqual(race_name(3), "Race C")


class RaceTests(unittest.TestCase):
    def test_finishers_are_text(self):
        self.assertEqual(Race("A", [12, "7"]).finishers, ["12", "7"])

    def test_places_skip_empty_places_but_keep_numbering(self):
        race = Race("A", [" 12 ", "", "  ", "7"])
        self.assertEqual(list(race.places()), [(1, "12"), (4, "7")])

    def test_points_are_the_place(self):
        self.assertEqual([Race.points(p) for p in (1, 2, 15)], [1, 2, 15])


if __name__ == "__main__":
    unittest.main()
