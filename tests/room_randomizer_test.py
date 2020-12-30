from unittest import TestCase

from donjuan import (
    AlphaNumRoomName,
    Cell,
    Dungeon,
    DungeonRoomRandomizer,
    HexGrid,
    Room,
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


class AlphaNumRoomNameTest(RandomizerTestCase):
    def test_names(self):
        rr = AlphaNumRoomName()
        room = Room()
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


class RoomPositionRandomizerTest(RandomizerTestCase):
    def test_randomize_room_position(self):
        # Make a 1x1 room. try moving it around.
        rr = RoomPositionRandomizer()
        rr.seed(123)
        cells = [[SquareCell()]]
        room = Room(cells=cells)
        assert room.cells[0][0].coordinates == (0, 0)
        # Try moving it. 5% chance this fails if the seed is not set
        # Works with seed 123
        rr.randomize_room_position(room, self.dungeon)
        assert room.cells[0][0].coordinates != (0, 0)


class RoomSizeRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = RoomSizeRandomizer()
        assert rng is not None
        assert rng.min_size == 2
        assert rng.max_size == 4
        assert issubclass(rng.cell_type, Cell)

    def test_randomize_room(self):
        room = Room()
        assert room.cells == [[]]
        rng = RoomSizeRandomizer()
        rng.randomize_room_size(room)
        assert len(room.cells) >= rng.min_size
        assert len(room.cells) <= rng.max_size
        assert len(room.cells[0]) >= rng.min_size
        assert len(room.cells[0]) <= rng.max_size
        assert isinstance(room.cells[0][0], Cell)
        assert not room.cells[0][0].filled


class DungeonRoomRandomizerTest(RandomizerTestCase):
    def test_smoke(self):
        rng = DungeonRoomRandomizer()
        assert rng.max_room_attempts == 100

    def test_get_number_of_rooms(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(room_size_randomizer=rr)
        assert rng.get_number_of_rooms(4, 4) == 4
        assert rng.get_number_of_rooms(5, 4) == 5
        assert rng.get_number_of_rooms(5, 5) == 6

    def test_get_number_of_rooms_preset(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(max_num_rooms=3, room_size_randomizer=rr)
        assert rng.get_number_of_rooms(4, 4) == 3
        assert rng.get_number_of_rooms(5, 4) == 3
        assert rng.get_number_of_rooms(5, 5) == 3

    def test_randomize_dungeon_one_room_max(self):
        rng = DungeonRoomRandomizer()
        rng.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.rooms) == 1
        assert "A0" in self.dungeon.rooms

    def test_randomize_dungeon_up_to_five_rooms(self):
        rr = RoomSizeRandomizer(max_size=2)
        rng = DungeonRoomRandomizer(room_size_randomizer=rr)
        rng.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.rooms) <= 5
        assert len(self.dungeon.rooms) > 0
