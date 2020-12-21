import os
import tempfile
from unittest import TestCase

import pytest

from donjuan import Dungeon, Renderer


class RendererTest(TestCase):
    def setUp(self):
        super().setUp()
        self.TEMP_DIR = tempfile.mkdtemp()

    def test_smoke(self):
        r = Renderer()
        assert r is not None

    def test_scale(self):
        r = Renderer(scale=3)
        assert r.scale == 3

    @pytest.mark.slow
    def test_render(self):
        fp = os.path.join(self.TEMP_DIR, "rendered_dungeon.png")
        r = Renderer()
        dungeon = Dungeon(n_rows=5, n_cols=5)
        r.render(dungeon, file_path=fp)
        assert os.path.exists(fp)
