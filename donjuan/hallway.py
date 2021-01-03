from typing import List, Optional, Tuple, Union

from donjuan.cell import Cell
from donjuan.space import Space


class Hallway(Space):
    """
    A hallway in a dungeon. It has a start and end cell.

    Args:
        ordered_cells (Optional[List[Cell]]): ordered list of cells, where the
            order defines the path of the hallway
        name (Union[int, str], optional): defaults to '', the name of the
            hallway
    """

    def __init__(
        self, ordered_cells: Optional[List[Cell]] = None, name: Union[int, str] = "",
    ):
        self._ordered_cells = ordered_cells or []
        super().__init__(cells=set(self.ordered_cells), name=name)

    @property
    def ordered_cells(self) -> List[Cell]:
        """
        Cells that make up the path of the hallway. Does not contain
        extra cells that may be associated with this object (i.e. those
        off of the "path"). For the set of all cells, use :attr:`cells`.
        """
        return self._ordered_cells

    @property
    def end_cell(self) -> Cell:
        return self.ordered_cells[-1]

    @property
    def start_cell(self) -> Cell:
        return self.ordered_cells[0]

    def append_ordered_cell_list(self, cells: List[Cell]) -> None:
        """
        Append cells in order to the hallway. To add a cell to the hallway
        without including it in the hallways path, use
        :meth:`add_cells`.

        Args:
            cells: (List[Cell]): cells to append to the hallway
        """
        assert isinstance(cells, list)
        self.add_cells(cells)
        for cell in cells:
            assert isinstance(cell, Cell)
            self.ordered_cells.append(cell)
        return

    def get_coordinate_path(self) -> List[Tuple[int, int]]:
        """
        Get the coordinates of the cells that make up this path this
        hallway takes. Does not contain coordinates of extra cells on this
        object.

        Returns:
            coordinates of the hallway path
        """
        path = []
        for cell in self.ordered_cells:
            path.append(cell.coordinates)
        return path
