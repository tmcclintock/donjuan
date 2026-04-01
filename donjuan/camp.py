"""
Camp scene type: tents arranged radially around a central fire pit.
"""
import math
import random
from typing import Dict, List, Optional

from donjuan.cell import SquareCell
from donjuan.randomizer import Randomizer
from donjuan.scene import Scene
from donjuan.space import Space


# ── Space subclasses ────────────────────────────────────────────────────────


class FirePit(Space):
    """Central fire pit clearing."""

    pass


class Tent(Space):
    """A small rectangular tent structure."""

    pass


class CampPath(Space):
    """A short dirt track from a tent to the fire pit."""

    pass


# ── Scene container ─────────────────────────────────────────────────────────


class CampScene(Scene):
    """
    A camp scene: a central fire pit surrounded by tents connected by
    short radial paths.

    Args:
        n_rows (int): grid rows (ignored if ``grid`` supplied)
        n_cols (int): grid columns (ignored if ``grid`` supplied)
        grid: pre-built :class:`~donjuan.grid.Grid` (overrides n_rows/n_cols)
    """

    def __init__(self, n_rows: int = 20, n_cols: int = 20, grid=None):
        from donjuan.grid import SquareGrid

        super().__init__(
            grid=grid or SquareGrid(n_rows, n_cols),
            scene_type="camp",
        )
        self.fire_pit: Optional[FirePit] = None
        self.tents: Dict[str, Tent] = {}
        self.paths: Dict[str, CampPath] = {}

    def add_tent(self, tent: Tent) -> None:
        self.tents[str(tent.name)] = tent

    def add_path(self, path: CampPath) -> None:
        self.paths[str(path.name)] = path


# ── Randomizer ──────────────────────────────────────────────────────────────


class CampRandomizer(Randomizer):
    """
    Generates a :class:`CampScene` by placing a central fire pit, then
    radiating tents at equal angular intervals and carving straight paths
    from each tent back to the fire pit.

    Args:
        n_tents (int): number of tents to place (default 6)
        tent_width (int): tent width in cells (default 2)
        tent_height (int): tent height in cells (default 3)
        fire_radius (int): radius of the fire pit clearing (default 2)
        camp_radius (float): tent centre distance from grid centre, as a
            fraction of grid half-size (0–1, default 0.55)
        perimeter (bool): carve a ring path around the outermost tent ring
            (default False)
    """

    def __init__(
        self,
        n_tents: int = 6,
        tent_width: int = 2,
        tent_height: int = 3,
        fire_radius: int = 2,
        camp_radius: float = 0.55,
        perimeter: bool = False,
    ):
        super().__init__()
        self.n_tents = n_tents
        self.tent_width = tent_width
        self.tent_height = tent_height
        self.fire_radius = fire_radius
        self.camp_radius = camp_radius
        self.perimeter = perimeter

    def randomize(self, scene: CampScene) -> None:
        """
        Generate the fire pit, tents, and connecting paths in *scene*.

        Args:
            scene (CampScene): the scene to populate
        """
        cy = scene.n_rows // 2
        cx = scene.n_cols // 2

        # ── Fire pit ──────────────────────────────────────────────────
        pit_cells = self._circle_cells(cy, cx, self.fire_radius, scene)
        fire_pit = FirePit(cells=set(pit_cells), name="fire")
        scene.emplace_space(fire_pit)
        scene.fire_pit = fire_pit

        # ── Tents ─────────────────────────────────────────────────────
        half_r = min(scene.n_rows, scene.n_cols) / 2.0
        radius_cells = half_r * self.camp_radius

        placed_tents: List[Tent] = []
        for i in range(self.n_tents):
            angle = (2 * math.pi / self.n_tents) * i + math.pi / self.n_tents
            # Tent centre: rotate around grid centre
            ty = int(round(cy + radius_cells * math.sin(angle)))
            tx = int(round(cx + radius_cells * math.cos(angle)))

            # Orient tent so its long axis points toward the fire pit
            if abs(math.sin(angle)) >= abs(math.cos(angle)):
                th, tw = self.tent_height, self.tent_width
            else:
                th, tw = self.tent_width, self.tent_height

            cells = self._rect_cells(ty, tx, th, tw, scene)
            if not cells:
                continue
            tent = Tent(cells=set(cells), name=f"T{i}")
            scene.emplace_space(tent)
            scene.add_tent(tent)
            placed_tents.append(tent)

        # ── Paths from each tent to fire pit ──────────────────────────
        fire_coords = {(c.y, c.x) for c in fire_pit.cells}
        for i, tent in enumerate(placed_tents):
            tc = self._center(tent)
            carved = self._straight_path(scene, tc, fire_coords)
            if carved:
                path = CampPath(cells=set(carved), name=f"P{i}")
                scene.emplace_space(path)
                scene.add_path(path)

        # ── Optional perimeter ring ────────────────────────────────────
        if self.perimeter and placed_tents:
            self._carve_perimeter(scene, placed_tents, radius_cells + self.tent_height)

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _circle_cells(cy: int, cx: int, radius: int, scene: CampScene) -> List[SquareCell]:
        cells = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dy * dy + dx * dx <= radius * radius:
                    r, c = cy + dy, cx + dx
                    if 0 <= r < scene.n_rows and 0 <= c < scene.n_cols:
                        cells.append(SquareCell(filled=False, coordinates=(r, c)))
        return cells

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
    def _center(space: Space):
        ys = [c.y for c in space.cells]
        xs = [c.x for c in space.cells]
        return (sum(ys) // len(ys), sum(xs) // len(xs))

    @staticmethod
    def _straight_path(
        scene: CampScene,
        start,
        target_coords,
    ) -> List[SquareCell]:
        """
        Walk from ``start`` toward the nearest target coord in a straight
        line (Bresenham-like), carving wall cells as we go.
        """
        if not target_coords:
            return []

        # Find closest target
        sy, sx = start
        ey, ex = min(
            target_coords,
            key=lambda p: abs(p[0] - sy) + abs(p[1] - sx),
        )

        carved = []
        cy, cx = sy, sx
        while (cy, cx) not in target_coords:
            cell = scene.grid.cells[cy][cx]
            if cell.space is None:
                cell.filled = False
                carved.append(cell)

            dy = ey - cy
            dx = ex - cx
            if dy == 0 and dx == 0:
                break

            # Advance one step — whichever axis needs it more (with random
            # tie-breaking to reduce grid-aligned rigidity)
            if abs(dy) > abs(dx) or (abs(dy) == abs(dx) and random.random() < 0.5):
                cy += 1 if dy > 0 else -1
            else:
                cx += 1 if dx > 0 else -1

            cy = max(0, min(scene.n_rows - 1, cy))
            cx = max(0, min(scene.n_cols - 1, cx))

        return carved

    def _carve_perimeter(
        self, scene: CampScene, tents: List[Tent], radius: float
    ) -> None:
        """Carve a rough circular ring at the perimeter radius."""
        cy = scene.n_rows // 2
        cx = scene.n_cols // 2
        steps = max(16, self.n_tents * 6)

        prev_coords = None
        first_coords = None

        for i in range(steps + 1):
            angle = (2 * math.pi / steps) * i
            r = int(round(cy + radius * math.sin(angle)))
            c = int(round(cx + radius * math.cos(angle)))
            r = max(1, min(scene.n_rows - 2, r))
            c = max(1, min(scene.n_cols - 2, c))

            if i == 0:
                first_coords = (r, c)

            if prev_coords is not None and (r, c) != prev_coords:
                # Carve the step between prev and current
                for coords in [(prev_coords[0], c), (r, prev_coords[1])]:
                    pr, pc = coords
                    cell = scene.grid.cells[pr][pc]
                    if cell.space is None:
                        cell.filled = False

            prev_coords = (r, c)

        scene.grid.link_edges_to_cells()
