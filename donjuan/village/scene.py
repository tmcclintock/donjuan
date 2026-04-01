"""
Village scene type: enterable buildings linked by roads with scattered trees.
"""
from typing import Dict

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
