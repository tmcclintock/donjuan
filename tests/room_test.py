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
