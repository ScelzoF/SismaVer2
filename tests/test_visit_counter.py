import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules import security


class VisitCounterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.counter_path = str(Path(self.temp_dir.name) / "visit_counter.txt")

    def test_missing_file_starts_at_zero_and_increments(self):
        with patch.object(security, "_COUNTER_PATH", self.counter_path), patch.object(security, "_ensure_data_dir", return_value=True):
            self.assertEqual(security.read_visit_counter(), 0)
            self.assertEqual(security.increment_visit_counter(), 1)
            self.assertEqual(security.read_visit_counter(), 1)

    def test_invalid_file_is_not_reported_as_zero(self):
        Path(self.counter_path).write_text("invalid", encoding="utf-8")
        with patch.object(security, "_COUNTER_PATH", self.counter_path):
            self.assertIsNone(security.read_visit_counter())
            self.assertIsNone(security.increment_visit_counter())

    def test_write_error_is_not_reported_as_zero(self):
        with patch.object(security, "_COUNTER_PATH", self.counter_path), patch.object(security, "_ensure_data_dir", return_value=True), patch("builtins.open", side_effect=OSError("read-only")):
            self.assertIsNone(security.increment_visit_counter())


if __name__ == "__main__":
    unittest.main()
