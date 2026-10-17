import unittest

from app.model.limits import MAX_PLACES
from app.ui.grid_navigation import next_cell_position, previous_cell_position


class NextCellTests(unittest.TestCase):
    def test_moves_down_the_column(self):
        self.assertEqual(next_cell_position(0, 2, 5, 4), (1, 2, False))

    def test_adds_a_row_at_the_bottom_while_growth_is_allowed(self):
        self.assertEqual(next_cell_position(4, 1, 5, 4), (5, 1, True))

    def test_wraps_to_next_column_when_table_is_full(self):
        self.assertEqual(next_cell_position(MAX_PLACES - 1, 1, MAX_PLACES, 4), (0, 2, False))

    def test_wraps_from_last_column_to_first(self):
        self.assertEqual(next_cell_position(MAX_PLACES - 1, 3, MAX_PLACES, 4), (0, 0, False))


class PreviousCellTests(unittest.TestCase):
    def test_up_the_column(self):
        self.assertEqual(previous_cell_position(3, 1, 5, 4), (2, 1))

    def test_wraps_to_bottom_of_previous_column(self):
        self.assertEqual(previous_cell_position(0, 2, 5, 4), (4, 1))

    def test_wraps_from_first_column_to_last(self):
        self.assertEqual(previous_cell_position(0, 0, 5, 4), (4, 3))


if __name__ == "__main__":
    unittest.main()
