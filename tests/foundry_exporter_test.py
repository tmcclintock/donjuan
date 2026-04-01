"""Tests for the shared Foundry exporter base class."""
import json
import os

import pytest

from donjuan.core.cell import SquareCell
from donjuan.core.exporter import (
    FoundryExporter,
    _boundary_coords,
    _door_wall,
    _movement_wall,
    _shared_edge_coords,
    _slugify,
    _solid_wall,
)
from donjuan.dungeon.exporter import DungeonExporter
from donjuan.forest.scene import ForestScene


class DummyExporter(FoundryExporter):
    """Minimal concrete exporter used to test shared base behavior."""

    default_scene_name = "Dummy Scene"
    default_slug = "dummy"
    background_color = "#123456"
    global_light_enabled = True
    global_light_color = "#abcdef"

    def _render_image(self, scene, img_path):
        with open(img_path, "wb") as f:
            f.write(b"dummy")

    def _build_walls(self, scene):
        return [_solid_wall([0, 0, self.tile_size, 0])]

    def _build_lights(self, scene):
        return [{"_id": "light1", "x": 10, "y": 20}]


def test_dungeon_exporter_is_foundry_exporter():
    exporter = DungeonExporter()
    assert isinstance(exporter, FoundryExporter)


def test_base_build_scene_uses_shared_foundry_fields():
    scene = ForestScene(n_rows=3, n_cols=4)
    exporter = DummyExporter(tile_size=50, grid_distance=10, darkness_level=0.4)

    doc = exporter._build_scene(scene, "dummy.png", "Shared Scene")

    assert doc["name"] == "Shared Scene"
    assert doc["img"] == "dummy.png"
    assert doc["width"] == 200
    assert doc["height"] == 150
    assert doc["backgroundColor"] == "#123456"
    assert doc["grid"]["size"] == 50
    assert doc["grid"]["distance"] == 10
    assert doc["environment"]["darknessLevel"] == 0.4
    assert doc["environment"]["globalLight"]["enabled"] is True
    assert doc["environment"]["globalLight"]["color"] == "#abcdef"
    assert len(doc["walls"]) == 1
    assert doc["lights"] == [{"_id": "light1", "x": 10, "y": 20}]


def test_base_export_uses_default_name_and_slug_fallback(tmp_path):
    scene = ForestScene(n_rows=2, n_cols=2)
    exporter = DummyExporter()

    img_path, json_path = exporter.export(scene, str(tmp_path), scene_name="!!!")

    assert os.path.basename(img_path) == "dummy.png"
    assert os.path.basename(json_path) == "dummy.json"

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["name"] == "!!!"


def test_base_export_uses_subclass_default_scene_name(tmp_path):
    scene = ForestScene(n_rows=2, n_cols=2)
    exporter = DummyExporter()

    _, json_path = exporter.export(scene, str(tmp_path))

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["name"] == "Dummy Scene"


def test_base_abstract_methods_raise_not_implemented():
    exporter = FoundryExporter()
    scene = ForestScene(n_rows=2, n_cols=2)

    with pytest.raises(NotImplementedError):
        exporter._render_image(scene, "dummy.png")

    with pytest.raises(NotImplementedError):
        exporter._build_walls(scene)

    assert exporter._build_lights(scene) == []


def test_slugify_uses_fallback_for_empty_slug():
    assert _slugify("!!!", "fallback") == "fallback"


def test_boundary_coords_cover_all_edge_indices():
    cell = SquareCell(coordinates=(3, 4))

    assert _boundary_coords(cell, 0, 10) == [40, 30, 50, 30]
    assert _boundary_coords(cell, 1, 10) == [40, 30, 40, 40]
    assert _boundary_coords(cell, 2, 10) == [40, 40, 50, 40]
    assert _boundary_coords(cell, 3, 10) == [50, 30, 50, 40]


def test_shared_edge_coords_handles_horizontal_vertical_and_diagonal():
    left = SquareCell(coordinates=(2, 1))
    right = SquareCell(coordinates=(2, 2))
    top = SquareCell(coordinates=(1, 3))
    bottom = SquareCell(coordinates=(2, 3))
    diagonal = SquareCell(coordinates=(4, 4))

    assert _shared_edge_coords(left, right, 10) == [20, 20, 20, 30]
    assert _shared_edge_coords(top, bottom, 10) == [30, 20, 40, 20]
    assert _shared_edge_coords(left, diagonal, 10) is None


def test_wall_helper_types_have_expected_foundry_flags():
    solid = _solid_wall([0, 0, 10, 0])
    door = _door_wall([0, 0, 10, 0])
    movement = _movement_wall([0, 0, 10, 0])

    assert solid["move"] == 20
    assert solid["sight"] == 20
    assert solid["door"] == 0

    assert door["move"] == 20
    assert door["sight"] == 20
    assert door["door"] == 1

    assert movement["move"] == 20
    assert movement["sight"] == 0
    assert movement["light"] == 0
    assert movement["sound"] == 0
