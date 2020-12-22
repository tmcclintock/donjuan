import random
from typing import Optional

from donjuan import Grid


class Randomizer:
    """
    Class for randomizing features of a dungeon.
    """

    @classmethod
    def seed(cls, seed: Optional[int] = None) -> None:
        """
        Args:
            seed (Optional[int]): seed passed to :meth:`random.seed`
        """
        random.seed(seed)


class RandomFilled(Randomizer):
    """
    Randomly set the :attr:`filled` attribute of cells.
    """

    def randomize(self, grid: Grid) -> None:
        pass
