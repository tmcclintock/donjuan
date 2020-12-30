from abc import ABC
from typing import List, Optional

from donjuan.cell import Cell, HexCell, SquareCell
from donjuan.edge import Edge


class Grid(ABC):
    """
    Abstract base class for a grid of cells. The underlying grid can either
    be square or hexagonal.
    """

    def __init__(
        self,
        n_rows: int,
        n_cols: int,
        cells: Optional[List[List[Cell]]] = None,
        edges: Optional[List[List[List[Edge]]]] = None,
    ):
        assert n_rows >= 1
        assert n_cols >= 1

        # If the cells were passed, then check the type
        if cells is not None:
            msg = f"cell type mismatch: {type(cells[0][0])} != {self.cell_type}"
            assert isinstance(cells[0][0], self.cell_type), msg

        cells = cells or [
            [self.cell_type(filled=True, coordinates=(i, j)) for j in range(n_cols)]
            for i in range(n_rows)
        ]

        assert len(cells) == n_rows, f"{len(cells)} vs {n_rows}"
        assert len(cells[0]) == n_cols, f"{len(cells[0])} vs {n_cols}"

        # Set attributes
        self._n_rows = n_rows
        self._n_cols = n_cols
        self._cells = cells

        # Create the edge grids
        self.set_edges(edges)

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

    @property
    def edge_grid(self) -> List[List[List[Edge]]]:
        return self._edges

    def reset_cell_coordinates(self) -> None:
        """
        Helper function that sets the coordinates of the cells in the grid
        to their index values.
        """
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                self.cells[i][j].set_coordinates(i, j)
        return

    def set_edges(self, edges: Optional[List[List[List[Edge]]]]):
        if edges is not None:
            msg = f"edge/cell grid mismatch: {len(edges)} vs {self.cell_type._n_sides // 2}"
            assert len(edges) == self.cell_type._n_sides // 2, msg
        else:
            edges = []

            # Horizontal edges
        pass


class SquareGrid(Grid):
    """
    Rectangular grid of square cells. In a square grid, the cell positions are
    integers.
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
