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

GEO_FILE = (
    DATA_ROOT
    / "pair01_actual_geo_matches.csv"
)

FINAL_PROTOCOL = (
    DATA_ROOT
    / "pair01_FINAL_validation_protocol.csv"
)


# ============================================================
# EXPERIMENTAL QUICKNESS PARAMETERS
# ============================================================

GEO_THRESHOLD = 0.00020

TILE_W = 600
TILE_H = 600

X_CENTERS = [300, 900]
Y_FRACTIONS = [0.10, 0.37, 0.63, 0.90]

MIN_GEO_SAMPLES_PER_TILE = 50

MAX_REFINE_TILES = 3

# Same provisional gate used in Quickness V1.
MIN_INLIER_RATIO = 0.30
MIN_SPATIAL_OCCUPANCY = 0.7778
MAX_SPATIAL_CV = 0.80
MAX_GEO_DISAGREEMENT = 100.0


# ============================================================
# IMPORT EXISTING ENGINE
# ============================================================

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    load_loftr_matcher,
    run_loftr_matching,
)


# ============================================================
# HELPERS
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


def clamp_tile(
    cx,
    cy,
    width,
    height
):
    x0 = int(round(
        cx - TILE_W / 2
    ))

    y0 = int(round(
        cy - TILE_H / 2
    ))

    x0 = max(
        0,
        min(x0, width - TILE_W)
    )

    y0 = max(
        0,
        min(y0, height - TILE_H)
    )

    return (
        x0,
        y0,
        x0 + TILE_W,
        y0 + TILE_H
    )


def calculate_grid_metrics(
    points,
    image_shape
):
    h, w = image_shape[:2]

    grid = np.zeros(
        (3, 3),
        dtype=np.int32
    )

    if len(points) == 0:
        return 0.0, 0.0, grid

    for x, y in points:

        col = min(
            2,
            max(
                0,
                int(x / (w / 3.0))
            )
        )

        row = min(
            2,
            max(
                0,
                int(y / (h / 3.0))
            )
        )

        grid[row, col] += 1

    occupancy = (
        np.count_nonzero(grid) / 9.0
    )

    mean_value = np.mean(grid)

    if mean_value > 0:
        spatial_cv = (
            np.std(grid)
            / mean_value
        )
    else:
        spatial_cv = 0.0

    return (
        float(occupancy),
        float(spatial_cv),
        grid
    )


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
            "Could not estimate geospatial model."
        )

    mask = (
        mask.ravel().astype(bool)
    )

    return (
        geo,
        src,
        dst,
        H_geo,
        mask
    )


def geo_visual_disagreement(
    src_points,
    H_geo,
    H_visual
):

    if len(src_points) > 2000:

        rng = np.random.default_rng(
            42
        )

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

    errors = np.linalg.norm(
        visual_pred - geo_pred,
        axis=1
    )

    return {
        "median": float(
            np.median(errors)
        ),
        "p90": float(
            np.percentile(errors, 90)
        ),
        "max": float(
            np.max(errors)
        )
    }


def fit_combined_model(
    pts0,
    pts1,
    source_shape,
    H_geo,
    geo_src
):

    if len(pts0) < 4:
        return None

    H, mask = cv2.findHomography(
        pts0,
        pts1,
        cv2.RANSAC,
        3.0,
        maxIters=10000,
        confidence=0.995
    )

    if H is None or mask is None:
        return None

    mask = (
        mask.ravel().astype(bool)
    )

    n_inliers = int(
        np.sum(mask)
    )

    ratio = (
        n_inliers / len(pts0)
    )

    inlier_pts0 = pts0[mask]

    occupancy, spatial_cv, grid = (
        calculate_grid_metrics(
            inlier_pts0,
            source_shape
        )
    )

    consistency = geo_visual_disagreement(
        geo_src,
        H_geo,
        H
    )

    return {
        "H": H,
        "mask": mask,
        "n_inliers": n_inliers,
        "inlier_ratio": ratio,
        "spatial_occupancy": occupancy,
        "spatial_cv": spatial_cv,
        "geo_median": consistency["median"],
        "geo_p90": consistency["p90"],
        "geo_max": consistency["max"],
        "grid": grid,
    }


def passes_quickness_gate(metrics):

    if metrics is None:
        return False

    return (
        metrics["inlier_ratio"]
        >= MIN_INLIER_RATIO

        and metrics["spatial_occupancy"]
        >= MIN_SPATIAL_OCCUPANCY

        and metrics["spatial_cv"]
        <= MAX_SPATIAL_CV

        and metrics["geo_median"]
        <= MAX_GEO_DISAGREEMENT
    )


def calculate_external_validation(
    H,
    protocol
):

    check_A = protocol[
        ["A_x", "A_y"]
    ].to_numpy(
        dtype=np.float32
    )

    check_B = protocol[
        ["B_x", "B_y"]
    ].to_numpy(
        dtype=np.float32
    )

    pred = apply_homography(
        check_A,
        H
    )

    errors = np.linalg.norm(
        pred - check_B,
        axis=1
    )

    return {
        "rmse": float(
            np.sqrt(
                np.mean(errors ** 2)
            )
        ),
        "mean": float(
            np.mean(errors)
        ),
        "median": float(
            np.median(errors)
        ),
        "max": float(
            np.max(errors)
        ),
        "below_1": float(
            np.mean(errors < 1.0)
            * 100.0
        )
    }


# ============================================================
# LOAD DATA
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V2 TARGETED REFINEMENT")
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
# GEOSPATIAL MODEL
# ============================================================

(
    geo,
    geo_src,
    geo_dst,
    H_geo,
    geo_mask
) = build_geo_model()

print()
print("GEOSPATIAL MODEL")
print("----------------")

print(
    "Strict geo points:",
    len(geo)
)

print(
    "Geo RANSAC inliers:",
    int(
        geo_mask.sum()
    )
)

print(
    "Geo inlier ratio:",
    f"{100 * geo_mask.mean():.2f}%"
)


# ============================================================
# LOAD LoFTR ONCE
# ============================================================

t_total = time.perf_counter()

t0 = time.perf_counter()

loftr_model = load_loftr_matcher()

model_load_time = (
    time.perf_counter() - t0
)


# ============================================================
# GLOBAL LoFTR
# ============================================================

print()
print("==============================================")
print("STAGE 1 — GLOBAL LoFTR")
print("==============================================")

t0 = time.perf_counter()

global_result = run_loftr_matching(
    A,
    B,
    loftr_model=loftr_model,
    ransac_thresh=3.0
)

global_runtime = (
    time.perf_counter() - t0
)

if not global_result.get(
    "success",
    False
):
    raise RuntimeError(
        "Global LoFTR failed:\n"
        + str(
            global_result.get(
                "failure_reason"
            )
        )
    )


global_A = (
    global_result["inlier_pts0"]
    .copy()
)

global_B = (
    global_result["inlier_pts1"]
    .copy()
)

global_conf = (
    global_result["confidences"]
    .copy()
)


global_metrics = fit_combined_model(
    global_A,
    global_B,
    A.shape,
    H_geo,
    geo_src
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
    "Initial inlier ratio:",
    f"{100 * global_result['inlier_ratio']:.2f}%"
)

print(
    "Spatial occupancy:",
    f"{global_metrics['spatial_occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{global_metrics['spatial_cv']:.4f}"
)

print(
    "Geo disagreement:",
    f"{global_metrics['geo_median']:.3f} px"
)


# ============================================================
# BUILD GUIDED TILE CANDIDATES
# ============================================================

print()
print("==============================================")
print("STAGE 2 — TILE PRIORITIZATION")
print("==============================================")


ha, wa = A.shape
hb, wb = B.shape

common_y_min = float(
    geo["A_y"].min()
)

common_y_max = float(
    geo["A_y"].max()
)


tile_candidates = []


tile_id = 0

for y_fraction in Y_FRACTIONS:

    a_center_y = (
        common_y_min
        + y_fraction
        * (
            common_y_max
            - common_y_min
        )
    )

    for x_center in X_CENTERS:

        tile_id += 1

        (
            ax0,
            ay0,
            ax1,
            ay1
        ) = clamp_tile(
            x_center,
            a_center_y,
            wa,
            ha
        )

        local_geo = geo[
            (geo["A_x"] >= ax0)
            & (geo["A_x"] < ax1)
            & (geo["A_y"] >= ay0)
            & (geo["A_y"] < ay1)
        ]

        n_geo = len(
            local_geo
        )

        if n_geo < MIN_GEO_SAMPLES_PER_TILE:
            continue


        # Count current global inliers
        # inside this source tile.
        in_tile = (
            (global_A[:, 0] >= ax0)
            & (global_A[:, 0] < ax1)
            & (global_A[:, 1] >= ay0)
            & (global_A[:, 1] < ay1)
        )

        n_global = int(
            np.sum(in_tile)
        )


        # Use geographic model to predict
        # center of B search tile.
        center_a = np.array(
            [[
                (ax0 + ax1) / 2.0,
                (ay0 + ay1) / 2.0,
            ]],
            dtype=np.float32
        )

        center_b = apply_homography(
            center_a,
            H_geo
        )[0]

        (
            bx0,
            by0,
            bx1,
            by1
        ) = clamp_tile(
            center_b[0],
            center_b[1],
            wb,
            hb
        )


        tile_candidates.append({
            "tile_id": tile_id,
            "A_x0": ax0,
            "A_y0": ay0,
            "A_x1": ax1,
            "A_y1": ay1,
            "B_x0": bx0,
            "B_y0": by0,
            "B_x1": bx1,
            "B_y1": by1,
            "geo_samples": n_geo,
            "global_inliers": n_global,
        })


# Weakest first.
tile_candidates.sort(
    key=lambda x: (
        x["global_inliers"],
        -x["geo_samples"]
    )
)


print()
print(
    "Candidate tiles ranked weakest-first:"
)

for tile in tile_candidates:

    print(
        f"Tile {tile['tile_id']}: "
        f"global_inliers="
        f"{tile['global_inliers']}, "
        f"geo_samples="
        f"{tile['geo_samples']} "
        f"A=({tile['A_x0']}:{tile['A_x1']}, "
        f"{tile['A_y0']}:{tile['A_y1']})"
    )


# ============================================================
# CHECK GLOBAL FAST PATH
# ============================================================

if passes_quickness_gate(
    global_metrics
):

    print()
    print(
        "GLOBAL RESULT PASSES QUICKNESS GATE."
    )

    selected_H = global_metrics["H"]
    refined_tiles = 0

else:

    print()
    print(
        "GLOBAL RESULT FAILS QUICKNESS GATE."
    )

    print(
        "Starting targeted refinement..."
    )

    selected_A = [
        global_A
    ]

    selected_B = [
        global_B
    ]

    selected_conf = [
        global_conf
    ]

    current_H = global_metrics["H"]

    refined_tiles = 0

    selected_H = current_H

    # --------------------------------------------------------
    # Target only the weakest regions.
    # Stop immediately once the combined evidence passes.
    # --------------------------------------------------------

    for tile in tile_candidates:

        if (
            refined_tiles
            >= MAX_REFINE_TILES
        ):
            break


        print()
        print(
            "----------------------------------------------"
        )

        print(
            f"REFINING TILE "
            f"{tile['tile_id']}"
        )

        print(
            f"A=({tile['A_x0']}:{tile['A_x1']}, "
            f"{tile['A_y0']}:{tile['A_y1']})"
        )

        print(
            f"B=({tile['B_x0']}:{tile['B_x1']}, "
            f"{tile['B_y0']}:{tile['B_y1']})"
        )


        tile_A = A[
            tile["A_y0"]:tile["A_y1"],
            tile["A_x0"]:tile["A_x1"]
        ]

        tile_B = B[
            tile["B_y0"]:tile["B_y1"],
            tile["B_x0"]:tile["B_x1"]
        ]


        t_tile = time.perf_counter()

        tile_result = run_loftr_matching(
            tile_A,
            tile_B,
            loftr_model=loftr_model,
            ransac_thresh=3.0
        )

        tile_runtime = (
            time.perf_counter()
            - t_tile
        )


        if not tile_result.get(
            "success",
            False
        ):

            print(
                "Tile LoFTR failed:",
                tile_result.get(
                    "failure_reason"
                )
            )

            continue


        # Convert tile coordinates back
        # to full-image coordinates.
        tA = (
            tile_result["inlier_pts0"]
            .copy()
        )

        tB = (
            tile_result["inlier_pts1"]
            .copy()
        )

        tA[:, 0] += tile["A_x0"]
        tA[:, 1] += tile["A_y0"]

        tB[:, 0] += tile["B_x0"]
        tB[:, 1] += tile["B_y0"]

        tc = (
            tile_result["confidences"]
            .copy()
        )


        selected_A.append(
            tA
        )

        selected_B.append(
            tB
        )

        selected_conf.append(
            tc
        )

        refined_tiles += 1


        print(
            "Tile runtime:",
            f"{tile_runtime:.3f} s"
        )

        print(
            "Tile candidates:",
            tile_result[
                "n_candidates"
            ]
        )

        print(
            "Tile inliers:",
            tile_result[
                "n_inliers"
            ]
        )

        print(
            "Tile inlier ratio:",
            f"{100 * tile_result['inlier_ratio']:.2f}%"
        )


        # ----------------------------------------------------
        # Re-evaluate combined evidence
        # ----------------------------------------------------

        combined_A = np.vstack(
            selected_A
        )

        combined_B = np.vstack(
            selected_B
        )

        combined_metrics = (
            fit_combined_model(
                combined_A,
                combined_B,
                A.shape,
                H_geo,
                geo_src
            )
        )


        if combined_metrics is None:
            print(
                "Combined model could not be estimated."
            )
            continue


        selected_H = (
            combined_metrics["H"]
        )


        print()
        print(
            "COMBINED QUALITY AFTER TILE"
        )

        print(
            "Combined inliers:",
            combined_metrics["n_inliers"]
        )

        print(
            "Combined inlier ratio:",
            f"{100 * combined_metrics['inlier_ratio']:.2f}%"
        )

        print(
            "Spatial occupancy:",
            f"{combined_metrics['spatial_occupancy']:.4f}"
        )

        print(
            "Spatial CV:",
            f"{combined_metrics['spatial_cv']:.4f}"
        )

        print(
            "Geo disagreement:",
            f"{combined_metrics['geo_median']:.3f} px"
        )


        if passes_quickness_gate(
            combined_metrics
        ):

            print()
            print(
                "QUICKNESS GATE PASSED."
            )

            print(
                "Stopping refinement early."
            )

            break

        else:

            print(
                "Gate still failing."
            )

            print(
                "Trying next weakest tile..."
            )


# ============================================================
# FINAL EXTERNAL VALIDATION
# ============================================================

protocol = pd.read_csv(
    FINAL_PROTOCOL
).sort_values(
    "point_id"
)

validation = calculate_external_validation(
    selected_H,
    protocol
)


# ============================================================
# FINAL RESULT
# ============================================================

total_runtime = (
    time.perf_counter()
    - t_total
)


print()
print("==============================================")
print("QUICKNESS V2 FINAL RESULT")
print("==============================================")

print(
    "Refinement tiles used:",
    refined_tiles
)

print(
    "Check RMSE:",
    f"{validation['rmse']:.6f} px"
)

print(
    "Check mean:",
    f"{validation['mean']:.6f} px"
)

print(
    "Check median:",
    f"{validation['median']:.6f} px"
)

print(
    "Check max:",
    f"{validation['max']:.6f} px"
)

print(
    "Checks < 1 px:",
    f"{validation['below_1']:.2f}%"
)

print(
    "Model load:",
    f"{model_load_time:.3f} s"
)

print(
    "Global LoFTR:",
    f"{global_runtime:.3f} s"
)

print(
    "Total prototype runtime:",
    f"{total_runtime:.3f} s"
)

print()
print(
    "Quickness V2 does not use the external"
)

print(
    "14-point validation to decide refinement."
)

print(
    "Validation is used only for final reporting."
)