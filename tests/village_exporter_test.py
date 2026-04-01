"""Tests for VillageExporter — FoundryVTT export of VillageScene."""
import json
import math
import os

import pytest

from donjuan import VillageExporter, VillageRandomizer, VillageScene
from donjuan.core.randomizer import Randomizer


def _make_scene(seed=42):
    Randomizer.seed(seed)
    scene = VillageScene(n_rows=24, n_cols=24)
    VillageRandomizer(
        n_buildings=8,
        min_building_size=2,
        max_building_size=4,
        tree_density=0.06,
        road_branchiness=0.2,
    ).randomize(scene)
    return scene


def test_exporter_builds_boundary_walls():
    scene = _make_scene()
    exporter = VillageExporter(tile_size=50)
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


def test_exporter_builds_building_doors():
    scene = _make_scene()
    exporter = VillageExporter(tile_size=50)
    walls = exporter._build_walls(scene)
    assert any(w["door"] == 1 for w in walls)


def test_exporter_builds_tree_circle_walls():
    scene = VillageScene(n_rows=5, n_cols=5)
    scene.grid.cells[2][2].filled = True
    from donjuan.village.scene import VillageTree

    tree = VillageTree(cells={scene.grid.cells[2][2]}, name="T0")
    scene.emplace_space(tree)
    scene.add_tree(tree)

    exporter = VillageExporter(
        tile_size=100,
        tree_wall_segments=10,
        tree_wall_radius_fraction=0.42,
        add_boundary_walls=False,
    )
    walls = exporter._build_walls(scene)
    assert len(walls) == 10

    cx = (2 + 0.5) * 100
    cy = (2 + 0.5) * 100
    for wall in walls:
        x1, y1, x2, y2 = wall["c"]
        for px, py in [(x1, y1), (x2, y2)]:
            dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
            assert abs(dist - 42.0) < 2.0


def test_exporter_default_tree_wall_radius_is_smaller():
    scene = VillageScene(n_rows=5, n_cols=5)
    scene.grid.cells[2][2].filled = True
    from donjuan.village.scene import VillageTree

    tree = VillageTree(cells={scene.grid.cells[2][2]}, name="T0")
    scene.emplace_space(tree)
    scene.add_tree(tree)

    exporter = VillageExporter(tile_size=100, tree_wall_segments=8, add_boundary_walls=False)
    wall = exporter._build_walls(scene)[0]
    cx = 250
    cy = 250
    x1, y1, _, _ = wall["c"]
    dist = math.sqrt((x1 - cx) ** 2 + (y1 - cy) ** 2)
    assert abs(dist - 34.0) < 2.0


def test_exporter_scene_json_structure():
    scene = _make_scene()
    exporter = VillageExporter(tile_size=50)
    doc = exporter._build_scene(scene, "village.png", "Test Village")
    required_keys = {
        "_id", "name", "img", "width", "height", "walls",
        "tokens", "lights", "grid", "tokenVision",
        "fogExploration", "environment",
    }
    assert required_keys.issubset(doc.keys())
    assert doc["name"] == "Test Village"
    assert doc["img"] == "village.png"
    assert doc["lights"] == []


@pytest.mark.slow
def test_exporter_writes_files(tmp_path):
    scene = _make_scene()
    exporter = VillageExporter(tile_size=24)
    img_path, json_path = exporter.export(scene, str(tmp_path), "Test Village")
    assert os.path.exists(img_path)
    assert os.path.exists(json_path)
    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["name"] == "Test Village"
    assert doc["img"].endswith(".png")
    assert len(doc["walls"]) > 0
