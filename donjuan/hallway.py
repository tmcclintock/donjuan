from typing import List, Optional, Set, Union

from donjuan.cell import Cell
from donjuan.space import Space


class Hallway(Space):
    """
    A hallway in a dungeon. It has a start and end cell.

    .. todo:: Complete this class
    """

    def __init__(
        self, cells: Optional[Set[Cell]] = None, name: Union[int, str] = "",
    ):
        super().__init__(cells=cells, name=name)
        self._cells_ordered: List[Cell] = []

    @property
    def cells_ordered(self) -> List[Cell]:
        return self._cells_ordered

    @property
    def end_cell(self) -> Cell:
        return self.cells_ordered[-1]

    @property
    def start_cell(self) -> Cell:
        return self.cells_ordered[0]
