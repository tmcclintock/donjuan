"""Tests for tool-based village edit mode behavior."""
import matplotlib.pyplot as plt

from donjuan.core.hallway import Hallway
from donjuan.core.room import Room
from donjuan.village.renderer import VillageRenderer
from donjuan.village.scene import VillageScene, VillageTree
from gui.village_edit_controller import VillageEditController


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


def _make_controller(scene=None, tool="building", theme="default"):
    scene = scene or VillageScene(n_rows=6, n_cols=6)
    canvas = _DummyCanvas()
    status = _DummyStatus()
    rerender_calls = []
    controller = VillageEditController(
        canvas=canvas,
        scene=scene,
        renderer=VillageRenderer(tile_size=10),
        status_bar=status,
        rerender_fn=lambda: rerender_calls.append("rerender"),
        get_theme_fn=lambda: theme,
        get_tool_fn=lambda: tool,
    )
    controller._drag_tool = tool
    return controller, scene, status, rerender_calls


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
    raise AssertionError(f"Missing edge between {cell.coordinates} and {target_coords}")


def test_building_tool_creates_room_cells_and_assigns_theme():
    controller, scene, _status, _ = _make_controller(tool="building", theme="treasury")

    controller._apply_tool(2, 2)

    cell = scene.grid.cells[2][2]
    assert isinstance(cell.space, Room)
    assert not cell.filled
    assert cell.space.theme == "treasury"
    assert len(scene.buildings) == 1


def test_road_tool_creates_and_extends_single_hallway():
    controller, scene, _status, _ = _make_controller(tool="road", theme="crypt")

    controller._apply_tool(1, 1)
    controller._apply_tool(1, 2)

    assert len(scene.roads) == 1
    road = next(iter(scene.roads.values()))
    assert isinstance(road, Hallway)
    assert road.theme == "crypt"
    assert scene.grid.cells[1][1].space is road
    assert scene.grid.cells[1][2].space is road


def test_tree_tool_creates_filled_tree_cells():
    controller, scene, _status, _ = _make_controller(tool="tree")

    controller._apply_tool(3, 3)

    cell = scene.grid.cells[3][3]
    assert isinstance(cell.space, VillageTree)
    assert cell.filled is True
    assert len(scene.trees) == 1


def test_erase_tool_removes_space_and_prunes_empty_space():
    controller, scene, _status, _ = _make_controller(tool="building")
    controller._apply_tool(2, 2)
    building = scene.grid.cells[2][2].space

    controller._drag_tool = "erase"
    controller._apply_tool(2, 2)

    cell = scene.grid.cells[2][2]
    assert cell.space is None
    assert cell.filled is False
    assert building.name not in scene.buildings


def test_door_tool_toggles_building_perimeter_edge_and_syncs_entrances():
    controller, scene, _status, rerenders = _make_controller(tool="building")
    controller._apply_tool(2, 2)
    controller._drag_tool = "door"

    controller._toggle_door_at(2, 2, 30, 25)

    edge = _edge_between(scene.grid.cells[2][2], (2, 3))
    assert edge.has_door is True
    assert edge.door_kind == "normal"
    building = scene.grid.cells[2][2].space
    assert building.entrances == [edge]
    assert scene.building_entrances[building.name] == (2, 3)
    assert rerenders == ["rerender"]


def test_door_tool_cycles_normal_locked_secret_and_removed():
    controller, scene, status, _ = _make_controller(tool="building")
    controller._apply_tool(2, 2)
    controller._drag_tool = "door"

    edge = _edge_between(scene.grid.cells[2][2], (2, 3))

    controller._toggle_door_at(2, 2, 30, 25)
    assert edge.door_kind == "normal"
    assert "normal door" in status.last_message

    controller._toggle_door_at(2, 2, 30, 25)
    assert edge.door_kind == "locked"
    assert "locked door" in status.last_message

    controller._toggle_door_at(2, 2, 30, 25)
    assert edge.door_kind == "secret"
    assert "secret door" in status.last_message

    controller._toggle_door_at(2, 2, 30, 25)
    assert edge.has_door is False
    assert "door removed" in status.last_message


def test_door_tool_ignores_non_building_edges():
    controller, scene, status, rerenders = _make_controller(tool="door")

    controller._toggle_door_at(1, 1, 15, 10)

    assert "building perimeter edge" in status.last_message
    assert rerenders == []


def test_erasing_building_cell_clears_stale_door_flags():
    controller, scene, _status, _ = _make_controller(tool="building")
    controller._apply_tool(2, 2)
    controller._drag_tool = "door"
    controller._toggle_door_at(2, 2, 30, 25)
    edge = _edge_between(scene.grid.cells[2][2], (2, 3))
    assert edge.has_door is True

    controller._drag_tool = "erase"
    controller._apply_tool(2, 2)

    assert edge.has_door is False
    assert scene.buildings == {}


def test_undo_restores_membership_filled_state_and_doors():
    controller, scene, _status, _ = _make_controller(tool="building")
    controller._push_snapshot()
    controller._apply_tool(2, 2)
    controller._drag_tool = "door"
    controller._toggle_door_at(2, 2, 30, 25)
    edge = _edge_between(scene.grid.cells[2][2], (2, 3))

    assert scene.grid.cells[2][2].space is not None
    assert edge.has_door is True

    controller.undo()

    assert scene.grid.cells[2][2].space is None
    assert scene.grid.cells[2][2].filled is False
    assert edge.has_door is False
    assert scene.buildings == {}
