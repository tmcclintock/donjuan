import random
from typing import Optional

from donjuan import Cell, Grid, DoorSpace, Door,Portcullis,Archway


class Randomizer:
    """
    Class for randomizing features of a dungeon.
    """

    def randomize_cell(self, cell: Cell) -> None:
        """Randomize properties of the `Cell`"""
        pass  # pragma: no cover

    def randomize_grid(self, grid: Grid) -> None:
        """Randomize properties of the `Grid`"""
        pass  # pragma: no cover
    def randomize_door(self, cell: DoorSpace):
        """Randomize properties of the `DoorSpace`"""
        pass #pragma: no cover

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

    def randomize_cell(self, cell: Cell) -> None:
        """Randomly fill the cell with probability 50%"""
        cell.filled = bool(random.randint(0, 1))

    def randomize_grid(self, grid: Grid) -> None:
        """Randomly fill all cells of the grid individually"""
        for i in range(grid.n_rows):
            for j in range(grid.n_cols):
                self.randomize_cell(grid.cells[i][j])
        return
class DoorSpaceRandomizer(Randomizer):
    """
    Randomly set the :attrs: of the DoorSpace and select a DoorSpace type (Door, Archway, Portcullis).
    """
    def randomize_doorspace(self, door_space:DoorSpace):
        #
        door_types = [Door, Portcullis, Archway]
        material_types = ["wood","metal","stone"]
        #randomize all possible attributes
        blocked = bool(random.randint(0,1))
        secret = bool(random.randint(0,1))
        locked = bool(random.randint(0,1))
        broken = bool(random.randint(0,1))
        jammed = bool(random.randint(0,1))
        closed = bool(random.randint(0,1))
        material = material_types[random.randint(0,len(material_types) - 1)]
        #pick a type and make a new instance of it
        selected_type = door_types[random.randint(0,len(door_types) - 1)]()

        if(isinstance(selected_type, Door)):
            door_space = Door(secret=secret,locked=locked,closed=closed,jammed=jammed,blocked=blocked,broken=broken,material=material)
        elif(isinstance(selected_type, Portcullis)):
            door_space = Portcullis(locked=locked,closed=closed,jammed=jammed,broken=broken,material=material)
        elif(isinstance(selected_type, Archway)):
            door_space = Archway(material=material,blocked=blocked,broken=broken,secret=secret)
        return door_space
        
