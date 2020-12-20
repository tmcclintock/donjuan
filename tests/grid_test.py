from unittest import TestCase

from donjuan import HexCell, HexGrid, SquareCell, SquareGrid


class SquareGridTest(TestCase):
    def test_smoke(self):
        sg = SquareGrid(5, 5)
        assert sg is not None

    def test_from_cells(self):
        cells = [[SquareCell() for i in range(5)] for j in range(5)]
        sg = SquareGrid.from_cells(cells)
        assert sg.n_cols == 5
        assert sg.n_rows == 5
        assert isinstance(sg.cells[0][0], SquareCell)


class HexGridTest(TestCase):
    def test_smoke(self):
        hg = HexGrid(5, 5)
        assert hg is not None

    def test_from_cells(self):
        cells = [[HexCell() for i in range(5)] for j in range(5)]
        hg = HexGrid.from_cells(cells)
        assert hg.n_cols == 5
        assert hg.n_rows == 5
        assert isinstance(hg.cells[0][0], HexCell)
