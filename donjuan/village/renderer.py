"""
Textured renderer for VillageScene.
"""
import random as _random
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.core.hallway import Hallway
from donjuan.core.renderer import BaseRenderer
from donjuan.core.room import Room
from donjuan.village.scene import VillageScene, VillageTree

_PALETTE = {
    "grass_base": (82, 122, 64),
    "grass_hi": (102, 146, 80),
    "grass_lo": (62, 96, 50),
    "road_base": (150, 126, 92),
    "road_hi": (176, 152, 116),
    "road_lo": (112, 90, 64),
    "building_floor": (186, 168, 136),
    "building_wash": (210, 194, 162),
    "wall_line": (92, 66, 38),
    "door": (104, 70, 34),
    "tree_trunk": (90, 58, 26),
    "tree_canopy": (38, 92, 40),
    "tree_canopy_hi": (56, 126, 54),
}


class VillageRenderer(BaseRenderer):
    """Render a village as a textured outdoor settlement map."""

    def __init__(self, tile_size: int = 48):
        super().__init__(scale=float(tile_size))
        self.tile_size = tile_size
        self._last_image: Optional[Image.Image] = None

    def render(
        self,
        scene: VillageScene,
        file_path: str = "rendered_village.png",
        dpi: int = 96,
        save: bool = True,
    ) -> Tuple:
        img = self._build_image(scene)
        self._last_image = img
        if save:
            img.save(file_path)

        w_in = img.width / dpi
        h_in = img.height / dpi
        fig, ax = plt.subplots(1, figsize=(w_in, h_in), dpi=dpi)
        ax.imshow(np.array(img), interpolation="nearest")
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        return fig, ax

    def _build_image(self, scene: VillageScene) -> Image.Image:
        t = self.tile_size
        rows, cols = scene.n_rows, scene.n_cols
        img = Image.new("RGB", (cols * t, rows * t), _PALETTE["grass_base"])

        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                x0, y0 = c * t, r * t
                seed = r * 10_007 + c
                if cell.filled and isinstance(cell.space, VillageTree):
                    self._draw_ground(img, x0, y0, seed)
                elif isinstance(cell.space, Hallway):
                    self._draw_road(img, x0, y0, seed)
                elif isinstance(cell.space, Room):
                    self._draw_building_floor(img, x0, y0, seed)
                else:
                    self._draw_ground(img, x0, y0, seed)

        for building in scene.buildings.values():
            self._draw_building_walls(img, building)

        for building in scene.buildings.values():
            self._draw_doors(img, building)

        for tree in scene.trees.values():
            self._draw_tree(img, next(iter(tree.cells)))

        return self._apply_vignette(img)

    def _draw_ground(self, img: Image.Image, x0: int, y0: int, seed: int) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        base = _PALETTE["grass_base"]
        v = rng.randint(-12, 12)
        draw.rectangle(
            [x0, y0, x0 + t - 1, y0 + t - 1],
            fill=(
                min(255, max(0, base[0] + v)),
                min(255, max(0, base[1] + v)),
                min(255, max(0, base[2] + v)),
            ),
        )
        for _ in range(3):
            gx = x0 + rng.randint(0, t - 4)
            gy = y0 + rng.randint(0, t - 4)
            draw.ellipse([gx, gy, gx + 3, gy + 2], fill=_PALETTE["grass_hi"])

    def _draw_road(self, img: Image.Image, x0: int, y0: int, seed: int) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=_PALETTE["road_base"])
        for _ in range(4):
            rx = x0 + rng.randint(1, t - 5)
            ry = y0 + rng.randint(1, t - 5)
            rw = rng.randint(2, max(3, t // 5))
            rh = rng.randint(2, max(3, t // 5))
            draw.rectangle([rx, ry, rx + rw, ry + rh], fill=_PALETTE["road_hi"])

    def _draw_building_floor(self, img: Image.Image, x0: int, y0: int, seed: int) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [x0, y0, x0 + t - 1, y0 + t - 1],
            fill=_PALETTE["building_floor"],
        )
        for _ in range(2):
            rx = x0 + rng.randint(2, t - 8)
            ry = y0 + rng.randint(2, t - 8)
            draw.rectangle([rx, ry, rx + 4, ry + 3], fill=_PALETTE["building_wash"])

    def _draw_building_walls(self, img: Image.Image, building: Room) -> None:
        draw = ImageDraw.Draw(img)
        t = self.tile_size
        for cell in building.cells:
            for idx, edge in enumerate(cell.edges):
                if edge is None or edge.has_door:
                    continue
                c1, c2 = edge.cell1, edge.cell2
                neighbor = c1 if c2 is cell else c2
                if neighbor is not None and neighbor.space is building:
                    continue
                x, y = cell.x * t, cell.y * t
                if idx == 0:
                    draw.line([(x, y), (x + t, y)], fill=_PALETTE["wall_line"], width=3)
                elif idx == 1:
                    draw.line([(x, y), (x, y + t)], fill=_PALETTE["wall_line"], width=3)
                elif idx == 2:
                    draw.line([(x, y + t), (x + t, y + t)], fill=_PALETTE["wall_line"], width=3)
                else:
                    draw.line([(x + t, y), (x + t, y + t)], fill=_PALETTE["wall_line"], width=3)

    def _draw_doors(self, img: Image.Image, building: Room) -> None:
        draw = ImageDraw.Draw(img)
        t = self.tile_size
        for edge in building.entrances:
            c1, c2 = edge.cell1, edge.cell2
            if c1 is None or c2 is None:
                continue
            cell = c1 if c1.space is building else c2
            other = c2 if cell is c1 else c1
            if other is None:
                continue
            x, y = cell.x * t, cell.y * t
            if other.y < cell.y:
                draw.rectangle([x + t * 0.3, y - 1, x + t * 0.7, y + 3], fill=_PALETTE["door"])
            elif other.y > cell.y:
                draw.rectangle([x + t * 0.3, y + t - 3, x + t * 0.7, y + t + 1], fill=_PALETTE["door"])
            elif other.x < cell.x:
                draw.rectangle([x - 1, y + t * 0.3, x + 3, y + t * 0.7], fill=_PALETTE["door"])
            else:
                draw.rectangle([x + t - 3, y + t * 0.3, x + t + 1, y + t * 0.7], fill=_PALETTE["door"])

    def _draw_tree(self, img: Image.Image, cell) -> None:
        draw = ImageDraw.Draw(img)
        t = self.tile_size
        x0, y0 = cell.x * t, cell.y * t
        draw.ellipse(
            [x0 + t * 0.35, y0 + t * 0.5, x0 + t * 0.65, y0 + t * 0.95],
            fill=_PALETTE["tree_trunk"],
        )
        draw.ellipse(
            [x0 + t * 0.08, y0 + t * 0.08, x0 + t * 0.92, y0 + t * 0.86],
            fill=_PALETTE["tree_canopy"],
        )
        draw.ellipse(
            [x0 + t * 0.2, y0 + t * 0.14, x0 + t * 0.72, y0 + t * 0.56],
            fill=_PALETTE["tree_canopy_hi"],
        )

    def _apply_vignette(self, img: Image.Image) -> Image.Image:
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        cy, cx = h / 2.0, w / 2.0
        dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        dist /= dist.max()
        vignette = 1.0 - 0.18 * (dist ** 2)
        arr *= vignette[..., None]
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8))
