"""
Pure Computer Vision Registration Core Module.
Contains reusable non-UI computer-vision functions, feature matching,
homography estimation, and validation primitives.

This module MUST NEVER import Streamlit or contain any UI execution.
"""

import os
import sys
import ssl
import time
import gc
import threading
import cv2
import numpy as np
import torch
from kornia.feature import LoFTR

# Disable SSL verification for model weight downloads on constrained platforms
ssl._create_default_https_context = ssl._create_unverified_context

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_MODEL_LOCK = threading.Lock()
_LOFTR_MATCHER = None


def load_loftr_matcher():
    """
    Load and cache the LoFTR outdoor pretrained model.
    Thread-safe process-level singleton caching without Streamlit dependency.
    """
    global _LOFTR_MATCHER
    if _LOFTR_MATCHER is None:
        with _MODEL_LOCK:
            if _LOFTR_MATCHER is None:
                matcher = LoFTR(pretrained="outdoor").to(_DEVICE)
                matcher.eval()
                _LOFTR_MATCHER = matcher
    return _LOFTR_MATCHER


def compute_matching_scale(image_shape, max_dim=1600, max_budget=1800000):
    """
    Computes an aspect-ratio-preserving scale factor for LoFTR matching.
    Guarantees:
      1. max(H, W) * scale <= max_dim (default 1600 px)
      2. H * scale * W * scale <= max_budget (default 1.8M pixels)
      3. Never enlarges the image (scale <= 1.0)
    Returns:
      scale (float), target_width (int), target_height (int)
    """
    h, w = image_shape[:2]
    if h <= 0 or w <= 0:
        raise ValueError(f"Invalid image dimensions: {image_shape}")

    scale_dim = float(max_dim) / float(max(h, w))
    scale_budget = (float(max_budget) / float(h * w)) ** 0.5
    scale = min(1.0, scale_dim, scale_budget)

    w_match = max(1, int(round(w * scale)))
    h_match = max(1, int(round(h * scale)))
    return scale, w_match, h_match


def preprocess_image(image):
    """
    Standard preprocessing: Grayscale conversion + CLAHE contrast enhancement.
    Tile grid: (8, 8), Clip limit: 2.0.
    """
    if image is None or image.size == 0:
        raise ValueError("Input image could not be decoded, is None, or is empty.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return gray, clahe.apply(gray)


def calculate_spatial_grid(points, image_shape, rows=3, cols=3):
    """
    Partition correspondence points into a rows x cols spatial grid
    and return the cell occupancy count matrix.
    """
    h, w = image_shape
    grid = np.zeros((rows, cols), dtype=int)
    for x, y in points:
        col = min(max(0, int(x / (w / cols))), cols - 1)
        row = min(max(0, int(y / (h / rows))), rows - 1)
        grid[row, col] += 1
    return grid


def split_spatially_balanced(points_src, image_shape, split_ratio=0.25, min_check_points=4, seed=42):
    """
    Spatially balanced partition of correspondences into estimation_points (~75%)
    and independent_check_points (~25%) preserving coverage across the 3x3 spatial grid.

    Guarantees:
      1. Every occupied cell with >= 2 points contributes at least 1 check point.
      2. Check points count >= min_check_points (if total points >= min_check_points + 4).
      3. Estimation points count >= 4 (sufficient for non-degenerate homography estimation).
    """
    rng = np.random.RandomState(seed)
    h, w = image_shape[:2]
    n_total = len(points_src)

    cell_bins = {(r, c): [] for r in range(3) for c in range(3)}
    for idx in range(n_total):
        pt = points_src[idx]
        col = min(max(0, int(pt[0] / (w / 3))), 2)
        row = min(max(0, int(pt[1] / (h / 3))), 2)
        cell_bins[(row, col)].append(idx)

    occupied_cells = [cell for cell, idxs in cell_bins.items() if len(idxs) > 0]
    if not occupied_cells or n_total < 8:
        shuffled = np.arange(n_total)
        rng.shuffle(shuffled)
        n_chk = max(min_check_points, int(round(n_total * split_ratio)))
        n_chk = min(n_chk, n_total - 4)
        return shuffled[n_chk:], shuffled[:n_chk]

    # Target number of check points (~25% of total points, at least min_check_points)
    total_check_needed = max(min_check_points, int(round(n_total * split_ratio)))
    total_check_needed = min(total_check_needed, n_total - 4)

    # Initial check counts per cell (at least 1 if cell has >= 2 points)
    cell_lens = [len(cell_bins[c]) for c in occupied_cells]
    cell_chk_counts = [max(1 if l >= 2 else 0, int(round(l * split_ratio))) for l in cell_lens]
    for i in range(len(cell_chk_counts)):
        cell_chk_counts[i] = min(cell_chk_counts[i], cell_lens[i] - 1)

    diff = sum(cell_chk_counts) - total_check_needed
    cell_order = list(range(len(occupied_cells)))
    rng.shuffle(cell_order)

    while diff > 0:
        reduced = False
        for c in cell_order:
            if cell_chk_counts[c] > 1 and diff > 0:
                cell_chk_counts[c] -= 1
                diff -= 1
                reduced = True
        if not reduced:
            break

    while diff < 0:
        increased = False
        for c in cell_order:
            if cell_chk_counts[c] < cell_lens[c] - 1 and diff < 0:
                cell_chk_counts[c] += 1
                diff += 1
                increased = True
        if not increased:
            break

    est_indices = []
    check_indices = []

    for i, cell in enumerate(occupied_cells):
        idx_arr = np.array(cell_bins[cell])
        rng.shuffle(idx_arr)
        k_chk = cell_chk_counts[i]
        check_indices.extend(idx_arr[:k_chk].tolist())
        est_indices.extend(idx_arr[k_chk:].tolist())

    return np.array(sorted(est_indices)), np.array(sorted(check_indices))


def run_independent_checkpoint_validation(points_src, points_ref, image_shape, seeds=(1, 2, 3, 4, 5), ransac_threshold=3.0):
    """
    Executes independent check-point validation across multiple deterministic seeds.
    For each seed:
      1. Spatially splits correspondences into estimation (~75%) and check (~25%) points.
      2. Estimates homography H_est using ONLY estimation_points (NEVER check points).
      3. Evaluates fit RMSE on estimation points.
      4. Transforms independent source check points through H_est.
      5. Computes independent check error metrics (mean, median, RMSE, max).
    Returns a comprehensive dictionary with primary run details and cross-seed summary stats.
    """
    if len(points_src) < 8:
        return None

    runs = []
    for seed in seeds:
        est_idx, chk_idx = split_spatially_balanced(points_src, image_shape, split_ratio=0.25, min_check_points=4, seed=seed)
        if len(est_idx) < 4 or len(chk_idx) < 4:
            continue

        src_est = points_src[est_idx]
        ref_est = points_ref[est_idx]
        src_chk = points_src[chk_idx]
        ref_chk = points_ref[chk_idx]

        # Estimate homography ONLY from estimation points
        H_est, mask_est = cv2.findHomography(
            src_est,
            ref_est,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_threshold,
            maxIters=10000,
            confidence=0.995
        )
        if H_est is None:
            continue

        # Fit metrics on estimation points
        proj_est = cv2.perspectiveTransform(src_est.reshape(-1, 1, 2), H_est).reshape(-1, 2)
        fit_errs = np.linalg.norm(proj_est - ref_est, axis=1)
        fit_rmse = float(np.sqrt(np.mean(fit_errs**2)))

        # Independent validation on strictly withheld check points
        pred_chk = cv2.perspectiveTransform(src_chk.reshape(-1, 1, 2), H_est).reshape(-1, 2)
        chk_errs = np.linalg.norm(pred_chk - ref_chk, axis=1)
        dx = pred_chk[:, 0] - ref_chk[:, 0]
        dy = pred_chk[:, 1] - ref_chk[:, 1]

        chk_rmse = float(np.sqrt(np.mean(chk_errs**2)))
        chk_mean = float(np.mean(chk_errs))
        chk_median = float(np.median(chk_errs))
        chk_max = float(np.max(chk_errs))

        runs.append({
            "seed": int(seed),
            "n_estimation": int(len(est_idx)),
            "n_check": int(len(chk_idx)),
            "fit_rmse": fit_rmse,
            "check_rmse": chk_rmse,
            "check_mean": chk_mean,
            "check_median": chk_median,
            "check_max": chk_max,
            "homography_est": H_est.tolist(),
            "est_indices": est_idx.tolist(),
            "check_indices": chk_idx.tolist(),
            "src_est": src_est.tolist(),
            "ref_est": ref_est.tolist(),
            "src_chk": src_chk.tolist(),
            "ref_chk": ref_chk.tolist(),
            "pred_chk": pred_chk.tolist(),
            "chk_errors": chk_errs.tolist(),
            "dx": dx.tolist(),
            "dy": dy.tolist(),
        })

    if not runs:
        return None

    all_rmses = [r["check_rmse"] for r in runs]
    all_means = [r["check_mean"] for r in runs]
    all_medians = [r["check_median"] for r in runs]
    all_maxes = [r["check_max"] for r in runs]

    summary = {
        "runs": runs,
        "primary_run": runs[0], # Seed 1 as primary
        "mean_check_rmse": float(np.mean(all_rmses)),
        "median_check_rmse": float(np.median(all_rmses)),
        "best_check_rmse": float(np.min(all_rmses)),
        "worst_check_rmse": float(np.max(all_rmses)),
        "mean_check_mean": float(np.mean(all_means)),
        "mean_check_median": float(np.mean(all_medians)),
        "mean_check_max": float(np.mean(all_maxes)),
    }
    return summary


def register_images(source_image, reference_image, max_per_cell=6, ransac_threshold=3.0, max_loftr_dim=1600, max_pixel_budget=1800000):
    """
    LOCKED CORE REGISTRATION PIPELINE WITH MEMORY-SAFE LARGE IMAGE PREPROCESSING:
    Detect Dims -> Aspect-Ratio Safe Scale -> CLAHE -> Memory-Safe LoFTR Matching -> Coordinate Back-Mapping ->
    Initial RANSAC -> Quality + 3x3 Spatial Selection -> Final Homography -> Full-Resolution Warping -> Telemetry Metrics.
    """
    start_time = time.perf_counter()
    matcher = load_loftr_matcher()

    # Step 0: Robust Input Dimension Verification
    if source_image is None or reference_image is None:
        raise ValueError("Input image is None or could not be decoded.")
    if source_image.size == 0 or reference_image.size == 0:
        raise ValueError("Input image has zero pixels.")
    if min(source_image.shape[:2]) < 32 or min(reference_image.shape[:2]) < 32:
        raise ValueError(f"Image dimensions too small for registration: source {source_image.shape[:2]}, ref {reference_image.shape[:2]}.")

    # Step 1: Preprocessing & CLAHE (kept at original full resolution)
    source_gray, source_clahe = preprocess_image(source_image)
    reference_gray, reference_clahe = preprocess_image(reference_image)
    s_h, s_w = source_gray.shape
    r_h, r_w = reference_gray.shape

    # Step 2: Compute Aspect-Ratio Preserving Matching Scales
    scale_s, s_w_match, s_h_match = compute_matching_scale((s_h, s_w), max_dim=max_loftr_dim, max_budget=max_pixel_budget)
    scale_r, r_w_match, r_h_match = compute_matching_scale((r_h, r_w), max_dim=max_loftr_dim, max_budget=max_pixel_budget)

    # Scale validity checks
    if not (0 < scale_s <= 1.0) or not np.isfinite(scale_s):
        raise ValueError(f"Invalid computed source scale factor: {scale_s}")
    if not (0 < scale_r <= 1.0) or not np.isfinite(scale_r):
        raise ValueError(f"Invalid computed reference scale factor: {scale_r}")

    # Resize only the copies used for LoFTR matching (preserve original images)
    if scale_s < 1.0:
        s_match = cv2.resize(source_clahe, (s_w_match, s_h_match), interpolation=cv2.INTER_AREA)
    else:
        s_match = source_clahe
        s_w_match, s_h_match = s_w, s_h

    if scale_r < 1.0:
        r_match = cv2.resize(reference_clahe, (r_w_match, r_h_match), interpolation=cv2.INTER_AREA)
    else:
        r_match = reference_clahe
        r_w_match, r_h_match = r_w, r_h

    # Exact coordinate scale factors: match coordinate -> original coordinate
    sx0 = float(s_w) / float(s_w_match)
    sy0 = float(s_h) / float(s_h_match)
    sx1 = float(r_w) / float(r_w_match)
    sy1 = float(r_h) / float(r_h_match)

    # Step 3: LoFTR Feature Matching with torch.inference_mode()
    source_tensor = torch.from_numpy(s_match.astype(np.float32) / 255.0)[None, None].to(_DEVICE)
    reference_tensor = torch.from_numpy(r_match.astype(np.float32) / 255.0)[None, None].to(_DEVICE)

    with torch.inference_mode():
        output = matcher({"image0": source_tensor, "image1": reference_tensor})

    mkpts0_match = output["keypoints0"].cpu().numpy()
    mkpts1_match = output["keypoints1"].cpu().numpy()
    confidence = output["confidence"].cpu().numpy()

    # Explicitly release temporary tensors and run garbage collection
    del source_tensor, reference_tensor, output
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if len(mkpts0_match) < 4:
        raise RuntimeError(f"LoFTR detected insufficient candidate matches ({len(mkpts0_match)}). Minimum 4 required for geometric alignment.")

    # Step 4: Map Keypoint Coordinates Back to ORIGINAL Image Coordinates
    mkpts0 = mkpts0_match.copy()
    mkpts1 = mkpts1_match.copy()
    mkpts0[:, 0] *= sx0
    mkpts0[:, 1] *= sy0
    mkpts1[:, 0] *= sx1
    mkpts1[:, 1] *= sy1

    # Step 5: Initial RANSAC Homography on Original Coordinates
    H_initial, mask_initial = cv2.findHomography(
        mkpts0,
        mkpts1,
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        maxIters=10000,
        confidence=0.995
    )
    if H_initial is None or mask_initial is None:
        raise RuntimeError("Initial RANSAC homography estimation failed. Could not establish geometric consensus.")

    inlier_ids = np.where(mask_initial.ravel() == 1)[0]
    if len(inlier_ids) < 4:
        raise RuntimeError(f"Initial RANSAC yielded insufficient inliers ({len(inlier_ids)}). Minimum 4 required.")

    # Step 6: Reprojection Error & Quality Scoring (in Original Coordinate Space)
    proj = cv2.perspectiveTransform(mkpts0[inlier_ids].reshape(-1, 1, 2), H_initial).reshape(-1, 2)
    errors = np.linalg.norm(proj - mkpts1[inlier_ids], axis=1)
    quality_score = confidence[inlier_ids] / (1.0 + errors)

    # Step 7: 3x3 Spatial Grid Binning & Quality Selection on ORIGINAL Dimensions
    cells = {(r, c): [] for r in range(3) for c in range(3)}
    for local_idx, original_idx in enumerate(inlier_ids):
        col = min(max(0, int(mkpts0[original_idx][0] / (s_w / 3))), 2)
        row = min(max(0, int(mkpts0[original_idx][1] / (s_h / 3))), 2)
        cells[(row, col)].append(local_idx)

    selected_local = []
    for cell, indices in cells.items():
        if indices:
            selected_local.extend(sorted(indices, key=lambda i: quality_score[i], reverse=True)[:max_per_cell])

    selected_ids = inlier_ids[selected_local]
    if len(selected_ids) < 4:
        raise RuntimeError(f"Spatial selection produced insufficient correspondences ({len(selected_ids)}). Minimum 4 required.")

    # Step 8: Final Homography Estimation on Selected Subset (Original Coordinates)
    H_final, mask_final = cv2.findHomography(
        mkpts0[selected_ids],
        mkpts1[selected_ids],
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        maxIters=10000,
        confidence=0.995
    )
    if H_final is None or mask_final is None:
        raise RuntimeError("Final RANSAC homography estimation failed.")

    final_inlier_ids = selected_ids[mask_final.ravel() == 1]
    if len(final_inlier_ids) < 4:
        raise RuntimeError(f"Final RANSAC yielded insufficient inliers ({len(final_inlier_ids)}). Minimum 4 required.")

    # Step 9: Final Reprojection Metrics (Calculated on Original Reference Pixels)
    src_f = mkpts0[final_inlier_ids]
    ref_f = mkpts1[final_inlier_ids]
    proj_f = cv2.perspectiveTransform(src_f.reshape(-1, 1, 2), H_final).reshape(-1, 2)
    final_errs = np.linalg.norm(proj_f - ref_f, axis=1)

    # Step 10: Source Image Warping to ORIGINAL Reference Dimensions
    reg_img = cv2.warpPerspective(source_gray, H_final, (r_w, r_h))

    # Step 11: Match Vector Visualization Canvas
    s_v = cv2.cvtColor(source_clahe, cv2.COLOR_GRAY2BGR)
    r_v = cv2.cvtColor(reference_clahe, cv2.COLOR_GRAY2BGR)
    canvas = np.zeros((max(s_v.shape[0], r_v.shape[0]), s_v.shape[1] + r_v.shape[1], 3), dtype=np.uint8)
    canvas[:s_v.shape[0], :s_v.shape[1]] = s_v
    canvas[:r_v.shape[0], s_v.shape[1]:] = r_v
    line_thickness = max(1, int(round(max(s_v.shape[0], r_v.shape[0]) / 1000)))
    circle_radius = max(2, int(round(max(s_v.shape[0], r_v.shape[0]) / 500)))
    for i in final_inlier_ids:
        pt0 = (int(round(mkpts0[i][0])), int(round(mkpts0[i][1])))
        pt1 = (int(round(mkpts1[i][0] + s_v.shape[1])), int(round(mkpts1[i][1])))
        cv2.line(canvas, pt0, pt1, (0, 255, 255), line_thickness, cv2.LINE_AA)
        cv2.circle(canvas, pt0, circle_radius, (0, 255, 0), -1)
        cv2.circle(canvas, pt1, circle_radius, (0, 0, 255), -1)

    # Spatial distribution grids
    selected_grid = calculate_spatial_grid(mkpts0[selected_ids], (s_h, s_w))
    final_grid = calculate_spatial_grid(src_f, (s_h, s_w))

    # Occupancy and Spatial CV calculation
    occupied_cells = int(np.count_nonzero(selected_grid))
    total_cells = 9
    occupancy_ratio = float(occupied_cells / total_cells)
    spatial_cv = float(np.std(selected_grid) / np.mean(selected_grid)) if np.mean(selected_grid) > 0 else 0.0

    resizing_applied = bool(scale_s < 1.0 or scale_r < 1.0)

    # Step 12: Independent Check-Point Validation (Spatially Balanced Hold-Out across 5 Seeds)
    independent_validation = run_independent_checkpoint_validation(
        mkpts0[selected_ids],
        mkpts1[selected_ids],
        (s_h, s_w),
        seeds=(1, 2, 3, 4, 5),
        ransac_threshold=ransac_threshold
    )

    return {
        "registered_image": reg_img,
        "match_visualization": canvas,
        "spatial_grid": final_grid,
        "selected_grid": selected_grid,
        "selected_ids": selected_ids.tolist(),
        "final_inlier_ids": final_inlier_ids.tolist(),
        "mkpts0_orig": mkpts0.tolist(),
        "mkpts1_orig": mkpts1.tolist(),
        "candidate_matches": int(len(mkpts0)),
        "initial_inliers": int(len(inlier_ids)),
        "initial_inlier_ratio": float(len(inlier_ids) / len(mkpts0)),
        "selected_matches": int(len(selected_ids)),
        "final_inliers": int(len(final_inlier_ids)),
        "final_inlier_ratio": float(len(final_inlier_ids) / len(selected_ids)),
        "rmse": float(np.sqrt(np.mean(final_errs**2))),
        "mean_error": float(np.mean(final_errs)),
        "median_error": float(np.median(final_errs)),
        "max_error": float(np.max(final_errs)),
        "occupied_cells": occupied_cells,
        "total_cells": total_cells,
        "occupancy_ratio": occupancy_ratio,
        "spatial_cv": spatial_cv,
        "homography_matrix": H_final.tolist(),
        "runtime": float(time.perf_counter() - start_time),
        "device": _DEVICE,
        # Resolution & Scale Telemetry
        "orig_source_shape": (s_h, s_w),
        "orig_ref_shape": (r_h, r_w),
        "match_source_shape": (s_h_match, s_w_match),
        "match_ref_shape": (r_h_match, r_w_match),
        "scale_source": float(scale_s),
        "scale_ref": float(scale_r),
        "resizing_applied": resizing_applied,
        "max_loftr_dim": max_loftr_dim,
        "max_pixel_budget": max_pixel_budget,
        # Independent Validation Module Telemetry
        "independent_validation": independent_validation,
    }


__all__ = [
    "_DEVICE",
    "load_loftr_matcher",
    "compute_matching_scale",
    "preprocess_image",
    "calculate_spatial_grid",
    "split_spatially_balanced",
    "run_independent_checkpoint_validation",
    "register_images",
]
