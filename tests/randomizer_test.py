from unittest import TestCase

from donjuan import (
    Cell,
    HexGrid,
    RandomFilled,
    Randomizer,
    Room,
    RoomRandomizer,
    SquareGrid,
)


class RandomizerTestCase(TestCase):
    def setUp(self):
        self.grid = SquareGrid(n_rows=4, n_cols=5)
        self.hexgrid = HexGrid(n_rows=4, n_cols=5)


class RandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = Randomizer()
        assert rng is not None

    def test_seed_passes(self):
        Randomizer.seed(0)


class RoomRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = RoomRandomizer()
        assert rng is not None
        assert rng.min_size == 3
        assert rng.max_size == 9
        assert issubclass(rng.cell_type, Cell)

    def test_randomize_room(self):
        room = Room()
        assert room.cells == [[]]
        rng = RoomRandomizer()
        rng.randomize_room(room)
        assert len(room.cells) >= rng.min_size
        assert len(room.cells) <= rng.max_size
        assert len(room.cells[0]) >= rng.min_size
        assert len(room.cells[0]) <= rng.max_size
        assert isinstance(room.cells[0][0], Cell)
        assert not room.cells[0][0].filled


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
                assert not grid.cells[i][j].filled
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
                assert not grid.cells[i][j].filled
        rng.randomize_grid(grid)
        # Test that at least one cell became filled
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                if grid.cells[i][j].filled:
                    break
        assert grid.cells[i][j].filled
