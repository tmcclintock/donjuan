from typing import Optional, Set, Union

from donjuan.space import Space


class Room(Space):
    """
    A room in a dungeon. A room has is a named ``Space`` and an optional
    theme that drives floor colour in the textured renderer.

    Args:
        cells: cells that make up this room
        name: room identifier
        theme: visual theme key — one of the keys in
            :data:`~donjuan.textured_renderer.ROOM_THEMES`
            (default ``"default"``).
    """

    def __init__(
        self,
        cells: Optional[Set] = None,
        name: Union[int, str] = "",
        theme: str = "default",
    ):
        super().__init__(cells=cells, name=name)
        self.theme = theme
