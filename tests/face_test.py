from unittest import TestCase

import pytest

from donjuan import BareFace, Faces


class BareFaceTest(TestCase):
    def test_bareface_smoke(self):
        f = BareFace()
        assert f.direction == 0

    def test_direction(self):
        f = BareFace(3)
        assert f.direction == 3
        with pytest.raises(AssertionError):
            BareFace(-1)


class FacesTest(TestCase):
    def test_faces_smoke(self):
        fs = Faces()
        assert len(fs) == 4
        assert isinstance(fs[0], BareFace)

    def test_faces_directions(self):
        fs = Faces()
        for i, f in enumerate(fs):
            assert f.direction == i
