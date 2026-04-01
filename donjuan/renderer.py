from abc import ABC, abstractmethod
from math import cos, pi, sin, sqrt
from typing import List, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from donjuan.dungeon import Dungeon
from donjuan.grid import HexGrid


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
        pass  # pragma: no cover


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


class HexRenderer(BaseRenderer):
    """
    Renderer for dungeons built on a :class:`~donjuan.grid.HexGrid`. Each
    cell is drawn as a pointy-top hexagon with odd rows offset to the right
    by half a cell width, matching the offset layout used by
    :class:`~donjuan.grid.HexGrid`.

    Filled cells are drawn in black; unfilled cells in white. Cell borders
    are drawn in grey.

    Args:
        scale (float, optional): circumradius of each hexagon in inches
            (default is 0.5 inches, giving a comfortable cell size at 200 dpi).
    """

    def __init__(self, scale: float = 0.5):
        super().__init__(scale)

    @staticmethod
    def _hex_vertices(cx: float, cy: float, r: float) -> List[Tuple[float, float]]:
        """
        Compute the six vertices of a pointy-top hexagon centred at
        ``(cx, cy)`` with circumradius ``r``.
        """
        return [
            (cx + r * cos(pi / 3 * k + pi / 6), cy + r * sin(pi / 3 * k + pi / 6))
            for k in range(6)
        ]

    def render(
        self,
        dungeon: Dungeon,
        file_path: str = "rendered_dungeon.png",
        dpi: int = 200,
        save: bool = True,
    ) -> Tuple:
        """
        Render a hex-grid dungeon.

        Args:
            dungeon (Dungeon): dungeon whose grid is a :class:`~donjuan.grid.HexGrid`
            file_path (str, optional): output path (default ``rendered_dungeon.png``)
            dpi (int, optional): dots per inch (default 200)
            save (bool, optional): whether to save to disk (default ``True``)

        Raises:
            AssertionError: if the dungeon's grid is not a :class:`~donjuan.grid.HexGrid`
        """
        assert isinstance(dungeon.grid, HexGrid), (
            "HexRenderer requires a dungeon with a HexGrid; "
            f"got {type(dungeon.grid).__name__}"
        )

        r = self.scale  # circumradius of each hex
        hex_w = sqrt(3) * r  # width of a pointy-top hex
        row_h = 1.5 * r  # vertical distance between row centres

        n_rows = dungeon.n_rows
        n_cols = dungeon.n_cols

        fig_w = hex_w * (n_cols + 0.5) + 0.2
        fig_h = row_h * n_rows + 0.5 * r + 0.2

        fig, ax = plt.subplots(1, figsize=(fig_w, fig_h))
        ax.set_aspect("equal")
        ax.axis("off")

        for i in range(n_rows):
            for j in range(n_cols):
                cell = dungeon.grid.cells[i][j]
                # Odd rows are offset right by half a hex width
                cx = j * hex_w + (i % 2) * hex_w / 2
                cy = i * row_h
                verts = self._hex_vertices(cx, cy, r)
                facecolor = "black" if cell.filled else "white"
                patch = MplPolygon(
                    verts,
                    closed=True,
                    facecolor=facecolor,
                    edgecolor="grey",
                    linewidth=0.5,
                )
                ax.add_patch(patch)

        ax.set_xlim(-r, hex_w * (n_cols + 0.5))
        ax.set_ylim(-r, row_h * n_rows + r * 0.5)

        if save:
            fig.savefig(file_path, bbox_inches="tight", dpi=dpi)
        return fig, ax
