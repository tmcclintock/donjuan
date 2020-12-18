from abc import ABC
from typing import List, Optional


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

    def __init__(self, faces: List[Face]):
        self._faces = faces
        self._init_faces()

    def _init_faces(self) -> None:
        # Set each face to have a different direction
        # note these directions don't have "meaning" in this base class
        dirs = {i for i in range(len(self._faces))}
        for f in self._faces:
            if f.direction in dirs:
                dirs.remove(f.direction)
            else:
                f.direction = dirs.pop()
        self._faces = sorted(self._faces, key=lambda face: face.direction)
        return

    @property
    def faces(self) -> List[Face]:
        return self._faces

    def __len__(self) -> int:
        return len(self._faces)

    def __getitem__(self, key):
        return self.faces[key]


class SquareFaces(Faces):
    """
    Four faces surrounding a square cell.
    """

    def __init__(self, faces: Optional[List[Face]] = None):
        if faces is not None:
            assert len(faces) == 4
        else:
            faces = [BareFace() for _ in range(4)]
        super().__init__(faces)

        # Ascribe each face to a cardinal direction
        self.north = self.faces[0]
        self.east = self.faces[1]
        self.south = self.faces[2]
        self.west = self.faces[3]


class HexFaces(Faces):
    """
    Six faces surrounding a hexagonal cell.
    """

    def __init__(self, faces: Optional[List[Face]] = None):
        if faces is not None:
            assert len(faces) == 6
        else:
            faces = [BareFace() for _ in range(6)]
        super().__init__(faces)

        # Ascribe each face to a cardinal-ish direction
        self.north = self.faces[0]
        self.northeast = self.faces[1]
        self.southeast = self.faces[2]
        self.south = self.faces[3]
        self.southwest = self.faces[4]
        self.northwest = self.faces[5]
