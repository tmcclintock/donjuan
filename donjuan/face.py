from abc import ABC
from typing import List, Union


class Face(ABC):
    """
    Abstract base class for the geometric face of a
    :class:`~donjuan.cell.Cell`.

    Args:
      direction (int, optional): represents the outer direction of the face
        (default 0)
    """

    def __init__(self, direction: int = 0):
        assert direction >= 0, f"invalid face direction {direction}"
        self.direction = direction


class BareFace(Face):
    """
    A face with nothing on it.
    """


class Faces:
    """
    A collection of faces of a cell.
    """

    __slots__ = ["n", "_faces", "north", "south", "east", "west"]

    def __init__(self, faces_or_n: Union[List[Face], int] = 4):
        if isinstance(faces_or_n, int):
            assert faces_or_n == 4, "only four faced cells supported"
            self.n = faces_or_n
            self._faces = [BareFace() for _ in range(self.n)]
        else:
            assert len(faces_or_n) == 4, "only four faced cells supported"
            self._faces = faces_or_n
            self.n = 4

        self._init_faces()

    def _init_faces(self):
        # Set the directions of the faces of the cell
        dirs = {0, 1, 2, 3}
        for f in self._faces:
            if f.direction in dirs:
                dirs.remove(f.direction)
            else:
                f.direction = dirs.pop()

        self._faces = sorted(self.faces, key=lambda face: face.direction)
        self.north = self._faces[0]
        self.east = self._faces[1]
        self.west = self._faces[2]
        self.south = self._faces[3]

    @property
    def faces(self) -> List[Face]:
        return self._faces

    def __len__(self) -> int:
        return len(self.faces)

    def __getitem__(self, key):
        return self.faces[key]
