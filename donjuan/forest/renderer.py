"""
Procedural tile-based renderer for ForestScene.

Visual model
------------
* Open ground (most cells): grassy forest floor with per-tile colour variation.
* Undergrowth cells: denser darker foliage texture, small leaf-blob marks.
* Tree cells (filled=True): dark trunk oval with a layered green canopy on top.
  The canopy is drawn slightly larger than the cell so adjacent cells show
  a soft shadow/overhang, giving trees visual weight beyond one tile.
* Wall shadows: numpy gradient darkening the ground immediately adjacent to
  any tree, simulating the shadow cast by the canopy.
* Edge outlines: thin dark line on the ground side of every ground-tree edge.
* Vignette: subtle corner darkening.
"""
import random as _random
from math import sqrt
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.forest.scene import ForestScene, Tree, Undergrowth
from donjuan.core.renderer import BaseRenderer


# ── Colour palette ─────────────────────────────────────────────────────────────

_PALETTE = {
    # Open ground
    "ground_base":    (82,  105,  48),  # mid green-brown grass
    "ground_hi":      (96,  120,  58),  # lighter variation
    "ground_lo":      (68,   88,  36),  # darker variation

    # Undergrowth / brush
    "brush_base":     (45,   72,  22),  # dense low vegetation
    "brush_hi":       (58,   90,  28),  # lighter leaf highlight
    "brush_blob":     (35,   58,  15),  # leaf cluster marks

    # Tree trunk
    "trunk":          (38,   25,  12),  # dark brown bark
    "trunk_hi":       (60,   42,  20),  # lit side of trunk
    "trunk_shadow":   (22,   14,   6),  # shadow side

    # Tree canopy
    "canopy_dark":    (18,   48,  12),  # deep inner canopy
    "canopy_mid":     (28,   72,  18),  # main canopy fill
    "canopy_hi":      (42,   95,  28),  # sunlit canopy tip
    "canopy_edge":    (48,   28,   8),  # outer canopy edge — dark bark brown

    # Ground shadow under trees (cast by canopy)
    "tree_shadow":    (55,   78,  30),  # slightly darker ground near trees

    # Outlines
    "edge_line":      (12,   18,   6),  # thin line on ground-tree boundaries
}


class ForestRenderer(BaseRenderer):
    """
    Renders a :class:`~donjuan.forest.ForestScene` as a textured tile image
    using Pillow.

    Rendering stages:

    1. Open ground — grassy floor tile with per-cell noise variation
    2. Undergrowth — denser foliage on :class:`~donjuan.forest.Undergrowth` cells
    3. Tree canopy shadow — soft darkening on ground cells adjacent to trees
    4. Tree trunks — dark bark oval centred on each filled cell
    5. Tree canopy — layered green ellipses overdrawing the trunk, bleeding
       slightly into adjacent cells for visual weight
    6. Wall shadows — numpy gradient shadow cast from tree edges onto ground
    7. Edge outlines — thin dark line on ground side of ground-tree boundaries
    8. Vignette

    Args:
        tile_size (int): pixel width/height per cell (default 48)
        wall_shadows (bool): enable numpy gradient shadows (default True)
        canopy_bleed (bool): let tree canopy slightly overdraw adjacent cells
            (default True)
    """

    def __init__(
        self,
        tile_size: int = 48,
        wall_shadows: bool = True,
        canopy_bleed: bool = True,
    ):
        super().__init__(scale=float(tile_size))
        self.tile_size = tile_size
        self.wall_shadows = wall_shadows
        self.canopy_bleed = canopy_bleed
        self._last_image: Optional[Image.Image] = None

    def render(
        self,
        scene: ForestScene,
        file_path: str = "rendered_forest.png",
        dpi: int = 96,
        save: bool = True,
    ) -> Tuple:
        """
        Render *scene* to a Pillow image embedded in a matplotlib Figure.
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

    # ── Image construction ──────────────────────────────────────────────────────

    def _build_image(self, scene: ForestScene) -> Image.Image:
        t = self.tile_size
        rows, cols = scene.n_rows, scene.n_cols
        H, W = rows * t, cols * t

        # Extra padding so canopy bleed has room to draw beyond border cells
        pad = t if self.canopy_bleed else 0
        canvas_w, canvas_h = W + 2 * pad, H + 2 * pad

        img = Image.new("RGB", (canvas_w, canvas_h), _PALETTE["ground_base"])

        filled = np.array(
            [[scene.grid.cells[r][c].filled for c in range(cols)]
             for r in range(rows)],
            dtype=bool,
        )

        # ── Stage 1: open ground on all cells ─────────────────────────
        for r in range(rows):
            for c in range(cols):
                self._draw_ground(img, c * t + pad, r * t + pad,
                                  r * 10_007 + c)

        # ── Stage 2: undergrowth texture ───────────────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if isinstance(cell.space, Undergrowth):
                    self._draw_undergrowth(img, c * t + pad, r * t + pad,
                                           r * 10_007 + c + 3)

        # ── Stage 3: canopy ground shadow (drawn before trees) ─────────
        self._draw_canopy_ground_shadow(img, scene, filled, t, pad)

        # ── Stage 4: trunks first, then canopy so canopy overlaps trunk ─
        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    self._draw_trunk(img, c * t + pad, r * t + pad,
                                     r * 10_007 + c + 1)
        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    self._draw_canopy(img, c * t + pad, r * t + pad,
                                      r * 10_007 + c + 2)

        # ── Stage 6: wall shadows (numpy) ──────────────────────────────
        if self.wall_shadows:
            arr = np.array(img, dtype=np.float32)
            arr = self._apply_wall_shadows(arr, filled, t, pad,
                                           canvas_h, canvas_w)
            img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

        # ── Stage 7: edge outlines ─────────────────────────────────────
        self._draw_wall_lines(img, scene, t, pad)

        # Crop the padding border back to the true scene dimensions
        if pad:
            img = img.crop((pad, pad, pad + W, pad + H))

        # ── Stage 8: vignette ──────────────────────────────────────────
        return self._vignette(img)

    # ── Ground tile ──────────────────────────────────────────────────────────

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

        # 1–3 small grass tufts
        for _ in range(rng.randint(1, 3)):
            gx = x0 + rng.randint(2, t - 5)
            gy = y0 + rng.randint(2, t - 5)
            gw = rng.randint(2, max(3, t // 8))
            gh = rng.randint(1, max(2, t // 10))
            gv = rng.randint(0, 18)
            r1, g1, b1 = p["ground_hi"]
            draw.rectangle(
                [gx, gy, gx + gw, gy + gh],
                fill=(
                    min(255, max(0, r1 - gv // 2)),
                    min(255, max(0, g1 + gv)),
                    min(255, max(0, b1 - gv // 3)),
                ),
            )

    # ── Undergrowth tile ─────────────────────────────────────────────────────

    def _draw_undergrowth(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        v = rng.randint(-6, 6)
        r0, g0, b0 = p["brush_base"]
        draw.rectangle(
            [x0, y0, x0 + t - 1, y0 + t - 1],
            fill=(
                min(255, max(0, r0 + v)),
                min(255, max(0, g0 + v)),
                min(255, max(0, b0 + v // 2)),
            ),
        )

        # 2–4 leaf blob ellipses
        for _ in range(rng.randint(2, 4)):
            bx = x0 + rng.randint(1, max(2, t - t // 3))
            by = y0 + rng.randint(1, max(2, t - t // 3))
            bw = rng.randint(t // 5, t // 2)
            bh = rng.randint(t // 6, t // 3)
            bv = rng.randint(-4, 10)
            r1, g1, b1 = p["brush_hi"]
            draw.ellipse(
                [bx, by, bx + bw, by + bh],
                fill=(
                    min(255, max(0, r1 + bv)),
                    min(255, max(0, g1 + bv)),
                    min(255, max(0, b1 + bv // 2)),
                ),
            )

        # 1–2 darker detail blobs
        for _ in range(rng.randint(1, 2)):
            bx = x0 + rng.randint(2, max(3, t - t // 4))
            by = y0 + rng.randint(2, max(3, t - t // 4))
            bw = rng.randint(t // 7, t // 4)
            bh = rng.randint(t // 8, t // 5)
            draw.ellipse([bx, by, bx + bw, by + bh], fill=p["brush_blob"])

    # ── Canopy ground shadow ──────────────────────────────────────────────────

    def _draw_canopy_ground_shadow(
        self,
        img: Image.Image,
        scene: ForestScene,
        filled: np.ndarray,
        t: int,
        pad: int,
    ) -> None:
        """Draw soft dark patches on open ground cells bordering a tree."""
        draw = ImageDraw.Draw(img)
        rows, cols = scene.n_rows, scene.n_cols

        for r in range(rows):
            for c in range(cols):
                if filled[r, c]:
                    continue
                if not self._borders_tree(filled, r, c, rows, cols):
                    continue
                x0, y0 = c * t + pad, r * t + pad
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

        # Shadow offset
        draw.ellipse(
            [cx - ts + 2, cy - ts + 2, cx + ts + 2, cy + ts + 2],
            fill=p["trunk_shadow"],
        )
        # Main trunk
        draw.ellipse(
            [cx - ts, cy - ts, cx + ts, cy + ts],
            fill=p["trunk"],
        )
        # Highlight (top-left)
        hs = max(1, ts // 2)
        draw.ellipse(
            [cx - ts, cy - ts, cx - ts + hs * 2, cy - ts + hs * 2],
            fill=p["trunk_hi"],
        )

    # ── Tree canopy ───────────────────────────────────────────────────────────

    def _draw_canopy(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        """Layered green canopy, optionally bleeding beyond the cell boundary."""
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        p = _PALETTE

        cx = x0 + t // 2 + rng.randint(-t // 12, t // 12)
        cy = y0 + t // 2 + rng.randint(-t // 12, t // 12)

        bleed = (t * 3 // 10) if self.canopy_bleed else 0
        outer_r = t // 2 + bleed
        mid_r   = int(outer_r * 0.72)
        inner_r = int(outer_r * 0.42)

        # Outer dark ring
        v = rng.randint(-4, 4)
        r0, g0, b0 = p["canopy_edge"]
        draw.ellipse(
            [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r],
            fill=(min(255, max(0, r0 + v)),
                  min(255, max(0, g0 + v)),
                  min(255, max(0, b0 + v // 2))),
        )

        # Mid fill
        v = rng.randint(-6, 8)
        r0, g0, b0 = p["canopy_mid"]
        draw.ellipse(
            [cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r],
            fill=(min(255, max(0, r0 + v)),
                  min(255, max(0, g0 + v)),
                  min(255, max(0, b0 + v // 2))),
        )

        # Inner highlight blobs
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

    # ── Wall shadows (numpy) ──────────────────────────────────────────────────

    def _apply_wall_shadows(
        self,
        arr: np.ndarray,
        filled: np.ndarray,
        t: int,
        pad: int,
        H: int,
        W: int,
    ) -> np.ndarray:
        d = max(2, t // 3)
        ramp = np.linspace(0.62, 1.0, d, dtype=np.float32)
        shadow = np.ones((H, W), dtype=np.float32)

        rows, cols = filled.shape

        def _cast_row(mask, row_offset_fn):
            rs, cs = np.where(mask)
            for k in range(d):
                py = row_offset_fn(rs, k)
                valid = (py >= 0) & (py < H)
                py_v = py[valid]
                cs_v = cs[valid]
                col_start = cs_v * t + pad
                for j in range(t):
                    cx_idx = col_start + j
                    good = (cx_idx >= 0) & (cx_idx < W)
                    shadow[py_v[good], cx_idx[good]] = np.minimum(
                        shadow[py_v[good], cx_idx[good]], ramp[k]
                    )

        def _cast_col(mask, col_offset_fn):
            rs, cs = np.where(mask)
            for k in range(d):
                px = col_offset_fn(cs, k)
                valid = (px >= 0) & (px < W)
                px_v = px[valid]
                rs_v = rs[valid]
                row_start = rs_v * t + pad
                for j in range(t):
                    ry_idx = row_start + j
                    good = (ry_idx >= 0) & (ry_idx < H)
                    shadow[ry_idx[good], px_v[good]] = np.minimum(
                        shadow[ry_idx[good], px_v[good]], ramp[k]
                    )

        if rows > 1:
            _cast_row(filled[:-1, :] & ~filled[1:,  :],
                      lambda rs, k: (rs + 1) * t + k + pad)
            _cast_row(filled[1:,  :] & ~filled[:-1, :],
                      lambda rs, k: (rs + 1) * t - 1 - k + pad)
        if cols > 1:
            _cast_col(filled[:, :-1] & ~filled[:, 1:],
                      lambda cs, k: (cs + 1) * t + k + pad)
            _cast_col(filled[:, 1:]  & ~filled[:, :-1],
                      lambda cs, k: (cs + 1) * t - 1 - k + pad)

        arr *= shadow[:, :, np.newaxis]
        return arr

    # ── Edge outlines ─────────────────────────────────────────────────────────

    def _draw_wall_lines(
        self, img: Image.Image, scene: ForestScene, t: int, pad: int
    ) -> None:
        lw = max(1, t // 24)
        color = _PALETTE["edge_line"]
        draw = ImageDraw.Draw(img)
        rows, cols = scene.n_rows, scene.n_cols
        cells = scene.grid.cells

        for r in range(rows):
            for c in range(cols):
                if cells[r][c].filled:
                    continue
                x0, y0 = c * t + pad, r * t + pad

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
        factor = 1.0 - 0.30 * (dist / max_dist) ** 2
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
