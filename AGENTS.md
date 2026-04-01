# AGENTS.md — Development Guide for DonJuan

## Project Overview

DonJuan is a Python package for procedurally generating tabletop battle-map
scenes. It started as a modular rebuild of the
[donjon dungeon generator](https://donjon.bin.sh/fantasy/dungeon/), and now
supports multiple scene types with dedicated renderers, FoundryVTT export, and
a PyQt5 desktop GUI.

Current version: **0.0.3** (active development). Remote:
`https://github.com/tmcclintock/donjuan.git`.

Implemented scene types:
- `dungeon`
- `forest`
- `camp`
- `village`

---

## Architecture

### Package layout

```text
donjuan/
├── core/      # shared cells, edges, grids, spaces, exporters, reusable Room/Hallway
├── dungeon/   # dungeon-specific generation, rendering, export
├── forest/    # forest-specific generation, rendering, export
├── camp/      # camp-specific generation, rendering, export
└── village/   # village-specific generation, rendering, export
```

### Shared core model

```text
Scene
├── Grid (SquareGrid | HexGrid)
│   ├── cells: List[List[Cell]]
│   └── edges: List[List[List[Edge]]]
└── scene_type: str

Space (abstract)
├── Room      — reusable enterable interior/building space
└── Hallway   — reusable ordered path/road/corridor space

Cell (abstract)
├── SquareCell  (_n_sides = 4)
└── HexCell     (_n_sides = 6)

Edge
├── cell1, cell2: Optional[Cell]
└── has_door: bool

DoorSpace
├── Archway
├── Door
└── Portcullis
```

Scene-specific containers:

- `Dungeon` keeps `rooms`, `hallways`, and `room_entrances`
- `ForestScene` keeps `trees` and `undergrowth`
- `CampScene` keeps `fires`, `tents`, `paths`, and `trees`
- `VillageScene` keeps `buildings`, `roads`, `trees`, and `building_entrances`

### Coordinate system

All coordinates are `(y, x)` — row first, column second. `cell.y` is the row
index (0 = top), `cell.x` is the column index.

### Cell states

- `cell.filled = True` — solid blocker / wall / tree obstacle
- `cell.filled = False` — open traversable space
- `cell.space` — the `Space` this cell belongs to (`None` for plain terrain)

### Edge / door logic

`edge.has_door = True` is the single source of truth for whether an edge is a
passage/door. Renderers and FoundryVTT exporters read this flag directly.

Key invariants:
- Doors are only valid between two unfilled cells.
- `HallwayRandomizer._clear_interior_doors()` removes `has_door=True` flags
  that become interior to open space.
- When dungeon edit mode paints a cell, all `has_door` flags on its edges are
  cleared to avoid stale markings.

### Randomizer architecture

All randomizers extend `Randomizer` and may override:
- `randomize_cell(cell)`
- `randomize_dungeon(dungeon)`
- `randomize_grid(grid)`
- `randomize_hallway(hallway)`
- `randomize_room_entrances(room, *args)`
- `randomize_room_size(room, *args)`
- `randomize_room_name(room, *args)`
- `randomize_room_position(room, *args)`

Reusable randomizers in `core`:
- `RoomSizeRandomizer`
- `RoomPositionRandomizer`

Dungeon-specific randomizers in `dungeon`:
- `AlphaNumRoomName`
- `RoomEntrancesRandomizer`
- `HallwayRandomizer`
- `DungeonRandomizer`

Village generation uses shared `Room` / `Hallway` primitives plus a dedicated
`VillageRandomizer`.

---

## Renderers

| Class | Scene / grid | Output |
|---|---|---|
| `Renderer` | generic square-grid dungeon | `ax.imshow` of filled-grid boolean array |
| `HexRenderer` | dungeon hex grid | matplotlib hex polygons |
| `TexturedRenderer` | dungeon square grid | PIL-based dungeon texture pipeline |
| `ForestRenderer` | forest | textured outdoor forest image |
| `CampRenderer` | camp | textured camp image |
| `VillageRenderer` | village | textured village image |

All accept `render(scene, save=False)` and return `(fig, ax)`. PIL-backed
renderers store `_last_image` for full-resolution saves.

### Dungeon texture packs and themes

Dungeon packs are defined in `donjuan/dungeon/renderer.py`.
Available packs:
- `stone`
- `cave`
- `wood`
- `sandstone`

`SPACE_THEMES` maps theme keys to dungeon floor-colour overrides.

To add a new dungeon theme:
1. append to `SPACE_THEMES` in `donjuan/dungeon/renderer.py`
2. add a matching swatch to `_THEME_SWATCHES` in `gui/widgets.py`

---

## FoundryVTT export

Shared export base:
- `donjuan/core/exporter.py` → `FoundryExporter`

Scene-specific exporters:
- `DungeonExporter`
- `ForestExporter`
- `CampExporter`
- `VillageExporter`

Current export semantics:
- Dungeon: solid walls, doors, torch lights
- Forest: circular tree blockers, movement-only undergrowth walls
- Camp: circular tree blockers, movement-only tent walls, fire lights
- Village: building perimeter walls/doors, circular tree blockers, open roads

---

## Key Gotchas

- **`Hallway.append_ordered_cell_list` is broken** — it appends to a throw-away
  `list(self._ordered_cells)` copy. Always build the cell list externally and
  pass it to `Hallway(ordered_cells=..., name=...)`.
- **`scene.emplace_space(space)`** re-links all edges via
  `grid.link_edges_to_cells()`. Call it after adding cells to a space.
- **Room/building names must be unique** — scene containers use `name` as the
  dict key.
- **`_build_spanning_tree` uses `id(room)`** instead of `room.name` to avoid
  collisions when names repeat.
- **`DungeonCanvas.update_figure()` destroys the canvas** — old matplotlib
  connection IDs become invalid after a rerender.
- **Slow tests** — rendering tests that write PNG files are marked
  `@pytest.mark.slow` and skipped by default. Run them with `pytest --runslow`.

---

## Running Tests

```bash
# Fast tests only (default)
python3 -m pytest tests/ -m "not slow"

# Include slow rendering tests
python3 -m pytest tests/ --runslow

# Single file
python3 -m pytest tests/village_test.py -v
```

Coverage is configured in `.coveragerc`.

---

## Code Style

Pre-commit hooks (configured in `.pre-commit-config.yaml`):
- **isort** — import ordering
- **black** — formatting (Python 3.7 target)
- **flake8** — linting

All public methods and classes use type annotations. Docstrings follow Google
style.

---

## GUI (`gui/` package)

Run with `python run_gui.py` from the repo root (requires `PyQt5`,
`matplotlib`, `Pillow`, `numpy`).

### Files

| File | Role |
|---|---|
| `gui/app.py` | `DonJuanApp(QMainWindow)` — widget tree, menu bar, entry point |
| `gui/controller.py` | `AppController` — generation, export, save, undo, overlay |
| `gui/widgets.py` | `ControlPanel`, `DungeonCanvas`, shared GUI widgets |
| `gui/edit_controller.py` | dungeon-only edit mode |
| `run_gui.py` | top-level entry point |

### Current GUI behavior

- Scene selector includes `Dungeon`, `Forest`, `Camp`, and `Village`
- Foundry export is available for all four scene types
- Foundry hover preview draws exported walls/doors/lights on top of the render
- Edit mode is currently dungeon-only

### Edit mode

`EditController` is recreated after each dungeon generation. It supports:

| Interaction | Action |
|---|---|
| Click / drag | Paint cells filled ↔ open |
| Shift + click | Toggle `edge.has_door` |
| Alt + click | Apply the selected dungeon theme |
| Cmd + Z | Undo (max 20 snapshots) |

The undo snapshot captures `(filled, space)` per cell and `has_door` per edge.

---

## What's Implemented

| Feature | Status |
|---|---|
| Shared core model (`Scene`, `Space`, `Cell`, `Edge`, `Room`, `Hallway`, `DoorSpace`) | Done |
| SquareGrid + HexGrid | Done |
| Dungeon generation/render/export | Done |
| Forest generation/render/export | Done |
| Camp generation/render/export | Done |
| Village generation/render/export | Done |
| Foundry movement-only terrain walls | Done |
| PyQt5 GUI with 4 scene types | Done |
| Dungeon edit mode | Done |

## What's Not Yet Implemented

| Feature | Notes |
|---|---|
| Hex edit mode | Click→cell math for axial hex coords is non-trivial |
| Loop hallways in dungeons | `HallwayRandomizer` currently produces a strict MST |
| Multi-floor dungeons | No staircase-linked multi-grid model yet |
| Non-dungeon edit mode | Forest/camp/village do not yet have dedicated edit interactions |
| Re-run hallways after dungeon editing | Hand-carved open cells without `space` are not rewired as hallways |
