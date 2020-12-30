from typing import Any, Dict, Optional

from donjuan.cell import Cell
from donjuan.door_space import DoorSpace


class Edge:
    """
    An edge sits between two `Cell`s.

    Args:
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
        features (Dict[str, Any]): other features on this edge
    """

    def __init__(
        self,
        cell1: Optional[Cell] = None,
        cell2: Optional[Cell] = None,
        solid: bool = False,
        features: Dict[str, Any] = None,
    ):
        self._cell1 = cell1
        self._cell2 = cell2
        self.features = features or {}

    @property
    def cell1(self) -> Cell:
        return self._cell1

    @property
    def cell2(self) -> Cell:
        return self._cell2

    def set_cell1(self, cell: Cell) -> None:
        self._cell1 = cell

    def set_cell2(self, cell: Cell) -> None:
        self._cell2 = cell


def WallEdge(Edge):
    """
    An edge that is a wall.

    Args:
        solid (bool, optional): default is ``True``. Flag whether this is a
            solid wall
        transparent (bool, optional): default is ``False``. Flag whetehr this
            wall is see-through
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
        features (Dict[str, Any]): other features on this edge
    """

    def __init__(
        self,
        solid: bool = True,
        transparent: bool = False,
        cell1: Optional[Cell] = None,
        cell2: Optional[Cell] = None,
        features: Dict[str, Any] = None,
    ):
        super().__init__(cell1, cell2, features)
        self.solid = solid
        self.transparent = transparent


def DoorEdge(Edge):
    """
    An edge with a door-like opening in it.

    Args:
        door_space (DoorSpace): the door-like thing on this edge
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
        features (Dict[str, Any]): other features on this edge
    """

    def __init__(
        self,
        door_space: DoorSpace,
        cell1: Optional[Cell] = None,
        cell2: Optional[Cell] = None,
        features: Dict[str, Any] = None,
    ):
        super().__init__(cell1, cell2, features)
        self._door_space = door_space

    @property
    def door_space(self) -> DoorSpace:
        return self._door_space

    def set_door_space(self, door_space: DoorSpace) -> None:
        self._door_space = door_space
