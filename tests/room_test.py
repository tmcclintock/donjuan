from unittest import TestCase

from donjuan import Room


class RoomTest(TestCase):
    def test_smoke(self):
        r = Room()
        assert r is not None
        assert r.cells == [[]]
