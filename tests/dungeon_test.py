from unittest import TestCase

from donjuan import Dungeon, SquareGrid


class DungeonTest(TestCase):
    def test_smoke(self):
        d = Dungeon()
        assert d is not None

    def test_pass_dimensions(self):
        d = Dungeon(n_rows=4, n_cols=5)
        assert d.grid.n_rows == 4
        assert d.grid.n_cols == 5

    def test_pass_grid(self):
        grid = SquareGrid(3, 4)
        d = Dungeon(grid=grid)
        assert d.grid.n_rows == 3
        assert d.grid.n_cols == 4
