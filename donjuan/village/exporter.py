"""
Exports a VillageScene as a FoundryVTT scene bundle.
"""
import math
from typing import List

from donjuan.core.exporter import (
    FoundryExporter,
    _door_wall,
    _shared_edge_coords,
    _solid_wall,
)
from donjuan.core.room import Room
from donjuan.village.renderer import VillageRenderer
from donjuan.village.scene import VillageScene, VillageTree


class VillageExporter(FoundryExporter):
    """Renders and exports a village as a FoundryVTT scene bundle."""

    default_scene_name = "DonJuan Village"
    default_slug = "village"
    background_color = "#304227"
    global_light_enabled = True
    global_light_color = "#e6ddb7"

    def __init__(
        self,
        tile_size: int = 100,
        tree_wall_segments: int = 10,
        tree_wall_radius_fraction: float = 0.34,
        add_boundary_walls: bool = True,
        darkness_level: float = 0.15,
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

    def _render_image(self, scene: VillageScene, img_path: str) -> None:
        renderer = VillageRenderer(tile_size=self.tile_size)
        fig, _ = renderer.render(scene, file_path=img_path, save=True)
        import matplotlib.pyplot as plt
        plt.close(fig)

    def _build_walls(self, scene: VillageScene) -> List[dict]:
        walls: List[dict] = []
        if self.add_boundary_walls:
            walls.extend(self._boundary_walls(scene))
        walls.extend(self._building_walls(scene))
        for tree in scene.trees.values():
            cell = next(iter(tree.cells))
            walls.extend(self._tree_circle_walls(cell.y, cell.x))
        return walls

    def _boundary_walls(self, scene: VillageScene) -> List[dict]:
        t = self.tile_size
        width = scene.n_cols * t
        height = scene.n_rows * t
        return [
            _solid_wall([0, 0, width, 0]),
            _solid_wall([width, 0, width, height]),
            _solid_wall([width, height, 0, height]),
            _solid_wall([0, height, 0, 0]),
        ]

    def _building_walls(self, scene: VillageScene) -> List[dict]:
        walls: List[dict] = []
        seen: set = set()
        t = self.tile_size
        for building in scene.buildings.values():
            for cell in building.cells:
                for edge in cell.edges:
                    if edge is None or id(edge) in seen:
                        continue
                    seen.add(id(edge))
                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None:
                        continue
                    if c1.space is building and c2.space is building:
                        continue
                    if not (c1.space is building or c2.space is building):
                        continue
                    coords = _shared_edge_coords(c1, c2, t)
                    if coords is None:
                        continue
                    if edge.has_door:
                        walls.append(_door_wall(coords))
                    else:
                        walls.append(_solid_wall(coords))
        return walls

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
            walls.append(_solid_wall([round(x1), round(y1), round(x2), round(y2)]))
        return walls
