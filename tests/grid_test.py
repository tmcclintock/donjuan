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

    def test_edge_grid(self):
        sg = SquareGrid(5, 4)
        assert len(sg.edges) == 2
        h, v = sg.edges
        assert len(h) == sg.n_rows + 1
        assert len(h[0]) == sg.n_cols
        assert len(v) == sg.n_rows
        assert len(v[0]) == sg.n_cols + 1
        assert h[0][0].cell1 is None
        assert h[0][0].cell2 is sg.cells[0][0]
        assert v[0][0].cell1 is None
        assert v[0][0].cell2 is sg.cells[0][0]
        assert h[-1][-1].cell1 is sg.cells[-1][-1]
        assert h[-1][-1].cell2 is None
        assert v[-1][-1].cell1 is sg.cells[-1][-1]
        assert v[-1][-1].cell2 is None

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

    def test_edge_grid(self):
        gg = HexGrid(5, 4)
        assert len(gg.edges) == 3
        h = gg.edges[0]
        assert len(h) == gg.n_rows + 1
        assert len(h[0]) == gg.n_cols
        for v in gg.edges[1:]:
            assert len(v) == gg.n_rows
            assert len(v[0]) == gg.n_cols + 1
            assert v[0][0].cell1 is None
            assert v[0][0].cell2 is gg.cells[0][0]
            assert v[-1][-1].cell1 is gg.cells[-1][-1]
            assert v[-1][-1].cell2 is None
        assert h[0][0].cell1 is None
        assert h[0][0].cell2 is gg.cells[0][0]
        assert h[-1][-1].cell1 is gg.cells[-1][-1]
        assert h[-1][-1].cell2 is None
