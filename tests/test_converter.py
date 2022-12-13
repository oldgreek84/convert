import os
import unittest
from unittest.mock import patch, Mock

from converter import Converter
from tests.common import DummyJobProcessor, DummyUI, DummyWorker


class ConverterTestCase(unittest.TestCase):
    def setUp(self):
        self.converter = Converter(ui=DummyUI(), processor=DummyJobProcessor())

    def test_set_config(self):
        self.converter.set_config("config")
        self.assertEqual(self.converter.config, "config")

    def test_main_convert(self):
        with patch.object(type(self.converter), "_convert") as mocked:
            self.converter.convert()
        mocked.assert_called_once()

    def test_main_convert_result(self):
        self.converter.config = Mock(path_to_save="path/to/save")
        with \
                patch.object(self.converter, "set_converter_executor") as mocked_executor,\
                patch.object(self.converter, "send_job") as mocked_send,\
                patch.object(self.converter, "get_job")as mocked_get,\
                patch.object(self.converter, "save") as mocked_save:
            mocked_executor.return_value = self.converter._convert
            self.converter.convert()
        mocked_send.assert_called_once()
        mocked_get.assert_called_once()
        mocked_save.assert_called_once()

    def test_main_convert_without_config(self):
        with self.assertRaises(Exception) as ex:
            self.converter._convert()
        self.assertEqual(ex.exception.args[0], "Converter`s config was not set")

    def test_main_convert_with_wrong_file_path(self):
        config = Mock(path_to_file="wrong/path/to/file")
        self.converter.set_config(config)
        with self.assertRaises(Exception) as ex:
            self.converter._convert()
        self.assertEqual(ex.exception.args[0], "Invalid file path")

    def test_main_convert_without_options(self):
        # prepare converter config
        class Config:
            path_to_file = "path/to/file"

            def get_config(self):
                return {}

        config = Config()
        self.converter.set_config(config)

        with \
                patch.object(self.converter, "validate_path") as mocked_path,\
                patch.object(self.converter.processor, "is_completed") as mocked_proc,\
                patch("builtins.open", open=True):
            mocked_proc.return_value = True
            mocked_path.return_value = True
            with self.assertRaises(Exception) as ex:
                self.converter._convert()
        self.assertEqual(ex.exception.args[0], "Converter`s config was not set")

    def test_main_convert_with_exception(self):
        with patch.object(type(self.converter), "set_converter_executor") as mocked:
            mocked.side_effect = Exception("test except")
            with patch.object(self.converter.ui, "display_errors") as mocked_ui:
                self.converter.convert()
        mocked_ui.assert_called_once()

    def test_get_convert_executor(self):
        self.converter.worker = DummyWorker()
        executor = self.converter.set_converter_executor()
        self.assertTrue(executor)

    def test_get_convert_executor_without_worker(self):
        executor = self.converter.set_converter_executor()
        self.assertTrue(executor)

    def test_validate_path(self):
        with self.assertRaises(ValueError):
            self.converter.validate_path("fake/path")

    def test_validate_with_error(self):
        path_to_file = os.path.abspath(__file__)
        res = self.converter.validate_path(path_to_file)
        self.assertTrue(res)

    def test_get_file_path(self):
        config = Mock()
        config.path_to_file = "path/to/file"
        self.converter.set_config(config)
        self.assertEqual(self.converter.get_file_path(), "path/to/file")

    def test_get_job_options(self):
        attrs = {
            "get_config": lambda: {
                "target": "target",
                "category": "category",
                "options": {},
            }
        }
        self.converter.config = Mock(**attrs)

        self.assertEqual(
            self.converter.get_job_options(),
            {
                "category": "category",
                "target": "target",
                "options": {}
            }
        )

    def test_send_job(self):
        # prepare converter for send job
        attrs = {
            "path_to_file": os.path.abspath(__file__),
            "target": "target",
            "category": "category",
            "options": {}
        }
        config = Mock(**attrs)
        self.converter.set_config(config)
        processor = Mock(
            send_job_data=lambda path_to_file, file_data, options: "test_id"
        )
        self.converter.processor = processor

        # run asserts
        res = self.converter.send_job()
        self.assertEqual(res, "test_id")

    def test_get_job(self):
        with patch.object(self.converter.processor, "is_completed") as mocked,\
                patch.object(self.converter.processor, "get_job_result") as mocked_result:
            mocked.return_value = True
            mocked_result.return_value = "path/to/result"
            res = self.converter.get_job("test_id")
        self.assertEqual(res, "path/to/result")

    def test_get_job_in_main(self):
        with\
                patch("time.sleep") as mocked_time,\
                patch.object(self.converter.processor, "is_completed") as mocked,\
                patch.object(self.converter.processor, "get_job_result") as mocked_result:
            mocked_time.return_value = None
            mocked.side_effect = [False, True]
            mocked_result.return_value = "path/to/result"
            res = self.converter.get_job("test_id")
        self.assertEqual(res, "path/to/result")

    def test_error_handler(self):
        with patch.object(self.converter.ui, "display_errors") as mocked:
            self.converter.error_handler(Exception("test error"))
            mocked.assert_called_once()

    def test_save(self):
        path_to_result = "path/to/result/file"
        with patch.object(self.converter.processor, "save_file") as mocked:
            mocked.return_value = path_to_result
            res = self.converter.save("path/to/save", path_to_result)
        self.assertEqual(res, path_to_result)


if __name__ == '__main__':
    unittest.main()
