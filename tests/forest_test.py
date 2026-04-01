"""Tests for ForestScene, ForestRandomizer, and ForestRenderer."""
import numpy as np
import pytest

from donjuan import ForestRenderer, ForestScene, Scene
from donjuan.forest.scene import ForestRandomizer, Tree, Undergrowth


# ── ForestScene ─────────────────────────────────────────────────────────────


def test_forest_scene_is_scene():
    scene = ForestScene(n_rows=20, n_cols=20)
    assert isinstance(scene, Scene)


def test_forest_scene_type():
    scene = ForestScene(n_rows=10, n_cols=10)
    assert scene.scene_type == "forest"


def test_forest_scene_dimensions():
    scene = ForestScene(n_rows=15, n_cols=25)
    assert scene.n_rows == 15
    assert scene.n_cols == 25


def test_forest_scene_all_cells_unfilled_on_init():
    """Fresh ForestScene: all cells are open ground (unfilled)."""
    scene = ForestScene(n_rows=8, n_cols=8)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            assert not scene.grid.cells[r][c].filled


def test_forest_scene_empty_on_init():
    scene = ForestScene(n_rows=10, n_cols=10)
    assert len(scene.trees) == 0
    assert len(scene.undergrowth) == 0


# ── ForestRandomizer ────────────────────────────────────────────────────────


def test_forest_randomizer_places_trees():
    scene = ForestScene(n_rows=20, n_cols=20)
    rng = ForestRandomizer(tree_density=0.1)
    rng.randomize(scene)
    assert len(scene.trees) >= 1


def test_forest_tree_cells_are_filled():
    """Every cell belonging to a Tree space must be filled=True."""
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.1).randomize(scene)
    for tree in scene.trees.values():
        assert isinstance(tree, Tree)
        for cell in tree.cells:
            assert cell.filled


def test_forest_undergrowth_cells_are_unfilled():
    """Undergrowth cells are traversable (filled=False)."""
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.0, undergrowth_density=0.15).randomize(scene)
    for patch in scene.undergrowth.values():
        assert isinstance(patch, Undergrowth)
        for cell in patch.cells:
            assert not cell.filled


def test_forest_trees_respect_minimum_spacing():
    """No two tree cells should be closer than min_tree_spacing (Manhattan)."""
    min_spacing = 3
    scene = ForestScene(n_rows=30, n_cols=30)
    ForestRandomizer(tree_density=0.05, min_tree_spacing=min_spacing).randomize(scene)

    tree_coords = []
    for tree in scene.trees.values():
        for cell in tree.cells:
            tree_coords.append((cell.y, cell.x))

    for i, (r1, c1) in enumerate(tree_coords):
        for r2, c2 in tree_coords[i + 1 :]:
            dist = abs(r1 - r2) + abs(c1 - c2)
            assert dist >= min_spacing, (
                f"Trees at ({r1},{c1}) and ({r2},{c2}) are only {dist} apart "
                f"(min_spacing={min_spacing})"
            )


def test_forest_undergrowth_not_placed_on_tree_cells():
    """Undergrowth must never overlap with tree cells."""
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.08, undergrowth_density=0.15).randomize(scene)

    tree_coords = set()
    for tree in scene.trees.values():
        for cell in tree.cells:
            tree_coords.add((cell.y, cell.x))

    for patch in scene.undergrowth.values():
        for cell in patch.cells:
            assert (cell.y, cell.x) not in tree_coords


def test_forest_zero_density_no_trees():
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.0, undergrowth_density=0.0).randomize(scene)
    assert len(scene.trees) == 0
    assert len(scene.undergrowth) == 0


def test_forest_no_doors():
    """Forest scenes should not set has_door on any edge."""
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.08, undergrowth_density=0.12).randomize(scene)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            for edge in scene.grid.cells[r][c].edges:
                if edge is not None:
                    assert not edge.has_door


def test_forest_small_grid_does_not_crash():
    """Tiny grids should not raise even if few trees fit."""
    scene = ForestScene(n_rows=4, n_cols=4)
    ForestRandomizer(tree_density=0.1, min_tree_spacing=3).randomize(scene)


def test_forest_renderer_uses_tree_icon_palette():
    renderer = ForestRenderer(tile_size=24, wall_shadows=False, canopy_bleed=False)
    from PIL import Image
    img = Image.new("RGB", (24, 24), (0, 0, 0))
    renderer._draw_tree(img, 0, 0)
    arr = np.array(img)

    canopy_color = np.array([38, 92, 40], dtype=np.uint8)
    trunk_color = np.array([90, 58, 26], dtype=np.uint8)
    assert np.any(np.all(arr == canopy_color, axis=2))
    assert np.any(np.all(arr == trunk_color, axis=2))


# ── ForestRenderer ──────────────────────────────────────────────────────────


@pytest.mark.slow
def test_forest_renderer_produces_image(tmp_path):
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(tree_density=0.08, undergrowth_density=0.12).randomize(scene)
    renderer = ForestRenderer(tile_size=24)
    path = str(tmp_path / "forest.png")
    fig, ax = renderer.render(scene, file_path=path, save=True)
    assert fig is not None
    assert renderer._last_image is not None
    import os
    assert os.path.exists(path)


@pytest.mark.slow
def test_forest_renderer_no_save():
    scene = ForestScene(n_rows=15, n_cols=15)
    ForestRandomizer(tree_density=0.08, undergrowth_density=0.12).randomize(scene)
    renderer = ForestRenderer(tile_size=24)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None
    assert renderer._last_image is not None
