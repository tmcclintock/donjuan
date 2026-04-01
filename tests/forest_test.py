"""Tests for ForestScene, ForestRandomizer, and ForestRenderer."""
import pytest

from donjuan import ForestRenderer, ForestScene, Scene
from donjuan.forest import Clearing, ForestPath, ForestRandomizer


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


def test_forest_scene_empty_on_init():
    scene = ForestScene(n_rows=10, n_cols=10)
    assert len(scene.clearings) == 0
    assert len(scene.paths) == 0


# ── ForestRandomizer ────────────────────────────────────────────────────────


def test_forest_randomizer_places_clearings():
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=4, min_radius=2, max_radius=3)
    rng.randomize(scene)
    assert len(scene.clearings) >= 1


def test_forest_randomizer_clearings_have_open_cells():
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=3, min_radius=2, max_radius=3)
    rng.randomize(scene)
    for clearing in scene.clearings.values():
        assert isinstance(clearing, Clearing)
        for cell in clearing.cells:
            assert not cell.filled


def test_forest_randomizer_paths_are_forest_path():
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=3, min_radius=2, max_radius=2)
    rng.randomize(scene)
    for path in scene.paths.values():
        assert isinstance(path, ForestPath)


def test_forest_randomizer_paths_open_cells():
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=3, min_radius=2, max_radius=2)
    rng.randomize(scene)
    for path in scene.paths.values():
        for cell in path.cells:
            assert not cell.filled


def test_forest_randomizer_no_doors():
    """Forest scenes should not set has_door on any edge."""
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=3, min_radius=2, max_radius=2)
    rng.randomize(scene)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            for edge in scene.grid.cells[r][c].edges:
                if edge is not None:
                    assert not edge.has_door


def test_forest_randomizer_small_grid_does_not_crash():
    """Should not raise even if grid is too small for clearings."""
    scene = ForestScene(n_rows=5, n_cols=5)
    rng = ForestRandomizer(n_clearings=3, min_radius=3, max_radius=4)
    rng.randomize(scene)  # may place 0 clearings; should not raise


def test_forest_randomizer_single_clearing_no_paths():
    """With only one clearing there are no MST pairs, so no paths."""
    scene = ForestScene(n_rows=30, n_cols=30)
    rng = ForestRandomizer(n_clearings=1, min_radius=2, max_radius=2, max_attempts=5)
    rng.randomize(scene)
    assert len(scene.paths) == 0


# ── ForestRenderer ──────────────────────────────────────────────────────────


@pytest.mark.slow
def test_forest_renderer_produces_image(tmp_path):
    scene = ForestScene(n_rows=20, n_cols=20)
    ForestRandomizer(n_clearings=4, min_radius=2, max_radius=3).randomize(scene)
    renderer = ForestRenderer(tile_size=24)
    path = str(tmp_path / "forest.png")
    fig, ax = renderer.render(scene, file_path=path, save=True)
    assert fig is not None
    assert renderer._last_image is not None
    import os
    assert os.path.exists(path)


@pytest.mark.slow
def test_forest_renderer_no_save(tmp_path):
    scene = ForestScene(n_rows=15, n_cols=15)
    ForestRandomizer(n_clearings=3).randomize(scene)
    renderer = ForestRenderer(tile_size=24)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None
    assert renderer._last_image is not None
