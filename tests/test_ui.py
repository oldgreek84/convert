from unittest import TestCase


class TestUI(TestCase):
    def setUp(self):
        super().setUp()

    def test_one(self):
        # NOTE: wrong test to run assertion
        self.assertEqual(1, 2)
