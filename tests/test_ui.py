import time
from unittest import TestCase


class TestUI(TestCase):
    def setUp(self):
        super().setUp()

    def test_one(self):
        time.sleep(3)
        self.assertEqual(1, 2)
