from unittest import TestCase

from donjuan import Renderer


class RendererTest(TestCase):
    def test_smoke(self):
        r = Renderer()
        assert r is not None

    def test_scale(self):
        r = Renderer(scale=3)
        assert r.scale == 3
