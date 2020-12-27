import random
from typing import Optional, Type

from donjuan.cell import Cell, SquareCell
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

    def randomize_room(self, room: Room) -> None:
        """Randomize properties of the `Room`"""
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


class RoomRandomizer(Randomizer):
    """
    Randomize the features of a `Room`.
    """

    def __init__(
        self, min_size: int = 3, max_size: int = 9, cell_type: Type[Cell] = SquareCell
    ):
        assert issubclass(cell_type, Cell)
        assert min_size >= 1
        assert max_size >= min_size
        assert max_size <= 100  # arbitrary
        self.min_size = 3
        self.max_size = 9
        self.cell_type = cell_type

    def randomize_room(self, room: Room) -> None:
        """
        Randomly determine the size of the room, and set the cells of
        the room to a 2D array of unfilled cells of that size.
        """
        # Draw the dimensions
        height = random.randint(self.min_size, self.max_size)
        width = random.randint(self.min_size, self.max_size)

        # Create empty cells and set them in the room
        cells = [
            [self.cell_type(filled=False, coordinates=(i, j)) for j in range(height)]
            for i in range(width)
        ]
        room.set_cells(cells)
        return
