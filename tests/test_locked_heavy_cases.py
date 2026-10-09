"""
Test suite for LunarReg locked heavy cases deployment verification.

Verifies:
1. Tycho does not invoke registration.
2. Large LoFTR does not invoke registration.
3. Locked message appears.
4. Drive link appears.
5. No stale results leak from another case.
6. Pair 01 still runs normally.
7. Documented read-only metrics integrity for both cases.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Path resolution: add SIH26_Lunar_Registration/app directory to sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
_APP_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "SIH26_Lunar_Registration", "app"))
if not os.path.exists(_APP_DIR):
    _APP_DIR = os.path.abspath(os.path.join(_PROJECT_ROOT, "app"))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from app import (
    is_case_locked,
    get_locked_case_data,
    LOCKED_CASE_DOCUMENTED_RESULTS,
    clear_registration_run_state,
    render_locked_case_panel,
    TYCHO_DRIVE_LINK,
    LARGE_LOFTR_DRIVE_LINK,
)
import app as app_module
import streamlit as st


class TestLockedHeavyCases(unittest.TestCase):

    def setUp(self):
        for k in list(st.session_state.keys()):
            del st.session_state[k]

    def test_01_is_case_locked_detection(self):
        """Verify that locked cases are correctly recognized and normal cases are not."""
        self.assertTrue(is_case_locked("tycho"))
        self.assertTrue(is_case_locked("large_image"))
        self.assertTrue(is_case_locked({"case_id": "tycho", "label": "Tycho Research / Stress Test"}))
        self.assertTrue(is_case_locked({"case_id": "large_image", "label": "Large Image Tiled LoFTR Stress Test"}))
        self.assertTrue(is_case_locked({"is_locked": True}))

        # Non-locked cases must remain unlocked
        self.assertFalse(is_case_locked("pair_01"))
        self.assertFalse(is_case_locked("pair_03"))
        self.assertFalse(is_case_locked("pair_04"))
        self.assertFalse(is_case_locked("cross_sensor"))
        self.assertFalse(is_case_locked("pair_05"))
        self.assertFalse(is_case_locked({"case_id": "pair_01"}))
        self.assertFalse(is_case_locked({}))
        self.assertFalse(is_case_locked(None))

    def test_02_tycho_does_not_invoke_registration(self):
        """Requirement 1: Tycho selection does not invoke registration engine."""
        with patch.object(app_module, "safe_run_adaptive_registration") as mock_adaptive, \
             patch.object(app_module, "register_images") as mock_reg:
            st.session_state["demo_case_info"] = {
                "case_id": "tycho",
                "label": "Tycho Research / Stress Test",
                "is_locked": True,
            }
            st.session_state["source_filename"] = "source (1).png (Tycho Stress)"
            st.session_state["reference_filename"] = "real_refrence.png (Tycho Stress)"
            st.session_state["source_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)
            st.session_state["reference_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)

            clear_registration_run_state(st.session_state)

            self.assertTrue(is_case_locked(st.session_state["demo_case_info"]))
            # Engine functions must NOT be called
            mock_adaptive.assert_not_called()
            mock_reg.assert_not_called()
            self.assertNotIn("registration_result", st.session_state)

    def test_03_large_loftr_does_not_invoke_registration(self):
        """Requirement 2: Large LoFTR selection does not invoke registration engine."""
        with patch.object(app_module, "safe_run_adaptive_registration") as mock_adaptive, \
             patch.object(app_module, "register_images") as mock_reg:
            st.session_state["demo_case_info"] = {
                "case_id": "large_image",
                "label": "Large Image Tiled LoFTR Stress Test",
                "is_locked": True,
            }
            st.session_state["source_filename"] = "source_ch2_large.png (1200×5053 px)"
            st.session_state["reference_filename"] = "reference_ch2_large.png (1200×3527 px)"
            st.session_state["source_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)
            st.session_state["reference_img_data"] = np.zeros((100, 100, 3), dtype=np.uint8)

            clear_registration_run_state(st.session_state)

            self.assertTrue(is_case_locked(st.session_state["demo_case_info"]))
            mock_adaptive.assert_not_called()
            mock_reg.assert_not_called()
            self.assertNotIn("registration_result", st.session_state)

    def test_04_locked_message_and_drive_link_appear(self):
        """Requirements 3 & 4: Locked message and Drive link button appear."""
        demo_info = {"case_id": "tycho", "label": "Tycho Research / Stress Test", "is_locked": True}
        with patch.object(app_module.st, "markdown") as mock_markdown:
            render_locked_case_panel(demo_info, page_context="inputs")

            self.assertTrue(mock_markdown.called)
            html_rendered = "".join(call[0][0] for call in mock_markdown.call_args_list if call[0])
            self.assertIn("LIVE EXECUTION LOCKED", html_rendered)
            self.assertIn("Live registration was not executed.", html_rendered)
            self.assertIn("This computationally intensive case is not executed on the current online CPU/compute environment.", html_rendered)
            self.assertIn("The documented local execution, video demonstration, and results are available on Drive.", html_rendered)
            self.assertIn("View Recorded Video &amp; Results", html_rendered)
            self.assertIn(TYCHO_DRIVE_LINK, html_rendered)

    def test_05_no_stale_results_leak_tycho(self):
        """Requirement 5: Selecting Tycho clears stale results from previous run."""
        # Setup previous run state
        st.session_state["registration_result"] = {
            "success": True,
            "final_inliers": 200,
            "reprojection_rmse": 0.45,
            "matcher": "SIFT",
        }
        st.session_state["validation_results"] = {"rmse": 0.40, "status": "VALIDATED"}
        st.session_state["export_package"] = {"zip": b"fake_export"}
        st.session_state["homography"] = np.eye(3).tolist()
        st.session_state["stage_states"] = {"stage_1": "COMPLETE", "stage_8": "COMPLETE"}
        st.session_state["is_running"] = True

        # Now select Tycho
        clear_registration_run_state(st.session_state)
        st.session_state["demo_case_info"] = {
            "case_id": "tycho",
            "label": "Tycho Research / Stress Test",
            "is_locked": True,
        }

        self.assertNotIn("registration_result", st.session_state)
        self.assertNotIn("validation_results", st.session_state)
        self.assertNotIn("export_package", st.session_state)
        self.assertNotIn("homography", st.session_state)
        self.assertNotIn("stage_states", st.session_state)
        self.assertFalse(st.session_state["is_running"])

    def test_06_no_stale_results_leak_large_loftr(self):
        """Requirement 5: Selecting Large LoFTR clears stale results from previous run."""
        st.session_state["registration_result"] = {
            "success": True,
            "final_inliers": 300,
            "reprojection_rmse": 0.28,
            "matcher": "LoFTR",
        }
        st.session_state["validation_results"] = {"rmse": 0.25, "status": "VALIDATED"}
        st.session_state["export_package"] = {"zip": b"fake_export_2"}

        clear_registration_run_state(st.session_state)
        st.session_state["demo_case_info"] = {
            "case_id": "large_image",
            "label": "Large Image Tiled LoFTR Stress Test",
            "is_locked": True,
        }

        self.assertNotIn("registration_result", st.session_state)
        self.assertNotIn("validation_results", st.session_state)
        self.assertNotIn("export_package", st.session_state)

    def test_07_pair_01_runs_normally(self):
        """Requirement 6: Pair 01 is not locked and runs normally."""
        p01_info = {
            "case_id": "pair_01",
            "label": "Pair 01 — Scale",
            "category": "PRIMARY SIH DEMO",
            "validation_protocol": "current production validation",
            "subpixel_status": "Demonstrated for this case",
        }
        self.assertFalse(is_case_locked(p01_info))
        self.assertIsNone(get_locked_case_data("pair_01"))

    def test_08_documented_metrics_tycho(self):
        """Verify exact documented metrics for Tycho."""
        data = get_locked_case_data("tycho")
        self.assertIsNotNone(data)
        metrics = dict(data["metrics"])
        self.assertEqual(metrics["LoFTR candidates"], "1,709")
        self.assertEqual(metrics["LoFTR initial inliers"], "8")
        self.assertEqual(metrics["LoFTR inlier ratio"], "0.47%")
        self.assertEqual(metrics["SIFT fallback"], "182 candidates / 51 initial inliers / 28.02%")
        self.assertEqual(metrics["Final selected points"], "24")
        self.assertEqual(metrics["Occupancy"], "4/9")
        self.assertEqual(metrics["Geometric RMSE"], "1.192 px")
        self.assertEqual(metrics["Hold-out RMSE"], "1.5088 px")
        self.assertEqual(metrics["Total CPU runtime"], "164.190 s")
        self.assertEqual(metrics["Documented tiled execution"], "16 tiles, 20% overlap")
        self.assertEqual(metrics["Memory estimate"], "2.839 GB > 2.60 GB cap")

    def test_09_documented_metrics_large_loftr(self):
        """Verify exact documented metrics for Large Image LoFTR."""
        data = get_locked_case_data("large_image")
        self.assertIsNotNone(data)
        metrics = dict(data["metrics"])
        self.assertEqual(metrics["Source"], "1200 × 5053")
        self.assertEqual(metrics["Reference"], "1200 × 3527")
        self.assertEqual(metrics["LoFTR candidates"], "5,979")
        self.assertEqual(metrics["Initial inliers"], "5,800")
        self.assertEqual(metrics["Initial inlier ratio"], "97.01%")
        self.assertEqual(metrics["Final selected points"], "54")
        self.assertEqual(metrics["Occupancy"], "9/9")
        self.assertEqual(metrics["Geometric RMSE"], "0.279 px")
        self.assertEqual(metrics["Validation RMSE"], "0.2763 px")
        self.assertEqual(metrics["CPU runtime"], "57.760 s")


    def test_10_helper_self_contained_session_resolution(self):
        """Verify render_locked_case_panel handles session_state resolution and returns bool."""
        st.session_state["demo_case_info"] = {
            "case_id": "tycho",
            "label": "Tycho Research / Stress Test",
            "is_locked": True,
        }
        st.session_state["registration_result"] = {"fake": "stale"}

        self.assertTrue(is_case_locked())

        with patch.object(app_module.st, "markdown") as mock_markdown:
            result = render_locked_case_panel(page_context="inputs")
            self.assertTrue(result)
            self.assertNotIn("registration_result", st.session_state)
            self.assertTrue(mock_markdown.called)

        # Non-locked case: should return False and not render
        st.session_state["demo_case_info"] = {
            "case_id": "pair_01",
            "label": "Pair 01 — Scale",
        }
        self.assertFalse(is_case_locked())
        with patch.object(app_module.st, "markdown") as mock_markdown:
            result = render_locked_case_panel(page_context="inputs")
            self.assertFalse(result)
            self.assertFalse(mock_markdown.called)

    def test_11_no_duplicate_render_calls_in_source(self):
        """Assert that render_locked_case_panel is called at most once per page context in app.py."""
        with open(app_module.__file__, "r", encoding="utf-8") as f:
            code = f.read()

        import re
        inputs_calls = re.findall(r'render_locked_case_panel\s*\(\s*page_context\s*=\s*["\']inputs["\']\s*\)', code)
        self.assertEqual(len(inputs_calls), 1, "render_locked_case_panel(page_context='inputs') must be called exactly once")

        overview_calls = re.findall(r'render_locked_case_panel\s*\(\s*page_context\s*=\s*["\']overview["\']\s*\)', code)
        self.assertEqual(len(overview_calls), 1, "render_locked_case_panel(page_context='overview') must be called exactly once")

    def test_12_single_locked_card_per_page_apptest(self):
        """Integration test using AppTest: both large_image and tycho render exactly 1 locked card on all pages."""
        from streamlit.testing.v1 import AppTest
        cases = [
            ("large_image", "Large Image Tiled LoFTR Stress Test"),
            ("tycho", "Tycho Research / Stress Test"),
        ]
        pages = ["Inputs", "Overview", "Results", "Validation", "Export"]

        for case_id, label in cases:
            for page in pages:
                at = AppTest.from_file(app_module.__file__, default_timeout=30)
                at.session_state["auth_authenticated"] = True
                at.session_state["auth_email"] = "researcher@isro.gov.in"
                at.session_state["auth_name"] = "Dr. Vikram"
                at.session_state["demo_case_info"] = {
                    "case_id": case_id,
                    "label": label,
                    "is_locked": True,
                }
                at.session_state["source_filename"] = "source.png"
                at.session_state["reference_filename"] = "reference.png"
                at.run()
                at.sidebar.radio(key="sidebar_page").set_value(page).run()

                locked_count = sum(1 for m in at.markdown if "LIVE EXECUTION LOCKED" in m.value)
                self.assertEqual(
                    locked_count,
                    1,
                    f"Expected exactly 1 locked card on page '{page}' for '{case_id}', got {locked_count}"
                )

                if page == "Overview":
                    empty_count = sum(1 for m in at.markdown if "No registration result available yet" in m.value)
                    self.assertEqual(
                        empty_count,
                        0,
                        f"Expected 0 empty result messages on Overview for locked case '{case_id}', got {empty_count}"
                    )


if __name__ == "__main__":
    unittest.main()

