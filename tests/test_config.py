import os
import unittest
from unittest.mock import patch

from mcq_agent.config import AppConfig


class ConfigTests(unittest.TestCase):
    def test_default_cost_controls(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig.from_env()

        self.assertEqual(config.max_upload_mb, 5)
        self.assertEqual(config.max_pages, 30)
        self.assertEqual(config.max_questions, 20)


if __name__ == "__main__":
    unittest.main()
