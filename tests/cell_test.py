from unittest import TestCase

from donjuan import Cell


class CellTest(TestCase):
    def test_smoke(self):
        c = Cell(x=0, y=0)
        assert c is not None

    def test_faces(self):
        c = Cell(x=0, y=0)
        assert len(c.faces) == 4
