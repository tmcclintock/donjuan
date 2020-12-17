from typing import Any, List, Optional

from donjuan import Doorspace, Faces


class Cell:
    """
    The cell represents a single 'unit' in the map. The attributes on the cell
    define what exists in that unit. This includes the terrain, doors,
    walls, lights, other room details etc.

    Args:
      x (float): horizontal grid coordinate
      y (float): veritcal grid coordinate
      filled (bool, optional): flag indicating whether the cell is
        filled (default ``False``)
      doorspace (Optional[Doorspace]): kind of doorway in this cell
      faces (Optional[Faces]): faces of the cell
      contents (Optional[List[Any]]): things in this cell
    """

    def __init__(
        self,
        x: float,
        y: float,
        filled: bool = False,
        doorspace: Optional[Doorspace] = None,
        faces: Optional[Faces] = None,
        contents: Optional[List[Any]] = None,
    ):
        self.x = x
        self.y = y
        self.filled = filled
        self.doorspace = doorspace
        self.faces = faces or Faces()
        self.contents = contents or []
