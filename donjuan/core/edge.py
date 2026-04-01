from typing import Optional

from donjuan.core.cell import Cell

DOOR_KIND_NORMAL = "normal"
DOOR_KIND_LOCKED = "locked"
DOOR_KIND_SECRET = "secret"

DOOR_STATE_CLOSED = "closed"
DOOR_STATE_OPEN = "open"
DOOR_STATE_LOCKED = "locked"

WALL_KIND_SOLID = "solid"
WALL_KIND_MOVEMENT = "movement"
WALL_KIND_SIGHT = "sight"
WALL_KIND_DENSE = "dense"


class Edge:
    """
    An edge sits between two `Cell`s.

    Args:
        cell1 (Optional[Cell]): cell on one side of the edge
        cell2 (Optional[Cell]): cell on the other side of the edge
        has_door (bool, optional): default ``False``, indicates whether this
            object has a door
    """

    def __init__(
        self,
        cell1: Optional[Cell] = None,
        cell2: Optional[Cell] = None,
        has_door: bool = False,
        door_kind: Optional[str] = None,
        door_state: Optional[str] = None,
        wall_kind: Optional[str] = None,
    ):
        self._cell1 = cell1
        self._cell2 = cell2
        self._has_door = False
        self.door_kind: Optional[str] = None
        self.door_state: Optional[str] = None
        self.wall_kind: Optional[str] = wall_kind
        self.has_door = has_door
        if has_door:
            self.set_door(
                kind=door_kind or DOOR_KIND_NORMAL,
                state=door_state,
            )

    @property
    def has_door(self) -> bool:
        return self._has_door

    @has_door.setter
    def has_door(self, value: bool) -> None:
        self._has_door = bool(value)
        if self._has_door:
            if self.door_kind is None:
                self.door_kind = DOOR_KIND_NORMAL
            if self.door_state is None:
                self.door_state = self._default_door_state(self.door_kind)
            self.wall_kind = None
        else:
            self.door_kind = None
            self.door_state = None

    def set_door(self, kind: str = DOOR_KIND_NORMAL, state: Optional[str] = None) -> None:
        self.door_kind = kind
        self.door_state = state or self._default_door_state(kind)
        self.wall_kind = None
        self._has_door = True

    def clear_door(self) -> None:
        self.has_door = False

    def cycle_door_kind(self) -> Optional[str]:
        kinds = [None, DOOR_KIND_NORMAL, DOOR_KIND_LOCKED, DOOR_KIND_SECRET]
        current = self.door_kind if self.has_door else None
        next_kind = kinds[(kinds.index(current) + 1) % len(kinds)]
        if next_kind is None:
            self.clear_door()
            return None
        self.set_door(kind=next_kind)
        return next_kind

    @staticmethod
    def _default_door_state(kind: str) -> str:
        if kind == DOOR_KIND_LOCKED:
            return DOOR_STATE_LOCKED
        return DOOR_STATE_CLOSED

    @property
    def cell1(self) -> Optional[Cell]:
        return self._cell1

    @property
    def cell2(self) -> Optional[Cell]:
        return self._cell2

    def set_cell1(self, cell: Cell) -> None:
        self._cell1 = cell

    def set_cell2(self, cell: Cell) -> None:
        self._cell2 = cell

    @property
    def is_wall(self) -> bool:
        return (
            (not self.has_door)
            or (self.cell1 is None)
            or (self.cell2 is None)
            or (self.cell1.filled != self.cell2.filled)
            or (self.cell1.space != self.cell2.space)
        )
