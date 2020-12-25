from donjuan import Grid


class WallFinder:
    """
    Class to find walls in a grid of cells. Using multiple inheritance,
    subclasses of this class can handle different grids and different
    kinds of walls to be searched for.
    """


class SquareWallFinder(WallFinder):
    def find_walls_on_grid(self, grid: Grid):
        pass
