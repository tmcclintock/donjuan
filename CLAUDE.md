# CLAUDE.md — Development Guide for DonJuan

## Project Overview

DonJuan is a Python package for procedurally generating fantasy dungeons. It is a modular rebuild of the [donjon dungeon generator](https://donjon.bin.sh/fantasy/dungeon/), designed to be composable and extensible. It ships a PyQt5 desktop GUI with real-time rendering, FoundryVTT export, and interactive edit mode.

Current version: **0.0.3** (active development). Remote: `https://github.com/tmcclintock/donjuan.git`.

---

## Architecture

### Core data model

```
Dungeon
├── Grid (SquareGrid | HexGrid)
│   ├── cells: List[List[Cell]]   # grid[row][col], all filled=True by default
│   └── edges: List[List[List[Edge]]]
├── rooms: Dict[str, Room]
├── hallways: Dict[str, Hallway]
└── room_entrances: Dict[str, List[Edge]]

Space (abstract)
├── Room      — theme: str (default "default")
└── Hallway   — theme: str (default "default")
    └── _ordered_cells: List[Cell]   # defines the corridor path

Cell (abstract)
├── SquareCell  (_n_sides = 4)
└── HexCell     (_n_sides = 6)

Edge
├── cell1, cell2: Optional[Cell]  # cell1 = left/upper; cell2 = right/lower
└── has_door: bool
```

### Coordinate system

All coordinates are `(y, x)` — row first, column second. `cell.y` is the row index (0 = top), `cell.x` is the column index.

### Cell states

- `cell.filled = True` — solid wall (default for all grid cells)
- `cell.filled = False` — open floor (set by rooms, hallways, and carved corridors)
- `cell.space` — the `Space` this cell belongs to (`None` for plain wall cells)

### Edge / door logic

`edge.has_door = True` is the single source of truth for whether an edge is a passage/door. The renderer and FoundryVTT exporter both read this flag directly. Key invariants:

- Doors are only valid between two unfilled cells.
- `HallwayRandomizer._clear_interior_doors()` runs a post-carve cleanup pass to remove any `has_door=True` flags that ended up floating in open space (i.e. not on a genuine floor↔wall boundary). It uses `_edge_is_interior()` which checks the flanking 2×2 blocks.
- When edit mode paints a cell, all `has_door` flags on its edges are cleared to avoid stale markings.

### Randomizer plugin architecture

All randomizers extend `Randomizer` and override one or more of:
- `randomize_cell(cell)`
- `randomize_dungeon(dungeon)`
- `randomize_grid(grid)`
- `randomize_hallway(hallway)`
- `randomize_room_entrances(room, *args)`
- `randomize_room_size(room, *args)`
- `randomize_room_name(room, *args)`
- `randomize_room_position(room, *args)`

`DungeonRandomizer` is the top-level orchestrator. Its pipeline (in order):
1. Generate rooms (size → name → position → overlap check)
2. `dungeon.emplace_rooms()` — writes room cells into the grid and re-links edges
3. `RoomEntrancesRandomizer` — sets `edge.has_door = True` on perimeter edges (filled-wall side only)
4. `HallwayRandomizer.randomize_dungeon()` — MST + BFS corridor carving, then `_clear_interior_doors()`

Both `RoomEntrancesRandomizer` and `HallwayRandomizer` accept a `door_probability: float` parameter (0.0–1.0). `DungeonRandomizer` threads this through from its own constructor.

---

## Renderers

| Class | Grid type | Output |
|---|---|---|
| `Renderer` | `SquareGrid` | `ax.imshow` of filled-grid boolean array |
| `HexRenderer` | `HexGrid` | `matplotlib.patches.Polygon` hexagons, pointy-top layout with odd-row offset |
| `TexturedRenderer` | `SquareGrid` | Multi-stage PIL image (walls, floors, pillars, moss, shadows, torchlight, doors, wall lines, vignette) |

All accept `render(dungeon, save=False)` and return `(fig, ax)`. `TexturedRenderer` also stores `_last_image` (the PIL Image) for full-res saving.

### TexturedRenderer stages

1. Walls (brick / plank pattern per pack)
2. Floor tiles (room or hallway base colour, with per-stone variation)
3. Pillars (at concave wall corners)
4. Moss & cracks (noise-driven, near walls)
5. Wall shadows (numpy gradient)
6. Torchlight (radial warm glow at door midpoints)
7. Doors (wooden bar + iron pin sprite)
8. Wall outlines (thin dark line on floor side of every floor↔wall edge)
9. Vignette

### Texture packs and room themes

Packs are defined in `_PACKS` in `textured_renderer.py`. Each pack is a dict of RGB tuples and integer parameters. Available packs: `stone`, `cave`, `wood`, `sandstone`. `PACK_NAMES` lists them for UI combo boxes.

`SPACE_THEMES` maps theme keys to floor-colour overrides:
```python
{"default": None, "treasury": (175,145,55), "throne": (88,45,65), ...}
```
`None` means "use the pack's own `floor_room` / `floor_hall` colour". Both `Room` and `Hallway` carry a `theme: str` attribute (default `"default"`). The renderer reads `cell.space.theme` at draw time.

To add a new theme: append to `SPACE_THEMES` in `textured_renderer.py` and add a matching swatch to `_THEME_SWATCHES` in `gui/widgets.py`.

---

## Key Gotchas

- **`Hallway.append_ordered_cell_list` is broken** — it appends to a throw-away `list(self._ordered_cells)` copy. Always build the cell list externally and pass it to `Hallway(ordered_cells=..., name=...)`.
- **`dungeon.emplace_space(space)`** re-links all edges via `grid.link_edges_to_cells()`. Call it after adding cells to a space.
- **Room names must be unique** — `dungeon.add_room(room)` uses `room.name` as the dict key. Rooms default to `name=""`, so always assign unique names before calling `add_room`.
- **`_build_spanning_tree` uses `id(room)`** as keys, not `room.name`, specifically to avoid collisions when rooms share names.
- **`update_figure` destroys the canvas** — `DungeonCanvas.update_figure()` calls `_clear_canvas()` which deletes the `FigureCanvasQTAgg`. Any `mpl_connect` IDs from the previous canvas are invalidated. `EditController` always calls `deactivate()` before `update_figure` and `activate()` after.
- **Slow tests** — rendering tests that write PNG files are marked `@pytest.mark.slow` and skipped by default. Run them with `pytest --runslow`.

---

## Running Tests

```bash
# Fast tests only (default)
python3 -m pytest tests/ -m "not slow"

# Include slow rendering tests
python3 -m pytest tests/ --runslow

# Single file
python3 -m pytest tests/hallway_randomizer_test.py -v
```

Coverage is configured in `.coveragerc` — excludes `tests/` and `__init__.py`, enables `show_missing`.

---

## Code Style

Pre-commit hooks (configured in `.pre-commit-config.yaml`):
- **isort** — import ordering
- **black** — formatting (Python 3.7 target)
- **flake8** — linting

All public methods and classes use type annotations. Docstrings follow Google style.

---

## GUI (`gui/` package)

Run with `python run_gui.py` from the repo root (requires `PyQt5`, `matplotlib`, `Pillow`, `numpy`).

To activate the dev environment: `source venv/bin/activate` from the repo root.

### Files

| File | Role |
|---|---|
| `gui/app.py` | `DonJuanApp(QMainWindow)` — widget tree, QSS stylesheet, menu bar; `main()` entry point |
| `gui/controller.py` | `AppController` — `on_generate/regenerate/save/export/undo`; owns `_dungeon`, `_fig`, `_renderer`, `_edit_controller` |
| `gui/widgets.py` | `ControlPanel` (scrollable generate page + edit page via `QStackedWidget`), `DungeonCanvas`, helpers |
| `gui/edit_controller.py` | `EditController` — cell paint, door toggle, theme stamp, undo stack, cursor/hover feedback |
| `run_gui.py` | Top-level entry point |

### Key design notes

- **Backend**: `matplotlib.use("Qt5Agg")` is set at the top of `widgets.py` before any pyplot import.
- **Canvas embedding**: `DungeonCanvas.update_figure(fig)` replaces the `FigureCanvasQTAgg` widget in-place; the old figure is closed with `plt.close()` to avoid memory leaks.
- **Screen vs. save DPI**: figures are scaled to ≤8 inches at 100 dpi for on-screen display; `TexturedRenderer._last_image.save()` saves the PIL image at full tile resolution.
- **Panel swap**: `ControlPanel` uses a `QStackedWidget` — page 0 is the scrollable generation panel, page 1 is the lean edit panel (theme swatches + hint text). `AppController._on_edit_mode_toggled` calls `cp.set_edit_mode(checked)` to flip the stack.
- **Sync between menu action and panel button**: both call `_on_edit_mode_toggled`; the handler uses `blockSignals` to sync the other widget without feedback loops.
- **Click-to-defocus**: a `_ClickDefocusFilter(QObject)` installed on the `QApplication` clears focus from any input widget when the user clicks elsewhere, so keyboard shortcuts work without manually tabbing away.
- **FoundryVTT hover preview**: `_show_foundry_overlay` draws matplotlib artists (lines for walls/doors, circles for lights) directly on the existing axes; axis limits are saved and restored to prevent canvas resize on hover.

### Edit mode

`EditController` is created fresh after each generation and connected to the new canvas. It handles:

| Interaction | Action |
|---|---|
| Click / drag | Paint cells filled ↔ open; clears stale `has_door` on painted edges |
| Shift + click | Toggle `edge.has_door` on the nearest wall edge of the clicked cell |
| Alt + click | Stamp the selected theme onto the clicked room or hallway |
| Cmd + Z | Undo (snapshot stack, max 20 steps) |

For `TexturedRenderer`, drag-painting shows instant semi-transparent preview rectangles and defers the full re-render to mouse release. For `Renderer`, each cell change triggers an immediate re-render (cheap).

The undo snapshot captures `(filled, space)` per cell and `has_door` per edge across the entire grid.

---

## What's Implemented

| Feature | Status |
|---|---|
| Core model (Dungeon, Room, Hallway, Space, Cell, Edge) | Done |
| SquareGrid + HexGrid | Done |
| Room randomization (size, position, name, entrances) | Done |
| Door probability (0–100%) | Done |
| Hallway randomization (MST + BFS carving) | Done |
| Interior door cleanup pass | Done |
| PNG renderer (`Renderer`) | Done |
| Hex grid renderer (`HexRenderer`) | Done |
| Textured renderer (`TexturedRenderer`, 4 packs) | Done |
| Room / hallway themes (`SPACE_THEMES`) | Done |
| FoundryVTT exporter (walls, doors, lights, JSON + PNG) | Done |
| PyQt5 GUI | Done |
| Edit mode (paint, doors, themes, undo) | Done |

## What's Not Yet Implemented

| Feature | Notes |
|---|---|
| Hex edit mode | Click→cell math for axial hex coords is non-trivial; currently shows "not supported" |
| Loop hallways | `HallwayRandomizer` produces a strict MST; no optional extra connections |
| Multi-floor dungeons | Separate grids linked by staircase edges |
| Re-run hallways after editing | Hand-carved open cells have no `space`, so they aren't wired as `Hallway` objects |
| Undo for theme changes across sessions | Undo stack is reset when a new dungeon is generated |
