"""
Forest scene type: open ground scattered with individual trees and undergrowth.

Design model
------------
* Almost all cells are **unfilled** (open, traversable ground).
* :class:`Tree` spaces mark individual trees (``filled=True``).  These are solid
  vision-blocking obstacles.  In a future FoundryVTT export each tree cell will
  be represented as a *circular* wall polygon (~10 segments centred on the cell)
  rather than four box edges, to match the visual round footprint of a tree.
* :class:`Undergrowth` spaces mark brush / low vegetation (``filled=False``).
  Currently cosmetic only; Foundry export treatment is deferred.
"""
import random
from typing import Dict, List, Set, Tuple

from donjuan.core.cell import SquareCell
from donjuan.core.randomizer import Randomizer
from donjuan.core.scene import Scene
from donjuan.core.space import Space


# ── Space subclasses ────────────────────────────────────────────────────────


class Tree(Space):
    """
    A single tree or very tight cluster of trees (1–2 filled cells).

    Cells in this space are ``filled=True`` — solid, vision-blocking.

    Note: FoundryVTT export will represent each tree cell as a circular wall
    polygon rather than four rectangular edges.
    """

    pass


class Undergrowth(Space):
    """
    A patch of brush, ferns, or low vegetation (3–8 unfilled cells).

    Cells are ``filled=False`` so the space is traversable.  Cosmetic only
    for now; Foundry export treatment is deferred.
    """

    pass


# ── Scene container ─────────────────────────────────────────────────────────


class ForestScene(Scene):
    """
    A forest battle-map scene.  The grid is mostly open ground; individual
    :class:`Tree` obstacles are scattered across it, with patches of
    :class:`Undergrowth` adding visual texture.

    Args:
        n_rows (int): grid rows (ignored if ``grid`` supplied)
        n_cols (int): grid columns (ignored if ``grid`` supplied)
        grid: pre-built :class:`~donjuan.grid.Grid` (overrides n_rows/n_cols)
    """

    def __init__(self, n_rows: int = 20, n_cols: int = 20, grid=None):
        from donjuan.core.grid import SquareGrid

        super().__init__(
            grid=grid or SquareGrid(n_rows, n_cols),
            scene_type="forest",
        )
        self.trees: Dict[str, Tree] = {}
        self.undergrowth: Dict[str, Undergrowth] = {}

        # Open ground: unset the default filled=True on every cell so the
        # scene starts as fully traversable terrain.
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                self.grid.cells[r][c].filled = False

    def add_tree(self, tree: Tree) -> None:
        self.trees[str(tree.name)] = tree

    def add_undergrowth(self, patch: Undergrowth) -> None:
        self.undergrowth[str(patch.name)] = patch


# ── Randomizer ──────────────────────────────────────────────────────────────


class ForestRandomizer(Randomizer):
    """
    Generates a :class:`ForestScene` by scattering individual trees and
    undergrowth patches across open ground.

    Args:
        tree_density (float): fraction of cells to occupy with trees (0–1,
            default 0.08).  Actual count = ``tree_density * n_rows * n_cols``.
        undergrowth_density (float): fraction of cells to occupy with
            undergrowth patches (0–1, default 0.12).
        min_tree_spacing (int): minimum Manhattan distance between any two
            tree cells, keeping trees from clumping (default 2).
        max_attempts (int): placement retries per tree before giving up
            (default 20).
    """

    def __init__(
        self,
        tree_density: float = 0.08,
        undergrowth_density: float = 0.12,
        min_tree_spacing: int = 2,
        max_attempts: int = 20,
    ):
        super().__init__()
        self.tree_density = tree_density
        self.undergrowth_density = undergrowth_density
        self.min_tree_spacing = min_tree_spacing
        self.max_attempts = max_attempts

    def randomize(self, scene: ForestScene) -> None:
        """
        Populate *scene* with trees and undergrowth.

        All grid cells begin unfilled; this method marks tree cells as
        ``filled=True`` and assigns space objects to tree and undergrowth cells.

        Args:
            scene (ForestScene): the scene to populate
        """
        # All cells start unfilled — nothing to do for ground setup.
        n_trees = int(self.tree_density * scene.n_rows * scene.n_cols)
        n_undergrowth_cells = int(
            self.undergrowth_density * scene.n_rows * scene.n_cols
        )

        tree_coords = self._place_trees(scene, n_trees)
        self._place_undergrowth(scene, n_undergrowth_cells, tree_coords)

    # ── Tree placement ───────────────────────────────────────────────────────

    def _place_trees(
        self, scene: ForestScene, n_trees: int
    ) -> Set[Tuple[int, int]]:
        """
        Scatter ``n_trees`` individual tree cells across the grid, respecting
        ``min_tree_spacing`` so trees stay visually distinct.

        Returns the set of (row, col) coordinates that were claimed by trees.
        """
        occupied: Set[Tuple[int, int]] = set()
        rows, cols = scene.n_rows, scene.n_cols

        for idx in range(n_trees):
            for _ in range(self.max_attempts):
                r = random.randint(0, rows - 1)
                c = random.randint(0, cols - 1)
                if (r, c) in occupied:
                    continue
                if self._too_close(r, c, occupied, self.min_tree_spacing):
                    continue

                cell = scene.grid.cells[r][c]
                cell.filled = True
                tree = Tree(cells={cell}, name=f"TR{idx}")
                scene.emplace_space(tree)
                scene.add_tree(tree)
                occupied.add((r, c))
                break

        return occupied

    # ── Undergrowth placement ────────────────────────────────────────────────

    def _place_undergrowth(
        self,
        scene: ForestScene,
        target_cells: int,
        tree_coords: Set[Tuple[int, int]],
    ) -> None:
        """
        Scatter irregular undergrowth patches until approximately
        ``target_cells`` cells are covered.

        Each patch grows from a random seed cell by repeatedly annexing a
        random neighbour, producing organic blob shapes of 3–8 cells.
        Undergrowth is never placed on a tree cell.
        """
        rows, cols = scene.n_rows, scene.n_cols
        claimed: Set[Tuple[int, int]] = set(tree_coords)
        placed_cells = 0
        patch_idx = 0

        while placed_cells < target_cells:
            # Pick a seed not already used
            sr = random.randint(0, rows - 1)
            sc = random.randint(0, cols - 1)
            if (sr, sc) in claimed:
                continue

            patch_size = random.randint(3, 8)
            patch_coords: List[Tuple[int, int]] = []
            frontier = [(sr, sc)]
            visited: Set[Tuple[int, int]] = {(sr, sc)}

            while frontier and len(patch_coords) < patch_size:
                r, c = frontier.pop(random.randrange(len(frontier)))
                if (r, c) in claimed:
                    continue
                patch_coords.append((r, c))
                claimed.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in visited
                        and (nr, nc) not in claimed
                    ):
                        visited.add((nr, nc))
                        frontier.append((nr, nc))

            if not patch_coords:
                continue

            cells = set()
            for r, c in patch_coords:
                cell = scene.grid.cells[r][c]
                cells.add(cell)

            patch = Undergrowth(cells=cells, name=f"UG{patch_idx}")
            scene.emplace_space(patch)
            scene.add_undergrowth(patch)
            placed_cells += len(patch_coords)
            patch_idx += 1

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _too_close(
        r: int, c: int, occupied: Set[Tuple[int, int]], min_dist: int
    ) -> bool:
        """Return True if (r, c) is within ``min_dist`` of any occupied cell."""
        for or_, oc in occupied:
            if abs(r - or_) + abs(c - oc) < min_dist:
                return True
        return False
