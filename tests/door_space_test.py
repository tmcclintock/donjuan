from unittest import TestCase

from donjuan import Archway, Door, Portcullis


class DoorspaceTest(TestCase):
    def test_archway_smoke(self):
        a = Archway()
        assert a is not None

    def test_door_smoke(self):
        d = Door()
        assert d is not None

    def test_portcullis_smoke(self):
        p = Portcullis()
        assert p is not None

    def test_door_string(self):
        d = Door(
            secret=True,
            locked=True,
            closed=True,
            jammed=True,
            blocked=True,
            broken=True,
            material="wood",
        )
        s = "secret broken blocked jammed closed locked wood door"
        assert str(d) == s
