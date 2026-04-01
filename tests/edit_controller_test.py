"""Tests for richer dungeon edit-controller door cycling."""
import matplotlib.pyplot as plt

from donjuan import Dungeon
from donjuan.core.room import Room
from donjuan.dungeon.renderer import TexturedRenderer
from gui.edit_controller import EditController


class _DummyCanvas:
    def __init__(self):
        self._fig, self._ax = plt.subplots(1)

    def get_axes(self):
        return self._ax

    def refresh(self):
        return None

    def get_canvas(self):
        return None

    def get_toolbar(self):
        return None


class _DummyStatus:
    def __init__(self):
        self.last_message = ""

    def showMessage(self, message):
        self.last_message = message


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
    raise AssertionError


def _make_controller():
    dungeon = Dungeon(n_rows=4, n_cols=4)
    room_cells = {dungeon.grid.cells[1][1], dungeon.grid.cells[1][2]}
    for cell in room_cells:
        cell.filled = False
    room = Room(name="R0", cells=room_cells)
    dungeon.add_room(room)
    dungeon.emplace_space(room)
    status = _DummyStatus()
    rerenders = []
    controller = EditController(
        canvas=_DummyCanvas(),
        dungeon=dungeon,
        renderer=TexturedRenderer(tile_size=10),
        status_bar=status,
        rerender_fn=lambda: rerenders.append("rerender"),
        get_theme_fn=lambda: "default",
    )
    return controller, dungeon, status, rerenders


def test_shift_click_cycles_dungeon_door_types():
    controller, dungeon, status, rerenders = _make_controller()
    edge = _edge_between(dungeon.grid.cells[1][1], (1, 2))

    controller._toggle_door_at(1, 1, 19.0, 15.0)
    assert edge.door_kind == "normal"
    assert "normal door" in status.last_message

    controller._toggle_door_at(1, 1, 19.0, 15.0)
    assert edge.door_kind == "locked"

    controller._toggle_door_at(1, 1, 19.0, 15.0)
    assert edge.door_kind == "secret"

    controller._toggle_door_at(1, 1, 19.0, 15.0)
    assert edge.has_door is False
    assert rerenders == ["rerender", "rerender", "rerender", "rerender"]


def test_painting_cell_clears_richer_door_metadata():
    controller, dungeon, _status, _ = _make_controller()
    edge = _edge_between(dungeon.grid.cells[1][1], (1, 2))
    edge.set_door(kind="secret")
    controller._drag_fill = True

    controller._apply_paint(1, 1, 1.0, 1.0)

    assert edge.has_door is False
    assert edge.door_kind is None
