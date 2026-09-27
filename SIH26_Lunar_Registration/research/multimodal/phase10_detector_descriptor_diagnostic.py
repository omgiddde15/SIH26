"""
LunarReg Phase 10 — Detector vs Descriptor Diagnostic
Research-only diagnostic for the frozen Phase 7 SSC and Phase 9 rotation-normalized SSC branches.

Tracks:
A) Frozen Sobel+FAST detector synthetic-transform repeatability
B) Descriptor-only rotation consistency at known paired coordinates
C) Controlled-keypoint descriptor matching with known transformed coordinates
D) End-to-end Phase 7 vs Phase 9 comparison on synthetic rotations / native pair / real controls
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from research.multimodal.ssc_matcher import (
    SSCConfig,
    compute_ssc_descriptors,
    detect_ssc_keypoints,
    match_ssc_descriptors,
    run_ssc_matching,
)
from research.multimodal.ssc_rotation import (
    SSCRotationConfig,
    compute_rotation_normalized_ssc_descriptors,
    run_ssc_rotation_matching,
    summarize_orientation_stats,
)

try:
    from scipy.spatial import cKDTree
except Exception:
    cKDTree = None

DIAGNOSTIC_TOLERANCE_PX = 2.0
ROTATIONS_DEG = (10.0, 20.0, 30.0, -20.0)


def _as_gray(img: np.ndarray) -> np.ndarray:
    if img is None:
        raise ValueError("Image is None.")
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.copy()


def rotate_image_and_points(
    img_gray: np.ndarray,
    pts: np.ndarray,
    angle_deg: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    h, w = img_gray.shape
    matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle_deg, 1.0)
    rotated = cv2.warpAffine(
        img_gray,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    ones = np.ones((len(pts), 1), dtype=np.float32)
    expected = (matrix @ np.hstack([pts, ones]).T).T.astype(np.float32)
    return rotated, expected, matrix


def valid_expected_mask(
    pts_expected: np.ndarray,
    shape: Tuple[int, int],
    margin: int = 8,
) -> np.ndarray:
    h, w = shape
    return (
        (pts_expected[:, 0] >= margin)
        & (pts_expected[:, 0] <= w - 1 - margin)
        & (pts_expected[:, 1] >= margin)
        & (pts_expected[:, 1] <= h - 1 - margin)
    )


def nearest_distances(query_pts: np.ndarray, reference_pts: np.ndarray) -> np.ndarray:
    if len(query_pts) == 0 or len(reference_pts) == 0:
        return np.full((len(query_pts),), np.inf, dtype=np.float32)
    if cKDTree is not None:
        return cKDTree(reference_pts).query(query_pts, k=1)[0].astype(np.float32)
    # Deterministic fallback; 1500x1500 is manageable for the diagnostic.
    diffs = query_pts[:, None, :] - reference_pts[None, :, :]
    d2 = np.sum(diffs * diffs, axis=2)
    return np.sqrt(np.min(d2, axis=1)).astype(np.float32)


def track_a_detector_repeatability(
    img_gray: np.ndarray,
    rotations: Sequence[float] = ROTATIONS_DEG,
    max_kps: int = 1500,
    margin: int = 8,
) -> List[Dict[str, Any]]:
    pts_orig, raw_orig = detect_ssc_keypoints(
        img_gray, max_kps=max_kps, fast_threshold=10, margin=margin
    )
    rows: List[Dict[str, Any]] = []
    for angle in rotations:
        rotated, expected, _ = rotate_image_and_points(img_gray, pts_orig, angle)
        mask = valid_expected_mask(expected, rotated.shape, margin=margin)
        expected_valid = expected[mask]
        detected, raw_rot = detect_ssc_keypoints(
            rotated, max_kps=max_kps, fast_threshold=10, margin=margin
        )
        dists = nearest_distances(expected_valid, detected)
        finite = np.isfinite(dists)
        if np.any(finite):
            vals = dists[finite]
            cov = float(np.mean(vals <= DIAGNOSTIC_TOLERANCE_PX))
            median = float(np.median(vals))
            p90 = float(np.percentile(vals, 90))
            mean = float(np.mean(vals))
            maxd = float(np.max(vals))
        else:
            cov = median = p90 = mean = maxd = float("nan")
        rows.append({
            "track": "A_detector_repeatability",
            "angle_deg": angle,
            "original_keypoints": int(len(pts_orig)),
            "original_raw_keypoints": int(raw_orig),
            "valid_expected_keypoints": int(len(expected_valid)),
            "rotated_detected_keypoints": int(len(detected)),
            "rotated_raw_keypoints": int(raw_rot),
            "coverage_at_2px": cov,
            "mean_nearest_distance_px": mean,
            "median_nearest_distance_px": median,
            "p90_nearest_distance_px": p90,
            "max_nearest_distance_px": maxd,
            "diagnostic_tolerance_px": DIAGNOSTIC_TOLERANCE_PX,
        })
    return rows


def track_b_descriptor_consistency(
    img_gray: np.ndarray,
    rotations: Sequence[float] = ROTATIONS_DEG,
    margin: int = 8,
    ssc_config: Optional[SSCConfig] = None,
    rot_config: Optional[SSCRotationConfig] = None,
) -> List[Dict[str, Any]]:
    ssc_config = ssc_config or SSCConfig()
    rot_config = rot_config or SSCRotationConfig(ssc=ssc_config)
    pts_orig, _ = detect_ssc_keypoints(
        img_gray,
        max_kps=ssc_config.max_keypoints,
        fast_threshold=ssc_config.fast_threshold,
        margin=ssc_config.margin,
    )
    d7_orig_all = compute_ssc_descriptors(img_gray, pts_orig, ssc_config)
    d9_orig_all, _ = compute_rotation_normalized_ssc_descriptors(
        img_gray, pts_orig, rot_config, return_stats=True
    )

    rows: List[Dict[str, Any]] = []
    for angle in rotations:
        rotated, expected, _ = rotate_image_and_points(img_gray, pts_orig, angle)
        mask = valid_expected_mask(expected, rotated.shape, margin=margin)
        d7_o = d7_orig_all[mask]
        d9_o = d9_orig_all[mask]
        expected_valid = expected[mask]

        d7_r = compute_ssc_descriptors(rotated, expected_valid, ssc_config)
        d9_r, stats_r = compute_rotation_normalized_ssc_descriptors(
            rotated, expected_valid, rot_config, return_stats=True
        )

        dist7 = np.linalg.norm(d7_o - d7_r, axis=1) if len(d7_o) else np.empty(0)
        dist9 = np.linalg.norm(d9_o - d9_r, axis=1) if len(d9_o) else np.empty(0)

        stat_summary = summarize_orientation_stats(stats_r)

        def summary(arr: np.ndarray) -> Tuple[float, float, float, float]:
            if len(arr) == 0:
                return (float("nan"),) * 4
            return (
                float(np.mean(arr)),
                float(np.median(arr)),
                float(np.percentile(arr, 90)),
                float(np.max(arr)),
            )

        b7 = summary(dist7)
        b9 = summary(dist9)

        rows.append({
            "track": "B_descriptor_rotation_consistency",
            "angle_deg": angle,
            "valid_pairs": int(len(expected_valid)),
            "phase7_mean_l2": b7[0],
            "phase7_median_l2": b7[1],
            "phase7_p90_l2": b7[2],
            "phase7_max_l2": b7[3],
            "phase9_mean_l2": b9[0],
            "phase9_median_l2": b9[1],
            "phase9_p90_l2": b9[2],
            "phase9_max_l2": b9[3],
            "phase9_valid_orientation_count": int(stat_summary["valid_count"]),
            "phase9_low_confidence_orientation_count": int(stat_summary["low_confidence_count"]),
            "phase9_flat_orientation_count": int(stat_summary["flat_count"]),
            "phase9_valid_orientation_fraction": float(stat_summary["valid_fraction"]),
        })
    return rows


def controlled_match_recovery(
    p0: np.ndarray,
    p1_true: np.ndarray,
    d0: np.ndarray,
    d1: np.ndarray,
    nndr_threshold: float = 0.90,
) -> Dict[str, Any]:
    match = match_ssc_descriptors(
        p0, d0, p1_true, d1, nndr_threshold=nndr_threshold
    )
    p0m = match["pts0"]
    p1m = match["pts1"]
    if len(p0m) == 0:
        return {
            "candidates": 0,
            "correct": 0,
            "correct_rate": 0.0,
            "match_result": match,
        }
    # Here p0 and p1_true are already paired by the synthetic transform.
    # Evaluate each matched pair against the known geometric correspondence
    # by nearest-point lookup in p0 index space.
    # p0 points are unique in the detector output, so exact coordinate lookup is safe.
    idx_by_point = {
        (round(float(x), 4), round(float(y), 4)): i
        for i, (x, y) in enumerate(p0)
    }
    correct = 0
    for a, b in zip(p0m, p1m):
        i = idx_by_point.get((round(float(a[0]), 4), round(float(a[1]), 4)))
        if i is None:
            continue
        truth = p1_true[i]
        if float(np.linalg.norm(truth - b)) <= DIAGNOSTIC_TOLERANCE_PX:
            correct += 1
    n = int(match["n_candidates"])
    return {
        "candidates": n,
        "correct": int(correct),
        "correct_rate": float(correct / max(1, n)),
        "match_result": match,
    }


def track_c_controlled_keypoints(
    img_gray: np.ndarray,
    rotations: Sequence[float] = ROTATIONS_DEG,
    margin: int = 8,
    ssc_config: Optional[SSCConfig] = None,
    rot_config: Optional[SSCRotationConfig] = None,
) -> List[Dict[str, Any]]:
    ssc_config = ssc_config or SSCConfig()
    rot_config = rot_config or SSCRotationConfig(ssc=ssc_config)
    pts_orig, _ = detect_ssc_keypoints(
        img_gray,
        max_kps=ssc_config.max_keypoints,
        fast_threshold=ssc_config.fast_threshold,
        margin=ssc_config.margin,
    )
    rows: List[Dict[str, Any]] = []

    for angle in rotations:
        rotated, expected, _ = rotate_image_and_points(img_gray, pts_orig, angle)
        mask = valid_expected_mask(expected, rotated.shape, margin=margin)
        p0 = pts_orig[mask]
        p1 = expected[mask]

        d7_o = compute_ssc_descriptors(img_gray, p0, ssc_config)
        d7_r = compute_ssc_descriptors(rotated, p1, ssc_config)
        d9_o, _ = compute_rotation_normalized_ssc_descriptors(img_gray, p0, rot_config)
        d9_r, _ = compute_rotation_normalized_ssc_descriptors(rotated, p1, rot_config)

        r7 = controlled_match_recovery(
            p0, p1, d7_o, d7_r, nndr_threshold=ssc_config.nndr_threshold
        )
        r9 = controlled_match_recovery(
            p0, p1, d9_o, d9_r, nndr_threshold=ssc_config.nndr_threshold
        )

        rows.append({
            "track": "C_controlled_keypoints",
            "angle_deg": angle,
            "valid_points": int(len(p0)),
            "phase7_candidates": r7["candidates"],
            "phase7_correct": r7["correct"],
            "phase7_correct_rate": r7["correct_rate"],
            "phase9_candidates": r9["candidates"],
            "phase9_correct": r9["correct"],
            "phase9_correct_rate": r9["correct_rate"],
        })
    return rows


def _load_angle_pairs(base_dir: Path) -> List[Tuple[str, np.ndarray, np.ndarray]]:
    pairs: List[Tuple[str, np.ndarray, np.ndarray]] = []
    if not base_dir.exists():
        return pairs
    for pair_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
        src = next(iter([pair_dir / f"source{ext}" for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff") if (pair_dir / f"source{ext}").exists()]), None)
        ref = next(iter([pair_dir / f"reference{ext}" for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff") if (pair_dir / f"reference{ext}").exists()]), None)
        if src is None or ref is None:
            continue
        s = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
        r = cv2.imread(str(ref), cv2.IMREAD_GRAYSCALE)
        if s is not None and r is not None:
            pairs.append((pair_dir.name, s, r))
    return pairs


def track_d_end_to_end(
    iirs_source: np.ndarray,
    ohrc_reference: np.ndarray,
    angle_pairs_dir: Optional[Path],
    ssc_config: Optional[SSCConfig] = None,
    rot_config: Optional[SSCRotationConfig] = None,
) -> List[Dict[str, Any]]:
    ssc_config = ssc_config or SSCConfig()
    rot_config = rot_config or SSCRotationConfig(ssc=ssc_config)
    cases: List[Tuple[str, np.ndarray, np.ndarray]] = [
        ("IIRS <-> OHRC | Native", iirs_source, ohrc_reference)
    ]

    h, w = iirs_source.shape
    for angle in ROTATIONS_DEG:
        rot, _, _ = rotate_image_and_points(
            iirs_source, np.empty((0, 2), dtype=np.float32), angle
        )
        cases.append((f"IIRS <-> OHRC | Synthetic Rotation {angle:+g} deg", rot, ohrc_reference))

    if angle_pairs_dir is not None:
        for pair_id, s, r in _load_angle_pairs(angle_pairs_dir):
            if pair_id in {"pair_01", "pair_02", "pair_03"}:
                cases.append((f"{pair_id} | Real Control", s, r))

    rows: List[Dict[str, Any]] = []
    for label, s, r in cases:
        p7 = run_ssc_matching(
            s, r, config=ssc_config, ransac_thresh=3.0, seeds=(1, 2, 3, 4, 5), pair_label=label
        )
        p9 = run_ssc_rotation_matching(
            s, r, config=rot_config, ransac_thresh=3.0, seeds=(1, 2, 3, 4, 5), pair_label=label
        )
        rows.append({
            "track": "D_end_to_end",
            "pair": label,
            "phase7_candidates": int(p7.get("candidates", 0)),
            "phase7_initial_inliers": int(p7.get("initial_inliers", 0)),
            "phase7_initial_ratio": float(p7.get("initial_inlier_ratio", 0.0)),
            "phase7_fit_rmse": p7.get("fit_rmse"),
            "phase7_heldout_rmse": p7.get("independent_held_out_rmse"),
            "phase7_heldout_valid": bool(p7.get("success", False)),
            "phase9_candidates": int(p9.get("candidates", 0)),
            "phase9_initial_inliers": int(p9.get("initial_inliers", 0)),
            "phase9_initial_ratio": float(p9.get("initial_inlier_ratio", 0.0)),
            "phase9_fit_rmse": p9.get("fit_rmse"),
            "phase9_heldout_rmse": p9.get("independent_held_out_rmse"),
            "phase9_heldout_valid": bool(p9.get("success", False)),
        })
    return rows


def diagnosis_guidance() -> str:
    return (
        "Diagnosis is intentionally left for evidence review. "
        "Compare Track A detector repeatability, Track B descriptor-only "
        "rotation consistency, Track C controlled correspondence recovery, "
        "and Track D end-to-end behavior. Do not apply a post-hoc numeric "
        "winner threshold to force a detector-dominant or descriptor-dominant label."
    )


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = []
    seen = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def run_phase10(
    iirs_source: str,
    ohrc_reference: str,
    angle_pairs_dir: Optional[str],
    output_dir: str,
) -> Dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s = cv2.imread(iirs_source, cv2.IMREAD_GRAYSCALE)
    r = cv2.imread(ohrc_reference, cv2.IMREAD_GRAYSCALE)
    if s is None or r is None:
        raise FileNotFoundError("Could not decode IIRS/OHRC source/reference images.")

    ssc_cfg = SSCConfig()
    rot_cfg = SSCRotationConfig(ssc=ssc_cfg)

    sign_sanity = {
        "note": "Use the already-frozen Phase 9 sign sanity result before running this diagnostic."
    }

    detector_rows = track_a_detector_repeatability(s)
    descriptor_rows = track_b_descriptor_consistency(s, ssc_config=ssc_cfg, rot_config=rot_cfg)
    controlled_rows = track_c_controlled_keypoints(s, ssc_config=ssc_cfg, rot_config=rot_cfg)
    e2e_rows = track_d_end_to_end(s, r, Path(angle_pairs_dir) if angle_pairs_dir else None, ssc_cfg, rot_cfg)

    write_csv(output / "phase10_detector_diagnostic_results.csv", detector_rows)
    write_csv(output / "phase10_descriptor_diagnostic_results.csv", descriptor_rows)
    write_csv(output / "phase10_controlled_matching_results.csv", controlled_rows)
    write_csv(output / "phase10_end_to_end_results.csv", e2e_rows)

    diagnosis = diagnosis_guidance()

    report = [
        "# LunarReg Phase 10 — Detector vs Descriptor Diagnostic",
        "",
        "## Scope",
        "",
        "Phase 10 separates keypoint repeatability from descriptor rotation consistency under frozen Phase 7/8 SSC and Phase 9 rotation-normalized SSC settings.",
        "",
        "## Frozen settings",
        "",
        "- Detector: Independent Sobel-gradient + FAST, threshold=10, fallback=5, margin=8, max=1500.",
        "- SSC: frozen 21-D descriptor, 7x7 patches, R=4 px, six fixed neighbours.",
        "- Matching: KNN k=2/k=1, mutual check, NNDR=0.90.",
        "- Phase 9 orientation: Sobel structure tensor, 7x7 Gaussian sigma=1.5, coherence<0.15 or trace<1e-4 -> theta=0, R(+theta).",
        "- Downstream: RANSAC 3.0 px, confidence 0.995, 3x3 spatial selection, max 6/cell, seeds 1-5.",
        "",
        "## Interpretation",
        "",
        "Use detector repeatability and descriptor-only distances as evidence about component contribution. Do not treat these diagnostics as proofs of causality.",
        "",
        f"### Integrated diagnostic",
        diagnosis,
        "",
        "## Production boundary",
        "",
        "Phase 10 is research-only. No production routing, quality gates, Locked LoFTR, or common downstream code is changed by this diagnostic.",
        "",
        "### Outputs",
        "",
        "- phase10_detector_diagnostic_results.csv",
        "- phase10_descriptor_diagnostic_results.csv",
        "- phase10_controlled_matching_results.csv",
        "- phase10_end_to_end_results.csv",
    ]
    (output / "phase10_diagnostic_report.md").write_text("\n".join(report), encoding="utf-8")

    return {
        "detector_rows": detector_rows,
        "descriptor_rows": descriptor_rows,
        "controlled_rows": controlled_rows,
        "e2e_rows": e2e_rows,
        "diagnosis": diagnosis,
        "sign_sanity_note": sign_sanity,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iirs-source", required=True)
    parser.add_argument("--ohrc-reference", required=True)
    parser.add_argument("--angle-pairs-dir", default=None)
    parser.add_argument("--output-dir", default="research/multimodal")
    args = parser.parse_args()

    result = run_phase10(
        args.iirs_source,
        args.ohrc_reference,
        args.angle_pairs_dir,
        args.output_dir,
    )
    print(result["diagnosis"])


if __name__ == "__main__":
    main()
