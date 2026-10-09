"""
Regression Test Suite for LunarReg Live PDF Export
Tests for:
1. Bug fix: Separation of immutable canonical historical evidence PDF from live run-specific PDF export.
2. Requirement 9: Stale PDF reuse regression test (Test A: Success, Test B: Safe Rejection).
3. Requirement 10: Run A (Success) -> Run B (Safe Rejection) export test.
4. Requirement 1 & 7: Canonical PDF generation remains available and unchanged; validator works.
"""

import os
import sys
import io
import unittest
import numpy as np
import pypdf

# Add app directory to sys.path
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if not os.path.exists(APP_DIR):
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SIH26_Lunar_Registration", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from pdf_generator import (
    generate_scientific_pdf_report,
    generate_canonical_evidence_pdf,
    validate_pdf_report,
)
from app import build_registration_export_package


class TestPdfExportRegression(unittest.TestCase):

    def setUp(self):
        self.s_img = np.zeros((400, 400, 3), dtype=np.uint8)
        self.r_img = np.zeros((400, 400, 3), dtype=np.uint8)

    def test_requirement_9_stale_pdf_reuse(self):
        """
        REQUIREMENT 9:
        TEST A:
        Create a synthetic/current result with obviously unique values:
        candidate_count = 1111
        final_inliers = 77
        status = "SUCCESS"
        run_id = "TEST_RUN_A"
        Generate PDF A.

        TEST B:
        Create a second result with:
        candidate_count = 2222
        final_inliers = 13
        status = "SAFE REJECTION"
        run_id = "TEST_RUN_B"
        Generate PDF B.

        Assertions:
        - PDF A is valid.
        - PDF B is valid.
        - PDF A and PDF B are not byte-identical.
        - Extracted PDF A text contains TEST_RUN_A / 1111 / 77.
        - Extracted PDF B text contains TEST_RUN_B / 2222 / 13.
        - PDF B does NOT contain the SUCCESS result from Test A.
        - Neither test uses the canonical historical PDF as its live export.
        """
        # TEST A
        res_a = {
            "candidate_count": 1111,
            "candidate_matches": 1111,
            "final_inliers": 77,
            "status": "SUCCESS",
            "success": True,
            "registration_accepted": True,
            "run_id": "TEST_RUN_A",
            "runtime_seconds": 2.345,
            "source_filename": "source_a.png",
            "reference_filename": "ref_a.png",
        }
        pdf_a = generate_scientific_pdf_report(
            res=res_a,
            s_img=self.s_img,
            r_img=self.r_img,
            s_filename="source_a.png",
            r_filename="ref_a.png",
            timestamp="TEST_RUN_A",
        )

        # TEST B
        res_b = {
            "candidate_count": 2222,
            "candidate_matches": 2222,
            "final_inliers": 13,
            "status": "SAFE REJECTION",
            "success": False,
            "registration_accepted": False,
            "rejection_reason": "Low inlier consensus below threshold",
            "run_id": "TEST_RUN_B",
            "runtime_seconds": 0.876,
            "source_filename": "source_b.png",
            "reference_filename": "ref_b.png",
        }
        pdf_b = generate_scientific_pdf_report(
            res=res_b,
            s_img=self.s_img,
            r_img=self.r_img,
            s_filename="source_b.png",
            r_filename="ref_b.png",
            timestamp="TEST_RUN_B",
        )

        # Assertion: PDF A is valid
        ok_a, msg_a = validate_pdf_report(pdf_a)
        self.assertTrue(ok_a, f"PDF A validation failed: {msg_a}")

        # Assertion: PDF B is valid
        ok_b, msg_b = validate_pdf_report(pdf_b)
        self.assertTrue(ok_b, f"PDF B validation failed: {msg_b}")

        # Assertion: PDF A and PDF B are not byte-identical
        self.assertNotEqual(pdf_a, pdf_b, "PDF A and PDF B must NOT be byte-identical!")

        # Extract text
        reader_a = pypdf.PdfReader(io.BytesIO(pdf_a))
        self.assertEqual(len(reader_a.pages), 7, f"Expected 7 pages for PDF A, got {len(reader_a.pages)}")
        text_a = "\n".join([page.extract_text() for page in reader_a.pages])

        reader_b = pypdf.PdfReader(io.BytesIO(pdf_b))
        self.assertEqual(len(reader_b.pages), 7, f"Expected 7 pages for PDF B, got {len(reader_b.pages)}")
        text_b = "\n".join([page.extract_text() for page in reader_b.pages])

        # Assertion: Extracted PDF A text contains TEST_RUN_A / 1111 / 77
        self.assertIn("TEST_RUN_A", text_a, "PDF A must contain run_id TEST_RUN_A")
        self.assertIn("1111", text_a, "PDF A must contain candidate_count 1111")
        self.assertIn("77", text_a, "PDF A must contain final_inliers 77")
        self.assertIn("ACCEPTED REGISTRATION", text_a, "PDF A must report ACCEPTED REGISTRATION")

        # Assertion: Extracted PDF B text contains TEST_RUN_B / 2222 / 13
        self.assertIn("TEST_RUN_B", text_b, "PDF B must contain run_id TEST_RUN_B")
        self.assertIn("2222", text_b, "PDF B must contain candidate_count 2222")
        self.assertIn("13", text_b, "PDF B must contain final_inliers 13")
        self.assertIn("SAFE REJECTION", text_b, "PDF B must report SAFE REJECTION")

        # Assertion: PDF B does NOT contain the SUCCESS result from Test A
        self.assertNotIn("TEST_RUN_A", text_b, "PDF B must NOT contain TEST_RUN_A from Test A")
        self.assertNotIn("1111", text_b, "PDF B must NOT contain 1111 from Test A")
        self.assertNotIn("77", text_b, "PDF B must NOT contain 77 from Test A")
        self.assertNotIn("ACCEPTED REGISTRATION", text_b, "PDF B must NOT contain ACCEPTED REGISTRATION")

        # Assertion: Neither test uses the canonical historical PDF as its live export
        canonical_pdf = generate_canonical_evidence_pdf()
        self.assertNotEqual(pdf_a, canonical_pdf, "PDF A must not be the canonical historical PDF")
        self.assertNotEqual(pdf_b, canonical_pdf, "PDF B must not be the canonical historical PDF")

        # Check that canonical historical markers are NOT in PDF A or B
        self.assertNotIn("Pair 04 Optical", text_a, "PDF A should not have canonical historical marker")
        self.assertNotIn("Pair 04 Optical", text_b, "PDF B should not have canonical historical marker")

    def test_requirement_10_sequential_run_export(self):
        """
        REQUIREMENT 10:
        Add a specific regression test:
        Run A = successful registration.
        Run B = safe rejection.
        Export B.
        Assert B's PDF reports safe rejection and does not contain Run A metrics.
        """
        # Run A = successful registration
        res_a = {
            "success": True,
            "registration_accepted": True,
            "status": "SUCCESS",
            "candidate_matches": 850,
            "final_inliers": 92,
            "inlier_ratio": 0.54,
            "spatial_occupancy": 8.0 / 9.0,
            "reprojection_rmse": 0.42,
            "independent_validation_rmse": 0.49,
            "runtime": 3.12,
            "run_id": "RUN_A_SUCCESS",
            "final_matcher_used": "LoFTR",
        }

        # Run B = safe rejection
        res_b = {
            "success": False,
            "registration_accepted": False,
            "status": "SAFE REJECTION",
            "rejection_reason": "Geometric inlier count (4) fell below safety threshold (8)",
            "candidate_matches": 420,
            "final_inliers": 4,
            "inlier_ratio": 0.08,
            "spatial_occupancy": 2.0 / 9.0,
            "reprojection_rmse": 4.15,
            "independent_validation_rmse": None,
            "runtime": 1.05,
            "run_id": "RUN_B_REJECTED",
            "final_matcher_used": "LoFTR",
        }

        # Export B via build_registration_export_package
        export_pkg_b = build_registration_export_package(
            res_b,
            self.s_img,
            self.r_img,
            s_filename="b_source.png",
            r_filename="b_ref.png"
        )

        pdf_bytes_b = export_pkg_b["pdf"]["bytes"]
        self.assertTrue(len(pdf_bytes_b) > 10000, "Export B PDF should be non-empty")

        ok_b, msg_b = validate_pdf_report(pdf_bytes_b)
        self.assertTrue(ok_b, f"Export B PDF validation failed: {msg_b}")

        reader_b = pypdf.PdfReader(io.BytesIO(pdf_bytes_b))
        text_b = "\n".join([page.extract_text() for page in reader_b.pages])

        # Assert B's PDF reports safe rejection
        self.assertIn("SAFE REJECTION", text_b, "Export B PDF must report SAFE REJECTION")
        self.assertIn("Geometric inlier count (4) fell below safety threshold (8)", text_b, "Export B must contain rejection reason")

        # Assert B's PDF does not contain Run A metrics
        self.assertNotIn("RUN_A_SUCCESS", text_b, "Export B must not contain Run A identifier")
        self.assertNotIn("850", text_b, "Export B must not contain Run A candidate matches (850)")
        self.assertNotIn("92 pts", text_b, "Export B must not contain Run A inliers (92)")
        self.assertNotIn("ACCEPTED REGISTRATION", text_b, "Export B must not report ACCEPTED REGISTRATION")

        # Verify ZIP archive contains the exact same run-specific PDF
        import zipfile
        zf = zipfile.ZipFile(io.BytesIO(export_pkg_b["zip"]["bytes"]))
        pdf_name_in_zip = export_pkg_b["pdf"]["filename"]
        zip_pdf_bytes = zf.read(pdf_name_in_zip)
        self.assertEqual(pdf_bytes_b, zip_pdf_bytes, "PDF in ZIP must be byte-identical to standalone PDF export")

    def test_canonical_pdf_available_and_unchanged(self):
        """
        REQUIREMENT 1:
        KEEP the canonical 7-page evidence PDF completely unchanged.
        - It is an archived historical/reference artifact.
        - Do not rewrite its content or layout.
        - Do not remove canonical generation functionality.
        """
        canonical_bytes = generate_canonical_evidence_pdf()
        self.assertTrue(isinstance(canonical_bytes, bytes))
        self.assertTrue(len(canonical_bytes) > 20000)

        ok, msg = validate_pdf_report(canonical_bytes)
        self.assertTrue(ok, f"Canonical PDF validation failed: {msg}")

        reader = pypdf.PdfReader(io.BytesIO(canonical_bytes))
        self.assertEqual(len(reader.pages), 7, "Canonical PDF must have exactly 7 pages")
        text = "\n".join([p.extract_text() for p in reader.pages])
        self.assertIn("Pair 04 Optical", text, "Canonical PDF must retain historical baseline content")


if __name__ == "__main__":
    unittest.main()
