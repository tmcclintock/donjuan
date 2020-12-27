from typing import List, Optional

from donjuan.cell import Cell
from donjuan.space import Space


class Hallway(Space):
    """
    A hallway in a dungeon. It has a start an end cell.
    """

    def __init__(self, cells: Optional[List[List[Cell]]] = None):
        super().__init__(cells=cells or [[]])
