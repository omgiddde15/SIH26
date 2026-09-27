"""
research/multimodal/scale_search.py
====================================
Adaptive Coarse-to-Fine Scale Search Module
(LunarReg Phase 2 — Multimodal Scale Research Branch).

Investigates whether cross-scale resolution divergence is a limiting factor
in difficult cross-sensor lunar image registration (such as IIRS ↔ OHRC).

Mathematical & Operational Guarantees:
- Research-only: does NOT modify production registration or change default routing.
- Native Coordinate Mapping (MANDATORY): All correspondences found on scaled images
  are mapped back to original native pixel coordinates before common downstream registration.
- Common Downstream Invariants: Every candidate passes through unchanged
  `execute_common_downstream` (RANSAC thresh=3.0, conf=0.995, 3x3 spatial selection,
  held-out validation across seeds 1-5).
- Existing Matchers: Uses existing `run_loftr_matching` and `run_sift_matching`.
- No image enlargement or artificial super-resolution (scale <= 1.0).
- Scale Telemetry: Explicitly distinguishes external research scale from LoFTR internal working scale.
- No automatic winner promotion: Results returned in an unbiased research comparison table.
"""

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import pandas as pd

from research.adaptive_matcher.adaptive_engine import (
    run_loftr_matching,
    run_sift_matching,
    execute_common_downstream,
)
from research.multimodal.multimodal_preprocess import (
    preprocess_representation,
    compute_pair_condition_telemetry,
    MULTIMODAL_REPRESENTATIONS,
)


@dataclass
class ScaleSearchConfig:
    """Configuration for empirical coarse-to-fine scale search."""
    # Conservative initial downsampling factors: 1.0, 1/sqrt(2), 0.5, 1/(2*sqrt(2)), 0.25
    scale_factors: Tuple[float, ...] = (
        1.0,
        float(1.0 / np.sqrt(2)),  # ~0.7071
        0.5,
        float(0.5 / np.sqrt(2)),  # ~0.3536
        0.25,
    )
    # Minimum spatial dimension bound to avoid sub-feature blur
    min_dimension: int = 64
    # Representations to evaluate
    representations: Tuple[str, ...] = (
        "baseline_clahe",
        "gradient_magnitude",
        "local_gradient_normalized",
    )
    # Matchers to evaluate
    matchers: Tuple[str, ...] = ("LoFTR", "SIFT")
    # Whether to include histogram_normalized
    include_histogram_normalized: bool = False
    # Extensible range for future deep research (not run automatically)
    extended_scale_factors: Tuple[float, ...] = (0.1768, 0.125, 0.0884, 0.0625)


def map_points_to_original(
    points: np.ndarray,
    scaled_shape: Tuple[int, int],
    orig_shape: Tuple[int, int],
) -> np.ndarray:
    """Map 2D points from scaled image coordinates back to original native pixel coordinates.

    Uses actual integer scaled and original dimensions to avoid float rounding discrepancies:
        x_orig = x_scaled * orig_w / scaled_w
        y_orig = y_scaled * orig_h / scaled_h

    Points are strictly clamped to valid native coordinate bounds: [0, orig_w - 1] x [0, orig_h - 1].
    """
    if points is None or len(points) == 0:
        return np.empty((0, 2), dtype=np.float32)

    scaled_h, scaled_w = scaled_shape[:2]
    orig_h, orig_w = orig_shape[:2]

    if scaled_w <= 0 or scaled_h <= 0 or orig_w <= 0 or orig_h <= 0:
        raise ValueError(f"Invalid shapes for coordinate mapping: scaled={scaled_shape}, orig={orig_shape}")

    mapped = points.copy().astype(np.float32)
    mapped[:, 0] = np.clip(mapped[:, 0] * (float(orig_w) / float(scaled_w)), 0.0, float(orig_w - 1))
    mapped[:, 1] = np.clip(mapped[:, 1] * (float(orig_h) / float(scaled_h)), 0.0, float(orig_h - 1))
    return mapped


def generate_scale_pairs(
    config: ScaleSearchConfig,
    orig_s_shape: Tuple[int, int],
    orig_r_shape: Tuple[int, int],
) -> List[Dict[str, Any]]:
    """Generate deterministic candidate scale combinations for cross-scale and ablation experiments.

    Distinguishes:
    - 'native_baseline': (1.0, 1.0)
    - 'relative_scale_search': Asymmetric scaling where one image is downsampled relative to the other
    - 'resolution_ablation': Symmetric downsampling (s, s) where relative scale remains 1.0
    """
    s_h, s_w = orig_s_shape[:2]
    r_h, r_w = orig_r_shape[:2]
    min_dim = config.min_dimension

    pairs: List[Dict[str, Any]] = []

    # 1. Native baseline
    pairs.append({
        "scale_mode": "native_baseline",
        "source_scale": 1.0,
        "reference_scale": 1.0,
        "effective_relative_scale": 1.0,
    })

    # 2. Asymmetric Cross-Scale Search
    for factor in config.scale_factors:
        if factor >= 1.0:
            continue
        # Check source reduction
        s_sw = int(round(s_w * factor))
        s_sh = int(round(s_h * factor))
        if s_sw >= min_dim and s_sh >= min_dim:
            pairs.append({
                "scale_mode": "relative_scale_search",
                "source_scale": float(factor),
                "reference_scale": 1.0,
                "effective_relative_scale": round(float(factor / 1.0), 4),
            })

        # Check reference reduction
        r_sw = int(round(r_w * factor))
        r_sh = int(round(r_h * factor))
        if r_sw >= min_dim and r_sh >= min_dim:
            pairs.append({
                "scale_mode": "relative_scale_search",
                "source_scale": 1.0,
                "reference_scale": float(factor),
                "effective_relative_scale": round(float(1.0 / factor), 4),
            })

    # 3. Symmetric Resolution Ablation
    for factor in config.scale_factors:
        if factor >= 1.0:
            continue
        s_sw = int(round(s_w * factor))
        s_sh = int(round(s_h * factor))
        r_sw = int(round(r_w * factor))
        r_sh = int(round(r_h * factor))
        if s_sw >= min_dim and s_sh >= min_dim and r_sw >= min_dim and r_sh >= min_dim:
            pairs.append({
                "scale_mode": "resolution_ablation",
                "source_scale": float(factor),
                "reference_scale": float(factor),
                "effective_relative_scale": 1.0,
            })

    return pairs


def run_scale_search(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    loftr_model=None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    config: Optional[ScaleSearchConfig] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """Execute the coarse-to-fine scale search across scale configurations, representations, and matchers.

    Returns:
    - pair_condition_telemetry: Descriptive radiometric stats of native images
    - scale_search_config: Config parameters used
    - results: List of individual experimental trial dictionaries
    - comparison_table: pandas DataFrame formatted for research comparison
    """
    if source_img is None or reference_img is None:
        raise ValueError("source_img and reference_img must not be None.")

    if config is None:
        config = ScaleSearchConfig()

    # 1. Compute factual pair-condition telemetry on original rasters
    telemetry = compute_pair_condition_telemetry(source_img, reference_img)

    orig_s_h, orig_s_w = source_img.shape[:2]
    orig_r_h, orig_r_w = reference_img.shape[:2]

    # 2. Determine representations to evaluate
    reps_to_test = list(config.representations)
    if config.include_histogram_normalized and "histogram_normalized" not in reps_to_test:
        reps_to_test.append("histogram_normalized")

    # 3. Generate candidate scale pairs
    scale_pairs = generate_scale_pairs(config, (orig_s_h, orig_s_w), (orig_r_h, orig_r_w))

    # 4. Construct search experiment list
    # SIFT evaluated on structural representations; LoFTR on all
    experiments: List[Dict[str, Any]] = []
    for sp in scale_pairs:
        for rep in reps_to_test:
            for matcher in config.matchers:
                # SIFT is evaluated on baseline and structural representations
                if matcher == "SIFT" and rep == "histogram_normalized":
                    continue
                exp = dict(sp)
                exp["representation"] = rep
                exp["matcher"] = matcher
                experiments.append(exp)

    total_experiments = len(experiments)
    results: List[Dict[str, Any]] = []

    # Cache preprocessed and scaled images to avoid redundant computation
    # Key: (representation, width, height)
    scaled_cache_s: Dict[Tuple[str, int, int], np.ndarray] = {}
    scaled_cache_r: Dict[Tuple[str, int, int], np.ndarray] = {}

    for idx, exp in enumerate(experiments):
        rep_name = exp["representation"]
        matcher_name = exp["matcher"]
        s_scale = exp["source_scale"]
        r_scale = exp["reference_scale"]
        rel_scale = exp["effective_relative_scale"]
        scale_mode = exp["scale_mode"]

        if progress_callback:
            pct = int((idx / max(1, total_experiments)) * 100)
            progress_callback(pct, f"Testing {scale_mode}: s={s_scale:.2f}, r={r_scale:.2f} ({rep_name}, {matcher_name})...")

        # Determine scaled dimensions
        scaled_s_w = max(1, int(round(orig_s_w * s_scale)))
        scaled_s_h = max(1, int(round(orig_s_h * s_scale)))
        scaled_r_w = max(1, int(round(orig_r_w * r_scale)))
        scaled_r_h = max(1, int(round(orig_r_h * r_scale)))

        s_key = (rep_name, scaled_s_w, scaled_s_h)
        if s_key not in scaled_cache_s:
            s_raw_scaled = cv2.resize(source_img, (scaled_s_w, scaled_s_h), interpolation=cv2.INTER_AREA) if s_scale < 1.0 else source_img
            scaled_cache_s[s_key] = preprocess_representation(s_raw_scaled, rep_name)
        s_prep_scaled = scaled_cache_s[s_key]

        r_key = (rep_name, scaled_r_w, scaled_r_h)
        if r_key not in scaled_cache_r:
            r_raw_scaled = cv2.resize(reference_img, (scaled_r_w, scaled_r_h), interpolation=cv2.INTER_AREA) if r_scale < 1.0 else reference_img
            scaled_cache_r[r_key] = preprocess_representation(r_raw_scaled, rep_name)
        r_prep_scaled = scaled_cache_r[r_key]

        t_start = time.perf_counter()

        record: Dict[str, Any] = {
            "scale_mode": scale_mode,
            "research_source_scale": round(float(s_scale), 4),
            "research_reference_scale": round(float(r_scale), 4),
            "nominal_external_relative_scale": round(float(rel_scale), 4),
            "research_source_shape": (scaled_s_h, scaled_s_w),
            "research_reference_shape": (scaled_r_h, scaled_r_w),
            "loftr_internal_source_scale": None,
            "loftr_internal_reference_scale": None,
            "loftr_internal_source_shape": None,
            "loftr_internal_reference_shape": None,
            "representation": rep_name,
            "matcher": matcher_name,
            "candidates": 0,
            "initial_inliers": 0,
            "initial_inlier_ratio": 0.0,
            "spatial_occupancy": 0.0,
            "spatial_cv": 0.0,
            "fit_rmse": np.nan,
            "independent_held_out_rmse": np.nan,
            "runtime": 0.0,
            "resource_guard_triggered": False,
            "tiled_loftr_used": False,
            "success": False,
            "failure_stage": None,
            "failure_reason": None,
        }

        # Step A: Run Matcher on Scaled Representation
        try:
            if matcher_name == "LoFTR":
                matcher_res = run_loftr_matching(
                    s_prep_scaled,
                    r_prep_scaled,
                    loftr_model=loftr_model,
                    ransac_thresh=ransac_thresh,
                )
                record["loftr_internal_source_scale"] = float(matcher_res.get("source_scale", 1.0))
                record["loftr_internal_reference_scale"] = float(matcher_res.get("reference_scale", 1.0))
                record["loftr_internal_source_shape"] = matcher_res.get("working_source_shape")
                record["loftr_internal_reference_shape"] = matcher_res.get("working_reference_shape")
                record["tiled_loftr_used"] = bool(matcher_res.get("tiled_loftr", False))
                record["resource_guard_triggered"] = bool(not matcher_res.get("memory_safe", True) or matcher_res.get("failure_stage") == "resource_guard")

            elif matcher_name == "SIFT":
                matcher_res = run_sift_matching(
                    s_prep_scaled,
                    r_prep_scaled,
                    ransac_thresh=ransac_thresh,
                )
            else:
                raise ValueError(f"Unsupported matcher '{matcher_name}'.")

        except Exception as e:
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = "feature_matching"
            record["failure_reason"] = f"Matcher exception: {str(e)}"
            results.append(record)
            continue

        record["candidates"] = int(matcher_res.get("n_candidates", 0))
        record["initial_inliers"] = int(matcher_res.get("n_inliers", 0))
        record["initial_inlier_ratio"] = round(float(matcher_res.get("inlier_ratio", 0.0)), 4)

        if not matcher_res.get("success", False):
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = matcher_res.get("failure_stage", "feature_matching")
            record["failure_reason"] = matcher_res.get("failure_reason", "Matcher reported failure")
            results.append(record)
            continue

        pts0_scaled = matcher_res.get("inlier_pts0")
        pts1_scaled = matcher_res.get("inlier_pts1")
        confs = matcher_res.get("confidences")

        if pts0_scaled is None or pts1_scaled is None or len(pts0_scaled) < 4 or len(pts1_scaled) < 4:
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = "inlier_count"
            record["failure_reason"] = f"Insufficient initial inliers for downstream registration ({0 if pts0_scaled is None else len(pts0_scaled)} < 4)"
            results.append(record)
            continue

        # Step B: MANDATORY Coordinate Inverse-Mapping
        # Map detected keypoints back to original native pixel coordinates
        pts0_orig = map_points_to_original(pts0_scaled, (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
        pts1_orig = map_points_to_original(pts1_scaled, (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))

        # Step C: Send Mapped Native Points into UNCHANGED Common Downstream
        # Evaluates RANSAC, homography, warp, and held-out validation in native coordinates
        try:
            downstream = execute_common_downstream(
                pts0=pts0_orig,
                pts1=pts1_orig,
                confidences=confs,
                source_img=source_img,
                reference_img=reference_img,
                max_per_cell=6,
                ransac_thresh=ransac_thresh,
                seeds=seeds,
            )

            chk_rmse = downstream.get("mean_check_rmse")
            fit_rmse = downstream.get("fit_rmse")
            held_out_valid = downstream.get("held_out_valid", False)

            record["spatial_occupancy"] = round(float(downstream.get("spatial_occupancy", 0.0)), 4)
            record["spatial_cv"] = round(float(downstream.get("spatial_cv", 0.0)), 4)
            record["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
            record["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan
            record["runtime"] = round(time.perf_counter() - t_start, 3)

            if held_out_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                record["success"] = True
                record["failure_stage"] = None
                record["failure_reason"] = None
            else:
                n_fin = downstream.get("n_final_inliers", len(pts0_orig))
                record["success"] = False
                record["failure_stage"] = "held_out_validation"
                record["failure_reason"] = (
                    f"Insufficient inliers for independent held-out validation ({n_fin} < 8; 0 check points)"
                )

        except Exception as e:
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = "common_downstream"
            record["failure_reason"] = f"Common downstream registration failed: {str(e)}"

        results.append(record)

    # 5. Build research comparison table
    df_rows = []
    for r in results:
        df_rows.append({
            "Representation": r["representation"],
            "Matcher": r["matcher"],
            "Scale Mode": r["scale_mode"],
            "Source Scale": r["research_source_scale"],
            "Reference Scale": r["research_reference_scale"],
            "Effective Relative Scale": r["nominal_external_relative_scale"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Inlier Ratio": r["initial_inlier_ratio"],
            "3×3 Occupancy": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["runtime"],
            "Success": r["success"],
            "Failure Reason": r["failure_reason"] if r["failure_reason"] is not None else "None",
        })

    comparison_df = pd.DataFrame(df_rows)

    return {
        "pair_condition_telemetry": telemetry,
        "scale_search_config": asdict(config),
        "results": results,
        "comparison_table": comparison_df,
    }
