"""Tests for ForestExporter — FoundryVTT export of ForestScene."""
import json
import math
import os
import tempfile

import pytest

from donjuan.forest.scene import ForestRandomizer, ForestScene
from donjuan.forest.exporter import ForestExporter


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_scene(n_rows=16, n_cols=16, seed=42, tree_density=0.08):
    from donjuan.core.randomizer import Randomizer
    Randomizer.seed(seed)
    scene = ForestScene(n_rows=n_rows, n_cols=n_cols)
    ForestRandomizer(tree_density=tree_density, undergrowth_density=0.10).randomize(scene)
    return scene


# ── ForestExporter unit tests (no file I/O) ───────────────────────────────────


def test_exporter_builds_boundary_walls():
    scene = _make_scene()
    exporter = ForestExporter(tile_size=50, tree_wall_segments=8)
    walls = exporter._build_walls(scene)

    # Boundary walls: exactly 4
    t = exporter.tile_size
    W = scene.n_cols * t
    H = scene.n_rows * t
    boundary_coords = {
        (0, 0, W, 0),
        (W, 0, W, H),
        (W, H, 0, H),
        (0, H, 0, 0),
    }
    found = set()
    for w in walls:
        c = tuple(w["c"])
        if c in boundary_coords:
            found.add(c)
    assert found == boundary_coords, "Not all four boundary walls were generated"


def test_exporter_no_boundary_walls_when_disabled():
    scene = _make_scene()
    exporter = ForestExporter(tile_size=50, add_boundary_walls=False)
    walls = exporter._build_walls(scene)

    t = exporter.tile_size
    W = scene.n_cols * t
    H = scene.n_rows * t
    boundary_coords = {
        (0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0),
    }
    for w in walls:
        assert tuple(w["c"]) not in boundary_coords, \
            "Boundary wall found when add_boundary_walls=False"


def test_exporter_tree_walls_count():
    """Each tree cell should produce exactly tree_wall_segments wall segments."""
    scene = _make_scene(tree_density=0.05)
    n_segs = 8
    exporter = ForestExporter(tile_size=50, tree_wall_segments=n_segs,
                              add_boundary_walls=False,
                              add_undergrowth_walls=False)
    walls = exporter._build_walls(scene)

    n_trees = len(scene.trees)
    assert len(walls) == n_trees * n_segs, (
        f"Expected {n_trees} trees × {n_segs} segs = {n_trees * n_segs} walls, "
        f"got {len(walls)}"
    )


def test_exporter_zero_trees_only_boundary_walls():
    scene = _make_scene(tree_density=0.0)
    exporter = ForestExporter(tile_size=50, add_undergrowth_walls=False)
    walls = exporter._build_walls(scene)
    assert len(walls) == 4  # boundary only


def test_exporter_tree_walls_form_circle():
    """Verify that the generated wall segments are tangent to the expected radius."""
    scene = ForestScene(n_rows=5, n_cols=5)
    # Manually place one tree at (2, 2)
    scene.grid.cells[2][2].filled = True

    n_segs = 10
    tile_size = 100
    radius_frac = 0.42
    exporter = ForestExporter(
        tile_size=tile_size,
        tree_wall_segments=n_segs,
        tree_wall_radius_fraction=radius_frac,
        add_boundary_walls=False,
        add_undergrowth_walls=False,
    )
    walls = exporter._build_walls(scene)
    assert len(walls) == n_segs

    cx = (2 + 0.5) * tile_size
    cy = (2 + 0.5) * tile_size
    expected_radius = tile_size * radius_frac

    for w in walls:
        x1, y1, x2, y2 = w["c"]
        # Both endpoints should be approximately on the circle
        for px, py in [(x1, y1), (x2, y2)]:
            dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
            assert abs(dist - expected_radius) < 2.0, (
                f"Point ({px},{py}) is {dist:.1f}px from centre, "
                f"expected ~{expected_radius}"
            )


def test_exporter_wall_structure():
    """All generated walls should have the required FoundryVTT fields."""
    scene = _make_scene(tree_density=0.03)
    exporter = ForestExporter(tile_size=50)
    walls = exporter._build_walls(scene)

    required_keys = {"_id", "c", "light", "move", "sight", "sound",
                     "dir", "door", "ds", "threshold", "flags"}
    for w in walls:
        assert required_keys.issubset(w.keys()), \
            f"Wall missing keys: {required_keys - w.keys()}"
        assert w["door"] == 0, "Forest walls should never be doors"
        assert len(w["c"]) == 4, "Wall coords must be [x1, y1, x2, y2]"


def test_exporter_scene_json_structure():
    """_build_scene should produce a valid FoundryVTT scene document."""
    scene = _make_scene()
    exporter = ForestExporter(tile_size=50)
    doc = exporter._build_scene(scene, "forest.png", "Test Forest")

    required_keys = {
        "_id", "name", "img", "width", "height",
        "walls", "tokens", "lights", "grid",
        "tokenVision", "fogExploration", "environment",
    }
    assert required_keys.issubset(doc.keys())
    assert doc["name"] == "Test Forest"
    assert doc["img"] == "forest.png"
    assert doc["width"] == scene.n_cols * 50
    assert doc["height"] == scene.n_rows * 50
    assert isinstance(doc["walls"], list)
    assert doc["lights"] == []  # forests have no torch lights

    # Outdoor scene: global light should be enabled
    assert doc["environment"]["globalLight"]["enabled"] is True


def test_exporter_scene_darkness_level():
    exporter = ForestExporter(darkness_level=0.5)
    scene = _make_scene()
    doc = exporter._build_scene(scene, "f.png", "Dark Forest")
    assert doc["environment"]["darknessLevel"] == 0.5


def test_exporter_unique_wall_ids():
    """Every wall _id should be unique."""
    scene = _make_scene(tree_density=0.10)
    exporter = ForestExporter(tile_size=50)
    walls = exporter._build_walls(scene)
    ids = [w["_id"] for w in walls]
    assert len(ids) == len(set(ids)), "Duplicate wall _id values found"


def test_exporter_undergrowth_walls_block_movement_only():
    scene = ForestScene(n_rows=6, n_cols=6)
    from donjuan.forest.scene import Undergrowth
    patch_cells = {
        scene.grid.cells[2][2],
        scene.grid.cells[2][3],
    }
    scene.emplace_space(Undergrowth(cells=patch_cells, name="UG0"))

    exporter = ForestExporter(
        tile_size=50,
        add_boundary_walls=False,
        tree_wall_segments=8,
    )
    walls = exporter._build_walls(scene)

    movement_walls = [w for w in walls if w["move"] == 20 and w["sight"] == 0]
    assert movement_walls, "Expected movement-only walls around undergrowth"
    for wall in movement_walls:
        assert wall["light"] == 0
        assert wall["sound"] == 0
        assert wall["door"] == 0


# ── Integration: full export to disk ─────────────────────────────────────────


@pytest.mark.slow
def test_exporter_writes_files(tmp_path):
    scene = _make_scene()
    exporter = ForestExporter(tile_size=24)
    img_path, json_path = exporter.export(scene, str(tmp_path), "Test Export")

    assert os.path.exists(img_path), "Image file was not written"
    assert os.path.exists(json_path), "JSON file was not written"

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["name"] == "Test Export"
    assert doc["img"].endswith(".png")
    assert len(doc["walls"]) > 0


@pytest.mark.slow
def test_exporter_filename_slug(tmp_path):
    """Scene name should be slugified into the filename."""
    scene = _make_scene()
    exporter = ForestExporter(tile_size=24)
    img_path, json_path = exporter.export(
        scene, str(tmp_path), "My Cool Forest!!"
    )
    assert os.path.basename(img_path) == "my_cool_forest.png"
    assert os.path.basename(json_path) == "my_cool_forest.json"


@pytest.mark.slow
def test_exporter_json_is_valid_foundry(tmp_path):
    """The JSON should be importable — check all top-level required keys."""
    scene = _make_scene()
    exporter = ForestExporter(tile_size=24)
    _, json_path = exporter.export(scene, str(tmp_path), "Valid Forest")

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    for key in ("_id", "name", "img", "width", "height", "grid",
                "walls", "tokens", "lights", "notes", "sounds",
                "tiles", "drawings", "flags", "environment"):
        assert key in doc, f"Missing required FoundryVTT field: {key}"

    assert doc["grid"]["type"] == 1        # SQUARE
    assert doc["grid"]["size"] == 24
    assert doc["tokenVision"] is True
