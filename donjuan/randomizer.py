import random
from typing import Optional

from donjuan.cell import Cell
from donjuan.dungeon import Dungeon
from donjuan.grid import Grid
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


class RandomFilled(Randomizer):
    """
    Randomly set the :attr:`filled` attribute of cells.
    """

    def randomize_cell(self, cell: Cell) -> None:
        """Randomly fill the cell with probability 50%"""
        cell.filled = bool(random.randint(0, 1))

    def randomize_grid(self, grid: Grid) -> None:
        """Randomly fill all cells of the grid individually"""
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                self.randomize_cell(grid.cells[i][j])
        return
