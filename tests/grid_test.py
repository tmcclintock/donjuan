import json
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

    def test_from_cells(self):
        cells = [[SquareCell() for i in range(4)] for j in range(5)]
        sg = SquareGrid.from_cells(cells)
        assert sg.n_cols == 4
        assert sg.n_rows == 5
        assert isinstance(sg.cells[0][0], SquareCell)

    def test_get_filled_grid(self):
        sg = SquareGrid(5, 5)
        fg = sg.get_filled_grid()
        assert all(fg)

    def test_get_filled_grid_some_unfilled(self):
        sg = SquareGrid(5, 5)
        for i in range(5):
            sg.cells[i][3].filled = True
        fg = sg.get_filled_grid()
        for i in range(5):
            for j in range(5):
                assert fg[i][j] == sg.cells[i][j].filled, (i, j)
                if j != 3:
                    assert not fg[i][j], (i, j)
                else:
                    assert fg[i][j], (i, j)

    def test_find_walls(self):
        input_path = "tests/fixtures/dummy_dungeon.json"
        with open(input_path, "r") as f:
            dungeon_array = json.load(f)["dungeon"]
        dungeon_walls = [
            ((2, 0), (2, 4), "vertical"),
            ((3, 0), (3, 1), "vertical"),
            ((4, 1), (4, 1), "horizontal"),
            ((4, 2), (4, 2), "horizontal"),
            ((3, 3), (3, 4), "vertical"),
        ]
        n_rows = len(dungeon_array)
        n_cols = len(dungeon_array)
        grid = SquareGrid(n_rows=n_rows, n_cols=n_cols)
        for i in range(n_rows):
            for j in range(n_cols):
                grid.cells[i][j].filled = bool(dungeon_array[i][j])
        assert grid.find_walls() == dungeon_walls


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

    def test_from_cells(self):
        cells = [[HexCell() for i in range(4)] for j in range(5)]
        hg = HexGrid.from_cells(cells)
        assert hg.n_cols == 4
        assert hg.n_rows == 5
        assert isinstance(hg.cells[0][0], HexCell)
