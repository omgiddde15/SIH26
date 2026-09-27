"""
research/multimodal/multimodal_benchmark.py
============================================
Multimodal Benchmark Module (LunarReg Phase 1 — Multimodal Research Branch).

Explicitly research-only evaluation framework comparing experimental multimodal
representations (baseline_clahe, histogram_normalized, gradient_magnitude,
local_gradient_normalized) using EXISTING matchers (LoFTR, SIFT) and the
EXISTING common downstream registration pipeline.

Mathematical & Operational Guarantees:
- Uses existing LoFTR (`run_loftr_matching`) without changing weights or memory guards.
- Uses existing SIFT (`run_sift_matching`) without changing thresholds.
- Every candidate set is routed through existing `execute_common_downstream`.
- Preserves all mathematical invariants: RANSAC thresh=3.0, conf=0.995, max 6 pts/cell,
  seeds 1-5, 25% check-point held-out validation.
- Strictly unbiased: does NOT automatically rank, select, or promote a winner.
- Returns structured results and a pandas DataFrame comparison table.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
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


def run_multimodal_benchmark(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    loftr_model=None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    progress_callback=None,
) -> Dict[str, Any]:
    """Execute the multimodal benchmark across representations and matchers.

    Evaluates:
    - LoFTR on: baseline_clahe, histogram_normalized, gradient_magnitude, local_gradient_normalized
    - SIFT on: baseline_clahe, gradient_magnitude, local_gradient_normalized

    Every candidate correspondence set that passes feature matching is sent
    through the existing `execute_common_downstream` registration layer.

    Returns:
    - "pair_condition_telemetry": factual radiometric telemetry dict
    - "results": list of per-candidate execution dictionaries
    - "comparison_table": pandas DataFrame formatted for research comparison
    """
    if source_img is None or reference_img is None:
        raise ValueError("source_img and reference_img must not be None.")

    # 1. Compute factual pair-condition telemetry
    telemetry = compute_pair_condition_telemetry(source_img, reference_img)

    # 2. Define benchmark matrix: (representation, matcher)
    # LoFTR is tested on all four representations
    # SIFT is tested on baseline and structural representations
    benchmark_matrix: List[Tuple[str, str]] = [
        ("baseline_clahe", "LoFTR"),
        ("histogram_normalized", "LoFTR"),
        ("gradient_magnitude", "LoFTR"),
        ("local_gradient_normalized", "LoFTR"),
        ("baseline_clahe", "SIFT"),
        ("gradient_magnitude", "SIFT"),
        ("local_gradient_normalized", "SIFT"),
    ]

    total_runs = len(benchmark_matrix)
    results: List[Dict[str, Any]] = []

    # Cache preprocessed images so each representation is computed once
    cached_source_reps: Dict[str, np.ndarray] = {}
    cached_ref_reps: Dict[str, np.ndarray] = {}

    for idx, (rep_name, matcher_name) in enumerate(benchmark_matrix):
        if progress_callback:
            pct = int((idx / total_runs) * 100)
            progress_callback(pct, f"Evaluating {rep_name} with {matcher_name}...")

        # Obtain preprocessed matching-ready representations
        if rep_name not in cached_source_reps:
            cached_source_reps[rep_name] = preprocess_representation(source_img, rep_name)
        if rep_name not in cached_ref_reps:
            cached_ref_reps[rep_name] = preprocess_representation(reference_img, rep_name)

        s_prep = cached_source_reps[rep_name]
        r_prep = cached_ref_reps[rep_name]

        t_start = time.perf_counter()

        record: Dict[str, Any] = {
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
            "success": False,
            "failure_stage": None,
            "failure_reason": None,
        }

        # Step A: Run EXISTING Matcher
        try:
            if matcher_name == "LoFTR":
                matcher_res = run_loftr_matching(
                    s_prep,
                    r_prep,
                    loftr_model=loftr_model,
                    ransac_thresh=ransac_thresh,
                )
            elif matcher_name == "SIFT":
                matcher_res = run_sift_matching(
                    s_prep,
                    r_prep,
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

        pts0 = matcher_res.get("inlier_pts0")
        pts1 = matcher_res.get("inlier_pts1")
        confs = matcher_res.get("confidences")

        if pts0 is None or pts1 is None or len(pts0) < 4 or len(pts1) < 4:
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = "inlier_count"
            record["failure_reason"] = f"Insufficient initial inliers for downstream registration ({0 if pts0 is None else len(pts0)} < 4)"
            results.append(record)
            continue

        # Step B: Route through EXISTING Common Downstream Registration
        # Preserves native coordinate system by supplying original source/reference rasters
        try:
            downstream = execute_common_downstream(
                pts0=pts0,
                pts1=pts1,
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
                n_fin = downstream.get("n_final_inliers", len(pts0))
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

    # 3. Construct research comparison DataFrame without automatic winner selection
    df_rows = []
    for r in results:
        df_rows.append({
            "Representation": r["representation"],
            "Matcher": r["matcher"],
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
        "results": results,
        "comparison_table": comparison_df,
    }
