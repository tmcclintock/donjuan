"""
Procedural tile-based renderer for CampScene.

Visual model
------------
* Open ground (most cells): warm beaten-earth dirt with per-tile variation.
* Tent cells: worn canvas texture with a ridge line along the long axis.
* FirePit cells: stone ring with ash fill; warm fire-glow radiates outward.
* CampPath cells: packed mud, slightly darker than open ground.
* CampTree cells (filled=True): dark trunk oval with layered green canopy.
  Trees cast a ground shadow onto adjacent open cells.
* Wall shadows: numpy gradient darkening at ground↔tree edges.
* Edge outlines: thin dark line on open side of open↔tree boundaries.
* Vignette: subtle corner darkening.
"""
import random as _random
from math import sqrt
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.camp.scene import CampPath, CampScene, CampTree, FirePit, Tent
from donjuan.core.renderer import BaseRenderer


# ── Colour palette ─────────────────────────────────────────────────────────────

_PALETTE = {
    # Open ground
    "ground_base":    (62,  46,  26),  # warm beaten earth
    "ground_hi":      (78,  60,  34),  # lighter dirt patch
    "ground_lo":      (48,  34,  18),  # darker variation

    # Tent canvas
    "tent_base":      (178, 148, 102), # worn canvas tan
    "tent_hi":        (198, 172, 122), # canvas highlight
    "tent_shadow":    (128, 100,  62), # canvas crease shadow
    "tent_ridge":     (80,   58,  30), # dark ridge pole line

    # Fire pit / stone ring
    "pit_stone":      (78,   72,  65), # grey stone ring
    "pit_stone_hi":   (108, 100,  90), # lit face of stone
    "pit_ash":        (58,   55,  50), # cold ash fill
    "fire_lo":        (200,  80,  12), # low flame orange
    "fire_hi":        (255, 200,  30), # hot flame yellow
    "ember":          (255, 240, 100), # bright ember dot

    # Path (packed mud)
    "path_base":      (88,   66,  36), # compacted mud
    "path_hi":        (108,  82,  48), # worn lighter strip

    # Tree trunk
    "trunk":          (52,   32,  14), # dark brown bark
    "trunk_hi":       (72,   48,  22), # lit side of trunk
    "trunk_shadow":   (30,   18,   6), # shadow side

    # Tree canopy
    "canopy_dark":    (18,   48,  12), # deep inner canopy
    "canopy_mid":     (28,   72,  18), # main canopy fill
    "canopy_hi":      (42,   95,  28), # sunlit canopy tip
    "canopy_edge":    (10,   30,   8), # outer canopy edge shadow

    # Ground shadow beneath tree canopy
    "tree_shadow":    (48,   34,  16), # slightly darker ground near trees

    # Outlines
    "edge_line":      (12,    8,   4), # thin line on open side of trees
}


class CampRenderer(BaseRenderer):
    """
    Renders a :class:`~donjuan.camp.CampScene` as a textured tile image
    using Pillow.

    Rendering stages:

    1. Open ground — warm dirt tile, all cells
    2. Space floors — tent canvas, fire-pit stone, path mud
    3. Canopy ground shadow — dark patches on ground cells bordering trees
    4. Tree trunks — dark bark oval centred on each filled (CampTree) cell
    5. Tree canopies — layered green ellipses overdrawing each trunk
    6. Tent ridge lines — dark peaked line along tent long axis
    7. Fire glow + wall shadows — numpy radial/gradient passes
    8. Embers — scattered bright dots near each fire cell (PIL)
    9. Edge outlines — thin dark line on open side of open↔tree edge
    10. Vignette

    Args:
        tile_size (int): pixel width/height per cell (default 48)
        fire_glow (bool): enable radial fire glow (default True)
        wall_shadows (bool): enable numpy gradient shadows (default True)
    """

    def __init__(
        self,
        tile_size: int = 48,
        fire_glow: bool = True,
        wall_shadows: bool = True,
    ):
        super().__init__(scale=float(tile_size))
        self.tile_size = tile_size
        self.fire_glow = fire_glow
        self.wall_shadows = wall_shadows
        self._last_image: Optional[Image.Image] = None

    def render(
        self,
        scene: CampScene,
        file_path: str = "rendered_camp.png",
        dpi: int = 96,
        save: bool = True,
    ) -> Tuple:
        """
        Render *scene* to a Pillow image embedded in a matplotlib Figure.

        Args:
            scene (CampScene): the scene to render
            file_path (str): output path if ``save=True``
            dpi (int): figure DPI
            save (bool): write image to disk

        Returns:
            ``(fig, ax)`` tuple
        """
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

    # ── Image construction ────────────────────────────────────────────────────

    def _build_image(self, scene: CampScene) -> Image.Image:
        t = self.tile_size
        rows, cols = scene.n_rows, scene.n_cols
        H, W = rows * t, cols * t

        filled = np.array(
            [[scene.grid.cells[r][c].filled for c in range(cols)]
             for r in range(rows)],
            dtype=bool,
        )

        img = Image.new("RGB", (W, H), _PALETTE["ground_base"])

        # ── Stage 1: open ground on every cell ────────────────────────
        for r in range(rows):
            for c in range(cols):
                self._draw_ground(img, c * t, r * t, r * 10_007 + c)

        # ── Stage 2: space-specific floor tiles ───────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if cell.filled:
                    continue  # trees are drawn later
                seed = r * 10_007 + c
                if isinstance(cell.space, Tent):
                    self._draw_tent_floor(img, c * t, r * t, seed)
                elif isinstance(cell.space, FirePit):
                    self._draw_pit_floor(img, c * t, r * t, seed)
                elif isinstance(cell.space, CampPath):
                    self._draw_path_floor(img, c * t, r * t, seed)

        # ── Stage 3: canopy ground shadow (before trees) ──────────────
        self._draw_canopy_ground_shadow(img, scene, filled, t)

        # ── Stage 4: tree trunks ──────────────────────────────────────
        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    self._draw_trunk(img, c * t, r * t, r * 10_007 + c + 1)

        # ── Stage 5: tree canopies ────────────────────────────────────
        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    self._draw_canopy(img, c * t, r * t, r * 10_007 + c + 2)

        # ── Stage 6: tent ridge lines ─────────────────────────────────
        for tent in scene.tents.values():
            self._draw_tent_ridge(img, tent, t)

        # ── Stage 7: fire glow + wall shadows (numpy) ─────────────────
        arr = np.array(img, dtype=np.float32)
        if self.fire_glow and scene.fires:
            arr = self._apply_fire_glow(arr, scene, filled)
        if self.wall_shadows:
            arr = self._apply_wall_shadows(arr, filled, H, W)
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

        # ── Stage 8: ember sparks (PIL, after lighting) ───────────────
        for fire in scene.fires:
            self._draw_embers(img, fire, t)

        # ── Stage 9: edge outlines ────────────────────────────────────
        self._draw_wall_lines(img, scene)

        # ── Stage 10: vignette ────────────────────────────────────────
        return self._vignette(img)

    # ── Tile drawers ──────────────────────────────────────────────────────────

    def _draw_ground(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        v = rng.randint(-10, 10)
        r0, g0, b0 = p["ground_base"]
        draw.rectangle(
            [x0, y0, x0 + t - 1, y0 + t - 1],
            fill=(
                min(255, max(0, r0 + v)),
                min(255, max(0, g0 + v)),
                min(255, max(0, b0 + v // 2)),
            ),
        )

        # 1–3 small pebble / twig marks
        for _ in range(rng.randint(1, 3)):
            gx = x0 + rng.randint(2, t - 5)
            gy = y0 + rng.randint(2, t - 5)
            gw = rng.randint(2, max(3, t // 8))
            gh = rng.randint(1, max(2, t // 10))
            gv = rng.randint(0, 16)
            r1, g1, b1 = p["ground_hi"]
            draw.rectangle(
                [gx, gy, gx + gw, gy + gh],
                fill=(
                    min(255, max(0, r1 + gv // 2)),
                    min(255, max(0, g1 + gv // 3)),
                    min(255, max(0, b1 + gv // 4)),
                ),
            )

    def _draw_tent_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["tent_base"])

        # Woven grain — horizontal lines
        n_lines = max(2, t // 12)
        for i in range(n_lines):
            ly = y0 + (i * t) // n_lines + rng.randint(0, t // n_lines)
            v = rng.randint(-8, 8)
            r0c, g0c, b0c = p["tent_shadow"]
            draw.line(
                [(x0 + 1, ly), (x0 + t - 2, ly)],
                fill=(
                    min(255, max(0, r0c + v)),
                    min(255, max(0, g0c + v)),
                    min(255, max(0, b0c + v)),
                ),
                width=1,
            )

        # Highlight patch
        hs = max(2, t // 4)
        r0c, g0c, b0c = p["tent_hi"]
        v = rng.randint(-6, 6)
        draw.rectangle(
            [x0 + 2, y0 + 2, x0 + hs, y0 + hs],
            fill=(min(255, r0c + v), min(255, g0c + v), min(255, b0c + v)),
        )

    def _draw_pit_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["pit_stone"])

        inner = max(2, t // 3)
        cx, cy = x0 + t // 2, y0 + t // 2
        draw.ellipse(
            [cx - inner, cy - inner, cx + inner, cy + inner],
            fill=p["pit_ash"],
        )

        hs = max(2, t // 5)
        draw.rectangle(
            [x0 + 1, y0 + 1, x0 + hs, y0 + hs],
            fill=p["pit_stone_hi"],
        )

    def _draw_path_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["path_base"])

        # Worn centre strip
        strip_w = max(2, t // 4)
        cx = x0 + t // 2
        r0c, g0c, b0c = p["path_hi"]
        v = rng.randint(-4, 4)
        draw.rectangle(
            [cx - strip_w // 2, y0, cx + strip_w // 2, y0 + t - 1],
            fill=(
                min(255, max(0, r0c + v)),
                min(255, max(0, g0c + v)),
                min(255, max(0, b0c + v)),
            ),
        )

    # ── Canopy ground shadow ──────────────────────────────────────────────────

    def _draw_canopy_ground_shadow(
        self,
        img: Image.Image,
        scene: CampScene,
        filled: np.ndarray,
        t: int,
    ) -> None:
        """Draw soft dark patches on open ground cells adjacent to trees."""
        draw = ImageDraw.Draw(img)
        rows, cols = scene.n_rows, scene.n_cols

        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    continue
                if not self._borders_tree(filled, r, c, rows, cols):
                    continue
                x0, y0 = c * t, r * t
                rng = _random.Random(r * 10_007 + c + 7_777)
                for _ in range(rng.randint(2, 3)):
                    ex = x0 + rng.randint(0, max(1, t - t // 3))
                    ey = y0 + rng.randint(0, max(1, t - t // 3))
                    ew = rng.randint(t // 4, t * 2 // 3)
                    eh = rng.randint(t // 4, t * 2 // 3)
                    draw.ellipse([ex, ey, ex + ew, ey + eh],
                                 fill=_PALETTE["tree_shadow"])

    # ── Tree trunk ────────────────────────────────────────────────────────────

    def _draw_trunk(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        ts = max(3, t // 5)
        cx = x0 + t // 2 + rng.randint(-t // 10, t // 10)
        cy = y0 + t // 2 + rng.randint(-t // 10, t // 10)

        draw.ellipse(
            [cx - ts + 2, cy - ts + 2, cx + ts + 2, cy + ts + 2],
            fill=p["trunk_shadow"],
        )
        draw.ellipse(
            [cx - ts, cy - ts, cx + ts, cy + ts],
            fill=p["trunk"],
        )
        hs = max(1, ts // 2)
        draw.ellipse(
            [cx - ts, cy - ts, cx - ts + hs * 2, cy - ts + hs * 2],
            fill=p["trunk_hi"],
        )

    # ── Tree canopy ───────────────────────────────────────────────────────────

    def _draw_canopy(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        """Layered green canopy drawn within the cell boundary."""
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        cx = x0 + t // 2 + rng.randint(-t // 12, t // 12)
        cy = y0 + t // 2 + rng.randint(-t // 12, t // 12)

        outer_r = t // 2 - 1
        mid_r   = int(outer_r * 0.72)
        inner_r = int(outer_r * 0.42)

        v = rng.randint(-4, 4)
        r0, g0, b0 = p["canopy_edge"]
        draw.ellipse(
            [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
            fill=(min(255, max(0, r0 + v)),
                  min(255, max(0, g0 + v)),
                  min(255, max(0, b0 + v // 2))),
        )

        v = rng.randint(-6, 8)
        r0, g0, b0 = p["canopy_mid"]
        draw.ellipse(
            [cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r],
            fill=(min(255, max(0, r0 + v)),
                  min(255, max(0, g0 + v)),
                  min(255, max(0, b0 + v // 2))),
        )

        for _ in range(rng.randint(2, 3)):
            ox = rng.randint(-inner_r // 2, inner_r // 2)
            oy = rng.randint(-inner_r // 2, inner_r // 2)
            hr = rng.randint(inner_r // 2, inner_r)
            v2 = rng.randint(0, 12)
            r1, g1, b1 = p["canopy_hi"]
            draw.ellipse(
                [cx + ox - hr, cy + oy - hr, cx + ox + hr, cy + oy + hr],
                fill=(min(255, max(0, r1 + v2)),
                      min(255, max(0, g1 + v2)),
                      min(255, max(0, b1 + v2 // 2))),
            )

    # ── Tent ridge ────────────────────────────────────────────────────────────

    def _draw_tent_ridge(self, img: Image.Image, tent: Tent, t: int) -> None:
        """Draw a dark ridge line along the centre of a tent's bounding box."""
        if not tent.cells:
            return
        draw = ImageDraw.Draw(img)

        ys = [c.y for c in tent.cells]
        xs = [c.x for c in tent.cells]
        min_r, max_r = min(ys), max(ys)
        min_c, max_c = min(xs), max(xs)
        height = max_r - min_r + 1
        width  = max_c - min_c + 1

        if height >= width:
            # Vertical tent — ridge runs top to bottom at centre column
            cx = (min_c + max_c) // 2
            px = cx * t + t // 2
            img_draw = ImageDraw.Draw(img)
            img_draw.line(
                [(px, min_r * t + 1), (px, (max_r + 1) * t - 2)],
                fill=_PALETTE["tent_ridge"],
                width=max(1, t // 16),
            )
        else:
            # Horizontal tent — ridge runs left to right at centre row
            cy_cell = (min_r + max_r) // 2
            py = cy_cell * t + t // 2
            img_draw = ImageDraw.Draw(img)
            img_draw.line(
                [(min_c * t + 1, py), ((max_c + 1) * t - 2, py)],
                fill=_PALETTE["tent_ridge"],
                width=max(1, t // 16),
            )

    # ── Fire glow ─────────────────────────────────────────────────────────────

    def _apply_fire_glow(
        self,
        arr: np.ndarray,
        scene: CampScene,
        filled: np.ndarray,
    ) -> np.ndarray:
        t = self.tile_size
        H, W = arr.shape[:2]
        radius = t * 3.5

        floor_mask = np.kron(~filled, np.ones((t, t), dtype=bool))
        py_g, px_g = np.mgrid[0:H, 0:W]

        for fire in scene.fires:
            pit_cells = list(fire.cells)
            ys = [c.y for c in pit_cells]
            xs = [c.x for c in pit_cells]
            pit_cy = (sum(ys) / len(ys) + 0.5) * t
            pit_cx = (sum(xs) / len(xs) + 0.5) * t

            dist = np.sqrt((px_g - pit_cx) ** 2 + (py_g - pit_cy) ** 2)
            glow = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 1.5
            glow[~floor_mask] = 0.0

            arr[:, :, 0] = np.clip(arr[:, :, 0] + glow * 110, 0, 255)
            arr[:, :, 1] = np.clip(arr[:, :, 1] + glow * 50,  0, 255)
            arr[:, :, 2] = np.clip(arr[:, :, 2] - glow * 10,  0, 255)

        return arr

    # ── Embers ────────────────────────────────────────────────────────────────

    def _draw_embers(
        self, img: Image.Image, fire: FirePit, t: int
    ) -> None:
        p = _PALETTE
        draw = ImageDraw.Draw(img)
        pit_cells = list(fire.cells)
        rng = _random.Random(id(fire))

        for _ in range(15):
            cell = rng.choice(pit_cells)
            x0, y0 = cell.x * t, cell.y * t
            ex = x0 + rng.randint(2, t - 2)
            ey = y0 + rng.randint(2, t - 2)
            es = max(1, t // 20)
            color = p["fire_hi"] if rng.random() < 0.5 else p["ember"]
            draw.ellipse([ex - es, ey - es, ex + es, ey + es], fill=color)

    # ── Wall shadows ──────────────────────────────────────────────────────────

    def _apply_wall_shadows(
        self,
        arr: np.ndarray,
        filled: np.ndarray,
        H: int,
        W: int,
    ) -> np.ndarray:
        t = self.tile_size
        d = max(2, t // 3)
        ramp = np.linspace(0.52, 1.0, d, dtype=np.float32)
        shadow = np.ones((H, W), dtype=np.float32)

        rows, cols = filled.shape

        def _cast_row(mask, row_offset_fn):
            rs, cs = np.where(mask)
            for k in range(d):
                py = row_offset_fn(rs, k)
                valid = (py >= 0) & (py < H)
                py_v, cs_v = py[valid], cs[valid]
                for j in range(t):
                    cx_idx = cs_v * t + j
                    good = (cx_idx >= 0) & (cx_idx < W)
                    shadow[py_v[good], cx_idx[good]] = np.minimum(
                        shadow[py_v[good], cx_idx[good]], ramp[k]
                    )

        def _cast_col(mask, col_offset_fn):
            rs, cs = np.where(mask)
            for k in range(d):
                px = col_offset_fn(cs, k)
                valid = (px >= 0) & (px < W)
                rs_v, px_v = rs[valid], px[valid]
                for j in range(t):
                    ry_idx = rs_v * t + j
                    good = (ry_idx >= 0) & (ry_idx < H)
                    shadow[ry_idx[good], px_v[good]] = np.minimum(
                        shadow[ry_idx[good], px_v[good]], ramp[k]
                    )

        if rows > 1:
            _cast_row(filled[:-1, :] & ~filled[1:,  :],
                      lambda rs, k: (rs + 1) * t + k)
            _cast_row(filled[1:,  :] & ~filled[:-1, :],
                      lambda rs, k: (rs + 1) * t - 1 - k)
        if cols > 1:
            _cast_col(filled[:, :-1] & ~filled[:, 1:],
                      lambda cs, k: (cs + 1) * t + k)
            _cast_col(filled[:, 1:]  & ~filled[:, :-1],
                      lambda cs, k: (cs + 1) * t - 1 - k)

        arr *= shadow[:, :, np.newaxis]
        return arr

    # ── Edge outlines ─────────────────────────────────────────────────────────

    def _draw_wall_lines(self, img: Image.Image, scene: CampScene) -> None:
        t = self.tile_size
        lw = max(1, t // 24)
        color = _PALETTE["edge_line"]
        draw = ImageDraw.Draw(img)
        rows, cols = scene.n_rows, scene.n_cols
        cells = scene.grid.cells

        for r in range(rows):
            for c in range(cols):
                if cells[r][c].filled:
                    continue
                x0, y0 = c * t, r * t

                if r == 0 or cells[r - 1][c].filled:
                    draw.rectangle([x0, y0, x0 + t - 1, y0 + lw - 1], fill=color)
                if r == rows - 1 or cells[r + 1][c].filled:
                    draw.rectangle([x0, y0 + t - lw, x0 + t - 1, y0 + t - 1], fill=color)
                if c == 0 or cells[r][c - 1].filled:
                    draw.rectangle([x0, y0, x0 + lw - 1, y0 + t - 1], fill=color)
                if c == cols - 1 or cells[r][c + 1].filled:
                    draw.rectangle([x0 + t - lw, y0, x0 + t - 1, y0 + t - 1], fill=color)

    # ── Vignette ──────────────────────────────────────────────────────────────

    @staticmethod
    def _vignette(img: Image.Image) -> Image.Image:
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        cx, cy = w / 2.0, h / 2.0
        max_dist = sqrt(cx ** 2 + cy ** 2)
        ys, xs = np.mgrid[0:h, 0:w]
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        factor = 1.0 - 0.35 * (dist / max_dist) ** 2
        arr *= factor[:, :, np.newaxis]
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8))

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _borders_tree(
        filled: np.ndarray, r: int, c: int, rows: int, cols: int
    ) -> bool:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and filled[nr, nc]:
                return True
        return False
