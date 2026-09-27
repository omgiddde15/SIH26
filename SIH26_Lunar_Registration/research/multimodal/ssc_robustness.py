"""
research/multimodal/ssc_robustness.py
=====================================
Controlled Robustness and Sensitivity Validation for SSC-Style Research Branch
(LunarReg Phase 8 — Research-Only Validation).

Objective:
Validate whether the Phase 7 local self-similarity context (SSC) improvement
on IIRS <-> OHRC remains stable under controlled, pre-defined perturbations
and control conditions.

Strict Invariants:
- Phase 7 baseline remains FROZEN (detector, patch 7x7, radius 4.0 px, 6 radial angles,
  21-D pairwise descriptor, KNN k=2, mutual cross-check, NNDR 0.90, deduplication).
- Zero parameter tuning based on Phase 8 results.
- Production routing, quality gates, and common downstream mathematics remain untouched.

Pre-Defined Degradation Categories:
- "Stable": Held-out check valid (initial_inliers >= 8, held_out_valid=True) and held_out_rmse < 3.0 px.
- "Degraded but usable": Held-out check valid, but held_out_rmse >= 3.0 px or inliers deteriorate materially.
- "Failed": Held-out check invalid (initial_inliers < 8, held_out_valid=False, or NaN RMSE), or registration breakdown.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

from research.multimodal.ssc_matcher import (
    SSCConfig,
    run_ssc_matching,
)


# ---------------------------------------------------------------------------
# Pre-Defined Perturbation Operators
# ---------------------------------------------------------------------------

def apply_brightness(img: np.ndarray, delta: int) -> np.ndarray:
    """Apply additive intensity shift: I_new = clip(I + delta, 0, 255)."""
    return np.clip(img.astype(np.int16) + delta, 0, 255).astype(np.uint8)


def apply_contrast(img: np.ndarray, factor: float) -> np.ndarray:
    """Apply multiplicative contrast scale: I_new = clip(I * factor, 0, 255)."""
    return np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def apply_gamma(img: np.ndarray, gamma: float) -> np.ndarray:
    """Apply power-law gamma correction: I_new = 255 * (I / 255) ^ gamma."""
    lut = np.clip(
        np.round(255.0 * ((np.arange(256, dtype=np.float32) / 255.0) ** gamma)),
        0,
        255,
    ).astype(np.uint8)
    return cv2.LUT(img, lut)


def apply_gaussian_noise(img: np.ndarray, sigma: float, seed: int = 42) -> np.ndarray:
    """Apply additive Gaussian noise with specified standard deviation and deterministic seed."""
    rng = np.random.RandomState(seed)
    noise = rng.normal(loc=0.0, scale=sigma, size=img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_gaussian_blur(img: np.ndarray, ksize: int) -> np.ndarray:
    """Apply 2D Gaussian smoothing blur with square kernel (ksize x ksize)."""
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(img, (ksize, ksize), sigmaX=0)


def apply_synthetic_rotation(img: np.ndarray, angle_deg: float) -> np.ndarray:
    """Apply 2D in-plane Euclidean rotation around the image geometric center.

    Uses cv2.INTER_LINEAR interpolation and BORDER_REFLECT padding to preserve boundary statistics.
    """
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def apply_perturbation(
    img: np.ndarray,
    perturbation_type: str,
    param: Any,
    seed: int = 42,
) -> np.ndarray:
    """Dispatch perturbation operator by name."""
    p_type = perturbation_type.lower().strip()
    if p_type in ("none", "native", "identity"):
        return img.copy()
    elif p_type == "brightness":
        return apply_brightness(img, int(param))
    elif p_type == "contrast":
        return apply_contrast(img, float(param))
    elif p_type == "gamma":
        return apply_gamma(img, float(param))
    elif p_type == "noise":
        return apply_gaussian_noise(img, float(param), seed=seed)
    elif p_type == "blur":
        return apply_gaussian_blur(img, int(param))
    elif p_type == "rotation":
        return apply_synthetic_rotation(img, float(param))
    else:
        raise ValueError(f"Unknown perturbation type: '{perturbation_type}'")


# ---------------------------------------------------------------------------
# Pre-Defined Degradation Classification
# ---------------------------------------------------------------------------

def classify_robustness_status(
    initial_inliers: int,
    held_out_valid: bool,
    held_out_rmse: Optional[float],
    fit_rmse: Optional[float] = None,
) -> str:
    """Classify registration robustness into pre-defined categories:

    - 'Stable': Held-out check valid (initial_inliers >= 8, held_out_valid=True) and held_out_rmse < 3.0 px.
    - 'Degraded but usable': Held-out check valid, but held_out_rmse >= 3.0 px.
    - 'Failed': Held-out check invalid (initial_inliers < 8, held_out_valid=False, or NaN RMSE), or registration breakdown.
    """
    if not held_out_valid or initial_inliers < 8 or held_out_rmse is None or np.isnan(held_out_rmse):
        return "Failed"
    if held_out_rmse < 3.0:
        return "Stable"
    else:
        return "Degraded but usable"


# ---------------------------------------------------------------------------
# Robustness Single-Trial Runner
# ---------------------------------------------------------------------------

def run_ssc_robustness_trial(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    condition_group: str,
    perturbation_type: str = "none",
    perturbation_param: Any = 0,
    scale_source: float = 1.0,
    scale_reference: float = 1.0,
    config: Optional[SSCConfig] = None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    pair_label: str = "IIRS <-> OHRC",
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute a single controlled robustness evaluation trial.

    Applies the perturbation to source_img, scales images if specified,
    runs frozen SSC matching + downstream registration, and classifies outcome.
    """
    if config is None:
        config = SSCConfig()

    # Apply perturbation to source image
    s_perturbed = apply_perturbation(source_img, perturbation_type, perturbation_param, seed=seed)

    # Label generation
    if perturbation_type.lower() == "none":
        pert_desc = "None (Native)"
    elif perturbation_type.lower() == "brightness":
        pert_desc = f"Brightness ({perturbation_param:+d})"
    elif perturbation_type.lower() == "contrast":
        pert_desc = f"Contrast (x{float(perturbation_param):.2f})"
    elif perturbation_type.lower() == "gamma":
        pert_desc = f"Gamma ({float(perturbation_param):.1f})"
    elif perturbation_type.lower() == "noise":
        pert_desc = f"Noise (sigma={float(perturbation_param)})"
    elif perturbation_type.lower() == "blur":
        pert_desc = f"Blur ({int(perturbation_param)}x{int(perturbation_param)})"
    elif perturbation_type.lower() == "rotation":
        pert_desc = f"Rotation ({float(perturbation_param):+g} deg)"
    else:
        pert_desc = f"{perturbation_type} ({perturbation_param})"

    full_label = f"{pair_label} [{pert_desc}]"

    # Execute matching
    res = run_ssc_matching(
        source_img=s_perturbed,
        reference_img=reference_img,
        scale_source=scale_source,
        scale_reference=scale_reference,
        config=config,
        ransac_thresh=ransac_thresh,
        seeds=seeds,
        pair_label=full_label,
    )

    down = res.get("downstream_result") or {}
    held_valid = bool(down.get("held_out_valid", False))
    init_inl = int(res.get("initial_inliers", 0))
    chk_rmse = res.get("independent_held_out_rmse")
    fit_rmse = res.get("fit_rmse")

    status = classify_robustness_status(
        initial_inliers=init_inl,
        held_out_valid=held_valid,
        held_out_rmse=chk_rmse,
        fit_rmse=fit_rmse,
    )

    # Attach robustness metadata
    res["condition_group"] = condition_group
    res["perturbation_type"] = perturbation_type
    res["perturbation_param"] = str(perturbation_param)
    res["perturbation_desc"] = pert_desc
    res["robustness_status"] = status
    res["held_out_valid"] = held_valid

    return res
