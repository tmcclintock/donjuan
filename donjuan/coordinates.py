from collections.abc import Sequence
from dataclasses import dataclass
from typing import Tuple, Union


@dataclass
class Coordinates(list):
    x: int = 0
    y: int = 0

    def __hash__(self):
        return hash((self.y, self.x))

    def __add__(self, other: "Coordinates") -> "Coordinates":
        x = self.x + other.x
        y = self.y + other.y
        return Coordinates(x=x, y=y)

    def __eq__(self, other: Union[Tuple[int, int], "Coordinates"]) -> bool:
        if not isinstance(other, tuple):
            return super().__eq__(other)
        else:  # compare to tuple
            assert isinstance(other, tuple)
            return (self.y, self.x) == other

    @classmethod
    def from_sequence(cls, coordinates: Sequence[int, int]):
        return cls(x=coordinates[1], y=coordinates[0])
