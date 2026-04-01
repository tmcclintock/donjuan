"""Tests for DungeonExporter Foundry export behavior."""
from unittest.mock import patch

import pytest

from donjuan import Dungeon
from donjuan.core.hallway import Hallway
from donjuan.core.room import Room
from donjuan.dungeon.exporter import DungeonExporter, _edge_is_interior


def _open_room(scene, name, cells):
    room_cells = {scene.grid.cells[y][x] for y, x in cells}
    for cell in room_cells:
        cell.filled = False
    room = Room(cells=room_cells, name=name)
    scene.add_room(room)
    scene.emplace_space(room)
    return room


def _open_hallway(scene, name, cells):
    hallway_cells = [scene.grid.cells[y][x] for y, x in cells]
    for cell in hallway_cells:
        cell.filled = False
    hallway = Hallway(ordered_cells=hallway_cells, name=name)
    scene.add_hallway(hallway)
    scene.emplace_space(hallway)
    return hallway


def test_init_rejects_unknown_texture_pack():
    with pytest.raises(ValueError, match="Unknown texture pack"):
        DungeonExporter(pack="lava")


def test_render_image_uses_textured_renderer_and_closes_figure():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    exporter = DungeonExporter(tile_size=64, pack="wood", add_lights=False)
    fake_fig = object()
    fake_renderer = type(
        "FakeRenderer",
        (),
        {
            "__init__": lambda self, **kwargs: setattr(self, "kwargs", kwargs),
            "render": lambda self, scene, file_path, save: (fake_fig, None),
        },
    )()

    with patch("donjuan.dungeon.exporter.TexturedRenderer", return_value=fake_renderer) as renderer_cls, patch(
        "matplotlib.pyplot.close"
    ) as close:
        exporter._render_image(dungeon, "dummy.png")

    renderer_cls.assert_called_once_with(
        tile_size=64,
        pack="wood",
        wall_shadows=True,
        torchlight=True,
        moss_and_cracks=True,
        pillars=True,
        wall_lines=True,
    )
    close.assert_called_once_with(fake_fig)


def test_build_walls_handles_boundary_filled_and_door_cases():
    dungeon = Dungeon(n_rows=3, n_cols=3)
    exporter = DungeonExporter(tile_size=10)

    left_room = _open_room(dungeon, "left", {(1, 0)})
    right_room = _open_room(dungeon, "right", {(1, 1)})
    dungeon.grid.cells[1][0].edges[3].has_door = True

    walls = exporter._build_walls(dungeon)
    coords = [tuple(w["c"]) for w in walls]

    assert (0, 10, 0, 20) in coords
    assert any(w["door"] == 1 and tuple(w["c"]) == (10, 10, 10, 20) for w in walls)
    assert any(w["door"] == 0 and tuple(w["c"]) == (20, 10, 20, 20) for w in walls)
    assert left_room is not right_room


def test_build_walls_skips_same_space_hallway_pairs_and_interior_edges():
    dungeon = Dungeon(n_rows=4, n_cols=4)
    exporter = DungeonExporter(tile_size=10)

    _open_room(dungeon, "big", {(1, 1), (1, 2), (2, 1), (2, 2)})
    _open_hallway(dungeon, "h1", {(2, 1)})
    _open_hallway(dungeon, "h2", {(2, 2)})

    walls = exporter._build_walls(dungeon)
    coords = {tuple(w["c"]) for w in walls}

    assert (20, 10, 20, 20) not in coords
    assert (20, 20, 20, 30) not in coords
    assert _edge_is_interior(dungeon.grid.cells[1][1], dungeon.grid.cells[1][2], dungeon) is True


def test_build_lights_ignores_invalid_doors_and_deduplicates_edges():
    dungeon = Dungeon(n_rows=3, n_cols=3)
    exporter = DungeonExporter(tile_size=10, add_lights=True)

    _open_room(dungeon, "left", {(1, 0)})
    _open_room(dungeon, "right", {(1, 1)})
    door_edge = dungeon.grid.cells[1][0].edges[3]
    door_edge.has_door = True

    boundary_edge = dungeon.grid.cells[1][0].edges[1]
    boundary_edge.has_door = True

    lights = exporter._build_lights(dungeon)

    assert len(lights) == 1
    assert lights[0]["x"] == 10.0
    assert lights[0]["y"] == 15.0


def test_build_lights_can_be_disabled():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    exporter = DungeonExporter(add_lights=False)

    assert exporter._build_lights(dungeon) == []


def test_edge_is_interior_detects_vertical_and_non_interior_cases():
    dungeon = Dungeon(n_rows=4, n_cols=4)

    for y, x in {(1, 1), (1, 2), (2, 1), (2, 2)}:
        dungeon.grid.cells[y][x].filled = False

    top = dungeon.grid.cells[1][1]
    bottom = dungeon.grid.cells[2][1]
    assert _edge_is_interior(top, bottom, dungeon) is True

    other = Dungeon(n_rows=3, n_cols=3)
    other.grid.cells[1][1].filled = False
    other.grid.cells[1][2].filled = False
    assert _edge_is_interior(other.grid.cells[1][1], other.grid.cells[1][2], other) is False
