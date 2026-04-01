from typing import List, Optional, Tuple, Union

from donjuan.core.cell import Cell
from donjuan.core.space import Space


class Hallway(Space):
    """
    A reusable path/corridor space. Dungeon hallways and village roads both
    use this primitive.
    """

    def __init__(
        self,
        ordered_cells: Optional[List[Cell]] = None,
        name: Union[int, str] = "",
        theme: str = "default",
    ):
        self._ordered_cells = ordered_cells or list()
        super().__init__(cells=set(self.ordered_cells), name=name)
        self.theme = theme

    @property
    def ordered_cells(self) -> List[Cell]:
        return list(self._ordered_cells)

    @property
    def end_cell(self) -> Cell:
        return self.ordered_cells[-1]

    @property
    def start_cell(self) -> Cell:
        return self.ordered_cells[0]

    def append_ordered_cell_list(self, cells: List[Cell]) -> None:
        assert isinstance(cells, list)
        self.add_cells(cells)
        for cell in cells:
            assert isinstance(cell, Cell)
            self.ordered_cells.append(cell)
        return

    def get_coordinate_path(self) -> List[Tuple[int, int]]:
        path = []
        for cell in self.ordered_cells:
            path.append(cell.coordinates)
        return path
