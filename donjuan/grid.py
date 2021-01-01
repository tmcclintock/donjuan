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
        edges = edges or self.init_edges()
        self.check_edges(edges)
        self._edges = edges
        self.link_edges_to_cells()

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
    def edges(self) -> List[List[List[Edge]]]:
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

    def check_edges(self, edges: Optional[List[List[List[Edge]]]]) -> None:
        """
        Check the dimensions of the `edges`.
        """
        msg = f"edge/cell grid mismatch: {len(edges)} vs {self.cell_type._n_sides // 2}"
        assert len(edges) == self.cell_type._n_sides // 2, msg
        h = edges[0]
        assert len(h) == self.n_rows + 1
        assert len(h[0]) == self.n_cols
        for v_edge in edges[1:]:
            assert len(v_edge) == self.n_rows
            assert len(v_edge[0]) == self.n_cols + 1
        return

    def init_edges(self) -> List[List[List[Edge]]]:
        edges = []
        # Horizontal edges
        edges.append(
            [[Edge() for i in range(self.n_cols)] for j in range(self.n_rows + 1)]
        )
        # Non-horizontal edges
        for i in range(self.cell_type._n_sides // 2 - 1):
            edges.append(
                [[Edge() for i in range(self.n_cols + 1)] for j in range(self.n_rows)]
            )
        return edges

    def link_edges_to_cells(self) -> None:
        """
        For an `Edge`, the :attr:`Edge.cell1` always points to either the left
        or upper `Cell`. The :attr:`Edge.cell2` always points to the right or
        the bottom.
        """
        # Horizontal edges first
        for i in range(self.n_rows + 1):
            for j in range(self.n_cols):
                self.edges[0][i][j].set_cell1(self.cells[i - 1][j] if i > 0 else None)
                self.edges[0][i][j].set_cell2(
                    self.cells[i][j] if i < self.n_rows else None
                )
        # Non-horizontal edges
        for k in range(1, len(self.edges)):
            for i in range(self.n_rows):
                for j in range(self.n_cols + 1):
                    self.edges[k][i][j].set_cell1(
                        self.cells[i][j - 1] if j > 0 else None
                    )
                    self.edges[k][i][j].set_cell2(
                        self.cells[i][j] if j < self.n_cols else None
                    )
        return


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
