"""Tests for CampScene, CampRandomizer, and CampRenderer."""
import math

import pytest

from donjuan import CampRenderer, CampScene, Scene
from donjuan.camp.scene import CampPath, CampRandomizer, CampTree, FirePit, Tent


# ── CampScene ────────────────────────────────────────────────────────────────


def test_camp_scene_is_scene():
    scene = CampScene(n_rows=20, n_cols=20)
    assert isinstance(scene, Scene)


def test_camp_scene_type():
    scene = CampScene(n_rows=10, n_cols=10)
    assert scene.scene_type == "camp"


def test_camp_scene_dimensions():
    scene = CampScene(n_rows=18, n_cols=22)
    assert scene.n_rows == 18
    assert scene.n_cols == 22


def test_camp_scene_all_cells_unfilled_on_init():
    """Fresh CampScene: all cells start as open ground (unfilled)."""
    scene = CampScene(n_rows=8, n_cols=8)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            assert not scene.grid.cells[r][c].filled


def test_camp_scene_empty_on_init():
    scene = CampScene(n_rows=10, n_cols=10)
    assert len(scene.fires) == 0
    assert scene.fire_pit is None  # backward-compat property
    assert len(scene.tents) == 0
    assert len(scene.paths) == 0
    assert len(scene.trees) == 0


# ── CampRandomizer ────────────────────────────────────────────────────────────


def test_camp_randomizer_places_one_fire_by_default():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer().randomize(scene)
    assert len(scene.fires) == 1
    assert isinstance(scene.fires[0], FirePit)


def test_camp_randomizer_places_n_fires():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_fires=3, n_tents=6).randomize(scene)
    assert len(scene.fires) == 3


def test_camp_fire_is_single_cell():
    """Each fire must occupy exactly one cell."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_fires=2, n_tents=4).randomize(scene)
    for fire in scene.fires:
        assert len(fire.cells) == 1


def test_camp_fire_cells_are_unfilled():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer().randomize(scene)
    for fire in scene.fires:
        for cell in fire.cells:
            assert not cell.filled


def test_camp_single_fire_near_centre():
    """With one fire it should land at the grid centre."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_fires=1).randomize(scene)
    cell = next(iter(scene.fires[0].cells))
    assert abs(cell.y - 15) <= 2
    assert abs(cell.x - 15) <= 2


def test_camp_backward_compat_fire_pit_property():
    """fire_pit property returns the first fire or None."""
    scene = CampScene(n_rows=20, n_cols=20)
    assert scene.fire_pit is None
    CampRandomizer(n_fires=1).randomize(scene)
    assert scene.fire_pit is scene.fires[0]


def test_camp_randomizer_places_tents():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=6).randomize(scene)
    assert len(scene.tents) > 0


def test_camp_tents_are_tent_instances():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for tent in scene.tents.values():
        assert isinstance(tent, Tent)


def test_camp_tent_cells_are_unfilled():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for tent in scene.tents.values():
        for cell in tent.cells:
            assert not cell.filled


def test_camp_tent_sizes_small():
    """Tents should be at most 3 cells in any dimension (1×2, 2×2, 2×3)."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=8).randomize(scene)
    for tent in scene.tents.values():
        ys = [c.y for c in tent.cells]
        xs = [c.x for c in tent.cells]
        h = max(ys) - min(ys) + 1
        w = max(xs) - min(xs) + 1
        assert h <= 3, f"Tent height {h} exceeds max 3"
        assert w <= 3, f"Tent width {w} exceeds max 3"
        assert h * w <= 6, f"Tent area {h * w} exceeds max 6"


def test_camp_paths_are_camppath_instances():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for path in scene.paths.values():
        assert isinstance(path, CampPath)
        for cell in path.cells:
            assert not cell.filled


def test_camp_trees_are_filled():
    """CampTree cells must be filled=True."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(perimeter_tree_density=0.10).randomize(scene)
    for tree in scene.trees.values():
        assert isinstance(tree, CampTree)
        for cell in tree.cells:
            assert cell.filled


def test_camp_trees_in_outer_band():
    """Trees should appear in the outer portion of the grid, not near the centre."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(perimeter_tree_density=0.10).randomize(scene)
    cy, cx = scene.n_rows / 2.0, scene.n_cols / 2.0
    half = min(scene.n_rows, scene.n_cols) / 2.0
    inner_limit = half * 0.6  # trees should not be closer than 60 % of half

    for tree in scene.trees.values():
        for cell in tree.cells:
            dist = math.sqrt((cell.y - cy) ** 2 + (cell.x - cx) ** 2)
            assert dist >= inner_limit * 0.8, (
                f"Tree at ({cell.y},{cell.x}) is suspiciously close to centre "
                f"(dist={dist:.1f}, limit={inner_limit:.1f})"
            )


def test_camp_zero_tree_density_no_trees():
    scene = CampScene(n_rows=20, n_cols=20)
    CampRandomizer(perimeter_tree_density=0.0).randomize(scene)
    assert len(scene.trees) == 0


def test_camp_no_doors():
    """Camp scenes never set has_door on any edge."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            for edge in scene.grid.cells[r][c].edges:
                if edge is not None:
                    assert not edge.has_door


def test_camp_small_grid_does_not_crash():
    scene = CampScene(n_rows=8, n_cols=8)
    CampRandomizer(n_tents=3).randomize(scene)


def test_camp_multi_fire_does_not_crash():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_fires=3, n_tents=9).randomize(scene)
    assert len(scene.fires) == 3


# ── CampRenderer ─────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_camp_renderer_produces_image(tmp_path):
    scene = CampScene(n_rows=20, n_cols=20)
    CampRandomizer(n_fires=1, n_tents=5, perimeter_tree_density=0.05).randomize(scene)
    renderer = CampRenderer(tile_size=24)
    path = str(tmp_path / "camp.png")
    fig, ax = renderer.render(scene, file_path=path, save=True)
    assert fig is not None
    assert renderer._last_image is not None
    import os
    assert os.path.exists(path)


@pytest.mark.slow
def test_camp_renderer_no_save():
    scene = CampScene(n_rows=15, n_cols=15)
    CampRandomizer(n_tents=4).randomize(scene)
    renderer = CampRenderer(tile_size=24)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None
    assert renderer._last_image is not None


@pytest.mark.slow
def test_camp_renderer_no_fires_does_not_crash():
    """Renderer handles a scene with no fires (e.g. empty scene)."""
    scene = CampScene(n_rows=15, n_cols=15)
    renderer = CampRenderer(tile_size=24, fire_glow=True)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None


@pytest.mark.slow
def test_camp_renderer_multi_fire():
    scene = CampScene(n_rows=20, n_cols=20)
    CampRandomizer(n_fires=2, n_tents=6).randomize(scene)
    renderer = CampRenderer(tile_size=24)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None
