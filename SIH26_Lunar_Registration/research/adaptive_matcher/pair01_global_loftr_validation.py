from pathlib import Path
import sys
import time

import cv2
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

A_PATH = (
    DATA_ROOT
    / "Images_PNG"
    / "ch2_ohr_ncp_20251109T0909533595.png"
)

B_PATH = (
    DATA_ROOT
    / "Images_PNG"
    / "ch2_ohr_ncp_20251109T1305444583.png"
)

FINAL_PROTOCOL = (
    DATA_ROOT
    / "pair01_FINAL_validation_protocol.csv"
)


# ============================================================
# IMPORT EXISTING ADAPTIVE ENGINE
# ============================================================

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    AdaptiveConfig,
    compute_pair_characteristics,
    classify_difficulty_profile,
    rule_based_router,
    load_loftr_matcher,
    run_loftr_matching,
    execute_common_downstream,
)


# ============================================================
# LOAD IMAGES
# ============================================================

A = cv2.imread(
    str(A_PATH),
    cv2.IMREAD_COLOR
)

B = cv2.imread(
    str(B_PATH),
    cv2.IMREAD_COLOR
)

if A is None:
    raise RuntimeError(
        f"Could not load image A:\n{A_PATH}"
    )

if B is None:
    raise RuntimeError(
        f"Could not load image B:\n{B_PATH}"
    )


print("==============================================")
print("PAIR 01 — GLOBAL LoFTR FAIR VALIDATION")
print("==============================================")

print(
    "Image A:",
    (A.shape[1], A.shape[0])
)

print(
    "Image B:",
    (B.shape[1], B.shape[0])
)


# ============================================================
# CONFIG
# ============================================================

config = AdaptiveConfig()


# ============================================================
# IMAGE CHARACTERIZATION
# ============================================================

t0 = time.perf_counter()

characteristics = compute_pair_characteristics(
    A,
    B
)

characterization_time = (
    time.perf_counter() - t0
)

profile = classify_difficulty_profile(
    characteristics,
    config
)

decision = rule_based_router(
    profile,
    characteristics,
    config
)

print()
print("IMAGE CHARACTERIZATION")
print("----------------------")

print(
    f"Time: {characterization_time:.4f} s"
)

print(
    "Profile:",
    profile
)

print(
    "Router recommendation:",
    decision["selected_matcher"]
)


# ============================================================
# LOAD LoFTR
# ============================================================

t0 = time.perf_counter()

loftr_model = load_loftr_matcher()

model_load_time = (
    time.perf_counter() - t0
)

print()
print("LoFTR MODEL LOAD")
print("----------------")

print(
    f"Time: {model_load_time:.4f} s"
)


# ============================================================
# GLOBAL LoFTR
# ============================================================

t0 = time.perf_counter()

loftr_result = run_loftr_matching(
    A,
    B,
    loftr_model=loftr_model,
    ransac_thresh=config.ransac_threshold,
)

loftr_time = (
    time.perf_counter() - t0
)

if not loftr_result.get("success", False):
    raise RuntimeError(
        "Global LoFTR failed:\n"
        + str(
            loftr_result.get(
                "failure_reason"
            )
        )
    )


print()
print("GLOBAL LoFTR")
print("------------")

print(
    f"Time: {loftr_time:.4f} s"
)

print(
    "Candidates:",
    loftr_result["n_candidates"]
)

print(
    "Initial inliers:",
    loftr_result["n_inliers"]
)

print(
    "Initial inlier ratio:",
    f"{100 * loftr_result['inlier_ratio']:.2f}%"
)

print(
    "Initial spatial occupancy:",
    loftr_result["spatial_occupancy"]
)

print(
    "Initial spatial CV:",
    loftr_result["spatial_cv"]
)


# ============================================================
# COMMON DOWNSTREAM
# ============================================================

t0 = time.perf_counter()

downstream = execute_common_downstream(
    loftr_result["inlier_pts0"],
    loftr_result["inlier_pts1"],
    loftr_result["confidences"],
    A,
    B,
    ransac_thresh=config.ransac_threshold,
)

downstream_time = (
    time.perf_counter() - t0
)


print()
print("COMMON DOWNSTREAM")
print("-----------------")

print(
    f"Time: {downstream_time:.4f} s"
)

print(
    "Selected points:",
    downstream["n_selected"]
)

print(
    "Final inliers:",
    downstream["n_final_inliers"]
)

print(
    "Final inlier ratio:",
    f"{100 * downstream['final_inlier_ratio']:.2f}%"
)

print(
    "Spatial occupancy:",
    downstream["spatial_occupancy"]
)

print(
    "Spatial CV:",
    downstream["spatial_cv"]
)


# ============================================================
# EXTERNAL 14-POINT VALIDATION
# ============================================================

protocol = pd.read_csv(
    FINAL_PROTOCOL
)

checks = protocol.sort_values(
    "point_id"
).copy()

if len(checks) != 14:
    raise RuntimeError(
        f"Expected 14 validation points, got {len(checks)}"
    )

check_A = checks[
    ["A_x", "A_y"]
].to_numpy(
    dtype=np.float32
)

check_B = checks[
    ["B_x", "B_y"]
].to_numpy(
    dtype=np.float32
)


H_final = downstream["H_final"]

pred_B = cv2.perspectiveTransform(
    check_A.reshape(-1, 1, 2),
    H_final
).reshape(-1, 2)

errors = np.linalg.norm(
    pred_B - check_B,
    axis=1
)


rmse = float(
    np.sqrt(
        np.mean(errors ** 2)
    )
)

mean_error = float(
    np.mean(errors)
)

median_error = float(
    np.median(errors)
)

max_error = float(
    np.max(errors)
)

below_1 = float(
    np.mean(errors < 1.0) * 100.0
)


# ============================================================
# RUNTIME
# ============================================================

total_time = (
    characterization_time
    + model_load_time
    + loftr_time
    + downstream_time
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("==============================================")
print("GLOBAL LoFTR — FINAL 14-POINT VALIDATION")
print("==============================================")

print(
    "Validation points:",
    len(checks)
)

print()
print("Check RMSE:", f"{rmse:.6f} px")
print("Check mean:", f"{mean_error:.6f} px")
print("Check median:", f"{median_error:.6f} px")
print("Check max:", f"{max_error:.6f} px")
print("Checks < 1 px:", f"{below_1:.2f}%")


print()
print("==============================================")
print("RUNTIME SUMMARY")
print("==============================================")

print(
    f"Characterization: {characterization_time:.4f} s"
)

print(
    f"Model loading:    {model_load_time:.4f} s"
)

print(
    f"Global LoFTR:     {loftr_time:.4f} s"
)

print(
    f"Downstream:       {downstream_time:.4f} s"
)

print(
    f"Total measured:   {total_time:.4f} s"
)


print()
print("==============================================")
print("8-TILE COMPARISON BASELINE")
print("==============================================")

print(
    "Previous PAIR 01 8-tile Adaptive:"
)

print(
    "RMSE:      4.438954 px"
)

print(
    "Runtime:   104.546 s"
)

print()
print("Now compare the Global LoFTR values above.")
