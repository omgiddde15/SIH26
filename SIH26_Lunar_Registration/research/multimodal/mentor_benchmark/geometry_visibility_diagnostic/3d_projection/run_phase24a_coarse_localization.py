"""
Phase 24A — Cheap Deterministic Coarse Localization Prefilter
=============================================================
RESEARCH-ONLY. Production code is NOT modified.

Canonical production files FROZEN (READ-ONLY):
  app/app.py
  app/adaptive_adapter.py
  app/registration_core.py
  research/adaptive_matcher/adaptive_engine.py

Preserved Governance Constants:
  REFERENCE_PRODUCT_UNRESOLVED
  REFERENCE_GEODETIC_REALIZATION = UNKNOWN
  REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
  PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW

Phase 24A Research Question:
  "Can a cheap deterministic structural prefilter identify a small set of
   image-space placement hypotheses that are worth expensive LoFTR verification?"

Predeclared Deterministic Lattice (dx, dy in metres):
  {-3000, -2000, -1000, 0, 1000, 2000, 3000}
  → 7 x 7 = 49 offsets per pair × 4 pairs = 196 coarse candidates.

Reference Scale: 5 m/pixel
Pixel offsets = {-600, -400, -200, 0, 200, 400, 600} pixels

Predeclared Screening Thresholds (FIXED — NOT tuned after seeing results):
  T_INT_NCC_MIN = 0.08        (per-window, zero-mean intensity NCC)
  T_GRAD_NCC_MIN = 0.06       (per-window, Sobel-gradient NCC)
  T_PHASE_RESP_MIN = 0.05     (per-window phase correlation response)
  T_FAST_N_MIN = 3            (per-window FAST+ZMUV candidate correspondences)
  T_VALID_WINDOWS_MIN = 3     (min valid local windows for SCREEN_PASS)
  T_SPATIAL_CELLS_MIN = 3     (min distinct 3x3 source cells)
  T_FAST_ANY_CANDIDATES = 4   (any single-window FAST threshold)

Failure Classes:
  F1 = insufficient reference support
  F2 = no coarse structural recovery
  F3 = coarse structure exists but LoFTR correspondence insufficient
  F4 = LoFTR geometry initially passes but hold-out fails
  F5 = validated relative-registration candidate exists

Phase 24A Overall Classification (one of):
  A. PREFILTER_RECOVERED_CANDIDATES
  B. PREFILTER_FOUND_NO_CANDIDATE
  C. VERIFICATION_FAILED
  D. INCONCLUSIVE
"""

import sys
import os
import json
import csv
import time
import hashlib
import math
import datetime
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
torch.set_num_threads(4)

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import cv2
import rasterio

from research.adaptive_matcher.adaptive_engine import (
    load_loftr_matcher,
    run_loftr_matching,
    execute_common_downstream,
)

DATA_DIR = Path(r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc")
OUT_DIR = Path(__file__).parent
CHECKPOINT_FILE = OUT_DIR / "phase24a_checkpoint.json"

SCREEN_CSV = OUT_DIR / "phase24a_screen_candidates.csv"
SCREEN_JSON = OUT_DIR / "phase24a_screen_candidates.json"
LOFTR_CSV = OUT_DIR / "phase24a_loftr_verification.csv"
PAIR_SUMMARY_CSV = OUT_DIR / "phase24a_pair_summary.csv"
REPORT_MD = OUT_DIR / "phase24a_coarse_localization_report.md"
FAILURE_MD = OUT_DIR / "phase24a_failure_classification.md"

GOVERNANCE = {
    "REFERENCE_PRODUCT_UNRESOLVED": True,
    "REFERENCE_GEODETIC_REALIZATION": "UNKNOWN",
    "REFERENCE_TO_MOON_ME_DE421": "NOT_VERIFIED",
    "PHASE_23B_STATUS": "BLOCKED_PENDING_GEODETIC_REVIEW",
    "PHASE_24_STATUS": "DEFERRED_COMPUTATIONAL_COST",
    "PHASE_24_RESEARCH_RESULT": "INCONCLUSIVE",
}

QG = {
    "min_candidates": 10,
    "min_initial_inliers": 8,
    "min_inlier_ratio": 0.20,
    "min_occupancy": 0.33,
    "ransac_threshold": 3.0,
    "downstream_min_inliers": 4,
    "grid": "3x3",
    "max_per_cell": 6,
    "validation_seeds": (1, 2, 3, 4, 5),
}

SCREEN_THRESHOLDS = {
    "T_INT_NCC_MIN": 0.08,
    "T_GRAD_NCC_MIN": 0.06,
    "T_PHASE_RESP_MIN": 0.05,
    "T_FAST_N_MIN": 3,
    "T_VALID_WINDOWS_MIN": 3,
    "T_SPATIAL_CELLS_MIN": 3,
    "T_FAST_ANY_CANDIDATES": 4,
    "declaration": "Thresholds fixed PRE-DECLARATION before evaluation. No tuning performed.",
}

OFFSET_METRES = [-3000, -2000, -1000, 0, 1000, 2000, 3000]
REFERENCE_SCALE_M_PER_PX = 5.0

PAIR_META = [
    {
        "pair": "OHRC_PAIR_01",
        "src_file": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif",
        "src_w": 624, "src_h": 4872,
        "ref_w": 5916, "ref_h": 4232,
        "center_ref_u": 3268.08, "center_ref_v": 2339.48,
        "crop_hw": 500, "crop_hh": 1500,
        "phase23a6_mean_dx_m": 1720.2, "phase23a6_mean_dy_m": -1303.61, "phase23a6_mag_m": 2158.36,
    },
    {
        "pair": "OHRC_PAIR_02",
        "src_file": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif",
        "src_w": 648, "src_h": 5059,
        "ref_w": 2593, "ref_h": 6279,
        "center_ref_u": 1365.52, "center_ref_v": 2679.45,
        "crop_hw": 500, "crop_hh": 1500,
        "phase23a6_mean_dx_m": 283.56, "phase23a6_mean_dy_m": 1232.74, "phase23a6_mag_m": 1264.93,
    },
    {
        "pair": "OHRC_PAIR_03",
        "src_file": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif",
        "src_w": 600, "src_h": 5054,
        "ref_w": 2416, "ref_h": 6316,
        "center_ref_u": 1291.4, "center_ref_v": 2625.21,
        "crop_hw": 500, "crop_hh": 1500,
        "phase23a6_mean_dx_m": 274.78, "phase23a6_mean_dy_m": 1677.59, "phase23a6_mag_m": 1699.94,
    },
    {
        "pair": "OHRC_PAIR_04",
        "src_file": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_source_at_5m.tif",
        "ref_file": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif",
        "src_w": 552, "src_h": 4649,
        "ref_w": 3164, "ref_h": 6322,
        "center_ref_u": 1722.51, "center_ref_v": 2445.59,
        "crop_hw": 500, "crop_hh": 1500,
        "phase23a6_mean_dx_m": 627.35, "phase23a6_mean_dy_m": 2088.93, "phase23a6_mag_m": 2181.1,
    },
]


def build_predeclared_offsets() -> List[Tuple[int, int]]:
    """Deterministic 7x7 = 49 offsets per pair from the fixed lattice."""
    return [(dx, dy) for dx in OFFSET_METRES for dy in OFFSET_METRES]


def make_candidate_key(pair_id: str, dx_m: int, dy_m: int) -> str:
    return f"{pair_id}__dx{dx_m:+d}m_dy{dy_m:+d}m"


def compute_gradient_magnitude(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    sobel_x = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(sobel_x**2 + sobel_y**2)
    ang = np.arctan2(sobel_y, sobel_x)
    return mag, ang


def zmuv_normalize(arr: np.ndarray) -> np.ndarray:
    mu = float(np.mean(arr))
    sd = float(np.std(arr))
    if sd < 1e-6:
        return np.zeros_like(arr, dtype=np.float32)
    return ((arr.astype(np.float32) - mu) / sd).astype(np.float32)


def compute_crop_window(
    center_ref_u: float,
    center_ref_v: float,
    ref_w: int,
    ref_h: int,
    du_m: int,
    dv_m: int,
    crop_hw: int = 500,
    crop_hh: int = 1500,
) -> Optional[Tuple[int, int, int, int, int, int]]:
    """
    Compute reference pixel crop window for an offset.
    du_px = du_m / 5.0       (map X = raster U)
    dv_px = -dv_m / 5.0      (map Y north-up, raster V south-down)
    Returns (u_min, v_min, u_max, v_max, crop_w, crop_h) or None if < 64 px.
    """
    du_px = int(round(du_m / REFERENCE_SCALE_M_PER_PX))
    dv_px = int(round(-dv_m / REFERENCE_SCALE_M_PER_PX))

    cu = int(round(center_ref_u + du_px))
    cv = int(round(center_ref_v + dv_px))

    u_min = max(0, cu - crop_hw)
    v_min = max(0, cv - crop_hh)
    u_max = min(ref_w, cu + crop_hw)
    v_max = min(ref_h, cv + crop_hh)

    cw = u_max - u_min
    ch = v_max - v_min
    if cw < 64 or ch < 64:
        return None
    return (u_min, v_min, u_max, v_max, cw, ch)


def source_3x3_windows(src_h: int, src_w: int, tpl_size: int = 128) -> List[Dict[str, Any]]:
    """
    Deterministic 3x3 local-window framework on the source image.
    Each window is centered at (cx, cy) of a 3x3 grid; clamped to the raster.
    Returns list of dicts with window_id, grid_rc, cx, cy, x1, y1, x2, y2, tpl_size.
    """
    windows = []
    for r_idx in range(3):
        for c_idx in range(3):
            win_id = r_idx * 3 + c_idx + 1
            cx = int(round(src_w * (2 * c_idx + 1) / 6.0))
            cy = int(round(src_h * (2 * r_idx + 1) / 6.0))
            half = tpl_size // 2
            x1 = max(0, min(src_w - tpl_size, cx - half))
            y1 = max(0, min(src_h - tpl_size, cy - half))
            x2 = x1 + tpl_size
            y2 = y1 + tpl_size
            actual_cx = (x1 + x2) / 2.0
            actual_cy = (y1 + y2) / 2.0
            windows.append({
                "window_id": win_id,
                "grid_rc": (r_idx, c_idx),
                "cx_src": actual_cx,
                "cy_src": actual_cy,
                "x1_src": x1, "y1_src": y1,
                "x2_src": x2, "y2_src": y2,
                "tpl_size": tpl_size,
            })
    return windows


def map_window_to_reference(
    win: Dict[str, Any],
    src_h: int, src_w: int,
    ref_crop_u_min: int, ref_crop_v_min: int,
    ref_crop_w: int, ref_crop_h: int,
) -> Optional[Dict[str, Any]]:
    """
    Map a source local window to the corresponding reference crop location
    under the current translational offset hypothesis.
    Uses proportional mapping within each raster's extent.
    """
    x1_rel = win["x1_src"] / float(src_w)
    y1_rel = win["y1_src"] / float(src_h)
    x2_rel = win["x2_src"] / float(src_w)
    y2_rel = win["y2_src"] / float(src_h)

    rx1 = int(round(x1_rel * ref_crop_w))
    ry1 = int(round(y1_rel * ref_crop_h))
    rx2 = int(round(x2_rel * ref_crop_w))
    ry2 = int(round(y2_rel * ref_crop_h))

    rx1 = max(0, min(ref_crop_w - 16, rx1))
    ry1 = max(0, min(ref_crop_h - 16, ry1))
    rx2 = max(rx1 + 16, min(ref_crop_w, rx2))
    ry2 = max(ry1 + 16, min(ref_crop_h, ry2))

    if (rx2 - rx1) < 16 or (ry2 - ry1) < 16:
        return None

    return {
        "window_id": win["window_id"],
        "grid_rc": win["grid_rc"],
        "x1_ref_local": rx1, "y1_ref_local": ry1,
        "x2_ref_local": rx2, "y2_ref_local": ry2,
        "x1_ref_global": rx1 + ref_crop_u_min,
        "y1_ref_global": ry1 + ref_crop_v_min,
        "x2_ref_global": rx2 + ref_crop_u_min,
        "y2_ref_global": ry2 + ref_crop_v_min,
        "crop_w": rx2 - rx1,
        "crop_h": ry2 - ry1,
    }


def per_window_intensity_ncc(src_patch: np.ndarray, ref_patch: np.ndarray) -> float:
    a = zmuv_normalize(src_patch)
    b = zmuv_normalize(ref_patch)
    if a.size == 0 or b.size == 0:
        return 0.0
    if np.std(a) < 1e-6 or np.std(b) < 1e-6:
        return 0.0
    h, w = a.shape
    bh, bw = b.shape
    if (bh, bw) != (h, w):
        target = cv2.resize(b, (w, h), interpolation=cv2.INTER_AREA)
    else:
        target = b
    denom = float(h * w)
    if denom < 1:
        return 0.0
    return float(np.sum(a * target) / denom)


def per_window_gradient_ncc(src_patch: np.ndarray, ref_patch: np.ndarray) -> float:
    sg, _ = compute_gradient_magnitude(src_patch.astype(np.uint8) if src_patch.dtype != np.uint8 else src_patch)
    rg, _ = compute_gradient_magnitude(ref_patch.astype(np.uint8) if ref_patch.dtype != np.uint8 else ref_patch)
    return per_window_intensity_ncc(sg, rg)


def per_window_phase_response(src_patch: np.ndarray, ref_patch: np.ndarray) -> Tuple[float, Tuple[float, float]]:
    h, w = src_patch.shape
    bh, bw = ref_patch.shape
    if (bh, bw) != (h, w):
        target = cv2.resize(ref_patch, (w, h), interpolation=cv2.INTER_AREA)
    else:
        target = ref_patch
    try:
        hann = cv2.createHanningWindow((w, h), cv2.CV_32F)
        shift, response = cv2.phaseCorrelate(
            src_patch.astype(np.float32),
            target.astype(np.float32),
            hann,
        )
        return float(response), (float(shift[0]), float(shift[1]))
    except Exception:
        return 0.0, (0.0, 0.0)


def per_window_fast_structural_support(
    src_patch: np.ndarray, ref_patch: np.ndarray, half: int = 7
) -> Dict[str, Any]:
    """
    FAST on Sobel gradient magnitude + 15x15 ZMUV descriptor + BFM knn (Lowe 0.80).
    Returns candidate correspondence count and per-cell information.
    """
    sg, _ = compute_gradient_magnitude(src_patch)
    rg, _ = compute_gradient_magnitude(ref_patch)

    sg_u8 = cv2.normalize(sg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    rg_u8 = cv2.normalize(rg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    fast = cv2.FastFeatureDetector_create(threshold=15, nonmaxSuppression=True)
    kps_s = fast.detect(sg_u8)
    kps_r = fast.detect(rg_u8)

    if len(kps_s) < 4 or len(kps_r) < 4:
        return {
            "fast_n_src": len(kps_s),
            "fast_n_ref": len(kps_r),
            "candidate_correspondences": 0,
            "status": "insufficient_keypoints",
        }

    def extract_zmuv(img, kps, half_=7):
        descs = []
        valid = []
        hh, ww = img.shape
        for kp in kps:
            x, y = int(round(kp.pt[0])), int(round(kp.pt[1]))
            if x >= half_ and x < ww - half_ and y >= half_ and y < hh - half_:
                patch = img[y-half_:y+half_+1, x-half_:x+half_+1].astype(np.float32)
                p_std = float(np.std(patch))
                if p_std > 1e-3:
                    patch = (patch - float(np.mean(patch))) / p_std
                    descs.append(patch.ravel())
                    valid.append(kp)
        return valid, np.array(descs, dtype=np.float32) if descs else np.empty((0, (2*half_+1)**2), dtype=np.float32)

    vk_s, des_s = extract_zmuv(sg_u8, kps_s, half)
    vk_r, des_r = extract_zmuv(rg_u8, kps_r, half)

    if len(des_s) < 4 or len(des_r) < 4:
        return {
            "fast_n_src": len(des_s),
            "fast_n_ref": len(des_r),
            "candidate_correspondences": 0,
            "status": "insufficient_descriptors",
        }

    bf = cv2.BFMatcher(cv2.NORM_L2)
    try:
        matches_sr = bf.knnMatch(des_s, des_r, k=2)
    except Exception:
        return {
            "fast_n_src": len(des_s),
            "fast_n_ref": len(des_r),
            "candidate_correspondences": 0,
            "status": "bfmatch_error",
        }

    good = []
    for pair in matches_sr:
        if len(pair) == 2:
            m, n = pair
            if m.distance < 0.80 * n.distance:
                good.append(m)

    return {
        "fast_n_src": len(vk_s),
        "fast_n_ref": len(vk_r),
        "candidate_correspondences": len(good),
        "status": "ok" if len(good) > 0 else "no_lowes_filtered_matches",
    }


def classify_window_support(
    wd: Dict[str, Any], T: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """Return (supported: bool, reasons: list[str]) for a single window."""
    reasons = []
    supported = False

    if wd.get("valid_support_pct", 0.0) < 50.0:
        reasons.append("insufficient_valid_pixels")
        return False, reasons

    int_ncc = float(wd.get("intensity_ncc", 0.0))
    grad_ncc = float(wd.get("gradient_ncc", 0.0))
    phase_resp = float(wd.get("phase_response", 0.0))
    fast_n = int(wd.get("fast_candidates", 0))

    if int_ncc >= T["T_INT_NCC_MIN"]:
        reasons.append(f"intensity_ncc={int_ncc:.3f}≥{T['T_INT_NCC_MIN']}")
        supported = True
    if grad_ncc >= T["T_GRAD_NCC_MIN"]:
        reasons.append(f"gradient_ncc={grad_ncc:.3f}≥{T['T_GRAD_NCC_MIN']}")
        supported = True
    if phase_resp >= T["T_PHASE_RESP_MIN"]:
        reasons.append(f"phase_resp={phase_resp:.3f}≥{T['T_PHASE_RESP_MIN']}")
        supported = True
    if fast_n >= T["T_FAST_N_MIN"]:
        reasons.append(f"fast_candidates={fast_n}≥{T['T_FAST_N_MIN']}")
        supported = True

    return supported, reasons


def evaluate_candidate_cheap(
    src_img: np.ndarray,
    ref_img: np.ndarray,
    src_h: int, src_w: int,
    ref_h: int, ref_w: int,
    crop: Tuple[int, int, int, int, int, int],
    windows: List[Dict[str, Any]],
    T: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run cheap diagnostics on 3x3 local windows for one candidate offset.
    Returns per-window diagnostics plus aggregate screening decision.
    """
    u_min, v_min, u_max, v_max, cw, ch = crop
    ref_crop = ref_img[v_min:v_max, u_min:u_max]

    per_window = []
    supported_cells: set = set()
    valid_window_count = 0
    valid_int_count = 0
    valid_grad_count = 0
    valid_phase_count = 0
    valid_fast_count = 0
    any_fast_ge_TF4 = False

    for win in windows:
        x1, y1, x2, y2 = win["x1_src"], win["y1_src"], win["x2_src"], win["y2_src"]
        src_patch = src_img[y1:y2, x1:x2]
        ref_win = map_window_to_reference(win, src_h, src_w, u_min, v_min, cw, ch)

        wd: Dict[str, Any] = {
            "window_id": win["window_id"],
            "grid_rc": f"{win['grid_rc'][0]},{win['grid_rc'][1]}",
            "mapped": ref_win is not None,
        }

        if ref_win is None:
            wd["status"] = "unmapped_ref_window"
            wd["valid_support_pct"] = 0.0
            wd["supported"] = False
            wd["support_reasons"] = []
            per_window.append(wd)
            continue

        rx1, ry1 = ref_win["x1_ref_local"], ref_win["y1_ref_local"]
        rx2, ry2 = ref_win["x2_ref_local"], ref_win["y2_ref_local"]
        ref_patch = ref_crop[ry1:ry2, rx1:rx2]

        valid_pct = float(np.count_nonzero(src_patch > 12) / float(src_patch.size) * 100.0)
        wd["valid_support_pct"] = round(valid_pct, 1)

        if valid_pct < 50.0:
            wd["status"] = "low_valid_support"
            wd["supported"] = False
            wd["support_reasons"] = ["insufficient_valid_pixels"]
            per_window.append(wd)
            continue

        wd["ref_global_rect"] = [
            ref_win["x1_ref_global"], ref_win["y1_ref_global"],
            ref_win["x2_ref_global"], ref_win["y2_ref_global"],
        ]

        int_ncc = per_window_intensity_ncc(src_patch.astype(np.float32), ref_patch.astype(np.float32))
        grad_ncc = per_window_gradient_ncc(src_patch, ref_patch)
        phase_resp, phase_shift = per_window_phase_response(
            src_patch.astype(np.uint8) if src_patch.dtype != np.uint8 else src_patch,
            ref_patch.astype(np.uint8) if ref_patch.dtype != np.uint8 else ref_patch,
        )
        fast_info = per_window_fast_structural_support(
            src_patch if src_patch.dtype == np.uint8 else cv2.normalize(src_patch, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
            ref_patch if ref_patch.dtype == np.uint8 else cv2.normalize(ref_patch, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
        )

        wd["intensity_ncc"] = round(float(int_ncc), 4)
        wd["gradient_ncc"] = round(float(grad_ncc), 4)
        wd["phase_response"] = round(float(phase_resp), 4)
        wd["phase_shift_px"] = [round(phase_shift[0], 2), round(phase_shift[1], 2)]
        wd["fast_src_kps"] = fast_info["fast_n_src"]
        wd["fast_ref_kps"] = fast_info["fast_n_ref"]
        wd["fast_candidates"] = int(fast_info["candidate_correspondences"])
        wd["fast_status"] = fast_info["status"]

        if int_ncc >= T["T_INT_NCC_MIN"]:
            valid_int_count += 1
        if grad_ncc >= T["T_GRAD_NCC_MIN"]:
            valid_grad_count += 1
        if phase_resp >= T["T_PHASE_RESP_MIN"]:
            valid_phase_count += 1
        if int(fast_info["candidate_correspondences"]) >= T["T_FAST_N_MIN"]:
            valid_fast_count += 1
        if int(fast_info["candidate_correspondences"]) >= T["T_FAST_ANY_CANDIDATES"]:
            any_fast_ge_TF4 = True

        supported, reasons = classify_window_support(wd, T)
        wd["supported"] = bool(supported)
        wd["support_reasons"] = reasons
        if supported:
            supported_cells.add(win["grid_rc"])
            valid_window_count += 1
        wd["status"] = "evaluated"
        per_window.append(wd)

    n_cells = len(supported_cells)
    finite_phase = valid_phase_count > 0
    structural_ok = valid_fast_count > 0 or any_fast_ge_TF4
    no_invalidating_support = True

    conds = {
        "C1_min_3_valid_windows": valid_window_count >= T["T_VALID_WINDOWS_MIN"],
        "C2_min_3_spatial_cells": n_cells >= T["T_SPATIAL_CELLS_MIN"],
        "C3_finite_phase_response": finite_phase,
        "C4_structural_strength": structural_ok,
        "C5_no_invalidating_support": no_invalidating_support,
    }

    all_pass = all(conds.values())

    if all_pass:
        decision = "SCREEN_PASS"
    elif valid_window_count == 0 and n_cells == 0:
        decision = "INSUFFICIENT_SUPPORT"
    else:
        decision = "SCREEN_FAIL"

    return {
        "per_window": per_window,
        "supported_windows": valid_window_count,
        "supported_spatial_cells": n_cells,
        "valid_intensity_windows": valid_int_count,
        "valid_gradient_windows": valid_grad_count,
        "valid_phase_windows": valid_phase_count,
        "valid_fast_windows": valid_fast_count,
        "any_fast_ge_TF4": any_fast_ge_TF4,
        "conditions": conds,
        "decision": decision,
        "crop_geometry": {
            "u_min": u_min, "v_min": v_min,
            "u_max": u_max, "v_max": v_max,
            "crop_w": cw, "crop_h": ch,
            "coverage_pct": round(100.0 * cw * ch / float(ref_w * ref_h), 3),
        },
    }


def load_checkpoint() -> Dict[str, Any]:
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "phase24a_v1",
        "created": datetime.datetime.now().isoformat(),
        "governance": GOVERNANCE,
        "screen_thresholds": SCREEN_THRESHOLDS,
        "quality_gate": {k: (list(v) if isinstance(v, tuple) else v) for k, v in QG.items()},
        "pair_meta": PAIR_META,
        "offset_grid_metres": OFFSET_METRES,
        "reference_scale_m_per_px": REFERENCE_SCALE_M_PER_PX,
        "controls": {},
        "candidates": {},
        "pair_summary": {},
        "final_classification": None,
        "total_runtime_s": None,
    }


def save_checkpoint(cp: Dict[str, Any]) -> None:
    cp["last_updated"] = datetime.datetime.now().isoformat()
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(cp, f, indent=2, default=str)


def load_gray_uint8(filepath: Path) -> Optional[np.ndarray]:
    try:
        with rasterio.open(str(filepath)) as ds:
            arr = ds.read(1).astype(np.float32)
        lo, hi = np.percentile(arr, 1), np.percentile(arr, 99)
        if hi > lo:
            arr = np.clip((arr - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
        else:
            arr = np.zeros_like(arr, dtype=np.uint8)
        return arr
    except Exception as exc:
        print(f"  [WARN] Could not load {filepath}: {exc}")
        return None


def run_controls(
    pair_meta: List[Dict[str, Any]],
    src_by_pair: Dict[str, np.ndarray],
    ref_by_pair: Dict[str, np.ndarray],
    loftr_model,
    T: Dict[str, Any],
) -> Dict[str, Any]:
    """
    CONTROL 1: Known negative (non-overlapping far-corner crop of Pair 01 reference)
    CONTROL 2: Known synthetic transform pair (R=2°, tx=10, ty=10)
    CONTROL 3: Deliberately displaced nominal crop (Control 3: known same-sensor overlap)
    """
    results: Dict[str, Any] = {}

    # ---------- CONTROL 1: Negative (Pair 01 top-left far crop) ----------
    try:
        p01 = pair_meta[0]
        src_p01 = src_by_pair["OHRC_PAIR_01"]
        ref_p01 = ref_by_pair["OHRC_PAIR_01"]
        rh, rw = ref_p01.shape[:2]
        crop_cw = min(512, rw // 4)
        crop_ch = min(512, rh // 4)
        ctrl_crop = ref_p01[0:crop_ch, 0:crop_cw]
        t0 = time.perf_counter()
        windows_c = source_3x3_windows(src_p01.shape[0], src_p01.shape[1], tpl_size=128)
        cheap_c = evaluate_candidate_cheap(
            src_p01, ref_p01,
            src_p01.shape[0], src_p01.shape[1],
            rh, rw,
            (0, 0, crop_cw, crop_ch, crop_cw, crop_ch),
            windows_c, T,
        )
        t_cheap = time.perf_counter() - t0
        loftr_res = None
        if cheap_c["decision"] == "SCREEN_PASS":
            t0_l = time.perf_counter()
            loftr_res = run_loftr_matching(src_p01, ctrl_crop, loftr_model=loftr_model)
            t_cheap = time.perf_counter() - t0_l
        n_candidates = int(loftr_res.get("n_candidates", 0)) if loftr_res else 0
        n_inliers = int(loftr_res.get("n_inliers", 0)) if loftr_res else 0
        results["CONTROL_1"] = {
            "control": "CONTROL_1",
            "description": "Known negative: non-overlapping top-left 512x512 corner of Pair 01 reference",
            "status": "EXECUTED",
            "cheap_decision": cheap_c["decision"],
            "supported_windows": cheap_c["supported_windows"],
            "supported_cells": cheap_c["supported_spatial_cells"],
            "conditions": cheap_c["conditions"],
            "n_candidates_loftr": n_candidates,
            "n_inliers_loftr": n_inliers,
            "inlier_ratio_loftr": round(float(loftr_res.get("inlier_ratio", 0.0)) if loftr_res else 0.0, 4),
            "expected_outcome": "SCREEN_FAIL_OR_MINIMAL_INLIERS",
            "observed_outcome": (
                "SCREEN_PASS_NEGATIVE_ANOMALY" if cheap_c["decision"] == "SCREEN_PASS" and n_inliers >= QG["min_initial_inliers"]
                else "AS_EXPECTED_NEGATIVE"
            ),
            "elapsed_cheap_s": round(t_cheap, 2),
        }
    except Exception as exc:
        results["CONTROL_1"] = {"control": "CONTROL_1", "status": "ERROR", "error": str(exc), "trace": traceback.format_exc(limit=2)}

    # ---------- CONTROL 2: Synthetic known transform ----------
    try:
        rng = np.random.RandomState(42)
        base = rng.randint(80, 180, (400, 400), dtype=np.uint8)
        for i in range(0, 400, 20):
            cv2.line(base, (i, 0), (i, 400), int(base[0, i]) + 40, 1)
            cv2.line(base, (0, i), (400, i), int(base[i, 0]) + 40, 1)
        for _ in range(40):
            cx, cy = int(rng.randint(30, 370)), int(rng.randint(30, 370))
            cv2.circle(base, (cx, cy), int(rng.randint(8, 20)), int(rng.uniform(40, 220)), -1)
        M = cv2.getRotationMatrix2D((200, 200), 2.0, 1.0)
        M[0, 2] += 10
        M[1, 2] += 10
        warped_ctrl = cv2.warpAffine(base, M, (400, 400))
        t0 = time.perf_counter()
        windows_c2 = source_3x3_windows(base.shape[0], base.shape[1], tpl_size=128)
        # Use the whole warped image as "reference" crop at 0,0
        cheap_c2 = evaluate_candidate_cheap(
            base, warped_ctrl,
            base.shape[0], base.shape[1],
            warped_ctrl.shape[0], warped_ctrl.shape[1],
            (0, 0, warped_ctrl.shape[1], warped_ctrl.shape[0], warped_ctrl.shape[1], warped_ctrl.shape[0]),
            windows_c2, T,
        )
        t_cheap_c2 = time.perf_counter() - t0
        loftr_c2 = None
        if cheap_c2["decision"] == "SCREEN_PASS":
            t0_l = time.perf_counter()
            loftr_c2 = run_loftr_matching(base, warped_ctrl, loftr_model=loftr_model)
            t_cheap_c2 = time.perf_counter() - t0_l
        n_cand_c2 = int(loftr_c2.get("n_candidates", 0)) if loftr_c2 else 0
        n_inl_c2 = int(loftr_c2.get("n_inliers", 0)) if loftr_c2 else 0
        results["CONTROL_2"] = {
            "control": "CONTROL_2",
            "description": "Synthetic known-transform pair (rotation=2.0°, tx=10px, ty=10px)",
            "status": "EXECUTED",
            "cheap_decision": cheap_c2["decision"],
            "supported_windows": cheap_c2["supported_windows"],
            "supported_cells": cheap_c2["supported_spatial_cells"],
            "conditions": cheap_c2["conditions"],
            "n_candidates_loftr": n_cand_c2,
            "n_inliers_loftr": n_inl_c2,
            "inlier_ratio_loftr": round(float(loftr_c2.get("inlier_ratio", 0.0)) if loftr_c2 else 0.0, 4),
            "expected_outcome": "SCREEN_PASS_AND_SUBSTANTIAL_INLIERS",
            "observed_outcome": (
                "AS_EXPECTED_POSITIVE"
                if (cheap_c2["decision"] == "SCREEN_PASS" and n_inl_c2 >= QG["min_initial_inliers"])
                else "LOW_INLIERS_OR_SCREEN_FAIL"
            ),
            "elapsed_cheap_s": round(t_cheap_c2, 2),
        }
    except Exception as exc:
        results["CONTROL_2"] = {"control": "CONTROL_2", "status": "ERROR", "error": str(exc), "trace": traceback.format_exc(limit=2)}

    # ---------- CONTROL 3: Same-sensor Pair 02 nominal crop (deliberate overlap) ----------
    try:
        p02 = pair_meta[1]
        src_p02 = src_by_pair["OHRC_PAIR_02"]
        ref_p02 = ref_by_pair["OHRC_PAIR_02"]
        cr_u_min = max(0, int(p02["center_ref_u"]) - p02["crop_hw"])
        cr_v_min = max(0, int(p02["center_ref_v"]) - p02["crop_hh"])
        cr_u_max = min(p02["ref_w"], int(p02["center_ref_u"]) + p02["crop_hw"])
        cr_v_max = min(p02["ref_h"], int(p02["center_ref_v"]) + p02["crop_hh"])
        ccw, cch = cr_u_max - cr_u_min, cr_v_max - cr_v_min
        nominal_crop = ref_p02[cr_v_min:cr_v_max, cr_u_min:cr_u_max]
        t0 = time.perf_counter()
        windows_c3 = source_3x3_windows(src_p02.shape[0], src_p02.shape[1], tpl_size=128)
        cheap_c3 = evaluate_candidate_cheap(
            src_p02, ref_p02,
            src_p02.shape[0], src_p02.shape[1],
            ref_p02.shape[0], ref_p02.shape[1],
            (cr_u_min, cr_v_min, cr_u_max, cr_v_max, ccw, cch),
            windows_c3, T,
        )
        t_cheap_c3 = time.perf_counter() - t0
        loftr_c3 = None
        if cheap_c3["decision"] == "SCREEN_PASS":
            t0_l = time.perf_counter()
            loftr_c3 = run_loftr_matching(src_p02, nominal_crop, loftr_model=loftr_model)
            t_cheap_c3 = time.perf_counter() - t0_l
        n_cand_c3 = int(loftr_c3.get("n_candidates", 0)) if loftr_c3 else 0
        n_inl_c3 = int(loftr_c3.get("n_inliers", 0)) if loftr_c3 else 0
        results["CONTROL_3"] = {
            "control": "CONTROL_3",
            "description": "Same-sensor Pair 02 nominal crop at (dx=0, dy=0) — known overlap via Phase 23A.9",
            "status": "EXECUTED",
            "cheap_decision": cheap_c3["decision"],
            "supported_windows": cheap_c3["supported_windows"],
            "supported_cells": cheap_c3["supported_spatial_cells"],
            "conditions": cheap_c3["conditions"],
            "n_candidates_loftr": n_cand_c3,
            "n_inliers_loftr": n_inl_c3,
            "inlier_ratio_loftr": round(float(loftr_c3.get("inlier_ratio", 0.0)) if loftr_c3 else 0.0, 4),
            "expected_outcome": "INDICATOR_OF_MATCHER_SENSITIVITY",
            "observed_outcome": f"n_candidates={n_cand_c3}, n_inliers={n_inl_c3}",
            "elapsed_cheap_s": round(t_cheap_c3, 2),
        }
    except Exception as exc:
        results["CONTROL_3"] = {"control": "CONTROL_3", "status": "ERROR", "error": str(exc), "trace": traceback.format_exc(limit=2)}

    return results


def check_quality_gate(
    match_result: Dict[str, Any],
    downstream_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    gate = {
        "gate_min_candidates": False,
        "gate_min_initial_inliers": False,
        "gate_min_inlier_ratio": False,
        "gate_min_occupancy": False,
        "gate_downstream_min_inliers": False,
        "gate_held_out_valid": False,
        "gate_all_pass": False,
        "failure_class": "F2",
    }
    n_cand = int(match_result.get("n_candidates", 0) or 0)
    n_inl = int(match_result.get("n_inliers", 0) or 0)
    ratio = float(match_result.get("inlier_ratio", 0.0) or (n_inl / n_cand if n_cand > 0 else 0.0))

    if n_cand < QG["min_candidates"]:
        gate["failure_class"] = "F2"
        return gate
    gate["gate_min_candidates"] = True

    gate["gate_min_initial_inliers"] = (n_inl >= QG["min_initial_inliers"])
    gate["gate_min_inlier_ratio"] = (ratio >= QG["min_inlier_ratio"])

    if not gate["gate_min_initial_inliers"] or not gate["gate_min_inlier_ratio"]:
        gate["failure_class"] = "F3"
        return gate

    if downstream_result is None:
        gate["failure_class"] = "F3"
        return gate

    occ = float(downstream_result.get("spatial_occupancy", 0.0) or 0.0)
    n_final = int(downstream_result.get("n_final_inliers", 0) or 0)
    held_out = bool(downstream_result.get("held_out_valid", False))

    gate["gate_min_occupancy"] = (occ >= QG["min_occupancy"])
    gate["gate_downstream_min_inliers"] = (n_final >= QG["downstream_min_inliers"])
    gate["gate_held_out_valid"] = held_out

    gate["gate_all_pass"] = (
        gate["gate_min_candidates"]
        and gate["gate_min_initial_inliers"]
        and gate["gate_min_inlier_ratio"]
        and gate["gate_min_occupancy"]
        and gate["gate_downstream_min_inliers"]
        and gate["gate_held_out_valid"]
    )

    if not gate["gate_min_occupancy"] or not gate["gate_downstream_min_inliers"]:
        gate["failure_class"] = "F3"
    elif not gate["gate_held_out_valid"]:
        gate["failure_class"] = "F4"
    else:
        gate["failure_class"] = "F5"

    return gate


def write_screen_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, default=str) if isinstance(v, (dict, list, tuple)) else v) for k, v in r.items()})


def write_loftr_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, default=str) if isinstance(v, (dict, list, tuple)) else v) for k, v in r.items()})


def write_pair_summary_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, default=str) if isinstance(v, (dict, list, tuple)) else v) for k, v in r.items()})


def render_report(
    cp: Dict[str, Any],
    screen_rows: List[Dict[str, Any]],
    loftr_rows: List[Dict[str, Any]],
    pair_summary: List[Dict[str, Any]],
    runtime_total: float,
) -> str:
    counts = {}
    counts["total_coarse_candidates"] = len(screen_rows)
    counts["screen_pass"] = sum(1 for r in screen_rows if r.get("decision") == "SCREEN_PASS")
    counts["screen_fail"] = sum(1 for r in screen_rows if r.get("decision") == "SCREEN_FAIL")
    counts["insufficient_support"] = sum(1 for r in screen_rows if r.get("decision") == "INSUFFICIENT_SUPPORT")
    counts["loftr_verified"] = len(loftr_rows)
    counts["qg_initial_pass"] = sum(
        1 for r in loftr_rows
        if (int(r.get("n_candidates", 0) or 0) >= QG["min_candidates"]
            and int(r.get("n_inliers", 0) or 0) >= QG["min_initial_inliers"]
            and float(r.get("inlier_ratio", 0.0) or 0.0) >= QG["min_inlier_ratio"])
    )
    counts["qg_all_pass"] = sum(1 for r in loftr_rows if str(r.get("gate_all_pass")) == "True")
    counts["hold_out_pass"] = sum(1 for r in loftr_rows if str(r.get("gate_held_out_valid")) == "True")
    counts["validated_f5"] = sum(1 for r in loftr_rows if str(r.get("gate_all_pass")) == "True")

    counts_by_pair: Dict[str, Dict[str, int]] = {}
    for ps in pair_summary:
        pid = ps["pair_id"]
        counts_by_pair.setdefault(pid, {"n_coarse": 0, "screen_pass": 0, "loftr_verified": 0, "qg_pass": 0, "f5": 0})
        counts_by_pair[pid]["n_coarse"] = int(ps.get("total_candidates", 0))
        counts_by_pair[pid]["screen_pass"] = int(ps.get("screen_pass", 0))
        counts_by_pair[pid]["loftr_verified"] = int(ps.get("loftr_verified", 0))
        counts_by_pair[pid]["qg_pass"] = int(ps.get("quality_gate_pass", 0))
        counts_by_pair[pid]["f5"] = int(ps.get("f5_validated", 0))

    lines: List[str] = []
    lines.append("# Phase 24A — Coarse Deterministic Image-Space Prefilter Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.datetime.now().isoformat()}  ")
    lines.append(f"**Total Runtime:** {runtime_total:.2f} s ({runtime_total/60.0:.1f} min)  ")
    lines.append(f"**Governing Discipline:** RESEARCH-ONLY — Production Code FROZEN  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Governance Constants (PRESERVED UNCHANGED)")
    lines.append("")
    lines.append(f"- `REFERENCE_PRODUCT_UNRESOLVED` = {GOVERNANCE['REFERENCE_PRODUCT_UNRESOLVED']}")
    lines.append(f"- `REFERENCE_GEODETIC_REALIZATION` = {GOVERNANCE['REFERENCE_GEODETIC_REALIZATION']}")
    lines.append(f"- `REFERENCE_TO_MOON_ME_DE421` = {GOVERNANCE['REFERENCE_TO_MOON_ME_DE421']}")
    lines.append(f"- `PHASE_23B_STATUS` = {GOVERNANCE['PHASE_23B_STATUS']}")
    lines.append(f"- `PHASE_24_STATUS` (original, unchanged) = {GOVERNANCE['PHASE_24_STATUS']}")
    lines.append(f"- `PHASE_24_RESEARCH_RESULT` (original, unchanged) = {GOVERNANCE['PHASE_24_RESEARCH_RESULT']}")
    lines.append("")
    lines.append("## 2. Predeclared Experimental Design")
    lines.append("")
    lines.append(f"- Coarse offset lattice (metres): `{OFFSET_METRES}`")
    lines.append(f"- 7 × 7 = 49 offsets per pair × 4 pairs = **196 coarse candidates**")
    lines.append(f"- Reference scale: 5 m / reference pixel → pixel offsets `{{-600,-400,-200,0,200,400,600}}` px")
    lines.append(f"- Local framework: 3×3 deterministic source windows, 128×128 px each")
    lines.append(f"- Search center: Nominal reference footprint from audited Phase 23 physical projection (NOT moved by Phase 23A.6 translations)")
    lines.append("")
    lines.append("### 2.1 Predeclared Screening Thresholds (FIXED)")
    lines.append("")
    for k, v in SCREEN_THRESHOLDS.items():
        if k == "declaration":
            lines.append(f"- {v}")
        else:
            lines.append(f"- `{k}` = {v}")
    lines.append("")
    lines.append("### 2.2 Frozen Quality Gate (UNCHANGED)")
    lines.append("")
    for k, v in QG.items():
        lines.append(f"- `{k}` = {v}")
    lines.append("")
    lines.append("## 3. Controls Summary")
    lines.append("")
    for cid in ("CONTROL_1", "CONTROL_2", "CONTROL_3"):
        c = cp.get("controls", {}).get(cid)
        if not c:
            continue
        lines.append(f"### 3.{('123')[('CONTROL_1','CONTROL_2','CONTROL_3').index(cid)]} {cid}")
        lines.append(f"- **Description:** {c.get('description','')}")
        lines.append(f"- **Cheap Decision:** `{c.get('cheap_decision','')}`")
        lines.append(f"- **Supported Windows / Cells:** {c.get('supported_windows',0)} / {c.get('supported_cells',0)}")
        lines.append(f"- **LoFTR n_candidates / n_inliers:** {c.get('n_candidates_loftr',0)} / {c.get('n_inliers_loftr',0)}")
        lines.append(f"- **Expected:** {c.get('expected_outcome','')}")
        lines.append(f"- **Observed:** {c.get('observed_outcome','')}")
        lines.append("")
    lines.append("## 4. Aggregate Counts")
    lines.append("")
    lines.append(f"- Total coarse candidates generated: **{counts['total_coarse_candidates']}**")
    lines.append(f"- `SCREEN_PASS`: **{counts['screen_pass']}**")
    lines.append(f"- `SCREEN_FAIL`: {counts['screen_fail']}")
    lines.append(f"- `INSUFFICIENT_SUPPORT`: {counts['insufficient_support']}")
    lines.append(f"- LoFTR verification runs (SCREEN_PASS only): **{counts['loftr_verified']}**")
    lines.append(f"- Initial quality-gate passes (n_cand≥10 ∧ n_inl≥8 ∧ ratio≥0.20): {counts['qg_initial_pass']}")
    lines.append(f"- Full quality-gate passes (incl. occupancy ≥0.33, final ≥4, held-out): {counts['qg_all_pass']}")
    lines.append(f"- Hold-out validation passes: {counts['hold_out_pass']}")
    lines.append(f"- Research-validated F5 candidates: **{counts['validated_f5']}**")
    lines.append("")
    lines.append("### 4.1 Per-Pair Summary")
    lines.append("")
    lines.append("| Pair | Coarse | SCREEN_PASS | LoFTR | Initial QG | Full QG | F5 | Failure Class |")
    lines.append("|:---|---:|---:|---:|---:|---:|---:|:---|")
    for ps in pair_summary:
        pid = ps["pair_id"]
        lines.append(
            f"| {pid} | {ps.get('total_candidates',0)} "
            f"| {ps.get('screen_pass',0)} | {ps.get('loftr_verified',0)} "
            f"| {ps.get('initial_qg_pass',0)} | {ps.get('quality_gate_pass',0)} "
            f"| {ps.get('f5_validated',0)} | {ps.get('failure_class','')} |"
        )
    lines.append("")
    lines.append("## 5. Phase 24A Overall Classification")
    lines.append("")
    lines.append(f"**`{cp.get('final_classification','INCONCLUSIVE')}`**")
    lines.append("")
    interpretation = cp.get("classification_interpretation", "")
    if interpretation:
        lines.append(f"{interpretation}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Interpretation Boundaries (IMPORTANT)")
    lines.append("")
    lines.append("- This phase is **candidate-window screening only**. It is NOT registration, NOT geolocation, NOT geodetic correction, NOT reference-product identification.")
    lines.append("- No ranking of candidate offsets is asserted. Multiple candidates may be `SCREEN_PASS`.")
    lines.append("- `SCREEN_PASS` alone is NOT a registration. Only `F5 = full frozen QG + independent hold-out` constitutes research-level relative-registration feasibility.")
    lines.append("- Phase 24 overall remains **DEFERRED_COMPUTATIONAL_COST / INCONCLUSIVE**.")
    lines.append("- Geodetic status of the reference product remains **UNRESOLVED / UNKNOWN / NOT_VERIFIED**.")
    lines.append("")
    return "\n".join(lines)


def render_failure_md(
    pair_summary: List[Dict[str, Any]],
    loftr_rows: List[Dict[str, Any]],
    screen_rows: List[Dict[str, Any]],
) -> str:
    lines: List[str] = []
    lines.append("# Phase 24A — Failure Classification")
    lines.append("")
    lines.append("Failure Classes:")
    lines.append("- `F1` = insufficient reference support")
    lines.append("- `F2` = no coarse structural recovery")
    lines.append("- `F3` = coarse structure exists but LoFTR correspondence insufficient")
    lines.append("- `F4` = LoFTR geometry initially passes but hold-out fails")
    lines.append("- `F5` = validated relative-registration candidate exists")
    lines.append("")
    lines.append("## Per-Pair Classification")
    lines.append("")
    for ps in pair_summary:
        pid = ps["pair_id"]
        lines.append(f"### {pid}")
        lines.append(f"- **Result Class:** `{ps.get('failure_class','')}`")
        lines.append(f"- **Rationale:** {ps.get('failure_rationale','')}")
        lines.append(f"- Coarse candidates: {ps.get('total_candidates',0)}")
        lines.append(f"  - SCREEN_PASS: {ps.get('screen_pass',0)}")
        lines.append(f"  - SCREEN_FAIL: {ps.get('screen_fail',0)}")
        lines.append(f"  - INSUFFICIENT_SUPPORT (F1 proxy): {ps.get('insufficient_support',0)}")
        lines.append(f"- LoFTR verified: {ps.get('loftr_verified',0)}")
        lines.append(f"- Initial QG pass: {ps.get('initial_qg_pass',0)}")
        lines.append(f"- Full QG pass: {ps.get('quality_gate_pass',0)}")
        lines.append(f"- F5 validated: {ps.get('f5_validated',0)}")
        lines.append("")
    lines.append("## Per-Candidate Failure Drill-Down")
    lines.append("")
    lines.append("### All SCREEN_PASS → LoFTR Results")
    lines.append("")
    if not loftr_rows:
        lines.append("_No SCREEN_PASS candidates were evaluated by LoFTR._")
    else:
        lines.append("| Key | dx_m | dy_m | n_cand | n_inl | ratio | occ | final_inl | held-out | gate | f-class |")
        lines.append("|:---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---|")
        for r in loftr_rows:
            lines.append(
                f"| {r.get('candidate_key','')} "
                f"| {r.get('dx_m','')} | {r.get('dy_m','')} "
                f"| {r.get('n_candidates',0)} | {r.get('n_inliers',0)} "
                f"| {r.get('inlier_ratio',0.0)} "
                f"| {r.get('spatial_occupancy',0.0)} "
                f"| {r.get('n_final_inliers',0)} "
                f"| {r.get('gate_held_out_valid','')} "
                f"| {r.get('gate_all_pass','')} "
                f"| {r.get('failure_class','')} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    t_total_start = time.perf_counter()
    print("=" * 80)
    print("PHASE 24A — CHEAP DETERMINISTIC COARSE LOCALIZATION PREFILTER")
    print("=" * 80)
    print(f"Repo root     : {REPO_ROOT}")
    print(f"Data dir      : {DATA_DIR}")
    print(f"Output dir    : {OUT_DIR}")
    print(f"Grid (metres) : {OFFSET_METRES}")
    print(f"Thresholds    : {SCREEN_THRESHOLDS}")

    cp = load_checkpoint()
    offsets = build_predeclared_offsets()
    print(f"Total candidates generated (planned): {len(offsets) * len(PAIR_META)}")

    src_by_pair: Dict[str, np.ndarray] = {}
    ref_by_pair: Dict[str, np.ndarray] = {}
    for pm in PAIR_META:
        pid = pm["pair"]
        sp = DATA_DIR / pm["src_file"]
        rp = DATA_DIR / pm["ref_file"]
        print(f"  Loading {pid} source: {sp.name}")
        s = load_gray_uint8(sp)
        print(f"    shape={s.shape if s is not None else 'None'}")
        print(f"  Loading {pid} reference: {rp.name}")
        r = load_gray_uint8(rp)
        print(f"    shape={r.shape if r is not None else 'None'}")
        if s is None or r is None:
            raise RuntimeError(f"Could not load rasters for {pid}")
        src_by_pair[pid] = s
        ref_by_pair[pid] = r

    print("\nLoading LoFTR model (once, process-wide) ...")
    loftr_model = load_loftr_matcher()
    print("  LoFTR loaded.\n")

    # ---- Controls (run once, before candidates) ----
    print("Running CONTROLS ...")
    controls = run_controls(PAIR_META, src_by_pair, ref_by_pair, loftr_model, SCREEN_THRESHOLDS)
    cp["controls"] = controls
    for cid, c in controls.items():
        print(f"  {cid}: decision={c.get('cheap_decision')} LoFTR n_inl={c.get('n_inliers_loftr',0)} observed={c.get('observed_outcome')}")
    save_checkpoint(cp)

    # ---- Iterate pairs & offsets ----
    screen_rows: List[Dict[str, Any]] = []
    loftr_rows: List[Dict[str, Any]] = []
    pair_summary_list: List[Dict[str, Any]] = []

    for pm in PAIR_META:
        pid = pm["pair"]
        print(f"\n========== {pid} ==========")
        src_img = src_by_pair[pid]
        ref_img = ref_by_pair[pid]
        src_h, src_w = src_img.shape
        ref_h, ref_w = ref_img.shape
        windows = source_3x3_windows(src_h, src_w, tpl_size=128)
        pair_n_coarse = 0
        pair_screen_pass = 0
        pair_screen_fail = 0
        pair_insuff = 0
        pair_loftr = 0
        pair_initial_qg_pass = 0
        pair_qg_pass = 0
        pair_f5 = 0

        for (dx_m, dy_m) in offsets:
            key = make_candidate_key(pid, dx_m, dy_m)
            if key in cp.get("candidates", {}):
                prev = cp["candidates"][key]
                stage_done = str(prev.get("stage", ""))
                if stage_done in ("cheap_done", "loftr_done", "complete"):
                    pair_n_coarse += 1
                    if prev.get("cheap_diagnostics", {}).get("decision") == "SCREEN_PASS":
                        pair_screen_pass += 1
                    elif prev.get("cheap_diagnostics", {}).get("decision") == "SCREEN_FAIL":
                        pair_screen_fail += 1
                    else:
                        pair_insuff += 1
                    if "loftr_verification" in prev and prev.get("loftr_verification") is not None:
                        pair_loftr += 1
                        lv = prev["loftr_verification"]
                        nc = int(lv.get("n_candidates", 0) or 0)
                        ni = int(lv.get("n_inliers", 0) or 0)
                        ir = float(lv.get("inlier_ratio", 0.0) or 0.0)
                        gate = lv.get("gate", {}) or {}
                        if nc >= QG["min_candidates"] and ni >= QG["min_initial_inliers"] and ir >= QG["min_inlier_ratio"]:
                            pair_initial_qg_pass += 1
                        if str(gate.get("gate_all_pass")) == "True":
                            pair_qg_pass += 1
                            pair_f5 += 1
                    continue

            t_cand_start = time.perf_counter()
            pair_n_coarse += 1

            crop = compute_crop_window(
                pm["center_ref_u"], pm["center_ref_v"],
                pm["ref_w"], pm["ref_h"],
                dx_m, dy_m,
                pm["crop_hw"], pm["crop_hh"],
            )

            cand_entry: Dict[str, Any] = {
                "candidate_key": key,
                "pair_id": pid,
                "dx_m": dx_m,
                "dy_m": dy_m,
                "du_px": int(round(dx_m / REFERENCE_SCALE_M_PER_PX)),
                "dv_px": int(round(-dy_m / REFERENCE_SCALE_M_PER_PX)),
                "stage": "init",
                "status": "pending",
                "failure_class": None,
            }

            if crop is None:
                cand_entry.update({
                    "stage": "cheap_done",
                    "status": "INSUFFICIENT_SUPPORT",
                    "failure_class": "F1",
                    "cheap_diagnostics": {
                        "decision": "INSUFFICIENT_SUPPORT",
                        "reason": "Reference crop < 64 pixels on an axis (F1 insufficient reference support)",
                        "supported_windows": 0,
                        "supported_spatial_cells": 0,
                        "conditions": {k: False for k in [
                            "C1_min_3_valid_windows","C2_min_3_spatial_cells",
                            "C3_finite_phase_response","C4_structural_strength",
                            "C5_no_invalidating_support"]},
                        "crop_geometry": None,
                    },
                    "loftr_verification": None,
                    "runtime_s": round(time.perf_counter() - t_cand_start, 3),
                })
                pair_insuff += 1
                cp.setdefault("candidates", {})[key] = cand_entry
                row = {
                    "candidate_key": key, "pair_id": pid,
                    "dx_m": dx_m, "dy_m": dy_m,
                    "du_px": cand_entry["du_px"], "dv_px": cand_entry["dv_px"],
                    "decision": "INSUFFICIENT_SUPPORT",
                    "supported_windows": 0, "supported_cells": 0,
                    "crop_u_min": None, "crop_v_min": None, "crop_u_max": None, "crop_v_max": None,
                    "coverage_pct": None,
                    "phase23a6_mean_dx_m": pm["phase23a6_mean_dx_m"],
                    "phase23a6_mean_dy_m": pm["phase23a6_mean_dy_m"],
                    "phase23a6_mag_m": pm["phase23a6_mag_m"],
                }
                screen_rows.append(row)
                continue

            try:
                cheap = evaluate_candidate_cheap(
                    src_img, ref_img,
                    src_h, src_w,
                    ref_h, ref_w,
                    crop, windows, SCREEN_THRESHOLDS,
                )
                decision = cheap["decision"]
                if decision == "SCREEN_PASS":
                    pair_screen_pass += 1
                elif decision == "SCREEN_FAIL":
                    pair_screen_fail += 1
                else:
                    pair_insuff += 1

                cand_entry.update({
                    "stage": "cheap_done",
                    "status": decision,
                    "cheap_diagnostics": cheap,
                    "runtime_s": round(time.perf_counter() - t_cand_start, 3),
                })

                cg = cheap.get("crop_geometry", {})
                row = {
                    "candidate_key": key, "pair_id": pid,
                    "dx_m": dx_m, "dy_m": dy_m,
                    "du_px": cand_entry["du_px"], "dv_px": cand_entry["dv_px"],
                    "decision": decision,
                    "supported_windows": cheap.get("supported_windows", 0),
                    "supported_cells": cheap.get("supported_spatial_cells", 0),
                    "valid_intensity": cheap.get("valid_intensity_windows", 0),
                    "valid_gradient": cheap.get("valid_gradient_windows", 0),
                    "valid_phase": cheap.get("valid_phase_windows", 0),
                    "valid_fast": cheap.get("valid_fast_windows", 0),
                    "any_fast_ge_TF4": cheap.get("any_fast_ge_TF4", False),
                    "C1_valid_windows": cheap.get("conditions", {}).get("C1_min_3_valid_windows"),
                    "C2_cells": cheap.get("conditions", {}).get("C2_min_3_spatial_cells"),
                    "C3_phase": cheap.get("conditions", {}).get("C3_finite_phase_response"),
                    "C4_structural": cheap.get("conditions", {}).get("C4_structural_strength"),
                    "C5_no_invalidate": cheap.get("conditions", {}).get("C5_no_invalidating_support"),
                    "crop_u_min": cg.get("u_min"), "crop_v_min": cg.get("v_min"),
                    "crop_u_max": cg.get("u_max"), "crop_v_max": cg.get("v_max"),
                    "coverage_pct": cg.get("coverage_pct"),
                    "phase23a6_mean_dx_m": pm["phase23a6_mean_dx_m"],
                    "phase23a6_mean_dy_m": pm["phase23a6_mean_dy_m"],
                    "phase23a6_mag_m": pm["phase23a6_mag_m"],
                    "per_window_json": json.dumps(cheap.get("per_window", []), default=str),
                }
                screen_rows.append(row)

                if decision == "SCREEN_PASS":
                    u_min, v_min, u_max, v_max, _, _ = crop
                    ref_crop_eval = ref_img[v_min:v_max, u_min:u_max]
                    pair_loftr += 1
                    t_loftr_start = time.perf_counter()
                    try:
                        mres = run_loftr_matching(src_img, ref_crop_eval, loftr_model=loftr_model)
                    except Exception as loftr_exc:
                        mres = {
                            "method": "LoFTR",
                            "success": False,
                            "failure_stage": "exception",
                            "failure_reason": str(loftr_exc),
                            "runtime": time.perf_counter() - t_loftr_start,
                            "n_candidates": 0, "n_inliers": 0, "inlier_ratio": 0.0,
                            "spatial_occupancy": 0.0, "spatial_cv": 0.0,
                        }
                    n_cand = int(mres.get("n_candidates", 0) or 0)
                    n_inl = int(mres.get("n_inliers", 0) or 0)
                    ir = float(mres.get("inlier_ratio", 0.0) or (n_inl / n_cand if n_cand > 0 else 0.0))
                    initial_qg_ok = (
                        n_cand >= QG["min_candidates"]
                        and n_inl >= QG["min_initial_inliers"]
                        and ir >= QG["min_inlier_ratio"]
                    )
                    if initial_qg_ok:
                        pair_initial_qg_pass += 1

                    downstream = None
                    try:
                        if initial_qg_ok and mres.get("success") and len(mres.get("pts0", [])) > 0:
                            pts0 = mres["pts0"]
                            pts1 = mres["pts1"]
                            confs = mres.get("confidences")
                            if confs is None or len(confs) != len(pts0):
                                confs = np.ones(len(pts0), dtype=np.float32)
                            downstream = execute_common_downstream(
                                pts0, pts1, confs,
                                src_img, ref_crop_eval,
                                max_per_cell=QG["max_per_cell"],
                                ransac_thresh=QG["ransac_threshold"],
                                seeds=QG["validation_seeds"],
                            )
                    except Exception as dsex:
                        downstream = None
                        mres.setdefault("downstream_exception", str(dsex))

                    gate = check_quality_gate(mres, downstream)
                    if str(gate.get("gate_all_pass")) == "True":
                        pair_qg_pass += 1
                        pair_f5 += 1
                        cand_entry["failure_class"] = "F5"
                    else:
                        cand_entry["failure_class"] = gate.get("failure_class", "F2")

                    cand_entry.update({
                        "stage": "complete",
                        "status": "loftr_complete",
                        "loftr_verification": {
                            "n_candidates": n_cand,
                            "n_inliers": n_inl,
                            "inlier_ratio": round(ir, 5),
                            "spatial_occupancy": round(float(mres.get("spatial_occupancy", 0.0) or 0.0), 4),
                            "spatial_cv": round(float(mres.get("spatial_cv", 0.0) or 0.0), 4),
                            "n_final_inliers": int(downstream.get("n_final_inliers", 0)) if downstream else 0,
                            "held_out_valid": bool(downstream.get("held_out_valid", False)) if downstream else False,
                            "mean_check_rmse": (
                                round(float(downstream.get("mean_check_rmse")), 4)
                                if downstream and downstream.get("mean_check_rmse") is not None
                                   and not (isinstance(downstream.get("mean_check_rmse"), float) and math.isnan(downstream.get("mean_check_rmse")))
                                else None
                            ),
                            "fit_rmse": round(float(downstream.get("fit_rmse", 0.0)), 4) if downstream else None,
                            "loftr_runtime_s": round(time.perf_counter() - t_loftr_start, 2),
                            "gate": gate,
                            "failure_class": gate.get("failure_class", "F2"),
                            "success": bool(mres.get("success", False)),
                            "failure_stage": mres.get("failure_stage"),
                            "failure_reason": mres.get("failure_reason"),
                        },
                        "runtime_s": round(time.perf_counter() - t_cand_start, 3),
                    })
                    cp.setdefault("candidates", {})[key] = cand_entry

                    loftr_rows.append({
                        "candidate_key": key, "pair_id": pid,
                        "dx_m": dx_m, "dy_m": dy_m,
                        "n_candidates": n_cand,
                        "n_inliers": n_inl,
                        "inlier_ratio": round(ir, 5),
                        "spatial_occupancy": cand_entry["loftr_verification"]["spatial_occupancy"],
                        "spatial_cv": cand_entry["loftr_verification"]["spatial_cv"],
                        "n_final_inliers": cand_entry["loftr_verification"]["n_final_inliers"],
                        "gate_min_candidates": gate.get("gate_min_candidates"),
                        "gate_min_initial_inliers": gate.get("gate_min_initial_inliers"),
                        "gate_min_inlier_ratio": gate.get("gate_min_inlier_ratio"),
                        "gate_min_occupancy": gate.get("gate_min_occupancy"),
                        "gate_downstream_min_inliers": gate.get("gate_downstream_min_inliers"),
                        "gate_held_out_valid": gate.get("gate_held_out_valid"),
                        "gate_all_pass": gate.get("gate_all_pass"),
                        "failure_class": gate.get("failure_class"),
                        "held_out_valid": cand_entry["loftr_verification"]["held_out_valid"],
                        "mean_check_rmse": cand_entry["loftr_verification"]["mean_check_rmse"],
                        "fit_rmse": cand_entry["loftr_verification"]["fit_rmse"],
                        "loftr_runtime_s": cand_entry["loftr_verification"]["loftr_runtime_s"],
                    })
                else:
                    # SCREEN_FAIL or INSUFFICIENT_SUPPORT → F1/F2; no LoFTR
                    if decision == "INSUFFICIENT_SUPPORT":
                        cand_entry["failure_class"] = "F1"
                    else:
                        cand_entry["failure_class"] = "F2"
                    cand_entry["loftr_verification"] = None
                    cp.setdefault("candidates", {})[key] = cand_entry
            except Exception as cand_exc:
                cand_entry.update({
                    "stage": "cheap_done",
                    "status": "ERROR",
                    "failure_class": "F2",
                    "error": str(cand_exc),
                    "error_trace": traceback.format_exc(limit=3),
                    "runtime_s": round(time.perf_counter() - t_cand_start, 3),
                })
                cp.setdefault("candidates", {})[key] = cand_entry
                screen_rows.append({
                    "candidate_key": key, "pair_id": pid,
                    "dx_m": dx_m, "dy_m": dy_m,
                    "du_px": cand_entry["du_px"], "dv_px": cand_entry["dv_px"],
                    "decision": "ERROR", "supported_windows": 0, "supported_cells": 0,
                    "error": str(cand_exc),
                })
            save_checkpoint(cp)

        # Per-pair failure classification
        if pair_f5 > 0:
            pf_class = "F5"
            pf_rationale = f"Research-validated candidates exist (F5={pair_f5})."
        elif pair_qg_pass > 0 or pair_initial_qg_pass > 0:
            pf_class = "F4"
            pf_rationale = "Initial geometry passes but full QG / hold-out does not."
        elif pair_loftr > 0:
            pf_class = "F3"
            pf_rationale = "SCREEN_PASS candidates exist but LoFTR correspondence/geometry insufficient."
        elif pair_screen_pass == 0 and pair_insuff == pair_n_coarse:
            pf_class = "F1"
            pf_rationale = "All coarse candidates suffered insufficient reference support."
        elif pair_screen_pass == 0:
            pf_class = "F2"
            pf_rationale = "No coarse structural recovery recovered from any predeclared offset."
        else:
            pf_class = "F2"
            pf_rationale = "No valid classification path; default F2."

        ps_entry = {
            "pair_id": pid,
            "total_candidates": pair_n_coarse,
            "screen_pass": pair_screen_pass,
            "screen_fail": pair_screen_fail,
            "insufficient_support": pair_insuff,
            "loftr_verified": pair_loftr,
            "initial_qg_pass": pair_initial_qg_pass,
            "quality_gate_pass": pair_qg_pass,
            "f5_validated": pair_f5,
            "failure_class": pf_class,
            "failure_rationale": pf_rationale,
            "phase23a6_mean_dx_m": pm["phase23a6_mean_dx_m"],
            "phase23a6_mean_dy_m": pm["phase23a6_mean_dy_m"],
            "phase23a6_mag_m": pm["phase23a6_mag_m"],
        }
        pair_summary_list.append(ps_entry)
        cp.setdefault("pair_summary", {})[pid] = ps_entry
        save_checkpoint(cp)

        print(f"  {pid} coarse={pair_n_coarse} SCREEN_PASS={pair_screen_pass} SCREEN_FAIL={pair_screen_fail} INSUFF={pair_insuff}")
        print(f"    LoFTR={pair_loftr} Initial_QG={pair_initial_qg_pass} Full_QG={pair_qg_pass} F5={pair_f5}")
        print(f"    Class: {pf_class} — {pf_rationale}")

    # ---- Overall classification ----
    total_f5 = sum(p["f5_validated"] for p in pair_summary_list)
    total_qg = sum(p["quality_gate_pass"] for p in pair_summary_list)
    total_initial = sum(p["initial_qg_pass"] for p in pair_summary_list)
    total_screen_pass = sum(p["screen_pass"] for p in pair_summary_list)

    if total_f5 > 0:
        overall = "PREFILTER_RECOVERED_CANDIDATES"
        interp = (
            "At least one deterministic coarse candidate passes the screen and succeeds "
            "through the frozen quality gate and independent hold-out validation. "
            "Research-level relative-registration feasibility is demonstrated under a "
            "predefined image-space placement hypothesis. "
            "This does NOT constitute absolute geolocation, a geodetically-corrected "
            "reference, or reference-product identification."
        )
    elif total_screen_pass == 0:
        overall = "PREFILTER_FOUND_NO_CANDIDATE"
        interp = (
            "No predefined coarse image-space placement showed sufficient cheap structural "
            "evidence under the predeclared deterministic screening rule. "
            "This does NOT imply registration is impossible; it only means the current "
            "prefilter lattice + thresholds did not justify expensive LoFTR verification."
        )
    elif total_qg == 0 and total_screen_pass > 0:
        overall = "VERIFICATION_FAILED"
        interp = (
            "Coarse structural evidence exists at some predefined placements, but reliable "
            "correspondence / geometric consistency was not demonstrated through the frozen "
            "LoFTR quality gate and hold-out validation."
        )
    else:
        overall = "INCONCLUSIVE"
        interp = (
            "Resource, coverage, or implementation limitations prevent a valid Phase 24A "
            "conclusion. The original Phase 24 status remains DEFERRED_COMPUTATIONAL_COST."
        )

    cp["final_classification"] = overall
    cp["classification_interpretation"] = interp
    runtime_total = time.perf_counter() - t_total_start
    cp["total_runtime_s"] = round(runtime_total, 2)
    save_checkpoint(cp)

    # ---- Persist outputs ----
    write_screen_csv(screen_rows, SCREEN_CSV)
    write_loftr_csv(loftr_rows, LOFTR_CSV)
    write_pair_summary_csv(pair_summary_list, PAIR_SUMMARY_CSV)

    with open(SCREEN_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "governance": GOVERNANCE,
            "screen_thresholds": SCREEN_THRESHOLDS,
            "quality_gate": {k: (list(v) if isinstance(v, tuple) else v) for k, v in QG.items()},
            "candidates": [
                {kk: (json.dumps(vv, default=str) if isinstance(vv, (dict, list, tuple, np.ndarray)) else vv)
                 for kk, vv in r.items()}
                for r in screen_rows
            ],
            "counts": {
                "total_coarse": len(screen_rows),
                "screen_pass": total_screen_pass,
                "loftr_verified": len(loftr_rows),
                "initial_qg": total_initial,
                "full_qg": total_qg,
                "hold_out_pass": total_qg,
                "f5": total_f5,
            },
        }, f, indent=2, default=str)

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(render_report(cp, screen_rows, loftr_rows, pair_summary_list, runtime_total))

    with open(FAILURE_MD, "w", encoding="utf-8") as f:
        f.write(render_failure_md(pair_summary_list, loftr_rows, screen_rows))

    # ---- Final summary ----
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total runtime: {runtime_total:.2f} s ({runtime_total/60.0:.1f} min)")
    print(f"Total coarse candidates: {len(screen_rows)}")
    print(f"SCREEN_PASS total       : {total_screen_pass}")
    print(f"LoFTR verified          : {len(loftr_rows)}")
    print(f"Initial QG passes       : {total_initial}")
    print(f"Full QG passes          : {total_qg}")
    print(f"Hold-out / F5 validated : {total_f5}")
    for ps in pair_summary_list:
        print(f"  {ps['pair_id']}: {ps['failure_class']} | SP={ps['screen_pass']} LoFTR={ps['loftr_verified']} QG={ps['quality_gate_pass']} F5={ps['f5_validated']}")
    print(f"\nPhase 24A classification: {overall}")
    print(f"Phase 24 (original)     : {GOVERNANCE['PHASE_24_STATUS']} / {GOVERNANCE['PHASE_24_RESEARCH_RESULT']}")
    print(f"Phase 23B status        : {GOVERNANCE['PHASE_23B_STATUS']} (UNCHANGED)")
    print(f"\nOutputs written to: {OUT_DIR}")
    print(f"  - {SCREEN_CSV.name}")
    print(f"  - {SCREEN_JSON.name}")
    print(f"  - {LOFTR_CSV.name}")
    print(f"  - {PAIR_SUMMARY_CSV.name}")
    print(f"  - {REPORT_MD.name}")
    print(f"  - {FAILURE_MD.name}")
    print(f"  - {CHECKPOINT_FILE.name}")


if __name__ == "__main__":
    main()
