"""
Reusable compound widgets for the DonJuan GUI.
"""
import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class LabeledSpinBox(QWidget):
    """A QLabel + QSpinBox pair laid out horizontally."""

    def __init__(self, label: str, min_val: int, max_val: int, default: int, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setMinimumWidth(110)
        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(default)
        self.spinbox.setMinimumWidth(70)

        layout.addWidget(lbl)
        layout.addWidget(self.spinbox)

    @property
    def value(self) -> int:
        return self.spinbox.value()

    def set_value(self, v: int) -> None:
        self.spinbox.setValue(v)


class Divider(QFrame):
    """A thin horizontal rule used to separate control groups."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class ControlPanel(QWidget):
    """
    Left-hand settings panel. Uses a QStackedWidget to show either the
    generation controls (page 0) or the edit-mode controls (page 1).
    Call :meth:`set_edit_mode` to switch between them.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(270)
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Stacked pages ──────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_generate_page())
        self._stack.addWidget(self._build_edit_page())

        # ── Bottom bar (always visible) ────────────────────────────────
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 12)
        bottom_layout.setSpacing(6)

        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(6)

        self.generate_btn = QPushButton("⚔  Generate")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.setMinimumHeight(36)

        self.edit_mode_btn = QPushButton("✏  Edit")
        self.edit_mode_btn.setObjectName("editModeButton")
        self.edit_mode_btn.setCheckable(True)
        self.edit_mode_btn.setEnabled(False)
        self.edit_mode_btn.setMinimumHeight(36)

        mode_layout.addWidget(self.generate_btn)
        mode_layout.addWidget(self.edit_mode_btn)

        self.save_btn = QPushButton("💾  Save PNG…")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(32)

        self.export_btn = QPushButton("🗺  Export FoundryVTT…")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(32)

        bottom_layout.addWidget(mode_row)
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.export_btn)

        # ── Assemble ───────────────────────────────────────────────────
        root.addWidget(self._stack, 1)
        root.addWidget(Divider())
        root.addWidget(bottom)

    # ── Page builders ──────────────────────────────────────────────────

    def _build_generate_page(self) -> QWidget:
        """Scrollable page shown during dungeon generation."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 16, 12, 8)

        # ── Scene type ────────────────────────────────────────────────
        scene_box = QGroupBox("Scene")
        scene_layout = QVBoxLayout(scene_box)
        scene_layout.setSpacing(6)

        scene_type_row = QWidget()
        scene_type_layout = QHBoxLayout(scene_type_row)
        scene_type_layout.setContentsMargins(0, 0, 0, 0)
        scene_type_lbl = QLabel("Scene type")
        scene_type_lbl.setMinimumWidth(110)
        self.scene_type = QComboBox()
        self.scene_type.addItems(["Dungeon", "Forest", "Camp", "Village"])
        self.scene_type.setMinimumWidth(70)
        scene_type_layout.addWidget(scene_type_lbl)
        scene_type_layout.addWidget(self.scene_type)

        self.rows = LabeledSpinBox("Rows", 5, 100, 20)
        self.cols = LabeledSpinBox("Columns", 5, 100, 20)

        for w in (scene_type_row, self.rows, self.cols):
            scene_layout.addWidget(w)

        # ── Dungeon-specific settings ─────────────────────────────────
        self._dungeon_settings = QWidget()
        dungeon_layout = QVBoxLayout(self._dungeon_settings)
        dungeon_layout.setSpacing(10)
        dungeon_layout.setContentsMargins(0, 0, 0, 0)

        grid_box = QGroupBox("Grid")
        grid_layout = QVBoxLayout(grid_box)
        grid_layout.setSpacing(6)

        type_row = QWidget()
        type_layout = QHBoxLayout(type_row)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_lbl = QLabel("Grid type")
        type_lbl.setMinimumWidth(110)
        self.grid_type = QComboBox()
        self.grid_type.addItems(["Square", "Hex"])
        self.grid_type.setMinimumWidth(70)
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.grid_type)

        style_row = QWidget()
        style_layout = QHBoxLayout(style_row)
        style_layout.setContentsMargins(0, 0, 0, 0)
        style_lbl = QLabel("Render style")
        style_lbl.setMinimumWidth(110)
        self.render_style = QComboBox()
        self.render_style.addItems(["Textured", "Grid"])
        self.render_style.setMinimumWidth(70)
        style_layout.addWidget(style_lbl)
        style_layout.addWidget(self.render_style)

        for w in (type_row, style_row):
            grid_layout.addWidget(w)

        self.grid_type.currentTextChanged.connect(self._on_grid_type_changed)
        self.render_style.currentTextChanged.connect(self._on_render_style_changed)

        self._texture_box = QGroupBox("Textures")
        texture_layout = QVBoxLayout(self._texture_box)
        texture_layout.setSpacing(4)

        self.cb_wall_shadows = QCheckBox("Wall shadows")
        self.cb_torchlight   = QCheckBox("Torchlight")
        self.cb_moss_cracks  = QCheckBox("Moss & cracks")
        self.cb_pillars      = QCheckBox("Pillars")
        self.cb_wall_lines   = QCheckBox("Wall outlines")

        for cb in (self.cb_wall_shadows, self.cb_torchlight,
                   self.cb_moss_cracks, self.cb_pillars, self.cb_wall_lines):
            cb.setChecked(True)
            texture_layout.addWidget(cb)

        pack_row = QWidget()
        pack_layout = QHBoxLayout(pack_row)
        pack_layout.setContentsMargins(0, 4, 0, 0)
        pack_lbl = QLabel("Pack")
        pack_lbl.setMinimumWidth(110)
        self.pack_combo = QComboBox()
        from donjuan import PACK_NAMES
        for name in PACK_NAMES:
            self.pack_combo.addItem(name.capitalize(), userData=name)
        self.pack_combo.setMinimumWidth(70)
        pack_layout.addWidget(pack_lbl)
        pack_layout.addWidget(self.pack_combo)
        texture_layout.addWidget(pack_row)

        room_box = QGroupBox("Rooms")
        room_layout = QVBoxLayout(room_box)
        room_layout.setSpacing(6)

        self.min_size = LabeledSpinBox("Min room size", 1, 20, 2)
        self.max_size = LabeledSpinBox("Max room size", 1, 20, 4)
        self.max_rooms = LabeledSpinBox("Max rooms", 1, 50, 10)
        self.door_probability = LabeledSpinBox("Door probability %", 0, 100, 100)

        for w in (self.min_size, self.max_size, self.max_rooms, self.door_probability):
            room_layout.addWidget(w)

        for w in (grid_box, self._texture_box, room_box):
            dungeon_layout.addWidget(w)

        # ── Forest-specific settings ───────────────────────────────────
        self._forest_settings = QWidget()
        forest_layout = QVBoxLayout(self._forest_settings)
        forest_layout.setSpacing(10)
        forest_layout.setContentsMargins(0, 0, 0, 0)

        trees_box = QGroupBox("Trees & Undergrowth")
        trees_layout = QVBoxLayout(trees_box)
        trees_layout.setSpacing(6)
        self.tree_density        = LabeledSpinBox("Tree density %",        1, 40,  8)
        self.undergrowth_density = LabeledSpinBox("Undergrowth density %", 0, 50, 12)
        self.min_tree_spacing    = LabeledSpinBox("Min tree spacing",       1,  6,  2)
        for w in (self.tree_density, self.undergrowth_density, self.min_tree_spacing):
            trees_layout.addWidget(w)
        forest_layout.addWidget(trees_box)

        # ── Camp-specific settings ─────────────────────────────────────
        self._camp_settings = QWidget()
        camp_layout = QVBoxLayout(self._camp_settings)
        camp_layout.setSpacing(10)
        camp_layout.setContentsMargins(0, 0, 0, 0)

        camp_box = QGroupBox("Campfires & Tents")
        camp_box_layout = QVBoxLayout(camp_box)
        camp_box_layout.setSpacing(6)
        self.n_fires          = LabeledSpinBox("Campfires",          1,  4,  1)
        self.n_tents          = LabeledSpinBox("Tents",              2, 16,  6)
        self.camp_radius_pct  = LabeledSpinBox("Tent ring radius %", 20, 70, 40)
        self.camp_tree_density_pct = LabeledSpinBox("Perimeter trees %", 0, 25, 5)
        for w in (self.n_fires, self.n_tents,
                  self.camp_radius_pct, self.camp_tree_density_pct):
            camp_box_layout.addWidget(w)
        camp_layout.addWidget(camp_box)

        # ── Village-specific settings ──────────────────────────────────
        self._village_settings = QWidget()
        village_layout = QVBoxLayout(self._village_settings)
        village_layout.setSpacing(10)
        village_layout.setContentsMargins(0, 0, 0, 0)

        village_box = QGroupBox("Buildings & Roads")
        village_box_layout = QVBoxLayout(village_box)
        village_box_layout.setSpacing(6)
        self.village_buildings = LabeledSpinBox("Buildings", 2, 30, 10)
        self.village_min_size = LabeledSpinBox("Min building size", 1, 8, 2)
        self.village_max_size = LabeledSpinBox("Max building size", 1, 10, 4)
        self.village_tree_density = LabeledSpinBox("Tree density %", 0, 25, 6)
        self.village_road_branchiness = LabeledSpinBox("Road branchiness %", 0, 100, 20)
        for w in (
            self.village_buildings,
            self.village_min_size,
            self.village_max_size,
            self.village_tree_density,
            self.village_road_branchiness,
        ):
            village_box_layout.addWidget(w)
        village_layout.addWidget(village_box)

        # ── Seed (always visible) ─────────────────────────────────────
        seed_box = QGroupBox("Seed")
        seed_layout = QHBoxLayout(seed_box)
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("leave blank for random")
        seed_layout.addWidget(self.seed_input)

        layout.addWidget(scene_box)
        layout.addWidget(self._dungeon_settings)
        layout.addWidget(self._forest_settings)
        layout.addWidget(self._camp_settings)
        layout.addWidget(self._village_settings)
        layout.addWidget(seed_box)
        layout.addStretch()

        self._forest_settings.hide()
        self._camp_settings.hide()
        self._village_settings.hide()
        self.scene_type.currentTextChanged.connect(self._on_scene_type_changed)

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        from PyQt5.QtCore import Qt
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll

    def _build_edit_page(self) -> QWidget:
        """Compact page shown while edit mode is active."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 16, 12, 8)

        # Hint label
        self._edit_hint = QLabel(
            "Click / drag  —  paint cells\n"
            "Shift + click  —  toggle door\n"
            "Alt + click  —  apply theme\n"
            "Cmd + Z  —  undo"
        )
        self._edit_hint.setStyleSheet("color: #6c7086; font-size: 11px; line-height: 1.6;")
        self._edit_hint.setWordWrap(True)
        layout.addWidget(self._edit_hint)

        self._village_tools_box = QGroupBox("Village Tool")
        tools_layout = QGridLayout(self._village_tools_box)
        tools_layout.setSpacing(4)
        tools_layout.setContentsMargins(6, 8, 6, 8)
        self._village_tool_group = QButtonGroup(self)
        self._village_tool_group.setExclusive(True)

        tool_specs = [
            ("building", "Building"),
            ("road", "Road"),
            ("tree", "Tree"),
            ("erase", "Erase"),
            ("door", "Door"),
        ]
        for i, (key, label) in enumerate(tool_specs):
            btn = QPushButton(label)
            btn.setObjectName("villageToolButton")
            btn.setCheckable(True)
            btn.setProperty("villageTool", key)
            btn.setMinimumHeight(28)
            self._village_tool_group.addButton(btn)
            tools_layout.addWidget(btn, i // 2, i % 2)
        self._village_tool_group.buttons()[0].setChecked(True)
        self._village_tools_box.hide()
        layout.addWidget(self._village_tools_box)

        layout.addWidget(Divider())

        # Theme swatches
        themes_box = QGroupBox("Room Theme")
        themes_layout = QGridLayout(themes_box)
        themes_layout.setSpacing(4)
        themes_layout.setContentsMargins(6, 8, 6, 8)

        _THEME_SWATCHES = [
            ("default",  "Default",  "#50505a", "#70707a"),
            ("treasury", "Treasury", "#7a6010", "#c8a830"),
            ("throne",   "Throne",   "#5a2040", "#9a4875"),
            ("prison",   "Prison",   "#283428", "#4a6048"),
            ("barracks", "Barracks", "#5a3820", "#9a6840"),
            ("crypt",    "Crypt",    "#2c2e48", "#5860a0"),
        ]

        self._theme_btn_group = QButtonGroup(self)
        self._theme_btn_group.setExclusive(True)

        for i, (key, label, bg, hi) in enumerate(_THEME_SWATCHES):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("themeKey", key)
            btn.setMinimumHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: #d0d0d8;
                    border: 1px solid {bg};
                    border-radius: 4px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {hi};
                    border-color: {hi};
                }}
                QPushButton:checked {{
                    background-color: {hi};
                    border: 2px solid #cdd6f4;
                    color: #ffffff;
                }}
            """)
            self._theme_btn_group.addButton(btn)
            themes_layout.addWidget(btn, i // 2, i % 2)

        self._theme_btn_group.buttons()[0].setChecked(True)

        layout.addWidget(themes_box)
        layout.addStretch()
        return page

    # ── Public API ─────────────────────────────────────────────────────

    def set_edit_mode(self, active: bool) -> None:
        """Switch between generate (0) and edit (1) panels."""
        self._stack.setCurrentIndex(1 if active else 0)

    def set_edit_scene_type(self, scene_type: str) -> None:
        scene = scene_type.lower()
        is_village = scene == "village"
        self._village_tools_box.setVisible(is_village)
        if is_village:
            self._edit_hint.setText(
                "Use the selected tool to paint\n"
                "Door  —  click a building edge\n"
                "Building / Road use the selected theme\n"
                "Cmd + Z  —  undo"
            )
        else:
            self._edit_hint.setText(
                "Click / drag  —  paint cells\n"
                "Shift + click  —  toggle door\n"
                "Alt + click  —  apply theme\n"
                "Cmd + Z  —  undo"
            )

    @property
    def current_theme(self) -> str:
        btn = self._theme_btn_group.checkedButton()
        return btn.property("themeKey") if btn is not None else "default"

    @property
    def current_village_tool(self) -> str:
        btn = self._village_tool_group.checkedButton()
        return btn.property("villageTool") if btn is not None else "building"

    def set_seed(self, seed: int) -> None:
        self.seed_input.setText(str(seed))

    def get_params(self) -> dict:
        seed_text = self.seed_input.text().strip()
        seed = int(seed_text) if seed_text else None
        scene = self.scene_type.currentText()

        params = {
            "scene_type": scene,
            "n_rows": self.rows.value,
            "n_cols": self.cols.value,
            "seed": seed,
        }

        if scene == "Dungeon":
            min_s = self.min_size.value
            max_s = self.max_size.value
            if min_s > max_s:
                raise ValueError(
                    f"Min room size ({min_s}) must be ≤ max room size ({max_s})."
                )
            params.update({
                "grid_type":       self.grid_type.currentText(),
                "render_style":    self.render_style.currentText(),
                "min_size":        min_s,
                "max_size":        max_s,
                "max_rooms":       self.max_rooms.value,
                "door_probability": self.door_probability.value / 100.0,
                "wall_shadows":    self.cb_wall_shadows.isChecked(),
                "torchlight":      self.cb_torchlight.isChecked(),
                "moss_and_cracks": self.cb_moss_cracks.isChecked(),
                "pillars":         self.cb_pillars.isChecked(),
                "wall_lines":      self.cb_wall_lines.isChecked(),
                "pack":            self.pack_combo.currentData(),
            })
        elif scene == "Forest":
            params.update({
                "tree_density":        self.tree_density.value / 100.0,
                "undergrowth_density": self.undergrowth_density.value / 100.0,
                "min_tree_spacing":    self.min_tree_spacing.value,
            })
        elif scene == "Camp":
            params.update({
                "n_fires":                self.n_fires.value,
                "n_tents":                self.n_tents.value,
                "camp_radius":            self.camp_radius_pct.value / 100.0,
                "perimeter_tree_density": self.camp_tree_density_pct.value / 100.0,
            })
        elif scene == "Village":
            min_s = self.village_min_size.value
            max_s = self.village_max_size.value
            if min_s > max_s:
                raise ValueError(
                    f"Min building size ({min_s}) must be ≤ max building size ({max_s})."
                )
            params.update({
                "n_buildings": self.village_buildings.value,
                "min_building_size": min_s,
                "max_building_size": max_s,
                "tree_density": self.village_tree_density.value / 100.0,
                "road_branchiness": self.village_road_branchiness.value / 100.0,
            })

        return params

    # ── Private helpers ────────────────────────────────────────────────

    def _on_scene_type_changed(self, scene: str) -> None:
        self._dungeon_settings.setVisible(scene == "Dungeon")
        self._forest_settings.setVisible(scene == "Forest")
        self._camp_settings.setVisible(scene == "Camp")
        self._village_settings.setVisible(scene == "Village")

    def _on_grid_type_changed(self, grid_type: str) -> None:
        is_hex = grid_type == "Hex"
        self.render_style.setCurrentText("Grid" if is_hex else self.render_style.currentText())
        self.render_style.setEnabled(not is_hex)
        self._update_texture_box()

    def _on_render_style_changed(self, _style: str) -> None:
        self._update_texture_box()

    def _update_texture_box(self) -> None:
        active = (
            self.grid_type.currentText() == "Square"
            and self.render_style.currentText() == "Textured"
        )
        self._texture_box.setEnabled(active)


class DungeonCanvas(QWidget):
    """
    Right-hand panel that hosts a matplotlib FigureCanvas and navigation
    toolbar. Call :meth:`update_figure` to swap in a new dungeon render.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._fig = None
        self._canvas = None
        self._toolbar = None

        self._show_placeholder()

    # ── Public API ─────────────────────────────────────────────────────

    def update_figure(self, fig: Figure) -> None:
        """Replace the current canvas with a new matplotlib Figure."""
        self._clear_canvas()

        self._fig = fig
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._toolbar = NavigationToolbar(self._canvas, self)

        self._layout.addWidget(self._canvas)
        self._layout.addWidget(self._toolbar)
        self._canvas.draw()

    @property
    def figure(self) -> Figure:
        return self._fig

    def get_axes(self):
        """Return the current matplotlib Axes, or None if not available."""
        if self._fig is None or not self._fig.axes:
            return None
        return self._fig.axes[0]

    def get_canvas(self):
        """Return the underlying FigureCanvas, or None if not available."""
        return self._canvas

    def get_toolbar(self):
        """Return the NavigationToolbar, or None if not available."""
        return self._toolbar

    def refresh(self) -> None:
        """Redraw the canvas without replacing the figure."""
        if self._canvas is not None:
            self._canvas.draw_idle()

    # ── Private helpers ────────────────────────────────────────────────

    def _show_placeholder(self) -> None:
        """Display a dark placeholder before any dungeon has been generated."""
        fig = Figure(facecolor="#1e1e2e")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1e1e2e")
        ax.text(
            0.5, 0.52,
            "⚔",
            ha="center", va="center",
            color="#45475a", fontsize=64,
            transform=ax.transAxes,
        )
        ax.text(
            0.5, 0.38,
            "Generate a dungeon to get started",
            ha="center", va="center",
            color="#585b70", fontsize=13,
            transform=ax.transAxes,
        )
        ax.axis("off")

        self._fig = fig
        self._canvas = FigureCanvas(fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._layout.addWidget(self._canvas)
        self._canvas.draw()

    def _clear_canvas(self) -> None:
        """Remove and destroy the existing canvas and toolbar widgets."""
        import matplotlib.pyplot as plt

        if self._toolbar is not None:
            self._layout.removeWidget(self._toolbar)
            self._toolbar.deleteLater()
            self._toolbar = None

        if self._canvas is not None:
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
            self._canvas = None

        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
