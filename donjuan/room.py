from itertools import chain
from typing import List, Optional

from donjuan import Cell


class Room:
    def __init__(self, cells: Optional[List[List[Cell]]] = None):
        self._cells = cells or [[]]

    @property
    def cells(self) -> List[List[Cell]]:
        return self._cells

    def overlaps(self, other: "Room") -> bool:
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
        # Loop over all of this room's cells
        for c1 in chain.from_iterable(self.cells):
            for c2 in chain.from_iterable(other.cells):
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
