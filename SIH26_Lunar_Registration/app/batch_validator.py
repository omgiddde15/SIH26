import os
import sys
import glob
import time
import logging
import cv2
import numpy as np
import pandas as pd

# Suppress noisy streamlit context warnings when running in standalone mode
logging.getLogger("streamlit").setLevel(logging.ERROR)

COLUMNS = [
    "Pair ID",
    "Source resolution",
    "Reference resolution",
    "LoFTR matching resolution",
    "Candidate matches",
    "Initial RANSAC inliers",
    "Selected correspondences",
    "Final inliers",
    "Final inlier ratio",
    "Fit RMSE",
    "Check RMSE for seed 1",
    "Check RMSE for seed 2",
    "Check RMSE for seed 3",
    "Check RMSE for seed 4",
    "Check RMSE for seed 5",
    "Mean Check RMSE",
    "Median Check RMSE",
    "Best Check RMSE",
    "Worst Check RMSE",
    "Spatial occupancy",
    "Spatial CV",
    "Runtime",
    "Success / Failure",
    "Failure Reason",
]


def find_validation_pairs(pairs_dir):
    """
    Scans pairs_dir for subdirectories containing source.* and reference.* image files.
    Returns a list of tuples: (pair_id, source_path, reference_path)
    """
    if not os.path.exists(pairs_dir):
        return []

    pairs = []
    subdirs = sorted([d for d in os.listdir(pairs_dir) if os.path.isdir(os.path.join(pairs_dir, d))])

    for sub in subdirs:
        sub_path = os.path.join(pairs_dir, sub)
        src_matches = glob.glob(os.path.join(sub_path, "source.*"))
        ref_matches = glob.glob(os.path.join(sub_path, "reference.*"))

        if src_matches and ref_matches:
            pairs.append((sub, src_matches[0], ref_matches[0]))

    return pairs


def compute_aggregate_summary(df):
    """
    Calculates the 10 standard aggregate summary metrics across validation pairs:
    1. Total pairs
    2. Successful pairs
    3. Failed pairs
    4. Mean Check RMSE across pairs
    5. Median Check RMSE across pairs
    6. Worst pair
    7. Best pair
    8. Percentage of pairs with check RMSE < 1 px
    9. Mean final inlier ratio
    10. Mean spatial occupancy
    """
    total_pairs = int(len(df))
    if total_pairs == 0:
        return {
            "total_pairs": 0,
            "successful_pairs": 0,
            "failed_pairs": 0,
            "mean_check_rmse": None,
            "median_check_rmse": None,
            "worst_pair": "N/A",
            "best_pair": "N/A",
            "pct_subpixel": None,
            "mean_inlier_ratio": None,
            "mean_spatial_occupancy": None,
        }

    df_succ = df[df["Success / Failure"] == "Success"].copy()
    successful_pairs = int(len(df_succ))
    failed_pairs = total_pairs - successful_pairs

    if successful_pairs > 0:
        # Convert numeric columns safely
        check_rmses = pd.to_numeric(df_succ["Mean Check RMSE"], errors="coerce").dropna()
        inlier_ratios = pd.to_numeric(df_succ["Final inlier ratio"], errors="coerce").dropna()
        occupancies = pd.to_numeric(df_succ["Spatial occupancy"], errors="coerce").dropna()

        mean_check_rmse = float(check_rmses.mean()) if not check_rmses.empty else None
        median_check_rmse = float(check_rmses.median()) if not check_rmses.empty else None

        if not check_rmses.empty:
            best_idx = check_rmses.idxmin()
            worst_idx = check_rmses.idxmax()
            best_pair = f"{df_succ.loc[best_idx, 'Pair ID']} ({check_rmses[best_idx]:.4f} px)"
            worst_pair = f"{df_succ.loc[worst_idx, 'Pair ID']} ({check_rmses[worst_idx]:.4f} px)"
            pct_subpixel = float((check_rmses < 1.0).mean() * 100.0)
        else:
            best_pair = "N/A"
            worst_pair = "N/A"
            pct_subpixel = None

        mean_inlier_ratio = float(inlier_ratios.mean()) if not inlier_ratios.empty else None
        mean_spatial_occupancy = float(occupancies.mean()) if not occupancies.empty else None
    else:
        mean_check_rmse = None
        median_check_rmse = None
        best_pair = "N/A"
        worst_pair = "N/A"
        pct_subpixel = None
        mean_inlier_ratio = None
        mean_spatial_occupancy = None

    return {
        "total_pairs": total_pairs,
        "successful_pairs": successful_pairs,
        "failed_pairs": failed_pairs,
        "mean_check_rmse": mean_check_rmse,
        "median_check_rmse": median_check_rmse,
        "worst_pair": worst_pair,
        "best_pair": best_pair,
        "pct_subpixel": pct_subpixel,
        "mean_inlier_ratio": mean_inlier_ratio,
        "mean_spatial_occupancy": mean_spatial_occupancy,
    }


def run_batch_validation(
    pairs_dir=os.path.join("data", "validation_pairs"),
    output_csv="batch_validation_results.csv",
    register_fn=None,
    progress_callback=None,
):
    """
    Runs existing registration + held-out check-point validation on multiple real lunar pairs.
    Produces batch_validation_results.csv and aggregate summary metrics.
    """
    if register_fn is None:
        try:
            from app.registration_core import register_images
        except ImportError:
            from registration_core import register_images
        register_fn = register_images

    pairs = find_validation_pairs(pairs_dir)
    if not pairs:
        print(f"[BatchValidator] No validation pairs found in {pairs_dir}")
        empty_df = pd.DataFrame(columns=COLUMNS)
        return empty_df, compute_aggregate_summary(empty_df)

    rows = []
    total = len(pairs)
    print(f"[BatchValidator] Found {total} validation pair(s) in '{pairs_dir}'. Starting batch execution...")

    for idx, (pair_id, src_path, ref_path) in enumerate(pairs):
        if progress_callback:
            progress_callback(idx, total, pair_id, "Processing...")

        print(f"\n[BatchValidator] [{idx+1}/{total}] Processing Pair: {pair_id}...")
        start_pair_time = time.perf_counter()

        src_img = cv2.imread(src_path)
        ref_img = cv2.imread(ref_path)

        if src_img is None or ref_img is None:
            reason = f"Image decode failure: source={src_img is not None}, ref={ref_img is not None}"
            print(f"  -> FAILED: {reason}")
            rows.append({
                "Pair ID": pair_id,
                "Source resolution": "Unknown" if src_img is None else f"{src_img.shape[1]}x{src_img.shape[0]}",
                "Reference resolution": "Unknown" if ref_img is None else f"{ref_img.shape[1]}x{ref_img.shape[0]}",
                "LoFTR matching resolution": None,
                "Candidate matches": None,
                "Initial RANSAC inliers": None,
                "Selected correspondences": None,
                "Final inliers": None,
                "Final inlier ratio": None,
                "Fit RMSE": None,
                "Check RMSE for seed 1": None,
                "Check RMSE for seed 2": None,
                "Check RMSE for seed 3": None,
                "Check RMSE for seed 4": None,
                "Check RMSE for seed 5": None,
                "Mean Check RMSE": None,
                "Median Check RMSE": None,
                "Best Check RMSE": None,
                "Worst Check RMSE": None,
                "Spatial occupancy": None,
                "Spatial CV": None,
                "Runtime": round(time.perf_counter() - start_pair_time, 2),
                "Success / Failure": "Failure",
                "Failure Reason": reason,
            })
            continue

        s_h, s_w = src_img.shape[:2]
        r_h, r_w = ref_img.shape[:2]
        src_res_str = f"{s_w}x{s_h}"
        ref_res_str = f"{r_w}x{r_h}"

        try:
            # Run the locked existing registration pipeline with deterministic seeds 1-5
            res = register_fn(src_img, ref_img)

            # Match resolution
            m_s_h, m_s_w = res["match_source_shape"]
            m_r_h, m_r_w = res["match_ref_shape"]
            match_res_str = f"{m_s_w}x{m_s_h} / {m_r_w}x{m_r_h}"

            val = res.get("independent_validation")
            runs = val["runs"] if val and "runs" in val else []

            seed_rmses = {}
            for r in runs:
                seed_rmses[r["seed"]] = round(float(r["check_rmse"]), 4)

            fit_rmse = round(float(val["primary_run"]["fit_rmse"]), 4) if val and "primary_run" in val else round(float(res.get("rmse", 0.0)), 4)
            mean_check_rmse = round(float(val["mean_check_rmse"]), 4) if val else None
            median_check_rmse = round(float(val["median_check_rmse"]), 4) if val else None
            best_check_rmse = round(float(val["best_check_rmse"]), 4) if val else None
            worst_check_rmse = round(float(val["worst_check_rmse"]), 4) if val else None

            row = {
                "Pair ID": pair_id,
                "Source resolution": src_res_str,
                "Reference resolution": ref_res_str,
                "LoFTR matching resolution": match_res_str,
                "Candidate matches": int(res["candidate_matches"]),
                "Initial RANSAC inliers": int(res["initial_inliers"]),
                "Selected correspondences": int(res["selected_matches"]),
                "Final inliers": int(res["final_inliers"]),
                "Final inlier ratio": round(float(res["final_inlier_ratio"]), 4),
                "Fit RMSE": fit_rmse,
                "Check RMSE for seed 1": seed_rmses.get(1, None),
                "Check RMSE for seed 2": seed_rmses.get(2, None),
                "Check RMSE for seed 3": seed_rmses.get(3, None),
                "Check RMSE for seed 4": seed_rmses.get(4, None),
                "Check RMSE for seed 5": seed_rmses.get(5, None),
                "Mean Check RMSE": mean_check_rmse,
                "Median Check RMSE": median_check_rmse,
                "Best Check RMSE": best_check_rmse,
                "Worst Check RMSE": worst_check_rmse,
                "Spatial occupancy": round(float(res["occupancy_ratio"]), 4),
                "Spatial CV": round(float(res["spatial_cv"]), 4),
                "Runtime": round(float(res["runtime"]), 2),
                "Success / Failure": "Success",
                "Failure Reason": "None",
            }
            print(f"  -> SUCCESS: Final Inliers={res['final_inliers']}, Check RMSE Mean={mean_check_rmse} px, Runtime={res['runtime']:.2f}s")
            rows.append(row)

        except Exception as e:
            reason = str(e)
            print(f"  -> FAILED: {reason}")
            # Do NOT fabricate values on failure
            rows.append({
                "Pair ID": pair_id,
                "Source resolution": src_res_str,
                "Reference resolution": ref_res_str,
                "LoFTR matching resolution": None,
                "Candidate matches": None,
                "Initial RANSAC inliers": None,
                "Selected correspondences": None,
                "Final inliers": None,
                "Final inlier ratio": None,
                "Fit RMSE": None,
                "Check RMSE for seed 1": None,
                "Check RMSE for seed 2": None,
                "Check RMSE for seed 3": None,
                "Check RMSE for seed 4": None,
                "Check RMSE for seed 5": None,
                "Mean Check RMSE": None,
                "Median Check RMSE": None,
                "Best Check RMSE": None,
                "Worst Check RMSE": None,
                "Spatial occupancy": None,
                "Spatial CV": None,
                "Runtime": round(time.perf_counter() - start_pair_time, 2),
                "Success / Failure": "Failure",
                "Failure Reason": reason,
            })

    if progress_callback:
        progress_callback(total, total, "Done", "Validation complete.")

    df_results = pd.DataFrame(rows, columns=COLUMNS)

    # Save to primary output_csv
    df_results.to_csv(output_csv, index=False)
    print(f"\n[BatchValidator] Saved results to '{output_csv}'")

    # Also save to results/ directory if available
    os.makedirs("results", exist_ok=True)
    results_path = os.path.join("results", os.path.basename(output_csv))
    df_results.to_csv(results_path, index=False)
    print(f"[BatchValidator] Mirrored results to '{results_path}'")

    summary = compute_aggregate_summary(df_results)
    return df_results, summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lunar Image Registration Batch Real-Data Validation Engine")
    parser.add_argument("--pairs-dir", default=os.path.join("data", "validation_pairs"), help="Path to validation pairs directory")
    parser.add_argument("--output-csv", default="batch_validation_results.csv", help="Path to output CSV")
    args = parser.parse_args()

    # Add project directory to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    app_dir = os.path.abspath(os.path.dirname(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    df_res, agg = run_batch_validation(pairs_dir=args.pairs_dir, output_csv=args.output_csv)

    print("\n" + "=" * 60)
    print("           MULTI-PAIR VALIDATION AGGREGATE SUMMARY           ")
    print("=" * 60)
    print(f"Total pairs                             : {agg['total_pairs']}")
    print(f"Successful pairs                        : {agg['successful_pairs']}")
    print(f"Failed pairs                            : {agg['failed_pairs']}")
    if agg['successful_pairs'] > 0:
        print(f"Mean Check RMSE across pairs            : {agg['mean_check_rmse']:.4f} px")
        print(f"Median Check RMSE across pairs          : {agg['median_check_rmse']:.4f} px")
        print(f"Best pair                               : {agg['best_pair']}")
        print(f"Worst pair                              : {agg['worst_pair']}")
        print(f"Percentage of pairs with check RMSE < 1 px: {agg['pct_subpixel']:.1f}%")
        print(f"Mean final inlier ratio                 : {agg['mean_inlier_ratio']*100:.2f}%")
        print(f"Mean spatial occupancy                  : {agg['mean_spatial_occupancy']*100:.2f}%")
    print("=" * 60)
