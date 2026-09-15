"""
PHASE C: ADAPTIVE MATCHER v1
SIH26166 — Automated Lunar Image Registration

Exploratory, explainable, rule-based adaptive matcher router comparing:
  - SIFT
  - LoFTR
  - SuperGlue

Pipeline:
  Image Characterization
  -> Difficulty Profiling (Exploratory)
  -> Configurable Rule-based Router
  -> Primary Matcher
  -> Quality Gate
  -> Fallback Recovery (if needed)
  -> Common Downstream Registration Layer (RANSAC + Quality + 3x3 Spatial Selection + Warp + Validation)

DISCLAIMER:
All characterization heuristics and routing rules are exploratory heuristics
derived from validation experiments and are NOT claimed as universally optimal.
"""

import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
import torch
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
APP_DIR = os.path.join(PROJECT_ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
SUPERGLUE_REPO = os.path.join(PROJECT_ROOT, "research", "superglue_repo")
if SUPERGLUE_REPO not in sys.path:
    sys.path.insert(0, SUPERGLUE_REPO)

from registration_core import (
    preprocess_image,
    compute_matching_scale,
    calculate_spatial_grid,
    split_spatially_balanced,
    load_loftr_matcher,
    _DEVICE
)
from models.matching import Matching

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class AdaptiveConfig:
    """Configurable experimental thresholds for the Adaptive Matcher Router."""
    # Resolution thresholds
    small_res_threshold: int = 600          # max(W, H) < 600 -> SMALL
    large_res_threshold: int = 2000         # max(W, H) > 2000 -> LARGE
    small_mp_threshold: float = 0.35        # total MP < 0.35 -> SMALL
    large_mp_threshold: float = 1.8         # total MP > 1.8 -> LARGE

    # Contrast thresholds (intensity standard deviation)
    low_contrast_threshold: float = 20.0    # std < 20.0 -> LOW
    high_contrast_threshold: float = 35.0   # std > 35.0 -> HIGH

    # Texture thresholds (gradient magnitude mean)
    low_texture_threshold: float = 8.0      # gradient mean < 8.0 -> LOW
    high_texture_threshold: float = 18.0    # gradient mean > 18.0 -> HIGH
    low_gradient_fraction_threshold: float = 0.60  # > 60% low gradient -> LOW texture

    # Scale difference thresholds
    normal_scale_min: float = 0.80
    normal_scale_max: float = 1.25

    # Quality gate thresholds
    min_candidate_matches: int = 10
    min_initial_inliers: int = 8
    min_inlier_ratio: float = 0.20
    min_spatial_occupancy: float = 0.33
    ransac_threshold: float = 3.0


def characterize_image(image: np.ndarray, name: str = "image") -> Dict[str, Any]:
    """
    Step 1: Calculates measurable, factual image characteristics without fabricating metadata.
    """
    if image is None or image.size == 0:
        raise ValueError(f"Image '{name}' is None or empty.")

    h, w = image.shape[:2]
    total_pixels = int(h * w)
    aspect_ratio = round(float(w) / float(h), 4)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Photometric intensity stats
    mean_intensity = float(np.mean(gray))
    intensity_std = float(np.std(gray))

    # Local contrast estimate: mean std dev of 32x32 local patches
    patch_size = 32
    h_patches = h // patch_size
    w_patches = w // patch_size
    if h_patches > 0 and w_patches > 0:
        cropped = gray[:h_patches * patch_size, :w_patches * patch_size]
        blocks = cropped.reshape(h_patches, patch_size, w_patches, patch_size).swapaxes(1, 2)
        local_stds = np.std(blocks, axis=(2, 3))
        local_contrast = float(np.mean(local_stds))
    else:
        local_contrast = intensity_std

    # Gradient magnitude via Sobel (float32)
    sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)

    gradient_mean = float(np.mean(grad_mag))
    gradient_std = float(np.std(grad_mag))

    # Simple texture density: Laplacian variance (high-frequency energy)
    laplacian = cv2.Laplacian(gray, cv2.CV_32F)
    texture_density = float(np.var(laplacian))

    # Fraction of low-gradient pixels (flat or low-texture regions where gradient < 5.0)
    low_grad_count = int(np.count_nonzero(grad_mag < 5.0))
    low_gradient_fraction = float(low_grad_count / total_pixels)

    return {
        "name": name,
        "width": int(w),
        "height": int(h),
        "total_pixels": total_pixels,
        "megapixels": round(total_pixels / 1e6, 4),
        "aspect_ratio": aspect_ratio,
        "mean_intensity": round(mean_intensity, 2),
        "intensity_std": round(intensity_std, 2),
        "local_contrast": round(local_contrast, 2),
        "gradient_mean": round(gradient_mean, 2),
        "gradient_std": round(gradient_std, 2),
        "texture_density": round(texture_density, 2),
        "low_gradient_fraction": round(low_gradient_fraction, 4),
    }


def compute_pair_characteristics(source_img: np.ndarray, reference_img: np.ndarray) -> Dict[str, Any]:
    """
    Computes pairwise characteristics combining source and reference measurements.
    """
    src_chars = characterize_image(source_img, name="source")
    ref_chars = characterize_image(reference_img, name="reference")

    scale_ratio = float(np.sqrt((src_chars["total_pixels"]) / float(ref_chars["total_pixels"])))

    return {
        "source": src_chars,
        "reference": ref_chars,
        "scale_ratio": round(scale_ratio, 4),
        "approx_illumination_diff": "unknown",
        "viewpoint_diff": "unknown",
        "label": "Exploratory image characterization",
    }


def classify_difficulty_profile(pair_chars: Dict[str, Any], config: Optional[AdaptiveConfig] = None) -> Dict[str, Any]:
    """
    Step 2: Classifies the image pair into explainable difficulty classes.
    """
    if config is None:
        config = AdaptiveConfig()

    src = pair_chars["source"]
    ref = pair_chars["reference"]

    max_dim = max(src["width"], src["height"], ref["width"], ref["height"])
    max_mp = max(src["megapixels"], ref["megapixels"])
    min_std = min(src["intensity_std"], ref["intensity_std"])
    min_grad = min(src["gradient_mean"], ref["gradient_mean"])
    max_low_grad = max(src["low_gradient_fraction"], ref["low_gradient_fraction"])
    scale_ratio = pair_chars["scale_ratio"]

    # Resolution Class
    if max_dim < config.small_res_threshold or max_mp < config.small_mp_threshold:
        resolution_class = "SMALL"
    elif max_dim > config.large_res_threshold or max_mp > config.large_mp_threshold:
        resolution_class = "LARGE"
    else:
        resolution_class = "STANDARD"

    # Contrast Class
    if min_std < config.low_contrast_threshold:
        contrast_class = "LOW"
    elif min_std > config.high_contrast_threshold:
        contrast_class = "HIGH"
    else:
        contrast_class = "MEDIUM"

    # Texture Class
    if min_grad < config.low_texture_threshold or max_low_grad > config.low_gradient_fraction_threshold:
        texture_class = "LOW"
    elif min_grad > config.high_texture_threshold:
        texture_class = "HIGH"
    else:
        texture_class = "MEDIUM"

    # Scale Class
    if config.normal_scale_min <= scale_ratio <= config.normal_scale_max:
        scale_class = "NORMAL"
    else:
        scale_class = "LARGE-DIFFERENCE"

    return {
        "resolution_class": resolution_class,
        "contrast_class": contrast_class,
        "texture_class": texture_class,
        "scale_class": scale_class,
        "max_dim": max_dim,
        "max_mp": round(max_mp, 3),
        "min_contrast_std": round(min_std, 2),
        "min_gradient_mean": round(min_grad, 2),
        "max_low_gradient_fraction": round(max_low_grad, 4),
        "scale_ratio": round(scale_ratio, 4),
        "label": "Exploratory image characterization",
    }


def rule_based_router(profile: Dict[str, Any], pair_chars: Dict[str, Any], config: Optional[AdaptiveConfig] = None) -> Dict[str, Any]:
    """
    Step 3: Explainable, rule-based matcher routing using configurable heuristics.
    """
    if config is None:
        config = AdaptiveConfig()

    r_class = profile["resolution_class"]
    c_class = profile["contrast_class"]
    t_class = profile["texture_class"]

    reasons = []

    # Rule A: Robustness Priority (Low contrast or small/low-res or low-texture -> LoFTR)
    if c_class == "LOW" or r_class == "SMALL" or t_class == "LOW":
        selected = "LoFTR"
        rule = "Rule A (Robustness Priority)"
        if c_class == "LOW":
            reasons.append(f"Low intensity contrast (std {profile['min_contrast_std']} < {config.low_contrast_threshold}) suppresses gradient/corner detectors (SIFT/SuperPoint).")
        if r_class == "SMALL":
            reasons.append(f"Small resolution ({profile['max_dim']} px < {config.small_res_threshold} px) yields insufficient classical keypoints.")
        if t_class == "LOW":
            reasons.append(f"Low texture energy (gradient mean {profile['min_gradient_mean']} < {config.low_texture_threshold}) requires dense feature attention.")
        reasons.append("LoFTR selected for dense feature regression across low-contrast lunar regolith.")

    # Rule B: Scale & Memory-Safety Priority (Large images -> LoFTR with memory-safe scaling)
    elif r_class == "LARGE":
        selected = "LoFTR"
        rule = "Rule B (Scale & Memory-Safety Priority)"
        reasons.append(f"Large image scale ({profile['max_dim']} px > {config.large_res_threshold} px).")
        reasons.append("LoFTR with aspect-ratio-preserving scaling avoids quadratic KNN descriptor matching explosion of SIFT while remaining memory-safe.")

    # Rule C: Speed Priority (Standard resolution + High/Med contrast + High texture -> SIFT)
    elif c_class in ["HIGH", "MEDIUM"] and t_class == "HIGH" and r_class == "STANDARD":
        selected = "SIFT"
        rule = "Rule C (Speed Priority)"
        reasons.append(f"Standard resolution ({profile['max_dim']} px) with moderate-to-high contrast (std {profile['min_contrast_std']}).")
        reasons.append(f"High texture density (gradient mean {profile['min_gradient_mean']} >= {config.high_texture_threshold}).")
        reasons.append("SIFT expected to deliver 25x faster runtime (<1.5s) with sub-pixel held-out precision.")

    # Rule D: Default Robust Fallback
    else:
        selected = "LoFTR"
        rule = "Rule D (Default Robust Fallback)"
        reasons.append("Intermediate or uncertain image profile; LoFTR selected as robust default.")

    return {
        "selected_matcher": selected,
        "rule_triggered": rule,
        "reasons": reasons,
        "is_fallback": False,
        "label": "Rule-based adaptive matcher",
    }


def evaluate_quality_gate(matcher_result: Dict[str, Any], config: Optional[AdaptiveConfig] = None) -> Dict[str, Any]:
    """
    Step 4: Quality Gate verifying that matcher output is geometrically viable.
    """
    if config is None:
        config = AdaptiveConfig()

    if not matcher_result.get("success", False):
        return {
            "passed": False,
            "reasons": [f"Matcher execution failed: {matcher_result.get('failure_reason', 'unknown error')}"],
        }

    n_cand = matcher_result.get("n_candidates", 0)
    n_inl = matcher_result.get("n_inliers", 0)
    ratio = matcher_result.get("inlier_ratio", 0.0)
    occ = matcher_result.get("spatial_occupancy", 0.0)

    reasons = []
    if n_cand < config.min_candidate_matches:
        reasons.append(f"Candidate matches below threshold ({n_cand} < {config.min_candidate_matches})")
    if n_inl < config.min_initial_inliers:
        reasons.append(f"Initial inliers below threshold ({n_inl} < {config.min_initial_inliers})")
    if ratio < config.min_inlier_ratio:
        reasons.append(f"Inlier ratio below threshold ({ratio:.2f} < {config.min_inlier_ratio:.2f})")
    if occ < config.min_spatial_occupancy:
        reasons.append(f"Spatial occupancy below threshold ({occ:.2f} < {config.min_spatial_occupancy:.2f})")

    passed = (len(reasons) == 0)
    if passed:
        reasons.append("Quality gate PASSED: Sufficient inliers, ratio, and spatial coverage.")

    return {
        "passed": passed,
        "reasons": reasons,
    }


def run_sift_matching(source_img: np.ndarray, reference_img: np.ndarray, ratio_thresh: float = 0.75, ransac_thresh: float = 3.0) -> Dict[str, Any]:
    """
    Classical SIFT baseline matcher.
    """
    t0 = time.perf_counter()
    s_h, s_w = source_img.shape[:2]
    r_h, r_w = reference_img.shape[:2]

    # Resource-safety guard:
    # Full-image SIFT is resource-prohibitive on massive rasters.
    max_dim = max(s_h, s_w, r_h, r_w)
    if max_dim > 4000:
        return {
            "method": "SIFT",
            "success": False,
            "failure_stage": "resource_guard",
            "failure_reason": (
                f"Full-image SIFT disabled for large image "
                f"(max_dim={max_dim} > 4000). "
                "SIFT quadratic feature matching is resource-prohibitive on massive rasters."
            ),
            "runtime": time.perf_counter() - t0,
            "n_candidates": 0,
            "n_inliers": 0,
            "inlier_ratio": 0.0,
            "spatial_occupancy": 0.0,
            "spatial_cv": 0.0,
        }

    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if len(source_img.shape) == 3 else source_img
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if len(reference_img.shape) == 3 else reference_img

    sift = cv2.SIFT_create(contrastThreshold=0.03, edgeThreshold=10)
    kp0, des0 = sift.detectAndCompute(s_gray, None)
    kp1, des1 = sift.detectAndCompute(r_gray, None)

    if des0 is None or des1 is None or len(kp0) < 4 or len(kp1) < 4:
        return {
            "method": "SIFT",
            "success": False,
            "failure_stage": "feature_detection",
            "failure_reason": f"insufficient keypoints (src={len(kp0) if kp0 else 0}, ref={len(kp1) if kp1 else 0})",
            "runtime": time.perf_counter() - t0,
            "n_candidates": 0,
            "n_inliers": 0,
        }

    bf = cv2.BFMatcher(cv2.NORM_L2)
    raw_matches = bf.knnMatch(des0, des1, k=2)

    good_matches = []
    for m_pair in raw_matches:
        if len(m_pair) == 2:
            m, n = m_pair
            if m.distance < ratio_thresh * n.distance:
                good_matches.append(m)

    if len(good_matches) < 4:
        return {
            "method": "SIFT",
            "success": False,
            "failure_stage": "ratio_filtering",
            "failure_reason": f"insufficient ratio matches ({len(good_matches)} < 4)",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(good_matches),
            "n_inliers": 0,
        }

    pts0 = np.float32([kp0[m.queryIdx].pt for m in good_matches])
    pts1 = np.float32([kp1[m.trainIdx].pt for m in good_matches])

    H_init, mask = cv2.findHomography(pts0, pts1, cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
    t_feat = time.perf_counter() - t0

    if H_init is None or mask is None:
        return {
            "method": "SIFT",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "homography estimation failed",
            "runtime": t_feat,
            "n_candidates": len(good_matches),
            "n_inliers": 0,
        }

    inls = mask.ravel() == 1
    n_inl = int(np.sum(inls))
    if n_inl < 4:
        return {
            "method": "SIFT",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": f"insufficient inliers ({n_inl} < 4)",
            "runtime": t_feat,
            "n_candidates": len(good_matches),
            "n_inliers": n_inl,
        }

    inl_pts0 = pts0[inls]
    inl_pts1 = pts1[inls]
    grid = calculate_spatial_grid(inl_pts0, (s_h, s_w))
    occ = float(np.count_nonzero(grid) / 9.0)
    cv_val = float(np.std(grid) / np.mean(grid)) if np.mean(grid) > 0 else 0.0

    return {
        "method": "SIFT",
        "success": True,
        "pts0": pts0,
        "pts1": pts1,
        "inlier_pts0": inl_pts0,
        "inlier_pts1": inl_pts1,
        "confidences": np.ones(len(inl_pts0), dtype=np.float32),
        "H": H_init,
        "n_candidates": len(good_matches),
        "n_inliers": n_inl,
        "inlier_ratio": float(n_inl / len(good_matches)),
        "spatial_occupancy": occ,
        "spatial_cv": cv_val,
        "runtime": t_feat,
        "failure_reason": None,
    }


def run_loftr_matching(source_img: np.ndarray, reference_img: np.ndarray, loftr_model=None, ransac_thresh: float = 3.0) -> Dict[str, Any]:
    """
    LoFTR baseline matcher with aspect-ratio preserving scaling.
    """
    t0 = time.perf_counter()
    if loftr_model is None:
        loftr_model = load_loftr_matcher()

    s_gray, s_clahe = preprocess_image(source_img)
    r_gray, r_clahe = preprocess_image(reference_img)
    s_h, s_w = s_gray.shape
    r_h, r_w = r_gray.shape

    scale_s, s_wm, s_hm = compute_matching_scale((s_h, s_w), max_dim=1600, max_budget=1800000)
    scale_r, r_wm, r_hm = compute_matching_scale((r_h, r_w), max_dim=1600, max_budget=1800000)

    s_m = cv2.resize(s_clahe, (s_wm, s_hm), interpolation=cv2.INTER_AREA) if scale_s < 1.0 else s_clahe
    r_m = cv2.resize(r_clahe, (r_wm, r_hm), interpolation=cv2.INTER_AREA) if scale_r < 1.0 else r_clahe

    sx0 = float(s_w) / float(s_wm)
    sy0 = float(s_h) / float(s_hm)
    sx1 = float(r_w) / float(r_wm)
    sy1 = float(r_h) / float(r_hm)

    t_src = torch.from_numpy(s_m.astype(np.float32) / 255.0)[None, None].to(_DEVICE)
    t_ref = torch.from_numpy(r_m.astype(np.float32) / 255.0)[None, None].to(_DEVICE)

    with torch.inference_mode():
        out = loftr_model({"image0": t_src, "image1": t_ref})

    kpts0 = out["keypoints0"].cpu().numpy()
    kpts1 = out["keypoints1"].cpu().numpy()
    confs = out["confidence"].cpu().numpy()

    del t_src, t_ref, out
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if len(kpts0) < 4:
        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "feature_matching",
            "failure_reason": f"insufficient matches ({len(kpts0)} < 4)",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(kpts0),
            "n_inliers": 0,
        }

    kpts0[:, 0] *= sx0
    kpts0[:, 1] *= sy0
    kpts1[:, 0] *= sx1
    kpts1[:, 1] *= sy1

    H_init, mask = cv2.findHomography(kpts0, kpts1, cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
    t_feat = time.perf_counter() - t0

    if H_init is None or mask is None:
        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "homography estimation failed",
            "runtime": t_feat,
            "n_candidates": len(kpts0),
            "n_inliers": 0,
        }

    inls = mask.ravel() == 1
    n_inl = int(np.sum(inls))
    if n_inl < 4:
        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": f"insufficient inliers ({n_inl} < 4)",
            "runtime": t_feat,
            "n_candidates": len(kpts0),
            "n_inliers": n_inl,
        }

    inl_pts0 = kpts0[inls]
    inl_pts1 = kpts1[inls]
    grid = calculate_spatial_grid(inl_pts0, (s_h, s_w))
    occ = float(np.count_nonzero(grid) / 9.0)
    cv_val = float(np.std(grid) / np.mean(grid)) if np.mean(grid) > 0 else 0.0

    return {
        "method": "LoFTR",
        "success": True,
        "pts0": kpts0,
        "pts1": kpts1,
        "inlier_pts0": inl_pts0,
        "inlier_pts1": inl_pts1,
        "confidences": confs[inls],
        "H": H_init,
        "n_candidates": len(kpts0),
        "n_inliers": n_inl,
        "inlier_ratio": float(n_inl / len(kpts0)),
        "spatial_occupancy": occ,
        "spatial_cv": cv_val,
        "runtime": t_feat,
        "failure_reason": None,
    }


def run_superglue_matching(source_img: np.ndarray, reference_img: np.ndarray, sg_model=None, ransac_thresh: float = 3.0) -> Dict[str, Any]:
    """
    SuperPoint + SuperGlue baseline matcher.
    """
    t0 = time.perf_counter()
    # Resource-safety guard:
    # The current full-image SuperGlue implementation is not
    # safe for very large lunar rasters. Large images must use
    # the geoguided tiled SuperGlue implementation instead.
    max_dim = max(
        max(source_img.shape[:2]),
        max(reference_img.shape[:2])
    )

    if max_dim > 4000:
        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "resource_guard",
            "failure_reason": (
                f"Full-image SuperGlue disabled for large image "
                f"(max_dim={max_dim} > 4000). "
                "Use geoguided tiled SuperGlue."
            ),
            "runtime": time.perf_counter() - t0,
            "n_candidates": 0,
            "n_inliers": 0,
            "inlier_ratio": 0.0,
            "spatial_occupancy": 0.0,
            "spatial_cv": 0.0,
        }
    if sg_model is None:
        sg_model = Matching({
            "superpoint": {"nms_radius": 4, "keypoint_threshold": 0.005, "max_keypoints": 1024},
            "superglue": {"weights": "outdoor", "sinkhorn_iterations": 20, "match_threshold": 0.2}
        }).eval().to(_DEVICE)

    s_gray, s_clahe = preprocess_image(source_img)
    r_gray, r_clahe = preprocess_image(reference_img)
    s_h, s_w = s_gray.shape
    r_h, r_w = r_gray.shape

    # SuperPoint requires dims divisible by 8
    s_crop_h = s_h - (s_h % 8)
    s_crop_w = s_w - (s_w % 8)
    r_crop_h = r_h - (r_h % 8)
    r_crop_w = r_w - (r_w % 8)

    s_c = s_clahe[:s_crop_h, :s_crop_w]
    r_c = r_clahe[:r_crop_h, :r_crop_w]

    t_src = torch.from_numpy(s_c.astype(np.float32) / 255.0)[None, None].to(_DEVICE)
    t_ref = torch.from_numpy(r_c.astype(np.float32) / 255.0)[None, None].to(_DEVICE)

    with torch.inference_mode():
        pred = sg_model({"image0": t_src, "image1": t_ref})

    kpts0 = pred["keypoints0"][0].cpu().numpy()
    kpts1 = pred["keypoints1"][0].cpu().numpy()
    matches = pred["matches0"][0].cpu().numpy()
    match_conf = pred["matching_scores0"][0].cpu().numpy()

    del t_src, t_ref, pred
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    valid = matches > -1
    if np.sum(valid) < 4:
        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "feature_matching",
            "failure_reason": f"insufficient matches ({np.sum(valid)} < 4)",
            "runtime": time.perf_counter() - t0,
            "n_candidates": int(np.sum(valid)),
            "n_inliers": 0,
        }

    m_kpts0 = kpts0[valid]
    m_kpts1 = kpts1[matches[valid]]
    confs = match_conf[valid]

    H_init, mask = cv2.findHomography(m_kpts0, m_kpts1, cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
    t_feat = time.perf_counter() - t0

    if H_init is None or mask is None:
        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "homography estimation failed",
            "runtime": t_feat,
            "n_candidates": len(m_kpts0),
            "n_inliers": 0,
        }

    inls = mask.ravel() == 1
    n_inl = int(np.sum(inls))
    if n_inl < 4:
        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": f"insufficient inliers ({n_inl} < 4)",
            "runtime": t_feat,
            "n_candidates": len(m_kpts0),
            "n_inliers": n_inl,
        }

    inl_pts0 = m_kpts0[inls]
    inl_pts1 = m_kpts1[inls]
    grid = calculate_spatial_grid(inl_pts0, (s_h, s_w))
    occ = float(np.count_nonzero(grid) / 9.0)
    cv_val = float(np.std(grid) / np.mean(grid)) if np.mean(grid) > 0 else 0.0

    return {
        "method": "SuperGlue",
        "success": True,
        "pts0": m_kpts0,
        "pts1": m_kpts1,
        "inlier_pts0": inl_pts0,
        "inlier_pts1": inl_pts1,
        "confidences": confs[inls],
        "H": H_init,
        "n_candidates": len(m_kpts0),
        "n_inliers": n_inl,
        "inlier_ratio": float(n_inl / len(m_kpts0)),
        "spatial_occupancy": occ,
        "spatial_cv": cv_val,
        "runtime": t_feat,
        "failure_reason": None,
    }


def execute_common_downstream(
    pts0: np.ndarray,
    pts1: np.ndarray,
    confidences: np.ndarray,
    source_img: np.ndarray,
    reference_img: np.ndarray,
    max_per_cell: int = 6,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
) -> Dict[str, Any]:
    """
    Step 5: Common Downstream Registration Layer.
    Guarantees that ALL matchers feed into the EXACT same downstream pipeline:
      RANSAC -> Quality + 3x3 Spatial Selection -> Final Homography -> Warp -> Held-out Validation.
    """
    s_h, s_w = source_img.shape[:2]
    r_h, r_w = reference_img.shape[:2]

    # Initial RANSAC
    H_initial, mask_initial = cv2.findHomography(pts0, pts1, cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
    if H_initial is None or mask_initial is None:
        raise RuntimeError("Common downstream RANSAC failed.")

    inlier_ids = np.where(mask_initial.ravel() == 1)[0]
    if len(inlier_ids) < 4:
        raise RuntimeError(f"Common downstream RANSAC yielded insufficient inliers ({len(inlier_ids)} < 4).")

    # Quality scoring: confidence / (1.0 + reprojection_error)
    proj = cv2.perspectiveTransform(pts0[inlier_ids].reshape(-1, 1, 2), H_initial).reshape(-1, 2)
    errors = np.linalg.norm(proj - pts1[inlier_ids], axis=1)
    if confidences is None or len(confidences) != len(pts0):
        confs = np.ones(len(inlier_ids), dtype=np.float32)
    else:
        confs = confidences[inlier_ids]
    quality_score = confs / (1.0 + errors)

    # 3x3 Spatial Grid Binning & Quality Selection
    cells = {(r, c): [] for r in range(3) for c in range(3)}
    for local_idx, orig_idx in enumerate(inlier_ids):
        col = min(max(0, int(pts0[orig_idx][0] / (s_w / 3.0))), 2)
        row = min(max(0, int(pts0[orig_idx][1] / (s_h / 3.0))), 2)
        cells[(row, col)].append(local_idx)

    selected_local = []
    for cell, indices in cells.items():
        if indices:
            selected_local.extend(sorted(indices, key=lambda i: quality_score[i], reverse=True)[:max_per_cell])

    selected_ids = inlier_ids[selected_local]
    if len(selected_ids) < 4:
        raise RuntimeError(f"Spatial selection produced insufficient points ({len(selected_ids)} < 4).")

    # Final Homography Estimation on Selected Subset
    H_final, mask_final = cv2.findHomography(pts0[selected_ids], pts1[selected_ids], cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
    if H_final is None or mask_final is None:
        raise RuntimeError("Final homography estimation failed.")

    final_inlier_ids = selected_ids[mask_final.ravel() == 1]
    if len(final_inlier_ids) < 4:
        raise RuntimeError(f"Final RANSAC yielded insufficient inliers ({len(final_inlier_ids)} < 4).")

    src_f = pts0[final_inlier_ids]
    ref_f = pts1[final_inlier_ids]
    proj_f = cv2.perspectiveTransform(src_f.reshape(-1, 1, 2), H_final).reshape(-1, 2)
    final_errs = np.linalg.norm(proj_f - ref_f, axis=1)
    fit_rmse = float(np.sqrt(np.mean(final_errs**2)))

    # Perspective Warp
    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if len(source_img.shape) == 3 else source_img
    warped = cv2.warpPerspective(s_gray, H_final, (r_w, r_h))

    # Spatial coverage metrics
    selected_grid = calculate_spatial_grid(pts0[selected_ids], (s_h, s_w))
    occ = float(np.count_nonzero(selected_grid) / 9.0)
    cv_val = float(np.std(selected_grid) / np.mean(selected_grid)) if np.mean(selected_grid) > 0 else 0.0

    # Independent hold-out validation across seeds 1 to 5
    seed_chk_rmses = []
    seed_chk_means = []
    seed_chk_medians = []
    seed_chk_maxs = []

    for seed in seeds:
        if len(selected_ids) < 8:
            continue
        est_idx, chk_idx = split_spatially_balanced(pts0[selected_ids], (s_h, s_w), split_ratio=0.25, min_check_points=4, seed=seed)
        if len(est_idx) < 4 or len(chk_idx) < 4:
            continue

        src_est = pts0[selected_ids][est_idx]
        ref_est = pts1[selected_ids][est_idx]
        src_chk = pts0[selected_ids][chk_idx]
        ref_chk = pts1[selected_ids][chk_idx]

        H_seed, _ = cv2.findHomography(src_est, ref_est, cv2.RANSAC, ransac_thresh, maxIters=10000, confidence=0.995)
        if H_seed is not None:
            pred_chk = cv2.perspectiveTransform(src_chk.reshape(-1, 1, 2), H_seed).reshape(-1, 2)
            chk_errs = np.linalg.norm(pred_chk - ref_chk, axis=1)
            seed_chk_rmses.append(float(np.sqrt(np.mean(chk_errs**2))))
            seed_chk_means.append(float(np.mean(chk_errs)))
            seed_chk_medians.append(float(np.median(chk_errs)))
            seed_chk_maxs.append(float(np.max(chk_errs)))

    mean_chk_rmse = float(np.mean(seed_chk_rmses)) if seed_chk_rmses else np.nan
    median_chk_rmse = float(np.median(seed_chk_rmses)) if seed_chk_rmses else np.nan
    max_chk_error = float(np.max(seed_chk_maxs)) if seed_chk_maxs else np.nan

    return {
        "H_final": H_final,
        "warped_image": warped,
        "n_selected": len(selected_ids),
        "n_final_inliers": len(final_inlier_ids),
        "final_inlier_ratio": float(len(final_inlier_ids) / len(selected_ids)),
        "fit_rmse": round(fit_rmse, 4),
        "mean_check_rmse": round(mean_chk_rmse, 4) if not np.isnan(mean_chk_rmse) else np.nan,
        "median_check_rmse": round(median_chk_rmse, 4) if not np.isnan(median_chk_rmse) else np.nan,
        "max_check_error": round(max_chk_error, 4) if not np.isnan(max_chk_error) else np.nan,
        "held_out_valid": len(seed_chk_rmses) > 0,
        "spatial_occupancy": round(occ, 4),
        "spatial_cv": round(cv_val, 4),
        "selected_pts0": pts0[selected_ids],
        "selected_pts1": pts1[selected_ids],
        "final_pts0": src_f,
        "final_pts1": ref_f,
    }


def run_adaptive_registration(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    loftr_model=None,
    sg_model=None,
    config: Optional[AdaptiveConfig] = None,
) -> Dict[str, Any]:
    """
    Step 6: Complete End-to-End Adaptive Registration Pipeline.
    """
    t_start = time.perf_counter()
    if config is None:
        config = AdaptiveConfig()

    # Step 1: Inexpensive image characterization
    pair_chars = compute_pair_characteristics(source_img, reference_img)

    # Step 2: Difficulty profile
    profile = classify_difficulty_profile(pair_chars, config)

    # Step 3: Rule-based router
    decision = rule_based_router(profile, pair_chars, config)
    primary_choice = decision["selected_matcher"]

    matcher_map = {
        "SIFT": lambda: run_sift_matching(source_img, reference_img, ransac_thresh=config.ransac_threshold),
        "LoFTR": lambda: run_loftr_matching(source_img, reference_img, loftr_model=loftr_model, ransac_thresh=config.ransac_threshold),
        "SuperGlue": lambda: run_superglue_matching(source_img, reference_img, sg_model=sg_model, ransac_thresh=config.ransac_threshold),
    }

    # Step 4: Run primary matcher
    primary_res = matcher_map[primary_choice]()
    q_gate = evaluate_quality_gate(primary_res, config)

    active_res = primary_res
    fallback_used = False
    fallback_choice = None
    fallback_res = None
    fallback_reason = None

        # Quality Gate & Multi-Fallback logic
    #
    # Try the remaining matchers in a deterministic order.
    # A matcher is accepted only when its own quality gate passes.
    # If every available matcher fails the gate, registration fails.

    fallback_used = False
    fallback_choice = None
    fallback_res = None
    fallback_reason = None
    fallback_blocked = False
    blocked_fallbacks = []

    matcher_order = [
        "LoFTR",
        "SIFT",
        "SuperGlue",
    ]

    tried_results = {
        primary_choice: primary_res
    }

    active_res = None
    final_matcher_used = None

    # Primary accepted.
    if q_gate["passed"]:
        active_res = primary_res
        final_matcher_used = primary_choice

    else:
        fallback_reason = "; ".join(
            q_gate["reasons"]
        )

        max_dim = max(
            source_img.shape[0],
            source_img.shape[1],
            reference_img.shape[0],
            reference_img.shape[1],
        )

        executed_fallbacks = []

        for candidate in matcher_order:

            if candidate == primary_choice:
                continue

            # Resource policy guard: Block expensive full-image fallback on very large rasters
            if max_dim > 4000 and candidate in ("SIFT", "SuperGlue"):
                blocked_res = {
                    "method": candidate,
                    "success": False,
                    "failure_stage": "resource_guard",
                    "failure_reason": (
                        f"Full-image {candidate} fallback blocked by resource policy "
                        f"(max_dim={max_dim} > 4000)."
                    ),
                    "runtime": 0.0,
                    "n_candidates": 0,
                    "n_inliers": 0,
                    "inlier_ratio": 0.0,
                    "spatial_occupancy": 0.0,
                    "spatial_cv": 0.0,
                }
                tried_results[candidate] = blocked_res
                blocked_fallbacks.append(candidate)
                continue

            candidate_res = matcher_map[candidate]()
            tried_results[candidate] = candidate_res
            executed_fallbacks.append(candidate)

            candidate_gate = evaluate_quality_gate(
                candidate_res,
                config
            )

            # Keep the most recently attempted fallback
            # visible in the returned payload.
            fallback_choice = candidate
            fallback_res = candidate_res

            if candidate_gate["passed"]:
                active_res = candidate_res
                final_matcher_used = candidate
                break

        fallback_used = len(executed_fallbacks) > 0
        fallback_blocked = len(blocked_fallbacks) > 0 and not fallback_used

        # None of the matchers passed.
        if active_res is None:
            total_time = time.perf_counter() - t_start

            if max_dim > 4000 and primary_choice == "LoFTR":
                failure_msg = (
                    f"Primary matcher (LoFTR) failed quality gate ({fallback_reason}). "
                    f"Large-image fallback matchers (SIFT, SuperGlue) were intentionally "
                    f"blocked by the resource policy (max_dim={max_dim} > 4000)."
                )
            else:
                failure_msg = (
                    "All available matchers failed "
                    "the quality gate."
                )

            return {
                "success": False,
                "characterization": pair_chars,
                "difficulty_profile": profile,
                "decision": decision,

                "primary_choice": primary_choice,
                "primary_result": primary_res,
                "quality_gate": q_gate,

                "fallback_used": fallback_used,
                "fallback_choice": fallback_choice,
                "fallback_result": fallback_res,
                "fallback_blocked": fallback_blocked,
                "blocked_fallbacks": blocked_fallbacks,

                "fallback_reason": fallback_reason,

                "all_matcher_results": tried_results,

                "final_matcher_used": None,

                "failure_reason": failure_msg,

                "runtime": round(
                    time.perf_counter() - t_start,
                    2
                ),
            }
    # Step 5: Common Downstream Registration Layer
    try:
        pts0_down = active_res["inlier_pts0"]
        pts1_down = active_res["inlier_pts1"]
        confs_down = active_res.get("confidences", np.ones(len(pts0_down), dtype=np.float32))

        downstream = execute_common_downstream(
            pts0_down,
            pts1_down,
            confs_down,
            source_img,
            reference_img,
            ransac_thresh=config.ransac_threshold
        )
        total_time = time.perf_counter() - t_start

        return {
            "success": True,
            "characterization": pair_chars,
            "difficulty_profile": profile,
            "decision": decision,
            "primary_choice": primary_choice,
            "primary_result": primary_res,
            "quality_gate": q_gate,
            "fallback_used": fallback_used,
            "fallback_choice": fallback_choice,
            "fallback_result": fallback_res,
            "fallback_blocked": fallback_blocked,
            "blocked_fallbacks": blocked_fallbacks,
            "fallback_reason": fallback_reason,
            "final_matcher_used": fallback_choice if fallback_used else primary_choice,
            "downstream": downstream,
            "runtime": round(total_time, 2),
            "check_rmse": downstream["mean_check_rmse"],
            "spatial_occupancy": downstream["spatial_occupancy"],
            "spatial_cv": downstream["spatial_cv"],
            "final_inlier_ratio": downstream["final_inlier_ratio"],
            "fit_rmse": downstream["fit_rmse"],
        }
    except Exception as e:
        total_time = time.perf_counter() - t_start
        return {
            "success": False,
            "characterization": pair_chars,
            "difficulty_profile": profile,
            "decision": decision,
            "primary_choice": primary_choice,
            "primary_result": primary_res,
            "quality_gate": q_gate,
            "fallback_used": fallback_used,
            "fallback_choice": fallback_choice,
            "fallback_result": fallback_res,
            "fallback_blocked": fallback_blocked,
            "blocked_fallbacks": blocked_fallbacks,
            "fallback_reason": fallback_reason,
            "failure_reason": f"Common downstream registration failed: {str(e)}",
            "runtime": round(total_time, 2),
        }
