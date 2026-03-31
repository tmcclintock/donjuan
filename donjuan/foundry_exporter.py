"""
Exports a donjuan dungeon as a FoundryVTT v10/v11/v12 scene bundle.

Two files are written to the chosen output directory:

- ``dungeon.png``  — the rendered map at *tile_size* pixels per square
- ``dungeon.json`` — a FoundryVTT scene (import via Scenes tab ➜ "Import Data")

Typical usage::

    from donjuan import FoundryExporter
    exporter = FoundryExporter(tile_size=100, pack="stone")
    img_path, json_path = exporter.export(dungeon, "/path/to/output_dir")
"""
import json
import os
import secrets
from typing import List, Optional, Tuple

from donjuan.dungeon import Dungeon
from donjuan.hallway import Hallway
from donjuan.room import Room
from donjuan.textured_renderer import PACK_NAMES, TexturedRenderer

# ── Torch light defaults (grid squares) ───────────────────────────────────────
_TORCH_BRIGHT = 3
_TORCH_DIM    = 6


class FoundryExporter:
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
        if pack not in PACK_NAMES:
            raise ValueError(
                f"Unknown texture pack {pack!r}. Choose from: {PACK_NAMES}"
            )
        self.tile_size       = tile_size
        self.pack            = pack
        self.wall_shadows    = wall_shadows
        self.torchlight      = torchlight
        self.moss_and_cracks = moss_and_cracks
        self.pillars         = pillars
        self.wall_lines      = wall_lines
        self.add_lights      = add_lights
        self.grid_distance   = grid_distance
        self.darkness_level  = darkness_level

    # ── Public API ──────────────────────────────────────────────────────────────

    def export(
        self,
        dungeon: Dungeon,
        output_dir: str,
        scene_name: str = "DonJuan Dungeon",
    ) -> Tuple[str, str]:
        """
        Render the dungeon and write the scene bundle to *output_dir*.

        The file base-name is derived from *scene_name* by lower-casing,
        replacing spaces/special characters with underscores, and stripping
        leading/trailing underscores — e.g. ``"Crypt of Shadows"`` →
        ``crypt_of_shadows.png`` / ``crypt_of_shadows.json``.

        Args:
            dungeon (Dungeon): the dungeon to export.
            output_dir (str): directory to write files into (created if needed).
            scene_name (str): display name used in FoundryVTT and for filenames.

        Returns:
            ``(image_path, json_path)`` — absolute paths of the files written.
        """
        import re
        slug = re.sub(r"[^a-z0-9]+", "_", scene_name.lower()).strip("_") or "dungeon"

        os.makedirs(output_dir, exist_ok=True)
        img_filename  = f"{slug}.png"
        json_filename = f"{slug}.json"
        img_path  = os.path.join(output_dir, img_filename)
        json_path = os.path.join(output_dir, json_filename)

        # ── Render image ───────────────────────────────────────────────
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

        # ── Build & write scene JSON ───────────────────────────────────
        scene = self._build_scene(dungeon, img_filename, scene_name)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scene, f, indent=2)

        return img_path, json_path

    # ── Scene assembly ──────────────────────────────────────────────────────────

    def _build_scene(
        self, dungeon: Dungeon, img_filename: str, scene_name: str
    ) -> dict:
        t = self.tile_size
        W = dungeon.n_cols * t
        H = dungeon.n_rows * t

        walls  = self._build_walls(dungeon)
        lights = self._build_lights(dungeon) if self.add_lights else []

        return {
            "_id":           _random_id(),
            "name":          scene_name,
            "active":        False,
            "navigation":    False,
            "navOrder":      0,
            "navName":       "",
            # Users must place dungeon.png in their FoundryVTT data folder
            # and update this path, or re-link the image after import.
            "img":           img_filename,
            "foreground":    None,
            "fogOverlay":    None,
            "fogExploredColor":   None,
            "fogUnexploredColor": None,
            "width":         W,
            "height":        H,
            "padding":       0,
            "initial":       None,
            "backgroundColor": "#000000",
            "grid": {
                "type":     1,          # SQUARE
                "size":     t,
                "color":    "#000000",
                "alpha":    0.0,        # hide the grid overlay (image has its own)
                "distance": self.grid_distance,
                "units":    "ft",
            },
            "tokenVision":   True,
            "fogExploration": True,
            "environment": {
                "globalLight": {
                    "enabled":    False,
                    "bright":     0,
                    "color":      None,
                    "coloration": 1,
                    "darkness":   {"min": 0, "max": 1},
                    "luminosity": 0.5,
                    "saturation": 0,
                    "contrast":   0,
                    "shadows":    0,
                    "animation": {
                        "type":      None,
                        "speed":     5,
                        "intensity": 5,
                        "reverse":   False,
                    },
                },
                "darknessLevel": self.darkness_level,
            },
            "walls":    walls,
            "tokens":   [],
            "lights":   lights,
            "notes":    [],
            "sounds":   [],
            "tiles":    [],
            "drawings": [],
            "flags":    {},
        }

    # ── Wall generation ─────────────────────────────────────────────────────────

    def _build_walls(self, dungeon: Dungeon) -> List[dict]:
        """
        Generate FoundryVTT wall objects for every relevant edge in the dungeon.

        Rules applied in order:
        - Both cells filled → skip (players can never stand there).
        - Boundary edge (one cell outside grid) adjacent to unfilled cell
          → solid wall (exterior dungeon border).
        - Both cells unfilled, **different spaces**, ``has_door`` → door.
        - ``filled`` XOR (one filled, one unfilled) → solid wall.
        - Both cells unfilled, **different spaces**, no door → solid wall
          (e.g. two adjacent rooms not yet connected, or a hallway dead-end).
        - Both cells unfilled, **same space**, no door → open floor; skip.

        The "same-space" guard is the critical fix: ``edge.is_wall`` returns
        True for *any* edge without a door, including interior room edges.
        We must not add FoundryVTT walls there.
        """
        t    = self.tile_size
        out  = []
        seen: set = set()

        for r in range(dungeon.n_rows):
            for c in range(dungeon.n_cols):
                cell = dungeon.grid.cells[r][c]
                for idx, edge in enumerate(cell.edges):
                    if edge is None or id(edge) in seen:
                        continue
                    seen.add(id(edge))

                    c1, c2 = edge.cell1, edge.cell2

                    # ── Boundary edge ───────────────────────────────────
                    if c1 is None or c2 is None:
                        adj = c1 if c1 is not None else c2
                        if adj is not None and not adj.filled:
                            out.append(_solid_wall(_boundary_coords(adj, idx, t)))
                        continue

                    # ── Both filled — nothing to block ──────────────────
                    if c1.filled and c2.filled:
                        continue

                    coords = _shared_edge_coords(c1, c2, t)
                    if coords is None:
                        continue

                    # ── Physical boundary (filled ↔ unfilled) ───────────
                    if c1.filled != c2.filled:
                        out.append(_solid_wall(coords))
                        continue

                    # ── Both unfilled from here ─────────────────────────
                    # Same-space edges are open interior floor — no wall.
                    if c1.space is c2.space:
                        continue

                    # ── Different spaces ────────────────────────────────
                    # Only emit a FoundryVTT door where one side is a Room
                    # and the other is a Hallway.  The entrance randomizer
                    # also marks room↔room adjacent edges as has_door, but
                    # those must not appear as door icons in Foundry.
                    if edge.has_door and _is_room_hall_boundary(c1, c2):
                        out.append(_door_wall(coords))
                    else:
                        out.append(_solid_wall(coords))

        return out

    # ── Light generation ────────────────────────────────────────────────────────

    def _build_lights(self, dungeon: Dungeon) -> List[dict]:
        """Add a torch light at the midpoint of every door edge."""
        t    = self.tile_size
        out  = []
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
                    # Only torch at room↔hallway boundaries
                    if not _is_room_hall_boundary(c1, c2):
                        continue
                    # Pixel midpoint of the shared edge
                    mx = ((c1.x + c2.x) / 2.0 + 0.5) * t
                    my = ((c1.y + c2.y) / 2.0 + 0.5) * t
                    out.append(_torch_light(mx, my))

        return out


# ── Module-level helpers ────────────────────────────────────────────────────────

def _is_room_hall_boundary(c1, c2) -> bool:
    """
    Return True when the edge sits exactly between a Room cell and a
    Hallway cell — i.e. a genuine corridor entrance.

    Edges between two Room cells (adjacent rooms touching each other) are
    *not* considered corridor doors; the entrance randomizer marks those
    ``has_door=True`` but they should appear as solid walls in Foundry, not
    door icons.
    """
    return isinstance(c1.space, Room) != isinstance(c2.space, Room)


def _random_id() -> str:
    """Return a random 16-character hex string suitable as a FoundryVTT _id."""
    return secrets.token_hex(8)


def _boundary_coords(cell, edge_idx: int, t: int) -> List[int]:
    """
    Return ``[x1, y1, x2, y2]`` for a boundary edge.

    ``edge_idx`` is the edge's index in the cell's edges list:
    0=top, 1=right, 2=bottom, 3=left.
    """
    x, y = cell.x, cell.y   # column, row
    if edge_idx == 0:        # top
        return [x * t,       y * t,       (x + 1) * t, y * t      ]
    elif edge_idx == 1:      # right
        return [(x + 1) * t, y * t,       (x + 1) * t, (y + 1) * t]
    elif edge_idx == 2:      # bottom
        return [x * t,       (y + 1) * t, (x + 1) * t, (y + 1) * t]
    else:                    # left
        return [x * t,       y * t,       x * t,       (y + 1) * t]


def _shared_edge_coords(c1, c2, t: int) -> Optional[List[int]]:
    """
    Return ``[x1, y1, x2, y2]`` for the shared edge between two adjacent cells.

    ``c1`` is always left/upper and ``c2`` always right/lower per FoundryVTT
    grid convention.  Returns ``None`` for non-adjacent (diagonal) pairs.
    """
    if c1.y == c2.y:
        # Same row → vertical edge at x = c2.x * t
        x = c2.x * t
        return [x, c1.y * t, x, (c1.y + 1) * t]
    if c1.x == c2.x:
        # Same column → horizontal edge at y = c2.y * t
        y = c2.y * t
        return [c1.x * t, y, (c1.x + 1) * t, y]
    return None


def _solid_wall(coords: List[int]) -> dict:
    return {
        "_id":   _random_id(),
        "c":     coords,
        "light": 20,
        "move":  20,
        "sight": 20,
        "sound": 20,
        "dir":   0,
        "door":  0,
        "ds":    0,
        "threshold": {
            "light": None, "sight": None,
            "sound": None, "attenuation": False,
        },
        "flags": {},
    }


def _door_wall(coords: List[int]) -> dict:
    return {
        "_id":   _random_id(),
        "c":     coords,
        "light": 20,
        "move":  20,
        "sight": 20,
        "sound": 20,
        "dir":   0,
        "door":  1,    # normal door
        "ds":    0,    # closed
        "threshold": {
            "light": None, "sight": None,
            "sound": None, "attenuation": False,
        },
        "flags": {},
    }


def _torch_light(cx: float, cy: float) -> dict:
    return {
        "_id":      _random_id(),
        "x":        cx,
        "y":        cy,
        "rotation": 0,
        "walls":    True,
        "vision":   False,
        "config": {
            "alpha":       0.6,
            "angle":       360,
            "bright":      _TORCH_BRIGHT,
            "color":       "#ff9933",
            "coloration":  1,
            "dim":         _TORCH_DIM,
            "attenuation": 0.5,
            "luminosity":  0.5,
            "saturation":  0,
            "contrast":    0,
            "shadows":     0,
            "animation": {
                "type":      "torch",
                "speed":     5,
                "intensity": 5,
                "reverse":   False,
            },
            "darkness": {"min": 0, "max": 1},
        },
        "flags": {},
    }
