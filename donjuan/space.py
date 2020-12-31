from abc import ABC
from typing import List, Optional, Set

from donjuan.cell import Cell


class Space(ABC):
    """
    A space is a section of a dungeon composed of `Cell`s. This object
    contains these cells in a ``set`` under the property :attr:`cells`.

    Args:
        cells (Optional[Set[Cell]]): cells that make up this space
    """

    def __init__(self, cells: Optional[Set[Cell]] = None):
        self._cells = cells or set()

    @property
    def cells(self) -> Set[Cell]:
        return self._cells

    def insert_cell_list(self, cells: List[Cell]) -> None:
        """
        Insert a list of cells into the :attr:`cells` set, with
        keys being the coordinates of the cells.

        Args:
            cells (List[Cell]): list of cells to insert
        """
        if len(cells) > 0:
            assert isinstance(cells[0], Cell)
        for cell in cells:
            self.cells.add(cell)

    def overlaps(self, other: "Space") -> bool:
        """
        Compare the cells of this space to the other space to determine
        whether they overlap or not. Note, this algorithm is ``O(N)``
        where ``N`` is the number of cells in this space, since set
        lookup is ``O(1)``.

        Args:
            other (Space): other space to check against

        Returns:
            ``True`` if they overlap, ``False`` if not
        """
        # Loop over all of this space's cells
        for cell in self.cells:
            if cell in other.cells:
                return True

        # No overlap
        return False

    def shift_vertical(self, n: int) -> None:
        """
        Change the ``y`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment vertical position of cells
        """
        for cell in self.cells:
            cell.set_y(cell.y + int(n))
        return

    def shift_horizontal(self, n: int) -> None:
        """
        Change the ``x`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment horizontal position of cells
        """
        for cell in self.cells:
            cell.set_x(cell.x + int(n))
        return
