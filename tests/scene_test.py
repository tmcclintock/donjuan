"""Tests for the Scene base class and the Dungeon(Scene) refactor."""
import pytest

from donjuan import Dungeon, Scene
from donjuan.grid import SquareGrid
from donjuan.room import Room
from donjuan.cell import SquareCell


def test_scene_is_base_of_dungeon():
    dungeon = Dungeon(n_rows=5, n_cols=5)
    assert isinstance(dungeon, Scene)


def test_dungeon_scene_type():
    dungeon = Dungeon(n_rows=5, n_cols=5)
    assert dungeon.scene_type == "dungeon"


def test_dungeon_grid_dimensions():
    dungeon = Dungeon(n_rows=8, n_cols=10)
    assert dungeon.n_rows == 8
    assert dungeon.n_cols == 10


def test_dungeon_accepts_grid_kwarg():
    grid = SquareGrid(7, 9)
    dungeon = Dungeon(grid=grid)
    assert dungeon.grid is grid
    assert dungeon.n_rows == 7
    assert dungeon.n_cols == 9


def test_emplace_space_on_scene():
    """emplace_space is now inherited from Scene."""
    dungeon = Dungeon(n_rows=5, n_cols=5)
    cells = {SquareCell(filled=False, coordinates=(1, 1)),
             SquareCell(filled=False, coordinates=(1, 2))}
    room = Room(cells=cells, name="R0")
    dungeon.emplace_space(room)

    assert not dungeon.grid.cells[1][1].filled
    assert not dungeon.grid.cells[1][2].filled


def test_dungeon_rooms_and_hallways_still_work():
    dungeon = Dungeon(n_rows=10, n_cols=10)
    room = Room(name="A")
    room.add_cells([SquareCell(filled=False, coordinates=(2, 2))])
    dungeon.add_room(room)
    assert "A" in dungeon.rooms
