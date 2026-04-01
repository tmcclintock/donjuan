"""Tests for VillageScene, VillageRandomizer, and VillageRenderer."""
import os
from collections import deque

import pytest

from donjuan import Hallway, Room, Scene, VillageRandomizer, VillageRenderer, VillageScene
from donjuan.core.randomizer import Randomizer
from donjuan.village.scene import VillageTree


def _make_scene(seed=42, n_rows=24, n_cols=24, n_buildings=10):
    Randomizer.seed(seed)
    scene = VillageScene(n_rows=n_rows, n_cols=n_cols)
    VillageRandomizer(
        n_buildings=n_buildings,
        min_building_size=2,
        max_building_size=4,
        tree_density=0.06,
        road_branchiness=0.2,
    ).randomize(scene)
    return scene


def test_village_scene_is_scene():
    scene = VillageScene(n_rows=20, n_cols=20)
    assert isinstance(scene, Scene)


def test_village_scene_type():
    scene = VillageScene(n_rows=10, n_cols=10)
    assert scene.scene_type == "village"


def test_village_scene_all_cells_unfilled_on_init():
    scene = VillageScene(n_rows=8, n_cols=8)
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            assert not scene.grid.cells[r][c].filled


def test_village_randomizer_places_buildings():
    scene = _make_scene()
    assert len(scene.buildings) > 0
    for building in scene.buildings.values():
        assert isinstance(building, Room)
        for cell in building.cells:
            assert not cell.filled


def test_village_buildings_do_not_overlap():
    scene = _make_scene()
    seen = set()
    for building in scene.buildings.values():
        for coord in building.cell_coordinates:
            assert coord not in seen
            seen.add(coord)


def test_village_randomizer_places_roads():
    scene = _make_scene()
    assert len(scene.roads) > 0
    for road in scene.roads.values():
        assert isinstance(road, Hallway)


def test_village_road_network_connects_entrances():
    scene = _make_scene()
    entrances = list(scene.building_entrances.values())
    assert entrances
    road_coords = {
        (cell.y, cell.x)
        for road in scene.roads.values()
        for cell in road.cells
    }
    assert all(coord in road_coords for coord in entrances)

    start = entrances[0]
    visited = {start}
    queue = deque([start])
    while queue:
        y, x = queue.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (y + dy, x + dx)
            if neighbor in road_coords and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    assert all(coord in visited for coord in entrances)


def test_village_trees_do_not_overwrite_buildings_or_roads():
    scene = _make_scene()
    for tree in scene.trees.values():
        assert isinstance(tree, VillageTree)
        for cell in tree.cells:
            assert cell.filled
            assert not isinstance(cell.space, Room)
            assert not isinstance(cell.space, Hallway)


def test_village_doors_are_valid():
    scene = _make_scene()
    for r in range(scene.n_rows):
        for c in range(scene.n_cols):
            for edge in scene.grid.cells[r][c].edges:
                if edge is None or not edge.has_door:
                    continue
                assert edge.cell1 is not None and edge.cell2 is not None
                assert not edge.cell1.filled
                assert not edge.cell2.filled
                assert isinstance(edge.cell1.space, Room) or isinstance(edge.cell2.space, Room)


def test_shared_primitives_importable_from_core():
    from donjuan.core.door_space import DoorSpace
    from donjuan.core.hallway import Hallway as CoreHallway
    from donjuan.core.room import Room as CoreRoom

    assert CoreRoom is Room
    assert CoreHallway is Hallway
    assert DoorSpace.__name__ == "DoorSpace"


@pytest.mark.slow
def test_village_renderer_produces_image(tmp_path):
    scene = _make_scene()
    renderer = VillageRenderer(tile_size=24)
    path = str(tmp_path / "village.png")
    fig, _ax = renderer.render(scene, file_path=path, save=True)
    assert fig is not None
    assert renderer._last_image is not None
    assert os.path.exists(path)


@pytest.mark.slow
def test_village_renderer_no_save():
    scene = _make_scene()
    renderer = VillageRenderer(tile_size=24)
    fig, _ax = renderer.render(scene, save=False)
    assert fig is not None
    assert renderer._last_image is not None
