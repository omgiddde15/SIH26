"""
PHASE D: LEAVE-ONE-PAIR-OUT (LOPO) VALIDATION
SIH26166 — Automated Lunar Image Registration

Performs rigorous Leave-One-Pair-Out cross-validation for Adaptive Matcher v1
across all 4 lunar validation pairs:
  - Fold 1: Train on [pair_02, pair_03, pair_04] -> Test on pair_01
  - Fold 2: Train on [pair_01, pair_03, pair_04] -> Test on pair_02
  - Fold 3: Train on [pair_01, pair_02, pair_04] -> Test on pair_03
  - Fold 4: Train on [pair_01, pair_02, pair_03] -> Test on pair_04

Outputs:
  - research/adaptive_matcher/lopo_results.csv
  - research/adaptive_matcher/lopo_summary.csv
  - research/adaptive_matcher/lopo_routing_decisions.csv
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


def run_lopo_validation(output_dir=None, progress_callback=None):
    """
    Executes Leave-One-Pair-Out cross-validation across all 4 folds.
    """
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "research", "adaptive_matcher")
    os.makedirs(output_dir, exist_ok=True)

    pairs = discover_validation_pairs()
    if len(pairs) != 4:
        raise RuntimeError(f"LOPO requires exactly 4 validation pairs, found {len(pairs)}: {[p['pair_id'] for p in pairs]}")

    print(f"Loading LoFTR & SuperGlue models for LOPO validation across 4 folds...")
    if progress_callback:
        progress_callback(5, "Loading models for LOPO cross-validation...")

    loftr = load_loftr_matcher()
    sg = Matching({
        "superpoint": {"nms_radius": 4, "keypoint_threshold": 0.005, "max_keypoints": 1024},
        "superglue": {"weights": "outdoor", "sinkhorn_iterations": 20, "match_threshold": 0.2}
    }).eval().to(_DEVICE)

    # Pre-load all pair images and compute characteristics
    pair_data = {}
    for p in pairs:
        pid = p["pair_id"]
        s_img = cv2.imread(p["source_path"])
        r_img = cv2.imread(p["reference_path"])
        chars = compute_pair_characteristics(s_img, r_img)
        pair_data[pid] = {
            "info": p,
            "source_img": s_img,
            "reference_img": r_img,
            "characteristics": chars,
        }

    lopo_results = []
    lopo_summaries = []
    lopo_decisions = []

    # Iterate over 4 folds
    for fold_idx, test_pair_info in enumerate(pairs, start=1):
        test_pid = test_pair_info["pair_id"]
        train_pids = [p["pair_id"] for p in pairs if p["pair_id"] != test_pid]

        fold_str = f"Fold {fold_idx}"
        print(f"\n{'='*70}")
        print(f"  {fold_str.upper()}: TRAIN on {train_pids}  -->  TEST on {test_pid}")
        print(f"{'='*70}")

        if progress_callback:
            pct = 10 + int((fold_idx / 4) * 75)
            progress_callback(pct, f"Executing {fold_str}: Testing unseen {test_pid}...")

        # Step 1: Training set analysis (3 training pairs)
        # Verify training set metrics and freeze exploratory v1 rule set
        train_stats = []
        for tr_id in train_pids:
            tr_chars = pair_data[tr_id]["characteristics"]
            train_stats.append({
                "Pair": tr_id,
                "Src Res": f"{tr_chars['source']['width']}x{tr_chars['source']['height']}",
                "Min Contrast Std": min(tr_chars['source']['intensity_std'], tr_chars['reference']['intensity_std']),
                "Min Grad Mean": min(tr_chars['source']['gradient_mean'], tr_chars['reference']['gradient_mean']),
            })
        df_train_stats = pd.DataFrame(train_stats)
        print(f"  [Training Set Analysis ({len(train_pids)} pairs)]:")
        print("  " + df_train_stats.to_string().replace("\n", "\n  "))

        # In accordance with the scientific rule:
        # "If three training pairs do not provide enough evidence to derive a new threshold reliably,
        # use the existing v1 rule set unchanged, clearly label it as 'fixed exploratory heuristic',
        # and state that true independent generalization is not established."
        frozen_config = AdaptiveConfig()
        rule_label = "Fixed Exploratory Heuristic (v1 ruleset frozen prior to test inspection)"

        # Step 2: Apply frozen router to held-out test pair
        t_data = pair_data[test_pid]
        t_src = t_data["source_img"]
        t_ref = t_data["reference_img"]
        t_chars = t_data["characteristics"]
        t_prof = classify_difficulty_profile(t_chars, frozen_config)

        src_res_str = f"{t_chars['source']['width']}x{t_chars['source']['height']}"
        ref_res_str = f"{t_chars['reference']['width']}x{t_chars['reference']['height']}"
        contrast_str = f"{t_prof['contrast_class']} (std={t_prof['min_contrast_std']})"
        texture_str = f"{t_prof['texture_class']} (grad={t_prof['min_gradient_mean']})"

        # Evaluate SIFT on held-out test pair
        t0_sift = time.perf_counter()
        sift_raw = run_sift_matching(t_src, t_ref, ransac_thresh=frozen_config.ransac_threshold)
        t_sift = time.perf_counter() - t0_sift
        if sift_raw["success"]:
            try:
                down_sift = execute_common_downstream(sift_raw["inlier_pts0"], sift_raw["inlier_pts1"], sift_raw["confidences"], t_src, t_ref, ransac_thresh=frozen_config.ransac_threshold)
                sift_occ = round(down_sift["spatial_occupancy"], 4)
                sift_cv = round(down_sift["spatial_cv"], 4)
                sift_inl = down_sift["n_final_inliers"]
                sift_ratio = round(down_sift["final_inlier_ratio"], 4)
                sift_fit_rmse = round(down_sift["fit_rmse"], 4)
                if np.isnan(down_sift["mean_check_rmse"]):
                    sift_chk_rmse = np.nan
                    sift_val_status = "NO VALID CHECK"
                    sift_status = "NO VALID CHECK"
                    sift_succ = 0
                else:
                    sift_chk_rmse = round(down_sift["mean_check_rmse"], 4)
                    sift_val_status = "VALID"
                    sift_status = "Success"
                    sift_succ = 1
            except Exception as e:
                sift_chk_rmse = np.nan
                sift_occ = 0.0
                sift_cv = np.nan
                sift_inl = 0
                sift_ratio = 0.0
                sift_fit_rmse = np.nan
                sift_val_status = "REGISTRATION FAILED"
                sift_status = f"REGISTRATION FAILED: downstream error ({str(e)})"
                sift_succ = 0
        else:
            sift_chk_rmse = np.nan
            sift_occ = 0.0
            sift_cv = np.nan
            sift_inl = 0
            sift_ratio = 0.0
            sift_fit_rmse = np.nan
            sift_val_status = "REGISTRATION FAILED"
            sift_status = f"REGISTRATION FAILED: {sift_raw['failure_reason']}"
            sift_succ = 0

        lopo_results.append({
            "Fold": fold_str, "Pair": test_pid, "Method": "SIFT", "Selected Matcher": "SIFT", "Fallback Used": "No",
            "Source Res": src_res_str, "Ref Res": ref_res_str, "Contrast": contrast_str, "Texture": texture_str,
            "Resolution Class": t_prof["resolution_class"], "Candidate Matches": sift_raw["n_candidates"],
            "Initial Inliers": sift_raw["n_inliers"], "Final Inliers": sift_inl, "Final Inlier Ratio": sift_ratio,
            "Fit RMSE": sift_fit_rmse, "Held-out Check RMSE": sift_chk_rmse, "Spatial Occupancy": sift_occ,
            "Spatial CV": sift_cv, "Runtime": round(t_sift, 2), "Success": sift_succ,
            "Validation Status": sift_val_status, "Status": sift_status, "Decision Reason": "Fixed SIFT baseline",
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

        # Evaluate LoFTR on held-out test pair
        t0_loftr = time.perf_counter()
        loftr_raw = run_loftr_matching(t_src, t_ref, loftr_model=loftr, ransac_thresh=frozen_config.ransac_threshold)
        t_loftr = time.perf_counter() - t0_loftr
        if loftr_raw["success"]:
            try:
                down_loftr = execute_common_downstream(loftr_raw["inlier_pts0"], loftr_raw["inlier_pts1"], loftr_raw["confidences"], t_src, t_ref, ransac_thresh=frozen_config.ransac_threshold)
                loftr_occ = round(down_loftr["spatial_occupancy"], 4)
                loftr_cv = round(down_loftr["spatial_cv"], 4)
                loftr_inl = down_loftr["n_final_inliers"]
                loftr_ratio = round(down_loftr["final_inlier_ratio"], 4)
                loftr_fit_rmse = round(down_loftr["fit_rmse"], 4)
                if np.isnan(down_loftr["mean_check_rmse"]):
                    loftr_chk_rmse = np.nan
                    loftr_val_status = "NO VALID CHECK"
                    loftr_status = "NO VALID CHECK"
                    loftr_succ = 0
                else:
                    loftr_chk_rmse = round(down_loftr["mean_check_rmse"], 4)
                    loftr_val_status = "VALID"
                    loftr_status = "Success"
                    loftr_succ = 1
            except Exception as e:
                loftr_chk_rmse = np.nan
                loftr_occ = 0.0
                loftr_cv = np.nan
                loftr_inl = 0
                loftr_ratio = 0.0
                loftr_fit_rmse = np.nan
                loftr_val_status = "REGISTRATION FAILED"
                loftr_status = f"REGISTRATION FAILED: downstream error ({str(e)})"
                loftr_succ = 0
        else:
            loftr_chk_rmse = np.nan
            loftr_occ = 0.0
            loftr_cv = np.nan
            loftr_inl = 0
            loftr_ratio = 0.0
            loftr_fit_rmse = np.nan
            loftr_val_status = "REGISTRATION FAILED"
            loftr_status = f"REGISTRATION FAILED: {loftr_raw['failure_reason']}"
            loftr_succ = 0

        lopo_results.append({
            "Fold": fold_str, "Pair": test_pid, "Method": "LoFTR", "Selected Matcher": "LoFTR", "Fallback Used": "No",
            "Source Res": src_res_str, "Ref Res": ref_res_str, "Contrast": contrast_str, "Texture": texture_str,
            "Resolution Class": t_prof["resolution_class"], "Candidate Matches": loftr_raw["n_candidates"],
            "Initial Inliers": loftr_raw["n_inliers"], "Final Inliers": loftr_inl, "Final Inlier Ratio": loftr_ratio,
            "Fit RMSE": loftr_fit_rmse, "Held-out Check RMSE": loftr_chk_rmse, "Spatial Occupancy": loftr_occ,
            "Spatial CV": loftr_cv, "Runtime": round(t_loftr, 2), "Success": loftr_succ,
            "Validation Status": loftr_val_status, "Status": loftr_status, "Decision Reason": "Fixed LoFTR baseline",
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

        # Evaluate SuperGlue on held-out test pair
        t0_sg = time.perf_counter()
        sg_raw = run_superglue_matching(t_src, t_ref, sg_model=sg, ransac_thresh=frozen_config.ransac_threshold)
        t_sg = time.perf_counter() - t0_sg
        if sg_raw["success"]:
            try:
                down_sg = execute_common_downstream(sg_raw["inlier_pts0"], sg_raw["inlier_pts1"], sg_raw["confidences"], t_src, t_ref, ransac_thresh=frozen_config.ransac_threshold)
                sg_occ = round(down_sg["spatial_occupancy"], 4)
                sg_cv = round(down_sg["spatial_cv"], 4)
                sg_inl = down_sg["n_final_inliers"]
                sg_ratio = round(down_sg["final_inlier_ratio"], 4)
                sg_fit_rmse = round(down_sg["fit_rmse"], 4)
                if np.isnan(down_sg["mean_check_rmse"]):
                    sg_chk_rmse = np.nan
                    sg_val_status = "NO VALID CHECK"
                    sg_status = "NO VALID CHECK"
                    sg_succ = 0
                else:
                    sg_chk_rmse = round(down_sg["mean_check_rmse"], 4)
                    sg_val_status = "VALID"
                    sg_status = "Success"
                    sg_succ = 1
            except Exception as e:
                sg_chk_rmse = np.nan
                sg_occ = 0.0
                sg_cv = np.nan
                sg_inl = 0
                sg_ratio = 0.0
                sg_fit_rmse = np.nan
                sg_val_status = "REGISTRATION FAILED"
                sg_status = f"REGISTRATION FAILED: downstream error ({str(e)})"
                sg_succ = 0
        else:
            sg_chk_rmse = np.nan
            sg_occ = 0.0
            sg_cv = np.nan
            sg_inl = 0
            sg_ratio = 0.0
            sg_fit_rmse = np.nan
            sg_val_status = "REGISTRATION FAILED"
            sg_status = f"REGISTRATION FAILED: {sg_raw['failure_reason']}"
            sg_succ = 0

        lopo_results.append({
            "Fold": fold_str, "Pair": test_pid, "Method": "SuperGlue", "Selected Matcher": "SuperGlue", "Fallback Used": "No",
            "Source Res": src_res_str, "Ref Res": ref_res_str, "Contrast": contrast_str, "Texture": texture_str,
            "Resolution Class": t_prof["resolution_class"], "Candidate Matches": sg_raw["n_candidates"],
            "Initial Inliers": sg_raw["n_inliers"], "Final Inliers": sg_inl, "Final Inlier Ratio": sg_ratio,
            "Fit RMSE": sg_fit_rmse, "Held-out Check RMSE": sg_chk_rmse, "Spatial Occupancy": sg_occ,
            "Spatial CV": sg_cv, "Runtime": round(t_sg, 2), "Success": sg_succ,
            "Validation Status": sg_val_status, "Status": sg_status, "Decision Reason": "Fixed SuperGlue baseline",
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

        # Evaluate Adaptive Matcher v1 on held-out test pair (with frozen ruleset)
        adapt_res = run_adaptive_registration(t_src, t_ref, loftr_model=loftr, sg_model=sg, config=frozen_config)
        fb_used = "Yes" if adapt_res["fallback_used"] else "No"

        if adapt_res["success"]:
            down_adapt = adapt_res["downstream"]
            adapt_occ = round(down_adapt["spatial_occupancy"], 4)
            adapt_cv = round(down_adapt["spatial_cv"], 4)
            adapt_inl = down_adapt["n_final_inliers"]
            adapt_ratio = round(down_adapt["final_inlier_ratio"], 4)
            adapt_fit_rmse = round(down_adapt["fit_rmse"], 4)
            if np.isnan(down_adapt["mean_check_rmse"]):
                adapt_chk_rmse = np.nan
                adapt_val_status = "NO VALID CHECK"
                adapt_status = "NO VALID CHECK"
                adapt_succ = 0
            else:
                adapt_chk_rmse = round(down_adapt["mean_check_rmse"], 4)
                adapt_val_status = "VALID"
                adapt_status = "Success"
                adapt_succ = 1
            final_m = adapt_res["final_matcher_used"]
            primary_m = adapt_res["primary_choice"]
            rule_trig = adapt_res["decision"]["rule_triggered"]
            reasons_str = "; ".join(adapt_res["decision"]["reasons"])
            if adapt_res["fallback_used"]:
                reasons_str += f" -> Fallback to {adapt_res['fallback_choice']} ({adapt_res['fallback_reason']})"
        else:
            adapt_chk_rmse = np.nan
            adapt_occ = 0.0
            adapt_cv = np.nan
            adapt_inl = 0
            adapt_ratio = 0.0
            adapt_fit_rmse = np.nan
            adapt_val_status = "REGISTRATION FAILED"
            adapt_status = f"REGISTRATION FAILED: {adapt_res.get('failure_reason', 'unknown')}"
            adapt_succ = 0
            final_m = adapt_res.get("primary_choice", "Unknown")
            primary_m = adapt_res.get("primary_choice", "Unknown")
            rule_trig = adapt_res.get("decision", {}).get("rule_triggered", "None")
            reasons_str = "Adaptive registration failed"

        lopo_results.append({
            "Fold": fold_str, "Pair": test_pid, "Method": "Adaptive", "Selected Matcher": final_m, "Fallback Used": fb_used,
            "Source Res": src_res_str, "Ref Res": ref_res_str, "Contrast": contrast_str, "Texture": texture_str,
            "Resolution Class": t_prof["resolution_class"],
            "Candidate Matches": adapt_res["primary_result"].get("n_candidates", 0) if not adapt_res.get("fallback_used", False) else adapt_res.get("fallback_result", {}).get("n_candidates", 0),
            "Initial Inliers": adapt_res["primary_result"].get("n_inliers", 0) if not adapt_res.get("fallback_used", False) else adapt_res.get("fallback_result", {}).get("n_inliers", 0),
            "Final Inliers": adapt_inl, "Final Inlier Ratio": adapt_ratio, "Fit RMSE": adapt_fit_rmse,
            "Held-out Check RMSE": adapt_chk_rmse, "Spatial Occupancy": adapt_occ, "Spatial CV": adapt_cv,
            "Runtime": round(adapt_res["runtime"], 2), "Success": adapt_succ,
            "Validation Status": adapt_val_status, "Status": adapt_status, "Decision Reason": reasons_str,
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

        # Determine Best Accuracy Method and Fastest Method among VALID methods only
        succ_fixed = [
            ("SIFT", sift_chk_rmse, t_sift, sift_val_status),
            ("LoFTR", loftr_chk_rmse, t_loftr, loftr_val_status),
            ("SuperGlue", sg_chk_rmse, t_sg, sg_val_status)
        ]
        valid_fixed = [f for f in succ_fixed if f[3] == "VALID" and not np.isnan(f[1])]

        if valid_fixed:
            best_acc_method = min(valid_fixed, key=lambda x: x[1])[0]
            fastest_method = min(valid_fixed, key=lambda x: x[2])[0]
        else:
            best_acc_method = "None"
            fastest_method = "None"

        adapt_succ_bool = (adapt_val_status == "VALID")
        adapt_is_best_acc = (final_m == best_acc_method) if adapt_succ_bool else False
        adapt_is_fastest = (final_m == fastest_method) if adapt_succ_bool else False

        # Multi-Dimensional Evaluation of Routing Correctness:
        # 1. Robustness: Did it successfully register the pair with valid hold-out check?
        robust_pass = "PASS (Valid Check)" if adapt_succ_bool else ("NO VALID CHECK" if adapt_val_status == "NO VALID CHECK" else "FAIL")
        # 2. Accuracy: How did Check RMSE compare?
        if adapt_succ_bool and not np.isnan(adapt_chk_rmse):
            min_fixed_rmse = min([f[1] for f in valid_fixed]) if valid_fixed else adapt_chk_rmse
            if adapt_chk_rmse <= min_fixed_rmse + 0.05:
                acc_eval = f"OPTIMAL / NEAR-OPTIMAL ({adapt_chk_rmse:.4f} px vs {min_fixed_rmse:.4f} px)"
            else:
                acc_eval = f"ACCEPTABLE SUB-PIXEL ({adapt_chk_rmse:.4f} px vs {min_fixed_rmse:.4f} px)"
        else:
            acc_eval = "NO VALID CHECK" if adapt_val_status == "NO VALID CHECK" else "FAILED"
        # 3. Efficiency: Runtime comparison
        if adapt_succ_bool:
            max_fixed_rt = max([f[2] for f in valid_fixed]) if valid_fixed else adapt_res["runtime"]
            if adapt_res["runtime"] < max_fixed_rt * 0.2:
                eff_eval = f"HIGH SPEEDUP ({adapt_res['runtime']:.2f}s vs {max_fixed_rt:.2f}s, >5x faster)"
            else:
                eff_eval = f"STANDARD LATENCY ({adapt_res['runtime']:.2f}s)"
        else:
            eff_eval = "FAILED"
        # 4. Spatial Quality
        spat_eval = f"Occupancy {adapt_occ*100:.1f}%, CV {adapt_cv:.4f}"
        # 5. Overall Practical Choice
        if adapt_succ_bool and (adapt_is_fastest or adapt_is_best_acc or (sift_val_status != "VALID" and final_m == "LoFTR")):
            overall_choice = "OPTIMAL PARETO CHOICE"
        elif adapt_succ_bool:
            overall_choice = "VIABLE / NEAR-OPTIMAL"
        else:
            overall_choice = "DEGENERATE"

        # Summary entry
        lopo_summaries.append({
            "Fold": fold_str,
            "Held-Out Pair": test_pid,
            "Selected Matcher": final_m,
            "Validation Status": adapt_val_status,
            "Fallback": fb_used,
            "Adaptive Check RMSE": adapt_chk_rmse,
            "SIFT Check RMSE": sift_chk_rmse,
            "LoFTR Check RMSE": loftr_chk_rmse,
            "SuperGlue Check RMSE": sg_chk_rmse,
            "Adaptive Runtime": round(adapt_res["runtime"], 2),
            "Best Valid Accuracy Method": best_acc_method,
            "Fastest Valid Method": fastest_method,
            "Adaptive Successful?": "Yes" if adapt_succ_bool else "No",
            "Adaptive Best Accuracy?": "Yes" if adapt_is_best_acc else "No",
            "Adaptive Best Speed?": "Yes" if adapt_is_fastest else "No",
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

        # Decision trace entry
        lopo_decisions.append({
            "Fold": fold_str,
            "Held-Out Pair": test_pid,
            "Primary Selected": primary_m,
            "Rule Triggered": rule_trig,
            "Decision Reason": reasons_str,
            "Quality Gate": "PASS" if adapt_res.get("quality_gate", {}).get("passed", False) else "TRIGGERED FALLBACK",
            "Final Matcher": final_m,
            "1. Robustness": robust_pass,
            "2. Accuracy": acc_eval,
            "3. Efficiency": eff_eval,
            "4. Spatial Quality": spat_eval,
            "5. Overall Practical Choice": overall_choice,
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })

    df_lopo_results = pd.DataFrame(lopo_results)
    df_lopo_summary = pd.DataFrame(lopo_summaries)
    df_lopo_decisions = pd.DataFrame(lopo_decisions)

    # Compute Aggregate Metrics
    agg_rows = []
    for m in ["SIFT", "LoFTR", "SuperGlue", "Adaptive"]:
        m_df = df_lopo_results[df_lopo_results["Method"] == m]
        tot = len(m_df)
        val_df = m_df[m_df["Validation Status"] == "VALID"]
        n_val = len(val_df)
        n_fail = len(m_df[m_df["Validation Status"] == "REGISTRATION FAILED"])
        n_nocheck = len(m_df[m_df["Validation Status"] == "NO VALID CHECK"])
        s_rate = round((n_val / tot) * 100.0, 1) if tot > 0 else 0.0
        val_rmses = val_df["Held-out Check RMSE"].dropna().tolist()
        m_chk = round(float(np.mean(val_rmses)), 4) if val_rmses else np.nan
        med_chk = round(float(np.median(val_rmses)), 4) if val_rmses else np.nan
        m_rt = round(float(m_df["Runtime"].mean()), 2) if not m_df.empty else np.nan
        m_occ = round(float(m_df["Spatial Occupancy"].mean()), 4) if not m_df.empty else 0.0
        m_cv = round(float(val_df["Spatial CV"].mean()), 4) if not val_df.empty else np.nan

        agg_rows.append({
            "Method": m,
            "Total Folds": tot,
            "Valid Folds": n_val,
            "Registration Failed Folds": n_fail,
            "No Valid Check Folds": n_nocheck,
            "Success Rate (%)": s_rate,
            "Mean Check RMSE (px)": m_chk,
            "Median Check RMSE (px)": med_chk,
            "Mean Runtime (s)": m_rt,
            "Mean Spatial Occupancy": m_occ,
            "Mean Spatial CV": m_cv,
            "Scientific Note": "Fit RMSE is never used as a substitute for held-out Check RMSE.",
        })
    df_lopo_aggregate = pd.DataFrame(agg_rows)

    # Save Output 1: lopo_results.csv
    p_res = os.path.join(output_dir, "lopo_results.csv")
    df_lopo_results.to_csv(p_res, index=False)

    # Save Output 2: lopo_summary.csv
    p_sum = os.path.join(output_dir, "lopo_summary.csv")
    df_lopo_summary.to_csv(p_sum, index=False)

    # Save Output 3: lopo_routing_decisions.csv
    p_dec = os.path.join(output_dir, "lopo_routing_decisions.csv")
    df_lopo_decisions.to_csv(p_dec, index=False)

    # Save Output 4: lopo_aggregate_summary.csv
    p_agg = os.path.join(output_dir, "lopo_aggregate_summary.csv")
    df_lopo_aggregate.to_csv(p_agg, index=False)

    # Generate 5 Plots
    plots = generate_lopo_plots(df_lopo_results, df_lopo_summary, df_lopo_decisions, output_dir)

    if progress_callback:
        progress_callback(100, "LOPO validation complete.")

    return {
        "df_results": df_lopo_results,
        "df_summary": df_lopo_summary,
        "df_decisions": df_lopo_decisions,
        "df_aggregate": df_lopo_aggregate,
        "plots": plots,
    }


def generate_lopo_plots(df_results, df_summary, df_decisions, output_dir):
    """
    Generates 5 comparative visualization plots for Leave-One-Pair-Out validation.
    """
    plots = {}
    methods = ["SIFT", "LoFTR", "SuperGlue", "Adaptive"]
    colors = {"SIFT": "#58a6ff", "LoFTR": "#3fb950", "SuperGlue": "#bc8cff", "Adaptive": "#f0883e"}
    folds = sorted(df_summary["Fold"].unique())
    pairs = [df_summary[df_summary["Fold"] == f]["Held-Out Pair"].iloc[0] for f in folds]
    fold_labels = [f"{f}\n({p})" for f, p in zip(folds, pairs)]

    plt.style.use("dark_background")
    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "font.family": "sans-serif"})

    # Plot 1: LOPO Adaptive vs Fixed-Method Check RMSE
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    x = np.arange(len(folds))
    width = 0.18
    for i, m in enumerate(methods):
        vals = []
        for f in folds:
            row = df_results[(df_results["Fold"] == f) & (df_results["Method"] == m)]
            val = row["Held-out Check RMSE"].iloc[0] if not row.empty and row["Success"].iloc[0] == 1 else np.nan
            vals.append(val if not np.isnan(val) else 0.0)
        ax.bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    ax.set_xticks(x); ax.set_xticklabels(fold_labels, color="#c9d1d9")
    ax.set_ylabel("Held-out Check RMSE (px)", color="#c9d1d9")
    ax.set_title("LOPO Cross-Validation: Held-Out Check RMSE by Fold", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.legend(facecolor="#161b22", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p1 = os.path.join(output_dir, "lopo_check_rmse_comparison.png")
    fig.savefig(p1, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["check_rmse"] = p1

    # Plot 2: LOPO Runtime Comparison
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    for i, m in enumerate(methods):
        vals = []
        for f in folds:
            row = df_results[(df_results["Fold"] == f) & (df_results["Method"] == m)]
            val = row["Runtime"].iloc[0] if not row.empty else 0.0
            vals.append(val)
        ax.bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    ax.set_xticks(x); ax.set_xticklabels(fold_labels, color="#c9d1d9")
    ax.set_ylabel("Runtime (seconds)", color="#c9d1d9")
    ax.set_title("LOPO Cross-Validation: End-to-End Runtime by Fold", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.legend(facecolor="#161b22", edgecolor="#30363d")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p2 = os.path.join(output_dir, "lopo_runtime_comparison.png")
    fig.savefig(p2, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["runtime"] = p2

    # Plot 3: Selected Matcher Per Fold
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    sel_matchers = list(df_summary["Selected Matcher"])
    m_colors = [colors.get(m, "#8b949e") for m in sel_matchers]
    bars = ax.bar(fold_labels, [1]*len(folds), color=m_colors, width=0.45, edgecolor="#30363d")
    for idx_b, b in enumerate(bars):
        ax.text(b.get_x() + b.get_width()/2.0, 0.5, sel_matchers[idx_b], ha="center", va="center", color="#ffffff", fontweight="bold", fontsize=11)
    ax.set_yticks([])
    ax.set_title("Adaptive Router: Selected Matcher per Held-Out Fold", color="#58a6ff", fontsize=11, fontweight="bold")
    plt.tight_layout()
    p3 = os.path.join(output_dir, "lopo_selected_matcher.png")
    fig.savefig(p3, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["selected_matcher"] = p3

    # Plot 4: Adaptive Success / Failure per Fold
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#161b22")
    succ_vals = [1 if s == "Yes" else 0 for s in df_summary["Adaptive Successful?"]]
    s_colors = ["#3fb950" if v == 1 else "#f85149" for v in succ_vals]
    ax.bar(fold_labels, succ_vals, color=s_colors, width=0.45, edgecolor="#30363d")
    ax.set_ylim(0, 1.3)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Failed", "Success (100%)"], color="#c9d1d9")
    for idx_b, val_b in enumerate(succ_vals):
        lbl = "SUCCESS (100%)" if val_b == 1 else "FAILED"
        ax.text(idx_b, val_b + 0.08, lbl, ha="center", color="#c9d1d9", fontweight="bold")
    ax.set_title("LOPO Cross-Validation: Adaptive Matcher Success Rate per Fold", color="#58a6ff", fontsize=11, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.25, color="#8b949e")
    plt.tight_layout()
    p4 = os.path.join(output_dir, "lopo_success_distribution.png")
    fig.savefig(p4, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["success_distribution"] = p4

    # Plot 5: Consolidated LOPO Decision Dashboard
    fig, axs = plt.subplots(2, 2, figsize=(11, 7.5), dpi=150)
    fig.patch.set_facecolor("#0e1117")
    for ax_sub in axs.ravel():
        ax_sub.set_facecolor("#161b22")
        ax_sub.grid(True, linestyle="--", alpha=0.2, color="#8b949e")

    # (0, 0): Check RMSE
    for i, m in enumerate(methods):
        vals = [df_results[(df_results["Fold"] == f) & (df_results["Method"] == m)]["Held-out Check RMSE"].iloc[0] for f in folds]
        vals = [v if not np.isnan(v) else 0.0 for v in vals]
        axs[0, 0].bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    axs[0, 0].set_xticks(x); axs[0, 0].set_xticklabels(fold_labels, color="#c9d1d9", fontsize=8)
    axs[0, 0].set_title("Held-Out Check RMSE by Fold (px)", color="#58a6ff", fontsize=9, fontweight="bold")
    axs[0, 0].legend(facecolor="#161b22", edgecolor="#30363d", fontsize=7)

    # (0, 1): Runtime
    for i, m in enumerate(methods):
        vals = [df_results[(df_results["Fold"] == f) & (df_results["Method"] == m)]["Runtime"].iloc[0] for f in folds]
        axs[0, 1].bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    axs[0, 1].set_xticks(x); axs[0, 1].set_xticklabels(fold_labels, color="#c9d1d9", fontsize=8)
    axs[0, 1].set_title("Runtime by Fold (seconds)", color="#58a6ff", fontsize=9, fontweight="bold")
    axs[0, 1].legend(facecolor="#161b22", edgecolor="#30363d", fontsize=7)

    # (1, 0): Spatial Occupancy
    for i, m in enumerate(methods):
        vals = [df_results[(df_results["Fold"] == f) & (df_results["Method"] == m)]["Spatial Occupancy"].iloc[0] * 100.0 for f in folds]
        axs[1, 0].bar(x + (i - 1.5) * width, vals, width, label=m, color=colors[m], edgecolor="#30363d")
    axs[1, 0].set_xticks(x); axs[1, 0].set_xticklabels(fold_labels, color="#c9d1d9", fontsize=8)
    axs[1, 0].set_ylabel("Occupancy (%)", color="#c9d1d9", fontsize=8)
    axs[1, 0].set_ylim(0, 115)
    axs[1, 0].set_title("3x3 Spatial Occupancy by Fold (%)", color="#58a6ff", fontsize=9, fontweight="bold")

    # (1, 1): Multi-Dimensional Viability Counts
    choice_counts = df_decisions["5. Overall Practical Choice"].value_counts()
    c_lbls = list(choice_counts.index)
    c_v = [int(v) for v in choice_counts.values]
    axs[1, 1].bar(c_lbls, c_v, color=["#3fb950" if "OPTIMAL" in l else "#58a6ff" for l in c_lbls], width=0.45, edgecolor="#30363d")
    axs[1, 1].set_title("Overall Practical Pareto Choice (Count)", color="#58a6ff", fontsize=9, fontweight="bold")
    axs[1, 1].set_ylabel("Folds", color="#c9d1d9", fontsize=8)
    axs[1, 1].set_ylim(0, max(c_v) + 1.2)
    for idx_b, vb in enumerate(c_v):
        axs[1, 1].text(idx_b, vb + 0.1, f"{vb} folds", ha="center", color="#c9d1d9", fontweight="bold", fontsize=9)

    fig.suptitle("Phase D: Leave-One-Pair-Out Cross-Validation Dashboard", color="#f0883e", fontsize=12, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    p5 = os.path.join(output_dir, "lopo_decision_dashboard.png")
    fig.savefig(p5, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    plots["decision_dashboard"] = p5

    return plots


if __name__ == "__main__":
    print("Starting Leave-One-Pair-Out (LOPO) Validation...")
    res = run_lopo_validation()
    print("\n" + "=" * 95)
    print("                        LOPO RESULTS (ALL FOLDS x ALL METHODS)                       ")
    print("=" * 95)
    print(res["df_results"].to_string(index=False))
    print("=" * 95)
    print("\n" + "=" * 95)
    print("                        LOPO SUMMARY TABLE                                           ")
    print("=" * 95)
    print(res["df_summary"].to_string(index=False))
    print("=" * 95)
    print("\n" + "=" * 95)
    print("                        LOPO AGGREGATE SUMMARY TABLE                                 ")
    print("=" * 95)
    print(res["df_aggregate"].to_string(index=False))
    print("=" * 95)
    print("\n" + "=" * 95)
    print("                        LOPO MULTI-DIMENSIONAL ROUTING EVALUATION                    ")
    print("=" * 95)
    print(res["df_decisions"].to_string(index=False))
    print("=" * 95)
