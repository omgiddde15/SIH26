from pathlib import Path
import sys
import cv2

ROOT = Path(__file__).resolve().parent

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    run_adaptive_registration,
    AdaptiveConfig,
)


A_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20251108T1727303521.png"
)

B_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20251108T1924377926.png"
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
        "Could not load Pair 02 images."
    )


print("==============================================")
print("PAIR 02 — ADAPTIVE STRESS TEST")
print("==============================================")

print(
    "Source:",
    A.shape
)

print(
    "Reference:",
    B.shape
)


config = AdaptiveConfig()

result = run_adaptive_registration(
    A,
    B,
    config=config,
)


print()
print("==============================================")
print("ADAPTIVE DECISION")
print("==============================================")

print(
    "Primary matcher:",
    result.get("primary_choice")
)

print(
    "Final matcher used:",
    result.get("final_matcher_used")
)

print(
    "Fallback used:",
    result.get("fallback_used")
)

print(
    "Fallback choice:",
    result.get("fallback_choice")
)

print(
    "Fallback reason:",
    result.get("fallback_reason")
)

print(
    "Runtime:",
    result.get("runtime")
)


print()
print("DIFFICULTY PROFILE")
print("------------------")

print(
    result.get("difficulty_profile")
)


print()
print("QUALITY GATE")
print("------------")

print(
    result.get("quality_gate")
)


primary = result.get(
    "primary_result",
    {}
)

print()
print("PRIMARY MATCHER METRICS")
print("-----------------------")

for key in [
    "method",
    "success",
    "n_candidates",
    "n_inliers",
    "inlier_ratio",
    "spatial_occupancy",
    "spatial_cv",
    "runtime",
]:
    print(
        f"{key}:",
        primary.get(key)
    )


fallback = result.get(
    "fallback_result"
)

print()
print("FALLBACK MATCHER METRICS")
print("------------------------")

if fallback is None:
    print("No fallback executed.")

else:
    for key in [
        "method",
        "success",
        "n_candidates",
        "n_inliers",
        "inlier_ratio",
        "spatial_occupancy",
        "spatial_cv",
        "runtime",
    ]:
        print(
            f"{key}:",
            fallback.get(key)
        )

print()
print("ALL MATCHER ATTEMPTS")
print("--------------------")

all_results = result.get(
    "all_matcher_results",
    {}
)

for name in [
    "LoFTR",
    "SIFT",
    "SuperGlue",
]:
    r = all_results.get(name)

    if r is None:
        print(f"{name}: not attempted")
        continue

    print(f"{name}:")
    print("  success:", r.get("success"))
    print("  candidates:", r.get("n_candidates"))
    print("  inliers:", r.get("n_inliers"))
    print("  inlier_ratio:", r.get("inlier_ratio"))
    print("  spatial_occupancy:", r.get("spatial_occupancy"))
    print("  spatial_cv:", r.get("spatial_cv"))
    print("  failure_stage:", r.get("failure_stage"))
    print("  failure_reason:", r.get("failure_reason"))
print()
print("FINAL STATUS")
print("------------")

print(
    "Pipeline success:",
    result.get("success")
)

print(
    "Failure reason:",
    result.get("failure_reason")
)