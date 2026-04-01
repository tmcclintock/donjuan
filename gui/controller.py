"""
Application controller: bridges the GUI widgets and the donjuan library.
"""
import random
import time

import matplotlib.patches as mpatches
from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from donjuan import Dungeon, DungeonRandomizer, FoundryExporter, HexRenderer, Renderer, TexturedRenderer
from gui.edit_controller import EditController
from donjuan.grid import HexGrid, SquareGrid
from donjuan.randomizer import Randomizer
from donjuan.room_randomizer import RoomSizeRandomizer


class _HoverFilter(QObject):
    """Event filter that fires callbacks on mouse enter/leave."""
    def __init__(self, on_enter, on_leave, parent=None):
        super().__init__(parent)
        self._on_enter = on_enter
        self._on_leave = on_leave

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self._on_enter()
        elif event.type() == QEvent.Leave:
            self._on_leave()
        return False


# Maximum figure dimension (inches) used when displaying on screen.
# Figures are saved at full resolution independently of this.
_MAX_DISPLAY_INCHES = 8.0
_SCREEN_DPI = 100


class AppController:
    """
    Handles the Generate and Save actions. Owns the last-generated
    ``Dungeon`` and ``Figure`` so they can be reused for saving.

    Args:
        control_panel: the :class:`~gui.widgets.ControlPanel` instance
        canvas: the :class:`~gui.widgets.DungeonCanvas` instance
        status_bar: the ``QStatusBar`` of the main window
        regen_action: the "Regenerate" QAction to enable after first generate
        save_action: the "Save PNG" QAction to enable after first generate
    """

    def __init__(self, control_panel, canvas, status_bar, regen_action, save_action, export_action=None, edit_action=None, undo_action=None):
        self._cp = control_panel
        self._canvas = canvas
        self._status = status_bar
        self._regen_action = regen_action
        self._save_action = save_action
        self._export_action = export_action
        self._edit_action = edit_action
        self._undo_action = undo_action

        self._dungeon = None
        self._fig = None
        self._renderer = None
        self._last_seed = None
        self._overlay_artists = []
        self._edit_mode = False
        self._edit_controller = None

        if edit_action is not None:
            edit_action.toggled.connect(self._on_edit_mode_toggled)
        control_panel.edit_mode_btn.toggled.connect(self._on_edit_mode_toggled)

        # Show a Foundry preview overlay while hovering over the export button.
        self._hover_filter = _HoverFilter(
            self._show_foundry_overlay,
            self._hide_foundry_overlay,
        )
        control_panel.export_btn.installEventFilter(self._hover_filter)

    # ── Slots (connected to button clicks / menu actions) ──────────────

    def on_generate(self) -> None:
        try:
            params = self._cp.get_params()
        except ValueError as exc:
            QMessageBox.warning(None, "Invalid Settings", str(exc))
            return

        # If no seed supplied, pick one silently — the seed field stays blank
        # so the next Generate press produces a fresh dungeon automatically.
        # The seed used is always visible in the status bar for replay.
        if params["seed"] is None:
            params["seed"] = random.randint(0, 999_999)

        self._run_generation(params)

    def on_regenerate(self) -> None:
        """Re-run generation with the last seed used, writing it into the field."""
        if self._last_seed is None:
            self.on_generate()
            return
        self._cp.set_seed(self._last_seed)
        self.on_generate()

    def on_save(self) -> None:
        if self._fig is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            None,
            "Save Dungeon as PNG",
            "dungeon.png",
            "PNG Files (*.png)",
        )
        if not path:
            return
        # TexturedRenderer: save the raw PIL image at full tile resolution.
        # Other renderers: use matplotlib's savefig at high DPI.
        if (
            isinstance(self._renderer, TexturedRenderer)
            and self._renderer._last_image is not None
        ):
            self._renderer._last_image.save(path)
        else:
            self._fig.savefig(path, bbox_inches="tight", dpi=200)
        self._status.showMessage(f"Saved → {path}")

    def on_export(self) -> None:
        """Export the current dungeon as a FoundryVTT scene bundle."""
        if self._dungeon is None:
            return

        # ── Step 1: ask for a name ─────────────────────────────────────
        scene_name, ok = QInputDialog.getText(
            None,
            "Export to FoundryVTT",
            "Dungeon name (used for the scene and file names):",
            text="DonJuan Dungeon",
        )
        if not ok or not scene_name.strip():
            return
        scene_name = scene_name.strip()

        # ── Step 2: choose output folder ───────────────────────────────
        output_dir = QFileDialog.getExistingDirectory(
            None,
            "Choose Export Folder",
            "",
            QFileDialog.ShowDirsOnly,
        )
        if not output_dir:
            return

        try:
            params = self._cp.get_params()
        except ValueError:
            params = {}

        exporter = FoundryExporter(
            tile_size=100,
            pack=params.get("pack", "stone"),
            wall_shadows=params.get("wall_shadows", True),
            torchlight=params.get("torchlight", True),
            moss_and_cracks=params.get("moss_and_cracks", True),
            pillars=params.get("pillars", True),
            wall_lines=params.get("wall_lines", True),
            add_lights=True,
        )

        try:
            img_path, json_path = exporter.export(
                self._dungeon,
                output_dir,
                scene_name=scene_name,
            )
        except Exception as exc:
            QMessageBox.critical(None, "Export Failed", str(exc))
            return

        import os
        img_file  = os.path.basename(img_path)
        json_file = os.path.basename(json_path)

        QMessageBox.information(
            None,
            "FoundryVTT Export Complete",
            f"Files written to:\n  {img_path}\n  {json_path}\n\n"
            "── Importing into FoundryVTT ──────────────────────────────\n\n"
            "Easiest: install the Quick Battlemap Importer module\n"
            "  https://foundryvtt.com/packages/quick-battlemap-importer\n"
            "Then drag-and-drop the exported folder into Foundry.\n\n"
            "Manual import:\n"
            f"1. Copy {img_file} into your Foundry data folder (or a sub-folder).\n"
            f"2. Open Foundry → Scenes tab → Import Data → select {json_file}.\n"
            f"3. In the imported scene, re-link the background image to {img_file}.",
        )
        self._status.showMessage(f'Exported FoundryVTT scene "{scene_name}" \u2192 {output_dir}')

    # ── Edit mode ──────────────────────────────────────────────────────

    def _on_edit_mode_toggled(self, checked: bool) -> None:
        if checked == self._edit_mode:
            return  # already in the right state; avoid sync loops
        self._edit_mode = checked

        # Keep the menu action and panel button in sync with whichever fired.
        for widget in (self._edit_action, self._cp.edit_mode_btn):
            if widget is None:
                continue
            widget.blockSignals(True)
            widget.setChecked(checked)
            widget.blockSignals(False)

        self._cp.set_edit_mode(checked)

        if self._edit_controller is not None:
            if checked:
                self._edit_controller.activate()
            else:
                self._edit_controller.deactivate()

        if self._undo_action is not None:
            self._undo_action.setEnabled(checked)

        if not checked:
            self._status.showMessage("Edit mode off")

    def on_undo(self) -> None:
        if self._edit_mode and self._edit_controller is not None:
            self._edit_controller.undo()

    # ── Foundry overlay ────────────────────────────────────────────────

    def _show_foundry_overlay(self) -> None:
        """Draw Foundry walls/doors/lights on top of the current render."""
        if self._dungeon is None:
            return
        ax = self._canvas.get_axes()
        if ax is None:
            return

        tile_size = (
            self._renderer.tile_size
            if isinstance(self._renderer, TexturedRenderer)
            else 48
        )

        exporter = FoundryExporter(tile_size=tile_size)
        walls  = exporter._build_walls(self._dungeon)
        lights = exporter._build_lights(self._dungeon)

        # Lock the axes limits so the overlay doesn't cause a resize.
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        artists = []

        for wall in walls:
            x1, y1, x2, y2 = wall["c"]
            color = "#6699ff" if wall["door"] == 1 else "#ffffaa"
            lw    = 2.5       if wall["door"] == 1 else 1.5
            line, = ax.plot(
                [x1, x2], [y1, y2],
                color=color, alpha=0.85, linewidth=lw,
                solid_capstyle="round",
            )
            artists.append(line)

        for light in lights:
            cx, cy = light["x"], light["y"]
            circle = mpatches.Circle(
                (cx, cy), radius=tile_size * 0.28,
                color="#ff9933", alpha=0.5,
                linewidth=0,
            )
            ax.add_patch(circle)
            artists.append(circle)

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        self._overlay_artists = artists
        self._canvas.refresh()

    def _hide_foundry_overlay(self) -> None:
        """Remove the Foundry overlay from the canvas."""
        for artist in self._overlay_artists:
            artist.remove()
        self._overlay_artists = []
        self._canvas.refresh()

    # ── Private helpers ────────────────────────────────────────────────

    def _rerender_dungeon(self) -> None:
        """Re-render the current dungeon in-place (no regeneration)."""
        if self._dungeon is None or self._renderer is None:
            return

        fig, _ax = self._renderer.render(self._dungeon, save=False)
        w, h = fig.get_size_inches()
        scale = min(_MAX_DISPLAY_INCHES / max(w, h), 1.0)
        fig.set_size_inches(w * scale, h * scale, forward=True)
        fig.set_dpi(_SCREEN_DPI)
        self._fig = fig

        # update_figure destroys the old FigureCanvas, so deactivate first
        # and reconnect the edit controller to the new canvas afterwards.
        if self._edit_controller is not None:
            self._edit_controller.deactivate()
        self._canvas.update_figure(fig)
        if self._edit_controller is not None and self._edit_mode:
            self._edit_controller.activate()

    def _run_generation(self, params: dict) -> None:
        seed = params["seed"]
        Randomizer.seed(seed)
        self._last_seed = seed

        t0 = time.perf_counter()

        # Build the dungeon
        room_rng = RoomSizeRandomizer(
            min_size=params["min_size"],
            max_size=params["max_size"],
        )
        dr = DungeonRandomizer(
            room_size_randomizer=room_rng,
            max_num_rooms=params["max_rooms"],
            door_probability=params.get("door_probability", 1.0),
        )

        if params["grid_type"] == "Square":
            grid = SquareGrid(params["n_rows"], params["n_cols"])
            if params["render_style"] == "Textured":
                renderer = TexturedRenderer(
                    tile_size=48,
                    wall_shadows=params["wall_shadows"],
                    torchlight=params["torchlight"],
                    moss_and_cracks=params["moss_and_cracks"],
                    pillars=params["pillars"],
                    wall_lines=params["wall_lines"],
                    pack=params["pack"],
                )
            else:
                renderer = Renderer(scale=0.5)
        else:
            grid = HexGrid(params["n_rows"], params["n_cols"])
            renderer = HexRenderer(scale=0.35)

        dungeon = Dungeon(grid=grid)
        dr.randomize_dungeon(dungeon)

        # Render (no file write)
        self._renderer = renderer
        fig, _ax = renderer.render(dungeon, save=False)

        # Scale the figure down for comfortable on-screen display while
        # preserving aspect ratio. The original figsize is kept for saving.
        w, h = fig.get_size_inches()
        scale = min(_MAX_DISPLAY_INCHES / max(w, h), 1.0)
        fig.set_size_inches(w * scale, h * scale, forward=True)
        fig.set_dpi(_SCREEN_DPI)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Store and display (clear any stale overlay artists first)
        self._overlay_artists = []
        self._dungeon = dungeon
        self._fig = fig
        self._canvas.update_figure(fig)

        # Rebuild the edit controller for the new dungeon/renderer.
        # update_figure replaces the underlying FigureCanvas, so any old
        # mpl_connect IDs are gone — always start fresh.
        if self._edit_controller is not None:
            self._edit_controller.deactivate()
        self._edit_controller = EditController(
            canvas=self._canvas,
            dungeon=dungeon,
            renderer=renderer,
            status_bar=self._status,
            rerender_fn=self._rerender_dungeon,
            get_theme_fn=lambda: self._cp.current_theme,
        )
        if self._edit_mode:
            self._edit_controller.activate()

        n_rooms = len(dungeon.rooms)
        n_hallways = len(dungeon.hallways)
        self._status.showMessage(
            f"Generated {n_rooms} rooms, {n_hallways} hallways  ·  "
            f"seed {seed}  ·  {elapsed_ms:.0f} ms"
        )

        # Unlock save / export controls now that we have content
        self._cp.save_btn.setEnabled(True)
        self._cp.export_btn.setEnabled(True)
        self._regen_action.setEnabled(True)
        self._save_action.setEnabled(True)
        if self._export_action is not None:
            self._export_action.setEnabled(True)
        if self._edit_action is not None:
            self._edit_action.setEnabled(True)
        self._cp.edit_mode_btn.setEnabled(True)
