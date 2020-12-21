import json
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
        inpath = "fixtures/dummy_dungeon.json"
        with open(inpath, "r") as f:
            darr = json.load(f)["dungeon"]
        n_rows = len(darr)
        n_cols = len(darr)
        dungeon = Dungeon(n_rows=n_rows, n_cols=n_cols)
        for i in range(n_rows):
            for j in range(n_cols):
                dungeon.grid.cells[i][j].filled = bool(darr[i][j])

        # Render and check for the file
        fp = os.path.join(self.TEMP_DIR, "rendered_dungeon.png")
        r = Renderer()
        r.render(dungeon, file_path=fp)
        assert os.path.exists(fp)
