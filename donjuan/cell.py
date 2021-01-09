from abc import ABC
from collections.abc import Sequence
from typing import Any, List, Optional, Tuple, Type, Union

from donjuan.coordinates import Coordinates
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
        coordinates: Optional[Union[Sequence[int, int], Coordinates]] = None,
        space: Optional["Space"] = None,
        edges: Optional[List["Edge"]] = None,
    ):
        self.filled = filled
        self.door_space = door_space
        self.contents = contents or []
        if coordinates is None:
            self._coordinates = Coordinates(0, 0)
        else:
            if isinstance(coordinates, Sequence):
                self._coordinates = Coordinates.from_sequence(coordinates)
            else:
                self._coordinates = coordinates
        self._space = space
        self._edges = edges or [None] * self.n_sides

    def set_coordinates(self, y: int, x: int) -> None:
        self._coordinates = Coordinates(x, y)

    def set_edges(self, edges: List["Edge"]) -> None:
        assert len(edges) == self.n_sides, f"{len(edges)} vs {self.n_sides}"
        self._edges = edges

    def set_space(self, space: Type["Space"]) -> None:
        self._space = space

    def set_x(self, x: int) -> None:
        self._coordinates.x = int(x)

    def set_y(self, y: int) -> None:
        self._coordinates.y = int(y)

    @property
    def coordinates(self) -> Tuple[int, int]:
        return (self._coordinates.y, self._coordinates.x)

    @property
    def edges(self) -> List["Edge"]:
        return self._edges

    @property
    def space(self) -> Optional[Type["Space"]]:
        """``Space`` this cell is a part of."""
        return self._space

    @property
    def x(self) -> int:
        return self._coordinates.x

    @property
    def y(self) -> int:
        return self._coordinates.y

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
        coordinates: Optional[Union[Coordinates, Tuple[int, int]]] = None,
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
        coordinates: Optional[Union[Coordinates, Tuple[int, int]]] = None,
    ):
        super().__init__(
            filled=filled,
            door_space=door_space,
            contents=contents,
            coordinates=coordinates,
        )
