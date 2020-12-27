from copy import deepcopy
from unittest import TestCase

from donjuan import Room, SquareCell


class RoomTest(TestCase):
    def test_smoke(self):
        r = Room()
        assert r is not None
        assert r.cells == [[]]

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
