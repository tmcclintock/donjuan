import random
from string import ascii_uppercase
from typing import Type

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
