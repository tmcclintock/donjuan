from copy import deepcopy
from unittest import TestCase

import pytest

from donjuan import Room, SquareCell


class RoomTest(TestCase):
    def test_smoke(self):
        r = Room()
        assert r is not None
        assert r.cells == [[]]

    def test_assert_cell_coords(self):
        c = SquareCell()
        with pytest.raises(AssertionError):
            Room(cells=[[c]])

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
