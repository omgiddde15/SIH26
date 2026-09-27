"""
research/multimodal/rift2_matching_sweep.py
============================================
Experimental RIFT2 Candidate-Recovery / NNDR Sweep Module
(LunarReg Phase 4 — Research Branch).

Research Question:
Determine whether RIFT2 fails on difficult cross-sensor lunar pairs (specifically
IIRS <-> OHRC) because:
  (1) the descriptor itself cannot distinguish the two modalities, or
  (2) the fixed default NNDR threshold (0.90) rejects potentially useful but ambiguous
      cross-sensor correspondences.

Operational & Invariant Guarantees:
- Research-only: does not modify production matcher selection, routing, or thresholds.
- Preserves RIFT2 descriptor construction: uses identical 216-dimensional descriptors
  (96x96 patch, 6x6 spatial grid, 6 MIM bins).
- Efficient execution: extracts RIFT2 descriptors ONCE per image/scale condition,
  then sweeps NNDR thresholds: [0.90, 0.95, 0.97, 0.99].
- Strict Common Downstream: every threshold passes through the UNCHANGED
  `execute_common_downstream` (RANSAC 3.0, confidence 0.995, 3x3 spatial selection,
  independent held-out validation seeds 1-5).
- Neutral Confidence: confidences = None.
- Initial inlier ratio: strictly computed as initial_inliers / candidates.
"""

import os
import sys
import time
import gc
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.rift2_matcher import (
    build_log_gabor_filter_bank,
    compute_phase_congruency_and_mim,
    detect_rift2_keypoints,
    assign_gradient_orientations,
    compute_rift2_descriptors,
    _MAX_SAFE_PIXELS,
    _MAX_SAFE_DIM,
)
from research.multimodal.scale_search import map_points_to_original
from research.adaptive_matcher.adaptive_engine import execute_common_downstream
from research.multimodal.rift2_benchmark import load_angle_pairs


def extract_rift2_features(
    img_gray: np.ndarray,
    max_kps: int = 1500,
) -> Dict[str, Any]:
    """Extract canonical RIFT2 keypoints and 216-dimensional descriptors once.

    Returns:
    - pts: (N, 2) feature coordinates
    - descriptors: (N, 216) L2-normalized descriptors
    - base_keypoints: FAST keypoints detected on normalized PC
    - oriented_features: count of valid descriptors
    - runtime: seconds taken for extraction
    """
    t0 = time.perf_counter()
    h, w = img_gray.shape

    # Preflight resource check
    if h * w > _MAX_SAFE_PIXELS or max(h, w) > _MAX_SAFE_DIM:
        raise RuntimeError(
            f"Image dimensions ({w}x{h}) exceed safe RIFT2 limit ({_MAX_SAFE_DIM}px / {_MAX_SAFE_PIXELS}px)."
        )

    # 1. Log-Gabor filter bank & PC/MIM
    flts = build_log_gabor_filter_bank(h, w, n_scales=4, n_orientations=6)
    pc, mim, _ = compute_phase_congruency_and_mim(img_gray, flts)

    # 2. FAST keypoint detection on PC
    kps, _ = detect_rift2_keypoints(pc, max_kps=max_kps)

    # 3. Dominant orientation assignment
    oriented = assign_gradient_orientations(img_gray, kps)

    # 4. RIFT2 dominant MIM-index recoded 216-dim descriptors
    pts, desc = compute_rift2_descriptors((h, w), oriented, mim, patch_size=96, grid_size=6, n_orientations=6)

    # Clean up intermediate FFT arrays
    del flts, pc, mim
    gc.collect()

    t_feat = time.perf_counter() - t0

    return {
        "pts": pts,
        "descriptors": desc,
        "base_keypoints": len(kps),
        "oriented_features": len(desc),
        "runtime": round(t_feat, 3),
    }


def match_descriptors_at_thresholds(
    pts0: np.ndarray,
    desc0: np.ndarray,
    pts1: np.ndarray,
    desc1: np.ndarray,
    thresholds: Tuple[float, ...] = (0.90, 0.95, 0.97, 0.99),
) -> Dict[float, Dict[str, Any]]:
    """Perform Nearest-Neighbor Distance Ratio (NNDR) sweep with mutual cross-check

    and spatial duplicate removal.

    KNN match (k=2 forward, k=1 backward) is computed ONCE, then filtered across
    each requested NNDR threshold.

    Returns:
    - Dict mapping threshold -> matching result dictionary.
    """
    t0 = time.perf_counter()
    sweep_results: Dict[float, Dict[str, Any]] = {}

    if len(desc0) == 0 or len(desc1) == 0:
        empty_res = {
            "n_raw_descriptor_matches": 0,
            "n_after_nndr": 0,
            "n_after_mutual_check": 0,
            "n_after_duplicate_removal": 0,
            "candidates": 0,
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "confidences": None,
            "success": False,
            "matching_runtime": 0.0,
        }
        for tau in thresholds:
            sweep_results[tau] = empty_res.copy()
        return sweep_results

    bf = cv2.BFMatcher(cv2.NORM_L2)

    # 1. Forward KNN (k=2) computed ONCE
    matches_01 = bf.knnMatch(desc0, desc1, k=2)
    # 2. Backward KNN (k=1) computed ONCE for mutual cross-check
    matches_10 = bf.knnMatch(desc1, desc0, k=1)
    best_10: Dict[int, int] = {m[0].queryIdx: m[0].trainIdx for m in matches_10 if len(m) > 0}

    n_raw = len(desc0)

    for tau in thresholds:
        t_tau_start = time.perf_counter()

        # Step 2: NNDR filtering
        nndr_pairs: List[Tuple[int, int]] = []
        for m in matches_01:
            if len(m) == 2:
                if m[0].distance < tau * m[1].distance:
                    nndr_pairs.append((m[0].queryIdx, m[0].trainIdx))
            elif len(m) == 1:
                nndr_pairs.append((m[0].queryIdx, m[0].trainIdx))

        n_nndr = len(nndr_pairs)

        # Step 3: Mutual cross-check filtering
        mutual_pairs: List[Tuple[int, int]] = []
        for q_idx, t_idx in nndr_pairs:
            if best_10.get(t_idx) == q_idx:
                mutual_pairs.append((q_idx, t_idx))

        n_mutual = len(mutual_pairs)

        # Step 4: Spatial duplicate removal
        seen_coords = set()
        uniq_pairs: List[Tuple[int, int]] = []
        for q_idx, t_idx in mutual_pairs:
            p0 = pts0[q_idx]
            p1 = pts1[t_idx]
            # Key with coordinate precision to remove identical orientation clones
            coord_key = (
                round(float(p0[0]), 2),
                round(float(p0[1]), 2),
                round(float(p1[0]), 2),
                round(float(p1[1]), 2),
            )
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                uniq_pairs.append((q_idx, t_idx))

        n_unique = len(uniq_pairs)

        if n_unique > 0:
            idx0 = [p[0] for p in uniq_pairs]
            idx1 = [p[1] for p in uniq_pairs]
            pts0_cand = pts0[idx0]
            pts1_cand = pts1[idx1]
        else:
            pts0_cand = np.empty((0, 2), dtype=np.float32)
            pts1_cand = np.empty((0, 2), dtype=np.float32)

        sweep_results[tau] = {
            "n_raw_descriptor_matches": n_raw,
            "n_after_nndr": n_nndr,
            "n_after_mutual_check": n_mutual,
            "n_after_duplicate_removal": n_unique,
            "candidates": n_unique,
            "pts0": pts0_cand,
            "pts1": pts1_cand,
            "confidences": None,  # Neutral confidence
            "success": n_unique >= 4,
            "matching_runtime": round(time.perf_counter() - t_tau_start, 4),
        }

    return sweep_results


def run_rift2_matching_sweep(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    scale_source: float = 1.0,
    scale_reference: float = 1.0,
    thresholds: Tuple[float, ...] = (0.90, 0.95, 0.97, 0.99),
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    pair_label: str = "custom_pair",
) -> Dict[str, Any]:
    """Execute RIFT2 Candidate-Recovery / NNDR Sweep on a single pair/scale condition.

    Workflow:
    1. Scale images if requested (e.g. source 1.0, ref 0.5).
    2. Extract RIFT2 descriptors ONCE.
    3. Run matching sweep across thresholds [0.90, 0.95, 0.97, 0.99].
    4. Map candidate coordinates back to original native dimensions.
    5. Evaluate each threshold through UNCHANGED `execute_common_downstream`.
    6. Return individual threshold trials and summary comparison table.
    """
    t_start = time.perf_counter()

    # Input grayscale conversion
    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if source_img.ndim == 3 else source_img.copy()
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if reference_img.ndim == 3 else reference_img.copy()

    orig_s_h, orig_s_w = s_gray.shape
    orig_r_h, orig_r_w = r_gray.shape

    # Apply candidate scaling if specified
    if scale_source < 1.0:
        scaled_s_w = max(64, int(round(orig_s_w * scale_source)))
        scaled_s_h = max(64, int(round(orig_s_h * scale_source)))
        s_work = cv2.resize(s_gray, (scaled_s_w, scaled_s_h), interpolation=cv2.INTER_AREA)
    else:
        s_work = s_gray
        scaled_s_w, scaled_s_h = orig_s_w, orig_s_h

    if scale_reference < 1.0:
        scaled_r_w = max(64, int(round(orig_r_w * scale_reference)))
        scaled_r_h = max(64, int(round(orig_r_h * scale_reference)))
        r_work = cv2.resize(r_gray, (scaled_r_w, scaled_r_h), interpolation=cv2.INTER_AREA)
    else:
        r_work = r_gray
        scaled_r_w, scaled_r_h = orig_r_w, orig_r_h

    # Step 1: Feature Extraction ONCE
    t0_feat = time.perf_counter()
    feat_s = extract_rift2_features(s_work)
    feat_r = extract_rift2_features(r_work)
    feature_extraction_runtime = round(time.perf_counter() - t0_feat, 3)

    pts0 = feat_s["pts"]
    desc0 = feat_s["descriptors"]
    pts1 = feat_r["pts"]
    desc1 = feat_r["descriptors"]

    # Step 2: Matching Sweep across thresholds
    t0_match = time.perf_counter()
    sweep_data = match_descriptors_at_thresholds(pts0, desc0, pts1, desc1, thresholds=thresholds)
    matching_sweep_runtime = round(time.perf_counter() - t0_match, 3)

    results_list: List[Dict[str, Any]] = []

    # Step 3: Downstream Registration per threshold
    for tau in thresholds:
        m_info = sweep_data[tau]
        n_cands = m_info["candidates"]

        record: Dict[str, Any] = {
            "pair": pair_label,
            "scale": f"{scale_source:.1f} / {scale_reference:.1f}",
            "source_scale": scale_source,
            "reference_scale": scale_reference,
            "nndr_threshold": tau,
            "base_keypoints_source": feat_s["base_keypoints"],
            "base_keypoints_reference": feat_r["base_keypoints"],
            "oriented_features_source": feat_s["oriented_features"],
            "oriented_features_reference": feat_r["oriented_features"],
            "n_raw_descriptor_matches": m_info["n_raw_descriptor_matches"],
            "n_after_nndr": m_info["n_after_nndr"],
            "n_after_mutual_check": m_info["n_after_mutual_check"],
            "n_after_duplicate_removal": m_info["n_after_duplicate_removal"],
            "candidates": n_cands,
            "initial_inliers": 0,
            "initial_inlier_ratio": 0.0,
            "spatial_occupancy": 0.0,
            "spatial_cv": 0.0,
            "fit_rmse": np.nan,
            "independent_held_out_rmse": np.nan,
            "feature_extraction_runtime": feature_extraction_runtime,
            "matching_runtime": m_info["matching_runtime"],
            "total_runtime": round(feature_extraction_runtime + m_info["matching_runtime"], 3),
            "success": False,
            "failure_stage": None,
            "failure_reason": None,
        }

        if n_cands < 4:
            record["failure_stage"] = "descriptor_matching"
            record["failure_reason"] = f"Insufficient candidates ({n_cands} < 4)"
            results_list.append(record)
            continue

        # Coordinate Inverse-Mapping to native dimensions
        pts0_native = map_points_to_original(m_info["pts0"], (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
        pts1_native = map_points_to_original(m_info["pts1"], (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))

        try:
            downstream = execute_common_downstream(
                pts0=pts0_native,
                pts1=pts1_native,
                confidences=None,  # Neutral confidence
                source_img=source_img,
                reference_img=reference_img,
                max_per_cell=6,
                ransac_thresh=ransac_thresh,
                seeds=seeds,
            )

            init_inl = int(downstream.get("n_initial_inliers", downstream.get("n_final_inliers", 0)))
            chk_rmse = downstream.get("mean_check_rmse")
            fit_rmse = downstream.get("fit_rmse")
            held_valid = downstream.get("held_out_valid", False)

            record["initial_inliers"] = init_inl
            record["initial_inlier_ratio"] = round(float(init_inl / max(1, n_cands)), 4) if n_cands > 0 else 0.0
            record["spatial_occupancy"] = round(float(downstream.get("spatial_occupancy", 0.0)), 4)
            record["spatial_cv"] = round(float(downstream.get("spatial_cv", 0.0)), 4)
            record["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
            record["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan

            if held_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                record["success"] = True
                record["failure_stage"] = None
                record["failure_reason"] = None
            else:
                record["success"] = False
                record["failure_stage"] = "held_out_validation"
                record["failure_reason"] = f"Insufficient inliers for independent held-out check ({init_inl} < 8)"

        except Exception as e:
            record["success"] = False
            record["failure_stage"] = "common_downstream"
            record["failure_reason"] = str(e)

        results_list.append(record)

    # Format table strictly conforming to Requirement 10
    df_rows = []
    for r in results_list:
        df_rows.append({
            "Pair": r["pair"],
            "Scale": r["scale"],
            "NNDR": r["nndr_threshold"],
            "Raw Matches": r["n_raw_descriptor_matches"],
            "After NNDR": r["n_after_nndr"],
            "Mutual": r["n_after_mutual_check"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Ratio": r["initial_inlier_ratio"],
            "3×3 Occ.": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["total_runtime"],
            "Success": r["success"],
            "Failure": f"{r['failure_stage']}: {r['failure_reason']}" if not r["success"] else "None",
        })

    return {
        "results": results_list,
        "comparison_table": pd.DataFrame(df_rows),
        "feature_extraction_runtime": feature_extraction_runtime,
        "matching_sweep_runtime": matching_sweep_runtime,
        "total_runtime": round(time.perf_counter() - t_start, 3),
    }


def run_phase4_benchmark(
    iirs_src_path: str = r"C:\Users\Dell\Downloads\souse.jpeg",
    iirs_ref_path: str = r"C:\Users\Dell\Downloads\ref.jpeg",
    angle_pairs_base_dir: Optional[str] = None,
    thresholds: Tuple[float, ...] = (0.90, 0.95, 0.97, 0.99),
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
) -> Dict[str, Any]:
    """Execute complete Phase 4 NNDR sweep benchmark across:

    1. IIRS <-> OHRC Native (1.0 / 1.0)
    2. IIRS <-> OHRC Phase 2 Scale (1.0 / 0.5)
    3. Rotation-change pair (angle_pairs/pair_01)
    4. Viewpoint-change pair (angle_pairs/pair_02)
    5. Sun-angle-change pair (angle_pairs/pair_03)

    Outputs comprehensive comparison table and scientific interpretation.
    """
    all_trials: List[Dict[str, Any]] = []

    # --- Dataset A: IIRS <-> OHRC ---
    if os.path.exists(iirs_src_path) and os.path.exists(iirs_ref_path):
        s_iirs = cv2.imread(iirs_src_path)
        r_iirs = cv2.imread(iirs_ref_path)

        # A1. Native 1.0 / 1.0
        print("[Phase 4] Running IIRS <-> OHRC Native (1.0 / 1.0)...")
        res_native = run_rift2_matching_sweep(
            s_iirs,
            r_iirs,
            scale_source=1.0,
            scale_reference=1.0,
            thresholds=thresholds,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label="IIRS <-> OHRC (Native)",
        )
        all_trials.extend(res_native["results"])

        # A2. Phase 2 Scale 1.0 / 0.5
        print("[Phase 4] Running IIRS <-> OHRC Scale (1.0 / 0.5)...")
        res_scaled = run_rift2_matching_sweep(
            s_iirs,
            r_iirs,
            scale_source=1.0,
            scale_reference=0.5,
            thresholds=thresholds,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label="IIRS <-> OHRC (Scale 1.0/0.5)",
        )
        all_trials.extend(res_scaled["results"])

    # --- Datasets B, C, D: Angle Pairs ---
    angle_data = load_angle_pairs(angle_pairs_base_dir)
    pair_mapping = {
        "pair_01": "Rotation Pair (pair_01)",
        "pair_02": "Viewpoint Pair (pair_02)",
        "pair_03": "Sun Angle Pair (pair_03)",
    }

    for vp in angle_data.get("valid_pairs", []):
        pid = vp["pair_id"]
        label = pair_mapping.get(pid, pid)
        print(f"[Phase 4] Running {label} Native (1.0 / 1.0)...")
        res_ang = run_rift2_matching_sweep(
            vp["source_img"],
            vp["reference_img"],
            scale_source=1.0,
            scale_reference=1.0,
            thresholds=thresholds,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label=label,
        )
        all_trials.extend(res_ang["results"])

    # Build master DataFrame
    df_rows = []
    for r in all_trials:
        df_rows.append({
            "Pair": r["pair"],
            "Scale": r["scale"],
            "NNDR": r["nndr_threshold"],
            "Raw Matches": r["n_raw_descriptor_matches"],
            "After NNDR": r["n_after_nndr"],
            "Mutual": r["n_after_mutual_check"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Ratio": r["initial_inlier_ratio"],
            "3×3 Occ.": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["total_runtime"],
            "Success": r["success"],
            "Failure": f"{r['failure_stage']}: {r['failure_reason']}" if not r["success"] else "None",
        })

    master_df = pd.DataFrame(df_rows)

    return {
        "trials": all_trials,
        "comparison_table": master_df,
    }
