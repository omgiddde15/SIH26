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
    / "quickness_v6_pair01_refinement_only_results.csv"
)


# ============================================================
# EXPERIMENTAL PARAMETERS
# ============================================================

GEO_THRESHOLD = 0.00020

TILE_W = 600
TILE_H = 600

# Pair 01 has:
#   x = short dimension (~1200)
#   y = long dimension (~10106)
#
# These source regions come from the previously successful
# Pair 01 geoguided tiled experiment.
A_X_RANGES = [
    (0, 600),
    (600, 1200),
]

A_Y_RANGES = [
    (1246, 1846),
    (3044, 3644),
    (4775, 5375),
    (6573, 7173),
]

MIN_GEO_SAMPLES = 50

# We deliberately use fewer than the full 7 processed tiles.
MAX_ATTEMPTS = 6
MAX_ACCEPTED_TILES = 4

# Local visual-quality gate.
MIN_LOCAL_INLIERS = 20
MIN_LOCAL_INLIER_RATIO = 0.50

# Prevent one dense tile from dominating.
MAX_LOCAL_POINTS = 400

# Balanced final pool.
MAX_POINTS_PER_GRID_CELL = 100


# ============================================================
# EXISTING LoFTR ENGINE
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
    center_x,
    center_y,
    width,
    height
):
    x0 = int(round(
        center_x - TILE_W / 2
    ))

    y0 = int(round(
        center_y - TILE_H / 2
    ))

    x0 = max(
        0,
        min(
            x0,
            width - TILE_W
        )
    )

    y0 = max(
        0,
        min(
            y0,
            height - TILE_H
        )
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
            "Could not estimate geographic model."
        )

    return (
        geo,
        src,
        dst,
        H_geo,
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

    mask = (
        mask.ravel().astype(bool)
    )

    inlier_pts0 = pts0[mask]
    inlier_pts1 = pts1[mask]

    projected = apply_homography(
        inlier_pts0,
        H
    )

    errors = np.linalg.norm(
        projected - inlier_pts1,
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
            np.percentile(
                errors,
                90
            )
        ),
        "grid": grid,
        "occupancy": float(
            occupancy
        ),
        "spatial_cv": spatial_cv,
    }


def calculate_validation(
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

    pred_B = apply_homography(
        check_A,
        H
    )

    errors = np.linalg.norm(
        pred_B - check_B,
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
            )
            * 100.0
        ),
    }


def cap_tile_points(
    pts0,
    pts1,
    conf,
    max_points
):
    """
    Keep strong points while preserving spatial distribution
    inside the local tile.
    """

    n = len(pts0)

    if n <= max_points:
        return (
            pts0,
            pts1,
            conf
        )

    local_grid = {}

    # 4x4 local grid.
    tile_size = TILE_W / 4.0

    for i, (x, y) in enumerate(pts0):

        col = min(
            3,
            max(
                0,
                int(x / tile_size)
            )
        )

        row = min(
            3,
            max(
                0,
                int(y / tile_size)
            )
        )

        key = (
            row,
            col
        )

        local_grid.setdefault(
            key,
            []
        ).append(i)

    selected = []

    per_cell = max(
        1,
        max_points // max(
            1,
            len(local_grid)
        )
    )

    for ids in local_grid.values():

        ids = sorted(
            ids,
            key=lambda i: float(
                conf[i]
            ),
            reverse=True
        )

        selected.extend(
            ids[:per_cell]
        )

    # If the spatial cap did not fill the budget,
    # use remaining highest-confidence points.
    if len(selected) < max_points:

        used = set(
            selected
        )

        remaining = [
            i
            for i in range(n)
            if i not in used
        ]

        remaining.sort(
            key=lambda i: float(
                conf[i]
            ),
            reverse=True
        )

        selected.extend(
            remaining[
                :(
                    max_points
                    - len(selected)
                )
            ]
        )

    selected = np.asarray(
        selected[:max_points],
        dtype=np.int32
    )

    return (
        pts0[selected],
        pts1[selected],
        conf[selected]
    )


def candidate_priority(
    candidate
):
    return (
        candidate["need_score"]
    )


def select_candidates(
    candidates,
    max_count
):
    """
    Greedy selection that favors:
      - strong geographic support
      - low existing global evidence
      - spatial diversity
    """

    remaining = list(
        candidates
    )

    selected = []
    used_cells = set()

    while (
        remaining
        and len(selected) < max_count
    ):

        best = None
        best_score = -np.inf

        for candidate in remaining:

            cell = candidate[
                "coarse_cell"
            ]

            score = candidate_priority(
                candidate
            )

            # Encourage new spatial regions.
            if cell not in used_cells:
                score += 20.0

            # Encourage switching image side.
            selected_sides = {
                c["x_side"]
                for c in selected
            }

            if (
                candidate["x_side"]
                not in selected_sides
            ):
                score += 10.0

            if score > best_score:

                best_score = score
                best = candidate

        selected.append(
            best
        )

        used_cells.add(
            best["coarse_cell"]
        )

        remaining.remove(
            best
        )

    return selected


# ============================================================
# LOAD IMAGES
# ============================================================

print("==============================================")
print("PAIR 01 — QUICKNESS V6 REFINEMENT-ONLY")
print("==============================================")

A = load_gray(
    A_PATH
)

B = load_gray(
    B_PATH
)

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


global_A = global_result[
    "inlier_pts0"
].copy()

global_B = global_result[
    "inlier_pts1"
].copy()

global_conf = global_result[
    "confidences"
].copy()


global_model = fit_visual_model(
    global_A,
    global_B,
    A.shape
)

if global_model is None:
    raise RuntimeError(
        "Could not fit global visual model."
    )


print(
    "Runtime:",
    f"{global_runtime:.3f} s"
)

print(
    "Candidates:",
    global_result[
        "n_candidates"
    ]
)

print(
    "Initial inliers:",
    global_result[
        "n_inliers"
    ]
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
# GLOBAL EVIDENCE GRID
# ============================================================

global_grid = global_model[
    "grid"
]

print()
print(
    "Global 3x3 evidence grid:"
)

print(
    global_grid
)


# ============================================================
# STAGE 2 — BUILD LOCAL GEO CANDIDATES
# ============================================================

print()
print("==============================================")
print("STAGE 2 — LOCAL GEO TILE CANDIDATES")
print("==============================================")


candidate_tiles = []

tile_id = 0


# IMPORTANT:
# Pair 01 uses A_x as the short 0..1200 dimension
# and A_y as the long 0..10106 dimension.

for y_index, (
    ay0,
    ay1
) in enumerate(
    A_Y_RANGES
):

    for x_index, (
        ax0,
        ax1
    ) in enumerate(
        A_X_RANGES
    ):

        tile_id += 1


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
        # LOCAL GEO → B TILE CENTER
        # ----------------------------------------------------

        b_center_x = float(
            local_geo[
                "B_x"
            ].median()
        )

        b_center_y = float(
            local_geo[
                "B_y"
            ].median()
        )


        (
            bx0,
            by0,
            bx1,
            by1
        ) = clamp_tile(
            b_center_x,
            b_center_y,
            wb,
            hb
        )


        # ----------------------------------------------------
        # GLOBAL VISUAL EVIDENCE ALREADY IN A TILE
        # ----------------------------------------------------

        in_global_tile = (
            (global_A[:, 0] >= ax0)
            & (global_A[:, 0] < ax1)
            & (global_A[:, 1] >= ay0)
            & (global_A[:, 1] < ay1)
        )

        global_count = int(
            np.sum(
                in_global_tile
            )
        )


        # Coarse cell is based on tile center.
        center_x = (
            ax0 + ax1
        ) / 2.0

        center_y = (
            ay0 + ay1
        ) / 2.0

        coarse_cell = cell_for_point(
            center_x,
            center_y,
            wa,
            ha
        )

        x_side = (
            0
            if ax0 < 600
            else 1
        )


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
            "need_score": float(
                need_score
            ),
            "coarse_cell": coarse_cell,
            "x_side": x_side,
        })


selected_candidates = select_candidates(
    candidate_tiles,
    MAX_ATTEMPTS
)


for candidate in selected_candidates:

    print(
        f"Tile {candidate['tile_id']}: "
        f"geo={candidate['geo_samples']}, "
        f"global={candidate['global_count']}, "
        f"need={candidate['need_score']:.2f}, "
        f"cell={candidate['coarse_cell']}, "
        f"A=("
        f"{candidate['ax0']}:{candidate['ax1']}, "
        f"{candidate['ay0']}:{candidate['ay1']}), "
        f"B=("
        f"{candidate['bx0']}:{candidate['bx1']}, "
        f"{candidate['by0']}:{candidate['by1']})"
    )


# ============================================================
# REFINEMENT-ONLY POOL
# ============================================================
#
# IMPORTANT:
# Global LoFTR correspondences are deliberately NOT inserted
# into the final refinement pool.
#
# They are used only to:
#   - measure the global result
#   - identify weak regions
#   - prioritize candidate tiles
#
# This isolates the effect of local refinement.
# ============================================================

refined_A = []

refined_B = []

refined_conf = []

accepted_tiles = []

attempted_tiles = []


# ============================================================
# STAGE 3 — TARGETED LOCAL LoFTR
# ============================================================

print()
print("==============================================")
print("STAGE 3 — TARGETED LOCAL-GEO REFINEMENT")
print("==============================================")


for candidate in selected_candidates:

    if len(
        accepted_tiles
    ) >= MAX_ACCEPTED_TILES:
        break


    attempted_tiles.append(
        candidate["tile_id"]
    )


    ax0 = candidate["ax0"]
    ay0 = candidate["ay0"]
    ax1 = candidate["ax1"]
    ay1 = candidate["ay1"]

    bx0 = candidate["bx0"]
    by0 = candidate["by0"]
    bx1 = candidate["bx1"]
    by1 = candidate["by1"]


    print()
    print("----------------------------------------------")

    print(
        f"REFINING TILE {candidate['tile_id']}"
    )

    print(
        f"A=({ax0}:{ax1}, {ay0}:{ay1})"
    )

    print(
        f"B=({bx0}:{bx1}, {by0}:{by1})"
    )

    print(
        "Local geo samples:",
        candidate["geo_samples"]
    )

    print(
        "Existing global inliers:",
        candidate["global_count"]
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


    n_candidates = int(
        local_result[
            "n_candidates"
        ]
    )

    n_inliers = int(
        local_result[
            "n_inliers"
        ]
    )

    local_ratio = float(
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
        f"{100 * local_ratio:.2f}%"
    )


    # --------------------------------------------------------
    # Local visual quality gate
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


    local_A = local_result[
        "inlier_pts0"
    ].copy()

    local_B = local_result[
        "inlier_pts1"
    ].copy()

    local_conf = local_result[
        "confidences"
    ].copy()


    # --------------------------------------------------------
    # Convert local tile coordinates to full-image coords.
    # --------------------------------------------------------

    local_A[:, 0] += ax0
    local_A[:, 1] += ay0

    local_B[:, 0] += bx0
    local_B[:, 1] += by0


    # --------------------------------------------------------
    # Limit dense tile contribution while preserving
    # local spatial distribution.
    # --------------------------------------------------------

    (
        local_A,
        local_B,
        local_conf
    ) = cap_tile_points(
        local_A,
        local_B,
        local_conf,
        MAX_LOCAL_POINTS
    )


    refined_A.append(
        local_A
    )

    refined_B.append(
        local_B
    )

    refined_conf.append(
        local_conf
    )


    accepted_tiles.append(
        candidate["tile_id"]
    )


    print(
        "ACCEPTED:"
    )

    print(
        "Points retained:",
        len(local_A)
    )

    print(
        "Accepted tiles:",
        accepted_tiles
    )


# ============================================================
# CHECK REFINEMENT POOL
# ============================================================

if not refined_A:

    raise RuntimeError(
        "No local refinement tile passed the visual gate."
    )


all_refined_A = np.vstack(
    refined_A
)

all_refined_B = np.vstack(
    refined_B
)

all_refined_conf = np.concatenate(
    refined_conf
)


print()
print("==============================================")
print("STAGE 4 — REFINEMENT-ONLY GLOBAL MODEL")
print("==============================================")


print(
    "Refinement correspondences:",
    len(all_refined_A)
)

print(
    "Accepted tiles:",
    accepted_tiles
)


# ============================================================
# FIRST REFINEMENT MODEL
# ============================================================

pre_model = fit_visual_model(
    all_refined_A,
    all_refined_B,
    A.shape
)

if pre_model is None:

    raise RuntimeError(
        "Refinement-only RANSAC failed."
    )


print()
print(
    "Pre-final model:"
)

print(
    "Inliers:",
    pre_model["n_inliers"]
)

print(
    "Inlier ratio:",
    f"{100 * pre_model['inlier_ratio']:.2f}%"
)

print(
    "Occupancy:",
    f"{pre_model['occupancy']:.4f}"
)

print(
    "Spatial CV:",
    f"{pre_model['spatial_cv']:.4f}"
)


# ============================================================
# BALANCED FINAL SELECTION
# ============================================================

projected = apply_homography(
    all_refined_A,
    pre_model["H"]
)

residuals = np.linalg.norm(
    projected - all_refined_B,
    axis=1
)

quality = (
    all_refined_conf
    / (
        1.0 + residuals
    )
)


cells = {
    (row, col): []
    for row in range(3)
    for col in range(3)
}


for idx, point in enumerate(
    all_refined_A
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
        "Balanced refinement pool has fewer than 4 points."
    )


final_A = all_refined_A[
    selected_indices
]

final_B = all_refined_B[
    selected_indices
]


# ============================================================
# FINAL REFINED MODEL
# ============================================================

final_model = fit_visual_model(
    final_A,
    final_B,
    A.shape
)

if final_model is None:

    raise RuntimeError(
        "Final refinement model failed."
    )


H_final = final_model[
    "H"
]


print()
print(
    "BALANCED FINAL MODEL"
)

print(
    "Balanced points:",
    len(final_A)
)

print(
    "Final inliers:",
    final_model[
        "n_inliers"
    ]
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

validation = calculate_validation(
    H_final,
    protocol
)


# ============================================================
# FINAL RUNTIME
# ============================================================

total_runtime = (
    time.perf_counter()
    - t_total
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("==============================================")
print("QUICKNESS V6 FINAL RESULT")
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
    "Total V6 runtime:",
    f"{total_runtime:.3f} s"
)

print()
print("BASELINES")
print("---------")

print(
    "Global-only RMSE: 6.853206 px"
)

print(
    "Full geoguided tiled RMSE: 2.470816 px"
)

print(
    "Full geoguided processed tiles: 7"
)

print()
print(
    "V6 uses global LoFTR only for diagnosis "
    "and candidate prioritization."
)

print(
    "Final refinement model uses only accepted "
    "local-geographic tiles."
)


# ============================================================
# SAVE
# ============================================================

summary = pd.DataFrame([
    {
        "pair": "Pair 01",
        "method": "Quickness V6 refinement-only",
        "attempted_tiles": len(
            attempted_tiles
        ),
        "accepted_tiles": len(
            accepted_tiles
        ),
        "balanced_points": len(
            final_A
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
        "global_loftr_runtime_s": global_runtime,
        "total_runtime_s": total_runtime,
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