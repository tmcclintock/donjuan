from abc import ABC
from itertools import chain
from typing import List

from donjuan.cell import Cell


class Space(ABC):
    """
    A space is a section of a dungeon composed of cells.
    """

    def __init__(self, cells: List[List[Cell]]):
        self._cells = cells

    @property
    def cells(self) -> List[List[Cell]]:
        return self._cells

    def set_cells(self, cells: List[List[Cell]]) -> None:
        assert isinstance(cells, list)
        if len(cells) > 0:
            assert isinstance(cells[0], list)
            if len(cells[0]) > 0:
                assert isinstance(cells[0][0], Cell)
        self._cells = cells

    def overlaps(self, other: "Space") -> bool:
        """
        Compare the cells of this room to the other room to determine
        whether they overlap or not. Note, this algorithm is ``O(N*M)``
        where ``N`` is the number of cells in this room and ``M`` is
        the number of cells in the other room.

        Args:
            other (Room): other room to check against

        Returns:
            ``True`` if they overlap, ``False`` if not
        """
        # Loop over all of this space's cells
        for c1 in chain.from_iterable(self._cells):
            for c2 in chain.from_iterable(other._cells):
                if c1.coordinates == c2.coordinates:
                    return True
        # No overlap
        return False

    def shift_vertical(self, n: int) -> None:
        """
        Change the ``y`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment vertical position of cells
        """
        for c in chain.from_iterable(self.cells):
            c.set_y(c.y + int(n))
        return

    def shift_horizontal(self, n: int) -> None:
        """
        Change the ``x`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment horizontal position of cells
        """
        for c in chain.from_iterable(self.cells):
            c.set_x(c.x + int(n))
        return
