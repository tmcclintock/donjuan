"""
Village scene type: enterable buildings linked by roads with scattered trees.
"""
from typing import Dict, Iterable, Optional

from donjuan.core.scene import Scene
from donjuan.core.space import Space
from donjuan.core.room import Room
from donjuan.core.hallway import Hallway


class VillageTree(Space):
    """A single filled tree cell inside or around the village."""

    pass


class VillageScene(Scene):
    """
    A village battle-map scene with enterable buildings, roads, and trees.
    """

    def __init__(self, n_rows: int = 24, n_cols: int = 24, grid=None):
        from donjuan.core.grid import SquareGrid

        super().__init__(
            grid=grid or SquareGrid(n_rows, n_cols),
            scene_type="village",
        )
        self.buildings: Dict[str, Room] = {}
        self.roads: Dict[str, Hallway] = {}
        self.trees: Dict[str, VillageTree] = {}
        self.building_entrances = {}

        for r in range(self.n_rows):
            for c in range(self.n_cols):
                self.grid.cells[r][c].filled = False

    def add_building(self, building: Room) -> None:
        self.buildings[str(building.name)] = building

    def add_road(self, road: Hallway) -> None:
        self.roads[str(road.name)] = road

    def add_tree(self, tree: VillageTree) -> None:
        self.trees[str(tree.name)] = tree

    def next_building_name(self) -> str:
        return self._next_name(self.buildings, "B")

    def next_road_name(self) -> str:
        return self._next_name(self.roads, "R")

    def next_tree_name(self) -> str:
        return self._next_name(self.trees, "T")

    def remove_building(self, building: Room) -> None:
        self.buildings.pop(str(building.name), None)
        self.building_entrances.pop(str(building.name), None)

    def remove_road(self, road: Hallway) -> None:
        self.roads.pop(str(road.name), None)

    def remove_tree(self, tree: VillageTree) -> None:
        self.trees.pop(str(tree.name), None)

    def rebuild_space_membership(self, space: Space) -> None:
        cells = set()
        ordered_cells = []
        for r in range(self.n_rows):
            for c in range(self.n_cols):
                cell = self.grid.cells[r][c]
                if cell.space is space:
                    cells.add(cell)
                    ordered_cells.append(cell)
        space._cells = cells
        if isinstance(space, Hallway):
            ordered_cells.sort(key=lambda cell: (cell.y, cell.x))
            space._ordered_cells = ordered_cells
        space.reset_cell_coordinates()
        if isinstance(space, Room):
            self._sync_building_entrances(space)

    def prune_empty_space(self, space: Optional[Space]) -> None:
        if space is None:
            return
        self.rebuild_space_membership(space)
        if space.cells:
            return
        if isinstance(space, Room):
            self.remove_building(space)
        elif isinstance(space, Hallway):
            self.remove_road(space)
        elif isinstance(space, VillageTree):
            self.remove_tree(space)

    def clear_doors_for_cell(self, cell) -> None:
        for edge in cell.edges or []:
            if edge is not None:
                edge.has_door = False
        self.rebuild_all_building_entrances()

    def rebuild_all_building_entrances(self) -> None:
        self.building_entrances = {}
        for building in self.buildings.values():
            self._sync_building_entrances(building)

    def _sync_building_entrances(self, building: Room) -> None:
        entrances = []
        for cell in building.cells:
            for edge in cell.edges or []:
                if edge is None or not edge.has_door:
                    continue
                c1, c2 = edge.cell1, edge.cell2
                if c1 is None or c2 is None:
                    continue
                if c1.space is building and c2.space is building:
                    continue
                if not (c1.space is building or c2.space is building):
                    continue
                entrances.append(edge)
        # Preserve a deterministic order for rendering/tests.
        entrances = sorted(
            set(entrances),
            key=lambda edge: (
                min(
                    edge.cell1.y if edge.cell1 is not None else 10**9,
                    edge.cell2.y if edge.cell2 is not None else 10**9,
                ),
                min(
                    edge.cell1.x if edge.cell1 is not None else 10**9,
                    edge.cell2.x if edge.cell2 is not None else 10**9,
                ),
            ),
        )
        building.entrances = entrances

        if not entrances:
            self.building_entrances.pop(str(building.name), None)
            return

        edge = entrances[0]
        c1, c2 = edge.cell1, edge.cell2
        other = c2 if c1 is not None and c1.space is building else c1
        if other is not None:
            self.building_entrances[str(building.name)] = (other.y, other.x)

    def _next_name(self, registry: Dict[str, Space], prefix: str) -> str:
        idx = 0
        while f"{prefix}{idx}" in registry:
            idx += 1
        return f"{prefix}{idx}"
