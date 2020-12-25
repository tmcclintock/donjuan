from unittest import TestCase

from donjuan import SquareWallFinder


class SquareWallFinderTest(TestCase):
    def test_smoke(self):
        swf = SquareWallFinder()
        assert swf is not None
