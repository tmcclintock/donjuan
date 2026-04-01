"""
Exports a donjuan CampScene as a FoundryVTT v10/v11/v12 scene bundle.

Camp scenes export perimeter trees as circular wall polygons and campfires as
light sources, while tents and paths remain image-only terrain.
"""
import math
from typing import List

from donjuan.camp.scene import CampScene, Tent
from donjuan.camp.renderer import CampRenderer
from donjuan.core.exporter import (
    FoundryExporter,
    _dense_wall,
    _movement_wall,
    _shared_edge_coords,
    _solid_wall,
    _torch_light,
)


class CampExporter(FoundryExporter):
    """
    Renders and exports a :class:`~donjuan.camp.CampScene` as a FoundryVTT
    scene bundle.

    Args:
        tile_size (int): pixels per grid square in the exported image.
        tree_wall_segments (int): number of wall segments used per tree circle.
        tree_wall_radius_fraction (float): circle radius as a fraction of the
            tile size.
        add_boundary_walls (bool): add solid walls along the map edges.
        add_fire_lights (bool): add Foundry lights at each campfire.
        darkness_level (float): scene darkness 0–1.
        grid_distance (int): in-game distance per square in feet.
    """

    default_scene_name = "DonJuan Camp"
    default_slug = "camp"
    background_color = "#24180e"
    global_light_enabled = True
    global_light_color = "#d8c28f"

    def __init__(
        self,
        tile_size: int = 100,
        tree_wall_segments: int = 10,
        tree_wall_radius_fraction: float = 0.42,
        add_boundary_walls: bool = True,
        add_fire_lights: bool = True,
        add_tent_walls: bool = True,
        darkness_level: float = 0.35,
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
        self.add_fire_lights = add_fire_lights
        self.add_tent_walls = add_tent_walls

    def _render_image(self, scene: CampScene, img_path: str) -> None:
        renderer = CampRenderer(tile_size=self.tile_size, fire_glow=True)
        fig, _ = renderer.render(scene, file_path=img_path, save=True)
        import matplotlib.pyplot as plt
        plt.close(fig)

    def _build_walls(self, scene: CampScene) -> List[dict]:
        walls: List[dict] = []

        if self.add_boundary_walls:
            walls.extend(self._boundary_walls(scene))

        for r in range(scene.n_rows):
            for c in range(scene.n_cols):
                if scene.grid.cells[r][c].filled:
                    walls.extend(self._tree_circle_walls(r, c))

        if self.add_tent_walls:
            walls.extend(self._tent_walls(scene))

        return walls

    def _build_lights(self, scene: CampScene) -> List[dict]:
        if not self.add_fire_lights:
            return []

        t = self.tile_size
        lights = []
        for fire in scene.fires:
            for cell in fire.cells:
                cx = (cell.x + 0.5) * t
                cy = (cell.y + 0.5) * t
                lights.append(_torch_light(cx, cy))
        return lights

    def _boundary_walls(self, scene: CampScene) -> List[dict]:
        t = self.tile_size
        width = scene.n_cols * t
        height = scene.n_rows * t
        return [
            _solid_wall([0, 0, width, 0]),
            _solid_wall([width, 0, width, height]),
            _solid_wall([width, height, 0, height]),
            _solid_wall([0, height, 0, 0]),
        ]

    def _tree_circle_walls(self, row: int, col: int) -> List[dict]:
        t = self.tile_size
        cx = (col + 0.5) * t
        cy = (row + 0.5) * t
        radius = t * self.tree_wall_radius_fraction
        n = self.tree_wall_segments
        walls = []

        for i in range(n):
            a1 = 2 * math.pi * i / n
            a2 = 2 * math.pi * (i + 1) / n
            x1 = cx + radius * math.cos(a1)
            y1 = cy + radius * math.sin(a1)
            x2 = cx + radius * math.cos(a2)
            y2 = cy + radius * math.sin(a2)
            walls.append(_dense_wall([round(x1), round(y1), round(x2), round(y2)]))

        return walls

    def _tent_walls(self, scene: CampScene) -> List[dict]:
        """Perimeter walls for tents that block movement but not sight."""
        walls: List[dict] = []
        seen: set = set()

        for r in range(scene.n_rows):
            for c in range(scene.n_cols):
                cell = scene.grid.cells[r][c]
                if not isinstance(cell.space, Tent):
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
                        isinstance(c1.space, Tent)
                        or isinstance(c2.space, Tent)
                    ):
                        continue

                    coords = _shared_edge_coords(c1, c2, self.tile_size)
                    if coords is not None:
                        walls.append(_movement_wall(coords))

        return walls
