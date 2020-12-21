from abc import ABC, abstractmethod
from typing import Tuple

import matplotlib.pyplot as plt

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
    def render(self, dungeon: Dungeon) -> None:
        pass


class Renderer(BaseRenderer):
    """
    Default renderer for rendering dungeons into PNG files using `matplotlib`.

    Args:
        scale (float, optional): size of a single cell in inches (default is
            1 inch).
    """

    def __init__(self, scale: float = 1.0):
        super().__init__(scale)

    def render(
        self,
        dungeon: Dungeon,
        file_path: str = "rendered_dungeon.png",
        dpi: int = 200,
        save: bool = True,
    ) -> Tuple:
        """
        Render the dungeon.

        Args:
            dungeon (Dungeon): dungeon to render
            file_path (str, optional): path to save the dungeon at
                (default is `rendered_dungeon.png`)
            dpi (int, optional): dots per inch used to save (default is 200)
            save (bool, optional): flag indicating whether to save the dungeon
                with :meth:`matplotlib.pyplot.savefig`
        """
        assert isinstance(dungeon, Dungeon)
        assert isinstance(file_path, str)
        filled_grid = dungeon.grid.get_filled_grid()
        fig, ax = plt.subplots(
            1,
            figsize=(
                dungeon.grid.n_rows * self.scale,
                dungeon.grid.n_cols * self.scale,
            ),
        )
        ax.imshow(filled_grid, cmap="Greys")
        ax.axis("off")
        if save:
            fig.savefig(file_path, bbox_inches="tight", dpi=dpi)
        return fig, ax
