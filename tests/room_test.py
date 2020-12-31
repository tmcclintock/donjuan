from copy import deepcopy
from unittest import TestCase

from donjuan import Room, SquareCell


class RoomTest(TestCase):
    def setUp(self):
        super().setUp()
        self.cells = set(
            SquareCell(coordinates=(i, j)) for j in range(5) for i in range(4)
        )

    def test_smoke(self):
        r = Room()
        assert r is not None
        assert r.cells == set()
        assert r.cell_coordinates == set()
        assert r.name == ""

    def test_name(self):
        r = Room(name="testroom")
        assert r.name == "testroom"
        r = Room(name=12)
        assert r.name == "12"

    def test_set_name(self):
        r = Room()
        r.set_name("catdog")
        assert r.name == "catdog"

    def test_insert_cell_list(self):
        r = Room()
        assert len(r.cells) == 0
        r.insert_cell_list([SquareCell()])
        assert len(r.cells) == 1
        assert len(r.cell_coordinates) == 1
        assert r.cell_coordinates == set(((0, 0),))

    def test_shift_vertical(self):
        r = Room(self.cells)
        r.shift_vertical(100)
        for cell in r.cells:
            assert cell.coordinates[0] >= 100, cell.coordinates
        for i in range(4):
            for j in range(5):
                assert (i + 100, j) in r.cell_coordinates

    def test_shift_vertical_one_row(self):
        r = Room(self.cells)
        r.shift_vertical(1)
        for i in range(4):
            for j in range(5):
                assert (i + 1, j) in r.cell_coordinates

    def test_shift_horizontal(self):
        r = Room(self.cells)
        r.shift_horizontal(100)
        for cell in r.cells:
            assert cell.coordinates[1] >= 100, cell.coordinates
        for i in range(4):
            for j in range(5):
                assert (i, j + 100) in r.cell_coordinates

    def test_shift_horizontal_one_col(self):
        r = Room(self.cells)
        r.shift_horizontal(1)
        for i in range(4):
            for j in range(5):
                assert (i, j + 1) in r.cell_coordinates

    def test_overlaps(self):
        r1 = Room(self.cells)
        r2 = Room(deepcopy(self.cells))
        assert r1.overlaps(r2)

    def test_no_overlap(self):
        r1 = Room(self.cells)
        cs2 = deepcopy(self.cells)
        r2 = Room(cs2)
        r2.shift_vertical(100)
        assert not r1.overlaps(r2)
