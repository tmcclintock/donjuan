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
    def randomize_door(self, cell: door_space):
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
    Randomly set the attributes of the DoorSpace subclass (Door, Archway, Portcullis).
    """
    def randomize_doorspace(self, door_space:door_space):
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
            door_space.secret=secret
            door_space.locked=locked
            door_space.closed=closed
            door_space.jammed=jammed
            door_space.blocked=blocked
            door_space.broken=broken
            door_space.material=material
        elif(isinstance(selected_type, Portcullis)):
            door_space.locked=locked
            door_space.closed=closed
            door_space.jammed=jammed
            door_space.broken=broken
            door_space.material=material
        elif(isinstance(selected_type, Archway)):
            door_space.material=material
            door_space.blocked=blocked
            door_space.broken=broken
            door_space.secret=secret
        else:
            raise Exception("Unknown Door Type!")
        return
        
