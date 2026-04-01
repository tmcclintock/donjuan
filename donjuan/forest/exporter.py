"""
Exports a donjuan ForestScene as a FoundryVTT v10/v11/v12 scene bundle.

Tree cells become circular wall polygons, undergrowth remains cosmetic, and
the scene is exported as a bright outdoor map with ambient light enabled.
"""
import math
from typing import List

from donjuan.forest.scene import ForestScene, Undergrowth
from donjuan.forest.renderer import ForestRenderer
from donjuan.core.exporter import (
    FoundryExporter,
    _movement_wall,
    _shared_edge_coords,
    _solid_wall,
)


class ForestExporter(FoundryExporter):
    """
    Renders and exports a :class:`~donjuan.forest.ForestScene` as a
    FoundryVTT scene bundle.

    Args:
        tile_size (int): pixels per grid square in the exported image.
            FoundryVTT works best with multiples of 50; default 100.
        tree_wall_segments (int): number of wall segments used to approximate
            each circular tree wall (default 10).
        tree_wall_radius_fraction (float): tree wall circle radius as a
            fraction of ``tile_size`` (default 0.42 — slightly inside the
            cell boundary for a natural look).
        add_boundary_walls (bool): add solid walls along all four map edges
            (default True).
        darkness_level (float): scene darkness 0–1 (default 0.2 — dim
            filtered outdoor light).
        grid_distance (int): in-game distance per square in feet (default 5).
    """

    def __init__(
        self,
        tile_size: int = 100,
        tree_wall_segments: int = 10,
        tree_wall_radius_fraction: float = 0.42,
        add_boundary_walls: bool = True,
        add_undergrowth_walls: bool = True,
        darkness_level: float = 0.2,
        grid_distance: int = 5,
    ):
        super().__init__(
            tile_size=tile_size,
            grid_distance=grid_distance,
            darkness_level=darkness_level,
        )
        self.tree_wall_segments = tree_wall_segments
        self.tree_wall_radius_fraction = tree_wall_radius_fraction
        self.add_boundary_walls = add_boundary_walls
        self.add_undergrowth_walls = add_undergrowth_walls

    default_scene_name = "DonJuan Forest"
    default_slug = "forest"
    background_color = "#1a2e08"
    global_light_enabled = True
    global_light_color = "#c8e8a0"

    def _render_image(self, scene: ForestScene, img_path: str) -> None:
        renderer = ForestRenderer(tile_size=self.tile_size, wall_shadows=True)
        fig, _ = renderer.render(scene, file_path=img_path, save=True)
        import matplotlib.pyplot as plt
        plt.close(fig)

    # ── Wall generation ─────────────────────────────────────────────────────────

    def _build_walls(self, scene: ForestScene) -> List[dict]:
        """
        Build all FoundryVTT wall objects for the scene:

        1. Four boundary walls enclosing the entire map.
        2. For each tree cell, a circular polygon wall (~``tree_wall_segments``
           segments) centred on the cell.
        """
        walls: List[dict] = []

        if self.add_boundary_walls:
            walls.extend(self._boundary_walls(scene))

        for r in range(scene.n_rows):
            for c in range(scene.n_cols):
                if scene.grid.cells[r][c].filled:
                    walls.extend(self._tree_circle_walls(r, c))

        if self.add_undergrowth_walls:
            walls.extend(self._undergrowth_walls(scene))

        return walls

    def _boundary_walls(self, scene: ForestScene) -> List[dict]:
        """Four solid walls forming the outer edge of the map."""
        t = self.tile_size
        W = scene.n_cols * t
        H = scene.n_rows * t
        return [
            _solid_wall([0, 0, W, 0]),      # top
            _solid_wall([W, 0, W, H]),      # right
            _solid_wall([W, H, 0, H]),      # bottom
            _solid_wall([0, H, 0, 0]),      # left
        ]

    def _tree_circle_walls(self, row: int, col: int) -> List[dict]:
        """
        Return ``tree_wall_segments`` wall segments forming a circle centred
        on the cell at (row, col).
        """
        t      = self.tile_size
        cx     = (col + 0.5) * t
        cy     = (row + 0.5) * t
        radius = t * self.tree_wall_radius_fraction
        n      = self.tree_wall_segments
        walls  = []

        for i in range(n):
            a1 = 2 * math.pi * i / n
            a2 = 2 * math.pi * (i + 1) / n
            x1 = cx + radius * math.cos(a1)
            y1 = cy + radius * math.sin(a1)
            x2 = cx + radius * math.cos(a2)
            y2 = cy + radius * math.sin(a2)
            walls.append(_solid_wall([round(x1), round(y1), round(x2), round(y2)]))

        return walls

    def _undergrowth_walls(self, scene: ForestScene) -> List[dict]:
        """Perimeter walls for undergrowth that block movement but not sight."""
        walls: List[dict] = []
        seen: set = set()

        for r in range(scene.n_rows):
            for c in range(scene.n_cols):
                cell = scene.grid.cells[r][c]
                if not isinstance(cell.space, Undergrowth):
                    continue

                for edge in cell.edges:
                    if edge is None or id(edge) in seen:
                        continue
                    seen.add(id(edge))

                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None:
                        continue

                    if c1.space is c2.space:
                        continue

                    if not (
                        isinstance(c1.space, Undergrowth)
                        or isinstance(c2.space, Undergrowth)
                    ):
                        continue

                    coords = _shared_edge_coords(c1, c2, self.tile_size)
                    if coords is not None:
                        walls.append(_movement_wall(coords))

        return walls
