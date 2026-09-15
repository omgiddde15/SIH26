from pathlib import Path
import sys
import time
import subprocess
import re

import cv2
import numpy as np
import pandas as pd


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

GEO_FILE = (
    DATA_ROOT
    / "pair01_actual_geo_matches.csv"
)

FINAL_PROTOCOL = (
    DATA_ROOT
    / "pair01_FINAL_validation_protocol.csv"
)

# Existing validated geoguided tiled implementation.
TILED_SCRIPT = (
    DATA_ROOT
    / "loftr_geoguided_8tile_v3.py"
)

GEO_THRESHOLD = 0.00020

# ------------------------------------------------------------
# Experimental quickness thresholds
# ------------------------------------------------------------

MIN_INLIER_RATIO = 0.30
MIN_SPATIAL_OCCUPANCY = 0.7778
MAX_SPATIAL_CV = 0.80
MAX_GEO_DISAGREEMENT = 100.0


# ------------------------------------------------------------
# Import existing Adaptive LoFTR implementation
# ------------------------------------------------------------

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    load_loftr_matcher,
    run_loftr_matching,
    execute_common_downstream,
)


# ============================================================
# Helpers
# ============================================================

def load_gray(path):
    img = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise RuntimeError(
            f"Could not load image:\n{path}"
        )

    return img


def apply_homography(points, H):
    return cv2.perspectiveTransform(
        points.reshape(-1, 1, 2),
        H
    ).reshape(-1, 2)


def build_geo_model():
    geo = pd.read_csv(
        GEO_FILE
    )

    geo = geo[
        geo["geo_distance_deg"]
        <= GEO_THRESHOLD
    ].copy()

    if len(geo) < 8:
        raise RuntimeError(
            "Too few strict geographic correspondences."
        )

    src = geo[
        ["A_x", "A_y"]
    ].to_numpy(
        dtype=np.float32
    )

    dst = geo[
        ["B_x", "B_y"]
    ].to_numpy(
        dtype=np.float32
    )

    H_geo, mask = cv2.findHomography(
        src,
        dst,
        cv2.RANSAC,
        3.0,
        maxIters=10000,
        confidence=0.995,
    )

    if H_geo is None or mask is None:
        raise RuntimeError(
            "Could not estimate geographic homography."
        )

    mask = mask.ravel().astype(bool)

    return (
        geo,
        src,
        H_geo,
        mask,
    )


def calculate_geo_disagreement(
    src_points,
    H_geo,
    H_visual,
):
    if len(src_points) > 2000:
        rng = np.random.default_rng(42)

        idx = rng.choice(
            len(src_points),
            size=2000,
            replace=False
        )

        test_src = src_points[idx]

    else:
        test_src = src_points

    geo_pred = apply_homography(
        test_src,
        H_geo
    )

    visual_pred = apply_homography(
        test_src,
        H_visual
    )

    disagreement = np.linalg.norm(
        visual_pred - geo_pred,
        axis=1
    )

    return {
        "median": float(
            np.median(disagreement)
        ),
        "p90": float(
            np.percentile(
                disagreement,
                90
            )
        ),
        "max": float(
            np.max(disagreement)
        ),
    }


def parse_tiled_rmse(stdout):
    match = re.search(
        r"Check RMSE:\s*([0-9.]+)\s*px",
        stdout
    )

    if match:
        return float(
            match.group(1)
        )

    return None


def load_validation_protocol():
    df = pd.read_csv(
        FINAL_PROTOCOL
    ).sort_values(
        "point_id"
    )

    if len(df) != 14:
        raise RuntimeError(
            f"Expected 14 checks, got {len(df)}"
        )

    return (
        df[
            ["A_x", "A_y"]
        ].to_numpy(
            dtype=np.float32
        ),
        df[
            ["B_x", "B_y"]
        ].to_numpy(
            dtype=np.float32
        ),
    )


# ============================================================
# Main
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V1 PROGRESSIVE PROTOTYPE")
print("==============================================")


A = load_gray(A_PATH)
B = load_gray(B_PATH)

print(
    "Image A:",
    (A.shape[1], A.shape[0])
)

print(
    "Image B:",
    (B.shape[1], B.shape[0])
)


# ============================================================
# Stage 1 — Global LoFTR
# ============================================================

print()
print("==============================================")
print("STAGE 1 — GLOBAL LoFTR")
print("==============================================")


t_total = time.perf_counter()

t0 = time.perf_counter()

loftr_model = load_loftr_matcher()

model_load_time = (
    time.perf_counter() - t0
)


t0 = time.perf_counter()

global_result = run_loftr_matching(
    A,
    B,
    loftr_model=loftr_model,
    ransac_thresh=3.0,
)

global_runtime = (
    time.perf_counter() - t0
)


if not global_result.get("success", False):
    raise RuntimeError(
        "Global LoFTR failed:\n"
        + str(
            global_result.get(
                "failure_reason"
            )
        )
    )


print(
    "Runtime:",
    f"{global_runtime:.3f} s"
)

print(
    "Candidates:",
    global_result["n_candidates"]
)

print(
    "Initial inliers:",
    global_result["n_inliers"]
)

print(
    "Inlier ratio:",
    f"{100 * global_result['inlier_ratio']:.2f}%"
)

print(
    "Spatial occupancy:",
    f"{global_result['spatial_occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{global_result['spatial_cv']:.4f}"
)


# ============================================================
# Stage 2 — Geo consistency
# ============================================================

(
    geo,
    geo_src,
    H_geo,
    geo_mask,
) = build_geo_model()

geo_consistency = calculate_geo_disagreement(
    geo_src,
    H_geo,
    global_result["H"],
)


print()
print("GEO/VISUAL CONSISTENCY")
print("----------------------")

print(
    "Median disagreement:",
    f"{geo_consistency['median']:.3f} px"
)

print(
    "P90 disagreement:",
    f"{geo_consistency['p90']:.3f} px"
)

print(
    "Maximum disagreement:",
    f"{geo_consistency['max']:.3f} px"
)


# ============================================================
# Stage 3 — Quickness Gate
# ============================================================

fast_path = (
    global_result["inlier_ratio"]
    >= MIN_INLIER_RATIO

    and global_result["spatial_occupancy"]
    >= MIN_SPATIAL_OCCUPANCY

    and global_result["spatial_cv"]
    <= MAX_SPATIAL_CV

    and geo_consistency["median"]
    <= MAX_GEO_DISAGREEMENT
)


print()
print("==============================================")
print("STAGE 2 — QUICKNESS GATE")
print("==============================================")


print(
    f"Inlier ratio      >= {MIN_INLIER_RATIO:.4f}:",
    global_result["inlier_ratio"]
    >= MIN_INLIER_RATIO
)

print(
    f"Spatial occupancy >= {MIN_SPATIAL_OCCUPANCY:.4f}:",
    global_result["spatial_occupancy"]
    >= MIN_SPATIAL_OCCUPANCY
)

print(
    f"Spatial CV        <= {MAX_SPATIAL_CV:.4f}:",
    global_result["spatial_cv"]
    <= MAX_SPATIAL_CV
)

print(
    f"Geo disagreement  <= {MAX_GEO_DISAGREEMENT:.1f}px:",
    geo_consistency["median"]
    <= MAX_GEO_DISAGREEMENT
)


if fast_path:

    print()
    print(
        "DECISION: FAST PATH"
    )

else:

    print()
    print(
        "DECISION: TILED REFINEMENT"
    )


# ============================================================
# FAST PATH
# ============================================================

if fast_path:

    check_A, check_B = (
        load_validation_protocol()
    )

    downstream = execute_common_downstream(
        global_result["inlier_pts0"],
        global_result["inlier_pts1"],
        global_result["confidences"],
        A,
        B,
        ransac_thresh=3.0,
    )

    H_final = downstream["H_final"]

    pred_B = cv2.perspectiveTransform(
        check_A.reshape(-1, 1, 2),
        H_final,
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

    total_runtime = (
        time.perf_counter()
        - t_total
    )

    print()
    print("==============================================")
    print("FAST PATH RESULT")
    print("==============================================")

    print(
        "Check RMSE:",
        f"{rmse:.6f} px"
    )

    print(
        "Check mean:",
        f"{mean_error:.6f} px"
    )

    print(
        "Check median:",
        f"{median_error:.6f} px"
    )

    print(
        "Check max:",
        f"{max_error:.6f} px"
    )

    print(
        "Total runtime:",
        f"{total_runtime:.3f} s"
    )


# ============================================================
# TILED REFINEMENT
# ============================================================

else:

    print()
    print("==============================================")
    print("STAGE 3 — GEOGUIDED TILED REFINEMENT")
    print("==============================================")

    if not TILED_SCRIPT.exists():
        raise RuntimeError(
            f"Missing tiled LoFTR script:\n"
            f"{TILED_SCRIPT}"
        )

    t_refine = time.perf_counter()

    process = subprocess.run(
        [
            "py",
            "-3.13",
            str(TILED_SCRIPT),
        ],
        cwd=str(DATA_ROOT),
        capture_output=True,
        text=True,
    )

    refinement_runtime = (
        time.perf_counter()
        - t_refine
    )

    print(
        process.stdout
    )

    if process.returncode != 0:
        print(
            process.stderr
        )

        raise RuntimeError(
            "Geoguided tiled refinement failed."
        )

    tiled_rmse = parse_tiled_rmse(
        process.stdout
    )

    total_runtime = (
        time.perf_counter()
        - t_total
    )

    print()
    print("==============================================")
    print("PROGRESSIVE PROTOTYPE RESULT")
    print("==============================================")

    print(
        "Global LoFTR runtime:",
        f"{global_runtime:.3f} s"
    )

    print(
        "Tiled refinement runtime:",
        f"{refinement_runtime:.3f} s"
    )

    print(
        "Total prototype runtime:",
        f"{total_runtime:.3f} s"
    )

    if tiled_rmse is not None:
        print(
            "Tiled final RMSE:",
            f"{tiled_rmse:.6f} px"
        )

    print()
    print(
        "Final decision: TILED REFINEMENT"
    )