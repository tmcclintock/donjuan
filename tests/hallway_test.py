from unittest import TestCase

from donjuan import Hallway


class HallwayTest(TestCase):
    def test_smoke(self):
        h = Hallway()
        assert h is not None
        assert h.cells == [[]]
