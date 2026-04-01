from unittest import TestCase

from donjuan import Edge, SquareCell
from donjuan.core.edge import DOOR_KIND_LOCKED, DOOR_KIND_SECRET


class EdgeTest(TestCase):
    def setUp(self):
        super().setUp()
        # Make two cells separated horizontally
        self.cell1 = SquareCell(coordinates=(0, 0), filled=True)
        self.cell2 = SquareCell(coordinates=(0, 1), filled=False)

    def test_smoke(self):
        edge = Edge()
        assert edge is not None
        assert edge.cell1 is None
        assert edge.cell2 is None

    def test_cells(self):
        edge = Edge(self.cell1, self.cell2)
        assert isinstance(edge.cell1, SquareCell)
        assert isinstance(edge.cell2, SquareCell)

    def test_set_cell(self):
        edge = Edge()
        edge.set_cell1(self.cell1)
        edge.set_cell2(self.cell2)
        assert isinstance(edge.cell1, SquareCell)
        assert isinstance(edge.cell2, SquareCell)
        assert edge.is_wall

    def test_has_door_sets_default_kind(self):
        edge = Edge(self.cell1, self.cell2)
        edge.has_door = True
        assert edge.door_kind == "normal"
        assert edge.door_state == "closed"

    def test_cycle_door_kind(self):
        edge = Edge(self.cell1, self.cell2)
        assert edge.cycle_door_kind() == "normal"
        assert edge.cycle_door_kind() == DOOR_KIND_LOCKED
        assert edge.cycle_door_kind() == DOOR_KIND_SECRET
        assert edge.cycle_door_kind() is None
        assert edge.has_door is False

    def test_clear_door_resets_metadata(self):
        edge = Edge(self.cell1, self.cell2, has_door=True, door_kind=DOOR_KIND_LOCKED)
        edge.clear_door()
        assert edge.has_door is False
        assert edge.door_kind is None
        assert edge.door_state is None
