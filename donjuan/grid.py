from abc import ABC, abstractmethod
from typing import List

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
