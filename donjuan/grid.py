from abc import ABC
from typing import List, Optional, Tuple

from donjuan.cell import Cell, HexCell, SquareCell


class Grid(ABC):
    """
    Abstract base class for a grid of cells. The underlying grid can either
    be square or hexagonal.
    """

    def __init__(
        self, n_rows: int, n_cols: int, cells: Optional[List[List[Cell]]] = None
    ):
        assert n_rows > 1
        assert n_cols > 1
        cells = cells or [
            [self.cell_type() for i in range(n_cols)] for j in range(n_rows)
        ]
        assert len(cells) == n_rows, f"{len(cells)} vs {n_rows}"
        assert len(cells[0]) == n_cols, f"{len(cells[0])} vs {n_cols}"
        self._n_rows = n_rows
        self._n_cols = n_cols
        self._cells = cells

    def get_filled_grid(self) -> List[List[bool]]:
        """
        Obtain a 2D array of boolean values representing the :attr:`filled`
        state of the cells attached to the grid.
        """
        return [
            [self.cells[i][j].filled for j in range(self.n_cols)]
            for i in range(self.n_rows)
        ]

    @property
    def n_rows(self) -> int:
        return self._n_rows

    @property
    def n_cols(self) -> int:
        return self._n_cols

    @property
    def cells(self) -> List[List[Cell]]:
        return self._cells

    @classmethod
    def from_cells(cls, cells: List[List[Cell]]):
        assert isinstance(cells, list)
        assert len(cells) >= 1, "cells must have an inner dimension"
        assert isinstance(cells[0], list)
        assert len(cells[0]) >= 1, "cells must have at least 1 column"
        msg = f"passed cells of type {type(cells[0][0])} but require {cls.cell_type}"
        assert isinstance(cells[0][0], cls.cell_type), msg
        return cls(len(cells), len(cells[0]), cells)


class SquareGrid(Grid):
    """
    Square grid of cells. In a square grid, the cell positions are integers.
    """

    cell_type = SquareCell

    def __init__(
        self, n_rows: int, n_cols: int, cells: Optional[List[List[SquareCell]]] = None
    ):
        super().__init__(n_rows, n_cols, cells)

    def find_walls(self) -> List[Tuple[Tuple[int, int], Tuple[int, int], str]]:
        """
        Find all of the continuous walls.
        :return: a list of walls, where a wall is defined as a three part tuple:
                        1. the first cell of the wall's coordinates
                        2. the last cell of the wall's coordinates
                        3. the dimension of the wall (vertical or horizontal)
                 vertical walls run along side the east side of the cells
                 horizontal walls run along side the south side of the cells
        """
        checked_borders = {}
        walls = []
        for row, y in zip(self.cells, range(len(self.cells))):
            for cell, x in zip(row, range(len(row))):
                if (x, y, "y") not in checked_borders:
                    checked_borders[(x, y, "y")] = 1
                    if (
                        y + 1 < len(self.cells)
                        and cell.filled != self.cells[y + 1][x].filled
                    ):
                        wall_start = (x, y)
                        wall_end = (x, y)
                        i = 1
                        while x + i < len(row):
                            checked_borders[(x + i, y, "x")] = 1
                            if (
                                self.cells[y][x + i].filled
                                != self.cells[y + 1][x + i].filled
                            ):
                                wall_end = (x + i, y)
                                i += 1
                            else:
                                break
                        walls.append((wall_start, wall_end, "horizontal"))

                    if x + 1 < len(row) and cell.filled != row[x + 1].filled:
                        wall_start = (x, y)
                        wall_end = (x, y)
                        i = 1
                        while y + i < len(self.cells):
                            checked_borders[(x, y + i, "y")] = 1
                            if (
                                self.cells[y + i][x].filled
                                != self.cells[y + i][x + 1].filled
                            ):
                                wall_end = (x, y + i)
                                i += 1
                            else:
                                break
                        walls.append((wall_start, wall_end, "vertical"))
        return walls


class HexGrid(Grid):
    """
    Rectangular grid of hexagonal cells. In a hex grid, the cell positions
    are integers, with odd rows being "offset" by half a cell size when
    rendered.
    """

    cell_type = HexCell

    def __init__(
        self, n_rows: int, n_cols: int, cells: Optional[List[List[HexCell]]] = None
    ):
        super().__init__(n_rows, n_cols, cells)
