from unittest import TestCase

from donjuan.coordinates import Coordinates


class CoordinatesTest(TestCase):
    def test_smoke(self):
        d = Coordinates()
        assert d is not None
        assert d.x == 0
        assert d.y == 0

    def test_add(self):
        d1 = Coordinates(x=1, y=0)
        d2 = Coordinates(x=0, y=1)
        d3 = d1 + d2
        assert d3.x == 1
        assert d3.y == 1
