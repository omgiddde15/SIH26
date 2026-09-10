"""
PHASE C: ADAPTIVE MATCHER v1 BENCHMARK
SIH26166 — Automated Lunar Image Registration

Executes head-to-head multi-pair evaluation comparing:
  - SIFT (Fixed)
  - LoFTR (Fixed)
  - SuperGlue (Fixed)
  - Adaptive Matcher v1 (Dynamic Routing + Quality Gate + Fallback)

Outputs:
  - research/adaptive_matcher/adaptive_results.csv
  - research/adaptive_matcher/adaptive_summary.csv
  - research/adaptive_matcher/routing_decisions.csv
  - research/adaptive_matcher/failure_analysis.csv
  - Visualizations (5 plots)
"""

import os
import sys
import time
import cv2
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
SUPERGLUE_REPO = os.path.join(PROJECT_ROOT, "research", "superglue_repo")
if SUPERGLUE_REPO not in sys.path:
    sys.path.insert(0, SUPERGLUE_REPO)

from app.registration_core import load_loftr_matcher, _DEVICE
from models.matching import Matching
from research.adaptive_matcher.adaptive_engine import (
    AdaptiveConfig,
    compute_pair_characteristics,
    classify_difficulty_profile,
    rule_based_router,
    evaluate_quality_gate,
    run_sift_matching,
    run_loftr_matching,
    run_superglue_matching,
    execute_common_downstream,
    run_adaptive_registration,
)


def discover_validation_pairs(base_dir=None):
    """Automatically discovers all available pair directories."""
    if base_dir is None:
        base_dir = os.path.join(PROJECT_ROOT, "data", "validation_pairs")
    if not os.path.exists(base_dir):
        return []

    discovered = []
    for item in sorted(os.listdir(base_dir)):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            files = os.listdir(item_path)
            src_c = [f for f in files if "source" in f.lower() and f.lower().endswith((".png", ".jpg", ".jpeg", ".tif"))]
            ref_c = [f for f in files if "reference" in f.lower() and f.lower().endswith((".png", ".jpg", ".jpeg", ".tif"))]
            if src_c and ref_c:
                discovered.append({
                    "pair_id": item,
                    "pair_dir": item_path,
                    "source_path": os.path.join(item_path, src_c[0]),
                    "reference_path": os.path.join(item_path, ref_c[0]),
                })
    return discovered


def run_full_adaptive_benchmark(output_dir=None, progress_callback=None):
    """
    Executes the multi-pair benchmark across all validation pairs.
    """
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "research", "adaptive_matcher")
    os.makedirs(output_dir, exist_ok=True)

    pairs = discover_validation_pairs()
    if not pairs:
        raise RuntimeError("No validation pairs discovered in data/validation_pairs/")

    print(f"Loading LoFTR & SuperGlue models for Adaptive Benchmark ({len(pairs)} pairs)...")
    if progress_callback:
        progress_callback(5, f"Loading deep matchers for {len(pairs)} pairs...")

    loftr = load_loftr_matcher()
    sg = Matching({
        "superpoint": {"nms_radius": 4, "keypoint_threshold": 0.005, "max_keypoints": 1024},
        "superglue": {"weights": "outdoor", "sinkhorn_iterations": 20, "match_threshold": 0.2}
    }).eval().to(_DEVICE)

    config = AdaptiveConfig()

    all_results = []
    routing_decisions = []
    failure_records = []

    for p_idx, p_info in enumerate(pairs):
        p_id = p_info["pair_id"]
        print(f"\\nEvaluating Pair: {p_id} ({p_idx+1}/{len(pairs)})...")
        if progress_callback:
            pct = 10 + int((p_idx / len(pairs)) * 70)
            progress_callback(pct, f"Evaluating {p_id} across matchers & adaptive router...")

        s_img = cv2.imread(p_info["source_path"])
        r_img = cv2.imread(p_info["reference_path"])
        if s_img is None or r_img is None:
            continue

        pair_chars = compute_pair_characteristics(s_img, r_img)
        diff_prof = classify_difficulty_profile(pair_chars, config)

        src_res = f"{pair_chars['source']['width']}x{pair_chars['source']['height']}"
        ref_res = f"{pair_chars['reference']['width']}x{pair_chars['reference']['height']}"
        contrast_str = f"{diff_prof['contrast_class']} (std={diff_prof['min_contrast_std']})"
        texture_str = f"{diff_prof['texture_class']} (grad={diff_prof['min_gradient_mean']})"

        # 1. Evaluate SIFT (Fixed)
        t0_sift = time.perf_counter()
        sift_raw = run_sift_matching(s_img, r_img, ransac_thresh=config.ransac_threshold)
        t_sift = time.perf_counter() - t0_sift
        if sift_raw["success"]:
            try:
                down_sift = execute_common_downstream(sift_raw["inlier_pts0"], sift_raw["inlier_pts1"], sift_raw["confidences"], s_img, r_img, ransac_thresh=config.ransac_threshold)
                s_chk = round(down_sift["mean_check_rmse"], 4) if not np.isnan(down_sift["mean_check_rmse"]) else np.nan
                s_stat = "Success" if not np.isnan(s_chk) else f"Failed: insufficient inliers for held-out validation ({down_sift['n_final_inliers']} < 8; 0 check points)"
                all_results.append({
                    "Pair": p_id,
                    "Method": "SIFT",
                    "Selected Matcher": "SIFT",
                    "Fallback Used?": "No",
                    "Source Res": src_res,
                    "Ref Res": ref_res,
                    "Contrast": contrast_str,
                    "Texture": texture_str,
                    "Candidate Matches": sift_raw["n_candidates"],
                    "Initial Inliers": sift_raw["n_inliers"],
                    "Final Inliers": down_sift["n_final_inliers"],
                    "Final Inlier Ratio": round(down_sift["final_inlier_ratio"], 4),
                    "Fit RMSE": round(down_sift["fit_rmse"], 4),
                    "Held-out Check RMSE": s_chk,
                    "Spatial Occupancy": round(down_sift["spatial_occupancy"], 4),
                    "Spatial CV": round(down_sift["spatial_cv"], 4),
                    "Runtime": round(t_sift, 2),
                    "Status": s_stat,
                    "Decision Reason": "Fixed SIFT baseline",
                })
                if np.isnan(s_chk):
                    failure_records.append({"Pair": p_id, "Method": "SIFT", "Failure Stage": "held_out_validation", "Failure Reason": f"insufficient inliers ({down_sift['n_final_inliers']} < 8; 0 check points)", "Recovery Event": "None (Fixed)"})
            except Exception as e:
                all_results.append({
                    "Pair": p_id, "Method": "SIFT", "Selected Matcher": "SIFT", "Fallback Used?": "No",
                    "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                    "Candidate Matches": sift_raw["n_candidates"], "Initial Inliers": sift_raw["n_inliers"],
                    "Final Inliers": 0, "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                    "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_sift, 2),
                    "Status": f"Failed: downstream error ({str(e)})", "Decision Reason": "Fixed SIFT baseline",
                })
                failure_records.append({"Pair": p_id, "Method": "SIFT", "Failure Stage": "downstream_registration", "Failure Reason": str(e), "Recovery Event": "None (Fixed)"})
        else:
            all_results.append({
                "Pair": p_id, "Method": "SIFT", "Selected Matcher": "SIFT", "Fallback Used?": "No",
                "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                "Candidate Matches": sift_raw["n_candidates"], "Initial Inliers": 0, "Final Inliers": 0,
                "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_sift, 2),
                "Status": f"Failed: {sift_raw['failure_reason']}", "Decision Reason": "Fixed SIFT baseline",
            })
            failure_records.append({"Pair": p_id, "Method": "SIFT", "Failure Stage": sift_raw.get("failure_stage", "matching"), "Failure Reason": sift_raw["failure_reason"], "Recovery Event": "None (Fixed)"})

        # 2. Evaluate LoFTR (Fixed)
        t0_loftr = time.perf_counter()
        loftr_raw = run_loftr_matching(s_img, r_img, loftr_model=loftr, ransac_thresh=config.ransac_threshold)
        t_loftr = time.perf_counter() - t0_loftr
        if loftr_raw["success"]:
            try:
                down_loftr = execute_common_downstream(loftr_raw["inlier_pts0"], loftr_raw["inlier_pts1"], loftr_raw["confidences"], s_img, r_img, ransac_thresh=config.ransac_threshold)
                l_chk = round(down_loftr["mean_check_rmse"], 4) if not np.isnan(down_loftr["mean_check_rmse"]) else np.nan
                l_stat = "Success" if not np.isnan(l_chk) else f"Failed: insufficient inliers for held-out validation ({down_loftr['n_final_inliers']} < 8; 0 check points)"
                all_results.append({
                    "Pair": p_id,
                    "Method": "LoFTR",
                    "Selected Matcher": "LoFTR",
                    "Fallback Used?": "No",
                    "Source Res": src_res,
                    "Ref Res": ref_res,
                    "Contrast": contrast_str,
                    "Texture": texture_str,
                    "Candidate Matches": loftr_raw["n_candidates"],
                    "Initial Inliers": loftr_raw["n_inliers"],
                    "Final Inliers": down_loftr["n_final_inliers"],
                    "Final Inlier Ratio": round(down_loftr["final_inlier_ratio"], 4),
                    "Fit RMSE": round(down_loftr["fit_rmse"], 4),
                    "Held-out Check RMSE": l_chk,
                    "Spatial Occupancy": round(down_loftr["spatial_occupancy"], 4),
                    "Spatial CV": round(down_loftr["spatial_cv"], 4),
                    "Runtime": round(t_loftr, 2),
                    "Status": l_stat,
                    "Decision Reason": "Fixed LoFTR baseline",
                })
                if np.isnan(l_chk):
                    failure_records.append({"Pair": p_id, "Method": "LoFTR", "Failure Stage": "held_out_validation", "Failure Reason": f"insufficient inliers ({down_loftr['n_final_inliers']} < 8; 0 check points)", "Recovery Event": "None (Fixed)"})
            except Exception as e:
                all_results.append({
                    "Pair": p_id, "Method": "LoFTR", "Selected Matcher": "LoFTR", "Fallback Used?": "No",
                    "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                    "Candidate Matches": loftr_raw["n_candidates"], "Initial Inliers": loftr_raw["n_inliers"],
                    "Final Inliers": 0, "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                    "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_loftr, 2),
                    "Status": f"Failed: downstream error ({str(e)})", "Decision Reason": "Fixed LoFTR baseline",
                })
                failure_records.append({"Pair": p_id, "Method": "LoFTR", "Failure Stage": "downstream_registration", "Failure Reason": str(e), "Recovery Event": "None (Fixed)"})
        else:
            all_results.append({
                "Pair": p_id, "Method": "LoFTR", "Selected Matcher": "LoFTR", "Fallback Used?": "No",
                "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                "Candidate Matches": loftr_raw["n_candidates"], "Initial Inliers": 0, "Final Inliers": 0,
                "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_loftr, 2),
                "Status": f"Failed: {loftr_raw['failure_reason']}", "Decision Reason": "Fixed LoFTR baseline",
            })
            failure_records.append({"Pair": p_id, "Method": "LoFTR", "Failure Stage": loftr_raw.get("failure_stage", "matching"), "Failure Reason": loftr_raw["failure_reason"], "Recovery Event": "None (Fixed)"})

        # 3. Evaluate SuperGlue (Fixed)
        t0_sg = time.perf_counter()
        sg_raw = run_superglue_matching(s_img, r_img, sg_model=sg, ransac_thresh=config.ransac_threshold)
        t_sg = time.perf_counter() - t0_sg
        if sg_raw["success"]:
            try:
                down_sg = execute_common_downstream(sg_raw["inlier_pts0"], sg_raw["inlier_pts1"], sg_raw["confidences"], s_img, r_img, ransac_thresh=config.ransac_threshold)
                sg_chk = round(down_sg["mean_check_rmse"], 4) if not np.isnan(down_sg["mean_check_rmse"]) else np.nan
                sg_stat = "Success" if not np.isnan(sg_chk) else f"Failed: insufficient inliers for held-out validation ({down_sg['n_final_inliers']} < 8; 0 check points)"
                all_results.append({
                    "Pair": p_id,
                    "Method": "SuperGlue",
                    "Selected Matcher": "SuperGlue",
                    "Fallback Used?": "No",
                    "Source Res": src_res,
                    "Ref Res": ref_res,
                    "Contrast": contrast_str,
                    "Texture": texture_str,
                    "Candidate Matches": sg_raw["n_candidates"],
                    "Initial Inliers": sg_raw["n_inliers"],
                    "Final Inliers": down_sg["n_final_inliers"],
                    "Final Inlier Ratio": round(down_sg["final_inlier_ratio"], 4),
                    "Fit RMSE": round(down_sg["fit_rmse"], 4),
                    "Held-out Check RMSE": sg_chk,
                    "Spatial Occupancy": round(down_sg["spatial_occupancy"], 4),
                    "Spatial CV": round(down_sg["spatial_cv"], 4),
                    "Runtime": round(t_sg, 2),
                    "Status": sg_stat,
                    "Decision Reason": "Fixed SuperGlue baseline",
                })
                if np.isnan(sg_chk):
                    failure_records.append({"Pair": p_id, "Method": "SuperGlue", "Failure Stage": "held_out_validation", "Failure Reason": f"insufficient inliers ({down_sg['n_final_inliers']} < 8; 0 check points)", "Recovery Event": "None (Fixed)"})
            except Exception as e:
                all_results.append({
                    "Pair": p_id, "Method": "SuperGlue", "Selected Matcher": "SuperGlue", "Fallback Used?": "No",
                    "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                    "Candidate Matches": sg_raw["n_candidates"], "Initial Inliers": sg_raw["n_inliers"],
                    "Final Inliers": 0, "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                    "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_sg, 2),
                    "Status": f"Failed: downstream error ({str(e)})", "Decision Reason": "Fixed SuperGlue baseline",
                })
                failure_records.append({"Pair": p_id, "Method": "SuperGlue", "Failure Stage": "downstream_registration", "Failure Reason": str(e), "Recovery Event": "None (Fixed)"})
        else:
            all_results.append({
                "Pair": p_id, "Method": "SuperGlue", "Selected Matcher": "SuperGlue", "Fallback Used?": "No",
                "Source Res": src_res, "Ref Res": ref_res, "Contrast": contrast_str, "Texture": texture_str,
                "Candidate Matches": sg_raw["n_candidates"], "Initial Inliers": 0, "Final Inliers": 0,
                "Final Inlier Ratio": 0.0, "Fit RMSE": np.nan, "Held-out Check RMSE": np.nan,
                "Spatial Occupancy": 0.0, "Spatial CV": np.nan, "Runtime": round(t_sg, 2),
                "Status": f"Failed: {sg_raw['failure_reason']}", "Decision Reason": "Fixed SuperGlue baseline",
            })
            failure_records.append({"Pair": p_id, "Method": "SuperGlue", "Failure Stage": sg_raw.get("failure_stage", "matching"), "Failure Reason": sg_raw["failure_reason"], "Recovery Event": "None (Fixed)"})

        # 4. Evaluate Adaptive Matcher v1
        adapt_res = run_adaptive_registration(s_img, r_img, loftr_model=loftr, sg_model=sg, config=config)

        # Identify actual best fixed matcher by Check RMSE among successful fixed methods
        succ_fixed = [r for r in all_results if r["Pair"] == p_id and r["Method"] in ["SIFT", "LoFTR", "SuperGlue"] and r["Status"] == "Success"]
        if succ_fixed:
            actual_best = min(succ_fixed, key=lambda x: x["Held-out Check RMSE"])["Method"]
        else:
            actual_best = "None"

        # Record Adaptive Result
        if adapt_res["success"]:
            down_adapt = adapt_res["downstream"]
            final_m = adapt_res["final_matcher_used"]
            fb_used = "Yes" if adapt_res["fallback_used"] else "No"
            reason_str = "; ".join(adapt_res["decision"]["reasons"])
            if adapt_res["fallback_used"]:
                reason_str += f" -> Fallback to {adapt_res['fallback_choice']} ({adapt_res['fallback_reason']})"

            all_results.append({
                "Pair": p_id,
                "Method": "Adaptive",
                "Selected Matcher": final_m,
                "Fallback Used?": fb_used,
                "Source Res": src_res,
                "Ref Res": ref_res,
                "Contrast": contrast_str,
                "Texture": texture_str,
                "Candidate Matches": adapt_res["primary_result"].get("n_candidates", 0) if not adapt_res["fallback_used"] else adapt_res["fallback_result"].get("n_candidates", 0),
                "Initial Inliers": adapt_res["primary_result"].get("n_inliers", 0) if not adapt_res["fallback_used"] else adapt_res["fallback_result"].get("n_inliers", 0),
                "Final Inliers": down_adapt["n_final_inliers"],
                "Final Inlier Ratio": round(down_adapt["final_inlier_ratio"], 4),
                "Fit RMSE": round(down_adapt["fit_rmse"], 4),
                "Held-out Check RMSE": round(down_adapt["mean_check_rmse"], 4),
                "Spatial Occupancy": round(down_adapt["spatial_occupancy"], 4),
                "Spatial CV": round(down_adapt["spatial_cv"], 4),
                "Runtime": round(adapt_res["runtime"], 2),
                "Status": "Success",
                "Decision Reason": reason_str,
            })

            # Compare category vs best fixed
            best_fixed_r = next((r for r in succ_fixed if r["Method"] == actual_best), None)
            if best_fixed_r is not None:
                adapt_rmse = down_adapt["mean_check_rmse"]
                fixed_rmse = best_fixed_r["Held-out Check RMSE"]
                if adapt_rmse < fixed_rmse - 0.01:
                    comp_cat = "BETTER"
                elif abs(adapt_rmse - fixed_rmse) <= 0.05:
                    comp_cat = "SIMILAR"
                else:
                    comp_cat = "WORSE"
            else:
                comp_cat = "BETTER"  # Only adaptive succeeded

            correct_sel = "Yes" if (final_m == actual_best or comp_cat in ["BETTER", "SIMILAR"]) else "No"

            routing_decisions.append({
                "Pair": p_id,
                "Primary Selected": adapt_res["primary_choice"],
                "Rule Triggered": adapt_res["decision"]["rule_triggered"],
                "Decision Reason": "; ".join(adapt_res["decision"]["reasons"]),
                "Quality Gate Passed?": "Yes" if adapt_res["quality_gate"]["passed"] else "No",
                "Fallback Used?": fb_used,
                "Fallback Target": adapt_res.get("fallback_choice", "None"),
                "Final Matcher": final_m,
                "Actual Best Matcher": actual_best,
                "Selection Correct?": correct_sel,
                "Comparison Category": comp_cat,
            })

            if adapt_res["fallback_used"]:
                failure_records.append({
                    "Pair": p_id,
                    "Method": f"Adaptive ({adapt_res['primary_choice']})",
                    "Failure Stage": "quality_gate",
                    "Failure Reason": adapt_res["fallback_reason"],
                    "Recovery Event": f"Recovered via {adapt_res['fallback_choice']} fallback (RMSE: {down_adapt['mean_check_rmse']:.4f} px)",
                })
        else:
            all_results.append({
                "Pair": p_id,
                "Method": "Adaptive",
                "Selected Matcher": adapt_res.get("primary_choice", "Unknown"),
                "Fallback Used?": "Yes" if adapt_res.get("fallback_used", False) else "No",
                "Source Res": src_res,
                "Ref Res": ref_res,
                "Contrast": contrast_str,
                "Texture": texture_str,
                "Candidate Matches": 0,
                "Initial Inliers": 0,
                "Final Inliers": 0,
                "Final Inlier Ratio": 0.0,
                "Fit RMSE": np.nan,
                "Held-out Check RMSE": np.nan,
                "Spatial Occupancy": 0.0,
                "Spatial CV": np.nan,
                "Runtime": round(adapt_res["runtime"], 2),
                "Status": f"Failed: {adapt_res.get('failure_reason', 'unknown')}",
                "Decision Reason": "Adaptive registration failed",
            })
            routing_decisions.append({
                "Pair": p_id,
                "Primary Selected": adapt_res.get("primary_choice", "Unknown"),
                "Rule Triggered": adapt_res.get("decision", {}).get("rule_triggered", "None"),
                "Decision Reason": "Failed",
                "Quality Gate Passed?": "No",
                "Fallback Used?": "Yes",
                "Fallback Target": adapt_res.get("fallback_choice", "None"),
                "Final Matcher": "None",
                "Actual Best Matcher": actual_best,
                "Selection Correct?": "No",
                "Comparison Category": "WORSE",
            })
            failure_records.append({
                "Pair": p_id,
                "Method": "Adaptive",
                "Failure Stage": "fallback_exhausted",
                "Failure Reason": adapt_res.get("failure_reason", "unknown"),
                "Recovery Event": "Failed",
            })

    # DataFrames
    df_results = pd.DataFrame(all_results)
    df_decisions = pd.DataFrame(routing_decisions)
    df_failures = pd.DataFrame(failure_records) if failure_records else pd.DataFrame(columns=["Pair", "Method", "Failure Stage", "Failure Reason", "Recovery Event"])

    # Output 1: adaptive_results.csv
    p_res = os.path.join(output_dir, "adaptive_results.csv")
    df_results.to_csv(p_res, index=False)

    # Output 3: routing_decisions.csv
    p_dec = os.path.join(output_dir, "routing_decisions.csv")
    df_decisions.to_csv(p_dec, index=False)

    # Output 4: failure_analysis.csv
    p_fail = os.path.join(output_dir, "failure_analysis.csv")
    df_failures.to_csv(p_fail, index=False)

    # Output 2: adaptive_summary.csv (Method aggregate summary)
    agg_rows = []
    for m in ["SIFT", "LoFTR", "SuperGlue", "Adaptive"]:
        sub = df_results[df_results["Method"] == m]
        sub_succ = sub[sub["Status"] == "Success"]
        n_succ = len(sub_succ)
        n_tot = len(sub)
        succ_rate = round((n_succ / n_tot) * 100.0, 1) if n_tot > 0 else 0.0

        mean_chk = round(sub_succ["Held-out Check RMSE"].mean(), 4) if n_succ > 0 else np.nan
        med_chk = round(sub_succ["Held-out Check RMSE"].median(), 4) if n_succ > 0 else np.nan
        mean_ratio = round(sub_succ["Final Inlier Ratio"].mean(), 4) if n_succ > 0 else np.nan
        mean_occ = round(sub_succ["Spatial Occupancy"].mean(), 4) if n_succ > 0 else np.nan
        mean_cv = round(sub_succ["Spatial CV"].mean(), 4) if n_succ > 0 else np.nan
        mean_rt = round(sub_succ["Runtime"].mean(), 2) if n_succ > 0 else np.nan

        agg_rows.append({
            "Method": m,
            "Successful Pairs": n_succ,
            "Total Pairs": n_tot,
            "Success Rate (%)": succ_rate,
            "Mean Check RMSE": mean_chk,
            "Median Check RMSE": med_chk,
            "Mean Inlier Ratio": mean_ratio,
            "Mean Spatial Occupancy": mean_occ,
            "Mean Spatial CV": mean_cv,
            "Mean Runtime (s)": mean_rt,
        })
    df_summary = pd.DataFrame(agg_rows)
    p_sum = os.path.join(output_dir, "adaptive_summary.csv")
    df_summary.to_csv(p_sum, index=False)

    # Generate the 5 required plots
    plots = generate_adaptive_plots(df_results, df_decisions, df_summary, output_dir)

    if progress_callback:
        progress_callback(100, "Adaptive matcher benchmark complete.")

    return {
        "df_results": df_results,
        "df_summary": df_summary,
        "df_decisions": df_decisions,
        "df_failures": df_failures,
        "plots": plots,
    }


def generate_adaptive_plots(df_results, df_decisions, df_summary, output_dir):
    """
    Generates the 5 required comparative plots.
    """
    plots = {}
    methods = ["SIFT", "LoFTR", "SuperGlue", "Adaptive"]
    colors = {"SIFT": "#58a6ff", "LoFTR": "#3fb950", "SuperGlue": "#bc8cff", "Adaptive": "#f0883e"}
    pairs = sorted(df_results["Pair"].unique())

    plt.style.use("dark_background")
    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "font.family": "sans-serif"})

    # Plot 1: Fixed Matcher vs Adaptive Check RMSE
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    x = np.arange(len(pairs))
    width = 0.18
    for i, m in enumerate(methods):
        vals = []
        for p in pairs:
            row = df_results[(df_results["Pair"] == p) & (df_results["Method"] == m)]
            val = row["Held-out Check RMSE"].iloc[0] if not row.empty and row["Status"].iloc[0] == "Success" else np.nan
            vals.append(val if not np.isnan(val) else 0.0)
        ax.bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    ax.set_xticks(x); ax.set_xticklabels(pairs, color="#c9d1d9")
    ax.set_ylabel("Held-out Check RMSE (px)", color="#c9d1d9")
    ax.set_title("Fixed Matchers vs. Adaptive Matcher: Held-Out Check RMSE", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.legend(facecolor="#161b22", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p1 = os.path.join(output_dir, "fixed_vs_adaptive_check_rmse.png")
    fig.savefig(p1, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["check_rmse"] = p1

    # Plot 2: Fixed Matcher vs Adaptive Runtime
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    for i, m in enumerate(methods):
        vals = []
        for p in pairs:
            row = df_results[(df_results["Pair"] == p) & (df_results["Method"] == m)]
            val = row["Runtime"].iloc[0] if not row.empty else 0.0
            vals.append(val)
        ax.bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    ax.set_xticks(x); ax.set_xticklabels(pairs, color="#c9d1d9")
    ax.set_ylabel("Runtime (seconds)", color="#c9d1d9")
    ax.set_title("Fixed Matchers vs. Adaptive Matcher: End-to-End Runtime", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.legend(facecolor="#161b22", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p2 = os.path.join(output_dir, "fixed_vs_adaptive_runtime.png")
    fig.savefig(p2, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["runtime"] = p2

    # Plot 3: Fixed Matcher vs Adaptive Spatial Occupancy
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    for i, m in enumerate(methods):
        vals = []
        for p in pairs:
            row = df_results[(df_results["Pair"] == p) & (df_results["Method"] == m)]
            val = row["Spatial Occupancy"].iloc[0] * 100.0 if not row.empty and row["Status"].iloc[0] == "Success" else 0.0
            vals.append(val)
        ax.bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    ax.set_xticks(x); ax.set_xticklabels(pairs, color="#c9d1d9")
    ax.set_ylabel("Spatial Occupancy (%)", color="#c9d1d9")
    ax.set_ylim(0, 115)
    ax.set_title("Fixed Matchers vs. Adaptive Matcher: 3x3 Spatial Occupancy", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.legend(facecolor="#161b22", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p3 = os.path.join(output_dir, "fixed_vs_adaptive_spatial_occupancy.png")
    fig.savefig(p3, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["spatial_occupancy"] = p3

    # Plot 4: Matcher-Selection Accuracy & Decision Distribution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax1.set_facecolor("#161b22"); ax2.set_facecolor("#161b22")

    # Left: Selection Correctness
    corr_counts = df_decisions["Selection Correct?"].value_counts()
    c_labels = list(corr_counts.index)
    c_vals = [int(v) for v in corr_counts.values]
    c_colors = ["#3fb950" if l == "Yes" else "#f85149" for l in c_labels]
    ax1.bar(c_labels, c_vals, color=c_colors, width=0.45, edgecolor="#30363d")
    ax1.set_title("Matcher Selection Viability (Accuracy)", color="#58a6ff", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Number of Pairs", color="#c9d1d9")
    for idx_b, val_b in enumerate(c_vals):
        ax1.text(idx_b, val_b + 0.1, f"{val_b} pairs", ha="center", color="#c9d1d9", fontweight="bold")
    ax1.set_ylim(0, max(c_vals) + 1.2)
    ax1.grid(True, linestyle="--", alpha=0.25, color="#8b949e")

    # Right: Final Matchers Chosen
    m_counts = df_decisions["Final Matcher"].value_counts()
    m_labels = list(m_counts.index)
    m_vals = [int(v) for v in m_counts.values]
    m_c = [colors.get(l, "#8b949e") for l in m_labels]
    ax2.bar(m_labels, m_vals, color=m_c, width=0.45, edgecolor="#30363d")
    ax2.set_title("Adaptive Matcher Final Selection Count", color="#58a6ff", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Count", color="#c9d1d9")
    for idx_b, val_b in enumerate(m_vals):
        ax2.text(idx_b, val_b + 0.1, f"{val_b}", ha="center", color="#c9d1d9", fontweight="bold")
    ax2.set_ylim(0, max(m_vals) + 1.2)
    ax2.grid(True, linestyle="--", alpha=0.25, color="#8b949e")

    plt.tight_layout()
    p4 = os.path.join(output_dir, "matcher_selection_accuracy.png")
    fig.savefig(p4, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["selection_accuracy"] = p4

    # Plot 5: Fallback Frequency
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    fb_counts = df_decisions["Fallback Used?"].value_counts()
    fb_labels = [f"Primary Passed ({fb_counts.get('No', 0)})", f"Fallback Triggered ({fb_counts.get('Yes', 0)})"]
    fb_vals = [int(fb_counts.get("No", 0)), int(fb_counts.get("Yes", 0))]
    ax.pie(fb_vals, labels=fb_labels, autopct="%1.1f%%", colors=["#3fb950", "#d29922"], textprops={"color": "#c9d1d9", "fontweight": "bold"},
           wedgeprops={"edgecolor": "#30363d", "linewidth": 1.5}, startangle=140)
    ax.set_title("Adaptive Router: Primary Pass vs. Fallback Frequency", color="#58a6ff", fontsize=11, fontweight="bold")
    plt.tight_layout()
    p5 = os.path.join(output_dir, "fallback_frequency.png")
    fig.savefig(p5, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["fallback_frequency"] = p5

    return plots


if __name__ == "__main__":
    print("Starting Adaptive Matcher v1 Benchmark across validation pairs...")
    res = run_full_adaptive_benchmark()
    print("\n" + "=" * 90)
    print("                         ADAPTIVE RESULTS (ALL PAIRS x METHODS)                      ")
    print("=" * 90)
    print(res["df_results"].to_string(index=False))
    print("=" * 90)
    print("\n" + "=" * 90)
    print("                         ROUTING DECISIONS & VIABILITY TABLE                         ")
    print("=" * 90)
    print(res["df_decisions"].to_string(index=False))
    print("=" * 90)
    print("\n" + "=" * 90)
    print("                         AGGREGATE SUMMARY TABLE                                     ")
    print("=" * 90)
    print(res["df_summary"].to_string(index=False))
    print("=" * 90)
    print("\n" + "=" * 90)
    print("                         FAILURE & RECOVERY ANALYSIS                                 ")
    print("=" * 90)
    print(res["df_failures"].to_string(index=False))
    print("=" * 90)
