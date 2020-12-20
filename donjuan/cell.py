from abc import ABC
from typing import Any, List, Optional

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
    ):
        self.faces = faces
        self.filed = filled
        self.door_space = door_space
        self.contents = contents or []

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
    ):
        faces = faces or SquareFaces()
        super().__init__(
            faces=faces, filled=filled, door_space=door_space, contents=contents
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
    ):
        faces = faces or HexFaces()
        super().__init__(
            faces=faces, filled=filled, door_space=door_space, contents=contents
        )
