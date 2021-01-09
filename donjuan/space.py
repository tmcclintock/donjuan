from abc import ABC
from typing import List, Optional, Sequence, Set, Tuple, Union

from donjuan.cell import Cell
from donjuan.edge import Edge


class Space(ABC):
    """
    A space is a section of a dungeon composed of `Cell`s. This object
    contains these cells in a ``set`` under the property :attr:`cells`.
    It also has a :attr:`name` and knows about any entrances to the room
    (a list of `Edge` objects) via the :attr:`entrances` property.

    Args:
        cells (Optional[Set[Cell]]): cells that make up this space
        name (Union[int, str], optional): defaults to '', the room name
    """

    def __init__(self, cells: Optional[Set[Cell]] = None, name: Union[int, str] = ""):
        assert isinstance(name, (int, str))
        self._name = name
        self._cells = cells or set()
        self.entrances: List[Edge] = []
        self.assign_space_to_cells()
        self.reset_cell_coordinates()

    def assign_space_to_cells(self) -> None:
        """Set the :attr:`space` attribute for each `Cell` to ``self``."""
        for cell in self.cells:
            cell.set_space(self)

    def reset_cell_coordinates(self) -> None:
        self._cell_coordinates = set(cell.coordinates for cell in self.cells)

    @property
    def cells(self) -> Set[Cell]:
        return self._cells

    @property
    def cell_coordinates(self) -> Set[Tuple[int, int]]:
        return self._cell_coordinates

    @property
    def name(self) -> Union[int, str]:
        return str(self._name)

    def add_cells(self, cells: Sequence[Cell]) -> None:
        """
        Add cells to the set of cells in this space. Cells are added to
        both the :attr:`cells` set and the cell coordinates to the
        :attr:`cell_coordinates` set.

        Args:
            cells (Sequence[Cell]): any iterable collection of cells
        """
        for cell in cells:
            self.cells.add(cell)
            self.cell_coordinates.add(cell.coordinates)
        return

    def overlaps(self, other: "Space") -> bool:
        """
        Compare the cells of this space to the other space to determine
        whether they overlap or not. Note, this algorithm is ``O(N)``
        where ``N`` is the number of cells in this space, since set
        lookup is ``O(1)``.

        Args:
            other (Space): other space to check against

        Returns:
            ``True`` if they overlap, ``False`` if not
        """
        # Loop over all of this space's cells
        for cell in self.cells:
            if cell.coordinates in other.cell_coordinates:
                return True

        # No overlap
        return False

    def set_name(self, name: Union[int, str]) -> None:
        assert isinstance(name, (int, str))
        self._name = name

    def shift_vertical(self, n: int) -> None:
        """
        Change the ``y`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment vertical position of cells
        """
        for cell in self.cells:
            cell.set_y(cell.y + int(n))
        self.reset_cell_coordinates()
        return

    def shift_horizontal(self, n: int) -> None:
        """
        Change the ``x`` coordinates of all :attr:`cells` by ``n``.

        Args:
            n (int): number to increment horizontal position of cells
        """
        for cell in self.cells:
            cell.set_x(cell.x + int(n))
        self.reset_cell_coordinates()
        return
