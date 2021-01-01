from unittest import TestCase

from donjuan import Edge, SquareCell


class EdgeTest(TestCase):
    def setUp(self):
        super().setUp()
        # Make two cells separated horizontally
        self.cell1 = SquareCell(coordinates=(0, 0), filled=True)
        self.cell2 = SquareCell(coordinates=(0, 1), filled=False)

    def test_smoke(self):
        edge = Edge()
        assert edge is not None
        assert edge.cell1 is None
        assert edge.cell2 is None

    def test_cells(self):
        edge = Edge(self.cell1, self.cell2)
        assert isinstance(edge.cell1, SquareCell)
        assert isinstance(edge.cell2, SquareCell)

    def test_set_cell(self):
        edge = Edge()
        edge.set_cell1(self.cell1)
        edge.set_cell2(self.cell2)
        assert isinstance(edge.cell1, SquareCell)
        assert isinstance(edge.cell2, SquareCell)
        assert edge.is_wall
