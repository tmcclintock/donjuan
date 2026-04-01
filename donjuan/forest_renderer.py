"""
Procedural tile-based renderer for ForestScene.
"""
import random as _random
from math import sqrt
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.forest import Clearing, ForestPath, ForestScene
from donjuan.renderer import BaseRenderer


# ── Colour palette ─────────────────────────────────────────────────────────────

_PALETTE = {
    # Background / tree fill
    "outside":        (12,  28,  10),   # near-black dark green
    "tree_base":      (18,  38,  14),   # deep forest shadow
    "tree_bark":      (45,  32,  18),   # dark brown trunk oval
    "tree_bark_hi":   (72,  52,  28),   # lighter bark highlight
    "tree_canopy":    (22,  55,  18),   # mid-green canopy fill
    "canopy_hi":      (38,  82,  28),   # lighter canopy specular
    "canopy_shadow":  (8,   20,   6),   # dappled shadow patch

    # Clearing floor
    "clearing_base":  (88, 108,  42),   # grassy open ground
    "clearing_hi":    (108, 128,  55),  # brighter grass variation
    "grass_blade":    (55,  85,  22),   # individual blade stroke

    # Path floor
    "path_base":      (98,  75,  40),   # packed dirt
    "path_hi":        (118,  92,  52),  # lighter dirt variation
    "path_pebble":    (68,  58,  38),   # small pebble mark

    # Details
    "wall_line":      (8,   15,   6),   # dark outline on clearing edges
    "shadow_mult":    0.48,             # floor-cell shadow darkening factor
}


class ForestRenderer(BaseRenderer):
    """
    Renders a :class:`~donjuan.forest.ForestScene` as a textured tile image
    using Pillow.

    Rendering stages:

    1. Base fill — dark tree canopy for all cells
    2. Tree trunks — bark oval + highlight on filled cells that border open space
    3. Canopy — layered green fills on filled cells
    4. Floor tiles — grass (Clearing) or dirt (ForestPath) with per-tile noise
    5. Grass blades — short PIL line strokes on Clearing cells
    6. Canopy shadows — dappled dark patches on open cells near trees
    7. Wall shadows — numpy gradient darkening near tree edges
    8. Edge outlines — thin dark line on open side of filled↔open boundary
    9. Vignette

    Args:
        tile_size (int): pixel width/height per cell (default 48)
        canopy_shadows (bool): enable dappled shadow patches (default True)
        wall_shadows (bool): enable numpy gradient shadows (default True)
    """

    def __init__(
        self,
        tile_size: int = 48,
        canopy_shadows: bool = True,
        wall_shadows: bool = True,
    ):
        super().__init__(scale=float(tile_size))
        self.tile_size = tile_size
        self.canopy_shadows = canopy_shadows
        self.wall_shadows = wall_shadows
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

        Args:
            scene (ForestScene): the scene to render
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

    # ── Image construction ──────────────────────────────────────────────────────

    def _build_image(self, scene: ForestScene) -> Image.Image:
        t = self.tile_size
        rows, cols = scene.n_rows, scene.n_cols
        H, W = rows * t, cols * t
        p = _PALETTE

        img = Image.new("RGB", (W, H), p["outside"])

        filled = np.array(
            [[scene.grid.cells[r][c].filled for c in range(cols)]
             for r in range(rows)],
            dtype=bool,
        )

        # ── Stage 1: tree canopy on all filled cells ───────────────────
        for r in range(rows):
            for c in range(cols):
                if scene.grid.cells[r][c].filled:
                    self._draw_tree_canopy(img, c * t, r * t, r * 10_007 + c)

        # ── Stage 2: tree trunks on filled cells bordering open space ──
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if not cell.filled:
                    continue
                if self._borders_open(scene, r, c):
                    self._draw_trunk(img, c * t, r * t, r * 10_007 + c + 1)

        # ── Stage 3: floor tiles on open cells ────────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if cell.filled:
                    continue
                seed = r * 10_007 + c
                if isinstance(cell.space, Clearing):
                    self._draw_clearing_floor(img, c * t, r * t, seed)
                elif isinstance(cell.space, ForestPath):
                    self._draw_path_floor(img, c * t, r * t, seed)
                else:
                    # Bare open cell — treat as clearing
                    self._draw_clearing_floor(img, c * t, r * t, seed)

        # ── Stage 4: grass blades on Clearing cells ────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if isinstance(cell.space, Clearing):
                    self._draw_grass_blades(img, c * t, r * t, r * 10_007 + c + 2)

        # ── Stage 5: canopy shadow patches near trees ──────────────────
        if self.canopy_shadows:
            self._apply_canopy_shadows(img, scene, filled)

        # ── Stage 6 + 7: numpy shadows ────────────────────────────────
        arr = np.array(img, dtype=np.float32)
        if self.wall_shadows:
            arr = self._apply_wall_shadows(arr, scene, filled)
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

        # ── Stage 8: edge outlines ─────────────────────────────────────
        self._draw_wall_lines(img, scene)

        # ── Stage 9: vignette ──────────────────────────────────────────
        return self._vignette(img)

    # ── Tree drawing ────────────────────────────────────────────────────────────

    def _draw_tree_canopy(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        """Fill a cell with a layered green canopy."""
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        # Base dark green fill
        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["tree_base"])

        # Two overlapping ellipse blobs for canopy texture
        for _ in range(2):
            rx = rng.randint(t // 4, t * 3 // 4)
            ry = rng.randint(t // 4, t * 3 // 4)
            ew = rng.randint(t // 3, t * 2 // 3)
            eh = rng.randint(t // 3, t * 2 // 3)
            v = rng.randint(-8, 8)
            r0, g0, b0 = p["tree_canopy"]
            draw.ellipse(
                [x0 + rx, y0 + ry, x0 + rx + ew, y0 + ry + eh],
                fill=(
                    min(255, max(0, r0 + v)),
                    min(255, max(0, g0 + v)),
                    min(255, max(0, b0 + v // 2)),
                ),
            )

    def _draw_trunk(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        """Draw a small bark oval near the centre of a filled cell."""
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        ts = max(3, t // 6)   # trunk half-size
        # Slight random offset so trunks aren't perfectly centred
        cx = x0 + t // 2 + rng.randint(-t // 8, t // 8)
        cy = y0 + t // 2 + rng.randint(-t // 8, t // 8)

        draw.ellipse(
            [cx - ts, cy - ts, cx + ts, cy + ts],
            fill=p["tree_bark"],
        )
        # Highlight arc (top-left quadrant)
        hs = max(1, ts // 2)
        draw.ellipse(
            [cx - ts, cy - ts, cx - ts + hs * 2, cy - ts + hs * 2],
            fill=p["tree_bark_hi"],
        )

    # ── Floor tile drawing ──────────────────────────────────────────────────────

    def _draw_clearing_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["clearing_base"])

        # 2×2 sub-tiles with variation
        half = t // 2
        for ri in range(2):
            for ci in range(2):
                v = rng.randint(-12, 12)
                r0, g0, b0 = p["clearing_hi"]
                sx = x0 + ci * half + rng.randint(0, 2)
                sy = y0 + ri * half + rng.randint(0, 2)
                ex = x0 + (ci + 1) * half - rng.randint(0, 2)
                ey = y0 + (ri + 1) * half - rng.randint(0, 2)
                if ex <= sx or ey <= sy:
                    continue
                draw.rectangle(
                    [sx, sy, ex, ey],
                    fill=(
                        min(255, max(0, r0 + v)),
                        min(255, max(0, g0 + v)),
                        min(255, max(0, b0 + v // 2)),
                    ),
                )

    def _draw_path_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["path_base"])

        # Irregular dirt patches
        for _ in range(3):
            px = x0 + rng.randint(2, t - 4)
            py = y0 + rng.randint(2, t - 4)
            pw = rng.randint(t // 6, t // 3)
            ph = rng.randint(t // 6, t // 3)
            v = rng.randint(-10, 10)
            r0, g0, b0 = p["path_hi"]
            draw.ellipse(
                [px, py, px + pw, py + ph],
                fill=(
                    min(255, max(0, r0 + v)),
                    min(255, max(0, g0 + v // 2)),
                    min(255, max(0, b0 + v // 3)),
                ),
            )

        # Pebble marks
        for _ in range(2):
            px = x0 + rng.randint(3, t - 5)
            py = y0 + rng.randint(3, t - 5)
            ps = max(1, t // 16)
            draw.ellipse([px, py, px + ps, py + ps], fill=p["path_pebble"])

    def _draw_grass_blades(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)
        n = rng.randint(3, 6)
        for _ in range(n):
            bx = x0 + rng.randint(3, t - 3)
            by = y0 + rng.randint(3, t - 3)
            tip_x = bx + rng.randint(-t // 6, t // 6)
            tip_y = by - rng.randint(t // 8, t // 4)
            # Clamp to cell
            tip_x = max(x0, min(x0 + t - 1, tip_x))
            tip_y = max(y0, min(y0 + t - 1, tip_y))
            draw.line([(bx, by), (tip_x, tip_y)], fill=p["grass_blade"], width=1)

    # ── Canopy shadow patches ────────────────────────────────────────────────────

    def _apply_canopy_shadows(
        self,
        img: Image.Image,
        scene: ForestScene,
        filled: np.ndarray,
    ) -> None:
        p = _PALETTE
        draw = ImageDraw.Draw(img)
        t = self.tile_size
        rows, cols = scene.n_rows, scene.n_cols

        for r in range(rows):
            for c in range(cols):
                if scene.grid.cells[r][c].filled:
                    continue
                if not self._borders_filled(filled, r, c, rows, cols):
                    continue
                rng = _random.Random(r * 10_007 + c + 9_999)
                n = rng.randint(1, 3)
                for _ in range(n):
                    x0, y0 = c * t, r * t
                    px = x0 + rng.randint(0, t - t // 3)
                    py = y0 + rng.randint(0, t - t // 3)
                    pw = rng.randint(t // 5, t // 2)
                    ph = rng.randint(t // 5, t // 2)
                    draw.ellipse(
                        [px, py, px + pw, py + ph],
                        fill=p["canopy_shadow"],
                    )

    @staticmethod
    def _borders_filled(
        filled: np.ndarray, r: int, c: int, rows: int, cols: int
    ) -> bool:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and filled[nr, nc]:
                return True
        return False

    @staticmethod
    def _borders_open(scene: ForestScene, r: int, c: int) -> bool:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < scene.n_rows
                and 0 <= nc < scene.n_cols
                and not scene.grid.cells[nr][nc].filled
            ):
                return True
        return False

    # ── Wall shadows (numpy) ────────────────────────────────────────────────────

    def _apply_wall_shadows(
        self,
        arr: np.ndarray,
        scene: ForestScene,
        filled: np.ndarray,
    ) -> np.ndarray:
        t = self.tile_size
        d = max(2, t // 3)
        H, W = arr.shape[:2]
        ramp = np.linspace(0.50, 1.0, d, dtype=np.float32)
        shadow = np.ones((H, W), dtype=np.float32)

        def _cast(mask, get_pr):
            rs, cs = np.where(mask)
            for k in range(d):
                pr = get_pr(rs, k)
                valid = (pr >= 0) & (pr < H)
                pr_v, cs_v = pr[valid], cs[valid]
                col_idx = cs_v[:, None] * t + np.arange(t)[None, :]
                cur = shadow[pr_v[:, None], col_idx]
                shadow[pr_v[:, None], col_idx] = np.minimum(cur, ramp[k])

        def _cast_col(mask, get_pc):
            rs, cs = np.where(mask)
            for k in range(d):
                pc = get_pc(cs, k)
                valid = (pc >= 0) & (pc < W)
                rs_v, pc_v = rs[valid], pc[valid]
                row_idx = rs_v[:, None] * t + np.arange(t)[None, :]
                cur = shadow[row_idx, pc_v[:, None]]
                shadow[row_idx, pc_v[:, None]] = np.minimum(cur, ramp[k])

        rows, cols = scene.n_rows, scene.n_cols

        if rows > 1:
            _cast(filled[:-1, :] & ~filled[1:,  :],
                  lambda rs, k: (rs + 1) * t + k)
            _cast(filled[1:,  :] & ~filled[:-1, :],
                  lambda rs, k: (rs + 1) * t - 1 - k)
        if cols > 1:
            _cast_col(filled[:, :-1] & ~filled[:, 1:],
                      lambda cs, k: (cs + 1) * t + k)
            _cast_col(filled[:, 1:]  & ~filled[:, :-1],
                      lambda cs, k: (cs + 1) * t - 1 - k)

        arr *= shadow[:, :, np.newaxis]
        return arr

    # ── Edge outlines ────────────────────────────────────────────────────────────

    def _draw_wall_lines(self, img: Image.Image, scene: ForestScene) -> None:
        t = self.tile_size
        lw = max(1, t // 24)
        color = _PALETTE["wall_line"]
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

    # ── Vignette ─────────────────────────────────────────────────────────────────

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
