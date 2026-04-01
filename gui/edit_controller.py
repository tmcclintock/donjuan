"""
Edit mode controller: handles mouse events on the dungeon canvas for
cell painting and door toggling.
"""
import matplotlib.patches as mpatches
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication

from donjuan import TexturedRenderer

_UNDO_MAX_DEPTH = 20


class EditController:
    """
    Manages edit mode state and handles matplotlib canvas mouse events.

    Instantiated (or replaced) each time a dungeon is generated.
    Call :meth:`activate` / :meth:`deactivate` to connect and disconnect
    the mouse event handlers.

    Args:
        canvas: the :class:`~gui.widgets.DungeonCanvas` instance
        dungeon: the current :class:`~donjuan.Dungeon`
        renderer: the renderer used to produce the current figure
        status_bar: the ``QStatusBar`` of the main window
        rerender_fn: callable that re-renders the dungeon in-place
    """

    def __init__(self, canvas, dungeon, renderer, status_bar, rerender_fn, get_theme_fn=None):
        self._canvas = canvas
        self._dungeon = dungeon
        self._renderer = renderer
        self._status = status_bar
        self._rerender = rerender_fn
        self._get_theme = get_theme_fn or (lambda: "default")

        self._cid_press = None
        self._cid_motion = None
        self._cid_release = None
        self._active = False

        # Drag state
        self._dragging = False
        self._drag_fill = None
        self._last_drag_cell = None
        self._preview_artists = []

        # Hover edge highlight (visible while shift is held)
        self._hover_artist = None

        # Undo stack — list of snapshots, newest last
        self._undo_stack = []

    # ── Public API ─────────────────────────────────────────────────────

    def activate(self) -> None:
        """Connect mouse handlers and deactivate any conflicting toolbar tool."""
        if self._active:
            return

        # Pan/zoom intercepts mouse events — deactivate whichever is on.
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

        self._cid_press   = fig_canvas.mpl_connect("button_press_event",   self._on_press)
        self._cid_motion  = fig_canvas.mpl_connect("motion_notify_event",  self._on_motion)
        self._cid_release = fig_canvas.mpl_connect("button_release_event", self._on_release)

        fig_canvas.setCursor(QCursor(Qt.CrossCursor))
        self._active = True

    def deactivate(self) -> None:
        """Disconnect mouse handlers and clear any overlays."""
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
        self._active = False

    def undo(self) -> bool:
        """Restore the previous snapshot. Returns True if there was something to undo."""
        if not self._undo_stack:
            self._status.showMessage("Edit mode  ·  nothing to undo")
            return False
        self._restore_snapshot(self._undo_stack.pop())
        self._rerender()
        remaining = len(self._undo_stack)
        self._status.showMessage(
            f"Edit mode  ·  undo  ·  {remaining} step{'s' if remaining != 1 else ''} remaining"
        )
        return True

    # ── Event handlers ─────────────────────────────────────────────────

    def _on_press(self, event) -> None:
        if event.xdata is None or event.ydata is None:
            return
        if event.button != 1:
            return

        cell = self._data_to_cell(event.xdata, event.ydata)
        if cell is None:
            return

        row, col = cell
        mods = QApplication.keyboardModifiers()
        alt_held   = bool(mods & Qt.AltModifier)
        shift_held = bool(mods & Qt.ShiftModifier)

        if alt_held:
            self._push_snapshot()
            self._apply_theme(row, col)
        elif shift_held:
            self._push_snapshot()
            self._toggle_door_at(row, col, event.xdata, event.ydata)
        else:
            self._drag_fill = not self._dungeon.grid.cells[row][col].filled
            self._push_snapshot()
            self._dragging = True
            self._last_drag_cell = (row, col)
            self._apply_paint(row, col, event.xdata, event.ydata)

    def _on_motion(self, event) -> None:
        mods = QApplication.keyboardModifiers()
        alt_held   = bool(mods & Qt.AltModifier)
        shift_held = bool(mods & Qt.ShiftModifier)

        # Update cursor to reflect current mode.
        fig_canvas = self._canvas.get_canvas()
        if fig_canvas is not None:
            if shift_held:
                cursor = Qt.PointingHandCursor
            elif alt_held:
                cursor = Qt.UpArrowCursor
            else:
                cursor = Qt.CrossCursor
            fig_canvas.setCursor(QCursor(cursor))

        # Alt: show a theme-paint hint in the status bar.
        if alt_held and not shift_held:
            self._status.showMessage(
                f"Edit mode  ·  Alt+click to apply '{self._get_theme()}' theme to room or hallway"
            )

        # Hover edge highlight while shift is held.
        if shift_held and event.xdata is not None and event.ydata is not None:
            cell = self._data_to_cell(event.xdata, event.ydata)
            if cell is not None:
                self._update_hover(cell[0], cell[1], event.xdata, event.ydata)
            else:
                self._clear_hover()
        else:
            self._clear_hover()

        # Drag painting.
        if not self._dragging:
            return
        if event.xdata is None or event.ydata is None:
            return

        cell = self._data_to_cell(event.xdata, event.ydata)
        if cell is None or cell == self._last_drag_cell:
            return

        row, col = cell
        self._last_drag_cell = (row, col)
        self._apply_paint(row, col, event.xdata, event.ydata)

    def _on_release(self, event) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self._drag_fill = None
        self._last_drag_cell = None

        if isinstance(self._renderer, TexturedRenderer) and self._preview_artists:
            self._clear_previews()
            self._rerender()

    # ── Hover highlight ────────────────────────────────────────────────

    def _update_hover(self, row: int, col: int, xdata: float, ydata: float) -> None:
        """Draw (or reposition) a green highlight on the nearest edge."""
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
                color="#a6e3a1", linewidth=2.5, alpha=0.85,
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

    # ── Theme assignment ───────────────────────────────────────────────

    def _apply_theme(self, row: int, col: int) -> None:
        """Apply the selected theme to the room or hallway containing the clicked cell."""
        from donjuan.dungeon.hallway import Hallway
        from donjuan.dungeon.room import Room
        cell = self._dungeon.grid.cells[row][col]
        if not isinstance(cell.space, (Room, Hallway)):
            self._status.showMessage(
                "Edit mode  ·  Alt+click on a room or hallway cell to apply a theme"
            )
            return
        theme = self._get_theme()
        cell.space.theme = theme
        kind = "room" if isinstance(cell.space, Room) else "hallway"
        self._status.showMessage(
            f"Edit mode  ·  applied '{theme}' theme to {kind} '{cell.space.name}'"
        )
        self._rerender()

    # ── Door toggle ────────────────────────────────────────────────────

    def _toggle_door_at(self, row: int, col: int, xdata: float, ydata: float) -> None:
        """Toggle has_door on the edge nearest to the click position."""
        edge = self._nearest_edge(row, col, xdata, ydata)
        if edge is None:
            return

        c1, c2 = edge.cell1, edge.cell2
        if c1 is None or c2 is None:
            return
        if c1.filled or c2.filled:
            self._status.showMessage(
                "Edit mode  ·  can't place a door on a solid wall edge"
            )
            return

        edge.has_door = not edge.has_door
        self._status.showMessage(
            f"Edit mode  ·  door {'added' if edge.has_door else 'removed'} at ({row}, {col})"
        )
        self._rerender()

    def _nearest_edge(self, row: int, col: int, xdata: float, ydata: float):
        edge_idx = self._nearest_edge_idx(row, col, xdata, ydata)
        cell = self._dungeon.grid.cells[row][col]
        if cell.edges is None or edge_idx >= len(cell.edges):
            return None
        return cell.edges[edge_idx]

    def _nearest_edge_idx(self, row: int, col: int, xdata: float, ydata: float) -> int:
        """Return the index (0=top, 1=left, 2=bottom, 3=right) of the closest edge."""
        if isinstance(self._renderer, TexturedRenderer):
            t = self._renderer.tile_size
            fx = (xdata - col * t) / t
            fy = (ydata - row * t) / t
        else:
            fx = xdata - col
            fy = ydata - row

        fx = max(0.0, min(1.0, fx))
        fy = max(0.0, min(1.0, fy))

        distances = {0: fy, 1: fx, 2: 1.0 - fy, 3: 1.0 - fx}
        return min(distances, key=distances.__getitem__)

    def _edge_coords(self, row: int, col: int, edge_idx: int):
        """Return ``(x1, y1, x2, y2)`` for the given edge in axes data coordinates."""
        if isinstance(self._renderer, TexturedRenderer):
            t = self._renderer.tile_size
            if edge_idx == 0:    # top
                return (col * t,       row * t,       (col + 1) * t, row * t)
            elif edge_idx == 1:  # left
                return (col * t,       row * t,       col * t,       (row + 1) * t)
            elif edge_idx == 2:  # bottom
                return (col * t,       (row + 1) * t, (col + 1) * t, (row + 1) * t)
            else:                # right
                return ((col + 1) * t, row * t,       (col + 1) * t, (row + 1) * t)
        else:
            if edge_idx == 0:    # top
                return (col - 0.5, row - 0.5, col + 0.5, row - 0.5)
            elif edge_idx == 1:  # left
                return (col - 0.5, row - 0.5, col - 0.5, row + 0.5)
            elif edge_idx == 2:  # bottom
                return (col - 0.5, row + 0.5, col + 0.5, row + 0.5)
            else:                # right
                return (col + 0.5, row - 0.5, col + 0.5, row + 0.5)

    # ── Paint helpers ──────────────────────────────────────────────────

    def _apply_paint(self, row: int, col: int, xdata: float, ydata: float) -> None:
        """Mutate the cell and update the display."""
        cell = self._dungeon.grid.cells[row][col]

        if cell.filled == self._drag_fill:
            return

        cell.filled = self._drag_fill
        if cell.filled:
            cell.set_space(None)
        if cell.edges:
            for edge in cell.edges:
                if edge is not None:
                    edge.has_door = False

        self._status.showMessage(
            f"Edit mode  ·  cell ({row}, {col}) → {'filled' if cell.filled else 'open'}  ·  "
            "release to commit  ·  Shift+click wall edge to toggle door"
        )

        if isinstance(self._renderer, TexturedRenderer):
            self._show_preview(row, col)
        else:
            self._rerender()

    def _show_preview(self, row: int, col: int) -> None:
        """Draw a semi-transparent rectangle over the painted cell."""
        ax = self._canvas.get_axes()
        if ax is None:
            return

        t = self._renderer.tile_size
        color = "#313244" if self._drag_fill else "#8a6a3a"
        rect = mpatches.Rectangle(
            (col * t, row * t), t, t,
            facecolor=color, alpha=0.75, linewidth=0,
        )
        ax.add_patch(rect)
        self._preview_artists.append(rect)
        self._canvas.refresh()

    def _clear_previews(self) -> None:
        for artist in self._preview_artists:
            artist.remove()
        self._preview_artists = []
        self._canvas.refresh()

    # ── Undo ───────────────────────────────────────────────────────────

    def _push_snapshot(self) -> None:
        self._undo_stack.append(self._take_snapshot())
        if len(self._undo_stack) > _UNDO_MAX_DEPTH:
            self._undo_stack.pop(0)

    def _take_snapshot(self) -> dict:
        cells = {}
        edges = {}
        seen = set()
        for r in range(self._dungeon.n_rows):
            for c in range(self._dungeon.n_cols):
                cell = self._dungeon.grid.cells[r][c]
                cells[(r, c)] = (cell.filled, cell.space)
                for edge in cell.edges:
                    if edge is not None and id(edge) not in seen:
                        seen.add(id(edge))
                        edges[id(edge)] = (edge, edge.has_door)
        return {"cells": cells, "edges": edges}

    def _restore_snapshot(self, snapshot: dict) -> None:
        for (r, c), (filled, space) in snapshot["cells"].items():
            cell = self._dungeon.grid.cells[r][c]
            cell.filled = filled
            cell.set_space(space)
        for _eid, (edge, has_door) in snapshot["edges"].items():
            edge.has_door = has_door

    # ── Coordinate helpers ─────────────────────────────────────────────

    def _data_to_cell(self, xdata, ydata):
        """
        Convert matplotlib axes data coordinates to a ``(row, col)`` grid
        index, or ``None`` if the position is outside the dungeon bounds.
        """
        if isinstance(self._renderer, TexturedRenderer):
            t = self._renderer.tile_size
            col = int(xdata / t)
            row = int(ydata / t)
        else:
            col = int(round(xdata))
            row = int(round(ydata))

        n_rows = self._dungeon.n_rows
        n_cols = self._dungeon.n_cols
        if not (0 <= row < n_rows and 0 <= col < n_cols):
            return None
        return row, col
