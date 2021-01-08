from typing import Optional

from donjuan.cell import Cell


class Edge:
    """
    An edge sits between two `Cell`s.

    Args:
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
        has_door (bool, optional): default ``False``, indicates whether this
            object has a door
    """

    def __init__(
        self, cell1: Optional[Cell] = None, cell2: Optional[Cell] = None, has_door: bool = False,
    ):
        self._cell1 = cell1
        self._cell2 = cell2
        self.has_door = has_door

    @property
    def cell1(self) -> Optional[Cell]:
        return self._cell1

    @property
    def cell2(self) -> Optional[Cell]:
        return self._cell2

    def set_cell1(self, cell: Cell) -> None:
        self._cell1 = cell

    def set_cell2(self, cell: Cell) -> None:
        self._cell2 = cell

    @property
    def is_wall(self) -> bool:
        return (
            (not self.has_door) 
            or (self.cell1 is None)
            or (self.cell2 is None)
            or (self.cell1.filled != self.cell2.filled)
            or (self.cell1.space != self.cell2.space)
        )
