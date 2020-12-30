from unittest import TestCase

from donjuan import Door, DoorEdge, Edge, SquareCell, WallEdge


class EdgeSetUp(TestCase):
    def setUp(self):
        super().setUp()
        # Make two cells separated horizontally
        self.cell1 = SquareCell(coordinates=(0, 0))
        self.cell2 = SquareCell(coordinates=(0, 1))


class EdgeTest(EdgeSetUp):
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


class DoorEdgeTest(EdgeSetUp):
    def test_smoke(self):
        door = Door()
        edge = DoorEdge(door)
        assert edge is not None
        assert edge.door_space is door

    def test_set_door(self):
        door1 = Door()
        door2 = Door()
        edge = DoorEdge(door1)
        assert edge.door_space is door1
        assert edge.door_space is not door2
        edge.set_door_space(door2)
        assert edge.door_space is door2
        assert edge.door_space is not door1


class WallEdgeTest(EdgeSetUp):
    def test_smoke(self):
        edge = WallEdge(solid=False, transparent=True)
        assert edge is not None
        assert edge.solid is False
        assert edge.transparent is True
