from abc import ABC
from typing import List, Optional

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
            [self.cell_type(filled=True, coordinates=(i, j)) for j in range(n_cols)]
            for i in range(n_rows)
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

    def reset_cell_coordinates(self) -> None:
        """
        Helper function that sets the coordinates of the cells in the grid
        to their index values. Useful if a grid was created by
        :meth:`from_cells`.
        """
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                self.cells[i][j].set_coordinates(i, j)
        return


class SquareGrid(Grid):
    """
    Square grid of cells. In a square grid, the cell positions are integers.
    """

    cell_type = SquareCell

    def __init__(
        self, n_rows: int, n_cols: int, cells: Optional[List[List[SquareCell]]] = None
    ):
        super().__init__(n_rows, n_cols, cells)


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
