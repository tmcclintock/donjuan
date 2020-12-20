from typing import Optional

from donjuan.grid import Grid, SquareGrid


class Dungeon:
    def __init__(
        self,
        n_rows: Optional[int] = 5,
        n_cols: Optional[int] = 5,
        grid: Optional[Grid] = None,
    ):
        self.grid = grid if grid else SquareGrid(n_rows, n_cols)
