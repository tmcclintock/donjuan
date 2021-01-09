from unittest import TestCase

from donjuan import (
    AlphaNumRoomName,
    Cell,
    Dungeon,
    DungeonRandomizer,
    HexGrid,
    Room,
    RoomEntrancesRandomizer,
    RoomPositionRandomizer,
    RoomSizeRandomizer,
    SquareCell,
    SquareGrid,
)


class RandomizerTestCase(TestCase):
    def setUp(self):
        self.grid = SquareGrid(n_rows=4, n_cols=5)
        self.hexgrid = HexGrid(n_rows=4, n_cols=5)
        self.dungeon = Dungeon(grid=self.grid)
        self.room = Room(cells=set([SquareCell()]))


class AlphaNumRoomNameTest(RandomizerTestCase):
    def test_names(self):
        rr = AlphaNumRoomName()
        room = self.room
        rr.randomize_room_name(room)
        assert room.name == "A0"
        rr.randomize_room_name(room)
        assert room.name == "B0"
        rr.randomize_room_name(room)
        assert room.name == "C0"
        for i in range(23):
            rr.randomize_room_name(room)
        assert room.name == "Z0"
        rr.randomize_room_name(room)
        assert room.name == "A1"
        rr.randomize_room_name(room)
        assert room.name == "B1"
        rr.randomize_room_name(room)
        assert room.name == "C1"


class RoomEntrancesRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rr = RoomEntrancesRandomizer()
        assert rr is not None

    def test_gen_num_entrances(self):
        rr = RoomEntrancesRandomizer()
        cells = set([SquareCell() for _ in range(16)])  # 4x4 room
        # Make many draws of entrance numbers
        n = [rr.gen_num_entrances(cells) for _ in range(1000)]
        assert min(n) == 3
        assert max(n) == 6

    def test_randomize_room_entrances(self):
        rr = RoomEntrancesRandomizer()
        # Room in the top left corner
        cell_list = [
            SquareCell(coordinates=(0, 0)),
            SquareCell(coordinates=(0, 1)),
            SquareCell(coordinates=(1, 0)),
            SquareCell(coordinates=(1, 1)),
        ]
        cells = set(cell_list)
        room = Room(cells=cells)
        self.dungeon.emplace_space(room)
        # double check emplace is working
        for ind, cell in enumerate(cell_list):
            i = ind // 2
            j = ind % 2
            assert cell.y == i
            assert cell.x == j
            assert cell.edges is not None
            assert cell in cells
            assert cell is self.dungeon.grid.cells[i][j]
        rr.randomize_room_entrances(room, self.dungeon)


class RoomPositionRandomizerTest(RandomizerTestCase):
    def test_randomize_room_position(self):
        # Make a 1x1 room. try moving it around.
        rr = RoomPositionRandomizer()
        rr.seed(123)
        room = self.room
        assert (0, 0) in room.cell_coordinates
        # Try moving it. 5% chance this fails if the seed is not set
        # Works with seed 123
        rr.randomize_room_position(room, self.dungeon)
        assert (0, 0) not in room.cell_coordinates


class RoomSizeRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = RoomSizeRandomizer()
        assert rng is not None
        assert rng.min_size == 2
        assert rng.max_size == 4
        assert issubclass(rng.cell_type, Cell)

    def test_randomize_room_size(self):
        room = Room()
        assert room.cells == set()
        rng = RoomSizeRandomizer()
        rng.randomize_room_size(room)
        assert len(room.cells) >= rng.min_size ** 2
        assert len(room.cells) <= rng.max_size ** 2
        for cell in room.cells:
            assert not cell.filled


class DungeonRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = DungeonRandomizer()
        assert rng.max_room_attempts == 100

    def test_get_number_of_rooms(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRandomizer(room_size_randomizer=rr)
        assert rng.get_number_of_rooms(4, 4) == 4
        assert rng.get_number_of_rooms(5, 4) == 5
        assert rng.get_number_of_rooms(5, 5) == 6

    def test_get_number_of_rooms_preset(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRandomizer(max_num_rooms=3, room_size_randomizer=rr)
        assert rng.get_number_of_rooms(4, 4) == 3
        assert rng.get_number_of_rooms(5, 4) == 3
        assert rng.get_number_of_rooms(5, 5) == 3

    def test_randomize_dungeon_one_room_max(self):
        rng = DungeonRandomizer()
        rng.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.rooms) == 1
        assert "A0" in self.dungeon.rooms

    def test_randomize_dungeon_up_to_five_rooms(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRandomizer(room_size_randomizer=rr)
        rng.randomize_dungeon(self.dungeon)  # dungeon is 4x5
        assert len(self.dungeon.rooms) <= 5
        assert len(self.dungeon.rooms) > 0
