"""
Exports donjuan scenes as FoundryVTT v10/v11/v12 scene bundles.

`FoundryExporter` is the shared base class for scene-specific exporters.
"""
import json
import os
import re
import secrets
from typing import List, Optional, Tuple

from donjuan.core.edge import (
    DOOR_KIND_LOCKED,
    DOOR_KIND_NORMAL,
    DOOR_KIND_SECRET,
    DOOR_STATE_CLOSED,
    DOOR_STATE_LOCKED,
    DOOR_STATE_OPEN,
    WALL_KIND_DENSE,
    WALL_KIND_MOVEMENT,
    WALL_KIND_SIGHT,
    WALL_KIND_SOLID,
)
from donjuan.core.scene import Scene


class FoundryExporter:
    """
    Shared base class for exporters that write FoundryVTT scene bundles.

    Subclasses are responsible for rendering the scene image and generating any
    scene-specific walls and lights.

    Args:
        tile_size (int): pixels per grid square in the exported image.
            FoundryVTT works best with multiples of 50; default 100.
        grid_distance (int): in-game distance per square in feet (default 5).
        darkness_level (float): scene darkness 0–1.
    """

    default_scene_name = "DonJuan Scene"
    default_slug = "scene"
    background_color = "#000000"
    global_light_enabled = False
    global_light_color = None

    def __init__(
        self,
        tile_size: int = 100,
        grid_distance: int = 5,
        darkness_level: float = 1.0,
    ):
        self.tile_size = tile_size
        self.grid_distance = grid_distance
        self.darkness_level = darkness_level

    def export(
        self,
        scene: Scene,
        output_dir: str,
        scene_name: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Render *scene* and write the scene bundle to *output_dir*.

        Args:
            scene (Scene): the scene to export.
            output_dir (str): directory to write files into (created if needed).
            scene_name (Optional[str]): display name used in FoundryVTT and for
                filenames. Defaults to the subclass's ``default_scene_name``.

        Returns:
            ``(image_path, json_path)`` — absolute paths of the files written.
        """
        scene_name = scene_name or self.default_scene_name
        slug = _slugify(scene_name, self.default_slug)

        os.makedirs(output_dir, exist_ok=True)
        img_filename = f"{slug}.png"
        json_filename = f"{slug}.json"
        img_path = os.path.join(output_dir, img_filename)
        json_path = os.path.join(output_dir, json_filename)

        self._render_image(scene, img_path)

        scene_doc = self._build_scene(scene, img_filename, scene_name)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scene_doc, f, indent=2)

        return img_path, json_path

    def _render_image(self, scene: Scene, img_path: str) -> None:
        """Render *scene* to *img_path*. Subclasses must override this."""
        raise NotImplementedError

    def _build_scene(
        self,
        scene: Scene,
        img_filename: str,
        scene_name: str,
    ) -> dict:
        t = self.tile_size
        width = scene.n_cols * t
        height = scene.n_rows * t

        return {
            "_id": _random_id(),
            "name": scene_name,
            "active": False,
            "navigation": False,
            "navOrder": 0,
            "navName": "",
            "img": img_filename,
            "foreground": None,
            "fogOverlay": None,
            "fogExploredColor": None,
            "fogUnexploredColor": None,
            "width": width,
            "height": height,
            "padding": 0,
            "initial": None,
            "backgroundColor": self.background_color,
            "grid": {
                "type": 1,  # SQUARE
                "size": t,
                "color": "#000000",
                "alpha": 0.0,
                "distance": self.grid_distance,
                "units": "ft",
            },
            "tokenVision": True,
            "fogExploration": True,
            "environment": {
                "globalLight": self._global_light_config(),
                "darknessLevel": self.darkness_level,
            },
            "walls": self._build_walls(scene),
            "tokens": [],
            "lights": self._build_lights(scene),
            "notes": [],
            "sounds": [],
            "tiles": [],
            "drawings": [],
            "flags": {},
        }

    def _global_light_config(self) -> dict:
        return {
            "enabled": self.global_light_enabled,
            "bright": 0,
            "color": self.global_light_color,
            "coloration": 1,
            "darkness": {"min": 0, "max": 1},
            "luminosity": 0.5,
            "saturation": 0,
            "contrast": 0,
            "shadows": 0,
            "animation": {
                "type": None,
                "speed": 5,
                "intensity": 5,
                "reverse": False,
            },
        }

    def _build_walls(self, scene: Scene) -> List[dict]:
        """Return scene wall documents. Subclasses must override this."""
        raise NotImplementedError

    def _build_lights(self, scene: Scene) -> List[dict]:
        """Return scene light documents. Subclasses may override this."""
        return []


# ── Module-level helpers ───────────────────────────────────────────────────────


def _slugify(scene_name: str, fallback: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", scene_name.lower()).strip("_") or fallback


def _random_id() -> str:
    """Return a random 16-character hex string suitable as a FoundryVTT _id."""
    return secrets.token_hex(8)


def _boundary_coords(cell, edge_idx: int, t: int) -> List[int]:
    """
    Return ``[x1, y1, x2, y2]`` for a boundary edge.

    ``edge_idx`` is the edge's index in the cell's edges list:
    0=top, 1=right, 2=bottom, 3=left.
    """
    x, y = cell.x, cell.y
    if edge_idx == 0:
        return [x * t, y * t, (x + 1) * t, y * t]
    elif edge_idx == 1:
        return [x * t, y * t, x * t, (y + 1) * t]
    elif edge_idx == 2:
        return [x * t, (y + 1) * t, (x + 1) * t, (y + 1) * t]
    else:
        return [(x + 1) * t, y * t, (x + 1) * t, (y + 1) * t]


def _shared_edge_coords(c1, c2, t: int) -> Optional[List[int]]:
    """
    Return ``[x1, y1, x2, y2]`` for the shared edge between two adjacent cells.

    ``c1`` is always left/upper and ``c2`` always right/lower per FoundryVTT
    grid convention. Returns ``None`` for non-adjacent (diagonal) pairs.
    """
    if c1.y == c2.y:
        x = c2.x * t
        return [x, c1.y * t, x, (c1.y + 1) * t]
    if c1.x == c2.x:
        y = c2.y * t
        return [c1.x * t, y, (c1.x + 1) * t, y]
    return None


def _solid_wall(coords: List[int]) -> dict:
    return _wall_document(coords, wall_kind=WALL_KIND_SOLID)


def _door_wall(coords: List[int], door_kind: str = DOOR_KIND_NORMAL) -> dict:
    return _wall_document(
        coords,
        door_kind=door_kind,
        door_state=DOOR_STATE_LOCKED if door_kind == DOOR_KIND_LOCKED else DOOR_STATE_CLOSED,
    )


def _locked_door_wall(coords: List[int]) -> dict:
    return _wall_document(coords, door_kind=DOOR_KIND_LOCKED, door_state=DOOR_STATE_LOCKED)


def _secret_door_wall(coords: List[int]) -> dict:
    return _wall_document(coords, door_kind=DOOR_KIND_SECRET)


def _movement_wall(coords: List[int]) -> dict:
    """Wall that blocks movement but not vision, light, or sound."""
    return _wall_document(coords, wall_kind=WALL_KIND_MOVEMENT)


def _sight_wall(coords: List[int]) -> dict:
    """Wall that blocks sight/light but not movement."""
    return _wall_document(coords, wall_kind=WALL_KIND_SIGHT)


def _dense_wall(coords: List[int]) -> dict:
    """Wall that blocks movement and sight but is distinct from structure."""
    return _wall_document(coords, wall_kind=WALL_KIND_DENSE)


def _edge_wall(coords: List[int], edge, fallback_wall_kind: str = WALL_KIND_SOLID) -> dict:
    if getattr(edge, "has_door", False):
        return _wall_document(
            coords,
            door_kind=getattr(edge, "door_kind", None) or DOOR_KIND_NORMAL,
            door_state=getattr(edge, "door_state", None),
        )
    return _wall_document(
        coords,
        wall_kind=getattr(edge, "wall_kind", None) or fallback_wall_kind,
    )


def _wall_document(
    coords: List[int],
    door_kind: Optional[str] = None,
    door_state: Optional[str] = None,
    wall_kind: str = WALL_KIND_SOLID,
) -> dict:
    door_type = 0
    ds = 0
    light = 20
    move = 20
    sight = 20
    sound = 20

    if door_kind is not None:
        if door_kind == DOOR_KIND_SECRET:
            door_type = 2
        else:
            door_type = 1
        if (door_state or DOOR_STATE_CLOSED) == DOOR_STATE_OPEN:
            ds = 1
        elif (door_state or DOOR_STATE_CLOSED) == DOOR_STATE_LOCKED:
            ds = 2
        else:
            ds = 0
    elif wall_kind == WALL_KIND_MOVEMENT:
        light = 0
        sight = 0
        sound = 0
    elif wall_kind == WALL_KIND_SIGHT:
        move = 0
        light = 20
        sight = 20
        sound = 0
    elif wall_kind == WALL_KIND_DENSE:
        light = 20
        move = 20
        sight = 20
        sound = 0

    flags = {
        "donjuan": {
            "wall_kind": wall_kind,
            "door_kind": door_kind,
            "door_state": door_state or (DOOR_STATE_CLOSED if door_kind else None),
        }
    }
    return {
        "_id": _random_id(),
        "c": coords,
        "light": light,
        "move": move,
        "sight": sight,
        "sound": sound,
        "dir": 0,
        "door": door_type,
        "ds": ds,
        "threshold": {
            "light": None, "sight": None,
            "sound": None, "attenuation": False,
        },
        "flags": flags,
    }


# ── Torch light defaults (grid squares) ───────────────────────────────────────
_TORCH_BRIGHT = 3
_TORCH_DIM = 6


def _torch_light(cx: float, cy: float) -> dict:
    return {
        "_id": _random_id(),
        "x": cx,
        "y": cy,
        "rotation": 0,
        "walls": True,
        "vision": False,
        "config": {
            "alpha": 0.6,
            "angle": 360,
            "bright": _TORCH_BRIGHT,
            "color": "#ff9933",
            "coloration": 1,
            "dim": _TORCH_DIM,
            "attenuation": 0.5,
            "luminosity": 0.5,
            "saturation": 0,
            "contrast": 0,
            "shadows": 0,
            "animation": {
                "type": "torch",
                "speed": 5,
                "intensity": 5,
                "reverse": False,
            },
            "darkness": {"min": 0, "max": 1},
        },
        "flags": {},
    }
