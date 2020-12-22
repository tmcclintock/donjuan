from unittest import TestCase

from donjuan import Randomizer


class RandomizerTest(TestCase):
    def test_smoke(self):
        rng = Randomizer()
        assert rng is not None

    def test_seed_passes(self):
        Randomizer.seed(0)
