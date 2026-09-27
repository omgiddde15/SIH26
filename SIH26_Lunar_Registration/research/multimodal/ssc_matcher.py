"""
research/multimodal/ssc_matcher.py
==================================
Experimental SSC-Style (Self-Similarity Context) 2-D Adaptation Matcher
(LunarReg Phase 7 — Research Branch).

Research Objective:
Test whether a richer self-similarity context encoding relationships between
local neighbouring patches (rather than centre-to-neighbour similarity alone)
can improve correspondence specificity relative to the 6-D MIND-style representation.

Documented LunarReg Research Adaptations:
1. Keypoint Detection:
   - Reuses the exact corrected Phase 6 independent structural detector:
     Grayscale -> Sobel gradient magnitude -> FAST (threshold=10) -> fallback (threshold=5 if <50 detections)
     -> boundary margin guard (8 px) -> deterministic response-based sorting -> max 1500 keypoints.
   - Zero dependency on RIFT2, Log-Gabor filter banks, Phase Congruency, or MIM.
2. Descriptor Formulation ("SSC-style 2-D adaptation"):
   - Sampling geometry: Central patch (index 0) of size 7 × 7 pixels, plus 6 symmetric radial
     neighbouring patches (indices 1..6) at distance R = 4.0 px along angles {0°, 60°, 120°, 180°, 240°, 300°}.
   - Sampling: Exact subpixel bilinear interpolation via cv2.getRectSubPix.
   - Pairwise Relations: Computes all C(7, 2) = 21 pairwise Mean Squared Differences (MSD) across the
     7 sampled patches:
       * 6 centre-to-neighbour pairs: (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6)
       * 6 adjacent neighbour pairs around perimeter: (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)
       * 3 diametrically opposite neighbour pairs: (1, 4), (2, 5), (3, 6)
       * 6 skew / chordal neighbour pairs: (1, 3), (2, 4), (3, 5), (4, 6), (5, 1), (6, 2)
   - Local Noise Scale: V(x) = median_{i < j}(D_{ij}(x)) + 1e-6.
   - Self-Similarity Response: S_{ij}(x) = exp(-D_{ij}(x) / V(x)).
   - Normalization: Deterministic L2-normalized 21-dimensional unit vector.
3. Matching Policy:
   - Forward KNN (k=2) + backward KNN (k=1) mutual consistency check.
   - Fixed NNDR ratio threshold: 0.90 (no initial threshold sweeping).
   - Spatial coordinate deduplication.
4. Downstream Evaluation:
   - Candidate correspondences evaluated through the UNCHANGED `execute_common_downstream`
     (RANSAC threshold 3.0 px, confidence 0.995, 3×3 spatial binning max 6 pts/cell, seeds 1–5).
   - Initial Inlier Ratio strictly computed as initial_inliers / candidates.
"""

import os
import sys
import time
import gc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.multimodal_preprocess import to_gradient_magnitude
from research.multimodal.scale_search import map_points_to_original
from research.adaptive_matcher.adaptive_engine import execute_common_downstream

_MAX_SAFE_PIXELS = 9_000_000
_MAX_SAFE_DIM = 3500


@dataclass
class SSCConfig:
    """Hyperparameters for SSC-style local self-similarity context descriptor and matching."""
    patch_size: int = 7
    radius: float = 4.0
    n_neighbors: int = 6
    angles: Tuple[float, ...] = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)
    epsilon: float = 1e-6
    max_keypoints: int = 1500
    fast_threshold: int = 10
    nndr_threshold: float = 0.90
    margin: int = 8  # (patch_size // 2) + int(ceil(radius)) + 1 = 3 + 4 + 1 = 8
    detector_name: str = "Independent Sobel-gradient + FAST"
    detector_parameters: str = "Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500)"
    descriptor_name: str = "SSC-style 2-D adaptation"
    descriptor_dimension: int = 21


def compute_ssc_offsets(
    radius: float = 4.0,
    angles: Tuple[float, ...] = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0),
) -> np.ndarray:
    """Compute 2D Cartesian spatial offsets (dx, dy) for all 7 sampling positions.

    Index 0: (0.0, 0.0) - Central patch
    Indices 1..6: Radial neighbours at distance radius along specified angles.
    Returns: (7, 2) float32 array of relative offsets.
    """
    rad_angles = np.radians(angles)
    dx = radius * np.cos(rad_angles)
    dy = radius * np.sin(rad_angles)
    neighbor_offsets = np.column_stack([dx, dy]).astype(np.float32)
    center_offset = np.zeros((1, 2), dtype=np.float32)
    return np.vstack([center_offset, neighbor_offsets])


def get_ssc_pair_indices() -> List[Tuple[int, int]]:
    """Return canonical ordered list of unique pairs (i, j) with 0 <= i < j <= 6.

    Total: C(7, 2) = 21 pairs.
    """
    return [(i, j) for i in range(7) for j in range(i + 1, 7)]


def detect_ssc_keypoints(
    img_gray: np.ndarray,
    max_kps: int = 1500,
    fast_threshold: int = 10,
    margin: int = 8,
) -> Tuple[np.ndarray, int]:
    """Detect independent structural keypoints using Sobel gradient magnitude and FAST.

    Reuses the exact corrected Phase 6 detector:
    grayscale image -> Sobel gradient magnitude -> FAST detector -> fallback if <50 -> margin guard -> response sorting -> max_kps.

    Guarantees:
    - Zero dependency on RIFT2, Log-Gabor filters, Phase Congruency, or MIM.
    - Completely deterministic.
    - Preserves boundary margin to ensure patch extraction never falls out of bounds.
    - Capped at max_kps.

    Returns:
    - pts: (N, 2) array of keypoint coordinates [x, y].
    - base_count: Raw count of detected FAST keypoints before capping.
    """
    h, w = img_gray.shape

    # 1. Structural gradient magnitude via Sobel (Phase 1 implementation)
    grad_mag = to_gradient_magnitude(img_gray, ksize=3)

    # 2. FAST detector on gradient magnitude
    fast = cv2.FastFeatureDetector_create(threshold=fast_threshold, nonmaxSuppression=True)
    raw_kps = fast.detect(grad_mag)

    # Adaptive fallback if texture is low
    if len(raw_kps) < 50:
        fast_low = cv2.FastFeatureDetector_create(threshold=max(4, fast_threshold // 2), nonmaxSuppression=True)
        raw_kps = fast_low.detect(grad_mag)

    base_count = len(raw_kps)

    # 3. Boundary margin guard
    valid_kps = [
        kp for kp in raw_kps
        if (margin <= kp.pt[0] <= w - 1 - margin and margin <= kp.pt[1] <= h - 1 - margin)
    ]

    # 4. Deterministic response-based sorting (with coordinate tie-breaking)
    valid_kps.sort(key=lambda k: (-k.response, k.pt[1], k.pt[0]))
    selected_kps = valid_kps[:max_kps]

    if selected_kps:
        pts = np.array([[kp.pt[0], kp.pt[1]] for kp in selected_kps], dtype=np.float32)
    else:
        pts = np.empty((0, 2), dtype=np.float32)

    return pts, base_count


def compute_ssc_descriptors(
    img_gray: np.ndarray,
    pts: np.ndarray,
    config: Optional[SSCConfig] = None,
) -> np.ndarray:
    """Extract deterministic 21-dimensional SSC-style local self-similarity context descriptors.

    Algorithm:
    For each keypoint x:
      1. Extract central 7×7 patch P_0 via subpixel bilinear interpolation.
      2. Extract 6 neighbouring 7×7 patches P_1..P_6 at radius 4.0 in 6 radial directions.
      3. Compute Mean Squared Difference (MSD) for all C(7, 2) = 21 patch pairs:
           D_{ij}(x) = mean((P_i - P_j)^2), 0 <= i < j <= 6.
      4. Compute local variance estimate V(x) = median_{i < j}(D_{ij}(x)) + epsilon.
      5. Compute self-similarity context responses S_{ij}(x) = exp(-D_{ij}(x) / V(x)).
      6. L2-normalize the resulting 21-D vector.

    Returns:
    - descs: (N, 21) array of L2-normalized float32 descriptors.
    """
    if config is None:
        config = SSCConfig()

    n_pts = len(pts)
    n_dim = config.descriptor_dimension
    if n_pts == 0:
        return np.empty((0, n_dim), dtype=np.float32)

    # Normalize image to float32 [0, 1]
    img_f = img_gray.astype(np.float32) / 255.0
    h, w = img_gray.shape

    offsets = compute_ssc_offsets(radius=config.radius, angles=config.angles)  # shape (7, 2)
    pair_indices = get_ssc_pair_indices()  # 21 pairs
    patch_size = (config.patch_size, config.patch_size)
    eps = config.epsilon

    descs = np.zeros((n_pts, n_dim), dtype=np.float32)

    for i in range(n_pts):
        x = float(pts[i, 0])
        y = float(pts[i, 1])

        # Extract all 7 patches via subpixel bilinear interpolation
        patches = [
            cv2.getRectSubPix(img_f, patch_size, (x + float(offsets[k, 0]), y + float(offsets[k, 1])))
            for k in range(7)
        ]

        # Compute 21 pairwise MSD dissimilarities
        D = np.zeros(n_dim, dtype=np.float32)
        for p_idx, (pi, pj) in enumerate(pair_indices):
            diff = patches[pi] - patches[pj]
            D[p_idx] = float(np.mean(diff ** 2))

        # Local variance normalization
        V = float(np.median(D)) + eps

        # Self-similarity context responses
        S = np.exp(-D / V)

        # Deterministic L2 normalization
        norm = float(np.linalg.norm(S))
        if norm > 1e-6:
            descs[i] = S / norm
        else:
            descs[i] = np.zeros(n_dim, dtype=np.float32)

    return descs


def match_ssc_descriptors(
    pts0: np.ndarray,
    desc0: np.ndarray,
    pts1: np.ndarray,
    desc1: np.ndarray,
    nndr_threshold: float = 0.90,
) -> Dict[str, Any]:
    """Perform deterministic Nearest-Neighbor Distance Ratio (NNDR) matching with
    mutual cross-check and spatial deduplication on SSC-style descriptors.
    """
    t0 = time.perf_counter()

    n_raw_queries = len(desc0)
    if n_raw_queries == 0 or len(desc1) == 0:
        return {
            "method": "SSC-style 2-D adaptation",
            "success": False,
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "confidences": None,
            "n_raw_queries": n_raw_queries,
            "n_nndr_matches": 0,
            "n_mutual_matches": 0,
            "n_candidates": 0,
            "descriptor_dimension": 21,
            "runtime": round(time.perf_counter() - t0, 4),
            "failure_stage": "descriptor_matching",
            "failure_reason": "Empty descriptor set.",
        }

    bf = cv2.BFMatcher(cv2.NORM_L2)

    # 1. Forward KNN (k=2)
    matches_01 = bf.knnMatch(desc0, desc1, k=2)

    # 2. Backward KNN (k=1) for mutual cross-check
    matches_10 = bf.knnMatch(desc1, desc0, k=1)
    best_10: Dict[int, int] = {m[0].queryIdx: m[0].trainIdx for m in matches_10 if len(m) > 0}

    # 3. NNDR filtering
    nndr_pairs: List[Tuple[int, int]] = []
    for m in matches_01:
        if len(m) == 2:
            if m[0].distance < nndr_threshold * m[1].distance:
                nndr_pairs.append((m[0].queryIdx, m[0].trainIdx))
        elif len(m) == 1:
            nndr_pairs.append((m[0].queryIdx, m[0].trainIdx))

    n_nndr = len(nndr_pairs)

    # 4. Mutual consistency filtering
    mutual_pairs: List[Tuple[int, int]] = []
    for q_idx, t_idx in nndr_pairs:
        if best_10.get(t_idx) == q_idx:
            mutual_pairs.append((q_idx, t_idx))

    n_mutual = len(mutual_pairs)

    # 5. Spatial coordinate deduplication
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

    n_candidates = len(uniq_pairs)

    if n_candidates > 0:
        idx0 = [p[0] for p in uniq_pairs]
        idx1 = [p[1] for p in uniq_pairs]
        pts0_cand = pts0[idx0]
        pts1_cand = pts1[idx1]
    else:
        pts0_cand = np.empty((0, 2), dtype=np.float32)
        pts1_cand = np.empty((0, 2), dtype=np.float32)

    matching_runtime = round(time.perf_counter() - t0, 4)

    return {
        "method": "SSC-style 2-D adaptation",
        "success": n_candidates >= 4,
        "pts0": pts0_cand,
        "pts1": pts1_cand,
        "confidences": None,
        "n_raw_queries": n_raw_queries,
        "n_nndr_matches": n_nndr,
        "n_mutual_matches": n_mutual,
        "n_candidates": n_candidates,
        "descriptor_dimension": 21,
        "runtime": matching_runtime,
        "failure_stage": None if n_candidates >= 4 else "descriptor_matching",
        "failure_reason": None if n_candidates >= 4 else f"Insufficient candidates ({n_candidates} < 4)",
    }


def run_ssc_matching(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    scale_source: float = 1.0,
    scale_reference: float = 1.0,
    config: Optional[SSCConfig] = None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    pair_label: str = "custom_pair",
) -> Dict[str, Any]:
    """Execute complete end-to-end SSC-style candidate generation and common downstream registration.

    Workflow:
    1. Preprocess & scale images if requested.
    2. Detect independent structural keypoints (Sobel gradient magnitude + FAST).
    3. Compute 21-D SSC-style local self-similarity context descriptors.
    4. Match descriptors with NNDR 0.90, mutual check, and spatial deduplication.
    5. Map candidate coordinates back to native image resolution.
    6. Evaluate through UNCHANGED `execute_common_downstream()`.
    """
    if config is None:
        config = SSCConfig()

    t_start = time.perf_counter()

    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if source_img.ndim == 3 else source_img.copy()
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if reference_img.ndim == 3 else reference_img.copy()

    orig_s_h, orig_s_w = s_gray.shape
    orig_r_h, orig_r_w = r_gray.shape

    # Preflight resource check
    if orig_s_h * orig_s_w > _MAX_SAFE_PIXELS or orig_r_h * orig_r_w > _MAX_SAFE_PIXELS:
        raise RuntimeError("Image dimensions exceed safe limit for research execution.")

    # 1. Apply candidate scaling if specified
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

    # 2. Keypoint Detection (Independent Sobel + FAST)
    t0_kps = time.perf_counter()
    pts_s, total_kps_s = detect_ssc_keypoints(
        s_work,
        max_kps=config.max_keypoints,
        fast_threshold=config.fast_threshold,
        margin=config.margin,
    )
    pts_r, total_kps_r = detect_ssc_keypoints(
        r_work,
        max_kps=config.max_keypoints,
        fast_threshold=config.fast_threshold,
        margin=config.margin,
    )
    t_kps = time.perf_counter() - t0_kps

    # 3. Descriptor Extraction (21-D Local Self-Similarity Context)
    t0_desc = time.perf_counter()
    desc_s = compute_ssc_descriptors(s_work, pts_s, config)
    desc_r = compute_ssc_descriptors(r_work, pts_r, config)
    t_desc = time.perf_counter() - t0_desc

    # 4. Descriptor Matching
    t0_match = time.perf_counter()
    match_res = match_ssc_descriptors(
        pts0=pts_s,
        desc0=desc_s,
        pts1=pts_r,
        desc1=desc_r,
        nndr_threshold=config.nndr_threshold,
    )
    t_match = time.perf_counter() - t0_match

    n_cands = match_res["n_candidates"]

    record: Dict[str, Any] = {
        "pair": pair_label,
        "detector_name": config.detector_name,
        "detector_parameters": config.detector_parameters,
        "descriptor": config.descriptor_name,
        "scale": f"{scale_source:.1f} / {scale_reference:.1f}",
        "source_scale": scale_source,
        "reference_scale": scale_reference,
        "base_keypoints_source": total_kps_s,
        "base_keypoints_reference": total_kps_r,
        "valid_keypoints_source": len(pts_s),
        "valid_keypoints_reference": len(pts_r),
        "descriptor_dimension": config.descriptor_dimension,
        "rift2_dependency": "None",
        "raw_queries": match_res["n_raw_queries"],
        "nndr_matches": match_res["n_nndr_matches"],
        "mutual_matches": match_res["n_mutual_matches"],
        "candidates": n_cands,
        "initial_inliers": 0,
        "initial_inlier_ratio": 0.0,
        "spatial_occupancy": 0.0,
        "spatial_cv": 0.0,
        "fit_rmse": np.nan,
        "independent_held_out_rmse": np.nan,
        "feature_runtime": round(t_kps + t_desc, 3),
        "matching_runtime": round(t_match, 4),
        "total_runtime": round(time.perf_counter() - t_start, 3),
        "success": False,
        "failure_stage": match_res["failure_stage"],
        "failure_reason": match_res["failure_reason"],
        "match_result": match_res,
        "downstream_result": None,
    }

    if n_cands < 4:
        record["failure_stage"] = "descriptor_matching"
        record["failure_reason"] = f"Insufficient candidates ({n_cands} < 4)"
        return record

    # 5. Native coordinate inverse-mapping
    pts0_native = map_points_to_original(match_res["pts0"], (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
    pts1_native = map_points_to_original(match_res["pts1"], (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))

    # 6. Common downstream registration
    try:
        t0_down = time.perf_counter()
        down = execute_common_downstream(
            pts0=pts0_native,
            pts1=pts1_native,
            confidences=None,
            source_img=source_img,
            reference_img=reference_img,
            max_per_cell=6,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
        )
        t_down = time.perf_counter() - t0_down
        record["total_runtime"] = round(record["total_runtime"] + t_down, 3)
        record["downstream_result"] = down

        init_inl = int(down.get("n_initial_inliers", down.get("n_final_inliers", 0)))
        chk_rmse = down.get("mean_check_rmse")
        fit_rmse = down.get("fit_rmse")
        held_valid = down.get("held_out_valid", False)

        record["initial_inliers"] = init_inl
        record["initial_inlier_ratio"] = round(float(init_inl / max(1, n_cands)), 4)
        record["spatial_occupancy"] = round(float(down.get("spatial_occupancy", 0.0)), 4)
        record["spatial_cv"] = round(float(down.get("spatial_cv", 0.0)), 4)
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

    return record
