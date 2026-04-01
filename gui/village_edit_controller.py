"""
Village edit mode controller: handles tool-based mouse editing on the canvas.
"""
import matplotlib.patches as mpatches
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from donjuan.core.hallway import Hallway
from donjuan.core.room import Room
from donjuan.village.scene import VillageTree
from donjuan.village.renderer import VillageRenderer

_UNDO_MAX_DEPTH = 20


class VillageEditController:
    """Manages tool-based edit mode for village scenes."""

    def __init__(
        self,
        canvas,
        scene,
        renderer,
        status_bar,
        rerender_fn,
        get_theme_fn=None,
        get_tool_fn=None,
    ):
        self._canvas = canvas
        self._scene = scene
        self._renderer = renderer
        self._status = status_bar
        self._rerender = rerender_fn
        self._get_theme = get_theme_fn or (lambda: "default")
        self._get_tool = get_tool_fn or (lambda: "building")

        self._cid_press = None
        self._cid_motion = None
        self._cid_release = None
        self._active = False

        self._dragging = False
        self._drag_tool = None
        self._last_drag_cell = None
        self._preview_artists = []
        self._hover_artist = None
        self._undo_stack = []
        self._target_space = None

    def activate(self) -> None:
        if self._active:
            return

        toolbar = self._canvas.get_toolbar()
        if toolbar is not None and toolbar.mode != "":
            mode = toolbar.mode.lower()
            if "pan" in mode:
                toolbar.pan()
            elif "zoom" in mode:
                toolbar.zoom()

        fig_canvas = self._canvas.get_canvas()
        if fig_canvas is None:
            return

        self._cid_press = fig_canvas.mpl_connect("button_press_event", self._on_press)
        self._cid_motion = fig_canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._cid_release = fig_canvas.mpl_connect("button_release_event", self._on_release)
        fig_canvas.setCursor(QCursor(Qt.CrossCursor))
        self._active = True

    def deactivate(self) -> None:
        if not self._active:
            return

        fig_canvas = self._canvas.get_canvas()
        if fig_canvas is not None:
            for cid in (self._cid_press, self._cid_motion, self._cid_release):
                if cid is not None:
                    fig_canvas.mpl_disconnect(cid)
            fig_canvas.setCursor(QCursor(Qt.ArrowCursor))

        self._cid_press = self._cid_motion = self._cid_release = None
        self._clear_hover()
        self._clear_previews()
        self._dragging = False
        self._drag_tool = None
        self._target_space = None
        self._active = False

    def undo(self) -> bool:
        if not self._undo_stack:
            self._status.showMessage("Village edit mode  ·  nothing to undo")
            return False
        self._restore_snapshot(self._undo_stack.pop())
        self._rerender()
        remaining = len(self._undo_stack)
        self._status.showMessage(
            f"Village edit mode  ·  undo  ·  {remaining} step{'s' if remaining != 1 else ''} remaining"
        )
        return True

    def _on_press(self, event) -> None:
        if event.button != 1 or event.xdata is None or event.ydata is None:
            return
        cell = self._data_to_cell(event.xdata, event.ydata)
        if cell is None:
            return

        row, col = cell
        self._push_snapshot()
        self._drag_tool = self._get_tool().lower()
        self._target_space = None

        if self._drag_tool == "door":
            self._toggle_door_at(row, col, event.xdata, event.ydata)
            return

        self._dragging = True
        self._last_drag_cell = (row, col)
        self._apply_tool(row, col)

    def _on_motion(self, event) -> None:
        tool = self._get_tool().lower()
        fig_canvas = self._canvas.get_canvas()
        if fig_canvas is not None:
            cursor = Qt.PointingHandCursor if tool == "door" else Qt.CrossCursor
            fig_canvas.setCursor(QCursor(cursor))

        if tool == "door" and event.xdata is not None and event.ydata is not None:
            cell = self._data_to_cell(event.xdata, event.ydata)
            if cell is not None:
                self._update_hover(cell[0], cell[1], event.xdata, event.ydata)
            else:
                self._clear_hover()
        else:
            self._clear_hover()

        if not self._dragging or event.xdata is None or event.ydata is None:
            return

        cell = self._data_to_cell(event.xdata, event.ydata)
        if cell is None or cell == self._last_drag_cell:
            return

        row, col = cell
        self._last_drag_cell = (row, col)
        self._apply_tool(row, col)

    def _on_release(self, _event) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self._drag_tool = None
        self._last_drag_cell = None
        self._target_space = None
        if self._preview_artists:
            self._clear_previews()
        self._rerender()

    def _apply_tool(self, row: int, col: int) -> None:
        tool = self._drag_tool or self._get_tool().lower()
        if tool == "building":
            self._paint_building(row, col)
        elif tool == "road":
            self._paint_road(row, col)
        elif tool == "tree":
            self._paint_tree(row, col)
        elif tool == "erase":
            self._erase(row, col)

    def _paint_building(self, row: int, col: int) -> None:
        cell = self._scene.grid.cells[row][col]
        if isinstance(cell.space, Room):
            if self._target_space is not None and cell.space is not self._target_space:
                return
            cell.space.theme = self._get_theme()
            self._target_space = self._target_space or cell.space
            self._status.showMessage(
                f"Village edit mode  ·  building '{cell.space.name}' theme → {cell.space.theme}"
            )
            self._show_preview(row, col, "#d9c29a")
            return
        if isinstance(cell.space, Hallway):
            self._remove_cell_from_space(cell, cell.space)
        elif isinstance(cell.space, VillageTree):
            self._remove_cell_from_space(cell, cell.space)

        target = self._target_space
        if target is None:
            target = Room(name=self._scene.next_building_name(), theme=self._get_theme())
            self._scene.add_building(target)
            self._target_space = target

        cell.filled = False
        self._scene.clear_doors_for_cell(cell)
        cell.set_space(target)
        self._scene.rebuild_space_membership(target)
        self._status.showMessage(
            f"Village edit mode  ·  building '{target.name}'  ·  release to commit"
        )
        self._show_preview(row, col, "#d9c29a")

    def _paint_road(self, row: int, col: int) -> None:
        cell = self._scene.grid.cells[row][col]
        if isinstance(cell.space, Room):
            return
        if isinstance(cell.space, Hallway):
            if self._target_space is not None and cell.space is not self._target_space:
                return
            cell.space.theme = self._get_theme()
            self._target_space = self._target_space or cell.space
            self._status.showMessage(
                f"Village edit mode  ·  road '{cell.space.name}' theme → {cell.space.theme}"
            )
            self._show_preview(row, col, "#b89864")
            return
        if isinstance(cell.space, VillageTree):
            self._remove_cell_from_space(cell, cell.space)

        target = self._target_space
        if target is None:
            target = Hallway(name=self._scene.next_road_name(), theme=self._get_theme())
            self._scene.add_road(target)
            self._target_space = target

        cell.filled = False
        self._scene.clear_doors_for_cell(cell)
        cell.set_space(target)
        self._scene.rebuild_space_membership(target)
        self._status.showMessage(
            f"Village edit mode  ·  road '{target.name}'  ·  release to commit"
        )
        self._show_preview(row, col, "#b89864")

    def _paint_tree(self, row: int, col: int) -> None:
        cell = self._scene.grid.cells[row][col]
        if isinstance(cell.space, Room):
            return
        if isinstance(cell.space, Hallway):
            self._remove_cell_from_space(cell, cell.space)
        elif isinstance(cell.space, VillageTree):
            self._show_preview(row, col, "#2f6a34")
            return

        self._scene.clear_doors_for_cell(cell)
        cell.filled = True
        tree = VillageTree(cells={cell}, name=self._scene.next_tree_name())
        self._scene.add_tree(tree)
        self._scene.emplace_space(tree)
        self._status.showMessage("Village edit mode  ·  tree added  ·  release to commit")
        self._show_preview(row, col, "#2f6a34")

    def _erase(self, row: int, col: int) -> None:
        cell = self._scene.grid.cells[row][col]
        self._scene.clear_doors_for_cell(cell)
        if cell.space is not None:
            self._remove_cell_from_space(cell, cell.space)
        cell.filled = False
        cell.set_space(None)
        self._status.showMessage("Village edit mode  ·  erased to plain ground")
        self._show_preview(row, col, "#658245")

    def _remove_cell_from_space(self, cell, space) -> None:
        cell.set_space(None)
        cell.filled = False
        self._scene.prune_empty_space(space)

    def _toggle_door_at(self, row: int, col: int, xdata: float, ydata: float) -> None:
        edge = self._nearest_edge(row, col, xdata, ydata)
        if edge is None:
            return

        c1, c2 = edge.cell1, edge.cell2
        if c1 is None or c2 is None:
            return
        building = c1.space if isinstance(c1.space, Room) else c2.space if isinstance(c2.space, Room) else None
        if building is None:
            self._status.showMessage(
                "Village edit mode  ·  select a building perimeter edge for doors"
            )
            return
        if c1.space is building and c2.space is building:
            self._status.showMessage(
                "Village edit mode  ·  can't place a door inside a building"
            )
            return
        if c1.filled or c2.filled:
            self._status.showMessage(
                "Village edit mode  ·  can't place a door against a solid cell"
            )
            return

        next_kind = edge.cycle_door_kind()
        self._scene.rebuild_all_building_entrances()
        if next_kind is None:
            msg = f"Village edit mode  ·  door removed at ({row}, {col})"
        else:
            msg = f"Village edit mode  ·  {next_kind} door set at ({row}, {col})"
        self._status.showMessage(msg)
        self._rerender()

    def _update_hover(self, row: int, col: int, xdata: float, ydata: float) -> None:
        ax = self._canvas.get_axes()
        if ax is None:
            return

        edge_idx = self._nearest_edge_idx(row, col, xdata, ydata)
        coords = self._edge_coords(row, col, edge_idx)
        if coords is None:
            self._clear_hover()
            return

        x1, y1, x2, y2 = coords
        if self._hover_artist is None:
            line, = ax.plot(
                [x1, x2], [y1, y2],
                color="#8bd5ca", linewidth=2.5, alpha=0.85,
                solid_capstyle="round",
                zorder=10,
            )
            self._hover_artist = line
        else:
            self._hover_artist.set_data([x1, x2], [y1, y2])
        self._canvas.refresh()

    def _clear_hover(self) -> None:
        if self._hover_artist is not None:
            self._hover_artist.remove()
            self._hover_artist = None
            self._canvas.refresh()

    def _show_preview(self, row: int, col: int, color: str) -> None:
        ax = self._canvas.get_axes()
        if ax is None:
            return

        t = self._renderer.tile_size if isinstance(self._renderer, VillageRenderer) else 48
        rect = mpatches.Rectangle(
            (col * t, row * t), t, t,
            facecolor=color, alpha=0.65, linewidth=0,
        )
        ax.add_patch(rect)
        self._preview_artists.append(rect)
        self._canvas.refresh()

    def _clear_previews(self) -> None:
        for artist in self._preview_artists:
            artist.remove()
        self._preview_artists = []
        self._canvas.refresh()

    def _push_snapshot(self) -> None:
        self._undo_stack.append(self._take_snapshot())
        if len(self._undo_stack) > _UNDO_MAX_DEPTH:
            self._undo_stack.pop(0)

    def _take_snapshot(self) -> dict:
        cells = {}
        edges = {}
        seen_edges = set()
        spaces = {}
        seen_spaces = set()

        for r in range(self._scene.n_rows):
            for c in range(self._scene.n_cols):
                cell = self._scene.grid.cells[r][c]
                cells[(r, c)] = (cell.filled, cell.space)
                if cell.space is not None and id(cell.space) not in seen_spaces:
                    seen_spaces.add(id(cell.space))
                    spaces[id(cell.space)] = self._space_snapshot(cell.space)
                for edge in cell.edges or []:
                    if edge is not None and id(edge) not in seen_edges:
                        seen_edges.add(id(edge))
                        edges[id(edge)] = (
                            edge,
                            edge.has_door,
                            edge.door_kind,
                            edge.door_state,
                            edge.wall_kind,
                        )

        return {
            "cells": cells,
            "edges": edges,
            "spaces": spaces,
            "buildings": dict(self._scene.buildings),
            "roads": dict(self._scene.roads),
            "trees": dict(self._scene.trees),
            "building_entrances": dict(self._scene.building_entrances),
        }

    def _space_snapshot(self, space):
        snap = {
            "space": space,
            "cells": set(space.cells),
            "entrances": list(getattr(space, "entrances", [])),
            "theme": getattr(space, "theme", None),
        }
        if isinstance(space, Hallway):
            snap["ordered_cells"] = list(space.ordered_cells)
        return snap

    def _restore_snapshot(self, snapshot: dict) -> None:
        self._scene.buildings = dict(snapshot["buildings"])
        self._scene.roads = dict(snapshot["roads"])
        self._scene.trees = dict(snapshot["trees"])
        self._scene.building_entrances = dict(snapshot["building_entrances"])

        for space_snapshot in snapshot["spaces"].values():
            space = space_snapshot["space"]
            space._cells = set(space_snapshot["cells"])
            if isinstance(space, Hallway):
                space._ordered_cells = list(space_snapshot.get("ordered_cells", []))
            if hasattr(space, "entrances"):
                space.entrances = list(space_snapshot["entrances"])
            if space_snapshot["theme"] is not None:
                space.theme = space_snapshot["theme"]
            space.reset_cell_coordinates()

        for (r, c), (filled, space) in snapshot["cells"].items():
            cell = self._scene.grid.cells[r][c]
            cell.filled = filled
            cell.set_space(space)

        for _eid, (edge, has_door, door_kind, door_state, wall_kind) in snapshot["edges"].items():
            edge.wall_kind = wall_kind
            if has_door:
                edge.set_door(kind=door_kind, state=door_state)
            else:
                edge.clear_door()

    def _nearest_edge(self, row: int, col: int, xdata: float, ydata: float):
        edge_idx = self._nearest_edge_idx(row, col, xdata, ydata)
        cell = self._scene.grid.cells[row][col]
        if cell.edges is None or edge_idx >= len(cell.edges):
            return None
        return cell.edges[edge_idx]

    def _nearest_edge_idx(self, row: int, col: int, xdata: float, ydata: float) -> int:
        t = self._renderer.tile_size if isinstance(self._renderer, VillageRenderer) else 48
        fx = (xdata - col * t) / t
        fy = (ydata - row * t) / t
        fx = max(0.0, min(1.0, fx))
        fy = max(0.0, min(1.0, fy))
        distances = {0: fy, 1: fx, 2: 1.0 - fy, 3: 1.0 - fx}
        return min(distances, key=distances.__getitem__)

    def _edge_coords(self, row: int, col: int, edge_idx: int):
        t = self._renderer.tile_size if isinstance(self._renderer, VillageRenderer) else 48
        if edge_idx == 0:
            return (col * t, row * t, (col + 1) * t, row * t)
        if edge_idx == 1:
            return (col * t, row * t, col * t, (row + 1) * t)
        if edge_idx == 2:
            return (col * t, (row + 1) * t, (col + 1) * t, (row + 1) * t)
        return ((col + 1) * t, row * t, (col + 1) * t, (row + 1) * t)

    def _data_to_cell(self, xdata, ydata):
        t = self._renderer.tile_size if isinstance(self._renderer, VillageRenderer) else 48
        col = int(xdata / t)
        row = int(ydata / t)
        if not (0 <= row < self._scene.n_rows and 0 <= col < self._scene.n_cols):
            return None
        return row, col
