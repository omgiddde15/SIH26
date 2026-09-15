from pathlib import Path
import sys

import cv2
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import run_loftr_matching


# ============================================================
# Files
# ============================================================

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

GEO_FILE = (
    DATA_ROOT / "pair02_actual_geo_matches.csv"
)

A_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20251108T1727303521.png"
)

B_PATH = (
    DATA_ROOT / "Images_PNG" /
    "ch2_ohr_ncp_20251108T1924377926.png"
)

GEO_THRESHOLD = 0.00020


# ============================================================
# Resolve paths
# ============================================================

GEO_FILE = GEO_FILE.resolve()
A_PATH = A_PATH.resolve()
B_PATH = B_PATH.resolve()

if not GEO_FILE.exists():
    raise RuntimeError(
        f"Missing geo file:\n{GEO_FILE}"
    )

if not A_PATH.exists():
    raise RuntimeError(
        f"Missing image A:\n{A_PATH}"
    )

if not B_PATH.exists():
    raise RuntimeError(
        f"Missing image B:\n{B_PATH}"
    )


# ============================================================
# Load images
# ============================================================

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
print("PAIR 02 — GEO/VISUAL CONSISTENCY PROBE")
print("==============================================")


# ============================================================
# Load strict geographic correspondences
# ============================================================

geo = pd.read_csv(GEO_FILE)

geo = geo[
    geo["geo_distance_deg"] <= GEO_THRESHOLD
].copy()

print()
print(
    f"Strict geo threshold: {GEO_THRESHOLD:.5f}°"
)

print(
    "Geo correspondences:",
    len(geo)
)

if len(geo) < 8:
    raise RuntimeError(
        "Too few geographic correspondences."
    )


geo_src = geo[
    ["A_x", "A_y"]
].to_numpy(dtype=np.float32)

geo_dst = geo[
    ["B_x", "B_y"]
].to_numpy(dtype=np.float32)


# ============================================================
# Robust geospatial homography
# ============================================================

H_geo, geo_mask = cv2.findHomography(
    geo_src,
    geo_dst,
    cv2.RANSAC,
    3.0,
    maxIters=10000,
    confidence=0.995,
)

if H_geo is None or geo_mask is None:
    raise RuntimeError(
        "Could not estimate geospatial homography."
    )

geo_mask = geo_mask.ravel().astype(bool)

print()
print("GEOSPATIAL MODEL")
print("----------------")

print(
    "RANSAC inliers:",
    int(geo_mask.sum()),
    "/",
    len(geo_src)
)

print(
    "Inlier ratio:",
    f"{100 * geo_mask.mean():.2f}%"
)

print()
print(H_geo)


# ============================================================
# Run current LoFTR matcher
# ============================================================

print()
print("RUNNING CURRENT ADAPTIVE LoFTR")
print("--------------------------------")

visual = run_loftr_matching(
    A,
    B,
    ransac_thresh=3.0
)

if not visual.get("success", False):
    raise RuntimeError(
        "LoFTR failed:\n"
        + str(visual.get("failure_reason"))
    )


H_visual = visual["H"]


print()
print("VISUAL MODEL")
print("------------")

print(
    "Candidates:",
    visual["n_candidates"]
)

print(
    "Inliers:",
    visual["n_inliers"]
)

print(
    "Inlier ratio:",
    f"{visual['inlier_ratio']:.4f}"
)

print(
    "Spatial occupancy:",
    f"{visual['spatial_occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{visual['spatial_cv']:.4f}"
)

print()
print(H_visual)


# ============================================================
# Compare the two models on geographic support
# ============================================================

# Use a reproducible sample of geographic points.
if len(geo_src) > 1000:
    rng = np.random.default_rng(42)
    idx = rng.choice(
        len(geo_src),
        size=1000,
        replace=False
    )
    test_src = geo_src[idx]
else:
    test_src = geo_src


pred_geo = cv2.perspectiveTransform(
    test_src.reshape(-1, 1, 2),
    H_geo
).reshape(-1, 2)

pred_visual = cv2.perspectiveTransform(
    test_src.reshape(-1, 1, 2),
    H_visual
).reshape(-1, 2)


model_difference = np.linalg.norm(
    pred_visual - pred_geo,
    axis=1
)


# ============================================================
# Compare H_visual directly against actual geo destinations
# ============================================================

actual_geo_dst = cv2.perspectiveTransform(
    test_src.reshape(-1, 1, 2),
    H_geo
).reshape(-1, 2)

visual_geo_error = np.linalg.norm(
    pred_visual - actual_geo_dst,
    axis=1
)


print()
print("==============================================")
print("VISUAL vs GEOSPATIAL CONSISTENCY")
print("==============================================")


print(
    f"Median model difference: "
    f"{np.median(model_difference):.3f} px"
)

print(
    f"Mean model difference:   "
    f"{np.mean(model_difference):.3f} px"
)

print(
    f"P90 model difference:    "
    f"{np.percentile(model_difference, 90):.3f} px"
)

print(
    f"Max model difference:    "
    f"{np.max(model_difference):.3f} px"
)


print()
print("VISUAL HOMOGRAPHY ERROR AGAINST GEO MODEL")
print("------------------------------------------")

print(
    f"Median: "
    f"{np.median(visual_geo_error):.3f} px"
)

print(
    f"P90:    "
    f"{np.percentile(visual_geo_error, 90):.3f} px"
)

print(
    f"Max:    "
    f"{np.max(visual_geo_error):.3f} px"
)


print()
print("INTERPRETATION")
print("--------------")

median_diff = np.median(model_difference)

if median_diff < 10:
    print(
        "Visual and geospatial models are broadly consistent."
    )
elif median_diff < 50:
    print(
        "Moderate visual/geospatial disagreement."
    )
else:
    print(
        "STRONG visual/geospatial disagreement."
    )

print()
print("No Adaptive code was modified.")