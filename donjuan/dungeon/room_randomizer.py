import random
from math import sqrt
from string import ascii_uppercase
from typing import Set

from donjuan.core.cell import Cell
from donjuan.core.randomizer import Randomizer
from donjuan.core.room import Room
from donjuan.core.room_randomizer import RoomPositionRandomizer, RoomSizeRandomizer


class AlphaNumRoomName(Randomizer):
    """
    Simple room name randomizer that names rooms as alphabetical letters.
    followed by a number.
    Rooms are sequentially named 'A0', 'B0', ... 'Z0', 'A1', 'B1', ...
    """

    def __init__(self):
        super().__init__()
        self.uppercase_letters_iterator = iter(ascii_uppercase)
        self.n = 0

    def next_name(self) -> str:
        try:
            letter = next(self.uppercase_letters_iterator)
        except StopIteration:
            # reset
            self.uppercase_letters_iterator = iter(ascii_uppercase)
            self.n += 1
            letter = next(self.uppercase_letters_iterator)
        return f"{letter}{self.n}"

    def randomize_room_name(self, room: Room, *args) -> None:
        room.set_name(self.next_name())
        return


class RoomEntrancesRandomizer(Randomizer):
    """
    Randomizes the number of entrances on a room. The number is picked to be
    the square root of the number of cells in the room divided by 2 plus 1
    (``N``) plus a uniform random integer from 0 to ``N``.
    """

    def __init__(self, max_attempts: int = 100, door_probability: float = 1.0):
        self.max_attempts = max_attempts
        self.door_probability = door_probability

    def gen_num_entrances(self, cells: Set[Cell]) -> int:
        N = int(sqrt(len(cells))) // 2 + 1
        return N + random.randint(0, N)

    def randomize_room_entrances(self, room: Room, *args) -> None:
        """
        Randomly open edges of cells in a `Room`. The cells in the room must
        already be linked to edges in a `Grid`. See
        :meth:`~donjuan.dungeon.emplace_rooms`.

        .. note::

            This algorithm does not allow for a cell in a room to have two
            entrances.

        Args:
            room (Room): room to try to create entrances for
        """
        n_entrances = self.gen_num_entrances(room.cells)
        i = 0

        # Shuffle cells
        cell_list = random.sample(room.cells, k=len(room.cells))
        for cell in cell_list:
            assert cell.edges is not None, "cell edges not linked"

            # For each wall edge on this cell, open it as an entrance.
            # A single cell may contribute multiple entrances.
            edges = random.sample(cell.edges, k=len(cell.edges))
            for edge in edges:
                if len(room.entrances) >= n_entrances:
                    break
                c1, c2 = edge.cell1, edge.cell2
                # Skip boundary edges (one side is outside the grid)
                if c1 is None or c2 is None:
                    continue
                # Only open an entrance through a solid (filled) wall cell —
                # never between two unfilled cells (interior or adjacent-room edges).
                if not (c1.filled or c2.filled):
                    continue
                if not edge.has_door:
                    if random.random() < self.door_probability:
                        edge.has_door = True
                    room.entrances.append(edge)

            i += 1  # increment attempts
            if i >= self.max_attempts or len(room.entrances) >= n_entrances:
                break
        return
