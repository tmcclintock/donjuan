"""
Dungeon-specific FoundryVTT export.

`DungeonExporter` builds on the shared `FoundryExporter` base in
`donjuan.core.exporter`.
"""
from typing import List

from donjuan.core.exporter import (
    FoundryExporter,
    _boundary_coords,
    _door_wall,
    _shared_edge_coords,
    _solid_wall,
    _torch_light,
)
from donjuan.core.scene import Scene
from donjuan.dungeon.dungeon import Dungeon
from donjuan.core.hallway import Hallway
from donjuan.dungeon.renderer import PACK_NAMES, TexturedRenderer


class DungeonExporter(FoundryExporter):
    """
    Renders and exports a dungeon as a FoundryVTT scene bundle.

    Args:
        tile_size (int): pixels per grid square in the exported image.
            FoundryVTT works best with multiples of 50; default is 100.
        pack (str): texture pack name (default ``"stone"``).
        wall_shadows (bool): passed through to :class:`TexturedRenderer`.
        torchlight (bool): passed through to :class:`TexturedRenderer`.
        moss_and_cracks (bool): passed through to :class:`TexturedRenderer`.
        pillars (bool): passed through to :class:`TexturedRenderer`.
        wall_lines (bool): passed through to :class:`TexturedRenderer`.
        add_lights (bool): add FoundryVTT torch lights at door positions
            (default ``True``).
        grid_distance (int): in-game distance per square in feet (default 5).
        darkness_level (float): scene darkness 0–1 (default 1.0 = pitch dark).
    """

    default_scene_name = "DonJuan Dungeon"
    default_slug = "dungeon"

    def __init__(
        self,
        tile_size: int = 100,
        pack: str = "stone",
        wall_shadows: bool = True,
        torchlight: bool = True,
        moss_and_cracks: bool = True,
        pillars: bool = True,
        wall_lines: bool = True,
        add_lights: bool = True,
        grid_distance: int = 5,
        darkness_level: float = 1.0,
    ):
        super().__init__(
            tile_size=tile_size,
            grid_distance=grid_distance,
            darkness_level=darkness_level,
        )
        if pack not in PACK_NAMES:
            raise ValueError(
                f"Unknown texture pack {pack!r}. Choose from: {PACK_NAMES}"
            )
        self.pack = pack
        self.wall_shadows = wall_shadows
        self.torchlight = torchlight
        self.moss_and_cracks = moss_and_cracks
        self.pillars = pillars
        self.wall_lines = wall_lines
        self.add_lights = add_lights

    def _render_image(self, scene: Scene, img_path: str) -> None:
        dungeon = scene
        renderer = TexturedRenderer(
            tile_size=self.tile_size,
            pack=self.pack,
            wall_shadows=self.wall_shadows,
            torchlight=self.torchlight,
            moss_and_cracks=self.moss_and_cracks,
            pillars=self.pillars,
            wall_lines=self.wall_lines,
        )
        fig, _ = renderer.render(dungeon, file_path=img_path, save=True)
        import matplotlib.pyplot as plt
        plt.close(fig)

    def _build_walls(self, scene: Scene) -> List[dict]:
        """
        Generate FoundryVTT wall objects for every relevant edge in the dungeon.

        Rules applied in order:
        - Both cells filled → skip.
        - Boundary edge adjacent to unfilled cell → solid wall.
        - Filled ↔ unfilled → solid wall.
        - Both unfilled, same space → open floor, skip.
        - Both unfilled, both Hallway spaces → always open, skip.
        - Both unfilled, different spaces, ``edge.has_door`` → Foundry door.
        - Both unfilled, different spaces, interior edge → skip (open floor).
        - Both unfilled, different spaces, no door/opening → solid wall.
        """
        dungeon = scene
        t = self.tile_size
        out = []
        seen: set = set()

        for r in range(dungeon.n_rows):
            for c in range(dungeon.n_cols):
                cell = dungeon.grid.cells[r][c]
                for idx, edge in enumerate(cell.edges):
                    if edge is None or id(edge) in seen:
                        continue
                    seen.add(id(edge))

                    c1, c2 = edge.cell1, edge.cell2

                    if c1 is None or c2 is None:
                        adj = c1 if c1 is not None else c2
                        if adj is not None and not adj.filled:
                            out.append(_solid_wall(_boundary_coords(adj, idx, t)))
                        continue

                    if c1.filled and c2.filled:
                        continue

                    coords = _shared_edge_coords(c1, c2, t)
                    if coords is None:
                        continue

                    if c1.filled != c2.filled:
                        out.append(_solid_wall(coords))
                        continue

                    if c1.space is c2.space:
                        continue

                    if isinstance(c1.space, Hallway) and isinstance(c2.space, Hallway):
                        continue

                    if edge.has_door:
                        out.append(_door_wall(coords))
                    elif _edge_is_interior(c1, c2, dungeon):
                        pass
                    else:
                        out.append(_solid_wall(coords))

        return out

    def _build_lights(self, scene: Scene) -> List[dict]:
        """Add a torch light at the midpoint of every door edge."""
        if not self.add_lights:
            return []

        dungeon = scene
        t = self.tile_size
        out = []
        seen: set = set()

        for r in range(dungeon.n_rows):
            for c in range(dungeon.n_cols):
                for edge in dungeon.grid.cells[r][c].edges:
                    if edge is None or not edge.has_door or id(edge) in seen:
                        continue
                    seen.add(id(edge))
                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None or c1.filled or c2.filled:
                        continue
                    mx = ((c1.x + c2.x) / 2.0 + 0.5) * t
                    my = ((c1.y + c2.y) / 2.0 + 0.5) * t
                    out.append(_torch_light(mx, my))

        return out


def _edge_is_interior(c1, c2, dungeon: Dungeon) -> bool:
    """
    Return True if the edge between *c1* and *c2* sits entirely inside open
    space — i.e. at least one flanking 2×2 block contains only unfilled cells.
    Such an edge should not receive a wall in FoundryVTT.
    """
    cells = dungeon.grid.cells
    rows = dungeon.n_rows
    cols = dungeon.n_cols

    def _open(r: int, c: int) -> bool:
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        return not cells[r][c].filled

    r1, x1 = c1.y, c1.x
    r2, x2 = c2.y, c2.x

    if r1 == r2:
        r = r1
        c_left = min(x1, x2)
        above = (
            _open(r - 1, c_left) and _open(r - 1, c_left + 1)
            and _open(r, c_left) and _open(r, c_left + 1)
        )
        below = (
            _open(r, c_left) and _open(r, c_left + 1)
            and _open(r + 1, c_left) and _open(r + 1, c_left + 1)
        )
        return above or below
    else:
        r_top = min(r1, r2)
        c = x1
        left_block = (
            _open(r_top, c - 1) and _open(r_top, c)
            and _open(r_top + 1, c - 1) and _open(r_top + 1, c)
        )
        right_block = (
            _open(r_top, c) and _open(r_top, c + 1)
            and _open(r_top + 1, c) and _open(r_top + 1, c + 1)
        )
        return left_block or right_block
