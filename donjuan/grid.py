from abc import ABC, abstractmethod
from typing import List, Tuple

from donjuan.cell import Cell, HexCell, SquareCell


class Grid(ABC):
    """
    Abstract base class for a grid of cells. The underlying grid can either
    be square or hexagonal.
    """

    def __init__(self, cells: Cell):
        self.cells = cells

    def get_filled_grid(self) -> List[List[bool]]:
        """
        Obtain a 2D array of boolean values representing the :attr:`filled`
        state of the cells attached to the grid.
        """
        return [
            [self.cells[i][j].filled for j in range(self.n_cols)]
            for i in range(self.n_rows)
        ]

    @classmethod
    @abstractmethod
    def from_cells(cls, cells: List[List[Cell]]):
        pass  # pragma: no cover


class SquareGrid(Grid):
    """
    Square grid of cells. In a square grid, the cell positions are integers.
    """

    def __init__(self, n_rows: int, n_cols: int):
        self.n_rows = n_rows
        self.n_cols = n_cols
        cells = [[SquareCell() for i in range(n_cols)] for j in range(n_rows)]
        super().__init__(cells=cells)

    @classmethod
    def from_cells(cls, cells: List[List[Cell]]):
        assert isinstance(cells, list)
        assert len(cells) >= 1, "cells must have an inner dimension"
        assert isinstance(cells[0], list)
        assert len(cells[0]) >= 1, "cells must have at least 1 column"
        assert isinstance(cells[0][0], Cell)
        n_rows = len(cells)
        n_cols = len(cells[0])
        grid = SquareGrid(n_rows, n_cols)
        grid.cells = cells
        return grid

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

    def __init__(self, n_rows: int, n_cols: int):
        self.n_rows = n_rows
        self.n_cols = n_cols
        cells = [[HexCell() for i in range(n_cols)] for j in range(n_rows)]
        super().__init__(cells=cells)

    @classmethod
    def from_cells(cls, cells: List[List[Cell]]):
        assert isinstance(cells, list)
        assert len(cells) >= 1, "cells must have an inner dimension"
        assert isinstance(cells[0], list)
        assert len(cells[0]) >= 1, "cells must have at least 1 column"
        assert isinstance(cells[0][0], Cell)
        n_rows = len(cells)
        n_cols = len(cells[0])
        grid = HexGrid(n_rows, n_cols)
        grid.cells = cells
        return grid
