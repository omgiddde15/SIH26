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
# EXPERIMENTAL PARAMETERS
# ============================================================

GEO_THRESHOLD = 0.00020

TILE_W = 600
TILE_H = 600

MAX_REFINE_TILES = 2

MIN_GEO_SAMPLES = 50
MIN_LOCAL_MATCHES = 8
MIN_LOCAL_INLIER_RATIO = 0.30

# Experimental consistency threshold.
# A tile is accepted only if its local transform
# is reasonably close to the geospatial prior.
MAX_LOCAL_GEO_DISAGREEMENT = 50.0


# ============================================================
# IMPORT EXISTING LoFTR
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


def cell_for_point(
    x,
    y,
    width,
    height
):
    col = min(
        2,
        max(
            0,
            int(x / (width / 3.0))
        )
    )

    row = min(
        2,
        max(
            0,
            int(y / (height / 3.0))
        )
    )

    return (
        row,
        col
    )


def grid_counts(
    points,
    width,
    height
):
    grid = np.zeros(
        (3, 3),
        dtype=np.int32
    )

    for x, y in points:
        r, c = cell_for_point(
            x,
            y,
            width,
            height
        )
        grid[r, c] += 1

    return grid


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
        confidence=0.995
    )

    if H_geo is None or mask is None:
        raise RuntimeError(
            "Could not estimate geospatial homography."
        )

    mask = mask.ravel().astype(bool)

    return (
        geo,
        src,
        dst,
        H_geo,
        mask
    )


def geo_disagreement(
    points,
    H_local,
    H_geo
):
    if len(points) == 0:
        return np.inf

    local_pred = apply_homography(
        points,
        H_local
    )

    geo_pred = apply_homography(
        points,
        H_geo
    )

    errors = np.linalg.norm(
        local_pred - geo_pred,
        axis=1
    )

    return {
        "median": float(
            np.median(errors)
        ),
        "p90": float(
            np.percentile(
                errors,
                90
            )
        ),
        "max": float(
            np.max(errors)
        )
    }


def fit_model(
    pts0,
    pts1,
    source_shape
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

    mask = mask.ravel().astype(bool)

    inlier_pts0 = pts0[mask]
    inlier_pts1 = pts1[mask]

    ratio = (
        len(inlier_pts0)
        / len(pts0)
    )

    h, w = source_shape[:2]

    grid = grid_counts(
        inlier_pts0,
        w,
        h
    )

    occupancy = (
        np.count_nonzero(grid)
        / 9.0
    )

    mean_grid = np.mean(grid)

    if mean_grid > 0:
        spatial_cv = (
            np.std(grid)
            / mean_grid
        )
    else:
        spatial_cv = 0.0

    return {
        "H": H,
        "mask": mask,
        "inlier_pts0": inlier_pts0,
        "inlier_pts1": inlier_pts1,
        "n_inliers": len(inlier_pts0),
        "inlier_ratio": float(ratio),
        "spatial_occupancy": float(occupancy),
        "spatial_cv": float(spatial_cv),
        "grid": grid,
    }


def validation_metrics(
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
        ),
    }


# ============================================================
# LOAD IMAGES
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V3 COVERAGE REFINEMENT")
print("==============================================")

A = load_gray(A_PATH)
B = load_gray(B_PATH)

ha, wa = A.shape
hb, wb = B.shape

print(
    "Image A:",
    (wa, ha)
)

print(
    "Image B:",
    (wb, hb)
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
    int(geo_mask.sum())
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
    time.perf_counter()
    - t0
)


# ============================================================
# STAGE 1 — GLOBAL LoFTR
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
    time.perf_counter()
    - t0
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
    global_result[
        "inlier_pts0"
    ].copy()
)

global_B = (
    global_result[
        "inlier_pts1"
    ].copy()
)

global_conf = (
    global_result[
        "confidences"
    ].copy()
)


global_model = fit_model(
    global_A,
    global_B,
    A.shape
)

if global_model is None:
    raise RuntimeError(
        "Global model could not be estimated."
    )


global_geo_consistency = (
    geo_disagreement(
        geo_src,
        global_model["H"],
        H_geo
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
    "Initial inlier ratio:",
    f"{100 * global_result['inlier_ratio']:.2f}%"
)

print(
    "Spatial occupancy:",
    f"{global_model['spatial_occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{global_model['spatial_cv']:.4f}"
)

print(
    "Geo disagreement:",
    f"{global_geo_consistency['median']:.3f} px"
)


# ============================================================
# STAGE 2 — COVERAGE ANALYSIS
# ============================================================

print()
print("==============================================")
print("STAGE 2 — COVERAGE ANALYSIS")
print("==============================================")


global_grid = global_model["grid"]

print(
    "Global 3x3 evidence grid:"
)

print(
    global_grid
)


missing_cells = []

for row in range(3):
    for col in range(3):

        if global_grid[row, col] > 0:
            continue

        # Full source-cell boundaries.
        cell_x0 = col * (wa / 3.0)
        cell_x1 = (col + 1) * (wa / 3.0)

        cell_y0 = row * (ha / 3.0)
        cell_y1 = (row + 1) * (ha / 3.0)

        local_geo = geo[
            (geo["A_x"] >= cell_x0)
            & (geo["A_x"] < cell_x1)
            & (geo["A_y"] >= cell_y0)
            & (geo["A_y"] < cell_y1)
        ]

        n_geo = len(local_geo)

        if n_geo >= MIN_GEO_SAMPLES:

            missing_cells.append({
                "row": row,
                "col": col,
                "geo_samples": n_geo,
            })


# Most useful uncovered cells first.
missing_cells.sort(
    key=lambda x: x["geo_samples"],
    reverse=True
)


print()
print(
    "Missing cells with geographic support:"
)

for item in missing_cells:
    print(
        f"cell=({item['row']},{item['col']}), "
        f"geo_samples={item['geo_samples']}"
    )


# ============================================================
# REFINE AT MOST TWO COVERAGE CELLS
# ============================================================

selected_A = [
    global_A
]

selected_B = [
    global_B
]

selected_conf = [
    global_conf
]

accepted_tiles = []

current_H = (
    global_model["H"]
)


for item in missing_cells:

    if (
        len(accepted_tiles)
        >= MAX_REFINE_TILES
    ):
        break


    row = item["row"]
    col = item["col"]


    # Center of missing source grid cell.
    center_a = np.array(
        [[
            (col + 0.5) * (wa / 3.0),
            (row + 0.5) * (ha / 3.0)
        ]],
        dtype=np.float32
    )


    # Geographic prior places B tile.
    center_b = apply_homography(
        center_a,
        H_geo
    )[0]


    (
        ax0,
        ay0,
        ax1,
        ay1
    ) = clamp_tile(
        center_a[0, 0],
        center_a[0, 1],
        wa,
        ha
    )


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


    print()
    print("----------------------------------------------")
    print(
        f"REFINEMENT CELL "
        f"({row},{col})"
    )

    print(
        f"A=({ax0}:{ax1}, {ay0}:{ay1})"
    )

    print(
        f"B=({bx0}:{bx1}, {by0}:{by1})"
    )

    print(
        "Geographic samples:",
        item["geo_samples"]
    )


    tile_A = A[
        ay0:ay1,
        ax0:ax1
    ]

    tile_B = B[
        by0:by1,
        bx0:bx1
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
            "Local LoFTR failed:"
        )

        print(
            tile_result.get(
                "failure_reason"
            )
        )

        continue


    local_A = (
        tile_result[
            "inlier_pts0"
        ].copy()
    )

    local_B = (
        tile_result[
            "inlier_pts1"
        ].copy()
    )

    local_conf = (
        tile_result[
            "confidences"
        ].copy()
    )


    # Convert local tile coordinates
    # back to full-image coordinates.
    local_A[:, 0] += ax0
    local_A[:, 1] += ay0

    local_B[:, 0] += bx0
    local_B[:, 1] += by0


    local_model = fit_model(
        local_A,
        local_B,
        A.shape
    )


    print(
        "Tile runtime:",
        f"{tile_runtime:.3f} s"
    )

    print(
        "Tile candidates:",
        tile_result["n_candidates"]
    )

    print(
        "Tile inliers:",
        tile_result["n_inliers"]
    )

    print(
        "Tile inlier ratio:",
        f"{100 * tile_result['inlier_ratio']:.2f}%"
    )


    if local_model is None:

        print(
            "Tile rejected: "
            "local homography failed."
        )

        continue


    local_consistency = (
        geo_disagreement(
            local_A,
            local_model["H"],
            H_geo
        )
    )


    print(
        "Local vs geo median:",
        f"{local_consistency['median']:.3f} px"
    )

    print(
        "Local vs geo P90:",
        f"{local_consistency['p90']:.3f} px"
    )


    # --------------------------------------------------------
    # Local consistency gate
    # --------------------------------------------------------

    local_pass = (
        tile_result["n_inliers"]
        >= MIN_LOCAL_MATCHES

        and tile_result["inlier_ratio"]
        >= MIN_LOCAL_INLIER_RATIO

        and local_consistency["median"]
        <= MAX_LOCAL_GEO_DISAGREEMENT
    )


    if not local_pass:

        print(
            "Tile REJECTED by local consistency gate."
        )

        continue


    print(
        "Tile ACCEPTED."
    )


    selected_A.append(
        local_A
    )

    selected_B.append(
        local_B
    )

    selected_conf.append(
        local_conf
    )

    accepted_tiles.append(
        (row, col)
    )


    # --------------------------------------------------------
    # Re-estimate after accepted tile
    # --------------------------------------------------------

    combined_A = np.vstack(
        selected_A
    )

    combined_B = np.vstack(
        selected_B
    )


    combined_model = fit_model(
        combined_A,
        combined_B,
        A.shape
    )


    if combined_model is None:

        print(
            "Combined model failed."
        )

        continue


    combined_consistency = (
        geo_disagreement(
            geo_src,
            combined_model["H"],
            H_geo
        )
    )


    current_H = (
        combined_model["H"]
    )


    print()
    print(
        "COMBINED MODEL"
    )

    print(
        "Inliers:",
        combined_model["n_inliers"]
    )

    print(
        "Inlier ratio:",
        f"{100 * combined_model['inlier_ratio']:.2f}%"
    )

    print(
        "Spatial occupancy:",
        f"{combined_model['spatial_occupancy']:.4f}"
    )

    print(
        "Spatial CV:",
        f"{combined_model['spatial_cv']:.4f}"
    )

    print(
        "Geo disagreement:",
        f"{combined_consistency['median']:.3f} px"
    )


# ============================================================
# FINAL EXTERNAL VALIDATION
# ============================================================

protocol = pd.read_csv(
    FINAL_PROTOCOL
).sort_values(
    "point_id"
)


final_validation = (
    validation_metrics(
        current_H,
        protocol
    )
)


total_runtime = (
    time.perf_counter()
    - t_total
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("==============================================")
print("QUICKNESS V3 FINAL RESULT")
print("==============================================")

print(
    "Accepted refinement cells:",
    accepted_tiles
)

print(
    "Refinement tiles used:",
    len(accepted_tiles)
)

print()
print(
    "Check RMSE:",
    f"{final_validation['rmse']:.6f} px"
)

print(
    "Check mean:",
    f"{final_validation['mean']:.6f} px"
)

print(
    "Check median:",
    f"{final_validation['median']:.6f} px"
)

print(
    "Check max:",
    f"{final_validation['max']:.6f} px"
)

print(
    "Checks < 1 px:",
    f"{final_validation['below_1']:.2f}%"
)

print()
print(
    "Model load:",
    f"{model_load_time:.3f} s"
)

print(
    "Global LoFTR:",
    f"{global_runtime:.3f} s"
)

print(
    "Total V3 runtime:",
    f"{total_runtime:.3f} s"
)

print()
print("BASELINES")
print("---------")

print(
    "Global-only RMSE: 6.853206 px"
)

print(
    "Full 8-tile RMSE: 2.470816 px"
)

print(
    "Full 8-tile processed tiles: 7"
)

print()
print(
    "V3 tests coverage-aware targeted refinement."
)