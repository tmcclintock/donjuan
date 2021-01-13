import random
from typing import Optional

from donjuan.cell import Cell
from donjuan.dungeon import Dungeon
from donjuan.grid import Grid
from donjuan.hallway import Hallway
from donjuan.room import Room


class Randomizer:
    """
    Class for randomizing features of a dungeon.
    """

    def randomize_cell(self, cell: Cell) -> None:
        """Randomize properties of the `Cell`"""
        pass  # pragma: no cover

    def randomize_dungeon(self, dungeon: Dungeon) -> None:
        """Randomize properties of the `Dungeon`"""
        pass  # pragma: no cover

    def randomize_grid(self, grid: Grid) -> None:
        """Randomize properties of the `Grid`"""
        pass  # pragma: no cover

    def randomize_hallway_path(self, hallway: Hallway) -> None:
        """Randomize properties of the `Hallway`"""
        pass  # pragma: no cover

    def randomize_room_entrances(self, room: Room, *args) -> None:
        """Randomize the entrances of the `Room`"""
        pass  # pragma: no cover

    def randomize_room_size(self, room: Room, *args) -> None:
        """Randomize the size of the `Room`"""
        pass  # pragma: no cover

    def randomize_room_name(self, room: Room, *args) -> None:
        """Randomize the name of a `Room`"""
        pass  # pragma: no cover

    def randomize_room_position(self, room: Room, *args) -> None:
        """Randomize the position of a `Room`"""
        pass  # pragma: no cover

    @classmethod
    def seed(cls, seed: Optional[int] = None) -> None:
        """
        Args:
            seed (Optional[int]): seed passed to :meth:`random.seed`
        """
        random.seed(seed)
