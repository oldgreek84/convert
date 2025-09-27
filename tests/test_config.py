import unittest
import os
from unittest.mock import patch
from ..config import APIConfig

class TestAPIConfig(unittest.TestCase):
    @patch.dict(os.environ, {"API_KEY": "test_api_key", "CONVERTER_URL": "test_converter_url"})
    def test_api_config_with_env_vars(self):
        config = APIConfig()
        self.assertEqual(config.token, "test_api_key")
        self.assertEqual(config.url, "test_converter_url")
        self.assertEqual(config.headers["main_header"]["x-oc-api-key"], "test_api_key")
        self.assertEqual(config.headers["cache_header"]["x-oc-api-key"], "test_api_key")

    def test_api_config_with_params(self):
        config = APIConfig(token="test_token", url="test_url")
        self.assertEqual(config.token, "test_token")
        self.assertEqual(config.url, "test_url")
        self.assertEqual(config.headers["main_header"]["x-oc-api-key"], "test_token")
        self.assertEqual(config.headers["cache_header"]["x-oc-api-key"], "test_token")

    def test_get_header(self):
        config = APIConfig(token="test_token", url="test_url")
        main_header = config.get_header("main_header")
        self.assertEqual(main_header["x-oc-api-key"], "test_token")
        self.assertEqual(main_header["content-type"], "application/json")
        self.assertEqual(main_header["cache-control"], "no-cache")

        cache_header = config.get_header("cache_header")
        self.assertEqual(cache_header["x-oc-api-key"], "test_token")
        self.assertEqual(cache_header["cache-control"], "no-cache")

    def test_set_header(self):
        config = APIConfig(token="test_token", url="test_url")
        new_header = {"new_key": "new_value"}
        config.set_header("new_header", new_header)
        self.assertEqual(config.headers["new_header"], new_header)

if __name__ == '__main__':
    unittest.main()

