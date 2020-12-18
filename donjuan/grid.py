from abc import ABC, abstractmethod
from typing import List

from donjuan.cell import Cell


class Grid(ABC):
    """
    Abstract base class for a grid of cells. The underlying grid can either
    be square or hexagonal.
    """

    @classmethod
    @abstractmethod
    def from_cells(cls, cells: List[List[Cell]]):
        pass


class SquareGrid(Grid):
    """
    Square grid of cells. In a square grid, the cell positions are integers.
    """

    def __init__(self, n_rows: int, n_cols: int):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.cells = [[Cell() for i in range(n_rows)] for j in range(n_cols)]

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
