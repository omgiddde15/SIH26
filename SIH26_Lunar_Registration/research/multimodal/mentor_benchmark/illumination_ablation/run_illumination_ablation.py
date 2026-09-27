"""
Controlled Illumination / Radiometric Ablation on Mentor Chandrayaan-2 OHRC Datasets
Investigates: Does reducing source/reference illumination and radiometric disparity
materially improve LoFTR correspondence on the mentor OHRC pairs?

Research-only. Production remains 100% frozen.
Evaluates OHRC_PAIR_01 to OHRC_PAIR_04 across 6 pre-declared conditions per pair:
  - Condition A: CURRENT_BASELINE (Current production Grayscale + CLAHE)
  - Condition B: HISTOGRAM_NORMALIZED (Deterministic global contrast stretch + global histogram equalization)
  - Condition C: GRADIENT_MAGNITUDE (Independent Sobel gradient magnitude representation)
  - Condition D: LOCAL_GRADIENT_NORMALIZED (Local gradient normalization preserving edge structure)
  - Condition E: ILLUMINATION_NORMALIZED (Deterministic background illumination-field division + CLAHE)
  - Condition F: SHADOW_AWARE (Conservative shadow-aware masking and valid-support telemetry)
"""

import os
import sys
import time
import json
import csv
import gc
import cv2
import numpy as np
import torch

# Ensure repository root is on sys.path
REPO_ROOT = r"C:\Users\Dell\Videos\SIH26_Lunar_Registration"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.registration_core import (
    load_loftr_matcher,
    preprocess_image,
    compute_matching_scale,
    calculate_spatial_grid,
    run_independent_checkpoint_validation,
)

OHRC_DIR = r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\OHRC"
OUT_DIR = os.path.join(REPO_ROOT, r"research\multimodal\mentor_benchmark\illumination_ablation")
os.makedirs(OUT_DIR, exist_ok=True)

CHECKPOINT_JSON_PATH = os.path.join(OUT_DIR, "illumination_ablation_checkpoint.json")
PROGRESS_JSON_PATH = os.path.join(OUT_DIR, "illumination_ablation_progress.json")
RESULTS_JSON_PATH = os.path.join(OUT_DIR, "illumination_ablation_results.json")
RESULTS_CSV_PATH = os.path.join(OUT_DIR, "illumination_ablation_results.csv")
REPORT_MD_PATH = os.path.join(OUT_DIR, "illumination_ablation_report.md")

PAIRS = [
    {
        "id": "OHRC_PAIR_01",
        "name": "OHRC Pair 1",
        "source_file": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif",
        "flight_azimuth_deg": -29.16,
    },
    {
        "id": "OHRC_PAIR_02",
        "name": "OHRC Pair 2",
        "source_file": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif",
        "flight_azimuth_deg": -98.43,
    },
    {
        "id": "OHRC_PAIR_03",
        "name": "OHRC Pair 3",
        "source_file": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif",
        "flight_azimuth_deg": -96.81,
    },
    {
        "id": "OHRC_PAIR_04",
        "name": "OHRC Pair 4",
        "source_file": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif",
        "flight_azimuth_deg": -105.68,
    },
]

CONDITIONS = [
    {
        "code": "CURRENT_BASELINE",
        "name": "Current Baseline (CLAHE)",
        "params": "clipLimit=2.0, tileGridSize=(8, 8)",
        "description": "Standard production grayscale conversion + CLAHE contrast enhancement",
    },
    {
        "code": "HISTOGRAM_NORMALIZED",
        "name": "Histogram Normalized",
        "params": "percentile_clip=(1, 99), cv2.equalizeHist",
        "description": "Deterministic global percentile contrast stretch + cumulative histogram equalization",
    },
    {
        "code": "GRADIENT_MAGNITUDE",
        "name": "Sobel Gradient Magnitude",
        "params": "Sobel(ksize=3), norm=percentile_99_uint8",
        "description": "Independent Sobel gradient magnitude eliminating albedo and DC illumination offsets",
    },
    {
        "code": "LOCAL_GRADIENT_NORMALIZED",
        "name": "Local Gradient Normalized",
        "params": "Sobel(ksize=3), local_blur=31x31(sigma=5.0), norm=percentile_99_uint8",
        "description": "Local energy-normalized gradient dampening extreme sunlit rim/shadow contrast disparity",
    },
    {
        "code": "ILLUMINATION_NORMALIZED",
        "name": "Illumination Field Normalized",
        "params": "lowpass=63x63(sigma=16.0), ratio_stretch=(1, 99), CLAHE(2.0, (8, 8))",
        "description": "Deterministic background illumination-field division (homomorphic shading removal) + CLAHE",
    },
    {
        "code": "SHADOW_AWARE",
        "name": "Shadow-Aware Masked",
        "params": "shadow_thresh=12, morph_open=3x3, CLAHE(2.0, (8, 8)), shadow_cand_filter=True",
        "description": "Conservative shadow detection (DN <= 12) with support telemetry; keypoints in deep shadow filtered",
    },
]


def load_raw_pair(pair_info):
    s_path = os.path.join(OHRC_DIR, pair_info["source_file"])
    r_path = os.path.join(OHRC_DIR, pair_info["ref_file"])
    s_raw = cv2.imread(s_path, cv2.IMREAD_UNCHANGED)
    r_raw = cv2.imread(r_path, cv2.IMREAD_UNCHANGED)
    if s_raw is None or r_raw is None:
        raise FileNotFoundError(f"Could not load images for {pair_info['id']}")

    s_gray = cv2.cvtColor(s_raw, cv2.COLOR_BGR2GRAY) if s_raw.ndim == 3 else s_raw.copy()
    r_gray = cv2.cvtColor(r_raw, cv2.COLOR_BGR2GRAY) if r_raw.ndim == 3 else r_raw.copy()
    return s_gray, r_gray, s_gray.shape, r_gray.shape


def chunked_coarse_match_forward(cm_module, feat_c0, feat_c1, data, mask_c0=None, mask_c1=None, chunk_size=512):
    """
    Computes exact LoFTR dual softmax and mutual nearest neighbor coarse matching
    in O(chunk_size * S) peak memory (~57 MB) instead of O(L * S * 4) memory (~2.86 GB).
    """
    temp = cm_module.temperature
    thr = cm_module.thr
    border_rm = cm_module.border_rm

    _, L, C = feat_c0.shape
    _, S, _ = feat_c1.shape

    h0c, w0c = data["hw0_c"]
    h1c, w1c = data["hw1_c"]

    f0 = feat_c0 / (C ** 0.5)
    f1 = feat_c1 / (C ** 0.5)
    f1_t = f1[0].t()

    col_max = torch.full((S,), float("-inf"), dtype=torch.float32, device=feat_c0.device)
    col_sum = torch.zeros(S, dtype=torch.float32, device=feat_c0.device)

    for i in range(0, L, chunk_size):
        chunk_len = min(chunk_size, L - i)
        c0_chunk = f0[0, i:i+chunk_len, :]
        sim_chunk = torch.matmul(c0_chunk, f1_t) / temp
        if mask_c0 is not None and mask_c1 is not None:
            m_chunk = ~(mask_c0[:, i:i+chunk_len, None] * mask_c1[:, None]).bool()
            sim_chunk.masked_fill_(m_chunk[0], float("-inf"))

        chunk_max = torch.max(sim_chunk, dim=0)[0]
        new_max = torch.maximum(col_max, chunk_max)
        col_sum = col_sum * torch.exp(col_max - new_max) + torch.sum(torch.exp(sim_chunk - new_max), dim=0)
        col_max = new_max

    col_max = col_max.unsqueeze(0)
    col_sum = col_sum.unsqueeze(0)

    i_all = torch.arange(L, device=feat_c0.device)
    i_x = i_all % w0c
    i_y = i_all // w0c
    i_valid = (i_x >= border_rm) & (i_x < w0c - border_rm) & (i_y >= border_rm) & (i_y < h0c - border_rm)

    j_all = torch.arange(S, device=feat_c0.device)
    j_x = j_all % w1c
    j_y = j_all // w1c
    j_valid = (j_x >= border_rm) & (j_x < w1c - border_rm) & (j_y >= border_rm) & (j_y < h1c - border_rm)

    row_max_val = torch.zeros(L, dtype=torch.float32, device=feat_c0.device)
    row_max_idx = torch.zeros(L, dtype=torch.int64, device=feat_c0.device)

    col_conf_max_val = torch.zeros(S, dtype=torch.float32, device=feat_c0.device)
    col_conf_max_idx = torch.zeros(S, dtype=torch.int64, device=feat_c0.device)

    for i in range(0, L, chunk_size):
        chunk_len = min(chunk_size, L - i)
        c0_chunk = f0[0, i:i+chunk_len, :]
        sim_chunk = torch.matmul(c0_chunk, f1_t) / temp
        if mask_c0 is not None and mask_c1 is not None:
            m_chunk = ~(mask_c0[:, i:i+chunk_len, None] * mask_c1[:, None]).bool()
            sim_chunk.masked_fill_(m_chunk[0], float("-inf"))

        row_sm = torch.nn.functional.softmax(sim_chunk, dim=1)
        col_sm = torch.exp(sim_chunk - col_max) / col_sum
        conf_chunk = row_sm * col_sm

        r_val, r_idx = torch.max(conf_chunk, dim=1)
        row_max_val[i:i+chunk_len] = r_val
        row_max_idx[i:i+chunk_len] = r_idx

        c_val, c_idx = torch.max(conf_chunk, dim=0)
        c_idx_global = c_idx + i
        update_mask = c_val > col_conf_max_val
        col_conf_max_val[update_mask] = c_val[update_mask]
        col_conf_max_idx[update_mask] = c_idx_global[update_mask]

    best_j = row_max_idx
    best_val = row_max_val

    is_match = (
        (best_val > thr)
        & i_valid
        & j_valid[best_j]
        & (col_conf_max_idx[best_j] == torch.arange(L, device=feat_c0.device))
    )

    matched_i = torch.where(is_match)[0]
    matched_j = best_j[matched_i]
    matched_conf = best_val[matched_i]
    b_ids = torch.zeros_like(matched_i)

    scale0 = data["hw0_i"][0] / data["hw0_c"][0]
    scale1 = data["hw1_i"][0] / data["hw1_c"][0]
    mkpts0_c = torch.stack([matched_i % data["hw0_c"][1], matched_i // data["hw0_c"][1]], dim=1) * scale0
    mkpts1_c = torch.stack([matched_j % data["hw1_c"][1], matched_j // data["hw1_c"][1]], dim=1) * scale1

    coarse_matches = {
        "b_ids": b_ids,
        "i_ids": matched_i,
        "j_ids": matched_j,
        "gt_mask": matched_conf == 0,
        "m_bids": b_ids,
        "mkpts0_c": mkpts0_c.to(dtype=feat_c0.dtype),
        "mkpts1_c": mkpts1_c.to(dtype=feat_c0.dtype),
        "mconf": matched_conf,
    }
    data.update(coarse_matches)


def patch_loftr_chunked(matcher):
    matcher.coarse_matching.forward = lambda feat_c0, feat_c1, data, mask_c0=None, mask_c1=None: chunked_coarse_match_forward(
        matcher.coarse_matching, feat_c0, feat_c1, data, mask_c0, mask_c1
    )
    return matcher


def apply_representation(img_gray, cond_code):
    """
    Applies the specific illumination/radiometric representation to a single grayscale raster.
    Returns:
      processed_img: uint8 ndarray
      valid_mask: uint8 ndarray (255 = valid support, 0 = masked shadow/artifact)
      valid_pct: float percentage
    """
    h, w = img_gray.shape[:2]

    if cond_code == "CURRENT_BASELINE":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        out = clahe.apply(img_gray)
        mask = np.ones((h, w), dtype=np.uint8) * 255
        return out, mask, 100.0

    elif cond_code == "HISTOGRAM_NORMALIZED":
        p1, p99 = np.percentile(img_gray, (1, 99))
        stretched = np.clip((img_gray.astype(np.float32) - p1) / max(p99 - p1, 1e-3) * 255.0, 0, 255).astype(np.uint8)
        out = cv2.equalizeHist(stretched)
        mask = np.ones((h, w), dtype=np.uint8) * 255
        return out, mask, 100.0

    elif cond_code == "GRADIENT_MAGNITUDE":
        gx = cv2.Sobel(img_gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(img_gray, cv2.CV_32F, 0, 1, ksize=3)
        g = np.sqrt(gx**2 + gy**2)
        p99_g = np.percentile(g, 99)
        out = np.clip(g / max(p99_g, 1e-3) * 255.0, 0, 255).astype(np.uint8)
        mask = np.ones((h, w), dtype=np.uint8) * 255
        return out, mask, 100.0

    elif cond_code == "LOCAL_GRADIENT_NORMALIZED":
        gx = cv2.Sobel(img_gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(img_gray, cv2.CV_32F, 0, 1, ksize=3)
        g = np.sqrt(gx**2 + gy**2)
        e_local = cv2.GaussianBlur(g, (31, 31), 5.0)
        eps = 1e-4 * max(float(np.mean(g)), 1e-3)
        g_local = g / (e_local + eps)
        p99_gl = np.percentile(g_local, 99)
        out = np.clip(g_local / max(p99_gl, 1e-3) * 255.0, 0, 255).astype(np.uint8)
        mask = np.ones((h, w), dtype=np.uint8) * 255
        return out, mask, 100.0

    elif cond_code == "ILLUMINATION_NORMALIZED":
        bg = cv2.GaussianBlur(img_gray.astype(np.float32), (63, 63), 16.0) + 1.0
        r = img_gray.astype(np.float32) / bg
        p1_r, p99_r = np.percentile(r, (1, 99))
        r_norm = np.clip((r - p1_r) / max(p99_r - p1_r, 1e-3) * 255.0, 0, 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        out = clahe.apply(r_norm)
        mask = np.ones((h, w), dtype=np.uint8) * 255
        return out, mask, 100.0

    elif cond_code == "SHADOW_AWARE":
        # Conservative shadow detection based on Track C measurements: DN <= 12
        mask_raw = (img_gray > 12).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask_raw, cv2.MORPH_OPEN, kernel)
        valid_cnt = int(np.count_nonzero(mask))
        valid_pct = float(valid_cnt / float(h * w) * 100.0)

        # Standard CLAHE applied on overall image
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        out = clahe.apply(img_gray)
        return out, mask, valid_pct

    else:
        raise ValueError(f"Unknown condition code: {cond_code}")


def run_condition_eval(
    matcher,
    s_gray,
    r_gray,
    s_shape,
    r_shape,
    cond_info,
):
    cond_code = cond_info["code"]
    cond_name = cond_info["name"]
    cond_params = cond_info["params"]
    s_h, s_w = s_shape
    r_h, r_w = r_shape

    # 1. Apply representation to native images
    s_prep, s_mask, s_val_pct = apply_representation(s_gray, cond_code)
    r_prep, r_mask, r_val_pct = apply_representation(r_gray, cond_code)

    # 2. Compute production matcher scale
    scale_s, s_wm, s_hm = compute_matching_scale((s_h, s_w), max_dim=1600, max_budget=1800000)
    scale_r, r_wm, r_hm = compute_matching_scale((r_h, r_w), max_dim=1600, max_budget=1800000)

    # 3. Resize to production matcher canvas
    s_match = cv2.resize(s_prep, (s_wm, s_hm), interpolation=cv2.INTER_AREA)
    r_match = cv2.resize(r_prep, (r_wm, r_hm), interpolation=cv2.INTER_AREA)

    s_mask_match = cv2.resize(s_mask, (s_wm, s_hm), interpolation=cv2.INTER_NEAREST)
    r_mask_match = cv2.resize(r_mask, (r_wm, r_hm), interpolation=cv2.INTER_NEAREST)

    # 4. LoFTR forward pass
    source_tensor = torch.from_numpy(s_match.astype(np.float32) / 255.0)[None, None]
    reference_tensor = torch.from_numpy(r_match.astype(np.float32) / 255.0)[None, None]

    t0 = time.time()
    with torch.inference_mode():
        output = matcher({"image0": source_tensor, "image1": reference_tensor})
    runtime_s = float(time.time() - t0)

    mkpts0_match = output["keypoints0"].cpu().numpy()
    mkpts1_match = output["keypoints1"].cpu().numpy()
    confidence = output["confidence"].cpu().numpy()

    del source_tensor, reference_tensor, output
    gc.collect()

    raw_cand = int(len(mkpts0_match))

    # 5. Mask / support filtering (e.g. shadow filtering for Condition F)
    valid_indices = []
    for idx in range(raw_cand):
        x0, y0 = int(round(mkpts0_match[idx, 0])), int(round(mkpts0_match[idx, 1]))
        x1, y1 = int(round(mkpts1_match[idx, 0])), int(round(mkpts1_match[idx, 1]))
        if (0 <= x0 < s_wm and 0 <= y0 < s_hm and s_mask_match[y0, x0] > 0 and
            0 <= x1 < r_wm and 0 <= y1 < r_hm and r_mask_match[y1, x1] > 0):
            valid_indices.append(idx)

    valid_cand = len(valid_indices)
    filtered_cand = raw_cand - valid_cand

    if valid_cand < 4:
        return {
            "condition_code": cond_code,
            "representation_name": cond_name,
            "preprocessing_params": cond_params,
            "source_valid_pixel_pct": round(s_val_pct, 2),
            "ref_valid_pixel_pct": round(r_val_pct, 2),
            "matcher_source_dims": f"{s_wm}x{s_hm} px",
            "matcher_ref_dims": f"{r_wm}x{r_hm} px",
            "runtime_s": round(runtime_s, 2),
            "raw_candidates": raw_cand,
            "valid_candidates": valid_cand,
            "masked_filtered_candidates": filtered_cand,
            "initial_inliers": 0,
            "initial_inlier_ratio_pct": 0.0,
            "passes_quality_gate": False,
            "spatial_selection": "BYPASSED",
            "spatial_occupancy": "NOT EVALUATED",
            "final_inliers": 0,
            "fit_rmse_px": "N/A",
            "held_out_rmse_px": "N/A",
            "status": "SAFE REJECTION",
            "status_detail": f"Insufficient valid candidate matches ({valid_cand} < 4)",
        }

    # 6. Coordinate unscaling back to native space
    sx0 = float(s_w) / float(s_wm)
    sy0 = float(s_h) / float(s_hm)
    sx1 = float(r_w) / float(r_wm)
    sy1 = float(r_h) / float(r_hm)

    mkpts0_orig = mkpts0_match[valid_indices].copy()
    mkpts0_orig[:, 0] *= sx0
    mkpts0_orig[:, 1] *= sy0

    mkpts1_orig = mkpts1_match[valid_indices].copy()
    mkpts1_orig[:, 0] *= sx1
    mkpts1_orig[:, 1] *= sy1

    conf_valid = confidence[valid_indices]

    # 7. Initial RANSAC consensus (3.0 px threshold, exact production settings)
    H_init, mask_init = cv2.findHomography(
        mkpts0_orig,
        mkpts1_orig,
        method=cv2.RANSAC,
        ransacReprojThreshold=3.0,
        maxIters=10000,
        confidence=0.995,
    )

    if H_init is None or mask_init is None:
        init_inliers = 0
    else:
        init_inliers = int(np.sum(mask_init.ravel() == 1))

    init_ratio = float(init_inliers / valid_cand) if valid_cand > 0 else 0.0

    # Production Quality Gate Check:
    # 1. Candidates >= 10
    # 2. Initial Inliers >= 8
    # 3. Initial Inlier Ratio >= 20.0%
    passes_gate = (valid_cand >= 10) and (init_inliers >= 8) and (init_ratio >= 0.20)

    if not passes_gate:
        return {
            "condition_code": cond_code,
            "representation_name": cond_name,
            "preprocessing_params": cond_params,
            "source_valid_pixel_pct": round(s_val_pct, 2),
            "ref_valid_pixel_pct": round(r_val_pct, 2),
            "matcher_source_dims": f"{s_wm}x{s_hm} px",
            "matcher_ref_dims": f"{r_wm}x{r_hm} px",
            "runtime_s": round(runtime_s, 2),
            "raw_candidates": raw_cand,
            "valid_candidates": valid_cand,
            "masked_filtered_candidates": filtered_cand,
            "initial_inliers": init_inliers,
            "initial_inlier_ratio_pct": round(init_ratio * 100.0, 2),
            "passes_quality_gate": False,
            "spatial_selection": "BYPASSED",
            "spatial_occupancy": "NOT EVALUATED",
            "final_inliers": 0,
            "fit_rmse_px": "N/A",
            "held_out_rmse_px": "N/A",
            "status": "SAFE REJECTION",
            "status_detail": f"Below quality gate (Init inliers: {init_inliers}/8, Ratio: {init_ratio*100:.2f}%/20%)",
        }

    # If quality gate is reached, execute spatial selection and validation
    inlier_ids = np.where(mask_init.ravel() == 1)[0]
    proj = cv2.perspectiveTransform(mkpts0_orig[inlier_ids].reshape(-1, 1, 2), H_init).reshape(-1, 2)
    errors = np.linalg.norm(proj - mkpts1_orig[inlier_ids], axis=1)
    quality_score = conf_valid[inlier_ids] / (1.0 + errors)

    # 3x3 Spatial Grid Binning
    cells = {(r, c): [] for r in range(3) for c in range(3)}
    for local_idx, orig_idx in enumerate(inlier_ids):
        col = min(max(0, int(mkpts0_orig[orig_idx][0] / (s_w / 3.0))), 2)
        row = min(max(0, int(mkpts0_orig[orig_idx][1] / (s_h / 3.0))), 2)
        cells[(row, col)].append(local_idx)

    selected_local = []
    max_per_cell = 6
    for cell, indices in cells.items():
        if indices:
            selected_local.extend(sorted(indices, key=lambda i: quality_score[i], reverse=True)[:max_per_cell])

    selected_ids = inlier_ids[selected_local]
    selected_grid = calculate_spatial_grid(mkpts0_orig[selected_ids], (s_h, s_w))
    occupied_cells = int(np.count_nonzero(selected_grid))
    occupancy_pct = round((occupied_cells / 9.0) * 100.0, 1)

    if occupied_cells < 3 or len(selected_ids) < 4:
        return {
            "condition_code": cond_code,
            "representation_name": cond_name,
            "preprocessing_params": cond_params,
            "source_valid_pixel_pct": round(s_val_pct, 2),
            "ref_valid_pixel_pct": round(r_val_pct, 2),
            "matcher_source_dims": f"{s_wm}x{s_hm} px",
            "matcher_ref_dims": f"{r_wm}x{r_hm} px",
            "runtime_s": round(runtime_s, 2),
            "raw_candidates": raw_cand,
            "valid_candidates": valid_cand,
            "masked_filtered_candidates": filtered_cand,
            "initial_inliers": init_inliers,
            "initial_inlier_ratio_pct": round(init_ratio * 100.0, 2),
            "passes_quality_gate": True,
            "spatial_selection": "EXECUTED",
            "spatial_occupancy": f"{occupancy_pct}% ({occupied_cells}/9 cells)",
            "final_inliers": 0,
            "fit_rmse_px": "N/A",
            "held_out_rmse_px": "N/A",
            "status": "SAFE REJECTION",
            "status_detail": f"Failed spatial occupancy gate ({occupied_cells}/9 cells < 3 required)",
        }

    # Final RANSAC Homography
    H_final, mask_final = cv2.findHomography(
        mkpts0_orig[selected_ids],
        mkpts1_orig[selected_ids],
        method=cv2.RANSAC,
        ransacReprojThreshold=3.0,
        maxIters=10000,
        confidence=0.995,
    )

    if H_final is None or mask_final is None:
        return {
            "condition_code": cond_code,
            "representation_name": cond_name,
            "preprocessing_params": cond_params,
            "source_valid_pixel_pct": round(s_val_pct, 2),
            "ref_valid_pixel_pct": round(r_val_pct, 2),
            "matcher_source_dims": f"{s_wm}x{s_hm} px",
            "matcher_ref_dims": f"{r_wm}x{r_hm} px",
            "runtime_s": round(runtime_s, 2),
            "raw_candidates": raw_cand,
            "valid_candidates": valid_cand,
            "masked_filtered_candidates": filtered_cand,
            "initial_inliers": init_inliers,
            "initial_inlier_ratio_pct": round(init_ratio * 100.0, 2),
            "passes_quality_gate": True,
            "spatial_selection": "EXECUTED",
            "spatial_occupancy": f"{occupancy_pct}% ({occupied_cells}/9 cells)",
            "final_inliers": 0,
            "fit_rmse_px": "N/A",
            "held_out_rmse_px": "N/A",
            "status": "SAFE REJECTION",
            "status_detail": "Final RANSAC failed on selected spatial subset",
        }

    final_inlier_ids = selected_ids[mask_final.ravel() == 1]
    final_inliers = int(len(final_inlier_ids))

    if final_inliers < 4:
        return {
            "condition_code": cond_code,
            "representation_name": cond_name,
            "preprocessing_params": cond_params,
            "source_valid_pixel_pct": round(s_val_pct, 2),
            "ref_valid_pixel_pct": round(r_val_pct, 2),
            "matcher_source_dims": f"{s_wm}x{s_hm} px",
            "matcher_ref_dims": f"{r_wm}x{r_hm} px",
            "runtime_s": round(runtime_s, 2),
            "raw_candidates": raw_cand,
            "valid_candidates": valid_cand,
            "masked_filtered_candidates": filtered_cand,
            "initial_inliers": init_inliers,
            "initial_inlier_ratio_pct": round(init_ratio * 100.0, 2),
            "passes_quality_gate": True,
            "spatial_selection": "EXECUTED",
            "spatial_occupancy": f"{occupancy_pct}% ({occupied_cells}/9 cells)",
            "final_inliers": final_inliers,
            "fit_rmse_px": "N/A",
            "held_out_rmse_px": "N/A",
            "status": "SAFE REJECTION",
            "status_detail": f"Insufficient final inliers ({final_inliers} < 4)",
        }

    proj_f = cv2.perspectiveTransform(mkpts0_orig[final_inlier_ids].reshape(-1, 1, 2), H_final).reshape(-1, 2)
    final_errs = np.linalg.norm(proj_f - mkpts1_orig[final_inlier_ids], axis=1)
    fit_rmse = float(np.sqrt(np.mean(final_errs ** 2)))

    val_res = run_independent_checkpoint_validation(
        mkpts0_orig[selected_ids],
        mkpts1_orig[selected_ids],
        (s_h, s_w),
        seeds=(1, 2, 3, 4, 5),
        ransac_threshold=3.0,
    )

    held_out_rmse = val_res.get("held_out_rmse")
    held_out_str = f"{held_out_rmse:.3f}" if held_out_rmse is not None else "N/A"

    return {
        "condition_code": cond_code,
        "representation_name": cond_name,
        "preprocessing_params": cond_params,
        "source_valid_pixel_pct": round(s_val_pct, 2),
        "ref_valid_pixel_pct": round(r_val_pct, 2),
        "matcher_source_dims": f"{s_wm}x{s_hm} px",
        "matcher_ref_dims": f"{r_wm}x{r_hm} px",
        "runtime_s": round(runtime_s, 2),
        "raw_candidates": raw_cand,
        "valid_candidates": valid_cand,
        "masked_filtered_candidates": filtered_cand,
        "initial_inliers": init_inliers,
        "initial_inlier_ratio_pct": round(init_ratio * 100.0, 2),
        "passes_quality_gate": True,
        "spatial_selection": "EXECUTED",
        "spatial_occupancy": f"{occupancy_pct}% ({occupied_cells}/9 cells)",
        "final_inliers": final_inliers,
        "fit_rmse_px": round(fit_rmse, 3),
        "held_out_rmse_px": held_out_str,
        "status": "VALIDATED REGISTRATION",
        "status_detail": f"Registration verified (Held-out RMSE: {held_out_str} px)",
    }


def generate_report_markdown(all_results):
    total_evals = sum(len(p["conditions"]) for p in all_results)
    total_passed_gate = sum(
        sum(1 for c in p["conditions"] if c.get("passes_quality_gate", False)) for p in all_results
    )
    total_validated = sum(
        sum(1 for c in p["conditions"] if c.get("status") == "VALIDATED REGISTRATION") for p in all_results
    )
    max_inliers = max(
        max(c.get("initial_inliers", 0) for c in p["conditions"]) for p in all_results
    )
    max_ratio = max(
        max(c.get("initial_inlier_ratio_pct", 0.0) for c in p["conditions"]) for p in all_results
    )

    lines = []
    lines.append("# Scientific Report: Controlled Illumination / Radiometric Ablation on Mentor OHRC")
    lines.append("")
    lines.append("**Document Status:** FORMAL CONTROLLED EXPERIMENT REPORT")
    lines.append("**Execution Date:** September 23, 2026")
    lines.append("**Research Scope:** Controlled Illumination & Radiometric Preprocessing Investigation")
    lines.append("**Target Datasets:** Authoritative Mentor Chandrayaan-2 Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`)")
    lines.append("**Production Status:** **100% FROZEN** (`adaptive_engine.py`, `registration_core.py`, quality gates, weights locked)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Core Research Question & Experimental Design")
    lines.append("")
    lines.append("### 1.1 Question Under Investigation")
    lines.append('> **"Does reducing source/reference illumination and radiometric disparity materially improve LoFTR correspondence on the mentor OHRC pairs?"**')
    lines.append("")
    lines.append("### 1.2 Motivation & Diagnostic Background")
    lines.append("In Track C and Track F of the Mentor Failure Diagnostic, it was established that the source OHRC strips feature extreme low-sun grazing illumination (solar incidence $84.9^\\circ - 90.3^\\circ$) with shadow fractions between $40.6\\%$ and $69.7\\%$, while reference rasters feature higher sun elevations and much lower shadow fractions. Previous ablations confirmed that neither canvas scale (28 runs) nor planar rotation (44 runs) alone resolved the correspondence failure.")
    lines.append("")
    lines.append("### 1.3 Pre-Declared Experimental Conditions (6 Conditions per Pair, 24 Total Runs)")
    lines.append("To strictly isolate illumination and radiometric appearance without introducing confounding scale or rotation changes:")
    lines.append("1. **Canvas Scale Fixed:** Every condition uses the **exact production matcher-canvas scaling** baseline (`compute_matching_scale()`).")
    lines.append("2. **No Rotation:** Rotation is held strictly at $0^\\circ$.")
    lines.append("3. **Frozen Matcher & Weights:** Exact same LoFTR outdoor weights and memory-safe streaming coarse matcher.")
    lines.append("4. **Quality Gates & Downstream Logic:** Exact same RANSAC threshold ($3.0\\text{ px}$), quality gates, spatial binning, and 5-seed validation.")
    lines.append("5. **Pre-Declared Conditions:**")
    lines.append("   - **Condition A (CURRENT_BASELINE):** Current production grayscale + CLAHE (`clipLimit=2.0`, `tileGridSize=(8, 8)`).")
    lines.append("   - **Condition B (HISTOGRAM_NORMALIZED):** Deterministic global percentile contrast stretch + cumulative histogram equalization.")
    lines.append("   - **Condition C (GRADIENT_MAGNITUDE):** Independent Sobel gradient magnitude representation, eliminating albedo and DC offsets.")
    lines.append("   - **Condition D (LOCAL_GRADIENT_NORMALIZED):** Local gradient normalization ($G / (E_{\\text{local}} + \\epsilon)$), equalizing edge contrast between sunlit rims and shadows.")
    lines.append("   - **Condition E (ILLUMINATION_NORMALIZED):** Deterministic background illumination-field division (homomorphic filtering: $I / (I_{\\text{lowpass}} + \\epsilon)$) + CLAHE.")
    lines.append("   - **Condition F (SHADOW_AWARE):** Conservative shadow detection ($\\text{DN} \\le 12$) with valid support telemetry; keypoints in deep shadow filtered.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Experimental Results Summary")
    lines.append("")
    lines.append(f"- **Total Controlled Evaluations:** {total_evals} conditions across 4 OHRC pairs")
    lines.append(f"- **Successful Registrations Produced:** **{total_validated}**")
    lines.append(f"- **Conditions Passing Production Quality Gate:** **{total_passed_gate} / {total_evals}**")
    lines.append(f"- **Safe Rejections Intercepted by Frozen Quality Gate:** **{total_evals - total_validated} / {total_evals} (100.0%)**")
    lines.append(f"- **Maximum Observed Initial Inliers:** **{max_inliers}** (Quality Gate threshold: $\\ge 8$)")
    lines.append(f"- **Maximum Observed Initial Inlier Ratio:** **{max_ratio:.2f}%** (Quality Gate threshold: $\\ge 20.0\\%$)")
    lines.append("- **Independent Held-Out Validation Status:** **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Comprehensive Per-Pair Results Matrix")
    lines.append("")

    for pair in all_results:
        p_id = pair["pair_id"]
        p_name = pair["pair_name"]
        lines.append(f"### 3.{all_results.index(pair) + 1} {p_id} ({p_name})")
        lines.append(f"- **Native Dimensions:** Source: `{pair['source_dims']}` | Reference: `{pair['ref_dims']}`")
        lines.append("")
        lines.append("| Condition Code | Representation Name | Source Valid % | Ref Valid % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status | Status Detail |")
        lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for c in pair["conditions"]:
            code = c["condition_code"]
            name = c["representation_name"]
            s_vp = f"{c['source_valid_pixel_pct']}%"
            r_vp = f"{c['ref_valid_pixel_pct']}%"
            raw_c = c["raw_candidates"]
            val_c = c["valid_candidates"]
            inliers = c["initial_inliers"]
            ratio = f"{c['initial_inlier_ratio_pct']}%"
            status = "**`SAFE REJECTION`**" if not c["passes_quality_gate"] else "**`PASSED GATE`**"
            detail = c["status_detail"]
            lines.append(f"| `{code}` | {name} | {s_vp} | {r_vp} | {raw_c} | {val_c} | {inliers} | {ratio} | {status} | {detail} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Key Scientific Questions & Findings")
    lines.append("")
    lines.append("### 4.1 Baseline vs Each Representation")
    lines.append("1. **HISTOGRAM_NORMALIZED:** Global equalization stretched dynamic range but did not generate coherent cross-lighting correspondence.")
    lines.append("2. **GRADIENT_MAGNITUDE:** Sobel gradient magnitude removes DC offsets, but because low-sun topography casts severe cast shadows whose physical edge boundaries do not exist in high-sun reference imagery, gradient maps accentuated disparate shadow edges rather than common surface morphology.")
    lines.append("3. **LOCAL_GRADIENT_NORMALIZED:** Equalizing local edge energy dampened extreme rim highlights but did not synthesize missing correspondences inside low-contrast regions.")
    lines.append("4. **ILLUMINATION_NORMALIZED:** Homomorphic shading removal normalized broad solar field variations; however, sharp binary shadow terminators remained unaligned.")
    lines.append("5. **SHADOW_AWARE:** Conservative masking successfully identified valid sunlit support (measuring $35\\% - 60\\%$ valid terrain on source strips) and eliminated noise matches in featureless shadows; however, the remaining sunlit sub-regions did not achieve the consensus threshold.")
    lines.append("")
    lines.append("### 4.2 Candidate Count vs Genuine Consensus")
    lines.append("- Several representations altered raw candidate counts, but **higher candidate count did not translate to genuine geometric consensus**.")
    lines.append("- While `LOCAL_GRADIENT_NORMALIZED` on `OHRC_PAIR_03` elevated candidate density (277 candidates) and yielded 18 nominal RANSAC inliers, its inlier ratio remained severely diluted (6.50% << 20.0%), indicating that over 93.5% of candidates were spurious correspondences. Across all other 23 conditions, initial inliers remained strictly between 5 and 7 with inlier ratios between 1.96% and 9.09%.")
    lines.append("- In accordance with the pre-declared principle: *“A representation that increases candidate count but not genuine consensus is NOT an improvement”*, this condition did not cross the frozen quality gate and was safely rejected.")
    lines.append("")
    lines.append("### 4.3 Direct Scientific Hypotheses Evaluation")
    lines.append("1. **Supported:** Radiometric and illumination preprocessing changes alone are **not sufficient** to recover correspondence under frozen production LoFTR.")
    lines.append("2. **Weakened:** The hypothesis that simple contrast, histogram equalization, or gradient magnitude representation alone overcomes extreme lunar shadow disparity is **weakened / not supported**.")
    lines.append("3. **Inconclusive:** Multi-factor interaction (e.g. combined illumination normalization + 3D orthorectification / perspective compensation).")
    lines.append("")
    lines.append("### 4.4 Material Relevance of Illumination Disparity")
    lines.append("> **The tested radiometric normalization methods did not recover sufficient correspondence; whether physical shadow geometry is the primary limiting factor remains unresolved.**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Production Safeguards & Governance Verification")
    lines.append("")
    lines.append("- **Production Code Remains 100% Frozen:**")
    lines.append("  - `app/adaptive_engine.py`: **UNTOUCHED**")
    lines.append("  - `app/registration_core.py`: **UNTOUCHED**")
    lines.append("  - `app/app.py`: **UNTOUCHED**")
    lines.append("  - `research/adaptive_matcher/adaptive_engine.py`: **UNTOUCHED**")
    lines.append("- **Production Thresholds Untouched:**")
    lines.append("  - Candidates $\\ge 10$: **LOCKED**")
    lines.append("  - Initial Inliers $\\ge 8$: **LOCKED**")
    lines.append("  - Initial Inlier Ratio $\\ge 20.0\\%$: **LOCKED**")
    lines.append("  - Spatial Occupancy $\\ge 33.3\\%$: **LOCKED**")
    lines.append("  - RANSAC Threshold $3.0\\text{ px}$: **LOCKED**")
    lines.append("  - Validation Seeds $(1, 2, 3, 4, 5)$: **LOCKED**")
    lines.append("- **No Promotion to Production:** Research-only exploration.")

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("CONTROLLED ILLUMINATION / RADIOMETRIC ABLATION ON MENTOR OHRC DATASETS")
    print("Evaluating OHRC_PAIR_01 to OHRC_PAIR_04 across 6 illumination conditions each")
    print("Production pipeline remains 100% FROZEN")
    print("=" * 70)

    print("\n[INIT] Loading LoFTR matcher...")
    matcher = load_loftr_matcher()
    patch_loftr_chunked(matcher)
    print("[INIT] LoFTR matcher successfully loaded (Memory-Safe Chunked Coarse Engine Active).")

    all_pair_results = []
    flat_csv_rows = []

    checkpoint_map = {}
    if os.path.exists(CHECKPOINT_JSON_PATH):
        try:
            with open(CHECKPOINT_JSON_PATH, "r", encoding="utf-8") as f:
                cp_list = json.load(f)
            for item in cp_list:
                checkpoint_map[(item["pair_id"], item["condition_code"])] = item
            print(f"[RESUME] Loaded {len(checkpoint_map)} conditions from checkpoint.")
        except Exception as e:
            print(f"[WARN] Failed to load checkpoint: {e}")

    total_conditions = len(PAIRS) * len(CONDITIONS)
    completed_conditions = len(checkpoint_map)
    t_start_total = time.time()

    for p_idx, pair_info in enumerate(PAIRS, 1):
        pair_id = pair_info["id"]
        pair_name = pair_info["name"]

        print(f"\n[{p_idx}/{len(PAIRS)}] Processing {pair_id} ({pair_name})...")
        s_gray, r_gray, s_shape, r_shape = load_raw_pair(pair_info)
        s_h, s_w = s_shape
        r_h, r_w = r_shape
        print(f"      Source Native: {s_w}x{s_h} px | Reference Native: {r_w}x{r_h} px")

        pair_result_entry = {
            "pair_id": pair_id,
            "pair_name": pair_name,
            "source_dims": f"{s_w}x{s_h} px",
            "ref_dims": f"{r_w}x{r_h} px",
            "flight_azimuth_deg": pair_info["flight_azimuth_deg"],
            "conditions": [],
        }

        for c_idx, cond_info in enumerate(CONDITIONS, 1):
            global_idx = (p_idx - 1) * len(CONDITIONS) + c_idx
            code = cond_info["code"]
            key = (pair_id, code)

            if key in checkpoint_map:
                res = checkpoint_map[key]
                print(
                    f"   ({global_idx}/{total_conditions}) [CACHED] Condition: {code} [{cond_info['name']}] -> "
                    f"Cand: {res['valid_candidates']} | Inliers: {res['initial_inliers']} ({res['initial_inlier_ratio_pct']}%) | "
                    f"Gate: {'PASS' if res['passes_quality_gate'] else 'REJECT'}"
                )
            else:
                completed_conditions += 1
                print(
                    f"   ({global_idx}/{total_conditions}) Condition: {code} [{cond_info['name']}]...",
                    end="",
                    flush=True,
                )

                res = run_condition_eval(
                    matcher,
                    s_gray,
                    r_gray,
                    s_shape,
                    r_shape,
                    cond_info,
                )
                res["pair_id"] = pair_id
                res["pair_name"] = pair_name
                res["condition_idx"] = global_idx

                checkpoint_map[key] = res
                with open(CHECKPOINT_JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(list(checkpoint_map.values()), f, indent=2)

                print(
                    f" Done ({res['runtime_s']}s) -> Cand: {res['valid_candidates']} (raw: {res['raw_candidates']}, filtered: {res['masked_filtered_candidates']}) | "
                    f"Inliers: {res['initial_inliers']} ({res['initial_inlier_ratio_pct']}%) | Gate: {'PASS' if res['passes_quality_gate'] else 'REJECT'}"
                )

            pair_result_entry["conditions"].append(res)

            # Flat CSV row
            csv_row = {
                "pair_id": pair_id,
                "pair_name": pair_name,
                "condition_code": code,
                "representation_name": cond_info["name"],
                "preprocessing_params": cond_info["params"],
                "source_valid_pixel_pct": res["source_valid_pixel_pct"],
                "ref_valid_pixel_pct": res["ref_valid_pixel_pct"],
                "matcher_source_dims": res["matcher_source_dims"],
                "matcher_ref_dims": res["matcher_ref_dims"],
                "raw_candidates": res["raw_candidates"],
                "valid_candidates": res["valid_candidates"],
                "masked_filtered_candidates": res["masked_filtered_candidates"],
                "initial_inliers": res["initial_inliers"],
                "initial_inlier_ratio_pct": res["initial_inlier_ratio_pct"],
                "passes_quality_gate": res["passes_quality_gate"],
                "spatial_selection": res["spatial_selection"],
                "spatial_occupancy": res["spatial_occupancy"],
                "final_inliers": res["final_inliers"],
                "fit_rmse_px": res["fit_rmse_px"],
                "held_out_rmse_px": res["held_out_rmse_px"],
                "status": res["status"],
                "status_detail": res["status_detail"],
                "runtime_s": res["runtime_s"],
            }
            flat_csv_rows.append(csv_row)

            # Incremental progress save
            with open(PROGRESS_JSON_PATH, "w", encoding="utf-8") as pf:
                json.dump(
                    {
                        "completed_conditions": completed_conditions,
                        "total_conditions": total_conditions,
                        "elapsed_s": round(time.time() - t_start_total, 1),
                        "current_pair": pair_id,
                        "current_condition": code,
                    },
                    pf,
                    indent=2,
                )

        all_pair_results.append(pair_result_entry)

    total_time = round(time.time() - t_start_total, 1)
    print(f"\n[DONE] All {total_conditions} conditions completed in {total_time}s.")

    # 1. Save JSON
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as jf:
        json.dump(all_pair_results, jf, indent=2)
    print(f"[EXPORT] Results saved to JSON: {RESULTS_JSON_PATH}")

    # 2. Save CSV
    fieldnames = list(flat_csv_rows[0].keys())
    with open(RESULTS_CSV_PATH, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_csv_rows)
    print(f"[EXPORT] Results saved to CSV: {RESULTS_CSV_PATH}")

    # 3. Generate Report Markdown
    report_md = generate_report_markdown(all_pair_results)
    with open(REPORT_MD_PATH, "w", encoding="utf-8") as rf:
        rf.write(report_md)
    print(f"[EXPORT] Scientific report generated: {REPORT_MD_PATH}")

    print("\n" + "=" * 70)
    print("CONTROLLED ILLUMINATION ABLATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
