from unittest import TestCase

from donjuan import HexCell, SquareCell


class SquareCellTest(TestCase):
    def test_smoke(self):
        c = SquareCell()
        assert c is not None

    def test_faces(self):
        c = SquareCell()
        assert len(c.faces) == 4


class HexCellTest(TestCase):
    def test_smoke(self):
        c = HexCell()
        assert c is not None

    def test_faces(self):
        c = HexCell()
        assert len(c.faces) == 6
