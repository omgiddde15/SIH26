"""
research/multimodal/rift2_structural_fusion.py
================================================
Experimental RIFT2 Structural-Fusion / Cross-Modal Re-Ranking Module
(LunarReg Phase 5 — Research Branch).

Research Question:
Can a structural-consistency signal improve the quality of RIFT2 candidate
correspondences without changing the RIFT2 descriptor itself?
Distinguishes:
  RIFT2 descriptor candidate generation
  vs.
  structural correspondence re-ranking

Operational & Invariant Guarantees:
- Research-only: does not modify production matcher selection, routing, or thresholds.
- Preserves RIFT2 descriptor construction: uses identical 216-dimensional descriptors
  (96x96 patch, 6x6 spatial grid, 6 MIM bins).
- Independent structural patch descriptor: extracts oriented local structural patches
  (32x32) using Phase 1 structural representation (primary: `gradient_magnitude`),
  zero-mean centered, unit-L2 normalized.
- Symmetric cosine similarity and equal-weight fusion score:
  fusion_score = 0.5 * normalized_rift2_similarity + 0.5 * structural_similarity
  (Weight 0.5/0.5 is fixed; no ad-hoc tuning or learned weights).
- Evaluates fixed Top-K configurations: K in [8, 12, 16, 24] and RIFT2-only (All).
- Strict Common Downstream: every candidate set passes through UNCHANGED
  `execute_common_downstream` (RANSAC 3.0, confidence 0.995, 3x3 spatial selection,
  independent held-out validation seeds 1-5).
- Neutral Confidence: confidences = None.
- Initial inlier ratio: strictly computed as initial_inliers / candidates.
"""

import os
import sys
import time
import gc
from typing import Any, Dict, List, Optional, Tuple, Union

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
from research.multimodal.multimodal_preprocess import (
    to_gradient_magnitude,
    to_local_gradient_normalized,
)
from research.multimodal.scale_search import map_points_to_original
from research.adaptive_matcher.adaptive_engine import execute_common_downstream
from research.multimodal.rift2_benchmark import load_angle_pairs


def extract_rift2_and_structural_features(
    img_gray: np.ndarray,
    representation: str = "gradient_magnitude",
    patch_size: int = 32,
    max_kps: int = 1500,
) -> Dict[str, Any]:
    """Extract canonical RIFT2 features and independent oriented structural descriptors.

    Parameters:
    - img_gray: Grayscale image (H, W), uint8.
    - representation: "gradient_magnitude" (default) or "local_gradient_normalized".
    - patch_size: Size of local structural patch (default: 32x32).
    - max_kps: Maximum FAST keypoints on Phase Congruency (default: 1500).

    Returns:
    - pts: (N, 2) feature coordinates
    - rift2_descriptors: (N, 216) L2-normalized RIFT2 descriptors
    - structural_descriptors: (N, patch_size*patch_size) zero-mean unit-L2 normalized descriptors
    - thetas: (N,) dominant orientation angles in radians
    - base_keypoints: count of FAST keypoints on PC
    - oriented_features: count of valid descriptors
    - rift2_feature_runtime: runtime for RIFT2 feature extraction
    - structural_desc_runtime: runtime for structural descriptor extraction
    - total_feature_runtime: sum of extraction runtimes
    """
    t0_all = time.perf_counter()
    h, w = img_gray.shape

    # Preflight resource check
    if h * w > _MAX_SAFE_PIXELS or max(h, w) > _MAX_SAFE_DIM:
        raise RuntimeError(
            f"Image dimensions ({w}x{h}) exceed safe RIFT2 limit ({_MAX_SAFE_DIM}px / {_MAX_SAFE_PIXELS}px)."
        )

    # 1. Structural representation image
    t0_struct_prep = time.perf_counter()
    if representation == "gradient_magnitude":
        struct_img = to_gradient_magnitude(img_gray)
    elif representation == "local_gradient_normalized":
        struct_img = to_local_gradient_normalized(img_gray)
    else:
        raise ValueError(f"Unknown structural representation: '{representation}'")
    t_struct_prep = time.perf_counter() - t0_struct_prep

    # 2. Canonical RIFT2 feature extraction
    t0_rift2 = time.perf_counter()
    flts = build_log_gabor_filter_bank(h, w, n_scales=4, n_orientations=6)
    pc, mim, _ = compute_phase_congruency_and_mim(img_gray, flts)
    kps, _ = detect_rift2_keypoints(pc, max_kps=max_kps)
    oriented = assign_gradient_orientations(img_gray, kps)
    pts, desc = compute_rift2_descriptors((h, w), oriented, mim, patch_size=96, grid_size=6, n_orientations=6)
    t_rift2 = time.perf_counter() - t0_rift2

    # Clean up intermediate FFT arrays
    del flts, pc, mim
    gc.collect()

    # Determine exact 1-to-1 orientations matching the valid descriptors
    # (compute_rift2_descriptors keeps points with ix - 48 >= 0, ix + 48 < w, iy - 48 >= 0, iy + 48 < h)
    radius_rift2 = 48
    thetas = [
        theta
        for x, y, theta in oriented
        if int(round(x)) - radius_rift2 >= 0
        and int(round(x)) + radius_rift2 < w
        and int(round(y)) - radius_rift2 >= 0
        and int(round(y)) + radius_rift2 < h
    ]
    thetas_arr = np.array(thetas, dtype=np.float32)

    if len(thetas_arr) != len(pts):
        raise RuntimeError(
            f"Orientation count mismatch: {len(thetas_arr)} orientations vs {len(pts)} valid points."
        )

    # 3. Extract oriented structural patch descriptors
    t0_struct_desc = time.perf_counter()
    P = patch_size
    n_feats = len(pts)
    struct_descs = np.zeros((n_feats, P * P), dtype=np.float32)

    for i in range(n_feats):
        x, y = float(pts[i, 0]), float(pts[i, 1])
        theta = float(thetas_arr[i])

        c, s = np.cos(theta), np.sin(theta)
        # Affine matrix mapping image coordinates (X, Y) to patch coordinates (p_x, p_y)
        A = np.array([
            [c, s, (P / 2.0) - (x * c + y * s)],
            [-s, c, (P / 2.0) - (-x * s + y * c)],
        ], dtype=np.float32)

        patch = cv2.warpAffine(struct_img, A, (P, P), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        patch_f = patch.astype(np.float32)

        # Deterministic zero-mean centering and unit L2 normalization
        patch_zm = patch_f - np.mean(patch_f)
        norm = float(np.linalg.norm(patch_zm))
        if norm > 1e-6:
            struct_descs[i] = (patch_zm / norm).ravel()
        else:
            struct_descs[i] = np.zeros(P * P, dtype=np.float32)

    t_struct_desc = (time.perf_counter() - t0_struct_desc) + t_struct_prep

    return {
        "pts": pts,
        "rift2_descriptors": desc,
        "structural_descriptors": struct_descs,
        "thetas": thetas_arr,
        "base_keypoints": len(kps),
        "oriented_features": len(desc),
        "rift2_feature_runtime": round(t_rift2, 3),
        "structural_desc_runtime": round(t_struct_desc, 3),
        "total_feature_runtime": round(t_rift2 + t_struct_desc, 3),
    }


def match_rift2_with_pair_indices(
    pts0: np.ndarray,
    desc0: np.ndarray,
    pts1: np.ndarray,
    desc1: np.ndarray,
    thresholds: Tuple[float, ...] = (0.95, 0.97, 0.99),
) -> Dict[float, Dict[str, Any]]:
    """Perform RIFT2 matching across NNDR thresholds, preserving candidate feature indices.

    Follows exact Phase 4 policy:
    1. Forward KNN (k=2) computed ONCE.
    2. Backward KNN (k=1) computed ONCE for mutual cross-check.
    3. Filtered by NNDR ratio threshold.
    4. Filtered by mutual cross-check consistency.
    5. Deduplicated by spatial coordinates.
    6. Returns candidate pairs with their corresponding feature array indices (idx0, idx1).
    """
    sweep_results: Dict[float, Dict[str, Any]] = {}

    if len(desc0) == 0 or len(desc1) == 0:
        empty_res = {
            "n_raw_descriptor_matches": 0,
            "n_after_nndr": 0,
            "n_after_mutual_check": 0,
            "n_after_duplicate_removal": 0,
            "candidates": 0,
            "idx0": np.empty(0, dtype=int),
            "idx1": np.empty(0, dtype=int),
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "matching_runtime": 0.0,
        }
        for tau in thresholds:
            sweep_results[tau] = empty_res.copy()
        return sweep_results

    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches_01 = bf.knnMatch(desc0, desc1, k=2)
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
            idx0 = np.array([p[0] for p in uniq_pairs], dtype=int)
            idx1 = np.array([p[1] for p in uniq_pairs], dtype=int)
            pts0_cand = pts0[idx0]
            pts1_cand = pts1[idx1]
        else:
            idx0 = np.empty(0, dtype=int)
            idx1 = np.empty(0, dtype=int)
            pts0_cand = np.empty((0, 2), dtype=np.float32)
            pts1_cand = np.empty((0, 2), dtype=np.float32)

        sweep_results[tau] = {
            "n_raw_descriptor_matches": n_raw,
            "n_after_nndr": n_nndr,
            "n_after_mutual_check": n_mutual,
            "n_after_duplicate_removal": n_unique,
            "candidates": n_unique,
            "idx0": idx0,
            "idx1": idx1,
            "pts0": pts0_cand,
            "pts1": pts1_cand,
            "matching_runtime": round(time.perf_counter() - t_tau_start, 4),
        }

    return sweep_results


def compute_structural_similarity_and_fusion(
    desc0: np.ndarray,
    desc1: np.ndarray,
    struct_desc0: np.ndarray,
    struct_desc1: np.ndarray,
    idx0: np.ndarray,
    idx1: np.ndarray,
) -> Dict[str, Any]:
    """Compute normalized RIFT2 similarity, structural cosine similarity, and equal-weight fusion score.

    Equations:
    - RIFT2 dot product S_rift2 = desc0[i] · desc1[j] in [0, 1].
      rift2_similarity = np.clip(float(np.sum(rift2_desc0 * rift2_desc1)), 0.0, 1.0)
    - Structural cosine similarity S_struct = struct_desc0[i] · struct_desc1[j] in [-1, 1].
      structural_similarity = np.clip(float((np.sum(struct_desc0 * struct_desc1) + 1.0) / 2.0), 0.0, 1.0)
    - Equal-weight fusion score:
      fusion_score = 0.5 * rift2_similarity + 0.5 * structural_similarity
    """
    n = len(idx0)
    if n == 0:
        return {
            "structural_scores": np.empty(0, dtype=np.float32),
            "structural_sims": np.empty(0, dtype=np.float32),
            "rift2_sims": np.empty(0, dtype=np.float32),
            "fusion_scores": np.empty(0, dtype=np.float32),
            "mean_structural_sim": np.nan,
            "median_structural_sim": np.nan,
            "min_structural_sim": np.nan,
            "max_structural_sim": np.nan,
            "mean_rift2_sim": np.nan,
            "mean_fusion_score": np.nan,
        }

    # Vectorized batch dot product across candidates
    d0_sub = desc0[idx0]
    d1_sub = desc1[idx1]
    rift2_sim = np.clip(np.sum(d0_sub * d1_sub, axis=1), 0.0, 1.0)

    sd0_sub = struct_desc0[idx0]
    sd1_sub = struct_desc1[idx1]
    s_struct = np.sum(sd0_sub * sd1_sub, axis=1)  # Cosine similarity in [-1, 1]
    struct_sim = np.clip((s_struct + 1.0) / 2.0, 0.0, 1.0)

    # Fixed 0.5 / 0.5 equal-weight fusion
    fusion = 0.5 * rift2_sim + 0.5 * struct_sim

    return {
        "structural_scores": s_struct,
        "structural_sims": struct_sim,
        "rift2_sims": rift2_sim,
        "fusion_scores": fusion,
        "mean_structural_sim": round(float(np.mean(struct_sim)), 4),
        "median_structural_sim": round(float(np.median(struct_sim)), 4),
        "min_structural_sim": round(float(np.min(struct_sim)), 4),
        "max_structural_sim": round(float(np.max(struct_sim)), 4),
        "mean_rift2_sim": round(float(np.mean(rift2_sim)), 4),
        "mean_fusion_score": round(float(np.mean(fusion)), 4),
    }


def run_rift2_structural_fusion_sweep(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    scale_source: float = 1.0,
    scale_reference: float = 1.0,
    thresholds: Tuple[float, ...] = (0.95, 0.97, 0.99),
    top_k_list: Tuple[int, ...] = (8, 12, 16, 24),
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    pair_label: str = "custom_pair",
    representation: str = "gradient_magnitude",
) -> Dict[str, Any]:
    """Execute complete RIFT2 Structural-Fusion / Re-Ranking sweep on a pair.

    Workflow:
    1. Preprocess & scale images if requested.
    2. Extract RIFT2 & structural patch descriptors ONCE per image.
    3. Run KNN matching sweep ONCE across NNDR thresholds [0.95, 0.97, 0.99].
    4. For each threshold:
       a. Evaluate RIFT2-only (All candidates) baseline.
       b. Compute structural similarities and fusion scores.
       c. Sort candidates descending by fusion_score (stable sort).
       d. For each Top-K in [8, 12, 16, 24]:
          Select top K candidates and evaluate through unchanged `execute_common_downstream`.
    """
    t_start = time.perf_counter()

    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if source_img.ndim == 3 else source_img.copy()
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if reference_img.ndim == 3 else reference_img.copy()

    orig_s_h, orig_s_w = s_gray.shape
    orig_r_h, orig_r_w = r_gray.shape

    # Apply scaling if requested
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

    # Step 1: Feature & Structural Descriptor Extraction ONCE
    t0_feat = time.perf_counter()
    feat_s = extract_rift2_and_structural_features(s_work, representation=representation)
    feat_r = extract_rift2_and_structural_features(r_work, representation=representation)
    total_feature_runtime = round(time.perf_counter() - t0_feat, 3)

    pts0 = feat_s["pts"]
    desc0 = feat_s["rift2_descriptors"]
    s_desc0 = feat_s["structural_descriptors"]

    pts1 = feat_r["pts"]
    desc1 = feat_r["rift2_descriptors"]
    s_desc1 = feat_r["structural_descriptors"]

    # Step 2: KNN Matching Sweep ONCE
    t0_match = time.perf_counter()
    sweep_data = match_rift2_with_pair_indices(pts0, desc0, pts1, desc1, thresholds=thresholds)
    matching_sweep_runtime = round(time.perf_counter() - t0_match, 4)

    results_list: List[Dict[str, Any]] = []

    # Step 3: Evaluate each NNDR threshold
    for tau in thresholds:
        m_info = sweep_data[tau]
        n_cands = m_info["candidates"]
        idx0 = m_info["idx0"]
        idx1 = m_info["idx1"]

        # Structural & Fusion Scoring
        t0_score = time.perf_counter()
        sim_data = compute_structural_similarity_and_fusion(desc0, desc1, s_desc0, s_desc1, idx0, idx1)
        scoring_runtime = round(time.perf_counter() - t0_score, 5)

        fusion_scores = sim_data["fusion_scores"]

        # --- Condition A: RIFT2-only (All Candidates) Baseline ---
        record_rift2 = {
            "pair": pair_label,
            "scale": f"{scale_source:.1f} / {scale_reference:.1f}",
            "nndr_threshold": tau,
            "method": "RIFT2-only",
            "top_k": "All",
            "candidates": n_cands,
            "initial_inliers": 0,
            "initial_inlier_ratio": 0.0,
            "spatial_occupancy": 0.0,
            "spatial_cv": 0.0,
            "fit_rmse": np.nan,
            "independent_held_out_rmse": np.nan,
            "runtime": round(total_feature_runtime + m_info["matching_runtime"], 3),
            "success": False,
            "failure_stage": None,
            "failure_reason": None,
            "mean_rift2_sim": sim_data["mean_rift2_sim"],
            "mean_structural_sim": sim_data["mean_structural_sim"],
            "median_structural_sim": sim_data["median_structural_sim"],
            "min_structural_sim": sim_data["min_structural_sim"],
            "max_structural_sim": sim_data["max_structural_sim"],
            "mean_fusion_score": sim_data["mean_fusion_score"],
        }

        if n_cands < 4:
            record_rift2["failure_stage"] = "descriptor_matching"
            record_rift2["failure_reason"] = f"Insufficient candidates ({n_cands} < 4)"
        else:
            pts0_nat = map_points_to_original(m_info["pts0"], (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
            pts1_nat = map_points_to_original(m_info["pts1"], (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))
            try:
                t0_down = time.perf_counter()
                down = execute_common_downstream(
                    pts0=pts0_nat,
                    pts1=pts1_nat,
                    confidences=None,
                    source_img=source_img,
                    reference_img=reference_img,
                    max_per_cell=6,
                    ransac_thresh=ransac_thresh,
                    seeds=seeds,
                )
                t_down = time.perf_counter() - t0_down
                record_rift2["runtime"] = round(record_rift2["runtime"] + t_down, 3)

                init_inl = int(down.get("n_initial_inliers", down.get("n_final_inliers", 0)))
                chk_rmse = down.get("mean_check_rmse")
                fit_rmse = down.get("fit_rmse")
                held_valid = down.get("held_out_valid", False)

                record_rift2["initial_inliers"] = init_inl
                record_rift2["initial_inlier_ratio"] = round(float(init_inl / max(1, n_cands)), 4)
                record_rift2["spatial_occupancy"] = round(float(down.get("spatial_occupancy", 0.0)), 4)
                record_rift2["spatial_cv"] = round(float(down.get("spatial_cv", 0.0)), 4)
                record_rift2["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
                record_rift2["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan

                if held_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                    record_rift2["success"] = True
                else:
                    record_rift2["success"] = False
                    record_rift2["failure_stage"] = "held_out_validation"
                    record_rift2["failure_reason"] = f"Insufficient inliers for independent held-out check ({init_inl} < 8)"
            except Exception as e:
                record_rift2["success"] = False
                record_rift2["failure_stage"] = "common_downstream"
                record_rift2["failure_reason"] = str(e)

        results_list.append(record_rift2)

        # --- Condition B: RIFT2 + Structural Fusion at Top-K ---
        # Sort candidates descending by fusion_score using stable sort
        if n_cands > 0:
            sort_order = np.argsort(-fusion_scores, kind="mergesort")
        else:
            sort_order = np.empty(0, dtype=int)

        for k in top_k_list:
            n_sel = min(k, n_cands)
            record_fused = {
                "pair": pair_label,
                "scale": f"{scale_source:.1f} / {scale_reference:.1f}",
                "nndr_threshold": tau,
                "method": "RIFT2 + structural fusion",
                "top_k": k,
                "candidates": n_sel,
                "initial_inliers": 0,
                "initial_inlier_ratio": 0.0,
                "spatial_occupancy": 0.0,
                "spatial_cv": 0.0,
                "fit_rmse": np.nan,
                "independent_held_out_rmse": np.nan,
                "runtime": round(total_feature_runtime + m_info["matching_runtime"] + scoring_runtime, 3),
                "success": False,
                "failure_stage": None,
                "failure_reason": None,
                "mean_rift2_sim": np.nan,
                "mean_structural_sim": np.nan,
                "median_structural_sim": np.nan,
                "min_structural_sim": np.nan,
                "max_structural_sim": np.nan,
                "mean_fusion_score": np.nan,
            }

            if n_sel < 4:
                record_fused["failure_stage"] = "structural_selection"
                record_fused["failure_reason"] = f"Insufficient candidates after top-{k} selection ({n_sel} < 4)"
                results_list.append(record_fused)
                continue

            sel_indices = sort_order[:n_sel]
            pts0_sel = pts0[idx0[sel_indices]]
            pts1_sel = pts1[idx1[sel_indices]]

            # Telemetry for the selected top-K subset
            sel_s_struct = sim_data["structural_sims"][sel_indices]
            sel_rift2 = sim_data["rift2_sims"][sel_indices]
            sel_fusion = fusion_scores[sel_indices]
            record_fused["mean_rift2_sim"] = round(float(np.mean(sel_rift2)), 4)
            record_fused["mean_structural_sim"] = round(float(np.mean(sel_s_struct)), 4)
            record_fused["median_structural_sim"] = round(float(np.median(sel_s_struct)), 4)
            record_fused["min_structural_sim"] = round(float(np.min(sel_s_struct)), 4)
            record_fused["max_structural_sim"] = round(float(np.max(sel_s_struct)), 4)
            record_fused["mean_fusion_score"] = round(float(np.mean(sel_fusion)), 4)

            # Map coordinates back to original native dimensions
            pts0_nat = map_points_to_original(pts0_sel, (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
            pts1_nat = map_points_to_original(pts1_sel, (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))

            try:
                t0_down = time.perf_counter()
                down = execute_common_downstream(
                    pts0=pts0_nat,
                    pts1=pts1_nat,
                    confidences=None,
                    source_img=source_img,
                    reference_img=reference_img,
                    max_per_cell=6,
                    ransac_thresh=ransac_thresh,
                    seeds=seeds,
                )
                t_down = time.perf_counter() - t0_down
                record_fused["runtime"] = round(record_fused["runtime"] + t_down, 3)

                init_inl = int(down.get("n_initial_inliers", down.get("n_final_inliers", 0)))
                chk_rmse = down.get("mean_check_rmse")
                fit_rmse = down.get("fit_rmse")
                held_valid = down.get("held_out_valid", False)

                record_fused["initial_inliers"] = init_inl
                record_fused["initial_inlier_ratio"] = round(float(init_inl / max(1, n_sel)), 4)
                record_fused["spatial_occupancy"] = round(float(down.get("spatial_occupancy", 0.0)), 4)
                record_fused["spatial_cv"] = round(float(down.get("spatial_cv", 0.0)), 4)
                record_fused["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
                record_fused["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan

                if held_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                    record_fused["success"] = True
                else:
                    record_fused["success"] = False
                    record_fused["failure_stage"] = "held_out_validation"
                    record_fused["failure_reason"] = f"Insufficient inliers for independent held-out check ({init_inl} < 8)"
            except Exception as e:
                record_fused["success"] = False
                record_fused["failure_stage"] = "common_downstream"
                record_fused["failure_reason"] = str(e)

            results_list.append(record_fused)

    # Master DataFrame
    df_rows = []
    for r in results_list:
        df_rows.append({
            "Pair": r["pair"],
            "Scale": r["scale"],
            "NNDR": r["nndr_threshold"],
            "Top-K": r["top_k"],
            "Method": r["method"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Ratio": r["initial_inlier_ratio"],
            "3×3 Occ.": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["runtime"],
            "Success": r["success"],
            "Failure": f"{r['failure_stage']}: {r['failure_reason']}" if not r["success"] else "None",
            "Mean RIFT2 Sim": r.get("mean_rift2_sim", np.nan),
            "Mean Struct Sim": r["mean_structural_sim"],
            "Median Struct Sim": r["median_structural_sim"],
            "Min Struct Sim": r["min_structural_sim"],
            "Max Struct Sim": r["max_structural_sim"],
            "Mean Fusion Score": r["mean_fusion_score"],
        })

    return {
        "results": results_list,
        "comparison_table": pd.DataFrame(df_rows),
        "total_feature_runtime": total_feature_runtime,
        "matching_sweep_runtime": matching_sweep_runtime,
        "total_runtime": round(time.perf_counter() - t_start, 3),
    }


def run_phase5_benchmark(
    iirs_src_path: str = r"C:\Users\Dell\Downloads\souse.jpeg",
    iirs_ref_path: str = r"C:\Users\Dell\Downloads\ref.jpeg",
    angle_pairs_base_dir: Optional[str] = None,
    thresholds: Tuple[float, ...] = (0.95, 0.97, 0.99),
    top_k_list: Tuple[int, ...] = (8, 12, 16, 24),
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    representation: str = "gradient_magnitude",
) -> Dict[str, Any]:
    """Execute complete Phase 5 Structural-Fusion / Re-Ranking benchmark across:

    1. IIRS <-> OHRC Native (1.0 / 1.0)
    2. Rotation pair (angle_pairs/pair_01)
    3. Viewpoint pair (angle_pairs/pair_02)
    4. Sun Angle pair (angle_pairs/pair_03)
    """
    all_trials: List[Dict[str, Any]] = []

    # Dataset A: IIRS <-> OHRC
    if os.path.exists(iirs_src_path) and os.path.exists(iirs_ref_path):
        s_iirs = cv2.imread(iirs_src_path)
        r_iirs = cv2.imread(iirs_ref_path)

        print("[Phase 5] Running IIRS <-> OHRC Native (1.0 / 1.0)...")
        res_iirs = run_rift2_structural_fusion_sweep(
            s_iirs,
            r_iirs,
            scale_source=1.0,
            scale_reference=1.0,
            thresholds=thresholds,
            top_k_list=top_k_list,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label="IIRS <-> OHRC (Native)",
            representation=representation,
        )
        all_trials.extend(res_iirs["results"])

    # Datasets B, C, D: Control Angle Pairs
    angle_data = load_angle_pairs(angle_pairs_base_dir)
    pair_mapping = {
        "pair_01": "Rotation Pair (pair_01)",
        "pair_02": "Viewpoint Pair (pair_02)",
        "pair_03": "Sun Angle Pair (pair_03)",
    }

    for vp in angle_data.get("valid_pairs", []):
        pid = vp["pair_id"]
        label = pair_mapping.get(pid, pid)
        print(f"[Phase 5] Running {label} Native (1.0 / 1.0)...")
        res_ang = run_rift2_structural_fusion_sweep(
            vp["source_img"],
            vp["reference_img"],
            scale_source=1.0,
            scale_reference=1.0,
            thresholds=thresholds,
            top_k_list=top_k_list,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label=label,
            representation=representation,
        )
        all_trials.extend(res_ang["results"])

    df_rows = []
    for r in all_trials:
        df_rows.append({
            "Pair": r["pair"],
            "Scale": r["scale"],
            "NNDR": r["nndr_threshold"],
            "Top-K": r["top_k"],
            "Method": r["method"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Ratio": r["initial_inlier_ratio"],
            "3×3 Occ.": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["runtime"],
            "Success": r["success"],
            "Failure": f"{r['failure_stage']}: {r['failure_reason']}" if not r["success"] else "None",
            "Mean RIFT2 Sim": r.get("mean_rift2_sim", np.nan),
            "Mean Struct Sim": r["mean_structural_sim"],
            "Median Struct Sim": r["median_structural_sim"],
            "Min Struct Sim": r["min_structural_sim"],
            "Max Struct Sim": r["max_structural_sim"],
            "Mean Fusion Score": r["mean_fusion_score"],
        })

    master_df = pd.DataFrame(df_rows)

    return {
        "trials": all_trials,
        "comparison_table": master_df,
    }
