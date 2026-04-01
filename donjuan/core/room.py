from typing import Optional, Set, Union

from donjuan.core.space import Space


class Room(Space):
    """
    A reusable interior space. Dungeon rooms and village buildings both use
    this primitive.

    Args:
        cells: cells that make up this room
        name: room identifier
        theme: visual theme key (default ``"default"``).
    """

    def __init__(
        self,
        cells: Optional[Set] = None,
        name: Union[int, str] = "",
        theme: str = "default",
    ):
        super().__init__(cells=cells, name=name)
        self.theme = theme
