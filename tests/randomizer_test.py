from unittest import TestCase

from donjuan import (
    Cell,
    Dungeon,
    DungeonRoomRandomizer,
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
        self.dungeon = Dungeon(grid=self.grid)


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
        assert rng.min_size == 2
        assert rng.max_size == 4
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


class DungeonRoomRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = DungeonRoomRandomizer()
        assert len(rng.room_randomizers) == 1
        assert rng.max_room_attempts == 100

    def test_get_number_of_rooms(self):
        rr = RoomRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(room_randomizers=[rr])
        assert rng.get_number_of_rooms(4, 4) == 4
        assert rng.get_number_of_rooms(5, 4) == 5
        assert rng.get_number_of_rooms(5, 5) == 6

    def test_get_number_of_rooms_preset(self):
        rr = RoomRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(max_num_rooms=3, room_randomizers=[rr])
        assert rng.get_number_of_rooms(4, 4) == 3
        assert rng.get_number_of_rooms(5, 4) == 3
        assert rng.get_number_of_rooms(5, 5) == 3

    def test_randomize_dungeon_one_room_max(self):
        rng = DungeonRoomRandomizer()
        rng.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.rooms) == 1
        assert "0" in self.dungeon.rooms

    def test_randomize_dungeon_up_to_five_rooms(self):
        rr = RoomRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(room_randomizers=[rr])
        rng.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.rooms) <= 5
        for i, k in enumerate(self.dungeon.rooms.keys()):
            assert str(i) == k


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
