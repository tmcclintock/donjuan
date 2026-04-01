"""
Camp scene type: open ground with clustered tents around campfires and
perimeter trees.

Design model
------------
* Almost all cells are **unfilled** (open, traversable ground).
* :class:`FirePit` — a single unfilled cell marking a campfire.  Multiple
  fires are supported; the default is one at the grid centre.
* :class:`Tent` — small rectangular space (1×2, 2×2, or 2×3 cells, chosen
  by weighted random).  Tents cluster radially around each campfire.
* :class:`CampPath` — unfilled cells forming a short dirt track from a tent
  to its nearest campfire.
* :class:`CampTree` — a single ``filled=True`` cell representing a tree at
  the camp perimeter.  These are solid, vision-blocking obstacles.  In a
  future FoundryVTT export each tree cell will be a circular wall polygon
  (~10 segments) rather than four rectangular edge segments.
"""
import math
import random
from typing import Dict, List, Optional, Set, Tuple

from donjuan.core.cell import SquareCell
from donjuan.core.randomizer import Randomizer
from donjuan.core.scene import Scene
from donjuan.core.space import Space


# ── Space subclasses ────────────────────────────────────────────────────────


class FirePit(Space):
    """Single-cell campfire marker.  Unfilled — traversable."""

    pass


class Tent(Space):
    """Small rectangular tent (1×2, 2×2, or 2×3 cells).  Unfilled."""

    pass


class CampPath(Space):
    """Short dirt track linking a tent to a campfire.  Unfilled."""

    pass


class CampTree(Space):
    """
    A tree at the camp perimeter (``filled=True`` — solid obstacle).

    Note: FoundryVTT export will represent each tree cell as a circular wall
    polygon rather than four rectangular edges.
    """

    pass


# ── Scene container ─────────────────────────────────────────────────────────


class CampScene(Scene):
    """
    A camp battle-map scene.  The grid is mostly open ground; trees ring the
    perimeter, campfires mark gathering spots, and tents cluster around each
    fire.

    Args:
        n_rows (int): grid rows (ignored if ``grid`` supplied)
        n_cols (int): grid columns (ignored if ``grid`` supplied)
        grid: pre-built :class:`~donjuan.grid.Grid` (overrides n_rows/n_cols)
    """

    def __init__(self, n_rows: int = 20, n_cols: int = 20, grid=None):
        from donjuan.core.grid import SquareGrid

        super().__init__(
            grid=grid or SquareGrid(n_rows, n_cols),
            scene_type="camp",
        )
        self.fires: List[FirePit] = []
        self.tents: Dict[str, Tent] = {}
        self.paths: Dict[str, CampPath] = {}
        self.trees: Dict[str, CampTree] = {}

        # Open ground: clear the grid-default filled=True on every cell.
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                self.grid.cells[r][c].filled = False

    # ── Backward-compatibility ────────────────────────────────────────────────

    @property
    def fire_pit(self) -> Optional[FirePit]:
        """Return the first fire (or None).  For backward compatibility."""
        return self.fires[0] if self.fires else None

    # ── Mutators ─────────────────────────────────────────────────────────────

    def add_fire(self, fire: FirePit) -> None:
        self.fires.append(fire)

    def add_tent(self, tent: Tent) -> None:
        self.tents[str(tent.name)] = tent

    def add_path(self, path: CampPath) -> None:
        self.paths[str(path.name)] = path

    def add_tree(self, tree: CampTree) -> None:
        self.trees[str(tree.name)] = tree


# ── Randomizer ──────────────────────────────────────────────────────────────


class CampRandomizer(Randomizer):
    """
    Generates a :class:`CampScene` by placing campfires, clustering tents
    around each fire, carving short dirt paths, and scattering trees around
    the outer perimeter.

    Args:
        n_fires (int): number of campfires to place (default 1)
        n_tents (int): total tents across all fires (default 6)
        camp_radius (float): tent ring distance from fire as a fraction of
            grid half-size (0–1, default 0.4)
        perimeter_tree_density (float): fraction of outer-band cells to fill
            with trees (0–1, default 0.05)
        perimeter_band (float): outer tree-band width as a fraction of grid
            half-size (default 0.25)
        min_fire_spacing (int): minimum Manhattan distance between fires
            when ``n_fires > 1`` (default 6)
    """

    # Weighted tent-size pool: (height, width).
    # 1×2 is most common (~60 %), 2×2 occasional (~20 %), 2×3 rarer (~20 %).
    _TENT_SIZES = [
        (1, 2), (2, 1),  # 1×2
        (1, 2), (2, 1),
        (1, 2), (2, 1),
        (2, 2),          # 2×2
        (2, 2),
        (2, 3), (3, 2),  # 2×3
    ]

    def __init__(
        self,
        n_fires: int = 1,
        n_tents: int = 6,
        camp_radius: float = 0.4,
        perimeter_tree_density: float = 0.05,
        perimeter_band: float = 0.25,
        min_fire_spacing: int = 6,
    ):
        super().__init__()
        self.n_fires = n_fires
        self.n_tents = n_tents
        self.camp_radius = camp_radius
        self.perimeter_tree_density = perimeter_tree_density
        self.perimeter_band = perimeter_band
        self.min_fire_spacing = min_fire_spacing

    def randomize(self, scene: CampScene) -> None:
        """
        Populate *scene* with campfires, tents, paths, and perimeter trees.

        Args:
            scene (CampScene): the scene to populate
        """
        fire_positions = self._place_fires(scene)
        self._place_tents_and_paths(scene, fire_positions)
        self._place_perimeter_trees(scene)

    # ── Fire placement ────────────────────────────────────────────────────────

    def _place_fires(self, scene: CampScene) -> List[Tuple[int, int]]:
        """
        Place campfire cells and return their (row, col) positions.

        One fire goes to the grid centre.  Additional fires are spaced at
        equal angular intervals on a ring at 30 % of the grid half-size.
        """
        cy, cx = scene.n_rows // 2, scene.n_cols // 2
        positions: List[Tuple[int, int]] = []

        if self.n_fires == 1:
            positions = [(cy, cx)]
        else:
            half = min(scene.n_rows, scene.n_cols) / 2.0
            ring_r = half * 0.30
            for i in range(self.n_fires):
                angle = (2 * math.pi / self.n_fires) * i
                fr = int(round(cy + ring_r * math.sin(angle)))
                fc = int(round(cx + ring_r * math.cos(angle)))
                fr = max(1, min(scene.n_rows - 2, fr))
                fc = max(1, min(scene.n_cols - 2, fc))
                positions.append((fr, fc))

        placed: List[Tuple[int, int]] = []
        for idx, (fr, fc) in enumerate(positions):
            cell = scene.grid.cells[fr][fc]
            fire = FirePit(cells={cell}, name=f"F{idx}")
            scene.emplace_space(fire)
            scene.add_fire(fire)
            placed.append((fr, fc))
        return placed

    # ── Tent + path placement ─────────────────────────────────────────────────

    def _place_tents_and_paths(
        self,
        scene: CampScene,
        fire_positions: List[Tuple[int, int]],
    ) -> None:
        """Place tent clusters around each fire and carve connecting paths."""
        if not fire_positions:
            return

        tents_per_fire = max(1, self.n_tents // len(fire_positions))
        half = min(scene.n_rows, scene.n_cols) / 2.0
        radius_cells = half * self.camp_radius
        tent_idx = path_idx = 0

        for fire_r, fire_c in fire_positions:
            fire_coords: Set[Tuple[int, int]] = {(fire_r, fire_c)}
            for i in range(tents_per_fire):
                base_angle = (2 * math.pi / tents_per_fire) * i
                angle = base_angle + random.uniform(-0.3, 0.3)
                ty = int(round(fire_r + radius_cells * math.sin(angle)))
                tx = int(round(fire_c + radius_cells * math.cos(angle)))

                th, tw = self._pick_tent_size(angle)
                cells = self._rect_cells(ty, tx, th, tw, scene)
                if not cells:
                    tent_idx += 1
                    continue

                tent = Tent(cells=set(cells), name=f"T{tent_idx}")
                scene.emplace_space(tent)
                scene.add_tent(tent)

                # Carve a dirt path from tent centre toward the fire
                tc = self._center(tent)
                carved = self._straight_path(scene, tc, fire_coords)
                if carved:
                    path = CampPath(cells=set(carved), name=f"P{path_idx}")
                    scene.emplace_space(path)
                    scene.add_path(path)
                    path_idx += 1

                tent_idx += 1

    def _pick_tent_size(self, angle: float) -> Tuple[int, int]:
        """
        Return (height, width) from the weighted pool, oriented so the longer
        axis points radially away from the fire.
        """
        base_h, base_w = random.choice(self._TENT_SIZES)
        # sin dominates vertical (rows), cos dominates horizontal (cols)
        if abs(math.sin(angle)) >= abs(math.cos(angle)):
            return (max(base_h, base_w), min(base_h, base_w))
        else:
            return (min(base_h, base_w), max(base_h, base_w))

    # ── Perimeter tree placement ──────────────────────────────────────────────

    def _place_perimeter_trees(self, scene: CampScene) -> None:
        """Scatter CampTree cells in the outer perimeter band."""
        if self.perimeter_tree_density <= 0:
            return

        rows, cols = scene.n_rows, scene.n_cols
        half = min(rows, cols) / 2.0
        band_px = half * self.perimeter_band
        cy, cx = rows / 2.0, cols / 2.0

        candidates = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if math.sqrt((r - cy) ** 2 + (c - cx) ** 2) >= half - band_px
        ]

        n_trees = int(self.perimeter_tree_density * len(candidates))
        random.shuffle(candidates)
        tree_idx = 0

        for r, c in candidates:
            if tree_idx >= n_trees:
                break
            cell = scene.grid.cells[r][c]
            if cell.space is not None:
                continue  # don't overwrite tents / paths
            cell.filled = True
            tree = CampTree(cells={cell}, name=f"CT{tree_idx}")
            scene.emplace_space(tree)
            scene.add_tree(tree)
            tree_idx += 1

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _rect_cells(
        cy: int, cx: int, height: int, width: int, scene: CampScene
    ) -> List[SquareCell]:
        """Return unfilled cells for a rectangle centred on (cy, cx)."""
        cells = []
        r0 = cy - height // 2
        c0 = cx - width // 2
        for dr in range(height):
            for dc in range(width):
                r, c = r0 + dr, c0 + dc
                if 0 <= r < scene.n_rows and 0 <= c < scene.n_cols:
                    cells.append(SquareCell(filled=False, coordinates=(r, c)))
        return cells

    @staticmethod
    def _center(space: Space) -> Tuple[int, int]:
        ys = [c.y for c in space.cells]
        xs = [c.x for c in space.cells]
        return (sum(ys) // len(ys), sum(xs) // len(xs))

    @staticmethod
    def _straight_path(
        scene: CampScene,
        start: Tuple[int, int],
        target_coords: Set[Tuple[int, int]],
    ) -> List[SquareCell]:
        """
        Walk from *start* toward the nearest target coordinate,
        collecting open cells with no existing space assignment.
        """
        if not target_coords:
            return []

        sy, sx = start
        ey, ex = min(
            target_coords,
            key=lambda p: abs(p[0] - sy) + abs(p[1] - sx),
        )

        carved: List[SquareCell] = []
        cy, cx = sy, sx
        while (cy, cx) not in target_coords:
            cell = scene.grid.cells[cy][cx]
            if cell.space is None:
                carved.append(cell)

            dy, dx = ey - cy, ex - cx
            if dy == 0 and dx == 0:
                break

            if abs(dy) > abs(dx) or (abs(dy) == abs(dx) and random.random() < 0.5):
                cy += 1 if dy > 0 else -1
            else:
                cx += 1 if dx > 0 else -1

            cy = max(0, min(scene.n_rows - 1, cy))
            cx = max(0, min(scene.n_cols - 1, cx))

        return carved
