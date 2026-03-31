"""
Randomizer for generating hallways that connect rooms in a dungeon.
"""
from collections import deque
from typing import Dict, List, Optional, Tuple

from donjuan.dungeon import Dungeon
from donjuan.hallway import Hallway
from donjuan.randomizer import Randomizer
from donjuan.room import Room


class HallwayRandomizer(Randomizer):
    """
    Connects rooms in a dungeon with hallways using a minimum spanning tree
    (Prim's algorithm) to ensure full connectivity, and BFS to carve each
    corridor through the grid.

    Args:
        hallway_name_prefix (str): prefix used when naming generated hallways.
            Hallways will be named ``{prefix}0``, ``{prefix}1``, etc.
        max_hallway_attempts (int): maximum number of connection attempts
            before giving up on a pair of rooms.
    """

    def __init__(
        self,
        hallway_name_prefix: str = "H",
        max_hallway_attempts: int = 50,
    ) -> None:
        super().__init__()
        self.hallway_name_prefix = hallway_name_prefix
        self.max_hallway_attempts = max_hallway_attempts

    def randomize_hallway(self, hallway: Hallway) -> None:
        """No-op: satisfies the base :class:`Randomizer` protocol."""
        pass  # pragma: no cover

    def randomize_dungeon(self, dungeon: Dungeon) -> None:
        """
        Connect all rooms in the dungeon with hallways.

        Rooms are connected using a minimum spanning tree so every room is
        reachable with the fewest hallways. Each individual hallway is carved
        via BFS, taking the shortest path through the grid.

        Args:
            dungeon (Dungeon): dungeon whose rooms should be connected
        """
        rooms = list(dungeon.rooms.values())
        if len(rooms) < 2:
            return

        pairs = self._build_spanning_tree(rooms)

        for i, (room_a, room_b) in enumerate(pairs):
            start = self._room_center(room_a)
            end = self._room_center(room_b)
            path = self._bfs_path(dungeon, start, end)
            if path is None:
                continue
            name = f"{self.hallway_name_prefix}{i}"
            hallway = self._carve_hallway(dungeon, path, name)
            self._open_hallway_connections(dungeon, hallway)
            dungeon.add_hallway(hallway)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _room_center(self, room: Room) -> Tuple[int, int]:
        """Return the approximate center ``(y, x)`` of a room."""
        ys = [c.y for c in room.cells]
        xs = [c.x for c in room.cells]
        return (sum(ys) // len(ys), sum(xs) // len(xs))

    def _build_spanning_tree(
        self, rooms: List[Room]
    ) -> List[Tuple[Room, Room]]:
        """
        Build a minimum spanning tree over rooms using Prim's algorithm with
        Manhattan distance between room centers.

        Returns:
            List of ``(room_a, room_b)`` pairs to connect, length N-1.
        """
        # Use object id as key so rooms with the same name don't collide
        centers: Dict[int, Tuple[int, int]] = {
            id(room): self._room_center(room) for room in rooms
        }

        visited: Dict[int, Room] = {id(rooms[0]): rooms[0]}
        unvisited: Dict[int, Room] = {id(room): room for room in rooms[1:]}
        pairs: List[Tuple[Room, Room]] = []

        while unvisited:
            best_dist = None
            best_v: Optional[Room] = None
            best_u: Optional[Room] = None

            for v_id, v_room in visited.items():
                cy, cx = centers[v_id]
                for u_id, u_room in unvisited.items():
                    uy, ux = centers[u_id]
                    dist = abs(cy - uy) + abs(cx - ux)
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_v = v_room
                        best_u = u_room

            if best_u is None:
                break

            pairs.append((best_v, best_u))
            visited[id(best_u)] = best_u
            del unvisited[id(best_u)]

        return pairs

    def _bfs_path(
        self,
        dungeon: Dungeon,
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find the shortest path from ``start`` to ``end`` on the dungeon grid
        using BFS. All cells are treated as walkable so that the hallway can
        carve through filled wall cells.

        Returns:
            Ordered list of ``(y, x)`` coordinates from start to end,
            or ``None`` if no path exists.
        """
        if start == end:
            return [start]

        queue: deque = deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
            start: None
        }

        while queue:
            current = queue.popleft()
            if current == end:
                # Back-trace
                path = []
                node: Optional[Tuple[int, int]] = current
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            cy, cx = current
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy + dy, cx + dx
                if (
                    0 <= ny < dungeon.n_rows
                    and 0 <= nx < dungeon.n_cols
                    and (ny, nx) not in came_from
                ):
                    came_from[(ny, nx)] = current
                    queue.append((ny, nx))

        return None  # no path found

    def _carve_hallway(
        self,
        dungeon: Dungeon,
        path: List[Tuple[int, int]],
        name: str,
    ) -> Hallway:
        """
        Build a :class:`Hallway` by carving the BFS path through the dungeon
        grid. Cells already belonging to a room are skipped; plain wall cells
        are set to unfilled and added to the hallway.

        Args:
            dungeon (Dungeon): dungeon to carve through
            path (List[Tuple[int, int]]): ordered ``(y, x)`` coordinates
            name (str): name for the new hallway

        Returns:
            The newly created and emplaced :class:`Hallway`.
        """
        hallway_cells = []
        for y, x in path:
            cell = dungeon.grid.cells[y][x]
            # Only claim cells that are not already part of a room
            if cell.space is None:
                cell.filled = False
                hallway_cells.append(cell)

        hallway = Hallway(ordered_cells=hallway_cells, name=name)
        dungeon.emplace_space(hallway)
        return hallway

    def _open_hallway_connections(
        self, dungeon: Dungeon, hallway: Hallway
    ) -> None:
        """
        Open edges between hallway cells and adjacent unfilled room cells by
        setting ``has_door = True`` on those edges.

        Args:
            dungeon (Dungeon): the dungeon (unused, kept for API symmetry)
            hallway (Hallway): the hallway to connect
        """
        for cell in hallway.cells:
            for edge in cell.edges:
                if edge is None:
                    continue
                # Determine the neighbour on the other side of the edge
                neighbor = (
                    edge.cell1 if edge.cell2 is cell else edge.cell2
                )
                if neighbor is None:
                    continue
                # Open the passage if the neighbour is an unfilled non-hallway cell
                if not neighbor.filled and neighbor.space is not hallway:
                    edge.has_door = True
