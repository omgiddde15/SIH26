"""
LunarReg Phase 9 — Rotation-Normalized SSC research benchmark.

This benchmark deliberately isolates local orientation normalization. Scale
normalization is excluded from Phase 9. All candidate sets use the unchanged
common downstream registration layer.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.ssc_matcher import SSCConfig
from research.multimodal.ssc_benchmark import load_angle_pairs
from research.multimodal.ssc_robustness import apply_synthetic_rotation
from research.multimodal.ssc_rotation import (
    SSCRotationConfig,
    run_orientation_sign_sanity,
    run_ssc_rotation_matching,
)


def _flatten_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(rec)
    src = out.pop("source_orientation", {}) or {}
    ref = out.pop("reference_orientation", {}) or {}
    for prefix, data in (("source_orientation", src), ("reference_orientation", ref)):
        for key, value in data.items():
            out[f"{prefix}_{key}"] = value
    out.pop("match_result", None)
    out.pop("downstream_result", None)
    return out


def _load_gray(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not decode image: {path}")
    return img


def run_phase9_rotation_benchmark(
    iirs_src_path: str,
    iirs_ref_path: str,
    angle_pairs_base_dir: Optional[str] = None,
    csv_out_path: Optional[str] = None,
    report_out_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run sign sanity plus all Phase 9 benchmark conditions."""
    sanity = run_orientation_sign_sanity()
    if sanity["status"] != "PASS":
        raise RuntimeError(f"Phase 9 orientation-sign sanity check failed: {sanity}")

    source = _load_gray(iirs_src_path)
    reference = _load_gray(iirs_ref_path)
    config = SSCRotationConfig(ssc=SSCConfig())

    rows: List[Dict[str, Any]] = []

    # Native primary pair.
    rows.append(
        _flatten_record(
            run_ssc_rotation_matching(
                source,
                reference,
                config=config,
                pair_label="IIRS <-> OHRC | Native",
            )
        )
    )

    # Synthetic rotations of the source against the unchanged reference.
    for angle in (10.0, 20.0, 30.0, -20.0):
        rotated = apply_synthetic_rotation(source, angle)
        rows.append(
            _flatten_record(
                run_ssc_rotation_matching(
                    rotated,
                    reference,
                    config=config,
                    pair_label=f"IIRS <-> OHRC | Synthetic Rotation {angle:+.0f} deg",
                )
            )
        )

    # Existing real control pairs.
    pair_info = load_angle_pairs(angle_pairs_base_dir)
    by_id = {p["pair_id"]: p for p in pair_info.get("valid_pairs", [])}
    for pair_id in ("pair_01", "pair_02", "pair_03"):
        item = by_id.get(pair_id)
        if item is None:
            rows.append(
                {
                    "pair": pair_id,
                    "method": "Rotation-normalized SSC-style 2-D adaptation",
                    "failure_stage": "pair_loader",
                    "failure_reason": "Required control pair unavailable.",
                    "success": False,
                }
            )
            continue
        src = cv2.imread(item["source_path"], cv2.IMREAD_GRAYSCALE)
        ref = cv2.imread(item["reference_path"], cv2.IMREAD_GRAYSCALE)
        rec = run_ssc_rotation_matching(
            src,
            ref,
            config=config,
            pair_label=f"{pair_id} | Real Control",
        )
        rec["pair_id"] = pair_id
        rec["metadata"] = item.get("metadata", {})
        rows.append(_flatten_record(rec))

    df = pd.DataFrame(rows)

    result: Dict[str, Any] = {
        "orientation_sign_sanity": sanity,
        "results": rows,
        "comparison_table": df,
        "configuration": {
            "orientation_estimator": "Sobel structure tensor",
            "tensor_window": config.tensor_window,
            "tensor_sigma": config.tensor_sigma,
            "coherence_threshold": config.coherence_threshold,
            "trace_threshold": config.trace_threshold,
            "orientation_convention": config.orientation_convention,
            "descriptor_dimension": 21,
            "nndr_threshold": config.ssc.nndr_threshold,
            "ransac_thresh": 3.0,
            "seeds": [1, 2, 3, 4, 5],
        },
    }

    if csv_out_path:
        Path(csv_out_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_out_path, index=False)

    if report_out_path:
        Path(report_out_path).parent.mkdir(parents=True, exist_ok=True)
        _write_report(result, report_out_path, iirs_src_path, iirs_ref_path)

    return result


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if np.isnan(v):
            return "NaN"
        return f"{v:.4f}"
    return str(v)


def _write_report(result: Dict[str, Any], path: str, src_path: str, ref_path: str) -> None:
    sanity = result["orientation_sign_sanity"]
    rows = result["results"]
    cfg = result["configuration"]

    lines: List[str] = []
    lines += [
        "# LunarReg Phase 9 — Rotation-Normalized SSC Research Report",
        "",
        "## 1. Scope",
        "",
        "> Phase 9 tests whether local structure-tensor orientation normalization improves the rotation robustness of the frozen Phase 7 SSC-style descriptor without changing its detector, descriptor dimension, matching policy, or common downstream geometry.",
        "",
        "## 2. Frozen Architecture",
        "",
        f"- Detector: Independent Sobel-gradient + FAST (Phase 7/8 frozen detector)",
        f"- Descriptor: SSC-style 2-D adaptation, 21-D",
        f"- Matching: forward KNN k=2 + mutual check + NNDR {cfg['nndr_threshold']:.2f}",
        f"- Orientation estimator: Sobel structure tensor, {cfg['tensor_window']}×{cfg['tensor_window']} Gaussian window, sigma={cfg['tensor_sigma']}",
        f"- Coherence threshold: {cfg['coherence_threshold']}",
        f"- Trace threshold: {cfg['trace_threshold']}",
        f"- Orientation convention: {cfg['orientation_convention']}",
        "- RANSAC threshold: 3.0 px",
        "- Spatial selection: 3×3, maximum 6 points/cell",
        "- Held-out seeds: 1–5",
        "- Scale normalization: NOT tested in Phase 9",
        "- RIFT2 dependency: None",
        "",
        "## 3. Rotation-Sign Sanity Check",
        "",
        f"- Synthetic rotation: +{sanity['synthetic_rotation_deg']:.0f}°",
        f"- Original tensor angle: {sanity['theta_original_deg']:.4f}°",
        f"- Rotated tensor angle: {sanity['theta_rotated_deg']:.4f}°",
        f"- Observed angle change: {sanity['theta_change_deg']:.4f}°",
        f"- R(+theta) descriptor distance: {sanity['R_plus_theta_descriptor_distance']:.6f}",
        f"- R(-theta) descriptor distance: {sanity['R_minus_theta_descriptor_distance']:.6f}",
        f"- Selected convention: {sanity['selected_convention']}",
        f"- Sanity status: **{sanity['status']}**",
        "",
        "## 4. Benchmark Matrix",
        "",
        "| Pair | Candidates | Inliers | Ratio | Fit RMSE (px) | Held-out RMSE (px) | Valid | Failure Stage |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("pair", "")),
                    _fmt(row.get("candidates")),
                    _fmt(row.get("initial_inliers")),
                    _fmt(row.get("initial_inlier_ratio")),
                    _fmt(row.get("fit_rmse")),
                    _fmt(row.get("independent_held_out_rmse")),
                    "VALID" if row.get("success") else "NO_VALID_CHECK",
                    str(row.get("failure_stage") or ""),
                ]
            )
            + "|"
        )

    lines += [
        "",
        "## 5. Interpretation Rules",
        "",
        "- Native IIRS↔OHRC quality is compared against the frozen Phase 7/8 SSC baseline, not against the best Phase 9 trial.",
        "- Synthetic rotation results test the proposed orientation normalization but do not establish general rotation invariance.",
        "- `VALID` means the existing independent held-out procedure completed; it does not by itself mean the registration is application-accurate.",
        "- Scale robustness is outside Phase 9 scope.",
        "",
        "## 6. Production Boundary",
        "",
        "> Phase 9 is research-only. Production routing, quality gates, Locked LoFTR, RANSAC, spatial selection, and common downstream registration remain unchanged.",
        "",
        f"Primary source: `{src_path}`",
        f"Primary reference: `{ref_path}`",
        "",
    ]

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LunarReg Phase 9 rotation-normalized SSC benchmark")
    parser.add_argument("--iirs-source", required=True)
    parser.add_argument("--ohrc-reference", required=True)
    parser.add_argument("--angle-pairs-dir", default=None)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    result = run_phase9_rotation_benchmark(
        iirs_src_path=args.iirs_source,
        iirs_ref_path=args.ohrc_reference,
        angle_pairs_base_dir=args.angle_pairs_dir,
        csv_out_path=args.csv,
        report_out_path=args.report,
    )
    print(json.dumps(result["orientation_sign_sanity"], indent=2))
    print(result["comparison_table"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
