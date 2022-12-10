import unittest
from unittest import mock

from converter import Converter
from ui import DummyUI
from processor import JobProcessorDummy


class ConverterTestCase(unittest.TestCase):
    def setUp(self):
        self.processor = None
        self.converter = Converter(ui=DummyUI(), processor=JobProcessorDummy())

    def test_set_config(self):
        self.converter.set_config("config")
        self.assertEqual(self.converter.config, "config")

    def test_main_convert(self):
        with mock.patch.object(type(self.converter), "_convert") as mocked:
            self.converter.convert()
        mocked.assert_called_once()

    def test_main_convert_with_exception(self):
        with mock.patch.object(type(self.converter), "set_converter_executor") as mocked:
            mocked.side_effect = Exception("test except")
            with mock.patch.object(self.converter.ui, "display_errors") as mocked_ui:
                self.converter.convert()
        mocked_ui.assert_called_once()

    def test_get_convert_executor(self):
        class Worker:
            def execute(self):
                pass

            def set_error_handler(self, error):
                pass

        self.converter.worker = Worker()
        executor = self.converter.set_converter_executor()
        self.assertTrue(executor)

    def test_get_convert_executor_without_worker(self):
        executor = self.converter.set_converter_executor()
        self.assertEqual(executor, self.converter._convert)

    def test_validate_path(self):
        pass

    def test_validate_with_error(self):
        pass

    def test_get_file_path(self):
        pass

    def test_get_job_options(self):
        pass

    def test_send_job(self):
        pass

    def test_get_job(self):
        pass

    def test_error_handler(self):
        pass

    def test_save(self):
        pass

if __name__ == '__main__':
    unittest.main()
