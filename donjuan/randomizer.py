import random
from typing import Optional

from donjuan import Cell, Grid


class Randomizer:
    """
    Class for randomizing features of a dungeon.
    """

    def randomize_cell(self, cell: Cell) -> None:
        """Randomize properties of the `Cell`"""
        pass

    def randomize_grid(self, grid: Grid) -> None:
        """Randomize properties of the `Grid`"""
        pass

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
