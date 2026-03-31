# CLAUDE.md — Development Guide for DonJuan

## Project Overview

DonJuan is a Python package for procedurally generating fantasy dungeons. It is a modular rebuild of the [donjon dungeon generator](https://donjon.bin.sh/fantasy/dungeon/), designed to be composable and extensible. The long-term goals are PNG map rendering, FoundryVTT module export (walls, doors, light sources), and support for custom generation pipelines.

Current version: **0.0.3** (early development). Remote: `https://github.com/tmcclintock/donjuan.git`.

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
├── Room
└── Hallway
    └── _ordered_cells: List[Cell]   # defines the corridor path

Cell (abstract)
├── SquareCell  (_n_sides = 4)
└── HexCell     (_n_sides = 6)

Edge
├── cell1, cell2: Optional[Cell]  # cell1 = left/upper; cell2 = right/lower
├── has_door: bool
└── is_wall: bool  # True if any of: no door, None cell, mismatched filled, different space
```

### Coordinate system

All coordinates are `(y, x)` — row first, column second. `cell.y` is the row index (0 = top), `cell.x` is the column index.

### Cell states

- `cell.filled = True` — solid wall (default for all grid cells)
- `cell.filled = False` — open floor (set by rooms, hallways, and carved corridors)
- `cell.space` — the `Space` this cell belongs to (`None` for plain wall cells)

### Edge / wall logic

`Edge.is_wall` returns `True` if **any** of these conditions holds:
1. `not has_door`
2. `cell1 is None` or `cell2 is None`
3. `cell1.filled != cell2.filled`
4. `cell1.space != cell2.space`

A passage is open only when all four conditions are False (both cells are unfilled, in the same space, and `has_door=True`). Hallway-to-room edges currently satisfy conditions 1 and 3 but not 4 (different spaces) — a known limitation to address before the FoundryVTT exporter.

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
3. `RoomEntrancesRandomizer` — sets `edge.has_door = True` on perimeter edges
4. `HallwayRandomizer.randomize_dungeon()` — MST + BFS corridor carving

### Renderers

| Class | Grid type | Output |
|---|---|---|
| `Renderer` | `SquareGrid` | `ax.imshow` of filled-grid boolean array |
| `HexRenderer` | `HexGrid` | `matplotlib.patches.Polygon` hexagons, pointy-top layout with odd-row offset |

Both accept `render(dungeon, file_path, dpi, save)` and return `(fig, ax)`.

---

## Key Gotchas

- **`Hallway.append_ordered_cell_list` is broken** — it appends to a throw-away `list(self._ordered_cells)` copy. Always build the cell list externally and pass it to `Hallway(ordered_cells=..., name=...)`.
- **`dungeon.emplace_space(space)`** re-links all edges via `grid.link_edges_to_cells()`. Call it after adding cells to a space.
- **Room names must be unique** — `dungeon.add_room(room)` uses `room.name` as the dict key. Rooms default to `name=""`, so always assign unique names before calling `add_room`.
- **`_build_spanning_tree` uses `id(room)`** as keys, not `room.name`, specifically to avoid collisions when rooms share names.
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

The test suite uses `python3` directly (not a conda env). If `pytest` is missing: `pip3 install pytest`.

Coverage is configured in `.coveragerc` — excludes `tests/` and `__init__.py`, enables `show_missing`.

---

## Code Style

Pre-commit hooks (configured in `.pre-commit-config.yaml`):
- **isort** — import ordering
- **black** — formatting (Python 3.7 target)
- **flake8** — linting

All public methods and classes use type annotations. Docstrings follow Google style.

---

## What's Implemented

| Feature | Status |
|---|---|
| Core model (Dungeon, Room, Hallway, Space, Cell, Edge) | Done |
| SquareGrid + HexGrid | Done |
| Room randomization (size, position, name, entrances) | Done |
| Multi-entrance cells (single cell can have >1 entrance edge) | Done |
| Hallway randomization (MST + BFS carving, `HallwayRandomizer`) | Done |
| PNG renderer (`Renderer` for square grids) | Done |
| Hex grid renderer (`HexRenderer` with polygon patches) | Done |
| DoorSpace bug fix (booleans stored as tuples) | Fixed |

## What's Not Yet Implemented

| Feature | Notes |
|---|---|
| **FoundryVTT exporter** | Main stated goal; needs walls, doors, light sources as JSON |
| Light / encounter generation | No dynamic dungeon features yet |
| Hex room/hallway randomizers | `RoomSizeRandomizer` creates `SquareCell`s only |
| `Edge.is_wall` space-equality fix | Cross-space passages (hallway↔room) are never truly "open" |
| Loop hallways | `HallwayRandomizer` produces a strict MST; no optional extra connections |
