from abc import ABC
from typing import Any, List, Optional, Tuple

from donjuan.door_space import DoorSpace


class Cell(ABC):
    """
    The cell represents a single 'unit' in the map. The attributes on the cell
    define what exists in that unit. This includes the terrain, doors,
    walls, lights, other room details etc.
    """

    def __init__(
        self,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
    ):
        self.filled = filled
        self.door_space = door_space
        self.contents = contents or []
        if coordinates is None:
            self._coordinates = [0, 0]
        else:
            self._coordinates = list(coordinates)
        self._n_sides = None

    def set_coordinates(self, y: int, x: int) -> None:
        self._coordinates = [int(y), int(x)]

    def set_x(self, x: int) -> None:
        self._coordinates[1] = int(x)

    def set_y(self, y: int) -> None:
        self._coordinates[0] = int(y)

    @property
    def coordinates(self) -> Tuple[int, int]:
        return tuple(self._coordinates)

    @property
    def x(self) -> int:
        return self._coordinates[1]

    @property
    def y(self) -> int:
        return self._coordinates[0]

    @property
    def n_sides(self) -> int:
        return type(self)._n_sides


class SquareCell(Cell):
    """
    A cell for a square grid.

    Args:
      filled (bool, optional): flag indicating whether the cell is
        filled (default ``False``)
      door_space (Optional[DoorSpace]): kind of doorway in this cell
      contents (Optional[List[Any]]): things in this cell
    """

    _n_sides = 4

    def __init__(
        self,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(
            filled=filled,
            door_space=door_space,
            contents=contents,
            coordinates=coordinates,
        )


class HexCell(Cell):
    """
    A cell for a hexagonal grid.

    Args:
      filled (bool, optional): flag indicating whether the cell is
        filled (default ``False``)
      door_space (Optional[DoorSpace]): kind of doorway in this cell
      contents (Optional[List[Any]]): things in this cell
    """

    _n_sides = 6

    def __init__(
        self,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(
            filled=filled,
            door_space=door_space,
            contents=contents,
            coordinates=coordinates,
        )
