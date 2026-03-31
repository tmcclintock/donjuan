"""
Main application window for the DonJuan dungeon generator GUI.
"""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QSplitter,
    QStatusBar,
)

from gui.controller import AppController
from gui.widgets import ControlPanel, DungeonCanvas

# ── Stylesheet ─────────────────────────────────────────────────────────────────
# A dark Catppuccin-inspired theme that fits a dungeon aesthetic.
STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Helvetica Neue", "Segoe UI", sans-serif;
    font-size: 13px;
}

QGroupBox {
    color: #a6adc8;
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QLabel {
    color: #cdd6f4;
}

QSpinBox, QComboBox, QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 3px 6px;
    min-height: 22px;
}
QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
    border: 1px solid #89b4fa;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #45475a;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #585b70;
}
QComboBox::drop-down {
    border: none;
    background-color: #45475a;
    width: 20px;
    border-radius: 0 4px 4px 0;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 12px;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    color: #45475a;
    border-color: #313244;
    background-color: #181825;
}
QPushButton#primaryButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}
QPushButton#primaryButton:hover {
    background-color: #b4befe;
}
QPushButton#primaryButton:pressed {
    background-color: #74c7ec;
}

QStatusBar {
    background-color: #181825;
    color: #6c7086;
    border-top: 1px solid #313244;
    padding: 2px 8px;
    font-size: 11px;
}

QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item:selected {
    background-color: #313244;
}
QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 3px 0;
}

QSplitter::handle {
    background-color: #313244;
    width: 2px;
}

/* matplotlib navigation toolbar */
QToolBar, NavigationToolbar2QT {
    background-color: #181825;
    border-top: 1px solid #313244;
    spacing: 2px;
}
QToolButton {
    background-color: transparent;
    border: none;
    padding: 3px;
    border-radius: 3px;
}
QToolButton:hover {
    background-color: #313244;
}
"""


class DonJuanApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DonJuan — Dungeon Generator")
        self.setMinimumSize(960, 640)
        self.resize(1200, 760)
        self.setStyleSheet(STYLESHEET)

        # ── Widgets ────────────────────────────────────────────────────
        self.control_panel = ControlPanel()
        self.canvas = DungeonCanvas()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(0, 0)   # control panel: fixed
        splitter.setStretchFactor(1, 1)   # canvas: stretches
        splitter.setSizes([270, 900])
        self.setCentralWidget(splitter)

        # ── Status bar ─────────────────────────────────────────────────
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready  ·  configure settings and press Generate")

        # ── Menu bar ───────────────────────────────────────────────────
        regen_action, save_action, export_action = self._build_menu()

        # ── Controller ─────────────────────────────────────────────────
        self.controller = AppController(
            control_panel=self.control_panel,
            canvas=self.canvas,
            status_bar=status_bar,
            regen_action=regen_action,
            save_action=save_action,
            export_action=export_action,
        )

        # ── Wire signals ───────────────────────────────────────────────
        self.control_panel.generate_btn.clicked.connect(self.controller.on_generate)
        self.control_panel.save_btn.clicked.connect(self.controller.on_save)
        self.control_panel.export_btn.clicked.connect(self.controller.on_export)

    def _build_menu(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")

        save_action = QAction("&Save PNG…", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setEnabled(False)
        save_action.triggered.connect(lambda: self.controller.on_save())
        file_menu.addAction(save_action)

        export_action = QAction("Export &FoundryVTT…", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setEnabled(False)
        export_action.triggered.connect(lambda: self.controller.on_export())
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Generate
        gen_menu = menubar.addMenu("&Generate")

        gen_action = QAction("&Generate", self)
        gen_action.setShortcut("Ctrl+G")
        gen_action.triggered.connect(lambda: self.controller.on_generate())
        gen_menu.addAction(gen_action)

        regen_action = QAction("&Regenerate (same seed)", self)
        regen_action.setShortcut("Ctrl+R")
        regen_action.setEnabled(False)
        regen_action.triggered.connect(lambda: self.controller.on_regenerate())
        gen_menu.addAction(regen_action)

        return regen_action, save_action, export_action


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DonJuan")
    window = DonJuanApp()
    window.show()
    sys.exit(app.exec_())
