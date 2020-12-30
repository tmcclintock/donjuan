from copy import deepcopy
from unittest import TestCase

from donjuan import Room, SquareCell


class RoomTest(TestCase):
    def test_smoke(self):
        r = Room()
        assert r is not None
        assert r.cells == [[]]
        assert r.name == ""
        assert r.n_rows == 0
        assert r.n_cols == 0

    def test_name(self):
        r = Room(name="testroom")
        assert r.name == "testroom"
        r = Room(name=12)
        assert r.name == "12"

    def test_set_name(self):
        r = Room()
        r.set_name("catdog")
        assert r.name == "catdog"

    def test_set_cells(self):
        cs = [[SquareCell()]]
        r = Room(cells=cs)
        assert r.n_rows == 1
        assert r.n_cols == 1
        cs = [[SquareCell(coordinates=(i, j)) for j in range(3)] for i in range(2)]
        r.set_cells(cs)
        assert r.n_rows == 2
        assert r.n_cols == 3

    def test_shift_vertical(self):
        cs = [[SquareCell(coordinates=(i, j)) for j in range(5)] for i in range(4)]
        r = Room(cs)
        r.shift_vertical(100)
        for i in range(len(cs)):
            for j in range(len(cs[0])):
                assert r.cells[i][j].coordinates == (i + 100, j)

    def test_shift_horizontal(self):
        cs = [[SquareCell(coordinates=(i, j)) for j in range(5)] for i in range(4)]
        r = Room(cs)
        r.shift_horizontal(100)
        for i in range(len(cs)):
            for j in range(len(cs[0])):
                assert r.cells[i][j].coordinates == (i, j + 100)

    def test_overlaps(self):
        cs = [[SquareCell(coordinates=(i, j)) for j in range(5)] for i in range(4)]
        r1 = Room(cs)
        r2 = Room(deepcopy(cs))
        assert r1.overlaps(r2)

    def test_no_overlap(self):
        cs = [[SquareCell(coordinates=(i, j)) for j in range(5)] for i in range(4)]
        r1 = Room(cs)
        cs2 = deepcopy(cs)
        for i in range(len(cs)):
            for j in range(len(cs[0])):
                cs2[i][j].set_coordinates(100 + i, j)
        r2 = Room(cs2)
        assert not r1.overlaps(r2)
