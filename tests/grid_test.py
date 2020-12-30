from unittest import TestCase

from donjuan import HexCell, HexGrid, SquareCell, SquareGrid


class SquareGridTest(TestCase):
    def test_smoke(self):
        sg = SquareGrid(5, 4)
        assert sg is not None

    def test_smoke_all_args(self):
        cells = [[SquareCell() for i in range(4)] for j in range(5)]
        sg = SquareGrid(5, 4, cells)
        assert sg is not None

    def test_cell_coordinates(self):
        sg = SquareGrid(5, 4)
        for i in range(sg.n_rows):
            for j in range(sg.n_cols):
                assert sg.cells[i][j].coordinates == (i, j)

    def test_get_filled_grid(self):
        sg = SquareGrid(5, 4)
        fg = sg.get_filled_grid()
        assert all(fg)

    def test_get_filled_grid_some_unfilled(self):
        sg = SquareGrid(5, 4)
        for i in range(5):
            sg.cells[i][3].filled = False
        fg = sg.get_filled_grid()
        for i in range(5):
            for j in range(4):
                assert fg[i][j] == sg.cells[i][j].filled, (i, j)
                if j != 3:
                    assert fg[i][j], (i, j)
                else:
                    assert not fg[i][j], (i, j)

    def test_reset_cell_coordinates(self):
        cells = [[SquareCell() for i in range(4)] for j in range(5)]
        sg = SquareGrid(5, 4, cells)
        for i in range(sg.n_rows):
            for j in range(sg.n_cols):
                assert sg.cells[i][j].coordinates == (0, 0)
        sg.reset_cell_coordinates()
        for i in range(sg.n_rows):
            for j in range(sg.n_cols):
                assert sg.cells[i][j].coordinates == (i, j)


class HexGridTest(TestCase):
    def test_smoke(self):
        hg = HexGrid(5, 4)
        assert hg is not None

    def test_smoke_all_args(self):
        cells = [[HexCell() for i in range(4)] for j in range(5)]
        hg = HexGrid(5, 4, cells)
        assert hg is not None
        assert hg.n_rows == 5
        assert hg.n_cols == 4
