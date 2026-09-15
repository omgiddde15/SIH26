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

OUTPUT = (
    ROOT
    / "quickness_v4_pair01_balanced_results.csv"
)


# ============================================================
# PARAMETERS
# ============================================================

GEO_THRESHOLD = 0.00020

TILE_W = 600
TILE_H = 600

X_CENTERS = [300, 900]
Y_FRACTIONS = [0.10, 0.37, 0.63, 0.90]

MIN_GEO_SAMPLES = 50

# At most 2 accepted refinement tiles.
MAX_ACCEPTED_TILES = 2

# We can test a few candidates, but don't run all 8.
MAX_TILE_ATTEMPTS = 5

# Local visual-quality gate.
MIN_LOCAL_INLIERS = 20
MIN_LOCAL_INLIER_RATIO = 0.50

# Cap dense local tile contribution.
MAX_LOCAL_POINTS = 200

# Final spatial balancing.
MAX_POINTS_PER_GRID_CELL = 60


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
            int(
                x / (width / 3.0)
            )
        )
    )

    row = min(
        2,
        max(
            0,
            int(
                y / (height / 3.0)
            )
        )
    )

    return row, col


def calculate_grid(
    points,
    image_shape
):
    h, w = image_shape[:2]

    grid = np.zeros(
        (3, 3),
        dtype=np.int32
    )

    for x, y in points:

        row, col = cell_for_point(
            x,
            y,
            w,
            h
        )

        grid[row, col] += 1

    return grid


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

    mask = (
        mask.ravel().astype(bool)
    )

    inlier_pts0 = pts0[mask]
    inlier_pts1 = pts1[mask]

    errors = np.linalg.norm(
        apply_homography(
            inlier_pts0,
            H
        ) - inlier_pts1,
        axis=1
    )

    grid = calculate_grid(
        inlier_pts0,
        source_shape
    )

    occupancy = (
        np.count_nonzero(grid)
        / 9.0
    )

    mean_grid = np.mean(grid)

    spatial_cv = (
        float(
            np.std(grid)
            / mean_grid
        )
        if mean_grid > 0
        else 0.0
    )

    return {
        "H": H,
        "mask": mask,
        "inlier_pts0": inlier_pts0,
        "inlier_pts1": inlier_pts1,
        "n_inliers": len(inlier_pts0),
        "inlier_ratio": (
            len(inlier_pts0)
            / len(pts0)
        ),
        "median_error": float(
            np.median(errors)
        ),
        "p90_error": float(
            np.percentile(errors, 90)
        ),
        "occupancy": float(
            occupancy
        ),
        "spatial_cv": spatial_cv,
        "grid": grid,
    }


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
            "Could not estimate geo model."
        )

    mask = (
        mask.ravel().astype(bool)
    )

    return (
        geo,
        src,
        H_geo,
        mask
    )


def calculate_validation(
    H,
    protocol
):
    A = protocol[
        ["A_x", "A_y"]
    ].to_numpy(
        dtype=np.float32
    )

    B = protocol[
        ["B_x", "B_y"]
    ].to_numpy(
        dtype=np.float32
    )

    pred = apply_homography(
        A,
        H
    )

    errors = np.linalg.norm(
        pred - B,
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
            np.mean(
                errors < 1.0
            ) * 100.0
        ),
    }


# ============================================================
# LOAD DATA
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V4 BALANCED REFINEMENT")
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
# GEOSPATIAL PRIOR
# ============================================================

(
    geo,
    geo_src,
    H_geo,
    geo_mask
) = build_geo_model()

print()
print("GEOSPATIAL PRIOR")
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

loftr_model = load_loftr_matcher()


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
        "Global model failed."
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
    f"{global_model['occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{global_model['spatial_cv']:.4f}"
)


# ============================================================
# STAGE 2 — BUILD ALL GEO-GUIDED TILE CANDIDATES
# ============================================================

print()
print("==============================================")
print("STAGE 2 — TILE PRIORITIZATION")
print("==============================================")


common_y_min = float(
    geo["A_y"].min()
)

common_y_max = float(
    geo["A_y"].max()
)

global_grid = global_model["grid"]

tile_candidates = []

tile_id = 0

for y_fraction in Y_FRACTIONS:

    center_y = (
        common_y_min
        + y_fraction
        * (
            common_y_max
            - common_y_min
        )
    )

    for center_x in X_CENTERS:

        tile_id += 1

        ax0, ay0, ax1, ay1 = (
            clamp_tile(
                center_x,
                center_y,
                wa,
                ha
            )
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

        if n_geo < MIN_GEO_SAMPLES:
            continue


        center_A = np.array(
            [[
                (ax0 + ax1) / 2.0,
                (ay0 + ay1) / 2.0
            ]],
            dtype=np.float32
        )

        center_B = apply_homography(
            center_A,
            H_geo
        )[0]

        bx0, by0, bx1, by1 = (
            clamp_tile(
                center_B[0],
                center_B[1],
                wb,
                hb
            )
        )


        tile_grid_points = (
            global_A[
                (global_A[:, 0] >= ax0)
                & (global_A[:, 0] < ax1)
                & (global_A[:, 1] >= ay0)
                & (global_A[:, 1] < ay1)
            ]
        )

        global_count = len(
            tile_grid_points
        )

        # ----------------------------------------------------
        # Need score:
        # Geographic support is useful,
        # while lower current evidence means
        # greater refinement opportunity.
        # ----------------------------------------------------

        need_score = (
            n_geo
            / (
                global_count + 5.0
            )
        )

        tile_candidates.append({
            "tile_id": tile_id,
            "ax0": ax0,
            "ay0": ay0,
            "ax1": ax1,
            "ay1": ay1,
            "bx0": bx0,
            "by0": by0,
            "bx1": bx1,
            "by1": by1,
            "geo_samples": n_geo,
            "global_count": global_count,
            "need_score": need_score,
        })


tile_candidates.sort(
    key=lambda x: x["need_score"],
    reverse=True
)


for tile in tile_candidates:

    print(
        f"Tile {tile['tile_id']}: "
        f"global={tile['global_count']}, "
        f"geo={tile['geo_samples']}, "
        f"need={tile['need_score']:.2f}"
    )


# ============================================================
# START WITH GLOBAL CORRESPONDENCES
# ============================================================

current_A = global_A.copy()
current_B = global_B.copy()
current_conf = global_conf.copy()

accepted_tiles = []
attempted_tiles = []


# ============================================================
# STAGE 3 — TARGETED REFINEMENT
# ============================================================

print()
print("==============================================")
print("STAGE 3 — TARGETED VISUAL REFINEMENT")
print("==============================================")


for tile in tile_candidates:

    if (
        len(accepted_tiles)
        >= MAX_ACCEPTED_TILES
    ):
        break

    if (
        len(attempted_tiles)
        >= MAX_TILE_ATTEMPTS
    ):
        break


    attempted_tiles.append(
        tile["tile_id"]
    )

    ax0 = tile["ax0"]
    ay0 = tile["ay0"]
    ax1 = tile["ax1"]
    ay1 = tile["ay1"]

    bx0 = tile["bx0"]
    by0 = tile["by0"]
    bx1 = tile["bx1"]
    by1 = tile["by1"]


    print()
    print("----------------------------------------------")
    print(
        f"REFINING TILE {tile['tile_id']}"
    )

    print(
        f"A=({ax0}:{ax1}, {ay0}:{ay1})"
    )

    print(
        f"B=({bx0}:{bx1}, {by0}:{by1})"
    )

    print(
        "Geo samples:",
        tile["geo_samples"]
    )

    print(
        "Existing global points:",
        tile["global_count"]
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

    result = run_loftr_matching(
        tile_A,
        tile_B,
        loftr_model=loftr_model,
        ransac_thresh=3.0
    )

    tile_runtime = (
        time.perf_counter()
        - t_tile
    )


    if not result.get(
        "success",
        False
    ):

        print(
            "Tile failed:"
        )

        print(
            result.get(
                "failure_reason"
            )
        )

        continue


    n_matches = result[
        "n_candidates"
    ]

    n_inliers = result[
        "n_inliers"
    ]

    local_ratio = result[
        "inlier_ratio"
    ]


    print(
        "Tile runtime:",
        f"{tile_runtime:.3f} s"
    )

    print(
        "Tile candidates:",
        n_matches
    )

    print(
        "Tile inliers:",
        n_inliers
    )

    print(
        "Tile inlier ratio:",
        f"{100 * local_ratio:.2f}%"
    )


    # --------------------------------------------------------
    # Visual-only local quality gate
    # --------------------------------------------------------

    if (
        n_inliers
        < MIN_LOCAL_INLIERS
    ):

        print(
            "REJECTED: insufficient local inliers."
        )

        continue


    if (
        local_ratio
        < MIN_LOCAL_INLIER_RATIO
    ):

        print(
            "REJECTED: weak local inlier ratio."
        )

        continue


    local_A = (
        result[
            "inlier_pts0"
        ].copy()
    )

    local_B = (
        result[
            "inlier_pts1"
        ].copy()
    )

    local_conf = (
        result[
            "confidences"
        ].copy()
    )


    # Convert to full-image coordinates.
    local_A[:, 0] += ax0
    local_A[:, 1] += ay0

    local_B[:, 0] += bx0
    local_B[:, 1] += by0


    # --------------------------------------------------------
    # Cap dense local contribution
    # --------------------------------------------------------

    if len(local_A) > MAX_LOCAL_POINTS:

        quality_order = np.argsort(
            -local_conf
        )

        keep = quality_order[
            :MAX_LOCAL_POINTS
        ]

        local_A = local_A[keep]
        local_B = local_B[keep]
        local_conf = local_conf[keep]


    # --------------------------------------------------------
    # Replace existing global points from this tile.
    # This prevents duplicated/conflicting evidence.
    # --------------------------------------------------------

    keep_global = ~(
        (current_A[:, 0] >= ax0)
        & (current_A[:, 0] < ax1)
        & (current_A[:, 1] >= ay0)
        & (current_A[:, 1] < ay1)
    )

    current_A = current_A[
        keep_global
    ]

    current_B = current_B[
        keep_global
    ]

    current_conf = current_conf[
        keep_global
    ]


    current_A = np.vstack([
        current_A,
        local_A
    ])

    current_B = np.vstack([
        current_B,
        local_B
    ])

    current_conf = np.concatenate([
        current_conf,
        local_conf
    ])


    accepted_tiles.append(
        tile["tile_id"]
    )


    print(
        "ACCEPTED:"
        f" {len(local_A)} local points added."
    )

    print(
        "Accepted refinement tiles:",
        accepted_tiles
    )


# ============================================================
# STAGE 4 — BALANCED FINAL CORRESPONDENCE SELECTION
# ============================================================

print()
print("==============================================")
print("STAGE 4 — BALANCED GLOBAL SELECTION")
print("==============================================")


pre_final = fit_model(
    current_A,
    current_B,
    A.shape
)

if pre_final is None:
    raise RuntimeError(
        "Pre-final model failed."
    )


H_pre = pre_final["H"]

projected = apply_homography(
    current_A,
    H_pre
)

errors = np.linalg.norm(
    projected - current_B,
    axis=1
)

quality = (
    current_conf
    / (
        1.0 + errors
    )
)


cells = {
    (row, col): []
    for row in range(3)
    for col in range(3)
}


for idx, point in enumerate(
    current_A
):

    row, col = cell_for_point(
        point[0],
        point[1],
        wa,
        ha
    )

    cells[
        (row, col)
    ].append(idx)


selected_indices = []

for cell, indices in cells.items():

    indices = sorted(
        indices,
        key=lambda i: quality[i],
        reverse=True
    )

    selected_indices.extend(
        indices[
            :MAX_POINTS_PER_GRID_CELL
        ]
    )


selected_indices = np.asarray(
    selected_indices,
    dtype=np.int32
)


if len(selected_indices) < 4:
    raise RuntimeError(
        "Balanced selection produced fewer than 4 points."
    )


final_A = current_A[
    selected_indices
]

final_B = current_B[
    selected_indices
]


# ============================================================
# FINAL HOMOGRAPHY
# ============================================================

final_model = fit_model(
    final_A,
    final_B,
    A.shape
)

if final_model is None:
    raise RuntimeError(
        "Final balanced model failed."
    )


H_final = final_model["H"]


print(
    "Balanced points:",
    len(final_A)
)

print(
    "Final RANSAC inliers:",
    final_model["n_inliers"]
)

print(
    "Final inlier ratio:",
    f"{100 * final_model['inlier_ratio']:.2f}%"
)

print(
    "Final spatial occupancy:",
    f"{final_model['occupancy']:.4f}"
)

print(
    "Final spatial CV:",
    f"{final_model['spatial_cv']:.4f}"
)


# ============================================================
# EXTERNAL 14-POINT VALIDATION
# ============================================================

protocol = pd.read_csv(
    FINAL_PROTOCOL
).sort_values(
    "point_id"
)

validation = calculate_validation(
    H_final,
    protocol
)


# ============================================================
# FINAL REPORT
# ============================================================

total_runtime = (
    time.perf_counter()
    - t_total
)

print()
print("==============================================")
print("QUICKNESS V4 FINAL RESULT")
print("==============================================")

print(
    "Attempted tiles:",
    attempted_tiles
)

print(
    "Accepted tiles:",
    accepted_tiles
)

print(
    "Accepted refinement count:",
    len(accepted_tiles)
)

print()
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

print()
print(
    "Global LoFTR runtime:",
    f"{global_runtime:.3f} s"
)

print(
    "Total V4 runtime:",
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


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame([
    {
        "pair": "Pair 01",
        "method": "Quickness V4",
        "accepted_tiles": len(
            accepted_tiles
        ),
        "attempted_tiles": len(
            attempted_tiles
        ),
        "final_inliers": final_model[
            "n_inliers"
        ],
        "final_inlier_ratio": final_model[
            "inlier_ratio"
        ],
        "spatial_occupancy": final_model[
            "occupancy"
        ],
        "spatial_cv": final_model[
            "spatial_cv"
        ],
        "check_rmse_px": validation[
            "rmse"
        ],
        "check_mean_px": validation[
            "mean"
        ],
        "check_median_px": validation[
            "median"
        ],
        "check_max_px": validation[
            "max"
        ],
        "checks_lt_1px_pct": validation[
            "below_1"
        ],
        "runtime_s": total_runtime,
    }
])

summary.to_csv(
    OUTPUT,
    index=False
)

print()
print(
    "Saved:",
    OUTPUT
)