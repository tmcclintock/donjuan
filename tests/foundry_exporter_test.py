"""Tests for the shared Foundry exporter base class."""
import json
import os

import pytest

from donjuan.core.cell import SquareCell
from donjuan.core.exporter import (
    FoundryExporter,
    _boundary_coords,
    _dense_wall,
    _door_wall,
    _edge_wall,
    _locked_door_wall,
    _movement_wall,
    _shared_edge_coords,
    _sight_wall,
    _slugify,
    _solid_wall,
    _secret_door_wall,
)
from donjuan.core.edge import DOOR_KIND_LOCKED, DOOR_KIND_SECRET, Edge, WALL_KIND_DENSE, WALL_KIND_MOVEMENT, WALL_KIND_SIGHT
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
    locked = _locked_door_wall([0, 0, 10, 0])
    secret = _secret_door_wall([0, 0, 10, 0])
    sight = _sight_wall([0, 0, 10, 0])
    dense = _dense_wall([0, 0, 10, 0])

    assert solid["move"] == 20
    assert solid["sight"] == 20
    assert solid["door"] == 0
    assert solid["flags"]["donjuan"]["wall_kind"] == "solid"

    assert door["move"] == 20
    assert door["sight"] == 20
    assert door["door"] == 1
    assert door["flags"]["donjuan"]["door_kind"] == "normal"

    assert movement["move"] == 20
    assert movement["sight"] == 0
    assert movement["light"] == 0
    assert movement["sound"] == 0
    assert movement["flags"]["donjuan"]["wall_kind"] == WALL_KIND_MOVEMENT

    assert locked["door"] == 1
    assert locked["ds"] == 2
    assert locked["flags"]["donjuan"]["door_kind"] == DOOR_KIND_LOCKED

    assert secret["door"] == 2
    assert secret["ds"] == 0
    assert secret["flags"]["donjuan"]["door_kind"] == DOOR_KIND_SECRET

    assert sight["move"] == 0
    assert sight["sight"] == 20
    assert sight["flags"]["donjuan"]["wall_kind"] == WALL_KIND_SIGHT

    assert dense["move"] == 20
    assert dense["sight"] == 20
    assert dense["sound"] == 0
    assert dense["flags"]["donjuan"]["wall_kind"] == WALL_KIND_DENSE


def test_edge_wall_uses_edge_metadata():
    edge = Edge()
    edge.set_door(kind=DOOR_KIND_SECRET)
    wall = _edge_wall([0, 0, 10, 0], edge)
    assert wall["door"] == 2
    assert wall["flags"]["donjuan"]["door_kind"] == DOOR_KIND_SECRET

    edge.clear_door()
    edge.wall_kind = WALL_KIND_DENSE
    wall = _edge_wall([0, 0, 10, 0], edge)
    assert wall["door"] == 0
    assert wall["flags"]["donjuan"]["wall_kind"] == WALL_KIND_DENSE
