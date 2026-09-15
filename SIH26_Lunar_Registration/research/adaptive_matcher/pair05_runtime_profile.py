from pathlib import Path
import sys
import time

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    AdaptiveConfig,
    compute_pair_characteristics,
    classify_difficulty_profile,
    rule_based_router,
    run_loftr_matching,
    execute_common_downstream,
    load_loftr_matcher,
)


A_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20200824T0806596861.png"
)

B_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20200824T1003365280.png"
)


A = cv2.imread(
    str(A_PATH),
    cv2.IMREAD_COLOR
)

B = cv2.imread(
    str(B_PATH),
    cv2.IMREAD_COLOR
)

if A is None or B is None:
    raise RuntimeError(
        "Could not load Pair 05 images."
    )


config = AdaptiveConfig()


print("==============================================")
print("PAIR 05 — ADAPTIVE RUNTIME PROFILE")
print("==============================================")

print(
    "Image A:",
    A.shape
)

print(
    "Image B:",
    B.shape
)


# ------------------------------------------------------------
# 1. Characterization
# ------------------------------------------------------------

t0 = time.perf_counter()

chars = compute_pair_characteristics(
    A,
    B
)

t_characterization = (
    time.perf_counter() - t0
)


profile = classify_difficulty_profile(
    chars,
    config
)

decision = rule_based_router(
    profile,
    chars,
    config
)


print()
print("CHARACTERIZATION")
print("----------------")

print(
    f"Time: {t_characterization:.4f} s"
)

print(
    "Profile:",
    profile
)

print(
    "Selected matcher:",
    decision["selected_matcher"]
)


# ------------------------------------------------------------
# 2. LoFTR model loading
# ------------------------------------------------------------

t0 = time.perf_counter()

loftr = load_loftr_matcher()

t_model = (
    time.perf_counter() - t0
)


print()
print("LoFTR MODEL LOAD")
print("----------------")

print(
    f"Time: {t_model:.4f} s"
)


# ------------------------------------------------------------
# 3. Full-image LoFTR
# ------------------------------------------------------------

t0 = time.perf_counter()

loftr_result = run_loftr_matching(
    A,
    B,
    loftr_model=loftr,
    ransac_thresh=config.ransac_threshold
)

t_loftr = (
    time.perf_counter() - t0
)


print()
print("FULL-IMAGE LoFTR")
print("----------------")

print(
    f"Time: {t_loftr:.4f} s"
)

print(
    "Candidates:",
    loftr_result.get("n_candidates")
)

print(
    "Inliers:",
    loftr_result.get("n_inliers")
)

print(
    "Inlier ratio:",
    loftr_result.get("inlier_ratio")
)

print(
    "Spatial occupancy:",
    loftr_result.get("spatial_occupancy")
)


if not loftr_result.get("success", False):
    raise RuntimeError(
        "LoFTR failed:\n"
        + str(
            loftr_result.get(
                "failure_reason"
            )
        )
    )


# ------------------------------------------------------------
# 4. Common downstream
# ------------------------------------------------------------

t0 = time.perf_counter()

downstream = execute_common_downstream(
    loftr_result["inlier_pts0"],
    loftr_result["inlier_pts1"],
    loftr_result["confidences"],
    A,
    B,
    ransac_thresh=config.ransac_threshold
)

t_downstream = (
    time.perf_counter() - t0
)


print()
print("COMMON DOWNSTREAM")
print("-----------------")

print(
    f"Time: {t_downstream:.4f} s"
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
    downstream["final_inlier_ratio"]
)

print(
    "Spatial occupancy:",
    downstream["spatial_occupancy"]
)

print(
    "Spatial CV:",
    downstream["spatial_cv"]
)

print(
    "Check RMSE:",
    downstream["mean_check_rmse"]
)


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

total = (
    t_characterization
    + t_model
    + t_loftr
    + t_downstream
)


print()
print("==============================================")
print("RUNTIME SUMMARY")
print("==============================================")

print(
    f"Characterization: {t_characterization:.3f} s"
)

print(
    f"Model loading:    {t_model:.3f} s"
)

print(
    f"LoFTR:            {t_loftr:.3f} s"
)

print(
    f"Downstream:       {t_downstream:.3f} s"
)

print(
    f"Measured total:   {total:.3f} s"
)

print()
print(
    "This profile uses the CURRENT full-image "
    "Adaptive implementation."
)