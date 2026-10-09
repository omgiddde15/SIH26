"""
Regression Test Suite for LunarReg User Metadata Upload Feature.

Verifies:
1. Valid source XML upload.
2. Valid reference XML upload.
3. Both metadata files uploaded.
4. Source metadata only.
5. Reference metadata only.
6. No metadata uploaded -> existing workflow still works.
7. Invalid XML -> clean error, no crash, no fake metadata.
8. Missing fields -> "Not available", no fabricated values.
9. Replacing source metadata does not change reference metadata.
10. Starting a new run clears old metadata.
11. Metadata from Run A does not appear in Run B.
12. Application still imports/compiles successfully.
13. Real parser behavior against repository Chandrayaan-2 XML verification case.
"""

from __future__ import annotations

import io
import os
import py_compile
import sys
import unittest
from typing import Dict, Any

# Ensure app path is in sys.path
possible_app_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SIH26_Lunar_Registration", "app")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "app")),
]
APP_DIR = None
for p in possible_app_dirs:
    if os.path.exists(p) and os.path.exists(os.path.join(p, "app.py")):
        APP_DIR = p
        break

if APP_DIR and APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from metadata_parser import (
    validate_xml,
    parse_metadata_xml,
    parse_metadata_file,
    handle_uploaded_metadata_file,
    clear_metadata_state,
    METADATA_DISPLAY_KEYS,
    NOT_AVAILABLE,
    get_metadata_card_html,
)
from app import resolve_image_metadata_and_geo


class MockUploadedFile:
    """Mock of Streamlit's UploadedFile for headless regression testing."""
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def read(self) -> bytes:
        return self._data


class TestUserMetadataUpload(unittest.TestCase):
    """Full regression suite for User Metadata Upload."""

    @classmethod
    def setUpClass(cls):
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "fixtures", "ch2_sample_metadata.xml"),
            os.path.join(os.path.dirname(__file__), "..", "data", "metadata", "ch2_sample_metadata.xml"),
            os.path.join(os.path.dirname(__file__), "..", "SIH26_Lunar_Registration", "data", "metadata", "ch2_sample_metadata.xml"),
            os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "ch2_sample_metadata.xml"),
        ]
        cls.fixture_path = None
        for p in possible_paths:
            if os.path.exists(p):
                cls.fixture_path = os.path.abspath(p)
                break

        if cls.fixture_path and os.path.exists(cls.fixture_path):
            with open(cls.fixture_path, "rb") as f:
                cls.ch2_xml_bytes = f.read()
        else:
            raise FileNotFoundError(f"ch2_sample_metadata.xml not found in any of: {possible_paths}")

        cls.minimal_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<product>
    <job_id>TEST_MINIMAL_001</job_id>
</product>
"""

        cls.ref_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<product>
    <job_id>LRO_REF_TILE_005</job_id>
    <platform>Lunar Reconnaissance Orbiter</platform>
    <instrument_name>LRO-NAC</instrument_name>
    <Resolution_in_meter>5.0</Resolution_in_meter>
    <spacecraft_altitude_in_km>50.0</spacecraft_altitude_in_km>
    <projection>Polar stereographic</projection>
    <area>South Pole</area>
</product>
"""

    def setUp(self):
        self.session_state: Dict[str, Any] = {}

    def test_01_valid_source_xml_upload(self):
        """1. Valid source XML upload correctly populates session state and parsed fields."""
        mock_file = MockUploadedFile("ch2_source.xml", self.ch2_xml_bytes)
        ok, err = handle_uploaded_metadata_file(mock_file, "source", self.session_state)

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertIn("source_metadata", self.session_state)
        self.assertIn("source_metadata_file", self.session_state)
        self.assertIsNone(self.session_state.get("source_metadata_error"))

        meta = self.session_state["source_metadata"]
        self.assertTrue(meta["valid"])
        self.assertEqual(meta["filename"], "ch2_source.xml")
        self.assertEqual(meta["raw_fields"]["product_identifier"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")
        self.assertEqual(meta["raw_fields"]["ground_sample_distance"], "0.26 m/px")
        self.assertEqual(meta["raw_fields"]["altitude"], "100.78 km")

    def test_02_valid_reference_xml_upload(self):
        """2. Valid reference XML upload correctly populates session state."""
        mock_file = MockUploadedFile("ref_meta.xml", self.ref_xml)
        ok, err = handle_uploaded_metadata_file(mock_file, "reference", self.session_state)

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertIn("reference_metadata", self.session_state)
        self.assertIn("reference_metadata_file", self.session_state)
        self.assertIsNone(self.session_state.get("reference_metadata_error"))

        meta = self.session_state["reference_metadata"]
        self.assertTrue(meta["valid"])
        self.assertEqual(meta["filename"], "ref_meta.xml")
        self.assertEqual(meta["raw_fields"]["product_identifier"], "LRO_REF_TILE_005")
        self.assertEqual(meta["raw_fields"]["ground_sample_distance"], "5.0 m/px")

    def test_03_both_metadata_files_uploaded(self):
        """3. Both metadata files uploaded coexist independently and attach to run."""
        mock_src = MockUploadedFile("source.xml", self.ch2_xml_bytes)
        mock_ref = MockUploadedFile("ref.xml", self.ref_xml)

        handle_uploaded_metadata_file(mock_src, "source", self.session_state)
        handle_uploaded_metadata_file(mock_ref, "reference", self.session_state)

        self.assertIsNotNone(self.session_state.get("source_metadata"))
        self.assertIsNotNone(self.session_state.get("reference_metadata"))
        self.assertEqual(self.session_state["source_metadata"]["filename"], "source.xml")
        self.assertEqual(self.session_state["reference_metadata"]["filename"], "ref.xml")

        # Simulate attaching to run result
        run_res = {
            "success": True,
            "runtime": 1.25,
            "source_metadata": self.session_state.get("source_metadata"),
            "reference_metadata": self.session_state.get("reference_metadata"),
        }
        self.assertEqual(run_res["source_metadata"]["raw_fields"]["product_identifier"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")
        self.assertEqual(run_res["reference_metadata"]["raw_fields"]["product_identifier"], "LRO_REF_TILE_005")

    def test_04_source_metadata_only(self):
        """4. Source metadata only works seamlessly; reference metadata remains None."""
        mock_src = MockUploadedFile("source.xml", self.ch2_xml_bytes)
        handle_uploaded_metadata_file(mock_src, "source", self.session_state)

        self.assertIsNotNone(self.session_state.get("source_metadata"))
        self.assertIsNone(self.session_state.get("reference_metadata"))
        self.assertIsNone(self.session_state.get("reference_metadata_file"))

        # Pipeline resolver accepts source only
        meta_info = resolve_image_metadata_and_geo(
            None, None, "src.png", "ref.png",
            s_meta=self.session_state.get("source_metadata"),
            r_meta=self.session_state.get("reference_metadata")
        )
        self.assertEqual(meta_info["source"]["acquisition_id"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")
        self.assertEqual(meta_info["reference"]["acquisition_id"], "Mission metadata not available for this image.")

    def test_05_reference_metadata_only(self):
        """5. Reference metadata only works seamlessly; source metadata remains None."""
        mock_ref = MockUploadedFile("ref.xml", self.ref_xml)
        handle_uploaded_metadata_file(mock_ref, "reference", self.session_state)

        self.assertIsNone(self.session_state.get("source_metadata"))
        self.assertIsNotNone(self.session_state.get("reference_metadata"))

        meta_info = resolve_image_metadata_and_geo(
            None, None, "src.png", "ref.png",
            s_meta=self.session_state.get("source_metadata"),
            r_meta=self.session_state.get("reference_metadata")
        )
        self.assertEqual(meta_info["source"]["acquisition_id"], "Mission metadata not available for this image.")
        self.assertEqual(meta_info["reference"]["acquisition_id"], "LRO_REF_TILE_005")

    def test_06_no_metadata_uploaded_existing_workflow_still_works(self):
        """6. No metadata uploaded -> existing workflow still works with zero disruption."""
        self.assertIsNone(self.session_state.get("source_metadata"))
        self.assertIsNone(self.session_state.get("reference_metadata"))

        meta_info = resolve_image_metadata_and_geo(
            None, None, "source.jpeg", "reference.jpeg",
            s_meta=None, r_meta=None
        )
        self.assertIn("source", meta_info)
        self.assertIn("reference", meta_info)
        self.assertIn("geo", meta_info)
        self.assertFalse(meta_info["mentor"]["is_mentor_data"])

    def test_07_invalid_xml_clean_error(self):
        """7. Invalid XML, empty XML, and unsupported extensions produce clean user errors."""
        # 7a. Malformed XML syntax
        bad_xml = MockUploadedFile("corrupted.xml", b"<product><unclosed_tag>")
        ok, err = handle_uploaded_metadata_file(bad_xml, "source", self.session_state)
        self.assertFalse(ok)
        self.assertIsNotNone(err)
        self.assertIn("Invalid XML format", err)
        self.assertIsNone(self.session_state.get("source_metadata"))
        self.assertEqual(self.session_state["source_metadata_error"], err)

        # 7b. Empty XML
        empty_xml = MockUploadedFile("empty.xml", b"   \n\t  ")
        ok, err = handle_uploaded_metadata_file(empty_xml, "reference", self.session_state)
        self.assertFalse(ok)
        self.assertIn("empty", err.lower())
        self.assertIsNone(self.session_state.get("reference_metadata"))

        # 7c. Unsupported extension
        txt_file = MockUploadedFile("notes.txt", b"some plain text metadata")
        ok, err = handle_uploaded_metadata_file(txt_file, "source", self.session_state)
        self.assertFalse(ok)
        self.assertIn("Unsupported file extension", err)

    def test_08_missing_fields_not_available_no_fabricated_values(self):
        """8. Missing fields display 'Not available' without fabricating physical quantities."""
        parsed = parse_metadata_xml(self.minimal_xml, "minimal.xml")
        self.assertTrue(parsed["valid"])

        # Product ID is present
        self.assertEqual(parsed["raw_fields"]["product_identifier"], "TEST_MINIMAL_001")
        self.assertEqual(parsed["display_fields"]["Product Identifier"], "TEST_MINIMAL_001")

        # Missing physical quantities MUST NOT be fabricated
        self.assertNotIn("ground_sample_distance", parsed["raw_fields"])
        self.assertNotIn("altitude", parsed["raw_fields"])
        self.assertNotIn("solar_azimuth", parsed["raw_fields"])
        self.assertNotIn("solar_elevation", parsed["raw_fields"])
        self.assertNotIn("incidence_angle", parsed["raw_fields"])
        self.assertNotIn("observation_geometry", parsed["raw_fields"])

        self.assertEqual(parsed["display_fields"]["Ground Sample Distance / Pixel Scale"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Spacecraft Altitude"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Solar Azimuth"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Solar Elevation"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Incidence Angle"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Observation Geometry"], NOT_AVAILABLE)
        self.assertEqual(parsed["display_fields"]["Processing Level"], NOT_AVAILABLE)

        # Malformed field retention test
        malformed_field_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<product>
    <job_id>TEST_JOB_OK</job_id>
    <Resolution_in_meter>0.26</Resolution_in_meter>
    <Solar_incidence_angle_in_degree>invalid_numeric_str</Solar_incidence_angle_in_degree>
</product>
"""
        parsed_mal = parse_metadata_xml(malformed_field_xml, "malformed_field.xml")
        self.assertTrue(parsed_mal["valid"])
        self.assertEqual(parsed_mal["raw_fields"]["product_identifier"], "TEST_JOB_OK")
        self.assertEqual(parsed_mal["raw_fields"]["ground_sample_distance"], "0.26 m/px")
        # Malformed field should be marked unavailable without crashing
        self.assertNotIn("incidence_angle", parsed_mal["raw_fields"])
        self.assertEqual(parsed_mal["display_fields"]["Incidence Angle"], NOT_AVAILABLE)

    def test_09_replacing_source_metadata_does_not_change_reference_metadata(self):
        """9. Replacing source metadata does not alter reference metadata."""
        src_a = MockUploadedFile("src_a.xml", self.ch2_xml_bytes)
        ref_a = MockUploadedFile("ref_a.xml", self.ref_xml)
        handle_uploaded_metadata_file(src_a, "source", self.session_state)
        handle_uploaded_metadata_file(ref_a, "reference", self.session_state)

        self.assertEqual(self.session_state["source_metadata"]["filename"], "src_a.xml")
        self.assertEqual(self.session_state["reference_metadata"]["filename"], "ref_a.xml")

        # Replace source with minimal XML
        src_b = MockUploadedFile("src_b.xml", self.minimal_xml)
        handle_uploaded_metadata_file(src_b, "source", self.session_state)

        self.assertEqual(self.session_state["source_metadata"]["filename"], "src_b.xml")
        self.assertEqual(self.session_state["source_metadata"]["raw_fields"]["product_identifier"], "TEST_MINIMAL_001")
        # Reference metadata MUST remain completely unchanged
        self.assertEqual(self.session_state["reference_metadata"]["filename"], "ref_a.xml")
        self.assertEqual(self.session_state["reference_metadata"]["raw_fields"]["product_identifier"], "LRO_REF_TILE_005")

    def test_10_starting_new_run_clears_old_metadata(self):
        """10. Starting a new run / session clears old metadata."""
        mock_src = MockUploadedFile("source.xml", self.ch2_xml_bytes)
        handle_uploaded_metadata_file(mock_src, "source", self.session_state)
        self.assertIn("source_metadata", self.session_state)

        # Clear session
        clear_metadata_state(self.session_state)
        self.assertNotIn("source_metadata", self.session_state)
        self.assertNotIn("source_metadata_file", self.session_state)
        self.assertNotIn("reference_metadata", self.session_state)
        self.assertNotIn("reference_metadata_file", self.session_state)

    def test_11_metadata_from_run_a_does_not_appear_in_run_b(self):
        """11. Metadata from Run A does not appear in Run B."""
        # Run A
        mock_src = MockUploadedFile("source_a.xml", self.ch2_xml_bytes)
        handle_uploaded_metadata_file(mock_src, "source", self.session_state)

        run_a_result = {
            "run_id": "RUN_A",
            "success": True,
            "source_metadata": self.session_state.get("source_metadata"),
            "reference_metadata": self.session_state.get("reference_metadata"),
        }
        self.assertIsNotNone(run_a_result["source_metadata"])

        # Reset session for Run B
        clear_metadata_state(self.session_state)
        run_b_result = {
            "run_id": "RUN_B",
            "success": True,
            "source_metadata": self.session_state.get("source_metadata"),
            "reference_metadata": self.session_state.get("reference_metadata"),
        }

        self.assertIsNotNone(run_a_result["source_metadata"])
        self.assertIsNone(run_b_result["source_metadata"])
        self.assertNotEqual(run_a_result["source_metadata"], run_b_result["source_metadata"])

    def test_12_application_compiles_and_imports_successfully(self):
        """12. Application and metadata module compile and import cleanly."""
        app_path = os.path.join(APP_DIR, "app.py")
        meta_path = os.path.join(APP_DIR, "metadata_parser.py")

        self.assertTrue(os.path.exists(app_path))
        self.assertTrue(os.path.exists(meta_path))

        py_compile.compile(app_path, doraise=True)
        py_compile.compile(meta_path, doraise=True)

    def test_13_real_chandrayaan2_xml_verification_case(self):
        """13. Verified extraction against real Chandrayaan-2 OHRC XML."""
        parsed = parse_metadata_xml(self.ch2_xml_bytes, "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03.xml")
        self.assertTrue(parsed["valid"])

        rf = parsed["raw_fields"]
        self.assertEqual(rf["product_identifier"], "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03")
        self.assertEqual(rf["ground_sample_distance"], "0.26 m/px")
        self.assertEqual(rf["altitude"], "100.78 km")
        self.assertEqual(rf["solar_azimuth"], "299.64°")
        self.assertEqual(rf["solar_elevation"], "2.11°")
        self.assertEqual(rf["incidence_angle"], "87.89°")
        self.assertEqual(rf["sensor_platform"], "OHRC (Optical High Resolution Camera) / Chandrayaan-2")
        self.assertIn("12000", rf["image_dimensions"])
        self.assertIn("Polar stereographic", rf["coordinate_reference"])
        self.assertIn("Roll", rf["observation_geometry"])

        # Corners
        corners = parsed.get("corners")
        self.assertIsNotNone(corners)
        self.assertIn("topleft", corners)
        self.assertIn("bottomright", corners)

    def test_14_ui_rendering_scenarios_a_to_f(self):
        """14. Tests UI rendering requirements A through F for user metadata summary cards."""
        # A. No metadata uploaded -> both cards render correctly with Not uploaded status and No metadata file uploaded
        card_a_src = get_metadata_card_html("Source Metadata", None)
        card_a_ref = get_metadata_card_html("Reference Metadata", None)

        self.assertIn("○ Not uploaded", card_a_src)
        self.assertIn("No metadata file uploaded", card_a_src)
        self.assertIn("Not available", card_a_src)

        self.assertIn("○ Not uploaded", card_a_ref)
        self.assertIn("No metadata file uploaded", card_a_ref)
        self.assertIn("Not available", card_a_ref)

        # B. Source metadata only -> source card shows Loaded, reference shows Not uploaded
        parsed_src = parse_metadata_xml(self.ch2_xml_bytes, "source_ch2.xml")
        card_b_src = get_metadata_card_html("Source Metadata", parsed_src)
        card_b_ref = get_metadata_card_html("Reference Metadata", None)

        self.assertIn("● Loaded", card_b_src)
        self.assertIn("source_ch2.xml", card_b_src)
        self.assertIn("OHRXXD18CHO2359602NNNN24342131250969_V1_0_03", card_b_src)
        self.assertIn("0.26 m/px", card_b_src)

        self.assertIn("○ Not uploaded", card_b_ref)
        self.assertIn("No metadata file uploaded", card_b_ref)

        # C. Reference metadata only -> reference card shows Loaded, source shows Not uploaded
        parsed_ref = parse_metadata_xml(self.ref_xml, "reference_lro.xml")
        card_c_src = get_metadata_card_html("Source Metadata", None)
        card_c_ref = get_metadata_card_html("Reference Metadata", parsed_ref)

        self.assertIn("○ Not uploaded", card_c_src)
        self.assertIn("● Loaded", card_c_ref)
        self.assertIn("reference_lro.xml", card_c_ref)
        self.assertIn("LRO_REF_TILE_005", card_c_ref)
        self.assertIn("5.0 m/px", card_c_ref)

        # D. Both metadata uploaded -> both cards show correct independent values
        card_d_src = get_metadata_card_html("Source Metadata", parsed_src)
        card_d_ref = get_metadata_card_html("Reference Metadata", parsed_ref)

        self.assertIn("● Loaded", card_d_src)
        self.assertIn("source_ch2.xml", card_d_src)
        self.assertIn("0.26 m/px", card_d_src)

        self.assertIn("● Loaded", card_d_ref)
        self.assertIn("reference_lro.xml", card_d_ref)
        self.assertIn("5.0 m/px", card_d_ref)

        # E. Invalid XML -> existing error handling remains unchanged with Error badge
        card_e = get_metadata_card_html("Source Metadata", None, error_msg="Invalid XML format: unclosed tag")
        self.assertIn("✕ Error", card_e)
        self.assertIn("Invalid XML format: unclosed tag", card_e)

        # F. Verify that no literal "<div", "<span", "style=" or "</div>" appears as visible text in the rendered UI
        # In CommonMark, any line with 4+ spaces or a tab becomes an indented code block where tags display as visible code.
        # Verify that EVERY line in the generated HTML has zero leading whitespace (no 4-space indentation)
        for card_html in [card_a_src, card_a_ref, card_b_src, card_b_ref, card_c_src, card_c_ref, card_d_src, card_d_ref, card_e]:
            lines = card_html.splitlines()
            for line_idx, line in enumerate(lines):
                self.assertFalse(line.startswith("    "), f"Line {line_idx} starts with 4 spaces: {line}")
                self.assertFalse(line.startswith("\t"), f"Line {line_idx} starts with tab: {line}")
                self.assertTrue(len(line) > 0, f"Line {line_idx} is empty which could break HTML block")
            # Verify no escaped HTML entities that would cause raw tags to display as text
            self.assertNotIn("&lt;div", card_html)
            self.assertNotIn("&lt;span", card_html)
            self.assertNotIn("```", card_html)
            # Verify word-break and overflow-wrap exist for long values
            self.assertIn("word-break", card_html)
            self.assertIn("overflow-wrap", card_html)


if __name__ == "__main__":
    unittest.main()
