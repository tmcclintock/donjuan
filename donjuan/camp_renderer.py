"""
Procedural tile-based renderer for CampScene.
"""
import random as _random
from math import sqrt
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.camp import CampPath, CampScene, FirePit, Tent
from donjuan.renderer import BaseRenderer


# ── Colour palette ─────────────────────────────────────────────────────────────

_PALETTE = {
    # Background undergrowth
    "outside":          (20,  14,   8),  # near-black dark earth
    "undergrowth_base": (28,  20,  10),  # dark soil / fallen leaves
    "undergrowth_hi":   (42,  30,  15),  # lighter leaf litter

    # Tent canvas
    "tent_base":        (178, 148, 102), # worn canvas tan
    "tent_hi":          (198, 172, 122), # canvas highlight
    "tent_shadow":      (128, 100,  62), # canvas shadow crease
    "tent_ridge":       (80,   58,  30), # dark ridge pole line

    # Fire pit / stone ring
    "pit_stone":        (78,  72,  65),  # grey stone ring
    "pit_stone_hi":     (108, 100,  90), # lit face of stone
    "pit_ash":          (58,  55,  50),  # cold ash fill
    "fire_lo":          (200,  80,  12), # low flame orange
    "fire_hi":          (255, 200,  30), # hot flame yellow
    "ember":            (255, 240, 100), # bright ember dot

    # Path
    "path_base":        (102,  80,  45), # packed mud
    "path_hi":          (122,  96,  58), # worn lighter strip

    # Details
    "wall_line":        (10,   8,   4),  # dark outline
}


class CampRenderer(BaseRenderer):
    """
    Renders a :class:`~donjuan.camp.CampScene` as a textured tile image
    using Pillow.

    Rendering stages:

    1. Base fill — dark undergrowth for all filled cells
    2. Floor tiles — canvas (Tent), stone+ash (FirePit), mud (CampPath)
    3. Tent ridge line — dark peaked line across each tent
    4. Fire glow — radial warm gradient around FirePit cells (numpy)
    5. Embers — scattered bright dots near the fire pit
    6. Wall shadows — numpy gradient darkening at undergrowth edges
    7. Edge outlines — thin dark line on open side of filled↔open boundary
    8. Vignette

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

    # ── Image construction ──────────────────────────────────────────────────────

    def _build_image(self, scene: CampScene) -> Image.Image:
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

        # ── Stage 1: undergrowth texture on filled cells ───────────────
        for r in range(rows):
            for c in range(cols):
                if scene.grid.cells[r][c].filled:
                    self._draw_undergrowth(img, c * t, r * t, r * 10_007 + c)

        # ── Stage 2: floor tiles on open cells ────────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = scene.grid.cells[r][c]
                if cell.filled:
                    continue
                seed = r * 10_007 + c
                if isinstance(cell.space, Tent):
                    self._draw_tent_floor(img, c * t, r * t, seed)
                elif isinstance(cell.space, FirePit):
                    self._draw_pit_floor(img, c * t, r * t, seed)
                elif isinstance(cell.space, CampPath):
                    self._draw_path_floor(img, c * t, r * t, seed)
                else:
                    self._draw_path_floor(img, c * t, r * t, seed)

        # ── Stage 3: tent ridge lines ─────────────────────────────────
        for tent in scene.tents.values():
            self._draw_tent_ridge(img, tent, t)

        # ── Stage 4+5: fire glow + embers (numpy pass) ────────────────
        arr = np.array(img, dtype=np.float32)
        if self.fire_glow and scene.fire_pit is not None:
            arr = self._apply_fire_glow(arr, scene, filled)
        if self.wall_shadows:
            arr = self._apply_wall_shadows(arr, scene, filled)
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

        # ── Stage 5: ember sparks (PIL, after lighting) ────────────────
        if scene.fire_pit is not None:
            self._draw_embers(img, scene.fire_pit, t)

        # ── Stage 6: edge outlines ─────────────────────────────────────
        self._draw_wall_lines(img, scene)

        # ── Stage 7: vignette ──────────────────────────────────────────
        return self._vignette(img)

    # ── Tile drawers ─────────────────────────────────────────────────────────────

    def _draw_undergrowth(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["undergrowth_base"])

        # Scatter a few lighter leaf/twig marks
        for _ in range(rng.randint(1, 3)):
            px = x0 + rng.randint(2, t - 4)
            py = y0 + rng.randint(2, t - 4)
            pw = rng.randint(t // 6, t // 3)
            ph = rng.randint(1, max(2, t // 8))
            angle_flag = rng.random() < 0.5
            if angle_flag:
                pw, ph = ph, pw
            draw.rectangle([px, py, px + pw, py + ph], fill=p["undergrowth_hi"])

    def _draw_tent_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["tent_base"])

        # Woven grain — light horizontal lines
        n_lines = max(2, t // 12)
        for i in range(n_lines):
            ly = y0 + (i * t) // n_lines + rng.randint(0, t // n_lines)
            v = rng.randint(-8, 8)
            r0, g0, b0 = p["tent_shadow"]
            draw.line(
                [(x0 + 1, ly), (x0 + t - 2, ly)],
                fill=(
                    min(255, max(0, r0 + v)),
                    min(255, max(0, g0 + v)),
                    min(255, max(0, b0 + v)),
                ),
                width=1,
            )

        # Highlight patch in upper-left corner
        hs = max(2, t // 4)
        r0, g0, b0 = p["tent_hi"]
        v = rng.randint(-6, 6)
        draw.rectangle(
            [x0 + 2, y0 + 2, x0 + hs, y0 + hs],
            fill=(min(255, r0 + v), min(255, g0 + v), min(255, b0 + v)),
        )

    def _draw_pit_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        # Stone ring base
        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["pit_stone"])

        # Ash fill in inner circle
        inner = max(2, t // 3)
        cx, cy = x0 + t // 2, y0 + t // 2
        draw.ellipse(
            [cx - inner, cy - inner, cx + inner, cy + inner],
            fill=p["pit_ash"],
        )

        # Highlight on top-left stone face
        hs = max(2, t // 5)
        draw.rectangle(
            [x0 + 1, y0 + 1, x0 + hs, y0 + hs],
            fill=p["pit_stone_hi"],
        )

    def _draw_path_floor(
        self, img: Image.Image, x0: int, y0: int, seed: int
    ) -> None:
        p = _PALETTE
        rng = _random.Random(seed)
        t = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=p["path_base"])

        # Worn centre strip
        strip_w = max(2, t // 4)
        cx = x0 + t // 2
        draw.rectangle(
            [cx - strip_w // 2, y0, cx + strip_w // 2, y0 + t - 1],
            fill=p["path_hi"],
        )

    # ── Tent ridge ───────────────────────────────────────────────────────────────

    def _draw_tent_ridge(self, img: Image.Image, tent: Tent, t: int) -> None:
        """Draw a dark ridge line along the centre of a tent's bounding box."""
        if not tent.cells:
            return
        p = _PALETTE
        draw = ImageDraw.Draw(img)

        ys = [c.y for c in tent.cells]
        xs = [c.x for c in tent.cells]
        min_r, max_r = min(ys), max(ys)
        min_c, max_c = min(xs), max(xs)
        height = max_r - min_r + 1
        width = max_c - min_c + 1

        # Ridge runs along the longer axis through the centre
        if height >= width:
            # Vertical tent — ridge runs top to bottom at centre column
            cx = (min_c + max_c) // 2
            px = cx * t + t // 2
            draw.line(
                [(px, min_r * t + 1), (px, (max_r + 1) * t - 2)],
                fill=p["tent_ridge"],
                width=max(1, t // 16),
            )
        else:
            # Horizontal tent — ridge runs left to right at centre row
            cy = (min_r + max_r) // 2
            py = cy * t + t // 2
            draw.line(
                [(min_c * t + 1, py), ((max_c + 1) * t - 2, py)],
                fill=p["tent_ridge"],
                width=max(1, t // 16),
            )

    # ── Fire glow ────────────────────────────────────────────────────────────────

    def _apply_fire_glow(
        self,
        arr: np.ndarray,
        scene: CampScene,
        filled: np.ndarray,
    ) -> np.ndarray:
        t = self.tile_size
        H, W = arr.shape[:2]
        # Glow radius: generous — 3× tile across
        radius = t * 3.5

        floor_mask = np.kron(~filled, np.ones((t, t), dtype=bool))

        # Compute fire pit centre in pixel space
        pit_cells = list(scene.fire_pit.cells)
        ys = [c.y for c in pit_cells]
        xs = [c.x for c in pit_cells]
        pit_cy = (sum(ys) / len(ys) + 0.5) * t
        pit_cx = (sum(xs) / len(xs) + 0.5) * t

        py_g, px_g = np.mgrid[0:H, 0:W]
        dist = np.sqrt((px_g - pit_cx) ** 2 + (py_g - pit_cy) ** 2)
        glow = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 1.5
        glow[~floor_mask] = 0.0

        # Warm orange push: strong red, medium green, minimal blue
        arr[:, :, 0] = np.clip(arr[:, :, 0] + glow * 120, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] + glow * 55,  0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] - glow * 10,  0, 255)
        return arr

    # ── Embers ───────────────────────────────────────────────────────────────────

    def _draw_embers(
        self, img: Image.Image, fire_pit: FirePit, t: int
    ) -> None:
        p = _PALETTE
        draw = ImageDraw.Draw(img)
        pit_cells = list(fire_pit.cells)
        rng = _random.Random(12345)

        # 20 embers scattered across pit cells
        for _ in range(20):
            cell = rng.choice(pit_cells)
            x0, y0 = cell.x * t, cell.y * t
            ex = x0 + rng.randint(2, t - 2)
            ey = y0 + rng.randint(2, t - 2)
            es = max(1, t // 20)
            color = p["fire_hi"] if rng.random() < 0.5 else p["ember"]
            draw.ellipse([ex - es, ey - es, ex + es, ey + es], fill=color)

    # ── Wall shadows ─────────────────────────────────────────────────────────────

    def _apply_wall_shadows(
        self,
        arr: np.ndarray,
        scene: CampScene,
        filled: np.ndarray,
    ) -> np.ndarray:
        t = self.tile_size
        d = max(2, t // 3)
        H, W = arr.shape[:2]
        ramp = np.linspace(0.52, 1.0, d, dtype=np.float32)
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

    def _draw_wall_lines(self, img: Image.Image, scene: CampScene) -> None:
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
