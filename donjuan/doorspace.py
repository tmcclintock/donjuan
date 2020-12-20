"""
Door ways that connect rooms to hallways and rooms to rooms.
"""
from abc import ABC


class Doorspace(ABC):
    """
    Abstract base class for different kinds of doors. Doorspaces can have many
    properties, like if they are locked or blocked etc. To facilitate
    this logic in the genative process, these are encompassed in the
    attributes of a ``Doorspace``.
    """

    __slots__ = [
        "locked",
        "closed",
        "jammed",
        "blocked",
        "secret",
        "broken",
        "material",
        "name",
    ]

    def __init__(
        self,
        secret: bool,
        locked: bool,
        closed: bool,
        jammed: bool,
        blocked: bool,
        broken: bool,
        material: str,
        name: str,
    ):
        self.secret = (secret,)
        self.locked = (locked,)
        self.closed = (closed,)
        self.jammed = (jammed,)
        self.blocked = (blocked,)
        self.broken = (broken,)
        self.material = material
        self.name = name

    def __str__(self):
        s = f"{self.name}"
        if self.material != "":
            s = f"{self.material} " + s
        if self.locked:
            s = "locked " + s
        if self.closed:
            s = "closed " + s
        if self.jammed:
            s = "jammed " + s
        if self.blocked:
            s = "blocked " + s
        if self.broken:
            s = "broken " + s
        if self.secret:
            s = "secret " + s
        return s


class Archway(Doorspace):
    """
    An archway to walk through.
    """

    def __init__(
        self,
        material: str = "stone",
        blocked: bool = False,
        broken: bool = False,
        secret: bool = False,
    ):
        super().__init__(
            material=material,
            blocked=blocked,
            broken=broken,
            secret=secret,
            locked=False,
            closed=False,
            jammed=False,
            name="archway",
        )


class Door(Doorspace):
    """
    A generic door.
    """

    def __init__(
        self,
        secret: bool = False,
        locked: bool = False,
        closed: bool = True,
        jammed: bool = False,
        blocked: bool = False,
        broken: bool = False,
        material: str = "wood",
    ):
        super().__init__(
            secret=secret,
            locked=locked,
            closed=closed,
            jammed=jammed,
            blocked=blocked,
            broken=broken,
            material=material,
            name="door",
        )


class Portcullis(Doorspace):
    """
    You can look but can't touch!
    """

    def __init__(
        self,
        locked: bool = False,
        closed: bool = True,
        jammed: bool = False,
        broken: bool = False,
        material: str = "metal",
    ):
        super().__init__(
            secret=False,
            locked=locked,
            closed=closed,
            jammed=jammed,
            blocked=False,
            broken=broken,
            material=material,
            name="portcullis",
        )
