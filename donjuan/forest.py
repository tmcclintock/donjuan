"""
Forest scene type: clearings connected by winding paths through dense trees.
"""
import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from donjuan.cell import SquareCell
from donjuan.randomizer import Randomizer
from donjuan.scene import Scene
from donjuan.space import Space


# ── Space subclasses ────────────────────────────────────────────────────────


class Clearing(Space):
    """An open area in a forest — analogous to a room."""

    pass


class ForestPath(Space):
    """A winding track carved through trees — analogous to a hallway."""

    pass


# ── Scene container ─────────────────────────────────────────────────────────


class ForestScene(Scene):
    """
    A forest scene: a grid of dense trees punctuated by open clearings
    connected by winding dirt paths.

    Args:
        n_rows (int): grid rows (ignored if ``grid`` supplied)
        n_cols (int): grid columns (ignored if ``grid`` supplied)
        grid: pre-built :class:`~donjuan.grid.Grid` (overrides n_rows/n_cols)
    """

    def __init__(self, n_rows: int = 20, n_cols: int = 20, grid=None):
        from donjuan.grid import SquareGrid

        super().__init__(
            grid=grid or SquareGrid(n_rows, n_cols),
            scene_type="forest",
        )
        self.clearings: Dict[str, Clearing] = {}
        self.paths: Dict[str, ForestPath] = {}

    def add_clearing(self, clearing: Clearing) -> None:
        self.clearings[str(clearing.name)] = clearing

    def add_path(self, path: ForestPath) -> None:
        self.paths[str(path.name)] = path


# ── Randomizer ──────────────────────────────────────────────────────────────


class ForestRandomizer(Randomizer):
    """
    Generates a :class:`ForestScene` by placing circular clearings and
    connecting them with drunken-walk paths.

    Args:
        n_clearings (int): number of clearings to place (default 5)
        min_radius (int): minimum clearing radius in cells (default 2)
        max_radius (int): maximum clearing radius in cells (default 4)
        max_attempts (int): placement attempts before giving up on a clearing
        walk_bias (float): probability of stepping toward target each step (0–1)
    """

    def __init__(
        self,
        n_clearings: int = 5,
        min_radius: int = 2,
        max_radius: int = 4,
        max_attempts: int = 100,
        walk_bias: float = 0.7,
    ):
        super().__init__()
        self.n_clearings = n_clearings
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.max_attempts = max_attempts
        self.walk_bias = walk_bias

    def randomize(self, scene: ForestScene) -> None:
        """
        Generate clearings and connecting paths in the given scene.

        Args:
            scene (ForestScene): the scene to populate
        """
        clearings = self._place_clearings(scene)
        if len(clearings) < 2:
            return

        pairs = self._build_spanning_tree(clearings)
        for i, (a, b) in enumerate(pairs):
            carved = self._drunken_walk(scene, a, b)
            if not carved:
                continue
            path = ForestPath(cells=set(carved), name=f"P{i}")
            scene.emplace_space(path)
            scene.add_path(path)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _place_clearings(self, scene: ForestScene) -> List[Clearing]:
        """Place up to ``n_clearings`` non-overlapping circular clearings."""
        placed: List[Clearing] = []

        for idx in range(self.n_clearings):
            for _ in range(self.max_attempts):
                radius = random.randint(self.min_radius, self.max_radius)
                # Centre must be far enough from edges that the full circle fits
                margin = radius + 1
                if scene.n_rows <= 2 * margin or scene.n_cols <= 2 * margin:
                    continue
                cy = random.randint(margin, scene.n_rows - margin - 1)
                cx = random.randint(margin, scene.n_cols - margin - 1)

                cells = self._circle_cells(cy, cx, radius)
                clearing = Clearing(cells=set(cells), name=f"C{idx}")

                if any(clearing.overlaps(p) for p in placed):
                    continue

                scene.emplace_space(clearing)
                scene.add_clearing(clearing)
                placed.append(clearing)
                break

        return placed

    @staticmethod
    def _circle_cells(cy: int, cx: int, radius: int) -> List[SquareCell]:
        """Return unfilled cells within Euclidean distance ``radius`` of (cy, cx)."""
        cells = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dy * dy + dx * dx <= radius * radius:
                    cells.append(
                        SquareCell(filled=False, coordinates=(cy + dy, cx + dx))
                    )
        return cells

    @staticmethod
    def _center(clearing: Clearing) -> Tuple[int, int]:
        ys = [c.y for c in clearing.cells]
        xs = [c.x for c in clearing.cells]
        return (sum(ys) // len(ys), sum(xs) // len(xs))

    def _build_spanning_tree(
        self, clearings: List[Clearing]
    ) -> List[Tuple[Clearing, Clearing]]:
        """Prim's MST over clearings by Manhattan distance between centres."""
        centers = {id(c): self._center(c) for c in clearings}
        visited: Dict[int, Clearing] = {id(clearings[0]): clearings[0]}
        unvisited: Dict[int, Clearing] = {id(c): c for c in clearings[1:]}
        pairs: List[Tuple[Clearing, Clearing]] = []

        while unvisited:
            best_dist = None
            best_v: Optional[Clearing] = None
            best_u: Optional[Clearing] = None

            for v_id, v in visited.items():
                vy, vx = centers[v_id]
                for u_id, u in unvisited.items():
                    uy, ux = centers[u_id]
                    dist = abs(vy - uy) + abs(vx - ux)
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_v = v
                        best_u = u

            if best_u is None:
                break
            pairs.append((best_v, best_u))
            visited[id(best_u)] = best_u
            del unvisited[id(best_u)]

        return pairs

    def _drunken_walk(
        self,
        scene: ForestScene,
        start_clearing: Clearing,
        end_clearing: Clearing,
    ) -> List[SquareCell]:
        """
        Walk from the centre of ``start_clearing`` toward ``end_clearing``
        with a directional bias, carving wall cells as we go.

        Returns:
            List of newly-carved :class:`~donjuan.cell.SquareCell` objects
            (cells that were solid wall before this walk).
        """
        sy, sx = self._center(start_clearing)
        ey, ex = self._center(end_clearing)
        target_coords: Set[Tuple[int, int]] = {
            (c.y, c.x) for c in end_clearing.cells
        }

        max_steps = 5 * (abs(ey - sy) + abs(ex - sx) + 1)
        cy, cx = sy, sx
        carved: List[SquareCell] = []

        for _ in range(max_steps):
            if (cy, cx) in target_coords:
                break

            cell = scene.grid.cells[cy][cx]
            if cell.space is None:
                cell.filled = False
                carved.append(cell)

            dy = ey - cy
            dx = ex - cx
            if dy == 0 and dx == 0:
                break

            # Choose direction: biased toward target, with occasional side step
            if random.random() < self.walk_bias:
                # Primary direction: whichever axis has larger remaining distance
                if abs(dy) >= abs(dx):
                    step = (1 if dy > 0 else -1, 0)
                else:
                    step = (0, 1 if dx > 0 else -1)
            else:
                # Perpendicular to the primary direction
                if abs(dy) >= abs(dx):
                    step = (0, random.choice([-1, 1]))
                else:
                    step = (random.choice([-1, 1]), 0)

            # Clamp to grid bounds
            ny = max(0, min(scene.n_rows - 1, cy + step[0]))
            nx = max(0, min(scene.n_cols - 1, cx + step[1]))
            cy, cx = ny, nx

        else:
            # max_steps exhausted — fall back to BFS for the final stretch
            extra = self._bfs_carve(scene, (cy, cx), target_coords)
            carved.extend(extra)

        return carved

    @staticmethod
    def _bfs_carve(
        scene: ForestScene,
        start: Tuple[int, int],
        targets: Set[Tuple[int, int]],
    ) -> List[SquareCell]:
        """BFS fallback: carve the shortest path from ``start`` to any target."""
        if start in targets:
            return []

        queue: deque = deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

        while queue:
            cy, cx = queue.popleft()
            if (cy, cx) in targets:
                # Reconstruct
                path: List[Tuple[int, int]] = []
                node: Optional[Tuple[int, int]] = (cy, cx)
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                carved = []
                for y, x in path:
                    cell = scene.grid.cells[y][x]
                    if cell.space is None:
                        cell.filled = False
                        carved.append(cell)
                return carved

            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy + dy, cx + dx
                if (
                    0 <= ny < scene.n_rows
                    and 0 <= nx < scene.n_cols
                    and (ny, nx) not in came_from
                ):
                    came_from[(ny, nx)] = (cy, cx)
                    queue.append((ny, nx))

        return []
