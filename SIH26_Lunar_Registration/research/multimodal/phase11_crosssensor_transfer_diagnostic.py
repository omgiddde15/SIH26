"""
LunarReg Phase 11 — Native Cross-Sensor Transfer Diagnostic
Research-only. No production routing or thresholds are changed.

Question:
Why does Phase 9 improve controlled rotation matching but still fail on native
IIRS <-> OHRC?

Tracks:
A. Anchor feasibility using the existing LoFTR matcher as an external,
   matcher-derived diagnostic reference. Anchors are NOT ground truth.
B. Cross-sensor descriptor consistency at fixed anchor coordinates:
   frozen Phase 7 SSC vs frozen Phase 9 rotation-normalized SSC.
C. Fixed-anchor local-footprint / scale sensitivity. This is a sensitivity
   diagnostic, not a search or parameter-selection procedure.
D. Native end-to-end comparison using frozen Phase 7 and Phase 9 pipelines.

Outputs are deterministic CSV/JSON/Markdown artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from research.adaptive_matcher.adaptive_engine import run_loftr_matching
from research.multimodal.ssc_matcher import SSCConfig, compute_ssc_descriptors
from research.multimodal.ssc_matcher import run_ssc_matching
from research.multimodal.ssc_rotation import (
    SSCRotationConfig,
    compute_rotation_normalized_ssc_descriptors,
    run_ssc_rotation_matching,
)


DEFAULT_SOURCES = r"C:\Users\Dell\Downloads\souse.jpeg"
DEFAULT_REFERENCE = r"C:\Users\Dell\Downloads\ref.jpeg"

# Pre-declared diagnostic conditions. These are not selected adaptively.
REFERENCE_SCALES: Tuple[float, ...] = (1.50, 1.25, 1.0, 0.75, 0.50)
SOURCE_SCALES: Tuple[float, ...] = (1.50, 1.25, 1.0, 0.75, 0.50)


def _safe_float(value: Any) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _load_gray(path: str) -> np.ndarray:
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Failed to decode grayscale image: {path}")
    if image.size == 0:
        raise ValueError(f"Empty image: {path}")
    return image


def _load_color(path: str) -> np.ndarray:
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Failed to decode image: {path}")
    if image.size == 0:
        raise ValueError(f"Empty image: {path}")
    return image


def _stats(values: Sequence[float]) -> Dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "p90": None,
            "max": None,
        }
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(np.max(arr)),
    }


def _three_by_three_occupancy(points: np.ndarray, shape: Tuple[int, int]) -> float:
    if points is None or len(points) == 0:
        return 0.0
    h, w = shape
    cells = set()
    for x, y in np.asarray(points, dtype=np.float32):
        cx = min(2, max(0, int((float(x) / max(1.0, w)) * 3.0)))
        cy = min(2, max(0, int((float(y) / max(1.0, h)) * 3.0)))
        cells.add((cx, cy))
    return float(len(cells) / 9.0)


def _rescale_image_and_points(
    image: np.ndarray,
    points: np.ndarray,
    scale: float,
) -> Tuple[np.ndarray, np.ndarray]:
    if scale <= 0:
        raise ValueError("scale must be > 0")
    h, w = image.shape[:2]
    new_w = max(32, int(round(w * scale)))
    new_h = max(32, int(round(h * scale)))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    scaled = cv2.resize(image, (new_w, new_h), interpolation=interp)
    scaled_points = np.asarray(points, dtype=np.float32) * float(scale)
    return scaled, scaled_points


def _anchor_feasibility(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
) -> Dict[str, Any]:
    """
    Use the existing LoFTR matcher as an external diagnostic anchor source.
    Anchors are matcher-derived and must never be called ground truth.
    """
    started = time.perf_counter()
    result = run_loftr_matching(
        source_bgr,
        reference_bgr,
        loftr_model=None,
        ransac_thresh=3.0,
    )

    pts0 = np.asarray(result.get("inlier_pts0", np.empty((0, 2))), dtype=np.float32)
    pts1 = np.asarray(result.get("inlier_pts1", np.empty((0, 2))), dtype=np.float32)

    n_candidates = int(result.get("n_candidates", 0))
    n_reported_inliers = int(result.get("n_inliers", len(pts0)))
    n_anchor_pairs = int(min(len(pts0), len(pts1)))

    occupancy = _three_by_three_occupancy(
        pts0,
        source_bgr.shape[:2],
    )

    valid = n_anchor_pairs >= 8

    return {
        "anchor_source": "existing LoFTR matcher",
        "anchor_is_ground_truth": False,
        "candidates": n_candidates,
        "reported_initial_inliers": n_reported_inliers,
        "anchor_pairs": n_anchor_pairs,
        "source_spatial_occupancy_3x3": occupancy,
        "held_out_valid": bool(result.get("held_out_valid", False)),
        "held_out_rmse": _safe_float(result.get("mean_check_rmse")),
        "matcher_success": bool(result.get("success", False)),
        "failure_stage": result.get("failure_stage"),
        "failure_reason": result.get("failure_reason"),
        "anchor_feasibility_status": (
            "adequate_for_descriptor_diagnostic"
            if valid
            else "insufficient_anchor_pairs_for_8_point_reference"
        ),
        "runtime_sec": round(time.perf_counter() - started, 4),
        "pts0": pts0,
        "pts1": pts1,
    }


def _cross_sensor_descriptor_diagnostic(
    source_gray: np.ndarray,
    reference_gray: np.ndarray,
    pts0: np.ndarray,
    pts1: np.ndarray,
) -> Dict[str, Any]:
    phase7_config = SSCConfig()
    phase9_config = SSCRotationConfig()

    desc7_0 = compute_ssc_descriptors(source_gray, pts0, phase7_config)
    desc7_1 = compute_ssc_descriptors(reference_gray, pts1, phase7_config)
    desc9_0, stats9_0 = compute_rotation_normalized_ssc_descriptors(
        source_gray, pts0, phase9_config
    )
    desc9_1, stats9_1 = compute_rotation_normalized_ssc_descriptors(
        reference_gray, pts1, phase9_config
    )

    phase7_dist = np.linalg.norm(desc7_0 - desc7_1, axis=1)
    phase9_dist = np.linalg.norm(desc9_0 - desc9_1, axis=1)

    orientation_items = list(stats9_0) + list(stats9_1)
    valid_orientation = sum(1 for s in orientation_items if str(s["status"]) == "valid")
    low_conf = sum(1 for s in orientation_items if str(s["status"]) == "low_confidence")
    flat = sum(1 for s in orientation_items if str(s["status"]) == "flat")

    return {
        "anchor_pairs": int(len(pts0)),
        "phase7_mean_l2": _safe_float(np.mean(phase7_dist)),
        "phase7_median_l2": _safe_float(np.median(phase7_dist)),
        "phase7_p90_l2": _safe_float(np.percentile(phase7_dist, 90)),
        "phase7_max_l2": _safe_float(np.max(phase7_dist)),
        "phase9_mean_l2": _safe_float(np.mean(phase9_dist)),
        "phase9_median_l2": _safe_float(np.median(phase9_dist)),
        "phase9_p90_l2": _safe_float(np.percentile(phase9_dist, 90)),
        "phase9_max_l2": _safe_float(np.max(phase9_dist)),
        "phase9_valid_orientation_count": int(valid_orientation),
        "phase9_low_confidence_orientation_count": int(low_conf),
        "phase9_flat_orientation_count": int(flat),
        "phase9_orientation_valid_fraction": float(
            valid_orientation / max(1, len(orientation_items))
        ),
    }


def _fixed_anchor_scale_sensitivity(
    source_gray: np.ndarray,
    reference_gray: np.ndarray,
    pts0_native: np.ndarray,
    pts1_native: np.ndarray,
) -> List[Dict[str, Any]]:
    phase7_config = SSCConfig()
    phase9_config = SSCRotationConfig()
    rows: List[Dict[str, Any]] = []

    # Both one-sided scale changes and symmetric native case are pre-declared.
    conditions: List[Tuple[float, float]] = []
    for s in SOURCE_SCALES:
        if abs(s - 1.0) < 1e-12:
            conditions.append((s, 1.0))
    conditions.extend((1.0, r) for r in REFERENCE_SCALES if abs(r - 1.0) > 1e-12)
    conditions.extend((s, 1.0) for s in SOURCE_SCALES if abs(s - 1.0) > 1e-12)

    for source_scale, reference_scale in conditions:
        s_img, s_pts = _rescale_image_and_points(source_gray, pts0_native, source_scale)
        r_img, r_pts = _rescale_image_and_points(reference_gray, pts1_native, reference_scale)

        d7_s = compute_ssc_descriptors(s_img, s_pts, phase7_config)
        d7_r = compute_ssc_descriptors(r_img, r_pts, phase7_config)
        d9_s, st9_s = compute_rotation_normalized_ssc_descriptors(
            s_img, s_pts, phase9_config
        )
        d9_r, st9_r = compute_rotation_normalized_ssc_descriptors(
            r_img, r_pts, phase9_config
        )

        dist7 = np.linalg.norm(d7_s - d7_r, axis=1)
        dist9 = np.linalg.norm(d9_s - d9_r, axis=1)
        orient = list(st9_s) + list(st9_r)
        valid = sum(1 for s in orient if str(s["status"]) == "valid")

        rows.append(
            {
                "source_scale": source_scale,
                "reference_scale": reference_scale,
                "anchor_pairs": int(len(pts0_native)),
                "phase7_mean_l2": _safe_float(np.mean(dist7)),
                "phase7_median_l2": _safe_float(np.median(dist7)),
                "phase7_p90_l2": _safe_float(np.percentile(dist7, 90)),
                "phase9_mean_l2": _safe_float(np.mean(dist9)),
                "phase9_median_l2": _safe_float(np.median(dist9)),
                "phase9_p90_l2": _safe_float(np.percentile(dist9, 90)),
                "phase9_orientation_valid_fraction": float(
                    valid / max(1, len(orient))
                ),
            }
        )

    return rows


def _end_to_end(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
) -> List[Dict[str, Any]]:
    phase7 = run_ssc_matching(
        source_bgr,
        reference_bgr,
        scale_source=1.0,
        scale_reference=1.0,
        config=SSCConfig(),
        ransac_thresh=3.0,
        seeds=(1, 2, 3, 4, 5),
        pair_label="IIRS <-> OHRC | Native | Phase 7 SSC",
    )
    phase9 = run_ssc_rotation_matching(
        source_bgr,
        reference_bgr,
        scale_source=1.0,
        scale_reference=1.0,
        config=SSCRotationConfig(),
        ransac_thresh=3.0,
        seeds=(1, 2, 3, 4, 5),
        pair_label="IIRS <-> OHRC | Native | Phase 9 Rot-Norm SSC",
    )

    rows = []
    for phase_name, result in (("Phase 7 SSC", phase7), ("Phase 9 Rot-Norm SSC", phase9)):
        rows.append(
            {
                "method": phase_name,
                "candidates": int(result.get("candidates", 0)),
                "initial_inliers": int(result.get("initial_inliers", 0)),
                "initial_inlier_ratio": _safe_float(result.get("initial_inlier_ratio")),
                "spatial_occupancy": _safe_float(result.get("spatial_occupancy")),
                "fit_rmse": _safe_float(result.get("fit_rmse")),
                "heldout_rmse": _safe_float(
                    result.get("independent_held_out_rmse")
                ),
                "heldout_valid": bool(
                    result.get("success", False)
                ),
                "failure_stage": result.get("failure_stage"),
                "failure_reason": result.get("failure_reason"),
                "runtime_sec": _safe_float(result.get("total_runtime")),
            }
        )
    return rows


def _write_json(path: Path, payload: Any) -> None:
    def convert(v: Any) -> Any:
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, dict):
            return {str(k): convert(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [convert(x) for x in v]
        return v

    path.write_text(json.dumps(convert(payload), indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    import csv

    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_report(
    path: Path,
    anchor: Dict[str, Any],
    descriptor: Dict[str, Any],
    scale_rows: List[Dict[str, Any]],
    end_to_end_rows: List[Dict[str, Any]],
) -> None:
    report = []
    report.append("# LunarReg Phase 11 — Native Cross-Sensor Transfer Diagnostic")
    report.append("")
    report.append("## Scope")
    report.append(
        "Phase 11 tests why the Phase 9 rotation-normalized SSC branch improves "
        "controlled rotation matching yet does not produce sufficient native "
        "IIRS ↔ OHRC registration."
    )
    report.append("")
    report.append("## Frozen invariants")
    report.append(
        "- Phase 7 SSC descriptor and detector remain unchanged."
    )
    report.append(
        "- Phase 9 orientation estimator and descriptor remain unchanged."
    )
    report.append(
        "- RANSAC threshold = 3.0 px; confidence = 0.995; 3×3 selection; "
        "max 6 points/cell; seeds 1–5."
    )
    report.append("- No production routing or quality-gate modification.")
    report.append("")
    report.append("## Track A — Anchor feasibility")
    report.append(
        f"- Anchor source: existing LoFTR matcher (diagnostic reference only)."
    )
    report.append(f"- Candidate count: {anchor['candidates']}")
    report.append(f"- Anchor pairs: {anchor['anchor_pairs']}")
    report.append(
        f"- 3×3 source occupancy: {anchor['source_spatial_occupancy_3x3']:.4f}"
    )
    report.append(
        f"- Anchor status: {anchor['anchor_feasibility_status']}"
    )
    report.append("")
    report.append("## Track B — Cross-sensor descriptor consistency")
    report.append(
        "| Metric | Phase 7 SSC | Phase 9 rotation-normalized SSC |"
    )
    report.append("|---|---:|---:|")
    for label, a, b in (
        ("Mean L2", descriptor["phase7_mean_l2"], descriptor["phase9_mean_l2"]),
        ("Median L2", descriptor["phase7_median_l2"], descriptor["phase9_median_l2"]),
        ("P90 L2", descriptor["phase7_p90_l2"], descriptor["phase9_p90_l2"]),
        ("Max L2", descriptor["phase7_max_l2"], descriptor["phase9_max_l2"]),
    ):
        report.append(f"| {label} | {a} | {b} |")
    report.append(
        f"- Phase 9 valid orientation fraction across anchors: "
        f"{descriptor['phase9_orientation_valid_fraction']:.6f}"
    )
    report.append("")
    report.append("## Track C — Fixed-anchor scale sensitivity")
    report.append(
        "The scale matrix was pre-declared and evaluated without selecting or "
        "promoting a preferred scale."
    )
    report.append("")
    report.append("| Source scale | Reference scale | Phase 7 mean L2 | Phase 9 mean L2 |")
    report.append("|---:|---:|---:|---:|")
    for row in scale_rows:
        report.append(
            f"| {row['source_scale']:.2f} | {row['reference_scale']:.2f} | "
            f"{row['phase7_mean_l2']} | {row['phase9_mean_l2']} |"
        )
    report.append("")
    report.append("## Track D — End-to-end native IIRS ↔ OHRC")
    report.append(
        "| Method | Candidates | Initial inliers | Ratio | Fit RMSE | Held-out RMSE | Valid |"
    )
    report.append("|---|---:|---:|---:|---:|---:|---|")
    for row in end_to_end_rows:
        report.append(
            f"| {row['method']} | {row['candidates']} | {row['initial_inliers']} | "
            f"{row['initial_inlier_ratio']} | {row['fit_rmse']} | "
            f"{row['heldout_rmse']} | {row['heldout_valid']} |"
        )
    report.append("")
    report.append("## Interpretation boundary")
    report.append(
        "Phase 11 is diagnostic. It does not declare a winner, tune thresholds, "
        "or promote any research branch. Descriptor-level evidence and end-to-end "
        "registration evidence must be interpreted together."
    )
    report.append("")
    report.append("## Production boundary")
    report.append(
        "No production routing, quality gate, Locked LoFTR baseline, or common "
        "downstream mathematics is modified."
    )
    path.write_text("\n".join(report), encoding="utf-8")


def run_phase11(
    source_path: str,
    reference_path: str,
    output_dir: str,
) -> Dict[str, Any]:
    source_bgr = _load_color(source_path)
    reference_bgr = _load_color(reference_path)
    source_gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
    reference_gray = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2GRAY)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    anchor = _anchor_feasibility(source_bgr, reference_bgr)
    pts0 = anchor.pop("pts0")
    pts1 = anchor.pop("pts1")

    # Always save the matcher-derived anchors, but label them clearly.
    _write_json(
        out / "phase11_loftr_anchor_pairs.json",
        {
            "anchor_source": "existing LoFTR matcher",
            "anchor_is_ground_truth": False,
            "source_points": pts0,
            "reference_points": pts1,
        },
    )
    _write_json(out / "phase11_anchor_feasibility.json", anchor)

    descriptor = _cross_sensor_descriptor_diagnostic(
        source_gray, reference_gray, pts0, pts1
    )
    _write_csv(
        out / "phase11_crosssensor_descriptor_results.csv",
        [descriptor],
    )

    scale_rows = _fixed_anchor_scale_sensitivity(
        source_gray, reference_gray, pts0, pts1
    )
    _write_csv(
        out / "phase11_scale_sensitivity_results.csv",
        scale_rows,
    )

    end_to_end_rows = _end_to_end(source_bgr, reference_bgr)
    _write_csv(
        out / "phase11_end_to_end_results.csv",
        end_to_end_rows,
    )

    _write_report(
        out / "phase11_diagnostic_report.md",
        anchor,
        descriptor,
        scale_rows,
        end_to_end_rows,
    )

    return {
        "anchor": anchor,
        "descriptor": descriptor,
        "scale_rows": scale_rows,
        "end_to_end_rows": end_to_end_rows,
        "output_dir": str(out),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LunarReg Phase 11 native cross-sensor transfer diagnostic"
    )
    parser.add_argument("--iirs-source", default=DEFAULT_SOURCES)
    parser.add_argument("--ohrc-reference", default=DEFAULT_REFERENCE)
    parser.add_argument(
        "--output-dir",
        default="research/multimodal/phase11_results",
    )
    args = parser.parse_args()

    try:
        result = run_phase11(
            source_path=args.iirs_source,
            reference_path=args.ohrc_reference,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(f"Phase 11 failed: {exc}")
        return 1

    print(
        "Phase 11 complete. "
        f"Anchor pairs={result['anchor']['anchor_pairs']}; "
        f"output={result['output_dir']}"
    )
    print(
        "Diagnosis is intentionally left for evidence review; "
        "no automatic winner or production decision was applied."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
