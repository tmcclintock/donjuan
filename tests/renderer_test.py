import json
import math
import os
import tempfile
from unittest import TestCase

import pytest

from donjuan import Dungeon, DungeonRandomizer, HexRenderer, Renderer
from donjuan.core.grid import HexGrid, SquareGrid


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
    def test_render_dummy_dungeon(self):
        inpath = os.path.abspath(os.path.dirname(__file__))
        inpath = os.path.join(inpath, "fixtures/dummy_dungeon.json")
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

    @pytest.mark.slow
    def test_render_dungeon_with_rooms(self):
        randomizer = DungeonRandomizer()
        dungeon = Dungeon(10, 10, randomizers=[randomizer])
        dungeon.randomize()
        dungeon.emplace_rooms()
        renderer = Renderer()

        # Render and check for the file
        fp = os.path.join(self.TEMP_DIR, "rendered_dungeon.png")
        renderer.render(dungeon, file_path=fp)
        assert os.path.exists(fp)


class HexRendererTest(TestCase):
    def setUp(self):
        super().setUp()
        self.TEMP_DIR = tempfile.mkdtemp()

    def test_smoke(self):
        r = HexRenderer()
        assert r is not None

    def test_default_scale(self):
        r = HexRenderer()
        assert r.scale == 0.5

    def test_custom_scale(self):
        r = HexRenderer(scale=1.0)
        assert r.scale == 1.0

    def test_hex_vertices_count(self):
        verts = HexRenderer._hex_vertices(0, 0, 1.0)
        assert len(verts) == 6

    def test_hex_vertices_radius(self):
        """Each vertex should be exactly r away from the centre."""
        r = 2.0
        verts = HexRenderer._hex_vertices(0.0, 0.0, r)
        for x, y in verts:
            dist = math.sqrt(x ** 2 + y ** 2)
            assert abs(dist - r) < 1e-10

    def test_hex_vertices_offset_centre(self):
        """Vertices should be offset correctly for a non-origin centre."""
        cx, cy, r = 3.0, 4.0, 1.0
        verts = HexRenderer._hex_vertices(cx, cy, r)
        for x, y in verts:
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            assert abs(dist - r) < 1e-10

    def test_render_raises_on_square_grid(self):
        dungeon = Dungeon(grid=SquareGrid(4, 4))
        r = HexRenderer()
        with self.assertRaises(AssertionError):
            r.render(dungeon, save=False)

    def test_render_returns_fig_ax(self):
        dungeon = Dungeon(grid=HexGrid(4, 4))
        r = HexRenderer()
        result = r.render(dungeon, save=False)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.slow
    def test_render_saves_file(self):
        dungeon = Dungeon(grid=HexGrid(6, 6))
        r = HexRenderer()
        fp = os.path.join(self.TEMP_DIR, "hex_dungeon.png")
        r.render(dungeon, file_path=fp)
        assert os.path.exists(fp)

    @pytest.mark.slow
    def test_render_hex_dungeon_with_rooms(self):
        from donjuan import DungeonRandomizer
        from donjuan.dungeon.room_randomizer import RoomSizeRandomizer
        from donjuan.core.cell import HexCell
        dungeon = Dungeon(grid=HexGrid(10, 10))
        # manually place a couple of unfilled hex cells
        dungeon.grid.cells[2][2].filled = False
        dungeon.grid.cells[2][3].filled = False
        r = HexRenderer(scale=0.4)
        fp = os.path.join(self.TEMP_DIR, "hex_dungeon_rooms.png")
        r.render(dungeon, file_path=fp)
        assert os.path.exists(fp)
