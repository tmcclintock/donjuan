"""Focused tests for the textured dungeon renderer."""
import os
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from donjuan import Dungeon
from donjuan.core.grid import HexGrid
from donjuan.core.hallway import Hallway
from donjuan.core.room import Room
from donjuan.dungeon.renderer import TexturedRenderer


def _open_room(scene, name, cells, theme="default"):
    room_cells = {scene.grid.cells[y][x] for y, x in cells}
    for cell in room_cells:
        cell.filled = False
    room = Room(cells=room_cells, name=name, theme=theme)
    scene.add_room(room)
    scene.emplace_space(room)
    return room


def _open_hallway(scene, name, cells, theme="default"):
    hallway_cells = [scene.grid.cells[y][x] for y, x in cells]
    for cell in hallway_cells:
        cell.filled = False
    hallway = Hallway(ordered_cells=hallway_cells, name=name, theme=theme)
    scene.add_hallway(hallway)
    scene.emplace_space(hallway)
    return hallway


def _edge_between(cell, target_coords):
    for edge in cell.edges:
        if edge is None:
            continue
        endpoints = {
            None if edge.cell1 is None else edge.cell1.coordinates,
            None if edge.cell2 is None else edge.cell2.coordinates,
        }
        if cell.coordinates in endpoints and target_coords in endpoints:
            return edge
    raise AssertionError(f"No edge found between {cell.coordinates} and {target_coords}")


def test_init_rejects_unknown_pack():
    with pytest.raises(ValueError, match="Unknown texture pack"):
        TexturedRenderer(pack="lava")


def test_render_rejects_non_square_grid():
    dungeon = Dungeon(grid=HexGrid(4, 4))
    renderer = TexturedRenderer()

    with pytest.raises(AssertionError, match="only supports SquareGrid"):
        renderer.render(dungeon, save=False)


def test_render_saves_image_and_tracks_last_image(tmp_path):
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0), (0, 1), (1, 0), (1, 1)})
    renderer = TexturedRenderer(tile_size=8, pillars=False, moss_and_cracks=False)

    file_path = tmp_path / "textured.png"
    fig, ax = renderer.render(dungeon, file_path=str(file_path), save=True)

    assert file_path.exists()
    assert renderer._last_image is not None
    assert renderer._last_image.size == (16, 16)
    assert fig is not None
    assert ax is not None


def test_build_image_calls_optional_stages_when_enabled():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0)})
    renderer = TexturedRenderer(
        tile_size=8,
        pillars=True,
        moss_and_cracks=True,
        wall_shadows=True,
        torchlight=True,
        wall_lines=True,
    )

    with patch.object(renderer, "_draw_pillars") as pillars, patch.object(
        renderer, "_apply_moss_and_cracks"
    ) as moss, patch.object(renderer, "_apply_wall_shadows", side_effect=lambda arr, *_: arr) as shadows, patch.object(
        renderer, "_apply_torchlight", side_effect=lambda arr, *_: arr
    ) as torchlight, patch.object(renderer, "_draw_doors") as doors, patch.object(
        renderer, "_draw_wall_lines"
    ) as wall_lines, patch.object(renderer, "_vignette", side_effect=lambda img: img) as vignette:
        img = renderer._build_image(dungeon)

    assert isinstance(img, Image.Image)
    pillars.assert_called_once()
    moss.assert_called_once()
    shadows.assert_called_once()
    torchlight.assert_called_once()
    doors.assert_called_once()
    wall_lines.assert_called_once()
    vignette.assert_called_once()


def test_build_image_skips_optional_stages_when_disabled():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0)})
    renderer = TexturedRenderer(
        tile_size=8,
        pillars=False,
        moss_and_cracks=False,
        wall_shadows=False,
        torchlight=False,
        wall_lines=False,
    )

    with patch.object(renderer, "_draw_pillars") as pillars, patch.object(
        renderer, "_apply_moss_and_cracks"
    ) as moss, patch.object(renderer, "_apply_wall_shadows") as shadows, patch.object(
        renderer, "_apply_torchlight"
    ) as torchlight, patch.object(renderer, "_draw_wall_lines") as wall_lines:
        img = renderer._build_image(dungeon)

    assert isinstance(img, Image.Image)
    pillars.assert_not_called()
    moss.assert_not_called()
    shadows.assert_not_called()
    torchlight.assert_not_called()
    wall_lines.assert_not_called()


def test_draw_wall_covers_brick_and_plank_modes():
    stone = TexturedRenderer(tile_size=12, pack="stone")
    wood = TexturedRenderer(tile_size=12, pack="wood")

    stone_img = Image.new("RGB", (12, 12), (0, 0, 0))
    wood_img = Image.new("RGB", (12, 12), (0, 0, 0))

    stone._draw_wall(stone_img, 0, 0, seed=1)
    wood._draw_wall(wood_img, 0, 0, seed=1)

    assert np.any(np.array(stone_img) != np.array([0, 0, 0], dtype=np.uint8))
    assert np.any(np.array(wood_img) != np.array([0, 0, 0], dtype=np.uint8))
    assert not np.array_equal(np.array(stone_img), np.array(wood_img))


def test_draw_floor_supports_room_hallway_and_theme_override():
    renderer = TexturedRenderer(tile_size=12)
    room_img = Image.new("RGB", (12, 12), (0, 0, 0))
    hall_img = Image.new("RGB", (12, 12), (0, 0, 0))
    override_img = Image.new("RGB", (12, 12), (0, 0, 0))

    renderer._draw_floor(room_img, 0, 0, seed=1, room=True)
    renderer._draw_floor(hall_img, 0, 0, seed=1, room=False)
    renderer._draw_floor(override_img, 0, 0, seed=1, room=True, floor_override=(255, 0, 0))

    assert not np.array_equal(np.array(room_img), np.array(hall_img))
    assert not np.array_equal(np.array(room_img), np.array(override_img))


def test_draw_pillars_adds_central_feature_for_four_room_block():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0), (0, 1), (1, 0), (1, 1)})
    renderer = TexturedRenderer(tile_size=20)
    img = Image.new("RGB", (40, 40), renderer._c["floor_room"])

    with patch("donjuan.dungeon.renderer._random.Random.random", return_value=0.0):
        renderer._draw_pillars(img, dungeon)

    arr = np.array(img)
    assert tuple(arr[20, 20]) != renderer._c["floor_room"]


def test_apply_moss_and_cracks_mutates_image_near_walls():
    dungeon = Dungeon(n_rows=3, n_cols=3)
    _open_room(dungeon, "R0", {(1, 1)})
    renderer = TexturedRenderer(tile_size=12)
    img = renderer._build_image(dungeon)
    before = np.array(img)
    filled = np.array(
        [[dungeon.grid.cells[r][c].filled for c in range(dungeon.n_cols)] for r in range(dungeon.n_rows)],
        dtype=bool,
    )

    with patch("donjuan.dungeon.renderer._random.Random.random", return_value=0.0):
        renderer._apply_moss_and_cracks(img, dungeon, filled)

    after = np.array(img)
    assert not np.array_equal(before, after)


def test_apply_wall_shadows_darkens_floor_adjacent_to_walls():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0)})
    renderer = TexturedRenderer(tile_size=12)
    arr = np.full((24, 24, 3), 200.0, dtype=np.float32)
    filled = np.array(
        [[dungeon.grid.cells[r][c].filled for c in range(dungeon.n_cols)] for r in range(dungeon.n_rows)],
        dtype=bool,
    )

    shaded = renderer._apply_wall_shadows(arr.copy(), dungeon, filled)

    assert shaded[6, 11, 0] < 200.0
    assert shaded[6, 6, 0] == pytest.approx(200.0)


def test_apply_torchlight_no_doors_is_noop():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0), (0, 1)})
    renderer = TexturedRenderer(tile_size=12)
    arr = np.full((24, 24, 3), 50.0, dtype=np.float32)
    filled = np.array(
        [[dungeon.grid.cells[r][c].filled for c in range(dungeon.n_cols)] for r in range(dungeon.n_rows)],
        dtype=bool,
    )

    lit = renderer._apply_torchlight(arr.copy(), dungeon, filled)

    assert np.array_equal(lit, arr)


def test_apply_torchlight_brightens_floor_at_door_midpoint():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "left", {(0, 0)})
    _open_room(dungeon, "right", {(0, 1)})
    edge = _edge_between(dungeon.grid.cells[0][0], (0, 1))
    edge.has_door = True

    renderer = TexturedRenderer(tile_size=12)
    arr = np.full((24, 24, 3), 50.0, dtype=np.float32)
    filled = np.array(
        [[dungeon.grid.cells[r][c].filled for c in range(dungeon.n_cols)] for r in range(dungeon.n_rows)],
        dtype=bool,
    )

    lit = renderer._apply_torchlight(arr.copy(), dungeon, filled)

    assert lit[6, 18, 0] > 50.0
    assert lit[18, 18, 0] == pytest.approx(50.0)


def test_draw_doors_draws_horizontal_and_vertical_doors():
    horizontal = Dungeon(n_rows=2, n_cols=2)
    _open_room(horizontal, "left", {(0, 0)})
    _open_room(horizontal, "right", {(0, 1)})
    _edge_between(horizontal.grid.cells[0][0], (0, 1)).has_door = True

    vertical = Dungeon(n_rows=2, n_cols=2)
    _open_room(vertical, "top", {(0, 0)})
    _open_room(vertical, "bottom", {(1, 0)})
    _edge_between(vertical.grid.cells[0][0], (1, 0)).has_door = True

    renderer = TexturedRenderer(tile_size=12)
    h_img = Image.new("RGB", (24, 24), (0, 0, 0))
    v_img = Image.new("RGB", (24, 24), (0, 0, 0))

    renderer._draw_doors(h_img, horizontal)
    renderer._draw_doors(v_img, vertical)

    assert tuple(np.array(h_img)[6, 12]) != (0, 0, 0)
    assert tuple(np.array(v_img)[12, 6]) != (0, 0, 0)


def test_draw_wall_lines_marks_floor_edges_against_walls_and_boundary():
    dungeon = Dungeon(n_rows=2, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0)})
    renderer = TexturedRenderer(tile_size=12)
    img = Image.new("RGB", (24, 24), (255, 255, 255))

    renderer._draw_wall_lines(img, dungeon)

    arr = np.array(img)
    assert tuple(arr[0, 6]) == renderer._c["wall_line"]
    assert tuple(arr[6, 0]) == renderer._c["wall_line"]
    assert tuple(arr[11, 6]) == renderer._c["wall_line"]
    assert tuple(arr[6, 11]) == renderer._c["wall_line"]


def test_build_image_uses_room_and_hallway_themes():
    dungeon = Dungeon(n_rows=1, n_cols=2)
    _open_room(dungeon, "R0", {(0, 0)}, theme="treasury")
    _open_hallway(dungeon, "H0", {(0, 1)}, theme="crypt")
    renderer = TexturedRenderer(tile_size=16, pillars=False, moss_and_cracks=False, wall_shadows=False, torchlight=False, wall_lines=False)

    img = renderer._build_image(dungeon)
    arr = np.array(img)

    assert not np.array_equal(arr[:, :16], arr[:, 16:])


def test_vignette_darkens_corners_more_than_center():
    img = Image.new("RGB", (20, 20), (100, 100, 100))

    vignetted = TexturedRenderer._vignette(img)
    arr = np.array(vignetted)

    assert arr[0, 0, 0] < arr[10, 10, 0]
