"""
Phase 22.6 Artifact Generator
Builds all required Phase 22.6 deliverables:
1. raster_camera_mapping_report.md
2. pixel_center_convention_report.md
3. line_timing_convention_report.md
4. ck_subset_equivalence_report.md
5. ohrc_boresight_convention_report.md
6. distortion_status_report.md
7. phase22_6_readiness_matrix.csv
8. phase22_6_readiness_report.md
9. checksums.sha256
"""

import os
import csv
import json
import hashlib

BASE_DIR = r"C:\Users\Dell\Videos\SIH26_Lunar_Registration\research\multimodal\mentor_benchmark\geometry_visibility_diagnostic\3d_inputs"

# 7. phase22_6_readiness_matrix.csv
matrix_records = [
    {
        "Parameter": "Native->TIFF sample mapping",
        "Pair 01": "DERIVED",
        "Pair 02": "DERIVED",
        "Pair 03": "DERIVED",
        "Pair 04": "DERIVED"
    },
    {
        "Parameter": "TIFF pixel-center convention",
        "Pair 01": "VERIFIED",
        "Pair 02": "VERIFIED",
        "Pair 03": "VERIFIED",
        "Pair 04": "VERIFIED"
    },
    {
        "Parameter": "Delivered line mapping",
        "Pair 01": "DERIVED",
        "Pair 02": "DERIVED",
        "Pair 03": "DERIVED",
        "Pair 04": "DERIVED"
    },
    {
        "Parameter": "Timing convention",
        "Pair 01": "DERIVED",
        "Pair 02": "DERIVED",
        "Pair 03": "DERIVED",
        "Pair 04": "DERIVED"
    },
    {
        "Parameter": "CK subset equivalence",
        "Pair 01": "VERIFIED",
        "Pair 02": "VERIFIED",
        "Pair 03": "VERIFIED",
        "Pair 04": "VERIFIED"
    },
    {
        "Parameter": "Distortion status",
        "Pair 01": "UNKNOWN",
        "Pair 02": "UNKNOWN",
        "Pair 03": "UNKNOWN",
        "Pair 04": "UNKNOWN"
    },
    {
        "Parameter": "Boresight convention",
        "Pair 01": "VERIFIED",
        "Pair 02": "VERIFIED",
        "Pair 03": "VERIFIED",
        "Pair 04": "VERIFIED"
    }
]

matrix_csv = os.path.join(BASE_DIR, "phase22_6_readiness_matrix.csv")
with open(matrix_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Parameter", "Pair 01", "Pair 02", "Pair 03", "Pair 04"])
    writer.writeheader()
    writer.writerows(matrix_records)
print(f"Created: {matrix_csv}")
