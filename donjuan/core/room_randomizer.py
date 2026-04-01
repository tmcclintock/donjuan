import random
from typing import Type

from donjuan.core.cell import Cell, SquareCell
from donjuan.core.randomizer import Randomizer
from donjuan.core.room import Room


class RoomSizeRandomizer(Randomizer):
    """Randomize the size of a ``Room``."""

    def __init__(
        self, min_size: int = 2, max_size: int = 4, cell_type: Type[Cell] = SquareCell
    ):
        super().__init__()
        assert issubclass(cell_type, Cell)
        assert min_size >= 1, f"{min_size}"
        assert max_size >= min_size, f"{max_size} < {min_size}"
        assert max_size <= 100, f"{max_size}"
        self.min_size = min_size
        self.max_size = max_size
        self.cell_type = cell_type

    def randomize_room_size(self, room: Room) -> None:
        height = random.randint(self.min_size, self.max_size)
        width = random.randint(self.min_size, self.max_size)
        cells = [
            self.cell_type(filled=False, coordinates=(i, j))
            for j in range(height)
            for i in range(width)
        ]
        room.add_cells(cells)
        return


class RoomPositionRandomizer(Randomizer):
    """
    Randomly shift a room assuming its left edge is at column 0 and its top
    edge is at row 0.
    """

    def randomize_room_position(self, room: Room, scene) -> None:
        bottom = max(room.cell_coordinates, key=lambda x: x[0])[0]
        right = max(room.cell_coordinates, key=lambda x: x[1])[1]
        room.shift_horizontal(random.randint(0, scene.n_cols - right - 1))
        room.shift_vertical(random.randint(0, scene.n_rows - bottom - 1))
        return
