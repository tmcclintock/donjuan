"""
Randomizer for generating hallways that connect rooms in a dungeon.
"""
import random
from collections import deque
from typing import Dict, List, Optional, Tuple

from donjuan.dungeon.dungeon import Dungeon
from donjuan.core.hallway import Hallway
from donjuan.core.randomizer import Randomizer
from donjuan.core.room import Room  # noqa: F401 — used in isinstance check below


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
        door_probability: float = 1.0,
    ) -> None:
        super().__init__()
        self.hallway_name_prefix = hallway_name_prefix
        self.max_hallway_attempts = max_hallway_attempts
        self.door_probability = door_probability

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
            if not hallway.cells:
                # Rooms are directly adjacent — open shared boundary edges
                self._open_room_boundary(dungeon, path)
            else:
                self._open_hallway_connections(dungeon, hallway)
            dungeon.add_hallway(hallway)

        # All hallways are now carved. Clear any has_door flags that ended up
        # interior to open space (can happen when a later hallway opened cells
        # adjacent to a door set by an earlier one).
        self._clear_interior_doors(dungeon)

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
            # Only carve cells that are plain walls (no existing space).
            # Room cells (space=Room) are skipped so their space is preserved.
            if cell.space is None:
                cell.filled = False
                # Clear any has_door flags set by RoomEntrancesRandomizer
                # against this wall before it was carved open.
                # _open_hallway_connections will re-establish the correct door
                # on the proper room↔hallway boundary edge afterwards.
                if cell.edges is not None:
                    for edge in cell.edges:
                        if edge is not None:
                            edge.has_door = False
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
            dungeon (Dungeon): the dungeon
            hallway (Hallway): the hallway to connect
        """
        for cell in hallway.cells:
            for edge in cell.edges:
                if edge is None:
                    continue
                neighbor = edge.cell1 if edge.cell2 is cell else edge.cell2
                if neighbor is None:
                    continue
                # Only open where hallway meets a Room, and only when the
                # edge is a genuine wall transition (not floating in open space).
                if not neighbor.filled and isinstance(neighbor.space, Room):
                    if random.random() < self.door_probability:
                        edge.has_door = True

    def _open_room_boundary(
        self, dungeon: Dungeon, path: List[Tuple[int, int]]
    ) -> None:
        """
        When two rooms are directly adjacent (no wall cells between them),
        open the shared edges along the path so the rooms are connected.
        """
        for k in range(len(path) - 1):
            y1, x1 = path[k]
            y2, x2 = path[k + 1]
            c1 = dungeon.grid.cells[y1][x1]
            c2 = dungeon.grid.cells[y2][x2]
            if (
                not c1.filled and isinstance(c1.space, Room)
                and not c2.filled and isinstance(c2.space, Room)
                and c1.space is not c2.space
            ):
                for edge in c1.edges:
                    if edge is None:
                        continue
                    if (edge.cell1 is c1 and edge.cell2 is c2) or \
                       (edge.cell1 is c2 and edge.cell2 is c1):
                        if random.random() < self.door_probability:
                            edge.has_door = True
                        break

    def _clear_interior_doors(self, dungeon: Dungeon) -> None:
        """
        Remove ``has_door`` from any edge that is now interior to open space
        in the fully-carved dungeon.  This catches cases where a later hallway
        opened cells adjacent to a door that was set by an earlier one, leaving
        it floating in the middle of open floor.
        """
        seen: set = set()
        for r in range(dungeon.n_rows):
            for c in range(dungeon.n_cols):
                for edge in dungeon.grid.cells[r][c].edges:
                    if edge is None or id(edge) in seen:
                        continue
                    seen.add(id(edge))
                    if not edge.has_door:
                        continue
                    c1, c2 = edge.cell1, edge.cell2
                    if c1 is None or c2 is None:
                        continue
                    if c1.filled or c2.filled:
                        continue
                    if self._edge_is_interior(c1, c2, dungeon):
                        edge.has_door = False

    @staticmethod
    def _edge_is_interior(c1, c2, dungeon: Dungeon) -> bool:
        """
        Return True if the edge between *c1* and *c2* is flanked by open
        space on at least one side — meaning it lies in open floor rather
        than through a wall, so it should not host a door.

        For a vertical edge (same row) the two flanking 2×2 blocks are the
        ones immediately above and below. For a horizontal edge (same column)
        they are the ones to the left and right.

        Out-of-bounds positions are treated as filled (solid wall), so
        map-border edges are never considered interior.
        """
        cells = dungeon.grid.cells
        rows  = dungeon.n_rows
        cols  = dungeon.n_cols

        def _open(r: int, c: int) -> bool:
            if r < 0 or r >= rows or c < 0 or c >= cols:
                return False
            return not cells[r][c].filled

        r1, x1 = c1.y, c1.x
        r2, x2 = c2.y, c2.x

        if r1 == r2:
            # Vertical edge; flanking blocks are above and below
            r      = r1
            c_left = min(x1, x2)
            block_above = (
                _open(r - 1, c_left) and _open(r - 1, c_left + 1)
                and _open(r,     c_left) and _open(r,     c_left + 1)
            )
            block_below = (
                _open(r,     c_left) and _open(r,     c_left + 1)
                and _open(r + 1, c_left) and _open(r + 1, c_left + 1)
            )
            return block_above or block_below
        else:
            # Horizontal edge; flanking blocks are left and right
            r_top = min(r1, r2)
            c     = x1
            block_left = (
                _open(r_top,     c - 1) and _open(r_top,     c)
                and _open(r_top + 1, c - 1) and _open(r_top + 1, c)
            )
            block_right = (
                _open(r_top,     c) and _open(r_top,     c + 1)
                and _open(r_top + 1, c) and _open(r_top + 1, c + 1)
            )
            return block_left or block_right
