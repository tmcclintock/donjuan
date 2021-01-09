from dataclasses import dataclass


@dataclass
class Coordinate:
    x: int = 0
    y: int = 0

    def __add__(self, other: "Coordinate") -> "Coordinate":
        x = self.x + other.x
        y = self.y + other.y
        return Coordinate(x=x, y=y)
