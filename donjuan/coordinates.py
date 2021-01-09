from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class Coordinates(list):
    x: int = 0
    y: int = 0

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other: "Coordinates") -> "Coordinates":
        x = self.x + other.x
        y = self.y + other.y
        return Coordinates(x=x, y=y)

    @classmethod
    def from_sequence(cls, coordinates: Sequence[int, int]):
        return cls(x=coordinates[1], y=coordinates[0])
