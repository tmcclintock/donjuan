"""
Randomizer for generating villages with buildings, roads, and trees.
"""
import random
from collections import deque
from typing import Dict, List, Optional, Sequence, Set, Tuple

from donjuan.core.cell import SquareCell
from donjuan.core.hallway import Hallway
from donjuan.core.randomizer import Randomizer
from donjuan.core.room import Room
from donjuan.core.room_randomizer import RoomSizeRandomizer
from donjuan.village.scene import VillageScene, VillageTree


class VillageRandomizer(Randomizer):
    """
    Generates a village by placing buildings, connecting them with roads,
    and scattering trees into the remaining outdoor space.
    """

    def __init__(
        self,
        n_buildings: int = 10,
        min_building_size: int = 2,
        max_building_size: int = 4,
        tree_density: float = 0.06,
        road_branchiness: float = 0.20,
        edge_margin: int = 2,
        building_gap: int = 1,
        max_attempts: int = 200,
    ):
        super().__init__()
        self.n_buildings = n_buildings
        self.tree_density = tree_density
        self.road_branchiness = road_branchiness
        self.edge_margin = edge_margin
        self.building_gap = building_gap
        self.max_attempts = max_attempts
        self._size_randomizer = RoomSizeRandomizer(
            min_size=min_building_size,
            max_size=max_building_size,
            cell_type=SquareCell,
        )

    def randomize(self, scene: VillageScene) -> None:
        self._place_buildings(scene)
        self._add_building_entrances(scene)
        self._build_road_network(scene)
        self._place_trees(scene)

    def _place_buildings(self, scene: VillageScene) -> None:
        reserved = self._reserved_plaza(scene)
        for idx in range(self.n_buildings):
            placed = False
            for _ in range(self.max_attempts):
                building = Room(name=f"B{idx}", theme="default")
                self._size_randomizer.randomize_room_size(building)
                height, width = self._room_dims(building)
                max_y = scene.n_rows - height - self.edge_margin
                max_x = scene.n_cols - width - self.edge_margin
                if max_y < self.edge_margin or max_x < self.edge_margin:
                    break
                y = random.randint(self.edge_margin, max_y)
                x = random.randint(self.edge_margin, max_x)
                building.shift_vertical(y)
                building.shift_horizontal(x)
                coords = set(building.cell_coordinates)
                if coords & reserved:
                    continue
                if self._overlaps_with_gap(building, scene.buildings.values()):
                    continue
                scene.emplace_space(building)
                scene.add_building(building)
                placed = True
                break
            if not placed:
                break

    def _add_building_entrances(self, scene: VillageScene) -> None:
        cy, cx = scene.n_rows / 2.0, scene.n_cols / 2.0
        for building in scene.buildings.values():
            best = None
            best_dist = None
            for cell in building.cells:
                for idx, edge in enumerate(cell.edges):
                    if edge is None:
                        continue
                    c1, c2 = edge.cell1, edge.cell2
                    neighbor = c1 if c2 is cell else c2
                    if neighbor is None:
                        continue
                    if neighbor.space is building:
                        continue
                    if neighbor.filled:
                        continue
                    ny, nx = neighbor.y, neighbor.x
                    dist = abs(ny - cy) + abs(nx - cx)
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best = (cell, edge, neighbor, idx)
            if best is None:
                continue
            _cell, edge, neighbor, _idx = best
            edge.has_door = True
            building.entrances.append(edge)
            scene.building_entrances[building.name] = (neighbor.y, neighbor.x)

    def _build_road_network(self, scene: VillageScene) -> None:
        plaza_cells = self._plaza_cells(scene)
        self._emplace_road(scene, plaza_cells, "R0")
        network: Set[Tuple[int, int]] = set((cell.y, cell.x) for cell in plaza_cells)

        entrances = {
            name: coord for name, coord in scene.building_entrances.items()
            if coord is not None
        }
        if not entrances:
            return

        connected = set()
        names = list(entrances.keys())
        names.sort(key=lambda n: self._manhattan(entrances[n], self._plaza_center(scene)))

        for idx, name in enumerate(names, start=1):
            start = entrances[name]
            path = self._bfs_to_targets(scene, start, network)
            if path is None:
                continue
            road_cells = self._coords_to_cells(scene, path)
            self._emplace_road(scene, road_cells, f"R{idx}")
            network.update(path)
            connected.add(name)

        extra_idx = len(scene.roads)
        for a_name, b_name in self._extra_pairs(list(connected)):
            if random.random() > self.road_branchiness:
                continue
            path = self._bfs_between(scene, entrances[a_name], entrances[b_name])
            if path is None:
                continue
            road_cells = self._coords_to_cells(scene, path)
            self._emplace_road(scene, road_cells, f"R{extra_idx}")
            network.update(path)
            extra_idx += 1

    def _place_trees(self, scene: VillageScene) -> None:
        candidates = []
        for r in range(scene.n_rows):
            for c in range(scene.n_cols):
                cell = scene.grid.cells[r][c]
                if cell.space is not None:
                    continue
                if (r, c) in self._reserved_plaza(scene):
                    continue
                candidates.append((r, c))

        random.shuffle(candidates)
        target = int(self.tree_density * len(candidates))
        placed = []
        for r, c in candidates:
            if len(placed) >= target:
                break
            if any(abs(r - pr) + abs(c - pc) < 2 for pr, pc in placed):
                continue
            cell = scene.grid.cells[r][c]
            cell.filled = True
            tree = VillageTree(cells={cell}, name=f"T{len(placed)}")
            scene.emplace_space(tree)
            scene.add_tree(tree)
            placed.append((r, c))

    def _emplace_road(
        self, scene: VillageScene, cells: Sequence[SquareCell], name: str
    ) -> None:
        if not cells:
            return
        road = Hallway(ordered_cells=list(cells), name=name, theme="road")
        scene.emplace_space(road)
        scene.add_road(road)

    def _coords_to_cells(
        self, scene: VillageScene, coords: Sequence[Tuple[int, int]]
    ) -> List[SquareCell]:
        cells = []
        for y, x in coords:
            cell = scene.grid.cells[y][x]
            if isinstance(cell.space, Room) or cell.filled:
                continue
            cells.append(cell)
        return cells

    def _bfs_to_targets(
        self,
        scene: VillageScene,
        start: Tuple[int, int],
        targets: Set[Tuple[int, int]],
    ) -> Optional[List[Tuple[int, int]]]:
        queue = deque([start])
        came_from = {start: None}

        while queue:
            current = queue.popleft()
            if current in targets:
                return self._reconstruct_path(came_from, current)
            for neighbor in self._neighbors(scene, current):
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return None

    def _bfs_between(
        self,
        scene: VillageScene,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> Optional[List[Tuple[int, int]]]:
        queue = deque([start])
        came_from = {start: None}

        while queue:
            current = queue.popleft()
            if current == end:
                return self._reconstruct_path(came_from, current)
            for neighbor in self._neighbors(scene, current):
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return None

    def _neighbors(
        self, scene: VillageScene, coord: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        y, x = coord
        out = []
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < scene.n_rows and 0 <= nx < scene.n_cols):
                continue
            cell = scene.grid.cells[ny][nx]
            if isinstance(cell.space, Room):
                continue
            if cell.filled:
                continue
            out.append((ny, nx))
        return out

    def _extra_pairs(self, names: List[str]) -> List[Tuple[str, str]]:
        pairs = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pairs.append((names[i], names[j]))
        random.shuffle(pairs)
        return pairs[:max(1, len(names) // 3)] if pairs else []

    def _reconstruct_path(
        self, came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]], current
    ) -> List[Tuple[int, int]]:
        path = []
        node = current
        while node is not None:
            path.append(node)
            node = came_from[node]
        path.reverse()
        return path

    def _reserved_plaza(self, scene: VillageScene) -> Set[Tuple[int, int]]:
        return set((cell.y, cell.x) for cell in self._plaza_cells(scene))

    def _plaza_cells(self, scene: VillageScene) -> List[SquareCell]:
        cy, cx = self._plaza_center(scene)
        cells = []
        for y in range(max(0, cy - 1), min(scene.n_rows, cy + 2)):
            for x in range(max(0, cx - 1), min(scene.n_cols, cx + 2)):
                cells.append(scene.grid.cells[y][x])
        return cells

    def _plaza_center(self, scene: VillageScene) -> Tuple[int, int]:
        return (scene.n_rows // 2, scene.n_cols // 2)

    def _room_dims(self, room: Room) -> Tuple[int, int]:
        ys = [c.y for c in room.cells]
        xs = [c.x for c in room.cells]
        return max(ys) - min(ys) + 1, max(xs) - min(xs) + 1

    def _expanded_coords(self, room: Room) -> Set[Tuple[int, int]]:
        coords = set()
        for y, x in room.cell_coordinates:
            for dy in range(-self.building_gap, self.building_gap + 1):
                for dx in range(-self.building_gap, self.building_gap + 1):
                    coords.add((y + dy, x + dx))
        return coords

    def _overlaps_with_gap(self, room: Room, others: Sequence[Room]) -> bool:
        expanded = self._expanded_coords(room)
        for other in others:
            if expanded & set(other.cell_coordinates):
                return True
            if room.cell_coordinates & self._expanded_coords(other):
                return True
        return False

    def _manhattan(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
