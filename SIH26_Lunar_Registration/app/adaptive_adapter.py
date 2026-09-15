"""
app/adaptive_adapter.py
=======================
Adapter bridging research Adaptive Registration Engine to the Streamlit UI.
"""

import os
import sys
import time
import traceback
from typing import Any, Dict, Optional

import cv2
import numpy as np

# Ensure project root is present in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from registration_core import (
    _DEVICE,
    calculate_spatial_grid,
    compute_matching_scale,
)
from research.adaptive_matcher.adaptive_engine import (
    AdaptiveConfig,
    run_adaptive_registration,
)

__all__ = ["safe_run_adaptive_registration"]


def _validate_registration_images(source_image, reference_image):
    if source_image is None:
        return False, "Source image is missing (None). Please upload or load a valid moving image.", "MissingSourceImage"
    if reference_image is None:
        return False, "Reference image is missing (None). Please upload or load a valid fixed reference image.", "MissingReferenceImage"
    if not isinstance(source_image, np.ndarray):
        return False, f"Source image must be a numpy ndarray, received {type(source_image).__name__}.", "InvalidSourceType"
    if not isinstance(reference_image, np.ndarray):
        return False, f"Reference image must be a numpy ndarray, received {type(reference_image).__name__}.", "InvalidReferenceType"
    if source_image.size == 0:
        return False, "Source image array is empty (0 bytes).", "EmptySourceImage"
    if reference_image.size == 0:
        return False, "Reference image array is empty (0 bytes).", "EmptyReferenceImage"
    if len(source_image.shape) not in (2, 3):
        return False, f"Source image must be 2D or 3D, got shape {source_image.shape}.", "InvalidSourceShape"
    if len(reference_image.shape) not in (2, 3):
        return False, f"Reference image must be 2D or 3D, got shape {reference_image.shape}.", "InvalidReferenceShape"
    s_h, s_w = source_image.shape[:2]
    r_h, r_w = reference_image.shape[:2]
    if s_h < 32 or s_w < 32:
        return False, f"Source image dimensions ({s_w}x{s_h} px) too small. Minimum is 32x32.", "SourceTooSmall"
    if r_h < 32 or r_w < 32:
        return False, f"Reference image dimensions ({r_w}x{r_h} px) too small. Minimum is 32x32.", "ReferenceTooSmall"
    return True, None, None


def _create_match_canvas(source_img: np.ndarray, reference_img: np.ndarray, pts0: np.ndarray, pts1: np.ndarray) -> np.ndarray:
    s_h, s_w = source_img.shape[:2]
    r_h, r_w = reference_img.shape[:2]

    canvas = np.zeros((max(s_h, r_h), s_w + r_w, 3), dtype=np.uint8)
    s_col = cv2.cvtColor(source_img, cv2.COLOR_GRAY2BGR) if len(source_img.shape) == 2 else source_img.copy()
    r_col = cv2.cvtColor(reference_img, cv2.COLOR_GRAY2BGR) if len(reference_img.shape) == 2 else reference_img.copy()
    canvas[:s_h, :s_w] = s_col
    canvas[:r_h, s_w:] = r_col

    circle_radius = max(2, int(min(s_h, s_w, r_h, r_w) / 180))
    line_thickness = max(1, int(min(s_h, s_w, r_h, r_w) / 360))

    if pts0 is not None and pts1 is not None and len(pts0) > 0 and len(pts1) > 0:
        for p0, p1 in zip(pts0, pts1):
            pt0 = (int(round(float(p0[0]))), int(round(float(p0[1]))))
            pt1 = (int(round(float(p1[0]))) + s_w, int(round(float(p1[1]))))
            cv2.line(canvas, pt0, pt1, (0, 255, 255), line_thickness, cv2.LINE_AA)
            cv2.circle(canvas, pt0, circle_radius, (0, 255, 0), -1)
            cv2.circle(canvas, pt1, circle_radius, (0, 0, 255), -1)

    return canvas


def safe_run_adaptive_registration(
    source_image: np.ndarray,
    reference_image: np.ndarray,
    config: Optional[AdaptiveConfig] = None,
    **kwargs
) -> Dict[str, Any]:
    start_time = time.perf_counter()

    # Step 1: Input Validation
    is_valid, err_msg, err_type = _validate_registration_images(source_image, reference_image)
    if not is_valid:
        return {
            "success": False,
            "status": "failed",
            "error_type": err_type,
            "error_message": err_msg,
            "details": err_msg,
            "stage": "input_validation",
            "runtime": float(time.perf_counter() - start_time),
            "primary_matcher": None,
            "final_matcher_used": None,
            "fallback_used": False,
            "fallback_choice": None,
            "fallback_reason": None,
            "fallback_blocked": False,
            "blocked_fallbacks": [],
            "difficulty_profile": None,
            "routing_decision": None,
            "quality_gate": None,
            "fit_rmse": None,
            "check_rmse": None,
            "final_homography": None,
            "registered_image": None,
            "inlier_points": None,
            "spatial_occupancy": None,
            "spatial_cv": None,
            "adaptive_raw": None,
        }

    # Step 2: Execute Research Adaptive Engine
    loftr_model = kwargs.get("loftr_model", None)
    sg_model = kwargs.get("sg_model", None)
    try:
        adaptive_res = run_adaptive_registration(
            source_image,
            reference_image,
            loftr_model=loftr_model,
            sg_model=sg_model,
            config=config,
        )
    except Exception as e:
        elapsed = float(time.perf_counter() - start_time)
        return {
            "success": False,
            "status": "failed",
            "error_type": "AdaptiveRegistrationRuntimeError",
            "error_message": f"Adaptive registration sequence halted: {str(e)}",
            "details": traceback.format_exc(),
            "stage": "adaptive_execution",
            "runtime": elapsed,
            "primary_matcher": None,
            "final_matcher_used": None,
            "fallback_used": False,
            "fallback_choice": None,
            "fallback_reason": None,
            "fallback_blocked": False,
            "blocked_fallbacks": [],
            "difficulty_profile": None,
            "routing_decision": None,
            "quality_gate": None,
            "fit_rmse": None,
            "check_rmse": None,
            "final_homography": None,
            "registered_image": None,
            "inlier_points": None,
            "spatial_occupancy": None,
            "spatial_cv": None,
            "adaptive_raw": None,
        }

    elapsed = float(time.perf_counter() - start_time)

    # Step 3: Handle Adaptive Failure
    if not adaptive_res.get("success", False):
        q_gate = adaptive_res.get("quality_gate", {})
        q_reasons = q_gate.get("reasons", []) if isinstance(q_gate, dict) else []
        fail_reason = adaptive_res.get("failure_reason", "Adaptive registration failed quality gate.")

        fallback_used = bool(adaptive_res.get("fallback_used", False))
        fallback_choice = adaptive_res.get("fallback_choice")
        fallback_blocked = bool(adaptive_res.get("fallback_blocked", False))
        blocked_fallbacks = adaptive_res.get("blocked_fallbacks", [])
        fallback_status_str = "BLOCKED — RESOURCE POLICY" if fallback_blocked else ("TRIGGERED" if fallback_used else "NONE")

        details_lines = [
            f"Primary Matcher: {adaptive_res.get('primary_choice')}",
            f"Fallback Used: {fallback_used}",
            f"Fallback Status: {fallback_status_str}",
        ]
        if fallback_blocked:
            details_lines.append(f"Blocked Fallbacks: {', '.join(blocked_fallbacks)}")
        if fallback_choice is not None:
            details_lines.append(f"Fallback Choice: {fallback_choice}")
        if adaptive_res.get("fallback_reason"):
            details_lines.append(f"Fallback Reason: {adaptive_res.get('fallback_reason')}")
        details_lines.append(f"Failure Reason: {fail_reason}")
        if q_reasons:
            details_lines.append(f"Quality Gate: {'; '.join(q_reasons)}")

        return {
            "success": False,
            "status": "failed",
            "error_type": "AdaptiveQualityGateFailed" if q_reasons else "AdaptiveRegistrationFailed",
            "error_message": fail_reason,
            "details": "\n".join(details_lines),
            "stage": "quality_gate" if (fallback_used or fallback_blocked) else "matcher_execution",
            "runtime": float(adaptive_res.get("runtime", elapsed)),
            "primary_matcher": adaptive_res.get("primary_choice"),
            "final_matcher_used": adaptive_res.get("final_matcher_used"),
            "fallback_used": fallback_used,
            "fallback_choice": fallback_choice,
            "fallback_reason": adaptive_res.get("fallback_reason"),
            "fallback_blocked": fallback_blocked,
            "blocked_fallbacks": blocked_fallbacks,
            "difficulty_profile": adaptive_res.get("difficulty_profile"),
            "routing_decision": adaptive_res.get("decision"),
            "quality_gate": q_gate,
            "fit_rmse": None,
            "check_rmse": None,
            "final_homography": None,
            "registered_image": None,
            "inlier_points": None,
            "spatial_occupancy": None,
            "spatial_cv": None,
            "confidences": adaptive_res.get("primary_result", {}).get("confidences") if isinstance(adaptive_res.get("primary_result"), dict) else None,
            "adaptive_raw": adaptive_res,
            "scale_source": float(compute_matching_scale(source_image.shape[:2], max_dim=1600, max_budget=1800000)[0]) if adaptive_res.get("primary_choice") == "LoFTR" else 1.0,
            "scale_ref": float(compute_matching_scale(reference_image.shape[:2], max_dim=1600, max_budget=1800000)[0]) if adaptive_res.get("primary_choice") == "LoFTR" else 1.0,
            "orig_source_shape": (source_image.shape[0], source_image.shape[1]),
            "orig_ref_shape": (reference_image.shape[0], reference_image.shape[1]),
            "match_source_shape": (compute_matching_scale(source_image.shape[:2], max_dim=1600, max_budget=1800000)[2], compute_matching_scale(source_image.shape[:2], max_dim=1600, max_budget=1800000)[1]) if adaptive_res.get("primary_choice") == "LoFTR" else (source_image.shape[0], source_image.shape[1]),
            "match_ref_shape": (compute_matching_scale(reference_image.shape[:2], max_dim=1600, max_budget=1800000)[2], compute_matching_scale(reference_image.shape[:2], max_dim=1600, max_budget=1800000)[1]) if adaptive_res.get("primary_choice") == "LoFTR" else (reference_image.shape[0], reference_image.shape[1]),
            "resizing_applied": bool(compute_matching_scale(source_image.shape[:2], max_dim=1600, max_budget=1800000)[0] < 1.0 or compute_matching_scale(reference_image.shape[:2], max_dim=1600, max_budget=1800000)[0] < 1.0) if adaptive_res.get("primary_choice") == "LoFTR" else False,
        }

    # Step 4: Normalize Successful Registration Output
    downstream = adaptive_res.get("downstream", {})
    s_h, s_w = source_image.shape[:2]
    r_h, r_w = reference_image.shape[:2]

    H_final = downstream.get("H_final")
    warped_image = downstream.get("warped_image")
    final_pts0 = downstream.get("final_pts0", np.empty((0, 2), dtype=np.float32))
    final_pts1 = downstream.get("final_pts1", np.empty((0, 2), dtype=np.float32))
    selected_pts0 = downstream.get("selected_pts0", final_pts0)
    selected_pts1 = downstream.get("selected_pts1", final_pts1)

    selected_grid = calculate_spatial_grid(selected_pts0, (s_h, s_w))
    occupied_cells = int(np.count_nonzero(selected_grid))
    total_cells = 9
    occupancy_ratio = float(occupied_cells / total_cells)
    spatial_cv = float(downstream.get("spatial_cv", 0.0))

    fit_rmse = float(downstream.get("fit_rmse", 0.0))
    if len(final_pts0) > 0 and H_final is not None:
        proj = cv2.perspectiveTransform(final_pts0.reshape(-1, 1, 2), H_final).reshape(-1, 2)
        final_errs = np.linalg.norm(proj - final_pts1, axis=1)
        rmse = float(np.sqrt(np.mean(final_errs**2))) if len(final_errs) > 0 else fit_rmse
        mean_err = float(np.mean(final_errs)) if len(final_errs) > 0 else 0.0
        median_err = float(np.median(final_errs)) if len(final_errs) > 0 else 0.0
        max_err = float(np.max(final_errs)) if len(final_errs) > 0 else 0.0
    else:
        rmse = fit_rmse
        mean_err = fit_rmse
        median_err = fit_rmse
        max_err = fit_rmse

    active_result = adaptive_res.get("fallback_result") if adaptive_res.get("fallback_used") else adaptive_res.get("primary_result")
    if active_result and isinstance(active_result, dict):
        cand_matches = int(active_result.get("n_candidates", len(selected_pts0)))
        init_inliers = int(active_result.get("n_inliers", len(final_pts0)))
        init_ratio = float(active_result.get("inlier_ratio", init_inliers / max(1, cand_matches)))
    else:
        cand_matches = int(downstream.get("n_selected", len(selected_pts0)))
        init_inliers = int(downstream.get("n_final_inliers", len(final_pts0)))
        init_ratio = float(downstream.get("final_inlier_ratio", 1.0))

    match_canvas = _create_match_canvas(source_image, reference_image, final_pts0, final_pts1)

    final_matcher = adaptive_res.get("final_matcher_used", adaptive_res.get("primary_choice", "LoFTR"))
    if final_matcher == "LoFTR":
        scale_s, s_wm, s_hm = compute_matching_scale((s_h, s_w), max_dim=1600, max_budget=1800000)
        scale_r, r_wm, r_hm = compute_matching_scale((r_h, r_w), max_dim=1600, max_budget=1800000)
    else:
        scale_s = 1.0
        scale_r = 1.0
        s_wm, s_hm = s_w, s_h
        r_wm, r_hm = r_w, r_h

    homography_list = H_final.tolist() if isinstance(H_final, np.ndarray) else H_final

    raw_check_rmse = downstream.get("mean_check_rmse")
    if raw_check_rmse is not None and isinstance(raw_check_rmse, (int, float)) and not np.isnan(raw_check_rmse):
        check_rmse = float(raw_check_rmse)
    else:
        check_rmse = None

    raw_median_check = downstream.get("median_check_rmse")
    if raw_median_check is not None and isinstance(raw_median_check, (int, float)) and not np.isnan(raw_median_check):
        median_check_rmse = float(raw_median_check)
    else:
        median_check_rmse = None

    raw_max_check = downstream.get("max_check_error")
    if raw_max_check is not None and isinstance(raw_max_check, (int, float)) and not np.isnan(raw_max_check):
        max_check_error = float(raw_max_check)
    else:
        max_check_error = None

    held_out_valid = bool(downstream.get("held_out_valid", False))

    return {
        "success": True,
        "status": "success",
        "primary_matcher": adaptive_res.get("primary_choice"),
        "final_matcher_used": final_matcher,
        "fallback_used": bool(adaptive_res.get("fallback_used", False)),
        "fallback_choice": adaptive_res.get("fallback_choice"),
        "fallback_reason": adaptive_res.get("fallback_reason"),
        "fallback_blocked": bool(adaptive_res.get("fallback_blocked", False)),
        "blocked_fallbacks": adaptive_res.get("blocked_fallbacks", []),
        "difficulty_profile": adaptive_res.get("difficulty_profile"),
        "routing_decision": adaptive_res.get("decision"),
        "quality_gate": adaptive_res.get("quality_gate"),
        "fit_rmse": float(fit_rmse),
        "check_rmse": check_rmse,
        "median_check_rmse": median_check_rmse,
        "max_check_error": max_check_error,
        "held_out_valid": held_out_valid,
        "final_homography": H_final,
        "registered_image": warped_image,
        "inlier_points": {"pts0": final_pts0, "pts1": final_pts1},
        "spatial_occupancy": float(downstream.get("spatial_occupancy", occupancy_ratio)),
        "spatial_cv": float(spatial_cv),
        "runtime": float(adaptive_res.get("runtime", elapsed)),
        "confidences": active_result.get("confidences") if (active_result and isinstance(active_result, dict)) else None,
        "adaptive_raw": adaptive_res,
        # Downstream UI compatibility fields
        "device": _DEVICE,
        "homography_matrix": homography_list,
        "match_visualization": match_canvas,
        "selected_grid": selected_grid,
        "occupied_cells": occupied_cells,
        "total_cells": total_cells,
        "occupancy_ratio": occupancy_ratio,
        "candidate_matches": cand_matches,
        "initial_inliers": init_inliers,
        "initial_inlier_ratio": init_ratio,
        "selected_matches": int(downstream.get("n_selected", len(selected_pts0))),
        "final_inliers": int(downstream.get("n_final_inliers", len(final_pts0))),
        "final_inlier_ratio": float(downstream.get("final_inlier_ratio", 0.0)),
        "rmse": float(rmse),
        "mean_error": float(mean_err),
        "median_error": float(median_err),
        "max_error": float(max_err),
        "scale_source": float(scale_s),
        "scale_ref": float(scale_r),
        "orig_source_shape": (s_h, s_w),
        "orig_ref_shape": (r_h, r_w),
        "match_source_shape": (s_hm, s_wm),
        "match_ref_shape": (r_hm, r_wm),
        "resizing_applied": bool(scale_s < 1.0 or scale_r < 1.0),
    }
