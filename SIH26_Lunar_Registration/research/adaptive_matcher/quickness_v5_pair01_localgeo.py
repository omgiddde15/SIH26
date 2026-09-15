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
    / "quickness_v5_pair01_localgeo_results.csv"
)


# ============================================================
# PARAMETERS
# ============================================================

GEO_THRESHOLD = 0.00020

TILE_W = 600
TILE_H = 600

# Same general candidate layout used by the
# previously successful geoguided Pair 01 experiment.
X_CENTERS = [300, 900]
Y_FRACTIONS = [0.10, 0.37, 0.63, 0.90]

MIN_GEO_SAMPLES = 50

# V5 deliberately tests only two local regions.
MAX_TILES = 2

# Local visual gate.
MIN_LOCAL_INLIERS = 20
MIN_LOCAL_INLIER_RATIO = 0.50

# Prevent one dense local tile from dominating.
MAX_LOCAL_POINTS = 200

# Balanced global pool.
MAX_POINTS_PER_CELL = 60


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


def grid_metrics(
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

    occupancy = (
        np.count_nonzero(grid)
        / 9.0
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
        grid,
        float(occupancy),
        float(spatial_cv)
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
            "Too few strict geo correspondences."
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

    H, mask = cv2.findHomography(
        src,
        dst,
        cv2.RANSAC,
        3.0,
        maxIters=10000,
        confidence=0.995
    )

    if H is None or mask is None:
        raise RuntimeError(
            "Geospatial model estimation failed."
        )

    return (
        geo,
        src,
        dst,
        H,
        mask.ravel().astype(bool)
    )


def fit_visual_model(
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

    errors = np.linalg.norm(
        apply_homography(
            inlier_pts0,
            H
        ) - inlier_pts1,
        axis=1
    )

    grid, occupancy, spatial_cv = (
        grid_metrics(
            inlier_pts0,
            source_shape
        )
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
        "grid": grid,
        "occupancy": occupancy,
        "spatial_cv": spatial_cv,
    }


def validate(
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
            np.mean(
                errors < 1.0
            ) * 100.0
        ),
    }


# ============================================================
# LOAD DATA
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V5 LOCAL-GEO REFINEMENT")
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
# LOAD GEO DATA
# ============================================================

(
    geo,
    geo_src,
    geo_dst,
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


global_model = fit_visual_model(
    global_A,
    global_B,
    A.shape
)

if global_model is None:
    raise RuntimeError(
        "Global visual model failed."
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
    "Global spatial occupancy:",
    f"{global_model['occupancy']:.4f}"
)

print(
    "Global spatial CV:",
    f"{global_model['spatial_cv']:.4f}"
)


# ============================================================
# STAGE 2 — BUILD LOCAL-GEO TILE CANDIDATES
# ============================================================

print()
print("==============================================")
print("STAGE 2 — LOCAL GEO TILE CANDIDATES")
print("==============================================")


common_y_min = float(
    geo["A_y"].min()
)

common_y_max = float(
    geo["A_y"].max()
)

candidate_tiles = []

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

    for a_center_x in X_CENTERS:

        tile_id += 1

        (
            ax0,
            ay0,
            ax1,
            ay1
        ) = clamp_tile(
            a_center_x,
            a_center_y,
            wa,
            ha
        )


        # ----------------------------------------------------
        # LOCAL GEO SUPPORT
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Place B tile using the LOCAL B correspondences.
        # Do NOT use H_geo here.
        # ----------------------------------------------------

        local_b_center_x = float(
            local_geo["B_x"].median()
        )

        local_b_center_y = float(
            local_geo["B_y"].median()
        )


        (
            bx0,
            by0,
            bx1,
            by1
        ) = clamp_tile(
            local_b_center_x,
            local_b_center_y,
            wb,
            hb
        )


        # ----------------------------------------------------
        # Global evidence already present in this A tile.
        # ----------------------------------------------------

        in_tile = (
            (global_A[:, 0] >= ax0)
            & (global_A[:, 0] < ax1)
            & (global_A[:, 1] >= ay0)
            & (global_A[:, 1] < ay1)
        )

        global_count = int(
            np.sum(in_tile)
        )


        # More geo support + less current
        # visual evidence = more useful candidate.
        need_score = (
            n_geo
            / (
                global_count + 5.0
            )
        )


        candidate_tiles.append({
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


candidate_tiles.sort(
    key=lambda t: t["need_score"],
    reverse=True
)


for tile in candidate_tiles:

    print(
        f"Tile {tile['tile_id']}: "
        f"global={tile['global_count']}, "
        f"geo={tile['geo_samples']}, "
        f"need={tile['need_score']:.2f}, "
        f"A=({tile['ax0']}:{tile['ax1']},"
        f"{tile['ay0']}:{tile['ay1']}), "
        f"B=({tile['bx0']}:{tile['bx1']},"
        f"{tile['by0']}:{tile['by1']})"
    )


# ============================================================
# START WITH GLOBAL MATCHES
# ============================================================

current_A = global_A.copy()
current_B = global_B.copy()
current_conf = global_conf.copy()

accepted_tiles = []
attempted_tiles = []


# ============================================================
# STAGE 3 — TWO LOCAL-GEO REFINEMENT TILES
# ============================================================

print()
print("==============================================")
print("STAGE 3 — LOCAL-GEO VISUAL REFINEMENT")
print("==============================================")


for tile in candidate_tiles:

    if len(accepted_tiles) >= MAX_TILES:
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
        "Local geo samples:",
        tile["geo_samples"]
    )

    print(
        "Existing global inliers:",
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

    local_result = run_loftr_matching(
        tile_A,
        tile_B,
        loftr_model=loftr_model,
        ransac_thresh=3.0
    )

    tile_runtime = (
        time.perf_counter()
        - t_tile
    )


    if not local_result.get(
        "success",
        False
    ):

        print(
            "Local LoFTR failed:"
        )

        print(
            local_result.get(
                "failure_reason"
            )
        )

        continue


    n_candidates = (
        local_result[
            "n_candidates"
        ]
    )

    n_inliers = (
        local_result[
            "n_inliers"
        ]
    )

    inlier_ratio = (
        local_result[
            "inlier_ratio"
        ]
    )


    print(
        "Tile runtime:",
        f"{tile_runtime:.3f} s"
    )

    print(
        "Candidates:",
        n_candidates
    )

    print(
        "Inliers:",
        n_inliers
    )

    print(
        "Inlier ratio:",
        f"{100 * inlier_ratio:.2f}%"
    )


    # --------------------------------------------------------
    # Local visual quality gate.
    # --------------------------------------------------------

    if (
        n_inliers
        < MIN_LOCAL_INLIERS
    ):

        print(
            "REJECTED: too few local inliers."
        )

        continue


    if (
        inlier_ratio
        < MIN_LOCAL_INLIER_RATIO
    ):

        print(
            "REJECTED: weak local inlier ratio."
        )

        continue


    local_A = (
        local_result[
            "inlier_pts0"
        ].copy()
    )

    local_B = (
        local_result[
            "inlier_pts1"
        ].copy()
    )

    local_conf = (
        local_result[
            "confidences"
        ].copy()
    )


    # Convert local coordinates to full-image coords.
    local_A[:, 0] += ax0
    local_A[:, 1] += ay0

    local_B[:, 0] += bx0
    local_B[:, 1] += by0


    # --------------------------------------------------------
    # Cap the local contribution.
    # --------------------------------------------------------

    if len(local_A) > MAX_LOCAL_POINTS:

        order = np.argsort(
            -local_conf
        )

        keep = order[
            :MAX_LOCAL_POINTS
        ]

        local_A = local_A[
            keep
        ]

        local_B = local_B[
            keep
        ]

        local_conf = local_conf[
            keep
        ]


    # --------------------------------------------------------
    # Replace existing global evidence from this tile.
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
    )

    print(
        "Local points retained:",
        len(local_A)
    )


# ============================================================
# STAGE 4 — BALANCED GLOBAL POOL
# ============================================================

print()
print("==============================================")
print("STAGE 4 — BALANCED GLOBAL POOL")
print("==============================================")


if len(current_A) < 4:
    raise RuntimeError(
        "Not enough correspondences."
    )


pre_model = fit_visual_model(
    current_A,
    current_B,
    A.shape
)

if pre_model is None:
    raise RuntimeError(
        "Could not fit pre-final model."
    )


projected = apply_homography(
    current_A,
    pre_model["H"]
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
    (r, c): []
    for r in range(3)
    for c in range(3)
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


selected_ids = []

for cell, ids in cells.items():

    ids = sorted(
        ids,
        key=lambda i: quality[i],
        reverse=True
    )

    selected_ids.extend(
        ids[
            :MAX_POINTS_PER_CELL
        ]
    )


selected_ids = np.asarray(
    selected_ids,
    dtype=np.int32
)


final_A = current_A[
    selected_ids
]

final_B = current_B[
    selected_ids
]


final_model = fit_visual_model(
    final_A,
    final_B,
    A.shape
)

if final_model is None:
    raise RuntimeError(
        "Final model failed."
    )


print(
    "Balanced points:",
    len(final_A)
)

print(
    "Final inliers:",
    final_model["n_inliers"]
)

print(
    "Final inlier ratio:",
    f"{100 * final_model['inlier_ratio']:.2f}%"
)

print(
    "Final occupancy:",
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

validation = validate(
    final_model["H"],
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
print("QUICKNESS V5 FINAL RESULT")
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
    "Model load:",
    f"{model_load_time:.3f} s"
)

print(
    "Global LoFTR:",
    f"{global_runtime:.3f} s"
)

print(
    "Total V5 runtime:",
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
    "Full tiled processed tiles: 7"
)


# ============================================================
# SAVE
# ============================================================

summary = pd.DataFrame([
    {
        "pair": "Pair 01",
        "method": "Quickness V5",
        "attempted_tiles": len(
            attempted_tiles
        ),
        "accepted_tiles": len(
            accepted_tiles
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