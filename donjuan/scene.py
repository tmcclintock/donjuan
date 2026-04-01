"""
Base class for all scene types (dungeons, forests, camps, etc.).
"""
from typing import TYPE_CHECKING

from donjuan.grid import Grid, SquareGrid
from donjuan.space import Space

if TYPE_CHECKING:
    pass


class Scene:
    """
    Abstract container for a procedurally-generated scene. Holds a :class:`~donjuan.grid.Grid`
    and knows how to emplace :class:`~donjuan.space.Space` objects into it.

    Subclasses add scene-specific space collections (rooms/hallways for
    :class:`~donjuan.dungeon.Dungeon`, clearings/paths for
    :class:`~donjuan.forest.ForestScene`, etc.).

    Args:
        grid (Grid): the grid backing this scene
        scene_type (str): identifier read by renderers to select drawing logic
    """

    def __init__(self, grid: Grid, scene_type: str = "dungeon"):
        self._grid = grid
        self.scene_type = scene_type

    @property
    def grid(self) -> Grid:
        return self._grid

    @property
    def n_rows(self) -> int:
        return self._grid.n_rows

    @property
    def n_cols(self) -> int:
        return self._grid.n_cols

    def emplace_space(self, space: Space) -> None:
        """
        Write the cells of ``space`` into the grid and re-link all edges.

        Args:
            space (Space): the space whose cells should be placed into the grid
        """
        last_cell = None
        for cell in space.cells:
            self.grid.cells[cell.y][cell.x] = cell
            last_cell = cell
        self.grid.link_edges_to_cells()
        if last_cell is not None:
            assert last_cell.edges is not None, "problem linking edges to cell"
