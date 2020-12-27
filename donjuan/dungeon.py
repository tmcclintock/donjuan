from typing import Dict, Optional

from donjuan.grid import Grid, SquareGrid
from donjuan.room import Room


class Dungeon:
    def __init__(
        self,
        n_rows: Optional[int] = 5,
        n_cols: Optional[int] = 5,
        grid: Optional[Grid] = None,
        rooms: Optional[Dict[str, Room]] = None,
    ):
        self._grid = grid or SquareGrid(n_rows, n_cols)
        self._rooms = rooms or {}

    def add_room(self, room: Room) -> None:
        self._rooms[room.name] = room

    @property
    def grid(self) -> Grid:
        return self._grid

    @property
    def rooms(self) -> Dict[str, Room]:
        return self._rooms
