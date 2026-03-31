from unittest import TestCase

from donjuan import (
    Dungeon,
    DungeonRandomizer,
    Hallway,
    HallwayRandomizer,
    Room,
    SquareCell,
    SquareGrid,
)
from donjuan.randomizer import Randomizer
from donjuan.room_randomizer import RoomSizeRandomizer


class HallwayRandomizerTestCase(TestCase):
    _room_counter = 0

    def setUp(self):
        super().setUp()
        HallwayRandomizerTestCase._room_counter = 0
        self.grid = SquareGrid(n_rows=10, n_cols=10)
        self.dungeon = Dungeon(grid=self.grid)

    def _make_room(self, top_left_y, top_left_x, height, width):
        """Helper: create a room at a known position with a unique name."""
        HallwayRandomizerTestCase._room_counter += 1
        cells = set(
            SquareCell(filled=False, coordinates=(top_left_y + dy, top_left_x + dx))
            for dy in range(height)
            for dx in range(width)
        )
        room = Room(cells=cells, name=f"R{HallwayRandomizerTestCase._room_counter}")
        return room


class HallwayRandomizerTest(HallwayRandomizerTestCase):
    def test_smoke(self):
        hr = HallwayRandomizer()
        assert hr is not None
        assert hr.hallway_name_prefix == "H"
        assert hr.max_hallway_attempts == 50

    def test_custom_args(self):
        hr = HallwayRandomizer(hallway_name_prefix="X", max_hallway_attempts=10)
        assert hr.hallway_name_prefix == "X"
        assert hr.max_hallway_attempts == 10

    def test_randomize_dungeon_no_rooms(self):
        hr = HallwayRandomizer()
        hr.randomize_dungeon(self.dungeon)
        assert self.dungeon.hallways == {}

    def test_randomize_dungeon_one_room(self):
        hr = HallwayRandomizer()
        room = self._make_room(0, 0, 2, 2)
        self.dungeon.add_room(room)
        self.dungeon.emplace_space(room)
        hr.randomize_dungeon(self.dungeon)
        assert self.dungeon.hallways == {}

    def test_randomize_dungeon_two_rooms_creates_hallway(self):
        hr = HallwayRandomizer()
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(7, 7, 2, 2)
        self.dungeon.add_room(room_a)
        self.dungeon.add_room(room_b)
        self.dungeon.emplace_space(room_a)
        self.dungeon.emplace_space(room_b)
        hr.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.hallways) == 1

    def test_hallway_has_cells(self):
        hr = HallwayRandomizer()
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(7, 7, 2, 2)
        self.dungeon.add_room(room_a)
        self.dungeon.add_room(room_b)
        self.dungeon.emplace_space(room_a)
        self.dungeon.emplace_space(room_b)
        hr.randomize_dungeon(self.dungeon)
        hallway = list(self.dungeon.hallways.values())[0]
        assert len(hallway.cells) > 0

    def test_hallway_cells_unfilled(self):
        hr = HallwayRandomizer()
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(7, 7, 2, 2)
        self.dungeon.add_room(room_a)
        self.dungeon.add_room(room_b)
        self.dungeon.emplace_space(room_a)
        self.dungeon.emplace_space(room_b)
        hr.randomize_dungeon(self.dungeon)
        for hallway in self.dungeon.hallways.values():
            for cell in hallway.cells:
                assert not cell.filled

    def test_hallway_cells_in_grid(self):
        hr = HallwayRandomizer()
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(7, 7, 2, 2)
        self.dungeon.add_room(room_a)
        self.dungeon.add_room(room_b)
        self.dungeon.emplace_space(room_a)
        self.dungeon.emplace_space(room_b)
        hr.randomize_dungeon(self.dungeon)
        for hallway in self.dungeon.hallways.values():
            for cell in hallway.cells:
                assert self.dungeon.grid.cells[cell.y][cell.x] is cell

    def test_hallway_name_prefix(self):
        hr = HallwayRandomizer(hallway_name_prefix="Z")
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(7, 7, 2, 2)
        self.dungeon.add_room(room_a)
        self.dungeon.add_room(room_b)
        self.dungeon.emplace_space(room_a)
        self.dungeon.emplace_space(room_b)
        hr.randomize_dungeon(self.dungeon)
        for name in self.dungeon.hallways:
            assert name.startswith("Z")

    def test_three_rooms_two_hallways(self):
        hr = HallwayRandomizer()
        room_a = self._make_room(0, 0, 2, 2)
        room_b = self._make_room(0, 7, 2, 2)
        room_c = self._make_room(7, 0, 2, 2)
        for room in (room_a, room_b, room_c):
            self.dungeon.add_room(room)
            self.dungeon.emplace_space(room)
        hr.randomize_dungeon(self.dungeon)
        assert len(self.dungeon.hallways) == 2


class HallwayRandomizerHelperTest(HallwayRandomizerTestCase):
    def setUp(self):
        super().setUp()
        self.hr = HallwayRandomizer()

    def test_room_center(self):
        # 2x2 room at (2, 4): center should be (2, 4) (integer division)
        room = self._make_room(2, 4, 2, 2)
        cy, cx = self.hr._room_center(room)
        assert cy == 2
        assert cx == 4

    def test_room_center_larger(self):
        # 4x4 room at (0, 0): center is (1, 1)
        room = self._make_room(0, 0, 4, 4)
        cy, cx = self.hr._room_center(room)
        assert cy == 1
        assert cx == 1

    def test_bfs_path_exists(self):
        path = self.hr._bfs_path(self.dungeon, (0, 0), (9, 9))
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)

    def test_bfs_path_same_start_end(self):
        path = self.hr._bfs_path(self.dungeon, (3, 3), (3, 3))
        assert path == [(3, 3)]

    def test_bfs_path_manhattan_length(self):
        # On an empty grid with no obstacles, BFS should return the
        # Manhattan-distance-optimal path (length = |dy|+|dx|+1)
        path = self.hr._bfs_path(self.dungeon, (0, 0), (0, 5))
        assert path is not None
        assert len(path) == 6  # 5 steps + start cell

    def test_bfs_path_all_coords_in_grid(self):
        path = self.hr._bfs_path(self.dungeon, (1, 1), (8, 8))
        assert path is not None
        for y, x in path:
            assert 0 <= y < self.dungeon.n_rows
            assert 0 <= x < self.dungeon.n_cols

    def test_spanning_tree_length(self):
        rooms = [self._make_room(0, 0, 2, 2),
                 self._make_room(0, 5, 2, 2),
                 self._make_room(5, 0, 2, 2)]
        for r in rooms:
            self.dungeon.add_room(r)
        pairs = self.hr._build_spanning_tree(rooms)
        assert len(pairs) == 2  # N-1 for N=3

    def test_spanning_tree_covers_all_rooms(self):
        rooms = [self._make_room(0, 0, 2, 2),
                 self._make_room(0, 5, 2, 2),
                 self._make_room(5, 0, 2, 2),
                 self._make_room(5, 7, 2, 2)]
        for r in rooms:
            self.dungeon.add_room(r)
        pairs = self.hr._build_spanning_tree(rooms)
        all_rooms_in_pairs = set()
        for a, b in pairs:
            all_rooms_in_pairs.add(a.name)
            all_rooms_in_pairs.add(b.name)
        for room in rooms:
            assert room.name in all_rooms_in_pairs

    def test_open_hallway_connections_sets_has_door(self):
        """Edges between hallway cells and adjacent room cells get has_door=True."""
        room = self._make_room(0, 0, 2, 2)
        self.dungeon.add_room(room)
        self.dungeon.emplace_space(room)

        # Manually carve a 1-cell hallway adjacent to the room
        path = self.hr._bfs_path(self.dungeon, (0, 2), (0, 2))
        hallway = self.hr._carve_hallway(self.dungeon, path, "test")
        self.hr._open_hallway_connections(self.dungeon, hallway)

        # The edge between (0,2) and (0,1) (a room cell) should have a door
        hallway_cell = self.dungeon.grid.cells[0][2]
        room_cell = self.dungeon.grid.cells[0][1]
        shared_edge = None
        for edge in hallway_cell.edges:
            if edge is not None and (edge.cell1 is room_cell or edge.cell2 is room_cell):
                shared_edge = edge
                break
        assert shared_edge is not None
        assert shared_edge.has_door is True


class DungeonRandomizerHallwayIntegrationTest(TestCase):
    def test_randomize_dungeon_creates_hallways(self):
        Randomizer.seed(42)
        grid = SquareGrid(n_rows=20, n_cols=20)
        dungeon = Dungeon(grid=grid)
        dr = DungeonRandomizer(room_size_randomizer=RoomSizeRandomizer(max_size=3))
        dr.randomize_dungeon(dungeon)
        assert len(dungeon.hallways) >= 1

    def test_custom_hallway_randomizer_prefix(self):
        Randomizer.seed(0)
        grid = SquareGrid(n_rows=20, n_cols=20)
        dungeon = Dungeon(grid=grid)
        hr = HallwayRandomizer(hallway_name_prefix="X")
        dr = DungeonRandomizer(
            room_size_randomizer=RoomSizeRandomizer(max_size=3),
            hallway_randomizer=hr,
        )
        dr.randomize_dungeon(dungeon)
        for name in dungeon.hallways:
            assert name.startswith("X")

    def test_noop_hallway_randomizer_skips_hallways(self):
        Randomizer.seed(1)
        grid = SquareGrid(n_rows=20, n_cols=20)
        dungeon = Dungeon(grid=grid)

        class NoOpRandomizer(Randomizer):
            def randomize_dungeon(self, dungeon):
                pass

        dr = DungeonRandomizer(
            room_size_randomizer=RoomSizeRandomizer(max_size=3),
            hallway_randomizer=NoOpRandomizer(),
        )
        dr.randomize_dungeon(dungeon)
        assert dungeon.hallways == {}
