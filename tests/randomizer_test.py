from unittest import TestCase

from donjuan import Dungeon, HexGrid, RandomFilled, Randomizer, SquareGrid


class RandomizerTestCase(TestCase):
    def setUp(self):
        self.grid = SquareGrid(n_rows=4, n_cols=5)
        self.hexgrid = HexGrid(n_rows=4, n_cols=5)
        self.dungeon = Dungeon(grid=self.grid)


class RandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = Randomizer()
        assert rng is not None

    def test_seed_passes(self):
        Randomizer.seed(0)


class RandomFilledTest(RandomizerTestCase):
    def test_smoke(self):
        rng = RandomFilled()
        assert rng is not None

    def test_filled(self):
        rng = RandomFilled()
        rng.seed(12345)
        grid = self.grid
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                assert grid.cells[i][j].filled
        rng.randomize_grid(grid)
        # Test that at least one cell became filled
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                if grid.cells[i][j].filled:
                    break
        assert grid.cells[i][j].filled

    def test_filled_hex(self):
        rng = RandomFilled()
        rng.seed(12345)
        grid = self.hexgrid
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                assert grid.cells[i][j].filled
        rng.randomize_grid(grid)
        # Test that at least one cell became filled
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                if grid.cells[i][j].filled:
                    break
        assert grid.cells[i][j].filled
