from unittest import TestCase

import pytest

from donjuan import BareFace, HexFaces, SquareFaces


class BareFaceTest(TestCase):
    def test_bareface_smoke(self):
        f = BareFace()
        assert f.direction == 0

    def test_direction(self):
        f = BareFace(3)
        assert f.direction == 3
        with pytest.raises(AssertionError):
            BareFace(-1)


class SquareFacesTest(TestCase):
    def test_squarefaces_smoke(self):
        fs = SquareFaces()
        assert len(fs) == 4
        assert isinstance(fs[0], BareFace)

    def test_squarefaces_directions(self):
        fs = SquareFaces()
        for i, f in enumerate(fs):
            assert f.direction == i

    def test_assert_number_of_Faces(self):
        faces = [BareFace()]  # should have four faces
        with pytest.raises(AssertionError):
            SquareFaces(faces)


class HexFacesTest(TestCase):
    def test_hexfaces_smoke(self):
        fs = HexFaces()
        assert len(fs) == 6
        assert isinstance(fs[0], BareFace)

    def test_hexfaces_directions(self):
        fs = HexFaces()
        for i, f in enumerate(fs):
            assert f.direction == i

    def test_assert_number_of_Faces(self):
        faces = [BareFace()]  # should have six faces
        with pytest.raises(AssertionError):
            HexFaces(faces)
