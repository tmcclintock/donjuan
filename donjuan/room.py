from typing import Optional, Set, Union

from donjuan.cell import Cell
from donjuan.space import Space


class Room(Space):
    """
    A room in a dungeon. A room has is a named ``Space``.
    """

    def __init__(
        self, cells: Optional[Set[Cell]] = None, name: Union[int, str] = "",
    ):
        super().__init__(cells=cells)
        assert isinstance(name, (int, str))
        self._name = name

    @property
    def name(self) -> str:
        return str(self._name)

    def set_name(self, name: Union[int, str]) -> None:
        self._name = name
        return
