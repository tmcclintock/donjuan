import random
from string import ascii_uppercase
from typing import Optional, Type

from donjuan import Randomizer
from donjuan.cell import Cell, SquareCell
from donjuan.dungeon import Dungeon
from donjuan.room import Room


class RoomRandomizer(Randomizer):
    """
    Base class for randomizing properties of `Room` objects.
    """

    pass


class RoomSizeRandomizer(RoomRandomizer):
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
            [self.cell_type(filled=False, coordinates=(i, j)) for j in range(height)]
            for i in range(width)
        ]
        room.set_cells(cells)
        return


class AlphaNumRoomName(RoomRandomizer):
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


class RoomPositionRandomizer(RoomRandomizer):
    """
    Randomly shift a room, assuming it has :attr:`n_cols`
    and :attr:`n_rows` attributes.
    """

    def randomize_room_position(self, room: Room, dungeon: Dungeon) -> None:
        # Draw random positions and shift
        room.shift_horizontal(random.randint(0, dungeon.n_cols - room.n_cols))
        room.shift_vertical(random.randint(0, dungeon.n_rows - room.n_rows))
        return


class DungeonRoomRandomizer(Randomizer):
    """
    Randomize a dungeon by first creating rooms and then applying
    :meth:`RoomRandomizer.room_randomize` to them.

    Args:
        room_size_randomizer (RoomRandomizer): randomizer for the room size.
            It must have a 'max_size' attribute.
        room_name_randomizer (RoomRandomizer): randomizer for the room name
        room_position_randomizer (RoomRandomizer): randomizer for the room
            position
        max_num_rooms (Optional[int]): maximum number of rooms to draw,
            if ``None` then default to the :attr:`max_room_attempts`. See
            :meth:`DungeonRoomRandomizer.get_number_of_rooms` for details.
        max_room_attempts (int, optional): default is 100. Maximum number of
            attempts to generate rooms.
    """

    def __init__(
        self,
        room_size_randomizer: RoomRandomizer = RoomSizeRandomizer(),
        room_name_randomizer: RoomRandomizer = AlphaNumRoomName(),
        room_position_randomizer: RoomRandomizer = RoomPositionRandomizer(),
        max_num_rooms: Optional[int] = None,
        max_room_attempts: int = 100,
    ):
        super().__init__()
        self.room_size_randomizer = room_size_randomizer
        assert hasattr(self.room_size_randomizer, "max_size")
        self.room_name_randomizer = room_name_randomizer
        self.room_position_randomizer = room_position_randomizer
        self.max_num_rooms = max_num_rooms or max_room_attempts
        self.max_room_attempts = max_room_attempts

    def get_number_of_rooms(self, dungeon_n_rows: int, dungeon_n_cols: int) -> int:
        """
        Randomly determine the number of rooms based on the size
        of the in coming grid or the :attr:`max_num_rooms` attribute,
        whichever is less.

        Args:
            dungeon_n_rows (int): number of rows
            dungeon_n_cols (int): number of columns
        """
        dungeon_area = dungeon_n_rows * dungeon_n_cols
        max_room_area = self.room_size_randomizer.max_size ** 2
        return min(self.max_num_rooms, dungeon_area // max_room_area)

    def randomize_dungeon(self, dungeon: Dungeon) -> None:
        """
        Randomly put rooms in the dungeon.

        Args:
            dungeon (Dungeon): dungeon to randomize the rooms of
        """
        # Compute then umber
        n_rooms = self.get_number_of_rooms(dungeon.n_rows, dungeon.n_cols)

        # Create rooms, randomize, and check for
        i = 0
        while len(dungeon.rooms) < n_rooms:
            # Create the room
            room = Room()

            # Randomize the name
            self.room_name_randomizer.randomize_room_name(room)

            # Randomize the size
            self.room_size_randomizer.randomize_room_size(room)

            # Randomize positions
            self.room_position_randomizer.randomize_room_position(room, dungeon)

            # Check for overlap
            overlaps = False
            for existing_room_id, existing_room in dungeon.rooms.items():
                if room.overlaps(existing_room):
                    overlaps = True
                    break

            if not overlaps:
                dungeon.add_room(room)

            # Check for max attempts
            i += 1
            if i == self.max_room_attempts:
                break
        return
