from typing import Optional

from donjuan.dungeon import Dungeon
from donjuan.randomizer import Randomizer
from donjuan.room import Room
from donjuan.room_randomizer import (
    AlphaNumRoomName,
    RoomEntrancesRandomizer,
    RoomPositionRandomizer,
    RoomSizeRandomizer,
)


class DungeonRandomizer(Randomizer):
    """
    Randomize a dungeon by first creating rooms and then applying
    room size, name, and position randomizers to sequentially generated
    rooms.

    Args:
        room_entrance_randomizer (Optional[Randomizer]): randomizer for the
            entrances of a room. If ``None`` then default to a
            ``RoomEntrancesRandomizer``.
        room_size_randomizer (Optional[Randomizer]): randomizer for the
            room size. It must have a 'max_size' attribute. If ``None`` then
            default to a ``RoomSizeRandomizer``.
        room_name_randomizer (Optional[Randomizer]): randomizer for the room
            name. If ``None`` default to a ``AlphaNumRoomName``.
        room_position_randomizer (Optional[Randomizer]): randomizer for the room
            position. If ``None`` default to a ``RoomPositionRandomizer``.
        max_num_rooms (Optional[int]): maximum number of rooms to draw,
            if ``None` then default to the :attr:`max_room_attempts`. See
            :meth:`DungeonRoomRandomizer.get_number_of_rooms` for details.
        max_room_attempts (int, optional): default is 100. Maximum number of
            attempts to generate rooms.
    """

    def __init__(
        self,
        room_entrance_randomizer: Optional[Randomizer] = None,
        room_size_randomizer: Optional[Randomizer] = None,
        room_name_randomizer: Optional[Randomizer] = None,
        room_position_randomizer: Optional[Randomizer] = None,
        max_num_rooms: Optional[int] = None,
        max_room_attempts: int = 100,
    ):
        super().__init__()
        self.room_entrance_randomizer = (
            room_entrance_randomizer or RoomEntrancesRandomizer()
        )
        self.room_size_randomizer = room_size_randomizer or RoomSizeRandomizer()
        assert hasattr(self.room_size_randomizer, "max_size")
        self.room_name_randomizer = room_name_randomizer or AlphaNumRoomName()
        self.room_position_randomizer = (
            room_position_randomizer or RoomPositionRandomizer()
        )
        self.max_num_rooms = max_num_rooms or max_room_attempts
        self.max_room_attempts = max_room_attempts

    def get_number_of_rooms(self, dungeon_n_rows: int, dungeon_n_cols: int) -> int:
        """
        Randomly determine the number of rooms based on the size
        of the incoming grid or the :attr:`max_num_rooms` attribute,
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
        # Compute the number
        n_rooms = self.get_number_of_rooms(dungeon.n_rows, dungeon.n_cols)

        # Create rooms, randomize, and check for overlap
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

        # Emplace the rooms
        dungeon.emplace_rooms()

        # Open entrances the rooms
        for room_name, room in dungeon.rooms.items():
            self.room_entrance_randomizer.randomize_room_entrances(room, dungeon)
            dungeon.room_entrances[room.name] = []
            for entrance in room.entrances:
                dungeon.room_entrances[room.name].append(entrance)

        return
