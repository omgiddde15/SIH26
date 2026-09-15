from pathlib import Path
import sys
import json
import gc
import time

import cv2
import numpy as np
import pandas as pd
import torch


# ============================================================
# Existing Adaptive engine
# ============================================================

ENGINE_DIR = Path(
    r"C:\Users\Dell\Videos\SIH26"
) / "SIH26_Lunar_Registration" / "research" / "adaptive_matcher"

sys.path.insert(0, str(ENGINE_DIR))

import adaptive_engine as ae


# ============================================================
# Kaggle Pair 01
# ============================================================

KAGGLE_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

A_PATH = KAGGLE_ROOT / "Images_PNG" / (
    "ch2_ohr_ncp_20251109T0909533595.png"
)

B_PATH = KAGGLE_ROOT / "Images_PNG" / (
    "ch2_ohr_ncp_20251109T1305444583.png"
)

GEO_FILE = KAGGLE_ROOT / "pair01_actual_geo_matches.csv"

FINAL_PROTOCOL = (
    KAGGLE_ROOT / "pair01_FINAL_validation_protocol_v3.csv"
)

CALIBRATION_FILE = (
    KAGGLE_ROOT / "pair01_affine_raster_calibration_v3.json"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

TILE_W = 600
TILE_H = 600

X_CENTERS = [300, 900]
Y_FRACTIONS = [0.10, 0.37, 0.63, 0.90]

CONF_THRESHOLD = 0.50


# ============================================================
# Utilities
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


def apply_clahe(img):
    return cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    ).apply(img)


def clamp_tile(cx, cy, width, height):
    x0 = int(round(cx - TILE_W / 2))
    y0 = int(round(cy - TILE_H / 2))

    x0 = max(0, min(x0, width - TILE_W))
    y0 = max(0, min(y0, height - TILE_H))

    return (
        x0,
        y0,
        x0 + TILE_W,
        y0 + TILE_H
    )


def load_affine():
    with open(
        CALIBRATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    H = np.asarray(
        data["affine_matrix"],
        dtype=np.float32
    )

    if H.shape != (2, 3):
        raise RuntimeError(
            f"Bad affine matrix shape: {H.shape}"
        )

    return H


def transform_points(points, affine):
    return cv2.transform(
        points.reshape(-1, 1, 2),
        affine
    ).reshape(-1, 2)


# ============================================================
# Geospatial tile layout
# Same layout used in our LoFTR/SuperGlue benchmarks.
# ============================================================

A_GEO = pd.read_csv(GEO_FILE)

AFFINE = load_affine()


def get_tiles(A_shape, B_shape):
    ha, wa = A_shape
    hb, wb = B_shape

    geo = A_GEO.copy()

    geo = geo[
        (geo["A_x"] >= 0.05 * wa)
        & (geo["A_x"] <= wa - 1 - 0.05 * wa)
        & (geo["A_y"] >= 0.05 * ha)
        & (geo["A_y"] <= ha - 1 - 0.05 * ha)
        & (geo["B_x"] >= 0.05 * wb)
        & (geo["B_x"] <= wb - 1 - 0.05 * wb)
        & (geo["B_y"] >= 0.05 * hb)
        & (geo["B_y"] <= hb - 1 - 0.05 * hb)
    ].copy()

    common_y_min = float(
        geo["A_y"].min()
    )

    common_y_max = float(
        geo["A_y"].max()
    )

    tiles = []

    tile_id = 0

    for x_center in X_CENTERS:

        for fraction in Y_FRACTIONS:

            tile_id += 1

            center_a_y = (
                common_y_min
                + fraction *
                (
                    common_y_max
                    - common_y_min
                )
            )

            ax0, ay0, ax1, ay1 = clamp_tile(
                x_center,
                center_a_y,
                wa,
                ha
            )

            local = geo[
                (geo["A_x"] >= ax0)
                & (geo["A_x"] < ax1)
                & (geo["A_y"] >= ay0)
                & (geo["A_y"] < ay1)
            ]

            if len(local) < 50:
                continue

            geo_center = np.array([
                [
                    float(local["B_x"].median()),
                    float(local["B_y"].median())
                ]
            ], dtype=np.float32)

            visual_center = transform_points(
                geo_center,
                AFFINE
            )[0]

            bx0, by0, bx1, by1 = clamp_tile(
                visual_center[0],
                visual_center[1],
                wb,
                hb
            )

            if (
                ax1 - ax0 == TILE_W
                and ay1 - ay0 == TILE_H
                and bx1 - bx0 == TILE_W
                and by1 - by0 == TILE_H
            ):
                tiles.append({
                    "tile": tile_id,
                    "A_x0": ax0,
                    "A_y0": ay0,
                    "A_x1": ax1,
                    "A_y1": ay1,
                    "B_x0": bx0,
                    "B_y0": by0,
                    "B_x1": bx1,
                    "B_y1": by1,
                    "geo_samples": len(local),
                })

    return tiles


# ============================================================
# Memory-safe LoFTR replacement
#
# This replaces ONLY the execution function used by the
# existing Adaptive router. Routing logic remains untouched.
# ============================================================

def tiled_loftr(
    source_img,
    reference_img,
    loftr_model=None,
    ransac_thresh=3.0
):

    t0 = time.perf_counter()

    if loftr_model is None:
        loftr_model = ae.load_loftr_matcher()

    src = apply_clahe(source_img)
    ref = apply_clahe(reference_img)

    tiles = get_tiles(
        src.shape,
        ref.shape
    )

    all_pts0 = []
    all_pts1 = []
    all_conf = []

    tile_rows = []

    for tile in tiles:

        ax0 = tile["A_x0"]
        ay0 = tile["A_y0"]
        ax1 = tile["A_x1"]
        ay1 = tile["A_y1"]

        bx0 = tile["B_x0"]
        by0 = tile["B_y0"]
        bx1 = tile["B_x1"]
        by1 = tile["B_y1"]

        tile_a = src[
            ay0:ay1,
            ax0:ax1
        ]

        tile_b = ref[
            by0:by1,
            bx0:bx1
        ]

        t_a = (
            torch.from_numpy(tile_a)
            .float()
            .div(255.0)
            .unsqueeze(0)
            .unsqueeze(0)
            .to(ae._DEVICE)
        )

        t_b = (
            torch.from_numpy(tile_b)
            .float()
            .div(255.0)
            .unsqueeze(0)
            .unsqueeze(0)
            .to(ae._DEVICE)
        )

        with torch.inference_mode():

            out = loftr_model({
                "image0": t_a,
                "image1": t_b,
            })

        k0 = (
            out["keypoints0"]
            .detach()
            .cpu()
            .numpy()
        )

        k1 = (
            out["keypoints1"]
            .detach()
            .cpu()
            .numpy()
        )

        conf = (
            out["confidence"]
            .detach()
            .cpu()
            .numpy()
        )

        keep = conf >= CONF_THRESHOLD

        k0 = k0[keep]
        k1 = k1[keep]
        conf = conf[keep]

        k0[:, 0] += ax0
        k0[:, 1] += ay0

        k1[:, 0] += bx0
        k1[:, 1] += by0

        if len(k0):

            all_pts0.append(k0)
            all_pts1.append(k1)
            all_conf.append(conf)

        tile_rows.append({
            "tile": tile["tile"],
            "matches": len(k0),
            "geo_samples": tile["geo_samples"],
        })

        del t_a
        del t_b
        del out

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_pts0:

        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "feature_matching",
            "failure_reason": "No usable tiled LoFTR matches",
            "runtime": time.perf_counter() - t0,
            "n_candidates": 0,
            "n_inliers": 0,
        }

    pts0 = np.concatenate(
        all_pts0,
        axis=0
    ).astype(np.float32)

    pts1 = np.concatenate(
        all_pts1,
        axis=0
    ).astype(np.float32)

    confs = np.concatenate(
        all_conf,
        axis=0
    ).astype(np.float32)

    H, mask = cv2.findHomography(
        pts0,
        pts1,
        cv2.RANSAC,
        ransac_thresh,
        maxIters=10000,
        confidence=0.995
    )

    if H is None or mask is None:

        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "Homography estimation failed",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(pts0),
            "n_inliers": 0,
        }

    inls = mask.ravel().astype(bool)

    n_inliers = int(inls.sum())

    if n_inliers < 4:

        return {
            "method": "LoFTR",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "Insufficient tiled inliers",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(pts0),
            "n_inliers": n_inliers,
        }

    inlier_pts0 = pts0[inls]
    inlier_pts1 = pts1[inls]

    grid = ae.calculate_spatial_grid(
        inlier_pts0,
        src.shape
    )

    occupancy = (
        np.count_nonzero(grid)
        / 9.0
    )

    cv_val = (
        np.std(grid) / np.mean(grid)
        if np.mean(grid) > 0
        else 0.0
    )

    return {
        "method": "LoFTR",
        "success": True,

        "pts0": pts0,
        "pts1": pts1,

        "inlier_pts0": inlier_pts0,
        "inlier_pts1": inlier_pts1,

        "confidences": confs[inls],

        "H": H,

        "n_candidates": len(pts0),
        "n_inliers": n_inliers,

        "inlier_ratio":
            float(
                n_inliers / len(pts0)
            ),

        "spatial_occupancy":
            float(occupancy),

        "spatial_cv":
            float(cv_val),

        "runtime":
            time.perf_counter() - t0,

        "failure_reason": None,

        "tile_rows": tile_rows,
    }


# ============================================================
# Memory-safe SuperGlue replacement
# Used only if Adaptive fallback selects SuperGlue.
# ============================================================

def tiled_superglue(
    source_img,
    reference_img,
    sg_model=None,
    ransac_thresh=3.0
):

    t0 = time.perf_counter()

    if sg_model is None:

        sg_model = ae.Matching({
            "superpoint": {
                "nms_radius": 4,
                "keypoint_threshold": 0.005,
                "max_keypoints": 1024,
            },
            "superglue": {
                "weights": "outdoor",
                "sinkhorn_iterations": 20,
                "match_threshold": 0.2,
            }
        }).eval().to(ae._DEVICE)

    src = apply_clahe(source_img)
    ref = apply_clahe(reference_img)

    tiles = get_tiles(
        src.shape,
        ref.shape
    )

    all0 = []
    all1 = []
    all_conf = []

    for tile in tiles:

        ax0 = tile["A_x0"]
        ay0 = tile["A_y0"]
        ax1 = tile["A_x1"]
        ay1 = tile["A_y1"]

        bx0 = tile["B_x0"]
        by0 = tile["B_y0"]
        bx1 = tile["B_x1"]
        by1 = tile["B_y1"]

        ta = (
            torch.from_numpy(
                src[ay0:ay1, ax0:ax1]
            )
            .float()
            .div(255.0)
            .unsqueeze(0)
            .unsqueeze(0)
            .to(ae._DEVICE)
        )

        tb = (
            torch.from_numpy(
                ref[by0:by1, bx0:bx1]
            )
            .float()
            .div(255.0)
            .unsqueeze(0)
            .unsqueeze(0)
            .to(ae._DEVICE)
        )

        with torch.inference_mode():

            pred = sg_model({
                "image0": ta,
                "image1": tb,
            })

        kp0 = (
            pred["keypoints0"][0]
            .detach()
            .cpu()
            .numpy()
        )

        kp1 = (
            pred["keypoints1"][0]
            .detach()
            .cpu()
            .numpy()
        )

        matches = (
            pred["matches0"][0]
            .detach()
            .cpu()
            .numpy()
        )

        scores = (
            pred["matching_scores0"][0]
            .detach()
            .cpu()
            .numpy()
        )

        valid = matches > -1

        m0 = kp0[valid]
        m1 = kp1[matches[valid]]
        sc = scores[valid]

        if len(m0):

            m0[:, 0] += ax0
            m0[:, 1] += ay0

            m1[:, 0] += bx0
            m1[:, 1] += by0

            all0.append(m0)
            all1.append(m1)
            all_conf.append(sc)

        del ta
        del tb
        del pred

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all0:

        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "feature_matching",
            "failure_reason": "No tiled SuperGlue matches",
            "runtime": time.perf_counter() - t0,
            "n_candidates": 0,
            "n_inliers": 0,
        }

    pts0 = np.concatenate(
        all0,
        axis=0
    ).astype(np.float32)

    pts1 = np.concatenate(
        all1,
        axis=0
    ).astype(np.float32)

    confs = np.concatenate(
        all_conf,
        axis=0
    ).astype(np.float32)

    H, mask = cv2.findHomography(
        pts0,
        pts1,
        cv2.RANSAC,
        ransac_thresh,
        maxIters=10000,
        confidence=0.995
    )

    if H is None or mask is None:

        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "Homography estimation failed",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(pts0),
            "n_inliers": 0,
        }

    inls = mask.ravel().astype(bool)

    n_inliers = int(inls.sum())

    if n_inliers < 4:

        return {
            "method": "SuperGlue",
            "success": False,
            "failure_stage": "initial_ransac",
            "failure_reason": "Insufficient inliers",
            "runtime": time.perf_counter() - t0,
            "n_candidates": len(pts0),
            "n_inliers": n_inliers,
        }

    inlier_pts0 = pts0[inls]
    inlier_pts1 = pts1[inls]

    grid = ae.calculate_spatial_grid(
        inlier_pts0,
        src.shape
    )

    occupancy = (
        np.count_nonzero(grid)
        / 9.0
    )

    cv_val = (
        np.std(grid) / np.mean(grid)
        if np.mean(grid) > 0
        else 0.0
    )

    return {
        "method": "SuperGlue",
        "success": True,

        "pts0": pts0,
        "pts1": pts1,

        "inlier_pts0": inlier_pts0,
        "inlier_pts1": inlier_pts1,

        "confidences": confs[inls],

        "H": H,

        "n_candidates": len(pts0),
        "n_inliers": n_inliers,

        "inlier_ratio":
            float(
                n_inliers / len(pts0)
            ),

        "spatial_occupancy":
            float(occupancy),

        "spatial_cv":
            float(cv_val),

        "runtime":
            time.perf_counter() - t0,

        "failure_reason": None,
    }


# ============================================================
# IMPORTANT:
# Keep Adaptive's existing routing / quality gate / fallback
# logic. Replace only the execution implementations.
# ============================================================

ae.run_loftr_matching = tiled_loftr
ae.run_superglue_matching = tiled_superglue


# ============================================================
# Load Kaggle images
# ============================================================

source = load_gray(A_PATH)
reference = load_gray(B_PATH)


print("==============================================")
print("KAGGLE PAIR 01 — ADAPTIVE BENCHMARK")
print("==============================================")

print(
    "Source:",
    (source.shape[1], source.shape[0])
)

print(
    "Reference:",
    (reference.shape[1], reference.shape[0])
)

print()


# ============================================================
# Run EXISTING Adaptive pipeline
# ============================================================

t0 = time.perf_counter()

result = ae.run_adaptive_registration(
    source,
    reference
)

elapsed = time.perf_counter() - t0


# ============================================================
# Report router / quality gate
# ============================================================

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
    "Runtime:",
    f"{elapsed:.3f} s"
)

print()
print("Difficulty profile:")
print(
    result.get("difficulty_profile")
)

print()
print("Routing rule:")
print(
    result.get("decision")
)

print()
print("Quality gate:")
print(
    result.get("quality_gate")
)


# ============================================================
# External FINAL 14-point validation
# ============================================================

if not result.get("success", False):

    print()
    print("==============================================")
    print("ADAPTIVE REGISTRATION FAILED")
    print("==============================================")

    print(
        result.get("failure_reason")
    )

    raise SystemExit(1)


H_final = result[
    "downstream"
]["H_final"]


protocol = pd.read_csv(
    FINAL_PROTOCOL
)

checks = protocol.sort_values(
    "point_id"
)

check_A = checks[
    ["A_x", "A_y"]
].to_numpy(dtype=np.float32)

check_B = checks[
    ["B_x", "B_y"]
].to_numpy(dtype=np.float32)


pred_B = cv2.perspectiveTransform(
    check_A.reshape(-1, 1, 2),
    H_final
).reshape(-1, 2)


errors = np.linalg.norm(
    pred_B - check_B,
    axis=1
)


rmse = float(
    np.sqrt(np.mean(errors ** 2))
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
    np.mean(errors < 1.0) * 100
)


print()
print("==============================================")
print("ADAPTIVE — FINAL 14-POINT VALIDATION")
print("==============================================")

print(
    "Primary matcher:",
    result["primary_choice"]
)

print(
    "Final matcher used:",
    result["final_matcher_used"]
)

print(
    "Fallback used:",
    result["fallback_used"]
)

print()
print("Check RMSE:", f"{rmse:.6f} px")
print("Check mean:", f"{mean_error:.6f} px")
print(
    "Check median:",
    f"{median_error:.6f} px"
)
print(
    "Check max:",
    f"{max_error:.6f} px"
)
print(
    "Checks < 1 px:",
    f"{below_1:.2f}%"
)

print()
print("Adaptive downstream metrics:")
print(
    "Selected points:",
    result["downstream"]["n_selected"]
)

print(
    "Final inliers:",
    result["downstream"]["n_final_inliers"]
)

print(
    "Final inlier ratio:",
    result["downstream"]["final_inlier_ratio"]
)

print(
    "Spatial occupancy:",
    result["downstream"]["spatial_occupancy"]
)

print(
    "Spatial CV:",
    result["downstream"]["spatial_cv"]
)

print()
print("Final homography:")
print(H_final)


# ============================================================
# Save result
# ============================================================

output = (
    KAGGLE_ROOT
    / "kaggle_pair01_adaptive_results.csv"
)

pd.DataFrame({
    "point_id": np.arange(1, 15),
    "A_x": check_A[:, 0],
    "A_y": check_A[:, 1],
    "B_x": check_B[:, 0],
    "B_y": check_B[:, 1],
    "pred_B_x": pred_B[:, 0],
    "pred_B_y": pred_B[:, 1],
    "error_px": errors,
}).to_csv(
    output,
    index=False
)

print()
print("Saved:")
print(output)
