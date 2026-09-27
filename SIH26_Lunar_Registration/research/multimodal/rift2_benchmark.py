"""
research/multimodal/rift2_benchmark.py
=======================================
Controlled Research Benchmark for RIFT2 Multimodal Matcher
(LunarReg Phase 3 — Experimental RIFT2 Research Branch).

Evaluates RIFT2 against existing LoFTR baselines on difficult cross-sensor
lunar image pairs (specifically IIRS ↔ OHRC) across controlled native and Phase 2
scale configurations.

Mathematical & Operational Guarantees:
- Research-only: does not alter production matcher selection or routing.
- Native Coordinate Conversion: Scaled matcher coordinates are converted back to
  original native pixel coordinates before downstream registration.
- Common Downstream: All candidate sets pass through the UNCHANGED
  `execute_common_downstream` (RANSAC 3.0, confidence 0.995, 3x3 spatial binning,
  held-out validation across seeds 1-5).
- Neutral Confidence: Uses confidences=None as returned by RIFT2.
- Unbiased Reporting: No automatic winner selection or promotion logic.
"""

import time
import gc
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import pandas as pd

from research.multimodal.rift2_matcher import run_rift2_matching
from research.multimodal.scale_search import map_points_to_original
from research.multimodal.multimodal_preprocess import compute_pair_condition_telemetry
from research.adaptive_matcher.adaptive_engine import (
    run_loftr_matching,
    execute_common_downstream,
)


def run_rift2_benchmark(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    loftr_model=None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    include_loftr_comparison: bool = True,
    progress_callback=None,
) -> Dict[str, Any]:
    """Execute controlled RIFT2 multimodal benchmark across native and Phase 2 scale conditions.

    Evaluates:
    - RIFT2 Native (1.0, 1.0)
    - RIFT2 Phase 2 Scale (1.0, 0.5)
    - RIFT2 Resolution Ablation (0.5, 0.5)
    - RIFT2 Directional Check (0.5, 1.0)
    - LoFTR Native (1.0, 1.0) [comparison]
    - LoFTR Phase 2 Scale (1.0, 0.5) [comparison]

    Returns:
    - pair_condition_telemetry: Descriptive radiometric metrics on native images
    - results: List of trial dictionaries
    - comparison_table: pandas DataFrame formatted for research comparison
    """
    if source_img is None or reference_img is None:
        raise ValueError("source_img and reference_img must not be None.")

    orig_s_h, orig_s_w = source_img.shape[:2]
    orig_r_h, orig_r_w = reference_img.shape[:2]

    # 1. Compute factual pair-condition telemetry on native images
    telemetry = compute_pair_condition_telemetry(source_img, reference_img)

    # 2. Define controlled benchmark configurations
    # Format: (matcher, scale_mode, s_scale, r_scale)
    benchmark_configs: List[Tuple[str, str, float, float]] = [
        ("RIFT2", "native_baseline", 1.0, 1.0),
        ("RIFT2", "relative_scale_search", 1.0, 0.5),
        ("RIFT2", "resolution_ablation", 0.5, 0.5),
        ("RIFT2", "relative_scale_search", 0.5, 1.0),
    ]

    if include_loftr_comparison:
        benchmark_configs.extend([
            ("LoFTR", "native_baseline", 1.0, 1.0),
            ("LoFTR", "relative_scale_search", 1.0, 0.5),
        ])

    total_configs = len(benchmark_configs)
    results: List[Dict[str, Any]] = []

    for idx, (matcher_name, scale_mode, s_scale, r_scale) in enumerate(benchmark_configs):
        if progress_callback:
            pct = int((idx / max(1, total_configs)) * 100)
            progress_callback(pct, f"Evaluating {matcher_name} ({scale_mode}, s={s_scale:.2f}, r={r_scale:.2f})...")

        # Determine scaled dimensions
        scaled_s_w = max(1, int(round(orig_s_w * s_scale)))
        scaled_s_h = max(1, int(round(orig_s_h * s_scale)))
        scaled_r_w = max(1, int(round(orig_r_w * r_scale)))
        scaled_r_h = max(1, int(round(orig_r_h * r_scale)))

        s_scaled = cv2.resize(source_img, (scaled_s_w, scaled_s_h), interpolation=cv2.INTER_AREA) if s_scale < 1.0 else source_img
        r_scaled = cv2.resize(reference_img, (scaled_r_w, scaled_r_h), interpolation=cv2.INTER_AREA) if r_scale < 1.0 else reference_img

        t_trial_start = time.perf_counter()

        trial_record: Dict[str, Any] = {
            "matcher": matcher_name,
            "scale_mode": scale_mode,
            "source_scale": round(float(s_scale), 4),
            "reference_scale": round(float(r_scale), 4),
            "base_keypoints_source": 0,
            "base_keypoints_reference": 0,
            "oriented_features_source": 0,
            "oriented_features_reference": 0,
            "keypoints_source": 0,
            "keypoints_reference": 0,
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

        try:
            if matcher_name == "RIFT2":
                # Execute RIFT2 feature matching pipeline
                matcher_res = run_rift2_matching(
                    s_scaled,
                    r_scaled,
                    ransac_thresh=ransac_thresh,
                    scale_mode=scale_mode,
                    source_scale=s_scale,
                    reference_scale=r_scale,
                )
                trial_record["base_keypoints_source"] = int(matcher_res.get("base_keypoints_source", matcher_res.get("keypoints_source", 0)))
                trial_record["base_keypoints_reference"] = int(matcher_res.get("base_keypoints_reference", matcher_res.get("keypoints_reference", 0)))
                trial_record["oriented_features_source"] = int(matcher_res.get("oriented_features_source", matcher_res.get("keypoints_source", 0)))
                trial_record["oriented_features_reference"] = int(matcher_res.get("oriented_features_reference", matcher_res.get("keypoints_reference", 0)))
                trial_record["keypoints_source"] = int(matcher_res.get("keypoints_source", 0))
                trial_record["keypoints_reference"] = int(matcher_res.get("keypoints_reference", 0))

            elif matcher_name == "LoFTR":
                # Execute existing LoFTR baseline
                # Note: LoFTR takes preprocessed or grayscale images; run_loftr_matching handles preprocessing
                matcher_res = run_loftr_matching(
                    s_scaled,
                    r_scaled,
                    loftr_model=loftr_model,
                    ransac_thresh=ransac_thresh,
                )
                trial_record["base_keypoints_source"] = int(matcher_res.get("n_candidates", 0))
                trial_record["base_keypoints_reference"] = int(matcher_res.get("n_candidates", 0))
                trial_record["oriented_features_source"] = int(matcher_res.get("n_candidates", 0))
                trial_record["oriented_features_reference"] = int(matcher_res.get("n_candidates", 0))
                trial_record["keypoints_source"] = int(matcher_res.get("n_candidates", 0))
                trial_record["keypoints_reference"] = int(matcher_res.get("n_candidates", 0))
            else:
                raise ValueError(f"Unknown matcher '{matcher_name}'.")

        except Exception as e:
            trial_record["runtime"] = round(time.perf_counter() - t_trial_start, 3)
            trial_record["failure_stage"] = "matcher_execution"
            trial_record["failure_reason"] = f"Matcher exception: {str(e)}"
            results.append(trial_record)
            continue

        n_cands = int(matcher_res.get("n_candidates", 0))
        trial_record["candidates"] = n_cands

        if not matcher_res.get("success", False) or n_cands < 4:
            trial_record["runtime"] = round(time.perf_counter() - t_trial_start, 3)
            trial_record["failure_stage"] = matcher_res.get("failure_stage", "descriptor_matching")
            trial_record["failure_reason"] = matcher_res.get("failure_reason", f"Insufficient candidates ({n_cands} < 4)")
            results.append(trial_record)
            continue

        pts0_scaled = matcher_res.get("pts0") if matcher_name == "RIFT2" else matcher_res.get("inlier_pts0")
        pts1_scaled = matcher_res.get("pts1") if matcher_name == "RIFT2" else matcher_res.get("inlier_pts1")
        confs = matcher_res.get("confidences")  # None for RIFT2

        if pts0_scaled is None or pts1_scaled is None or len(pts0_scaled) < 4 or len(pts1_scaled) < 4:
            trial_record["runtime"] = round(time.perf_counter() - t_trial_start, 3)
            trial_record["failure_stage"] = "candidate_extraction"
            trial_record["failure_reason"] = f"Insufficient valid correspondence points ({0 if pts0_scaled is None else len(pts0_scaled)} < 4)"
            results.append(trial_record)
            continue

        # Coordinate Inverse-Mapping: Map scaled coordinates back to original native pixel coordinates
        pts0_native = map_points_to_original(pts0_scaled, (scaled_s_h, scaled_s_w), (orig_s_h, orig_s_w))
        pts1_native = map_points_to_original(pts1_scaled, (scaled_r_h, scaled_r_w), (orig_r_h, orig_r_w))

        # Pass native correspondence points into UNCHANGED common downstream registration
        try:
            downstream = execute_common_downstream(
                pts0=pts0_native,
                pts1=pts1_native,
                confidences=confs,  # None triggers neutral-confidence fallback in downstream
                source_img=source_img,
                reference_img=reference_img,
                max_per_cell=6,
                ransac_thresh=ransac_thresh,
                seeds=seeds,
            )

            n_inl = int(downstream.get("n_initial_inliers", downstream.get("n_final_inliers", 0)))
            chk_rmse = downstream.get("mean_check_rmse")
            fit_rmse = downstream.get("fit_rmse")
            held_out_valid = downstream.get("held_out_valid", False)

            cands = int(trial_record.get("candidates", 0))
            trial_record["initial_inliers"] = n_inl
            trial_record["initial_inlier_ratio"] = round(float(n_inl / max(1, cands)), 4) if cands > 0 else 0.0
            trial_record["spatial_occupancy"] = round(float(downstream.get("spatial_occupancy", 0.0)), 4)
            trial_record["spatial_cv"] = round(float(downstream.get("spatial_cv", 0.0)), 4)
            trial_record["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
            trial_record["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan
            trial_record["runtime"] = round(time.perf_counter() - t_trial_start, 3)

            if held_out_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                trial_record["success"] = True
                trial_record["failure_stage"] = None
                trial_record["failure_reason"] = None
            else:
                trial_record["success"] = False
                trial_record["failure_stage"] = "held_out_validation"
                trial_record["failure_reason"] = f"Insufficient inliers for independent held-out validation ({n_inl} < 8; 0 check points)"

        except Exception as e:
            trial_record["runtime"] = round(time.perf_counter() - t_trial_start, 3)
            trial_record["failure_stage"] = "common_downstream"
            trial_record["failure_reason"] = f"Common downstream registration failed: {str(e)}"

        results.append(trial_record)

        # Release memory after each trial
        del s_scaled, r_scaled
        gc.collect()

    # 3. Construct comparison DataFrame
    df_rows = []
    for r in results:
        df_rows.append({
            "Matcher": r["matcher"],
            "Scale Mode": r["scale_mode"],
            "Source Scale": r["source_scale"],
            "Reference Scale": r["reference_scale"],
            "Base Keypoints (Src / Ref)": f"{r.get('base_keypoints_source', 0)} / {r.get('base_keypoints_reference', 0)}",
            "Oriented Features / Descriptors (Src / Ref)": f"{r.get('oriented_features_source', 0)} / {r.get('oriented_features_reference', 0)}",
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Inlier Ratio": r["initial_inlier_ratio"],
            "3×3 Occupancy": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Independent Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["runtime"],
            "Success": r["success"],
            "Failure Stage": r["failure_stage"] if r["failure_stage"] is not None else "None",
            "Failure Reason": r["failure_reason"] if r["failure_reason"] is not None else "None",
        })

    comparison_df = pd.DataFrame(df_rows)

    return {
        "pair_condition_telemetry": telemetry,
        "results": results,
        "comparison_table": comparison_df,
    }


def load_angle_pairs(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """Research-only loader for angle/viewpoint test image pairs.

    Discovers pairs located under data/research/phase3_rift2/angle_pairs/*/.
    Validates presence and readability of source and reference images.
    Parses optional metadata.json without fabricating missing angle attributes.

    Returns:
    - dict with keys: 'base_dir', 'total_discovered', 'n_valid', 'n_invalid',
      'valid_pairs', 'invalid_pairs'
    """
    import os
    import json

    if base_dir is None:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "research", "phase3_rift2", "angle_pairs")
        )

    valid_pairs: List[Dict[str, Any]] = []
    invalid_pairs: List[Dict[str, Any]] = []

    if not os.path.exists(base_dir):
        return {
            "base_dir": base_dir,
            "total_discovered": 0,
            "n_valid": 0,
            "n_invalid": 0,
            "valid_pairs": [],
            "invalid_pairs": [{"pair_id": "none", "path": base_dir, "reason": f"Directory not found: {base_dir}"}],
        }

    valid_img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")

    for entry in sorted(os.listdir(base_dir)):
        entry_path = os.path.join(base_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        pair_id = entry

        # Check metadata.json
        meta_path = os.path.join(entry_path, "metadata.json")
        metadata: Dict[str, Any] = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception as e:
                metadata = {"error": f"Failed to parse metadata.json: {str(e)}"}

        # Find source and reference image paths
        src_path = None
        ref_path = None
        for ext in valid_img_exts:
            s_cand = os.path.join(entry_path, f"source{ext}")
            if os.path.exists(s_cand):
                src_path = s_cand
                break
        for ext in valid_img_exts:
            r_cand = os.path.join(entry_path, f"reference{ext}")
            if os.path.exists(r_cand):
                ref_path = r_cand
                break

        if src_path is None or ref_path is None:
            missing = []
            if src_path is None:
                missing.append("source image")
            if ref_path is None:
                missing.append("reference image")
            invalid_pairs.append({
                "pair_id": pair_id,
                "path": entry_path,
                "reason": f"Missing {' and '.join(missing)}",
                "metadata": metadata,
            })
            continue

        # Load and validate images
        s_img = cv2.imread(src_path)
        r_img = cv2.imread(ref_path)
        if s_img is None or r_img is None:
            unreadable = []
            if s_img is None:
                unreadable.append("source image unreadable")
            if r_img is None:
                unreadable.append("reference image unreadable")
            invalid_pairs.append({
                "pair_id": pair_id,
                "path": entry_path,
                "reason": "; ".join(unreadable),
                "metadata": metadata,
            })
            continue

        # Explicit test_type verification
        raw_test_type = metadata.get("test_type", "unknown")
        allowed_types = {
            "viewpoint_change",
            "rotation_change",
            "sun_angle_change",
            "resolution_change",
            "multimodal_sensor_change",
        }
        test_type = raw_test_type if raw_test_type in allowed_types else "unknown"

        valid_pairs.append({
            "pair_id": pair_id,
            "path": entry_path,
            "source_path": src_path,
            "reference_path": ref_path,
            "source_img": s_img,
            "reference_img": r_img,
            "metadata": metadata,
            "test_type": test_type,
            "source_shape": s_img.shape,
            "reference_shape": r_img.shape,
        })

    return {
        "base_dir": base_dir,
        "total_discovered": len(valid_pairs) + len(invalid_pairs),
        "n_valid": len(valid_pairs),
        "n_invalid": len(invalid_pairs),
        "valid_pairs": valid_pairs,
        "invalid_pairs": invalid_pairs,
    }


def run_angle_pairs_benchmark(
    pairs_data: Optional[Dict[str, Any]] = None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    ratio_thresh: float = 0.90,
) -> Dict[str, Any]:
    """Execute RIFT2 feature matching and common downstream on each discovered angle/viewpoint pair.

    Outputs metrics strictly separated from the IIRS ↔ OHRC candidate pair.
    """
    if pairs_data is None:
        pairs_data = load_angle_pairs()

    results: List[Dict[str, Any]] = []

    for pair in pairs_data.get("valid_pairs", []):
        pair_id = pair["pair_id"]
        test_type = pair["test_type"]
        s_img = pair["source_img"]
        r_img = pair["reference_img"]
        s_h, s_w = s_img.shape[:2]
        r_h, r_w = r_img.shape[:2]

        t_start = time.perf_counter()

        record: Dict[str, Any] = {
            "pair_id": pair_id,
            "test_type": test_type,
            "source_dimensions": f"{s_w}x{s_h}",
            "reference_dimensions": f"{r_w}x{r_h}",
            "source_scale": 1.0,
            "reference_scale": 1.0,
            "base_keypoints_source": 0,
            "base_keypoints_reference": 0,
            "oriented_features_source": 0,
            "oriented_features_reference": 0,
            "keypoints_source": 0,
            "keypoints_reference": 0,
            "candidate_matches": 0,
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

        try:
            m_res = run_rift2_matching(
                s_img,
                r_img,
                ransac_thresh=ransac_thresh,
                ratio_thresh=ratio_thresh,
            )
            record["base_keypoints_source"] = int(m_res.get("base_keypoints_source", 0))
            record["base_keypoints_reference"] = int(m_res.get("base_keypoints_reference", 0))
            record["oriented_features_source"] = int(m_res.get("oriented_features_source", m_res.get("keypoints_source", 0)))
            record["oriented_features_reference"] = int(m_res.get("oriented_features_reference", m_res.get("keypoints_reference", 0)))
            record["keypoints_source"] = int(m_res.get("keypoints_source", 0))
            record["keypoints_reference"] = int(m_res.get("keypoints_reference", 0))
            n_cands = int(m_res.get("n_candidates", 0))
            record["candidate_matches"] = n_cands

            if not m_res.get("success", False) or n_cands < 4:
                record["runtime"] = round(time.perf_counter() - t_start, 3)
                record["failure_stage"] = m_res.get("failure_stage", "descriptor_matching")
                record["failure_reason"] = m_res.get("failure_reason", f"Insufficient candidates ({n_cands} < 4)")
                results.append(record)
                continue

            pts0 = m_res.get("pts0")
            pts1 = m_res.get("pts1")
            confs = m_res.get("confidences")  # None for RIFT2

            downstream = execute_common_downstream(
                pts0=pts0,
                pts1=pts1,
                confidences=confs,
                source_img=s_img,
                reference_img=r_img,
                max_per_cell=6,
                ransac_thresh=ransac_thresh,
                seeds=seeds,
            )

            init_inl = int(downstream.get("n_initial_inliers", downstream.get("n_final_inliers", 0)))
            record["initial_inliers"] = init_inl
            record["initial_inlier_ratio"] = round(float(init_inl / max(1, n_cands)), 4) if n_cands > 0 else 0.0
            record["spatial_occupancy"] = round(float(downstream.get("spatial_occupancy", 0.0)), 4)
            record["spatial_cv"] = round(float(downstream.get("spatial_cv", 0.0)), 4)

            fit_rmse = downstream.get("fit_rmse")
            chk_rmse = downstream.get("mean_check_rmse")
            held_valid = downstream.get("held_out_valid", False)

            record["fit_rmse"] = round(float(fit_rmse), 4) if fit_rmse is not None and not np.isnan(fit_rmse) else np.nan
            record["independent_held_out_rmse"] = round(float(chk_rmse), 4) if chk_rmse is not None and not np.isnan(chk_rmse) else np.nan
            record["runtime"] = round(time.perf_counter() - t_start, 3)

            if held_valid and chk_rmse is not None and not np.isnan(chk_rmse):
                record["success"] = True
            else:
                record["success"] = False
                record["failure_stage"] = "held_out_validation"
                record["failure_reason"] = f"Insufficient inliers for independent held-out check ({init_inl} < 8)"

        except Exception as e:
            record["runtime"] = round(time.perf_counter() - t_start, 3)
            record["failure_stage"] = "common_downstream"
            record["failure_reason"] = str(e)

        results.append(record)

    df_rows = []
    for r in results:
        df_rows.append({
            "Pair ID": r["pair_id"],
            "Test Type": r["test_type"],
            "Source Dims": r["source_dimensions"],
            "Ref Dims": r["reference_dimensions"],
            "Base Keypoints (Src / Ref)": f"{r.get('base_keypoints_source', 0)} / {r.get('base_keypoints_reference', 0)}",
            "Oriented Features / Descriptors (Src / Ref)": f"{r.get('oriented_features_source', r.get('keypoints_source', 0))} / {r.get('oriented_features_reference', r.get('keypoints_reference', 0))}",
            "Candidates": r["candidate_matches"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Inlier Ratio": r["initial_inlier_ratio"],
            "3×3 Occupancy": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Independent Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["runtime"],
            "Success": r["success"],
            "Failure Stage": r["failure_stage"] if r["failure_stage"] is not None else "None",
            "Failure Reason": r["failure_reason"] if r["failure_reason"] is not None else "None",
        })

    return {
        "discovery_summary": {
            "total_discovered": pairs_data.get("total_discovered", 0),
            "n_valid": pairs_data.get("n_valid", 0),
            "n_invalid": pairs_data.get("n_invalid", 0),
            "invalid_pairs": pairs_data.get("invalid_pairs", []),
        },
        "results": results,
        "comparison_table": pd.DataFrame(df_rows),
    }
