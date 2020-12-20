from abc import ABC, abstractmethod

from donjuan.dungeon import Dungeon


class BaseRenderer(ABC):
    """
    Base class for rendering dungeons into images.
    """

    def __init__(self, scale: float):
        self._scale = scale

    @property
    def scale(self) -> float:
        """
        The scale size of a single :class:`~donjuan.cell.Cell`. The meaning
        differs depending on the subclass.
        """
        return self._scale

    @abstractmethod
    def __call__(self, dungeon: Dungeon) -> None:
        pass


class Renderer(BaseRenderer):
    """
    Default renderer for rendering dungeons into PNG files using `pillow`.

    Args:
        scale (float, optional): size of a single cell in pixels (default is
            10 pixels).
    """

    def __init__(self, scale: float = 10.0):
        super().__init__(scale)

    def __call__(self, dungeon: Dungeon) -> None:
        """
        Render the dungeon.

        Args:
            dungeon (Dungeon): dungeon to render
        """
        assert isinstance(Dungeon)
        return
