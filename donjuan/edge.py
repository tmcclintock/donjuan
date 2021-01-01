from typing import Optional

from donjuan.cell import Cell
from donjuan.door_space import DoorSpace


class Edge:
    """
    An edge sits between two `Cell`s.

    Args:
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
    """

    def __init__(
        self, cell1: Optional[Cell] = None, cell2: Optional[Cell] = None,
    ):
        self._cell1 = cell1
        self._cell2 = cell2

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
            (self.cell1 is None)
            or (self.cell2 is None)
            or (self.cell1.filled != self.cell2.filled)
            or (
                self.cell1.space != self.cell2.space
                and self.cell1.space is not None
                and self.cell2.space is not None
            )
        )


class DoorEdge(Edge):
    """
    An edge with a door-like opening in it.

    Args:
        door_space (DoorSpace): the door-like thing on this edge
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
    """

    def __init__(
        self,
        door_space: DoorSpace,
        cell1: Optional[Cell] = None,
        cell2: Optional[Cell] = None,
    ):
        super().__init__(cell1, cell2)
        self._door_space = door_space

    @property
    def door_space(self) -> DoorSpace:
        return self._door_space

    def set_door_space(self, door_space: DoorSpace) -> None:
        self._door_space = door_space
