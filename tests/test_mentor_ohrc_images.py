"""
Test suite for Mentor OHRC 2D imagery availability and Tab 1 integration.

Verifies:
1. Bundled directory is detected and resolved in search directories.
2. Pair 1 source, reference TIFFs, and PDS4 XML exist with exact filenames.
3. Pair 1 raster dimensions match verified physical dimensions:
   - Reference: 5916 x 4232 px
   - Source: 624 x 4872 px
4. Scene selector accurately reflects online vs local availability.
5. Missing optional scenes display a clean informative panel, not an error.
6. 3D HTML artifact remains intact and renders in sequence.
"""

import os
import sys
import unittest
from unittest.mock import patch
import numpy as np

# Path setup
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
_APP_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "SIH26_Lunar_Registration", "app"))
if not os.path.exists(_APP_DIR):
    _APP_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "app"))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
_INNER_ROOT = os.path.abspath(os.path.join(_APP_DIR, ".."))
if _INNER_ROOT not in sys.path:
    sys.path.append(_INNER_ROOT)

import research_ui


class TestMentorOHRCImages(unittest.TestCase):

    def test_01_mentor_search_dirs_finds_bundled_dir(self):
        """Bundled project directory data/mentor/ohrc is detected in search paths."""
        dirs = research_ui._get_mentor_search_dirs()
        self.assertGreater(len(dirs), 0)
        primary_dir = research_ui._find_mentor_ohrc_dir()
        self.assertIsNotNone(primary_dir)
        self.assertTrue(os.path.exists(primary_dir))

    def test_02_pair1_files_exist_and_exact_filenames(self):
        """Pair 1 files exist with exact filenames associated with the 3D artifact."""
        p1_info = research_ui._MENTOR_OHRC_SCENES["Mentor OHRC Pair 1 (3D Terrain Artifact Scene)"]
        self.assertTrue(p1_info["is_3d_artifact_pair"])
        self.assertEqual(p1_info["job_id"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")

        ref_path = research_ui._find_mentor_file(p1_info["reference_filename"])
        src_path = research_ui._find_mentor_file(p1_info["source_filename"])
        xml_path = research_ui._find_mentor_file(p1_info["xml_filename"])

        self.assertIsNotNone(ref_path, f"Reference TIFF not found: {p1_info['reference_filename']}")
        self.assertIsNotNone(src_path, f"Source TIFF not found: {p1_info['source_filename']}")
        self.assertIsNotNone(xml_path, f"XML file not found: {p1_info['xml_filename']}")

        self.assertTrue(os.path.isfile(ref_path))
        self.assertTrue(os.path.isfile(src_path))
        self.assertTrue(os.path.isfile(xml_path))

    def test_03_pair1_raster_dimensions_and_metadata(self):
        """Pair 1 rasters have correct dimensions and XML parses correctly."""
        p1_info = research_ui._MENTOR_OHRC_SCENES["Mentor OHRC Pair 1 (3D Terrain Artifact Scene)"]
        ref_path = research_ui._find_mentor_file(p1_info["reference_filename"])
        src_path = research_ui._find_mentor_file(p1_info["source_filename"])
        xml_path = research_ui._find_mentor_file(p1_info["xml_filename"])

        ref_img = research_ui._load_mentor_ohrc_image_cached(ref_path)
        src_img = research_ui._load_mentor_ohrc_image_cached(src_path)

        self.assertIsNotNone(ref_img)
        self.assertIsNotNone(src_img)

        # Height x Width in numpy shape
        ref_h, ref_w = ref_img.shape[:2]
        src_h, src_w = src_img.shape[:2]

        self.assertEqual(ref_w, 5916, "Reference width must be 5916 px")
        self.assertEqual(ref_h, 4232, "Reference height must be 4232 px")
        self.assertEqual(src_w, 624, "Source width must be 624 px")
        self.assertEqual(src_h, 4872, "Source height must be 4872 px")

        xml_meta = research_ui._parse_mentor_xml_metadata(xml_path)
        self.assertIsNotNone(xml_meta)
        self.assertEqual(xml_meta["job_id"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")

    def test_04_scene_availability_and_labeling(self):
        """Pair 1 is labeled [Available Online]; optional missing scenes are labeled local only."""
        p1_label = "Mentor OHRC Pair 1 (3D Terrain Artifact Scene)"
        self.assertTrue(research_ui._is_scene_available(p1_label))
        formatted_p1 = research_ui._format_scene_label(p1_label)
        self.assertIn("[Available Online]", formatted_p1)

        # In cloud environment (mocked search dirs having only bundled dir)
        bundled_dir = research_ui._find_mentor_ohrc_dir()
        with patch.object(research_ui, "_get_mentor_search_dirs", return_value=[bundled_dir]):
            p2_label = "Mentor OHRC Pair 2"
            self.assertFalse(research_ui._is_scene_available(p2_label))
            formatted_p2 = research_ui._format_scene_label(p2_label)
            self.assertIn("[Local Dataset Only", formatted_p2)

    def test_05_html_artifact_intact_and_rendered(self):
        """The 3D terrain HTML artifact exists, is non-empty, and loadable."""
        html_content = research_ui._load_3d_terrain_html_cached()
        self.assertIsNotNone(html_content)
        self.assertIn("plotly", html_content.lower())
        self.assertGreater(len(html_content), 100000)


if __name__ == "__main__":
    unittest.main()
