from unittest import TestCase

from donjuan import Dungeon


class DungeonTest(TestCase):
    def test_smoke(self):
        d = Dungeon()
        assert d is not None
