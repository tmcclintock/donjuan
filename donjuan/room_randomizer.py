import random
from math import sqrt
from string import ascii_uppercase
from typing import Set, Type

from donjuan.cell import Cell, SquareCell
from donjuan.dungeon import Dungeon
from donjuan.randomizer import Randomizer
from donjuan.room import Room


class RoomSizeRandomizer(Randomizer):
    """
    Randomize the size of a `Room`.
    """

    def __init__(
        self, min_size: int = 2, max_size: int = 4, cell_type: Type[Cell] = SquareCell
    ):
        super().__init__()
        assert issubclass(cell_type, Cell)
        assert min_size >= 1, f"{min_size}"
        assert max_size >= min_size, f"{max_size} < {min_size}"
        assert max_size <= 100, f"{max_size}"  # arbitrary
        self.min_size = min_size
        self.max_size = max_size
        self.cell_type = cell_type

    def randomize_room_size(self, room: Room) -> None:
        """
        Randomly determine the size of the room, and set the cells of
        the room to a 2D array of unfilled cells of that size.
        """
        # Draw the dimensions
        height = random.randint(self.min_size, self.max_size)
        width = random.randint(self.min_size, self.max_size)

        # Create empty cells and set them in the room
        cells = [
            self.cell_type(filled=False, coordinates=(i, j))
            for j in range(height)
            for i in range(width)
        ]
        room.add_cells(cells)
        return


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


class RoomPositionRandomizer(Randomizer):
    """
    Randomly shift a room, assuming its left edge is at column 0 and it's top
    edge is at row 0.
    """

    def randomize_room_position(self, room: Room, dungeon: Dungeon) -> None:
        """
        Args:
            room (Room): room to move around
            dungeon (Dungeon): dungeon to move the room around in
        """
        # Determing the right-most and bottom-most cells of the room
        bottom = max(room.cell_coordinates, key=lambda x: x[0])[0]
        right = max(room.cell_coordinates, key=lambda x: x[1])[1]
        # Draw random positions and shift
        room.shift_horizontal(random.randint(0, dungeon.n_cols - right - 1))
        room.shift_vertical(random.randint(0, dungeon.n_rows - bottom - 1))
        return


class RoomEntrancesRandomizer(Randomizer):
    """
    Randomizes the number of entrances on a room. The number is picked to be
    the square root of the number of cells in the room divided by 2 plus 1
    (``N``) plus a uniform random integer from 0 to ``N``.
    """

    def __init__(self, max_attempts: int = 100):
        self.max_attempts = max_attempts

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

            # If an edge has a wall, set it to having a door
            # and record it
            # TODO: objectify this method so that cells can have many entrances
            edges = random.sample(cell.edges, k=len(cell.edges))
            for edge in edges:
                if edge.is_wall:
                    edge.has_door = True
                    room.entrances.append(edge)
                    break

            i += 1  # increment attempts
            if i >= self.max_attempts or len(room.entrances) >= n_entrances:
                break
        return
