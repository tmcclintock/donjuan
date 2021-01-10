from unittest import TestCase

from donjuan import Edge, HexCell, SquareCell


class SquareCellTest(TestCase):
    def test_smoke(self):
        c = SquareCell()
        assert c is not None

    def test_space(self):
        c = SquareCell()
        assert c.space is None

    def test_edges(self):
        c = SquareCell()
        assert c.edges == [None] * c.n_sides
        edges = [Edge() for i in range(4)]
        c.set_edges(edges)
        assert c.edges is edges

    def test_filled(self):
        c = SquareCell()
        assert not c.filled
        c.filled = True
        assert c.filled

    def test_n_sides(self):
        c = SquareCell()
        assert c.n_sides == 4

    def test_coordinates(self):
        c = SquareCell()
        assert c.coordinates == (0, 0)
        c.set_coordinates(1, 2)
        assert c.coordinates == (1, 2)
        assert c.x == 2
        assert c.y == 1


class HexCellTest(TestCase):
    def test_smoke(self):
        c = HexCell()
        assert c is not None

    def test_n_sides(self):
        c = HexCell()
        assert c.n_sides == 6

    def test_coordinates(self):
        c = HexCell()
        assert c.coordinates == (0, 0)
        c.set_coordinates(1, 2)
        assert c.coordinates == (1, 2)
        assert c.x == 2
        assert c.y == 1
