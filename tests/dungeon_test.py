from unittest import TestCase

from donjuan import Dungeon, HexGrid, Room, SquareGrid


class DungeonTest(TestCase):
    def test_smoke(self):
        d = Dungeon()
        assert d is not None
        assert d.grid is not None
        assert d.randomizers == []

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
