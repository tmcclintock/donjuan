from unittest import TestCase

from donjuan import Dungeon, HexGrid, Room, SquareCell, SquareGrid


class DungeonTest(TestCase):
    def test_smoke(self):
        d = Dungeon()
        assert d is not None
        assert d.grid is not None
        assert d.randomizers == []

    def test_randomize(self):
        class FakeRandomizer:
            def randomize_dungeon(self, dungeon: Dungeon):
                # set a dummy attribute
                setattr(dungeon, "dummy", True)
                return

        rng = FakeRandomizer()
        d = Dungeon(randomizers=[rng])
        assert not hasattr(d, "dummy")
        d.randomize()
        assert hasattr(d, "dummy")
        assert d.dummy is True

    def test_initial_attributes(self):
        d = Dungeon()
        assert d.rooms == {}

    def test_add_room(self):
        r = Room(name="blah")
        d = Dungeon()
        d.add_room(r)
        assert d.rooms["blah"] == r

    def test_hex_grid(self):
        hg = HexGrid(4, 5)
        d = Dungeon(grid=hg)
        assert isinstance(d.grid, HexGrid)
        assert d.n_rows == 4
        assert d.n_cols == 5

    def test_pass_dimensions(self):
        d = Dungeon(n_rows=4, n_cols=5)
        assert d.n_rows == 4
        assert d.n_cols == 5

    def test_pass_grid(self):
        grid = SquareGrid(3, 4)
        d = Dungeon(grid=grid)
        assert d.n_rows == 3
        assert d.n_cols == 4

    def test_emplace_space(self):
        grid = SquareGrid(3, 4)
        d = Dungeon(grid=grid)
        cs = set([SquareCell(filled=False, coordinates=(1, 2))])
        room = Room(cells=cs)
        d.emplace_space(room)
        for i in range(d.n_rows):
            for j in range(d.n_cols):
                if i == 1 and j == 2:
                    assert not d.grid.cells[i][j].filled
                else:
                    assert d.grid.cells[i][j].filled, f"({i}, {j})"

    def test_emplace_rooms(self):
        grid = SquareGrid(3, 4)
        cs = set([SquareCell(filled=False, coordinates=(1, 2))])
        room = Room(cells=cs)
        d = Dungeon(grid=grid, rooms={"0": room})
        d.emplace_rooms()
        for i in range(d.n_rows):
            for j in range(d.n_cols):
                if i == 1 and j == 2:
                    assert not d.grid.cells[i][j].filled
                else:
                    assert d.grid.cells[i][j].filled, f"({i}, {j})"
