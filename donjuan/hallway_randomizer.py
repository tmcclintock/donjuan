from typing import Dict, Union

from donjuan.edge import Edge
from donjuan.hallway import Hallway
from donjuan.randomizer import Randomizer


class HallwayPathRandomizer(Randomizer):
    """
    Randomizers the ordered cells of a `Hallway`.
    """

    def randomizer_hallway_path(
        self, hallway: Hallway, room_entrances: Dict[Union[int, str], Edge]
    ):
        pass
