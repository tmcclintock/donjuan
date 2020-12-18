from unittest import TestCase

from donjuan import Cell


class CellTest(TestCase):
    def test_smoke(self):
        c = Cell()
        assert c is not None

    def test_faces(self):
        c = Cell()
        assert len(c.faces) == 4
