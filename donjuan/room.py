from typing import List, Optional, Union

from donjuan import Cell, Space


class Room(Space):
    """
    A room in a dungeon. Rooms can have names. In future versions, rooms
    will have additional features.
    """

    def __init__(
        self, cells: Optional[List[List[Cell]]] = None, name: Union[int, str] = ""
    ):
        super().__init__(cells)
        assert isinstance(name, (int, str))
        self._name = name

    @property
    def name(self) -> str:
        return str(self._name)

    def set_name(self, name: Union[int, str]) -> None:
        self._name = name
        return
