"""Tests for CampExporter — FoundryVTT export of CampScene."""
import json
import math
import os

import pytest

from donjuan.camp.scene import CampRandomizer, CampScene
from donjuan.camp.exporter import CampExporter
from donjuan.core.randomizer import Randomizer


def _make_scene(
    n_rows=20,
    n_cols=20,
    seed=42,
    n_fires=2,
    n_tents=6,
    perimeter_tree_density=0.08,
):
    Randomizer.seed(seed)
    scene = CampScene(n_rows=n_rows, n_cols=n_cols)
    CampRandomizer(
        n_fires=n_fires,
        n_tents=n_tents,
        perimeter_tree_density=perimeter_tree_density,
    ).randomize(scene)
    return scene


def test_exporter_builds_boundary_walls():
    scene = _make_scene()
    exporter = CampExporter(tile_size=50, tree_wall_segments=8)
    walls = exporter._build_walls(scene)

    t = exporter.tile_size
    width = scene.n_cols * t
    height = scene.n_rows * t
    boundary_coords = {
        (0, 0, width, 0),
        (width, 0, width, height),
        (width, height, 0, height),
        (0, height, 0, 0),
    }

    found = {tuple(w["c"]) for w in walls if tuple(w["c"]) in boundary_coords}
    assert found == boundary_coords


def test_exporter_tree_walls_count():
    scene = _make_scene(perimeter_tree_density=0.05)
    n_segs = 8
    exporter = CampExporter(
        tile_size=50,
        tree_wall_segments=n_segs,
        add_boundary_walls=False,
        add_tent_walls=False,
    )
    walls = exporter._build_walls(scene)

    assert len(walls) == len(scene.trees) * n_segs


def test_exporter_tree_walls_form_circle():
    scene = CampScene(n_rows=5, n_cols=5)
    scene.grid.cells[2][2].filled = True

    tile_size = 100
    radius_frac = 0.42
    n_segs = 10
    exporter = CampExporter(
        tile_size=tile_size,
        tree_wall_segments=n_segs,
        tree_wall_radius_fraction=radius_frac,
        add_boundary_walls=False,
        add_tent_walls=False,
    )

    walls = exporter._build_walls(scene)
    assert len(walls) == n_segs

    cx = (2 + 0.5) * tile_size
    cy = (2 + 0.5) * tile_size
    expected_radius = tile_size * radius_frac

    for wall in walls:
        x1, y1, x2, y2 = wall["c"]
        for px, py in [(x1, y1), (x2, y2)]:
            dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
            assert abs(dist - expected_radius) < 2.0
        assert wall["flags"]["donjuan"]["wall_kind"] == "dense"


def test_exporter_builds_fire_lights():
    scene = _make_scene(n_fires=3, perimeter_tree_density=0.0)
    exporter = CampExporter(tile_size=50)
    lights = exporter._build_lights(scene)

    assert len(lights) == len(scene.fires)
    for light in lights:
        assert light["config"]["animation"]["type"] == "torch"


def test_exporter_can_disable_fire_lights():
    scene = _make_scene(n_fires=2)
    exporter = CampExporter(add_fire_lights=False)
    assert exporter._build_lights(scene) == []


def test_exporter_tent_walls_block_movement_only():
    scene = CampScene(n_rows=6, n_cols=6)
    from donjuan.camp.scene import Tent
    tent_cells = {
        scene.grid.cells[2][2],
        scene.grid.cells[2][3],
    }
    scene.emplace_space(Tent(cells=tent_cells, name="T0"))

    exporter = CampExporter(
        tile_size=50,
        add_boundary_walls=False,
        add_tent_walls=True,
    )
    walls = exporter._build_walls(scene)

    movement_walls = [w for w in walls if w["move"] == 20 and w["sight"] == 0]
    assert movement_walls, "Expected movement-only walls around tents"
    for wall in movement_walls:
        assert wall["light"] == 0
        assert wall["sound"] == 0
        assert wall["door"] == 0
        assert wall["flags"]["donjuan"]["wall_kind"] == "movement"


def test_exporter_scene_json_structure():
    scene = _make_scene()
    exporter = CampExporter(tile_size=50)
    doc = exporter._build_scene(scene, "camp.png", "Test Camp")

    required_keys = {
        "_id", "name", "img", "width", "height",
        "walls", "tokens", "lights", "grid",
        "tokenVision", "fogExploration", "environment",
    }
    assert required_keys.issubset(doc.keys())
    assert doc["name"] == "Test Camp"
    assert doc["img"] == "camp.png"
    assert doc["width"] == scene.n_cols * 50
    assert doc["height"] == scene.n_rows * 50
    assert len(doc["lights"]) == len(scene.fires)
    assert doc["environment"]["globalLight"]["enabled"] is True


@pytest.mark.slow
def test_exporter_writes_files(tmp_path):
    scene = _make_scene()
    exporter = CampExporter(tile_size=24)
    img_path, json_path = exporter.export(scene, str(tmp_path), "Test Camp")

    assert os.path.exists(img_path)
    assert os.path.exists(json_path)

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["name"] == "Test Camp"
    assert doc["img"].endswith(".png")
    assert len(doc["walls"]) > 0
    assert len(doc["lights"]) == len(scene.fires)
