"""Tests for CampScene, CampRandomizer, and CampRenderer."""
import pytest

from donjuan import CampRenderer, CampScene, Scene
from donjuan.camp import CampPath, CampRandomizer, FirePit, Tent


# ── CampScene ───────────────────────────────────────────────────────────────


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


def test_camp_scene_empty_on_init():
    scene = CampScene(n_rows=10, n_cols=10)
    assert scene.fire_pit is None
    assert len(scene.tents) == 0
    assert len(scene.paths) == 0


# ── CampRandomizer ──────────────────────────────────────────────────────────


def test_camp_randomizer_places_fire_pit():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    assert scene.fire_pit is not None
    assert isinstance(scene.fire_pit, FirePit)


def test_camp_fire_pit_near_centre():
    """Fire pit cells should be near the grid centre."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4, fire_radius=2).randomize(scene)
    assert scene.fire_pit is not None
    for cell in scene.fire_pit.cells:
        assert not cell.filled
        assert abs(cell.y - 15) <= 5
        assert abs(cell.x - 15) <= 5


def test_camp_randomizer_places_tents():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=6).randomize(scene)
    assert len(scene.tents) > 0


def test_camp_tents_are_tent_instances():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for tent in scene.tents.values():
        assert isinstance(tent, Tent)


def test_camp_tent_cells_are_open():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for tent in scene.tents.values():
        for cell in tent.cells:
            assert not cell.filled


def test_camp_paths_connect_to_scene():
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for path in scene.paths.values():
        assert isinstance(path, CampPath)
        for cell in path.cells:
            assert not cell.filled


def test_camp_randomizer_small_grid_does_not_crash():
    scene = CampScene(n_rows=8, n_cols=8)
    CampRandomizer(n_tents=3, fire_radius=1).randomize(scene)


def test_camp_randomizer_perimeter_flag():
    """Perimeter=True should not crash and should open extra cells."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4, perimeter=True).randomize(scene)
    # Just check it doesn't raise and fire pit is placed
    assert scene.fire_pit is not None


def test_camp_randomizer_no_doors():
    """Camp scenes never set has_door."""
    scene = CampScene(n_rows=30, n_cols=30)
    CampRandomizer(n_tents=4).randomize(scene)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            for edge in scene.grid.cells[r][c].edges:
                if edge is not None:
                    assert not edge.has_door


# ── CampRenderer ────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_camp_renderer_produces_image(tmp_path):
    scene = CampScene(n_rows=20, n_cols=20)
    CampRandomizer(n_tents=5, fire_radius=2).randomize(scene)
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
def test_camp_renderer_no_fire_pit_does_not_crash():
    """Renderer should handle a scene with no fire pit (edge case)."""
    scene = CampScene(n_rows=15, n_cols=15)
    # Don't run randomizer — fire_pit stays None
    renderer = CampRenderer(tile_size=24, fire_glow=True)
    fig, ax = renderer.render(scene, save=False)
    assert fig is not None
