"""Tests for Foundry overlay wall coloring."""

from gui.controller import _overlay_style_for_wall


def test_overlay_style_distinguishes_richer_wall_and_door_types():
    normal = {"door": 1, "flags": {"donjuan": {"door_kind": "normal", "wall_kind": "solid"}}}
    locked = {"door": 1, "flags": {"donjuan": {"door_kind": "locked", "wall_kind": "solid"}}}
    secret = {"door": 2, "flags": {"donjuan": {"door_kind": "secret", "wall_kind": "solid"}}}
    movement = {"door": 0, "flags": {"donjuan": {"door_kind": None, "wall_kind": "movement"}}}
    sight = {"door": 0, "flags": {"donjuan": {"door_kind": None, "wall_kind": "sight"}}}
    dense = {"door": 0, "flags": {"donjuan": {"door_kind": None, "wall_kind": "dense"}}}
    solid = {"door": 0, "flags": {"donjuan": {"door_kind": None, "wall_kind": "solid"}}}

    assert _overlay_style_for_wall(normal)[0] == "#6699ff"
    assert _overlay_style_for_wall(locked)[0] == "#ffb86c"
    assert _overlay_style_for_wall(secret)[0] == "#ff79c6"
    assert _overlay_style_for_wall(movement)[0] == "#4dd0a8"
    assert _overlay_style_for_wall(sight)[0] == "#c792ea"
    assert _overlay_style_for_wall(dense)[0] == "#8fbf5f"
    assert _overlay_style_for_wall(solid)[0] == "#ffffaa"
