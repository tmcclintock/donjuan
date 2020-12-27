from typing import Dict, List, Optional

from donjuan.grid import Grid, SquareGrid
from donjuan.room import Room


class Dungeon:
    def __init__(
        self,
        n_rows: Optional[int] = 5,
        n_cols: Optional[int] = 5,
        grid: Optional[Grid] = None,
        rooms: Optional[Dict[str, Room]] = None,
        randomizers: Optional[List["Randomizer"]] = None,
    ):
        self._grid = grid or SquareGrid(n_rows, n_cols)
        self._rooms = rooms or {}
        self._randomizers = randomizers or []

    def add_room(self, room: Room) -> None:
        self._rooms[room.name] = room

    @property
    def grid(self) -> Grid:
        return self._grid

    @property
    def n_cols(self) -> int:
        return self.grid.n_cols

    @property
    def n_rows(self) -> int:
        return self.grid.n_rows

    @property
    def randomizers(self) -> List["Randomizer"]:
        return self._randomizers

    @property
    def rooms(self) -> Dict[str, Room]:
        return self._rooms

    def randomize(self) -> None:
        """
        For each item in :attr:`randomizers`, run the
        :meth:`Randomizer.randomize_dungeon` method on this dungeon.
        """
        for rng in self.randomizers:
            rng.randomize_dungeon(self)
        return
