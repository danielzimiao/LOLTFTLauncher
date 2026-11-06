import os
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import utils


class MetadataDetectionTests(unittest.TestCase):
    @patch("utils.is_valid_metadata_file", return_value=True)
    def test_detects_lol_and_tft_live_and_pbe(self, _is_valid):
        detected = utils.detect_metadata_file(r"C:\ProgramData\Riot Games\Metadata")

        self.assertEqual(4, len(detected))
        self.assertTrue(any("league_of_legends.live" in path for path in detected))
        self.assertTrue(any("league_of_legends.pbe" in path for path in detected))
        self.assertTrue(any("teamfighttactics.live" in path for path in detected))
        self.assertTrue(any("teamfighttactics.pbe" in path for path in detected))

    def test_version_comparison_handles_v_prefix(self):
        self.assertGreater(utils.version_key("v1.3.1"), utils.version_key("1.3.0"))
        self.assertEqual(utils.version_key("v1.3.1"), utils.version_key("1.3.1"))

    def test_to_list_handles_empty_and_multiple_selections(self):
        self.assertEqual([], utils.to_list(None))
        self.assertEqual([], utils.to_list(""))
        self.assertEqual(["one", "two"], utils.to_list(("one", "two")))

    def test_identifies_product_from_metadata_filename(self):
        self.assertEqual(
            "league_of_legends",
            utils.get_metadata_product(r"C:\ProgramData\league_of_legends.live.product_settings.yaml"))
        self.assertEqual(
            "teamfighttactics",
            utils.get_metadata_product(r"C:\ProgramData\teamfighttactics.live.product_settings.yaml"))
        self.assertIsNone(utils.get_metadata_product(r"C:\ProgramData\other.product_settings.yaml"))


if __name__ == "__main__":
    unittest.main()
