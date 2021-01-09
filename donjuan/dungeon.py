from typing import Dict, List, Optional, Union

from donjuan.edge import Edge
from donjuan.grid import Grid, SquareGrid
from donjuan.hallway import Hallway
from donjuan.room import Room
from donjuan.space import Space


class Dungeon:
    def __init__(
        self,
        n_rows: Optional[int] = 5,
        n_cols: Optional[int] = 5,
        grid: Optional[Grid] = None,
        rooms: Optional[Dict[str, Room]] = None,
        hallways: Optional[Dict[str, Hallway]] = None,
        randomizers: Optional[List["Randomizer"]] = None,
    ):
        self._grid = grid or SquareGrid(n_rows, n_cols)
        self._rooms = rooms or {}
        self._hallways = hallways or {}
        self._randomizers = randomizers or []
        self.room_entrances: Dict[Union[int, str], List[Edge]] = {}

    def add_room(self, room: Room) -> None:
        self._rooms[room.name] = room

    def add_hallway(self, hallway: Hallway) -> None:
        self.hallways[hallway.name] = hallway

    @property
    def grid(self) -> Grid:
        return self._grid

    @property
    def hallways(self) -> Dict[str, Hallway]:
        return self._hallways

    @property
    def n_cols(self) -> int:
        return self.grid.n_cols

    @property
    def n_rows(self) -> int:
        return self.grid.n_rows

    @property
    def randomizers(self) -> List["Randomizer"]:
        return self._randomizers

    @property
    def rooms(self) -> Dict[str, Room]:
        return self._rooms

    def randomize(self) -> None:
        """
        For each item in :attr:`randomizers`, run the
        :meth:`Randomizer.randomize_dungeon` method on this dungeon.
        """
        for rng in self.randomizers:
            rng.randomize_dungeon(self)
        return

    def emplace_rooms(self) -> None:
        """
        Replace the cells in the :attr:`grid` with the cells of the
        :attr:`rooms`.
        """

        for room_name, room in self.rooms.items():
            self.emplace_space(room)
        return

    def emplace_space(self, space: Space) -> None:
        """
        Replace the cells in the :attr:`grid` with the cells of the `Space`,
        and automatically link them with the `Edge`s in the `Grid`.

        Args:
            space (Space): room to emplace in the :attr:`grid`
        """
        for cell in space.cells:
            self.grid.cells[cell.y][cell.x] = cell
        self.grid.link_edges_to_cells()
        assert cell.edges is not None, "problem linking edges to cell"
        return
