from abc import ABC
from typing import Any, List, Optional, Tuple, Type

from donjuan.door_space import DoorSpace
from donjuan.face import Faces, HexFaces, SquareFaces


class Cell(ABC):
    """
    The cell represents a single 'unit' in the map. The attributes on the cell
    define what exists in that unit. This includes the terrain, doors,
    walls, lights, other room details etc.
    """

    def __init__(
        self,
        faces: Faces,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
        space: Optional["Space"] = None,
    ):
        self.faces = faces
        self.filled = filled
        self.door_space = door_space
        self.contents = contents or []
        if coordinates is None:
            self._coordinates = [0, 0]
        else:
            self._coordinates = list(coordinates)
        self._space = space

    def set_coordinates(self, y: int, x: int) -> None:
        self._coordinates = [int(y), int(x)]

    def set_space(self, space: Type["Space"]) -> None:
        self._space = space

    def set_x(self, x: int) -> None:
        self._coordinates[1] = int(x)

    def set_y(self, y: int) -> None:
        self._coordinates[0] = int(y)

    @property
    def coordinates(self) -> Tuple[int, int]:
        return tuple(self._coordinates)

    @property
    def space(self) -> Optional[Type["Space"]]:
        """``Space`` this cell is a part of."""
        return self._space

    @property
    def x(self) -> int:
        return self._coordinates[1]

    @property
    def y(self) -> int:
        return self._coordinates[0]

    @property
    def n_sides(self) -> int:
        return len(self.faces)


class SquareCell(Cell):
    """
    A cell for a square grid.

    Args:
      faces (Optional[SquareFaces]): faces of the cell
      filled (bool, optional): flag indicating whether the cell is
        filled (default ``False``)
      door_space (Optional[DoorSpace]): kind of doorway in this cell
      contents (Optional[List[Any]]): things in this cell
    """

    def __init__(
        self,
        faces: Optional[SquareFaces] = None,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
    ):
        faces = faces or SquareFaces()
        super().__init__(
            faces=faces,
            filled=filled,
            door_space=door_space,
            contents=contents,
            coordinates=coordinates,
        )


class HexCell(Cell):
    """
    A cell for a hexagonal grid.

    Args:
      faces (Optional[HexFaces]): faces of the cell
      filled (bool, optional): flag indicating whether the cell is
        filled (default ``False``)
      door_space (Optional[DoorSpace]): kind of doorway in this cell
      contents (Optional[List[Any]]): things in this cell
    """

    def __init__(
        self,
        faces: Optional[HexFaces] = None,
        filled: bool = False,
        door_space: Optional[DoorSpace] = None,
        contents: Optional[List[Any]] = None,
        coordinates: Optional[Tuple[int, int]] = None,
    ):
        faces = faces or HexFaces()
        super().__init__(
            faces=faces,
            filled=filled,
            door_space=door_space,
            contents=contents,
            coordinates=coordinates,
        )
