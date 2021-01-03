from unittest import TestCase

from donjuan import Hallway, SquareCell


class HallwayTest(TestCase):
    def setUp(self):
        super().setUp()
        self.cells = [SquareCell() for _ in range(3)]

    def test_smoke(self):
        h = Hallway()
        assert h is not None
        assert h.name == ""

    def test_cells_ordered(self):
        h = Hallway(self.cells)
        assert h.start_cell is self.cells[0]
        assert h.end_cell is self.cells[-1]
        assert len(h.ordered_cells) == 3
        assert len(h.cells) == 3
        for cell in h.ordered_cells:
            assert cell in h.cells

    def test_get_coordinate_path(self):
        cells = [SquareCell(coordinates=(i, 0)) for i in range(10)]
        h = Hallway(cells)
        for i, coords in enumerate(h.get_coordinate_path()):
            assert coords == (i, 0)
