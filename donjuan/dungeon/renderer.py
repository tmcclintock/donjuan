"""
Procedural tile-based renderer for donjuan dungeons.

Supports multiple named texture packs:
  ``stone``     — classic dark dungeon (default)
  ``cave``      — organic cave rock with algae
  ``wood``      — warm wooden inn / cabin
  ``sandstone`` — sun-bleached desert ruins
"""
import random as _random
from math import sqrt
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from donjuan.dungeon.dungeon import Dungeon
from donjuan.core.hallway import Hallway
from donjuan.core.renderer import BaseRenderer
from donjuan.core.room import Room


# ── Texture packs ──────────────────────────────────────────────────────────────
# Each pack is a dict with colour keys plus optional tweaks.
# brick_h_div / brick_w_div: tile_size is divided by these to get brick dims.
# plank_mode: if True the wall is drawn as vertical planks instead of bricks.

_PACKS: Dict[str, dict] = {
    "stone": {
        "outside":          (8,   8,  10),
        "wall_base":        (20,  18,  18),
        "wall_brick":       (44,  40,  37),
        "wall_var":         22,
        "brick_h_div":      4,    # brick_h = tile_size // 4
        "brick_w_div":      2,    # brick_w = tile_size // 2
        "plank_mode":       False,
        "floor_grout":      (38,  32,  26),
        "floor_room":       (110, 93,  72),
        "floor_hall":       (74,  64,  50),
        "door_wood":        (132, 82,  28),
        "door_iron":        (148, 140, 130),
        "pillar_face":      (105, 92,  75),
        "pillar_hi":        (155, 138, 115),
        "pillar_sh":        (58,  50,  40),
        "pillar_dark":      (28,  24,  18),
        "moss_lo":          (18,  60,  20),
        "moss_hi":          (35,  95,  35),
        "wall_line":        (14,  11,   8),
    },
    "cave": {
        "outside":          (5,   4,   8),
        "wall_base":        (14,  13,  18),
        "wall_brick":       (40,  38,  48),
        "wall_var":         16,
        "brick_h_div":      3,
        "brick_w_div":      2,
        "plank_mode":       False,
        "floor_grout":      (25,  23,  32),
        "floor_room":       (68,  65,  80),
        "floor_hall":       (50,  48,  60),
        "door_wood":        (78,  60,  40),
        "door_iron":        (72,  78,  72),
        "pillar_face":      (75,  72,  88),
        "pillar_hi":        (108, 104, 122),
        "pillar_sh":        (42,  40,  52),
        "pillar_dark":      (20,  18,  26),
        "moss_lo":          (20,  68,  68),   # teal algae
        "moss_hi":          (28,  105, 105),
        "wall_line":        (8,   7,  12),
    },
    "wood": {
        "outside":          (10,  6,   3),
        "wall_base":        (28,  17,  9),
        "wall_brick":       (92,  56,  26),
        "wall_var":         18,
        "brick_h_div":      1,    # full-height planks
        "brick_w_div":      3,    # three planks across tile
        "plank_mode":       True,
        "floor_grout":      (72,  46,  20),
        "floor_room":       (162, 112, 62),
        "floor_hall":       (125, 82,  44),
        "door_wood":        (188, 132, 55),
        "door_iron":        (108, 82,  45),   # bronze nails
        "pillar_face":      (112, 74,  36),
        "pillar_hi":        (158, 112, 65),
        "pillar_sh":        (62,  40,  18),
        "pillar_dark":      (28,  16,  6),
        "moss_lo":          (125, 60,  12),   # orange fungi / lichen
        "moss_hi":          (158, 88,  26),
        "wall_line":        (12,   7,   3),
    },
    "sandstone": {
        "outside":          (14,  10,  5),
        "wall_base":        (62,  46,  28),
        "wall_brick":       (168, 136, 90),
        "wall_var":         28,
        "brick_h_div":      5,    # thin sandstone courses
        "brick_w_div":      2,
        "plank_mode":       False,
        "floor_grout":      (118, 94,  62),
        "floor_room":       (208, 180, 138),
        "floor_hall":       (170, 144, 108),
        "door_wood":        (148, 96,  42),
        "door_iron":        (158, 138, 98),
        "pillar_face":      (188, 158, 115),
        "pillar_hi":        (225, 198, 158),
        "pillar_sh":        (108, 88,  58),
        "pillar_dark":      (65,  50,  30),
        "moss_lo":          (80,  92,  35),   # dry desert lichen
        "moss_hi":          (112, 118, 55),
        "wall_line":        (28,  20,  10),
    },
}

#: Ordered list of available pack names for UI combo boxes.
PACK_NAMES = list(_PACKS.keys())

# ── Room themes ────────────────────────────────────────────────────────────────
# Each entry overrides the room floor colour regardless of the active pack.
# ``None`` means "use the pack's own floor_room colour".
SPACE_THEMES: Dict[str, Optional[Tuple[int, int, int]]] = {
    "default":  None,
    "treasury": (175, 145,  55),   # warm gold
    "throne":   ( 88,  45,  65),   # deep red-purple
    "prison":   ( 48,  58,  48),   # dark green-grey
    "barracks": (112,  82,  52),   # earthy brown
    "crypt":    ( 65,  68,  90),   # cold blue-grey
}

# Backwards-compat alias
ROOM_THEMES = SPACE_THEMES


class TexturedRenderer(BaseRenderer):
    """
    Renders a square-grid dungeon as a textured tile image using Pillow.

    Base layers (always drawn):

    - **Walls** – brick or plank pattern drawn per texture pack.
    - **Room floors** – warm cobblestone with individual stone outlines.
    - **Hallway floors** – the same pattern in a darker tone.
    - **Doors** – a short wooden bar with an iron pin at room↔hallway edges.

    Optional texture layers (each toggled by a constructor flag):

    - **wall_shadows** – floor cells adjacent to walls are darkened.
    - **torchlight** – warm orange radial glow at door midpoints.
    - **moss_and_cracks** – moss patches on wall faces; cracks on floors.
    - **pillars** – 3-D stone columns at inner room corners.

    Args:
        tile_size (int): pixel width/height of each cell tile (default 48).
        wall_shadows (bool): enable wall drop-shadow (default True).
        torchlight (bool): enable torchlight glow (default True).
        moss_and_cracks (bool): enable moss and crack overlays (default True).
        pillars (bool): enable stone pillar rendering (default True).
        pack (str): texture pack name — one of ``PACK_NAMES`` (default
            ``"stone"``).
    """

    def __init__(
        self,
        tile_size: int = 48,
        wall_shadows: bool = True,
        torchlight: bool = True,
        moss_and_cracks: bool = True,
        pillars: bool = True,
        wall_lines: bool = True,
        pack: str = "stone",
    ):
        super().__init__(scale=float(tile_size))
        if pack not in _PACKS:
            raise ValueError(
                f"Unknown texture pack {pack!r}. "
                f"Choose from: {', '.join(PACK_NAMES)}"
            )
        self.tile_size       = tile_size
        self.wall_shadows    = wall_shadows
        self.torchlight      = torchlight
        self.moss_and_cracks = moss_and_cracks
        self.pillars         = pillars
        self.wall_lines      = wall_lines
        self._c              = dict(_PACKS[pack])   # local copy
        self._last_image: Optional[Image.Image] = None

    def render(
        self,
        dungeon: Dungeon,
        file_path: str = "rendered_dungeon.png",
        dpi: int = 96,
        save: bool = True,
    ) -> Tuple:
        """Render *dungeon* to a Pillow image embedded in a matplotlib Figure."""
        from donjuan.core.grid import SquareGrid
        assert isinstance(dungeon.grid, SquareGrid), (
            "TexturedRenderer only supports SquareGrid dungeons; "
            f"got {type(dungeon.grid).__name__}."
        )

        img = self._build_image(dungeon)
        self._last_image = img

        if save:
            img.save(file_path)

        w_in = img.width  / dpi
        h_in = img.height / dpi
        fig, ax = plt.subplots(1, figsize=(w_in, h_in), dpi=dpi)
        ax.imshow(np.array(img), interpolation="nearest")
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        return fig, ax

    # ── Image construction ──────────────────────────────────────────────────────

    def _build_image(self, dungeon: Dungeon) -> Image.Image:
        t    = self.tile_size
        rows = dungeon.n_rows
        cols = dungeon.n_cols
        H, W = rows * t, cols * t

        img = Image.new("RGB", (W, H), self._c["outside"])

        # Pre-compute filled mask (used by several stages)
        filled = np.array(
            [[dungeon.grid.cells[r][c].filled for c in range(cols)]
             for r in range(rows)],
            dtype=bool,
        )

        # ── Stage 1: base cell textures ────────────────────────────────
        for r in range(rows):
            for c in range(cols):
                cell = dungeon.grid.cells[r][c]
                x0, y0 = c * t, r * t
                seed   = r * 10_007 + c
                if cell.filled:
                    self._draw_wall(img, x0, y0, seed)
                elif isinstance(cell.space, Hallway):
                    theme = getattr(cell.space, "theme", "default")
                    floor_override = SPACE_THEMES.get(theme)
                    self._draw_floor(img, x0, y0, seed, room=False, floor_override=floor_override)
                else:
                    theme = getattr(cell.space, "theme", "default") if cell.space is not None else "default"
                    floor_override = SPACE_THEMES.get(theme)
                    self._draw_floor(img, x0, y0, seed, room=True, floor_override=floor_override)

        # ── Stage 2: pillars ───────────────────────────────────────────
        if self.pillars:
            self._draw_pillars(img, dungeon)

        # ── Stage 3: moss & cracks ─────────────────────────────────────
        if self.moss_and_cracks:
            self._apply_moss_and_cracks(img, dungeon, filled)

        # ── Stages 4 + 5: wall shadows then torchlight (numpy) ─────────
        if self.wall_shadows or self.torchlight:
            arr = np.array(img, dtype=np.float32)
            if self.wall_shadows:
                arr = self._apply_wall_shadows(arr, dungeon, filled)
            if self.torchlight:
                arr = self._apply_torchlight(arr, dungeon, filled)
            img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

        # ── Stage 6: doors (PIL, on top of lighting) ───────────────────
        self._draw_doors(img, dungeon)

        # ── Stage 7: wall outlines ─────────────────────────────────────
        if self.wall_lines:
            self._draw_wall_lines(img, dungeon)

        # ── Stage 8: vignette ──────────────────────────────────────────
        return self._vignette(img)

    # ── Base tile drawers ───────────────────────────────────────────────────────

    def _draw_wall(self, img: Image.Image, x0: int, y0: int, seed: int) -> None:
        c    = self._c
        rng  = _random.Random(seed)
        t    = self.tile_size
        draw = ImageDraw.Draw(img)

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=c["wall_base"])

        brick_h = max(6, t // c["brick_h_div"])
        brick_w = max(6, t // c["brick_w_div"])
        var     = c["wall_var"]
        br, bg, bb = c["wall_brick"]

        if c.get("plank_mode"):
            # Vertical planks — no row offset, full-height boards
            for col_i in range(t // brick_w + 2):
                bx    = x0 + col_i * brick_w
                left  = max(bx + 1, x0 + 1)
                right = min(bx + brick_w - 2, x0 + t - 2)
                if right <= left:
                    continue
                v = rng.randint(0, var)
                draw.rectangle(
                    [left, y0 + 1, right, y0 + t - 2],
                    fill=(
                        min(255, br + v),
                        min(255, bg + v - 2),
                        min(255, bb + v - 4),
                    ),
                )
                # Horizontal wood grain line
                grain_y = y0 + rng.randint(t // 4, 3 * t // 4)
                draw.line(
                    [(left, grain_y), (right, grain_y)],
                    fill=(max(0, br - 12), max(0, bg - 10), max(0, bb - 8)),
                    width=1,
                )
        else:
            for row_i in range(t // brick_h + 2):
                ry     = y0 + row_i * brick_h
                if ry >= y0 + t:
                    break
                offset = (brick_w // 2) if (row_i % 2 == 1) else 0
                for col_i in range(-1, t // brick_w + 2):
                    bx     = x0 + col_i * brick_w + offset
                    left   = max(bx + 1,           x0 + 1)
                    top    = max(ry + 1,            y0 + 1)
                    right  = min(bx + brick_w - 2, x0 + t - 2)
                    bottom = min(ry + brick_h - 2, y0 + t - 2)
                    if right <= left or bottom <= top:
                        continue
                    v = rng.randint(0, var)
                    draw.rectangle(
                        [left, top, right, bottom],
                        fill=(
                            min(255, br + v),
                            min(255, max(0, bg + v - 2)),
                            min(255, max(0, bb + v - 4)),
                        ),
                    )

    def _draw_floor(
        self,
        img: Image.Image,
        x0: int,
        y0: int,
        seed: int,
        room: bool,
        floor_override: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        c    = self._c
        rng  = _random.Random(seed)
        t    = self.tile_size
        draw = ImageDraw.Draw(img)
        base = floor_override if floor_override is not None else (
            c["floor_room"] if room else c["floor_hall"]
        )

        draw.rectangle([x0, y0, x0 + t - 1, y0 + t - 1], fill=c["floor_grout"])

        n_cols = 3 if t >= 32 else 2
        n_rows = 2 if t >= 32 else 1
        sw, sh = t // n_cols, t // n_rows

        for ri in range(n_rows):
            for ci in range(n_cols):
                ml, mt = rng.randint(1, 3), rng.randint(1, 3)
                mr, mb = rng.randint(1, 3), rng.randint(1, 3)
                sx = x0 + ci * sw + ml
                sy = y0 + ri * sh + mt
                ex = x0 + (ci + 1) * sw - mr
                ey = y0 + (ri + 1) * sh - mb
                if ex <= sx or ey <= sy:
                    continue
                v = rng.randint(-16, 16)
                r, g, b = base
                draw.rectangle(
                    [sx, sy, ex, ey],
                    fill=(
                        min(255, max(0, r + v)),
                        min(255, max(0, g + v // 2)),
                        min(255, max(0, b + v // 3)),
                    ),
                )

    # ── Stage 2: pillars ────────────────────────────────────────────────────────

    def _draw_pillars(self, img: Image.Image, dungeon: Dungeon) -> None:
        c    = self._c
        draw = ImageDraw.Draw(img)
        t    = self.tile_size
        # Larger pillar: t//4 gives a 24px-wide pillar on a 48px tile
        ps   = max(5, t // 4)
        hs   = max(2, ps // 3)   # highlight / shadow strip width

        for r in range(dungeon.n_rows - 1):
            for col in range(dungeon.n_cols - 1):
                cells = [
                    dungeon.grid.cells[r    ][col    ],
                    dungeon.grid.cells[r    ][col + 1],
                    dungeon.grid.cells[r + 1][col    ],
                    dungeon.grid.cells[r + 1][col + 1],
                ]
                if not all(
                    not cell.filled and isinstance(cell.space, Room)
                    for cell in cells
                ):
                    continue

                rng = _random.Random(r * 10_007 + col + 55_555)
                if rng.random() > 0.35:
                    continue

                cx = (col + 1) * t
                cy = (r   + 1) * t

                # Main face
                draw.rectangle(
                    [cx - ps, cy - ps, cx + ps, cy + ps],
                    fill=c["pillar_face"],
                )
                # Top highlight strip
                draw.rectangle(
                    [cx - ps, cy - ps, cx + ps, cy - ps + hs],
                    fill=c["pillar_hi"],
                )
                # Left highlight strip
                draw.rectangle(
                    [cx - ps, cy - ps, cx - ps + hs, cy + ps],
                    fill=c["pillar_hi"],
                )
                # Bottom shadow strip
                draw.rectangle(
                    [cx - ps, cy + ps - hs, cx + ps, cy + ps],
                    fill=c["pillar_sh"],
                )
                # Right shadow strip
                draw.rectangle(
                    [cx + ps - hs, cy - ps, cx + ps, cy + ps],
                    fill=c["pillar_sh"],
                )
                # 1-px dark outline
                draw.rectangle(
                    [cx - ps, cy - ps, cx + ps, cy + ps],
                    outline=c["pillar_dark"],
                )
                # Small central cap for depth
                cap = max(2, ps // 3)
                draw.rectangle(
                    [cx - cap, cy - cap, cx + cap, cy + cap],
                    fill=c["pillar_hi"],
                    outline=c["pillar_sh"],
                )

    # ── Stage 3: moss & cracks ──────────────────────────────────────────────────

    def _apply_moss_and_cracks(
        self, img: Image.Image, dungeon: Dungeon, filled: np.ndarray
    ) -> None:
        c         = self._c
        draw      = ImageDraw.Draw(img)
        t         = self.tile_size
        rows, cols = dungeon.n_rows, dungeon.n_cols
        moss_d    = max(3, t // 5)

        wall_s = filled[:-1, :] & ~filled[1:,  :]
        wall_n = filled[1:,  :] & ~filled[:-1, :]
        wall_e = filled[:,  :-1] & ~filled[:, 1:]
        wall_w = filled[:, 1:]   & ~filled[:, :-1]

        moss_lo = c["moss_lo"]
        moss_hi = c["moss_hi"]

        def _moss(x0, y0, bw, bh, seed):
            rng = _random.Random(seed ^ 0xCA11)
            if rng.random() > 0.45:
                return
            n = rng.randint(1, 3)
            for _ in range(n):
                px = x0 + rng.randint(0, max(1, bw - 4))
                py = y0 + rng.randint(0, max(1, bh - 4))
                pw = rng.randint(2, max(3, bw // 3))
                ph = rng.randint(2, max(3, bh // 3))
                r0 = rng.randint(moss_lo[0], moss_hi[0])
                g0 = rng.randint(moss_lo[1], moss_hi[1])
                b0 = rng.randint(moss_lo[2], moss_hi[2])
                draw.rectangle(
                    [px, py, px + pw, py + ph],
                    fill=(r0, g0, b0),
                )

        for r, col in zip(*np.where(wall_s)):
            x0, y0 = int(col) * t, int(r) * t
            _moss(x0, y0 + t - moss_d, t, moss_d, int(r) * 10_007 + int(col))

        for r, col in zip(*np.where(wall_n)):
            x0, y0 = int(col) * t, int(r) * t
            _moss(x0, y0, t, moss_d, int(r) * 10_007 + int(col) + 1)

        for r, col in zip(*np.where(wall_e)):
            x0, y0 = int(col) * t, int(r) * t
            _moss(x0 + t - moss_d, y0, moss_d, t, int(r) * 10_007 + int(col) + 2)

        for r, col in zip(*np.where(wall_w)):
            x0, y0 = int(col) * t, int(r) * t
            _moss(x0, y0, moss_d, t, int(r) * 10_007 + int(col) + 3)

        # Cracks on floor cells
        for r in range(rows):
            for col in range(cols):
                if filled[r, col]:
                    continue
                x0, y0 = col * t, r * t
                rng = _random.Random(r * 10_007 + col ^ 0xDEAD)
                n = rng.randint(0, 2)
                for _ in range(n):
                    sx = x0 + rng.randint(4, t - 4)
                    sy = y0 + rng.randint(4, t - 4)
                    ex = sx + rng.randint(-(t // 4), t // 4)
                    ey = sy + rng.randint(-(t // 4), t // 4)
                    draw.line(
                        [(sx, sy), (max(x0, min(x0 + t - 1, ex)),
                                    max(y0, min(y0 + t - 1, ey)))],
                        fill=(28, 24, 18),
                        width=1,
                    )

    # ── Stage 4: wall shadows ───────────────────────────────────────────────────

    def _apply_wall_shadows(
        self,
        arr: np.ndarray,
        dungeon: Dungeon,
        filled: np.ndarray,
    ) -> np.ndarray:
        t    = self.tile_size
        d    = max(2, t // 3)
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

        rows, cols = dungeon.n_rows, dungeon.n_cols

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

    # ── Stage 5: torchlight ─────────────────────────────────────────────────────

    def _apply_torchlight(
        self,
        arr: np.ndarray,
        dungeon: Dungeon,
        filled: np.ndarray,
    ) -> np.ndarray:
        t      = self.tile_size
        H, W   = arr.shape[:2]
        radius = t * 2.2

        floor_mask = np.kron(~filled, np.ones((t, t), dtype=bool))

        torch_px = []
        seen: set = set()
        for r in range(dungeon.n_rows):
            for col in range(dungeon.n_cols):
                for edge in dungeon.grid.cells[r][col].edges:
                    if edge is None or not edge.has_door:
                        continue
                    eid = id(edge)
                    if eid in seen:
                        continue
                    seen.add(eid)
                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None:
                        continue
                    if c1.filled or c2.filled:
                        continue
                    mx = ((c1.x + c2.x) / 2.0 + 0.5) * t
                    my = ((c1.y + c2.y) / 2.0 + 0.5) * t
                    torch_px.append((mx, my))

        if not torch_px:
            return arr

        ys, xs = np.mgrid[0:H, 0:W]
        total_glow = np.zeros((H, W), dtype=np.float32)

        for cx, cy in torch_px:
            dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
            glow = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 2
            total_glow = np.maximum(total_glow, glow)

        total_glow[~floor_mask] = 0.0

        arr[:, :, 0] = np.clip(arr[:, :, 0] + total_glow * 85, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] + total_glow * 38, 0, 255)
        return arr

    # ── Stage 6: doors ──────────────────────────────────────────────────────────

    def _draw_doors(self, img: Image.Image, dungeon: Dungeon) -> None:
        c    = self._c
        t    = self.tile_size
        draw = ImageDraw.Draw(img)
        seen: set = set()

        for r in range(dungeon.n_rows):
            for col in range(dungeon.n_cols):
                for edge in dungeon.grid.cells[r][col].edges:
                    if edge is None or not edge.has_door:
                        continue
                    eid = id(edge)
                    if eid in seen:
                        continue
                    seen.add(eid)
                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None:
                        continue
                    if c1.filled or c2.filled:
                        continue

                    thick    = max(2, t // 10)
                    door_len = (t * 2) // 3
                    pin      = max(1, t // 16)

                    if c1.y == c2.y:
                        lc    = c1 if c1.x < c2.x else c2
                        ex    = (lc.x + 1) * t
                        mid_y = lc.y * t + t // 2
                        draw.rectangle(
                            [ex - thick, mid_y - door_len // 2,
                             ex + thick, mid_y + door_len // 2],
                            fill=c["door_wood"],
                        )
                        draw.rectangle(
                            [ex - pin, mid_y - pin, ex + pin, mid_y + pin],
                            fill=c["door_iron"],
                        )
                    else:
                        tc    = c1 if c1.y < c2.y else c2
                        ey    = (tc.y + 1) * t
                        mid_x = tc.x * t + t // 2
                        draw.rectangle(
                            [mid_x - door_len // 2, ey - thick,
                             mid_x + door_len // 2, ey + thick],
                            fill=c["door_wood"],
                        )
                        draw.rectangle(
                            [mid_x - pin, ey - pin, mid_x + pin, ey + pin],
                            fill=c["door_iron"],
                        )

    # ── Stage 7: wall outlines ──────────────────────────────────────────────────

    def _draw_wall_lines(self, img: Image.Image, dungeon: Dungeon) -> None:
        """
        Draw a thin dark line along every floor edge that faces a wall cell
        (or the map boundary).  The line is drawn on the *floor* side so the
        brick texture of the wall is never obscured.

        Line width scales with tile_size: 1 px for tiny tiles, 2 px for the
        default 48-px tile, 3+ px for export-sized tiles.
        """
        t     = self.tile_size
        lw    = max(1, t // 24)          # e.g. 2 px at t=48, 4 px at t=100
        color = self._c["wall_line"]
        draw  = ImageDraw.Draw(img)
        rows  = dungeon.n_rows
        cols  = dungeon.n_cols
        cells = dungeon.grid.cells

        for r in range(rows):
            for c in range(cols):
                if cells[r][c].filled:
                    continue
                x0, y0 = c * t, r * t

                # Top edge — wall or map boundary above?
                if r == 0 or cells[r - 1][c].filled:
                    draw.rectangle(
                        [x0, y0, x0 + t - 1, y0 + lw - 1],
                        fill=color,
                    )
                # Bottom edge — wall or map boundary below?
                if r == rows - 1 or cells[r + 1][c].filled:
                    draw.rectangle(
                        [x0, y0 + t - lw, x0 + t - 1, y0 + t - 1],
                        fill=color,
                    )
                # Left edge — wall or map boundary to the left?
                if c == 0 or cells[r][c - 1].filled:
                    draw.rectangle(
                        [x0, y0, x0 + lw - 1, y0 + t - 1],
                        fill=color,
                    )
                # Right edge — wall or map boundary to the right?
                if c == cols - 1 or cells[r][c + 1].filled:
                    draw.rectangle(
                        [x0 + t - lw, y0, x0 + t - 1, y0 + t - 1],
                        fill=color,
                    )

    # ── Stage 8: vignette ───────────────────────────────────────────────────────

    @staticmethod
    def _vignette(img: Image.Image) -> Image.Image:
        arr      = np.array(img, dtype=np.float32)
        h, w     = arr.shape[:2]
        cx, cy   = w / 2.0, h / 2.0
        max_dist = sqrt(cx ** 2 + cy ** 2)
        ys, xs   = np.mgrid[0:h, 0:w]
        dist     = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        factor   = 1.0 - 0.30 * (dist / max_dist) ** 2
        arr     *= factor[:, :, np.newaxis]
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8))
