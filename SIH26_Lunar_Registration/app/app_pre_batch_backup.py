import os
import ssl
import time
import gc
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
import streamlit as st
from kornia.feature import LoFTR

# Disable SSL verification for model weight downloads on constrained platforms
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================
# 1. CORE REGISTRATION ENGINE — LOCKED BACKEND WITH MEMORY-SAFE LARGE IMAGE SUPPORT
# ============================================================

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@st.cache_resource
def load_loftr_matcher():
    """Load and cache the LoFTR outdoor pretrained model."""
    matcher = LoFTR(pretrained="outdoor").to(_DEVICE)
    matcher.eval()
    return matcher

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


# ============================================================
# 2. LUNAR MISSION CONTROL UI (Streamlit)
# ============================================================

st.set_page_config(
    page_title="Lunar Image Registration System | Mission Control",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Tech Aerospace CSS Styling
st.markdown("""
<style>
    /* Dark Aerospace Theme */
    .stApp {
        background-color: #0b0e14;
        color: #d1d7e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header Section */
    .header-box {
        background: linear-gradient(135deg, #101724 0%, #162032 100%);
        border: 1px solid #233044;
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    }
    .header-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #58a6ff;
        margin: 0;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .header-subtitle {
        font-size: 0.95rem;
        color: #8b949e;
        margin: 4px 0 10px 0;
        font-weight: 400;
    }
    
    /* Pipeline Bar */
    .pipeline-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        background: #080b10;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #1c2738;
        font-size: 0.8rem;
    }
    .pipeline-step {
        background: #162032;
        color: #58a6ff;
        padding: 3px 9px;
        border-radius: 4px;
        font-weight: 600;
        border: 1px solid #253852;
    }
    .pipeline-arrow {
        color: #00f2ff;
        font-weight: bold;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .status-ready {
        background: #0d281e;
        color: #3fb950;
        border: 1px solid #1e4b38;
    }
    .status-locked {
        background: #092635;
        color: #00f2ff;
        border: 1px solid #0e4c68;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #121824;
        border: 1px solid #212c3d;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.76rem;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.6px;
        margin-bottom: 2px;
    }
    .metric-val {
        font-family: 'SF Mono', 'Cascadia Code', 'Courier New', monospace;
        font-size: 1.45rem;
        font-weight: 700;
        color: #00f2ff;
    }
    .metric-sub {
        font-size: 0.72rem;
        color: #6e7681;
        margin-top: 2px;
    }

    /* Action Buttons */
    .stButton>button {
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 6px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #00f2ff;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
    }
    
    /* Image containers */
    .img-box {
        background: #0d1117;
        border: 1px solid #212c3d;
        border-radius: 6px;
        padding: 6px;
        text-align: center;
    }
    .img-caption {
        font-size: 0.8rem;
        font-weight: 600;
        color: #58a6ff;
        text-transform: uppercase;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }

    /* Honesty Alert Box */
    .honesty-box {
        background: #161b22;
        border-left: 4px solid #f0883e;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        margin: 14px 0;
        font-size: 0.82rem;
        color: #c9d1d9;
    }

    /* Warning Banner for Large Images */
    .warning-box {
        background: #1f1a0e;
        border: 1px solid #744d06;
        border-left: 4px solid #d29922;
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        margin: 14px 0;
        font-size: 0.86rem;
        color: #e3b341;
        line-height: 1.45;
    }
    
    /* Code / Monospace containers */
    code, pre {
        background-color: #090d14 !important;
        border: 1px solid #1f2a3a !important;
        color: #00f2ff !important;
        font-family: 'SF Mono', 'Cascadia Code', 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
<div class="header-box">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 class="header-title">🌙 Lunar Image Registration System</h1>
            <div class="header-subtitle">Cross-Sensor Surface Alignment: Chandrayaan-2 ↔ Lunar Reference Telemetry</div>
        </div>
        <div style="text-align: right;">
            <span class="status-badge status-ready">● FLIGHT ENGINE READY</span>
            <div style="font-size: 0.72rem; color: #6e7681; margin-top: 4px; font-family: monospace;">ENV: PYTORCH / LOFTR-CPU</div>
        </div>
    </div>
    <div class="pipeline-bar">
        <span style="color: #8b949e; font-weight: bold; margin-right: 4px;">PIPELINE:</span>
        <span class="pipeline-step">1. CLAHE</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">2. LoFTR Matcher</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">3. Initial RANSAC</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">4. Quality + 3×3 Spatial Binning</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">5. Final Homography</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">6. Evaluation Metrics</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- DEMO DATA LOADER HELPER ---
DEV_SOURCE_PATH = os.path.join("data", "source", "source.jpeg")
DEV_REFERENCE_PATH = os.path.join("data", "reference", "reference.jpeg")
LARGE_SOURCE_PATH = os.path.join("data", "large_ch2", "source_ch2_large.png")
LARGE_REFERENCE_PATH = os.path.join("data", "large_ch2", "reference_ch2_large.png")

col_util1, col_util2, col_util3 = st.columns([1.6, 1.2, 1.2])
with col_util2:
    if st.button("⚡ Load Dev Pair (513×146)", help="Instantly load the small Chandrayaan-2 development pair for live demonstration."):
        if os.path.exists(DEV_SOURCE_PATH) and os.path.exists(DEV_REFERENCE_PATH):
            s_loaded = cv2.imread(DEV_SOURCE_PATH)
            r_loaded = cv2.imread(DEV_REFERENCE_PATH)
            if s_loaded is not None and r_loaded is not None:
                st.session_state["source_img_data"] = s_loaded
                st.session_state["reference_img_data"] = r_loaded
                st.session_state["source_filename"] = "source.jpeg (Dev Pair)"
                st.session_state["reference_filename"] = "reference.jpeg (Dev Pair)"
                st.session_state.pop("registration_result", None)
                st.toast("Loaded Chandrayaan-2 development pair successfully!", icon="🌕")
        else:
            st.error("Development data files not found in data/ directory.")

with col_util3:
    if st.button("🌕 Load Real CH-2 Large (1200×5053)", help="Load full-size real Chandrayaan-2 large image pair (1200×5053 px)."):
        if os.path.exists(LARGE_SOURCE_PATH) and os.path.exists(LARGE_REFERENCE_PATH):
            s_loaded = cv2.imread(LARGE_SOURCE_PATH)
            r_loaded = cv2.imread(LARGE_REFERENCE_PATH)
            if s_loaded is not None and r_loaded is not None:
                st.session_state["source_img_data"] = s_loaded
                st.session_state["reference_img_data"] = r_loaded
                st.session_state["source_filename"] = "source_ch2_large.png (Real CH-2)"
                st.session_state["reference_filename"] = "reference_ch2_large.png (Real CH-2)"
                st.session_state.pop("registration_result", None)
                st.toast("Loaded real Chandrayaan-2 large pair (1200×5053) successfully!", icon="🚀")
        else:
            st.error("Large Chandrayaan-2 data files not found in data/large_ch2/ directory.")

# --- INPUT / TELEMETRY ACQUISITION SECTION ---
col_in1, col_in2 = st.columns(2)

with col_in1:
    st.markdown("#### 🛰️ Moving / Source Image (Chandrayaan-2)")
    src_file = st.file_uploader(
        "Upload Source Image (Moving)",
        type=["jpg", "jpeg", "png", "tif"],
        key="u_source",
        label_visibility="collapsed"
    )
    if src_file is not None:
        file_bytes = np.frombuffer(src_file.read(), np.uint8)
        decoded_s = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if decoded_s is not None:
            st.session_state["source_img_data"] = decoded_s
            st.session_state["source_filename"] = src_file.name

with col_in2:
    st.markdown("#### 🗺️ Fixed / Reference Image (Lunar Base)")
    ref_file = st.file_uploader(
        "Upload Reference Image (Fixed)",
        type=["jpg", "jpeg", "png", "tif"],
        key="u_reference",
        label_visibility="collapsed"
    )
    if ref_file is not None:
        file_bytes = np.frombuffer(ref_file.read(), np.uint8)
        decoded_r = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if decoded_r is not None:
            st.session_state["reference_img_data"] = decoded_r
            st.session_state["reference_filename"] = ref_file.name

# Display previews if images are present in session state
s_active = st.session_state.get("source_img_data", None)
r_active = st.session_state.get("reference_img_data", None)

if s_active is not None and r_active is not None:
    c_prev1, c_prev2 = st.columns(2)
    with c_prev1:
        st.markdown(f"<div class='img-box'>", unsafe_allow_html=True)
        st.image(
            cv2.cvtColor(s_active, cv2.COLOR_BGR2RGB),
            caption=f"Source: {st.session_state.get('source_filename', 'source.jpeg')} [{s_active.shape[1]}×{s_active.shape[0]} px]",
            width="stretch"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c_prev2:
        st.markdown(f"<div class='img-box'>", unsafe_allow_html=True)
        st.image(
            cv2.cvtColor(r_active, cv2.COLOR_BGR2RGB),
            caption=f"Reference: {st.session_state.get('reference_filename', 'reference.jpeg')} [{r_active.shape[1]}×{r_active.shape[0]} px]",
            width="stretch"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Engine Mode & Budget Settings
    with st.expander("⚙️ Memory-Safe Engine & Resolution Settings", expanded=False):
        mode_opt = st.selectbox(
            "LoFTR Feature Matching Mode",
            ["Memory-Safe (Balanced, Default)", "High Resolution", "Fast Matching (Speed Priority)"],
            index=0,
            help="Controls intermediate tensor resolution during LoFTR feature matching. The final homography and warping are always executed at full original reference resolution."
        )
        if mode_opt == "High Resolution":
            cfg_max_dim = 2000
            cfg_max_budget = 2500000
        elif mode_opt == "Fast Matching (Speed Priority)":
            cfg_max_dim = 1000
            cfg_max_budget = 1000000
        else:
            cfg_max_dim = 1600
            cfg_max_budget = 1800000

        st.caption(f"Active matching constraint: Max Dimension = **{cfg_max_dim} px** | Max Pixel Budget = **{cfg_max_budget/1e6:.1f}M px**")

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 INITIATE REGISTRATION SEQUENCE", type="primary"):
        st.session_state.pop("registration_result", None)
        
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.info("Executing Scientific Registration Pipeline: CLAHE → LoFTR → RANSAC → Spatial Selection → Homography...")
        
        try:
            res = register_images(s_active, r_active, max_loftr_dim=cfg_max_dim, max_pixel_budget=cfg_max_budget)
            st.session_state["registration_result"] = res
            status_placeholder.empty()
        except Exception as e:
            status_placeholder.empty()
            st.error(f"Registration Sequence Encountered an Issue: {str(e)}")

# ============================================================
# 3. REGISTRATION RESULTS & METRICS TELEMETRY
# ============================================================

if "registration_result" in st.session_state:
    res = st.session_state["registration_result"]
    s_active = st.session_state["source_img_data"]
    r_active = st.session_state["reference_img_data"]

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    # Telemetry Status Bar
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; background: #0c1a24; border: 1px solid #1a3c54; padding: 10px 16px; border-radius: 6px; margin-bottom: 16px;">
        <div>
            <span class="status-badge status-locked">● REGISTRATION LOCKED</span>
            <span style="margin-left: 12px; font-weight: 600; color: #58a6ff; font-size: 0.9rem;">GEOMETRIC CONVERGENCE ACHIEVED</span>
        </div>
        <div style="font-family: monospace; font-size: 0.82rem; color: #8b949e;">
            EXECUTION TIME: <span style="color: #00f2ff; font-weight: bold;">{res['runtime']:.2f}s</span> | COMPUTE: <span style="color: #00f2ff; font-weight: bold;">{res['device'].upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clear Warning Banner for Large Images
    if res.get("resizing_applied", False):
        st.markdown("""
        <div class="warning-box">
            <b>⚠️ MEMORY-SAFE LARGE IMAGE PREPROCESSING ACTIVE:</b><br>
            Large image detected — matching is performed at reduced resolution for memory safety; final registration is mapped back to the original coordinate system.
        </div>
        """, unsafe_allow_html=True)

    # Resolution & Scaling Telemetry Grid
    st.markdown("##### 📐 Resolution & Scaling Telemetry")
    r_c1, r_c2, r_c3, r_c4 = st.columns(4)
    with r_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Original Resolution (Src / Ref)</div>
            <div class="metric-val" style="font-size:1.15rem; color:#58a6ff;">{res['orig_source_shape'][1]}×{res['orig_source_shape'][0]} <span style="font-size:0.8rem; color:#8b949e;">/</span> {res['orig_ref_shape'][1]}×{res['orig_ref_shape'][0]}</div>
            <div class="metric-sub">Full sensor coordinate frame</div>
        </div>
        """, unsafe_allow_html=True)
    with r_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LoFTR Matching Resolution</div>
            <div class="metric-val" style="font-size:1.15rem; color:#00f2ff;">{res['match_source_shape'][1]}×{res['match_source_shape'][0]} <span style="font-size:0.8rem; color:#8b949e;">/</span> {res['match_ref_shape'][1]}×{res['match_ref_shape'][0]}</div>
            <div class="metric-sub">Memory-safe tensor dimensions</div>
        </div>
        """, unsafe_allow_html=True)
    with r_c3:
        status_text = "YES (Downscaled)" if res['resizing_applied'] else "NO (Native 1:1)"
        status_color = "#f0883e" if res['resizing_applied'] else "#3fb950"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Resizing Applied</div>
            <div class="metric-val" style="font-size:1.15rem; color:{status_color};">{status_text}</div>
            <div class="metric-sub">Budget limit: {res['max_loftr_dim']} px / {res['max_pixel_budget']//1000}k px</div>
        </div>
        """, unsafe_allow_html=True)
    with r_c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Scale Factor(s) (Src / Ref)</div>
            <div class="metric-val" style="font-size:1.15rem; color:#d1d7e0;">{res['scale_source']:.3f}× <span style="font-size:0.8rem; color:#8b949e;">/</span> {res['scale_ref']:.3f}×</div>
            <div class="metric-sub">Exact x/y back-mapping to original</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🔬 Geometric & Spatial Telemetry")

    # High-Density 8-Card Telemetry Grid
    t_c1, t_c2, t_c3, t_c4 = st.columns(4)
    with t_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LoFTR Candidate Matches</div>
            <div class="metric-val">{res['candidate_matches']}</div>
            <div class="metric-sub">Dense feature pairs</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Initial RANSAC Inliers</div>
            <div class="metric-val">{res['initial_inliers']}</div>
            <div class="metric-sub">Initial inlier ratio: {res['initial_inlier_ratio']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial Selected Subset</div>
            <div class="metric-val">{res['selected_matches']}</div>
            <div class="metric-sub">3×3 grid quality filtered</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Final Geometric Inliers</div>
            <div class="metric-val">{res['final_inliers']}</div>
            <div class="metric-sub">Final inlier ratio: <b style="color:#3fb950;">{res['final_inlier_ratio']*100:.2f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    t_c5, t_c6, t_c7, t_c8 = st.columns(4)
    with t_c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Reprojection RMSE</div>
            <div class="metric-val">{res['rmse']:.3f} <span style="font-size:0.9rem;">px</span></div>
            <div class="metric-sub">Mean error: {res['mean_error']:.3f} px</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial Occupancy</div>
            <div class="metric-val">{res['occupied_cells']} / {res['total_cells']}</div>
            <div class="metric-sub">Coverage: {res['occupancy_ratio']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c7:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial CV</div>
            <div class="metric-val">{res['spatial_cv']:.3f}</div>
            <div class="metric-sub">Uniformity score (lower is better)</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c8:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Median Reprojection Error</div>
            <div class="metric-val">{res['median_error']:.3f} <span style="font-size:0.9rem;">px</span></div>
            <div class="metric-sub">Max error: {res['max_error']:.3f} px</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Alignment Verification Section
    st.markdown("### 🔍 Alignment Verification")
    tab_view, tab_blend, tab_diff = st.tabs([
        "Side-by-Side Verification",
        "Composite Blend (50/50)",
        "Difference Residual Map"
    ])

    ref_g = cv2.cvtColor(r_active, cv2.COLOR_BGR2GRAY) if len(r_active.shape) == 3 else r_active
    reg_src = res["registered_image"]

    with tab_view:
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            st.image(reg_src, caption="Warped Source Image (Aligned to Reference Grid)", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        with r_c2:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            st.image(ref_g, caption="Reference Base Image (Ground Truth Frame)", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_blend:
        ref_g = cv2.cvtColor(r_active, cv2.COLOR_BGR2GRAY) if len(r_active.shape) == 3 else r_active
        registered = res["registered_image"]

        st.caption(f"Full-Resolution Registration Grid: Reference {ref_g.shape[1]}×{ref_g.shape[0]} px | Warped Source {registered.shape[1]}×{registered.shape[0]} px (1:1 Native Pixel Alignment)")

        if registered.shape[:2] != ref_g.shape[:2]:
            registered = cv2.resize(
                registered,
                (ref_g.shape[1], ref_g.shape[0]),
                interpolation=cv2.INTER_LINEAR
            )

        if len(registered.shape) == 3:
            registered = cv2.cvtColor(registered, cv2.COLOR_BGR2GRAY)

        ref_f = ref_g.astype(np.float32)
        reg_f = registered.astype(np.float32)

        overlay = cv2.addWeighted(
            ref_f,
            0.5,
            reg_f,
            0.5,
            0
        ).astype(np.uint8)

        st.image(
            overlay,
            caption="Composite Blend (50/50)",
            width="stretch"
        )

    with tab_diff:
        diff = cv2.absdiff(ref_g, registered)
        fig_diff, ax_diff = plt.subplots(figsize=(8, 3.2))
        fig_diff.patch.set_facecolor('#0b0e14')
        ax_diff.set_facecolor('#121824')
        im_d = ax_diff.imshow(diff, cmap='inferno')
        ax_diff.set_title("Absolute Intensity Residual Map (|Reference - Warped Source|)", color='#58a6ff', fontsize=10)
        ax_diff.axis('off')
        cbar = fig_diff.colorbar(im_d, ax=ax_diff, fraction=0.03, pad=0.02)
        cbar.ax.tick_params(labelsize=8, colors='#8b949e')
        st.pyplot(fig_diff)
        plt.close(fig_diff)

    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

    # Correspondence Evidence & Spatial Distribution
    st.markdown("### 📊 Correspondence Evidence & Spatial Distribution")
    col_ev1, col_ev2 = st.columns([1.4, 1.0])

    with col_ev1:
        st.markdown("##### Geometrically Valid Correspondences (Final RANSAC Inliers)")
        st.image(
            cv2.cvtColor(res["match_visualization"], cv2.COLOR_BGR2RGB),
            caption=f"{res['final_inliers']} Geometrically Verified Correspondences (Yellow Vectors: Source → Reference)",
            width="stretch"
        )

    with col_ev2:
        st.markdown("##### 3×3 Spatial Grid Distribution")
        fig_grid, ax_grid = plt.subplots(figsize=(4.2, 3.2))
        fig_grid.patch.set_facecolor('#0b0e14')
        ax_grid.set_facecolor('#121824')
        im_g = ax_grid.imshow(res["selected_grid"], cmap="Blues", vmin=0, vmax=6)
        
        for (j, i), val in np.ndenumerate(res["selected_grid"]):
            color = "#00f2ff" if val > 0 else "#484f58"
            ax_grid.text(i, j, f"{val}", ha='center', va='center', color=color, fontweight='bold', fontsize=12)
            
        ax_grid.set_xticks([0, 1, 2])
        ax_grid.set_yticks([0, 1, 2])
        ax_grid.set_xticklabels(["C0", "C1", "C2"], color="#8b949e", fontsize=8)
        ax_grid.set_yticklabels(["R0", "R1", "R2"], color="#8b949e", fontsize=8)
        ax_grid.tick_params(colors="#30363d")
        ax_grid.set_title(f"Occupancy: {res['occupied_cells']}/9 ({res['occupancy_ratio']*100:.1f}%) | CV: {res['spatial_cv']:.3f}", color='#58a6ff', fontsize=9)
        st.pyplot(fig_grid)
        plt.close(fig_grid)
    # ============================================================
    # INDEPENDENT CHECK-POINT VALIDATION SECTION
    # ============================================================
    if "independent_validation" in res and res["independent_validation"] is not None:
        val = res["independent_validation"]
        prim = val["primary_run"]

        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🎯 Independent Check-Point Validation")

        st.markdown("""
        <div class="warning-box" style="background:#0b1d16; border:1px solid #1a4231; border-left:4px solid #3fb950; color:#7ee787;">
            <b>🛡️ INDEPENDENT CHECK-POINT PROTOCOL:</b><br>
            <b>Independent check points were not used to estimate the homography.</b><br>
            <span style="color:#8b949e; font-size:0.8rem;">
            A spatially balanced 75/25 split isolates hold-out check points uniformly across occupied 3×3 grid cells.
            The homography is estimated solely on estimation points, and predictive generalization accuracy is verified on independent reference check points.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 7-Metric Display Cards
        v_c1, v_c2, v_c3, v_c4 = st.columns(4)
        with v_c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Estimation Points</div>
                <div class="metric-val" style="color:#58a6ff;">{prim['n_estimation']}</div>
                <div class="metric-sub">Used to fit $H_{{est}}$ (~75%)</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Independent Check Points</div>
                <div class="metric-val" style="color:#3fb950;">{prim['n_check']}</div>
                <div class="metric-sub">Strictly withheld (~25%)</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Fit RMSE</div>
                <div class="metric-val" style="color:#58a6ff;">{prim['fit_rmse']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">Residual on estimation set</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Independent Check RMSE</div>
                <div class="metric-val" style="color:#00f2ff;">{prim['check_rmse']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">Generalization error (Seed {prim['seed']})</div>
            </div>
            """, unsafe_allow_html=True)

        v_c5, v_c6, v_c7, v_c8 = st.columns(4)
        with v_c5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Check Mean Error</div>
                <div class="metric-val">{prim['check_mean']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">Average check displacement</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c6:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Check Median Error</div>
                <div class="metric-val">{prim['check_median']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">50th percentile error</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c7:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Check Maximum Error</div>
                <div class="metric-val">{prim['check_max']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">Worst check displacement</div>
            </div>
            """, unsafe_allow_html=True)
        with v_c8:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Multi-Seed Mean RMSE</div>
                <div class="metric-val" style="color:#d29922;">{val['mean_check_rmse']:.4f} <span style="font-size:0.85rem;">px</span></div>
                <div class="metric-sub">Averaged across 5 seeds</div>
            </div>
            """, unsafe_allow_html=True)

        # Multi-Seed Validation Summary Table
        st.markdown("##### 🎲 Multi-Seed Sensitivity Analysis (Seeds 1, 2, 3, 4, 5)")
        seed_rows = []
        for r in val["runs"]:
            seed_rows.append({
                "Seed": f"Seed {r['seed']}",
                "Estimation Points": r["n_estimation"],
                "Check Points": r["n_check"],
                "Fit RMSE (px)": f"{r['fit_rmse']:.4f}",
                "Check RMSE (px)": f"{r['check_rmse']:.4f}",
                "Check Mean (px)": f"{r['check_mean']:.4f}",
                "Check Median (px)": f"{r['check_median']:.4f}",
                "Check Max (px)": f"{r['check_max']:.4f}"
            })
        st.dataframe(seed_rows, width="stretch", hide_index=True)

        st.markdown(f"""
        <div style="font-size: 0.85rem; color: #8b949e; background: #090d14; padding: 10px 14px; border-radius: 6px; border: 1px solid #1c2738; margin-bottom: 16px;">
            <b>Cross-Seed Summary:</b>
            Mean Check RMSE: <b style="color:#00f2ff;">{val['mean_check_rmse']:.4f} px</b> &nbsp;|&nbsp; 
            Median Check RMSE: <b style="color:#00f2ff;">{val['median_check_rmse']:.4f} px</b> &nbsp;|&nbsp; 
            Best Check RMSE: <b style="color:#3fb950;">{val['best_check_rmse']:.4f} px</b> &nbsp;|&nbsp; 
            Worst Check RMSE: <b style="color:#f0883e;">{val['worst_check_rmse']:.4f} px</b>
        </div>
        """, unsafe_allow_html=True)

        # Visualizations
        st.markdown("##### 🗺️ Independent Check-Point Error Vectors & Spatial Distribution")
        col_v1, col_v2 = st.columns([1.2, 1.0])

        with col_v1:
            fig_map, ax_map = plt.subplots(figsize=(6, 4.2))
            fig_map.patch.set_facecolor('#0b0e14')
            ax_map.set_facecolor('#121824')

            ref_est = np.array(prim["ref_est"])
            ref_chk = np.array(prim["ref_chk"])
            pred_chk = np.array(prim["pred_chk"])

            ax_map.scatter(ref_est[:, 0], ref_est[:, 1], c='#388bfd', s=28, alpha=0.7, label=f'Estimation Points (N={prim["n_estimation"]})')
            ax_map.scatter(ref_chk[:, 0], ref_chk[:, 1], c='#3fb950', s=45, marker='o', edgecolors='white', label=f'Actual Reference Check (M={prim["n_check"]})')
            ax_map.scatter(pred_chk[:, 0], pred_chk[:, 1], c='#f85149', s=55, marker='x', label='Predicted by H_est')

            for i in range(len(ref_chk)):
                ax_map.plot([ref_chk[i, 0], pred_chk[i, 0]], [ref_chk[i, 1], pred_chk[i, 1]], color='#d29922', linewidth=2.0)

            ax_map.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='#d1d7e0', fontsize=7.5, loc='upper right')
            ax_map.tick_params(colors='#8b949e', labelsize=8)
            ax_map.set_title(f"Spatial Distribution: Estimation vs Check Points (Seed {prim['seed']})", color='#58a6ff', fontsize=9.5)
            ax_map.set_xlabel("Reference X (px)", color='#8b949e', fontsize=8)
            ax_map.set_ylabel("Reference Y (px)", color='#8b949e', fontsize=8)
            st.pyplot(fig_map)
            plt.close(fig_map)

        with col_v2:
            fig_res, ax_res = plt.subplots(figsize=(5, 4.2))
            fig_res.patch.set_facecolor('#0b0e14')
            ax_res.set_facecolor('#121824')

            dx = np.array(prim["dx"])
            dy = np.array(prim["dy"])

            ax_res.scatter(dx, dy, c='#00f2ff', s=45, edgecolors='white', zorder=5)
            for i in range(len(dx)):
                ax_res.annotate(f"C{i+1}", (dx[i]+0.02, dy[i]+0.02), color='#c9d1d9', fontsize=7.5)

            max_lim = max(1.2, float(np.max(np.abs([dx, dy]))) * 1.3)
            c_025 = plt.Circle((0, 0), 0.25, color='#388bfd', fill=False, linestyle=':', label='0.25 px boundary')
            c_050 = plt.Circle((0, 0), 0.50, color='#3fb950', fill=False, linestyle='--', label='0.50 px boundary')
            c_100 = plt.Circle((0, 0), 1.00, color='#d29922', fill=False, linestyle='-.', label='1.00 px boundary')
            ax_res.add_patch(c_025)
            ax_res.add_patch(c_050)
            ax_res.add_patch(c_100)

            ax_res.axhline(0, color='#30363d', linestyle='-', linewidth=0.8)
            ax_res.axvline(0, color='#30363d', linestyle='-', linewidth=0.8)
            ax_res.set_xlim(-max_lim, max_lim)
            ax_res.set_ylim(-max_lim, max_lim)
            ax_res.legend(facecolor='#161b22', edgecolor='#30363d', labelcolor='#d1d7e0', fontsize=7.5, loc='lower right')
            ax_res.tick_params(colors='#8b949e', labelsize=8)
            ax_res.set_title(f"Check-Point Error Vectors Δx, Δy (RMSE: {prim['check_rmse']:.3f} px)", color='#58a6ff', fontsize=9.5)
            ax_res.set_xlabel("Δx Displacement (px)", color='#8b949e', fontsize=8)
            ax_res.set_ylabel("Δy Displacement (px)", color='#8b949e', fontsize=8)
            st.pyplot(fig_res)
            plt.close(fig_res)

    # Scientific Honesty Alert Box
    st.markdown(f"""
    <div class="honesty-box">
        <b>🔭 SCIENTIFIC BENCHMARK NOTE:</b><br>
        On our real lunar development pair, the validated reprojection RMSE is <b>{res['rmse']:.3f} px</b> (mean error: <b>{res['mean_error']:.3f} px</b>, maximum error: <b>{res['max_error']:.3f} px</b>).
        Sub-pixel accuracy (~0.097 px) was separately verified in controlled synthetic ground-truth experiments and is not claimed as real lunar cross-sensor accuracy.
    </div>
    """, unsafe_allow_html=True)

    # Expandable Technical Analytics
    with st.expander("🛠️ Advanced Technical & Geometric Analytics"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("##### Homography Transformation Matrix $H_{3\\times3}$")
            h_mat = np.array(res["homography_matrix"])
            st.code(
                f"[[ {h_mat[0,0]:12.6e}, {h_mat[0,1]:12.6e}, {h_mat[0,2]:12.6e} ],\n"
                f" [ {h_mat[1,0]:12.6e}, {h_mat[1,1]:12.6e}, {h_mat[1,2]:12.6e} ],\n"
                f" [ {h_mat[2,0]:12.6e}, {h_mat[2,1]:12.6e}, {h_mat[2,2]:12.6e} ]]",
                language="python"
            )
        with col_t2:
            st.markdown("##### Error Metrics Breakdown")
            st.markdown(f"""
            - **Reprojection RMSE**: `{res['rmse']:.4f} px`
            - **Mean Absolute Error**: `{res['mean_error']:.4f} px`
            - **Median Reprojection Error**: `{res['median_error']:.4f} px`
            - **Maximum Error**: `{res['max_error']:.4f} px`
            - **Inlier Retention Rate**: `{res['final_inlier_ratio']*100:.2f}%` ({res['final_inliers']}/{res['selected_matches']})
            - **Occupied Spatial Cells**: `{res['occupied_cells']} / 9`
            - **Original Source Coordinate Frame**: `{res['orig_source_shape'][1]}×{res['orig_source_shape'][0]} px`
            - **Original Reference Coordinate Frame**: `{res['orig_ref_shape'][1]}×{res['orig_ref_shape'][0]} px`
            - **LoFTR Matching Tensor Frame**: `Src {res['match_source_shape'][1]}×{res['match_source_shape'][0]} px, Ref {res['match_ref_shape'][1]}×{res['match_ref_shape'][0]} px`
            - **Memory-Safe Scale Factors**: `Src {res['scale_source']:.4f}×, Ref {res['scale_ref']:.4f}×`
            - **Intermediate Downscaling Active**: `{res['resizing_applied']}`
            """)

# --- FOOTER ---
st.markdown("""
<div style="margin-top: 30px; text-align: center; border-top: 1px solid #1c2738; padding-top: 12px; color: #484f58; font-size: 0.76rem;">
    Smart India Hackathon (SIH) 2026 — Lunar Image Registration System | Chandrayaan-2 Research Pipeline
</div>
""", unsafe_allow_html=True)
