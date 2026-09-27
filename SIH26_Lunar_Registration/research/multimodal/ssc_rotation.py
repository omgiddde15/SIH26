"""
LunarReg Phase 9 — Rotation-Normalized SSC-Style Research Branch.

Research-only extension of the frozen Phase 7 SSC-style descriptor.

Key invariants:
- Reuses the exact Phase 7/8 Sobel-gradient + FAST keypoints.
- Keeps the 21-D SSC descriptor geometry and matching policy unchanged.
- Adds only a local structure-tensor orientation estimate before sampling the
  six-neighbour constellation.
- Uses the empirically verified pixel-coordinate convention R(+theta) for
  rotating the sampling offsets. The convention is validated by the separate
  synthetic sign-sanity test in this module.
- Uses no RIFT2 / Log-Gabor / Phase Congruency / MIM components.
- Keeps common downstream registration unchanged.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from research.multimodal.ssc_matcher import (
    SSCConfig,
    compute_ssc_offsets,
    detect_ssc_keypoints,
    get_ssc_pair_indices,
    match_ssc_descriptors,
)
from research.multimodal.scale_search import map_points_to_original
from research.adaptive_matcher.adaptive_engine import execute_common_downstream


@dataclass
class SSCRotationConfig:
    """Frozen Phase 7 SSC settings plus fixed orientation-estimation settings."""

    ssc: SSCConfig = field(default_factory=SSCConfig)
    tensor_window: int = 7
    tensor_sigma: float = 1.5
    coherence_threshold: float = 0.15
    trace_threshold: float = 1e-4
    # Pixel-coordinate convention verified by the synthetic sign sanity check.
    orientation_sign: float = 1.0
    orientation_convention: str = "R(+theta) in image pixel coordinates"

    @property
    def orientation_parameters(self) -> str:
        return (
            f"Sobel(k=3); Gaussian({self.tensor_window}x{self.tensor_window}, "
            f"sigma={self.tensor_sigma}); coherence<{self.coherence_threshold} "
            f"or trace<{self.trace_threshold} -> theta=0; "
            f"offset rotation={self.orientation_sign:+.0f}theta"
        )


def _validate_orientation_window(window: int) -> None:
    if window <= 0 or window % 2 == 0:
        raise ValueError("tensor_window must be a positive odd integer.")


def compute_structure_tensor_fields(
    img_gray: np.ndarray,
    window: int = 7,
    sigma: float = 1.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Sobel derivatives and Gaussian-smoothed structure-tensor terms."""
    _validate_orientation_window(window)
    if img_gray is None or not isinstance(img_gray, np.ndarray) or img_gray.size == 0:
        raise ValueError("img_gray must be a non-empty numpy array.")

    img_f = img_gray.astype(np.float32) / 255.0
    ix = cv2.Sobel(img_f, cv2.CV_32F, 1, 0, ksize=3)
    iy = cv2.Sobel(img_f, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(ix * ix, (window, window), sigma)
    jyy = cv2.GaussianBlur(iy * iy, (window, window), sigma)
    jxy = cv2.GaussianBlur(ix * iy, (window, window), sigma)
    return jxx, jyy, jxy


def estimate_keypoint_orientations(
    img_gray: np.ndarray,
    pts: np.ndarray,
    config: Optional[SSCRotationConfig] = None,
) -> Tuple[np.ndarray, List[Dict[str, float | str]]]:
    """Estimate a deterministic local orientation and coherence per keypoint.

    Orientation uses the principal axis of the local gradient structure tensor:
        theta = 0.5 * atan2(2 Jxy, Jxx - Jyy)

    For flat or low-coherence points the frozen Phase 7 theta=0 convention is
    used and the status is recorded instead of inventing an orientation.
    """
    if config is None:
        config = SSCRotationConfig()

    pts = np.asarray(pts, dtype=np.float32)
    if pts.ndim != 2 or (pts.shape[1] if pts.size else 2) != 2:
        raise ValueError("pts must have shape (N, 2).")

    jxx, jyy, jxy = compute_structure_tensor_fields(
        img_gray,
        window=config.tensor_window,
        sigma=config.tensor_sigma,
    )

    thetas = np.zeros((len(pts),), dtype=np.float32)
    stats: List[Dict[str, float | str]] = []

    for idx, pt in enumerate(pts):
        x, y = float(pt[0]), float(pt[1])
        a = float(cv2.getRectSubPix(jxx, (1, 1), (x, y))[0, 0])
        b = float(cv2.getRectSubPix(jyy, (1, 1), (x, y))[0, 0])
        c = float(cv2.getRectSubPix(jxy, (1, 1), (x, y))[0, 0])

        trace = a + b
        delta = math.sqrt(max(0.0, (a - b) ** 2 + 4.0 * c * c))
        coherence = delta / (trace + 1e-6)

        if trace < config.trace_threshold:
            status = "flat"
            theta = 0.0
        elif coherence < config.coherence_threshold:
            status = "low_confidence"
            theta = 0.0
        else:
            status = "valid"
            theta = 0.5 * math.atan2(2.0 * c, a - b)

        thetas[idx] = np.float32(theta)
        stats.append(
            {
                "status": status,
                "theta_rad": float(theta),
                "theta_deg": float(np.degrees(theta)),
                "coherence": float(coherence),
                "trace": float(trace),
            }
        )

    return thetas, stats


def rotate_ssc_offsets(
    base_offsets: np.ndarray,
    theta: float,
    orientation_sign: float = 1.0,
) -> np.ndarray:
    """Rotate sampling offsets under the frozen pixel-coordinate convention."""
    signed_theta = float(orientation_sign) * float(theta)
    c = math.cos(signed_theta)
    s = math.sin(signed_theta)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    return (rot @ np.asarray(base_offsets, dtype=np.float32).T).T.astype(np.float32)


def compute_rotation_normalized_ssc_descriptors(
    img_gray: np.ndarray,
    pts: np.ndarray,
    config: Optional[SSCRotationConfig] = None,
    return_stats: bool = True,
) -> Tuple[np.ndarray, List[Dict[str, float | str]]]:
    """Compute the frozen 21-D SSC descriptor with locally rotated sampling."""
    if config is None:
        config = SSCRotationConfig()

    pts = np.asarray(pts, dtype=np.float32)
    n_pts = len(pts)
    n_dim = config.ssc.descriptor_dimension
    if n_dim != 21:
        raise ValueError("Phase 9 requires the frozen 21-D SSC descriptor.")
    if n_pts == 0:
        return np.empty((0, n_dim), dtype=np.float32), []

    img_f = img_gray.astype(np.float32) / 255.0
    base_offsets = compute_ssc_offsets(
        radius=config.ssc.radius,
        angles=config.ssc.angles,
    )
    pair_indices = get_ssc_pair_indices()
    patch_size = (config.ssc.patch_size, config.ssc.patch_size)
    eps = config.ssc.epsilon

    thetas, orientation_stats = estimate_keypoint_orientations(img_gray, pts, config)
    descs = np.zeros((n_pts, n_dim), dtype=np.float32)

    for idx, pt in enumerate(pts):
        x, y = float(pt[0]), float(pt[1])
        offsets = rotate_ssc_offsets(
            base_offsets,
            float(thetas[idx]),
            orientation_sign=config.orientation_sign,
        )
        patches = [
            cv2.getRectSubPix(
                img_f,
                patch_size,
                (x + float(offsets[k, 0]), y + float(offsets[k, 1])),
            )
            for k in range(7)
        ]

        d = np.zeros(n_dim, dtype=np.float32)
        for p_idx, (pi, pj) in enumerate(pair_indices):
            diff = patches[pi] - patches[pj]
            d[p_idx] = float(np.mean(diff ** 2))

        v = float(np.median(d)) + eps
        s = np.exp(-d / v)
        norm = float(np.linalg.norm(s))
        if norm > 1e-6:
            descs[idx] = s / norm

    return descs, orientation_stats if return_stats else []


def summarize_orientation_stats(stats: List[Dict[str, float | str]]) -> Dict[str, float | int]:
    """Return source/reference-independent counts and basic orientation statistics."""
    counts = {"valid": 0, "low_confidence": 0, "flat": 0}
    theta_valid: List[float] = []
    coherence_valid: List[float] = []
    for item in stats:
        status = str(item["status"])
        counts[status] = counts.get(status, 0) + 1
        if status == "valid":
            theta_valid.append(float(item["theta_deg"]))
            coherence_valid.append(float(item["coherence"]))

    theta_arr = np.asarray(theta_valid, dtype=np.float32)
    coh_arr = np.asarray(coherence_valid, dtype=np.float32)
    return {
        "valid_count": counts.get("valid", 0),
        "low_confidence_count": counts.get("low_confidence", 0),
        "flat_count": counts.get("flat", 0),
        "valid_fraction": round(counts.get("valid", 0) / max(1, len(stats)), 6),
        "valid_theta_mean_deg": round(float(theta_arr.mean()), 6) if len(theta_arr) else 0.0,
        "valid_theta_std_deg": round(float(theta_arr.std()), 6) if len(theta_arr) else 0.0,
        "valid_coherence_mean": round(float(coh_arr.mean()), 6) if len(coh_arr) else 0.0,
    }


def run_ssc_rotation_matching(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    scale_source: float = 1.0,
    scale_reference: float = 1.0,
    config: Optional[SSCRotationConfig] = None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    pair_label: str = "custom_pair",
) -> Dict[str, Any]:
    """Run Phase 9 rotation-normalized SSC candidate generation and unchanged downstream."""
    if config is None:
        config = SSCRotationConfig()

    t_start = time.perf_counter()
    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if source_img.ndim == 3 else source_img.copy()
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if reference_img.ndim == 3 else reference_img.copy()

    orig_s_h, orig_s_w = s_gray.shape
    orig_r_h, orig_r_w = r_gray.shape

    if scale_source < 1.0:
        sw, sh = max(64, int(round(orig_s_w * scale_source))), max(64, int(round(orig_s_h * scale_source)))
        s_work = cv2.resize(s_gray, (sw, sh), interpolation=cv2.INTER_AREA)
    else:
        sw, sh = orig_s_w, orig_s_h
        s_work = s_gray

    if scale_reference < 1.0:
        rw, rh = max(64, int(round(orig_r_w * scale_reference))), max(64, int(round(orig_r_h * scale_reference)))
        r_work = cv2.resize(r_gray, (rw, rh), interpolation=cv2.INTER_AREA)
    else:
        rw, rh = orig_r_w, orig_r_h
        r_work = r_gray

    pts_s, raw_s = detect_ssc_keypoints(
        s_work,
        max_kps=config.ssc.max_keypoints,
        fast_threshold=config.ssc.fast_threshold,
        margin=config.ssc.margin,
    )
    pts_r, raw_r = detect_ssc_keypoints(
        r_work,
        max_kps=config.ssc.max_keypoints,
        fast_threshold=config.ssc.fast_threshold,
        margin=config.ssc.margin,
    )

    desc_s, orient_s = compute_rotation_normalized_ssc_descriptors(s_work, pts_s, config)
    desc_r, orient_r = compute_rotation_normalized_ssc_descriptors(r_work, pts_r, config)

    match = match_ssc_descriptors(
        pts_s, desc_s, pts_r, desc_r, nndr_threshold=config.ssc.nndr_threshold
    )
    n_cands = int(match["n_candidates"])

    rec: Dict[str, Any] = {
        "pair": pair_label,
        "method": "Rotation-normalized SSC-style 2-D adaptation",
        "detector_name": config.ssc.detector_name,
        "detector_parameters": config.ssc.detector_parameters,
        "descriptor": config.ssc.descriptor_name,
        "descriptor_dimension": 21,
        "orientation_estimator": "Sobel structure tensor",
        "orientation_parameters": config.orientation_parameters,
        "orientation_convention": config.orientation_convention,
        "coherence_threshold": config.coherence_threshold,
        "trace_threshold": config.trace_threshold,
        "scale": f"{scale_source:.2f} / {scale_reference:.2f}",
        "source_scale": scale_source,
        "reference_scale": scale_reference,
        "base_keypoints_source": int(raw_s),
        "base_keypoints_reference": int(raw_r),
        "valid_keypoints_source": int(len(pts_s)),
        "valid_keypoints_reference": int(len(pts_r)),
        "source_orientation": summarize_orientation_stats(orient_s),
        "reference_orientation": summarize_orientation_stats(orient_r),
        "raw_queries": int(match["n_raw_queries"]),
        "nndr_matches": int(match["n_nndr_matches"]),
        "mutual_matches": int(match["n_mutual_matches"]),
        "candidates": n_cands,
        "initial_inliers": 0,
        "initial_inlier_ratio": 0.0,
        "spatial_occupancy": 0.0,
        "spatial_cv": 0.0,
        "fit_rmse": np.nan,
        "independent_held_out_rmse": np.nan,
        "success": False,
        "failure_stage": match.get("failure_stage"),
        "failure_reason": match.get("failure_reason"),
        "match_result": match,
        "downstream_result": None,
        "rift2_dependency": "None",
    }

    if n_cands < 4:
        rec["failure_stage"] = "descriptor_matching"
        rec["failure_reason"] = f"Insufficient candidates ({n_cands} < 4)"
        rec["total_runtime"] = round(time.perf_counter() - t_start, 3)
        return rec

    pts0_native = map_points_to_original(
        match["pts0"], (sh, sw), (orig_s_h, orig_s_w)
    )
    pts1_native = map_points_to_original(
        match["pts1"], (rh, rw), (orig_r_h, orig_r_w)
    )

    try:
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
        rec["downstream_result"] = down
        init_inl = int(down.get("n_initial_inliers", down.get("n_final_inliers", 0)))
        fit_rmse = down.get("fit_rmse")
        held_rmse = down.get("mean_check_rmse")
        held_valid = bool(down.get("held_out_valid", False))

        rec["initial_inliers"] = init_inl
        rec["initial_inlier_ratio"] = round(init_inl / max(1, n_cands), 4)
        rec["spatial_occupancy"] = round(float(down.get("spatial_occupancy", 0.0)), 4)
        rec["spatial_cv"] = round(float(down.get("spatial_cv", 0.0)), 4)
        rec["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
        rec["independent_held_out_rmse"] = round(float(held_rmse), 4) if held_rmse is not None and not np.isnan(held_rmse) else np.nan

        if held_valid and held_rmse is not None and not np.isnan(held_rmse):
            rec["success"] = True
            rec["failure_stage"] = None
            rec["failure_reason"] = None
        else:
            rec["failure_stage"] = "held_out_validation"
            rec["failure_reason"] = f"Insufficient inliers for independent held-out check ({init_inl} < 8)"
    except Exception as exc:
        rec["failure_stage"] = "common_downstream"
        rec["failure_reason"] = str(exc)

    rec["total_runtime"] = round(time.perf_counter() - t_start, 3)
    return rec


def _synthetic_orientation_test_image(size: int = 100, angle_deg: float = 30.0) -> np.ndarray:
    y, x = np.mgrid[-size // 2:size // 2, -size // 2:size // 2]
    coord = x * np.cos(np.radians(angle_deg)) + y * np.sin(np.radians(angle_deg))
    return np.clip(128.0 + 100.0 * np.sin(coord / 5.0), 0, 255).astype(np.uint8)


def _orientation_only_descriptor(
    img: np.ndarray,
    pt: Tuple[float, float],
    theta: float,
    sign: float,
    ssc: SSCConfig,
) -> np.ndarray:
    base_offsets = compute_ssc_offsets(radius=ssc.radius, angles=ssc.angles)
    offsets = rotate_ssc_offsets(base_offsets, theta, orientation_sign=sign)
    img_f = img.astype(np.float32) / 255.0
    patches = [
        cv2.getRectSubPix(
            img_f,
            (ssc.patch_size, ssc.patch_size),
            (pt[0] + float(o[0]), pt[1] + float(o[1])),
        )
        for o in offsets
    ]
    d = np.asarray(
        [np.mean((patches[i] - patches[j]) ** 2) for i, j in get_ssc_pair_indices()],
        dtype=np.float32,
    )
    v = float(np.median(d)) + ssc.epsilon
    s = np.exp(-d / v)
    return s / (np.linalg.norm(s) + 1e-6)


def run_orientation_sign_sanity() -> Dict[str, Any]:
    """Validate the image-coordinate rotation convention before full Phase 9 execution."""
    img = _synthetic_orientation_test_image()
    center = (50.0, 50.0)
    matrix = cv2.getRotationMatrix2D(center, 20.0, 1.0)
    rotated = cv2.warpAffine(
        img,
        matrix,
        (img.shape[1], img.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )

    cfg = SSCRotationConfig()
    theta0, stats0 = estimate_keypoint_orientations(img, np.asarray([center], np.float32), cfg)
    theta1, stats1 = estimate_keypoint_orientations(rotated, np.asarray([center], np.float32), cfg)
    angle_change = float(np.degrees(theta1[0] - theta0[0]))

    d_plus0 = _orientation_only_descriptor(img, center, float(theta0[0]), +1.0, cfg.ssc)
    d_plus1 = _orientation_only_descriptor(rotated, center, float(theta1[0]), +1.0, cfg.ssc)
    d_minus0 = _orientation_only_descriptor(img, center, float(theta0[0]), -1.0, cfg.ssc)
    d_minus1 = _orientation_only_descriptor(rotated, center, float(theta1[0]), -1.0, cfg.ssc)

    plus_distance = float(np.linalg.norm(d_plus0 - d_plus1))
    minus_distance = float(np.linalg.norm(d_minus0 - d_minus1))

    # Expected pixel-coordinate convention: OpenCV +20 deg causes the tensor
    # angle to change by approximately -20 deg. R(+theta) then compensates the
    # sampling frame in the image-coordinate system.
    passed = (
        abs(angle_change + 20.0) < 1.0
        and plus_distance < minus_distance
        and plus_distance < 0.05
    )

    return {
        "synthetic_rotation_deg": 20.0,
        "theta_original_deg": float(np.degrees(theta0[0])),
        "theta_rotated_deg": float(np.degrees(theta1[0])),
        "theta_change_deg": angle_change,
        "R_plus_theta_descriptor_distance": plus_distance,
        "R_minus_theta_descriptor_distance": minus_distance,
        "selected_convention": "R(+theta) in image pixel coordinates" if passed else "UNRESOLVED",
        "status": "PASS" if passed else "FAIL",
        "original_orientation_status": stats0[0]["status"],
        "rotated_orientation_status": stats1[0]["status"],
    }


__all__ = [
    "SSCRotationConfig",
    "compute_structure_tensor_fields",
    "estimate_keypoint_orientations",
    "rotate_ssc_offsets",
    "compute_rotation_normalized_ssc_descriptors",
    "summarize_orientation_stats",
    "run_ssc_rotation_matching",
    "run_orientation_sign_sanity",
]
