from pathlib import Path
import sys
import cv2
import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parent

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

SUPERGLUE_REPO = (
    Path(r"C:\Users\Dell\Videos\SIH26")
    / "SIH26_Lunar_Registration"
    / "research"
    / "superglue_repo"
)

sys.path.insert(0, str(SUPERGLUE_REPO))

from models.matching import Matching


A_NAME = "ch2_ohr_ncp_20251108T1727303521"
B_NAME = "ch2_ohr_ncp_20251108T1924377926"

GEO_FILE = (
    DATA_ROOT / "pair02_actual_geo_matches.csv"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

TILE_W = 600
TILE_H = 600

X_CENTERS = [300, 900]
Y_FRACTIONS = [0.10, 0.37, 0.63, 0.90]

GEO_THRESHOLD = 0.00020


def load_gray(path):
    img = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise RuntimeError(
            f"Could not load image: {path}"
        )

    return img


def clahe(img):
    return cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    ).apply(img)


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


def apply_homography(
    points,
    H
):
    return cv2.perspectiveTransform(
        points.reshape(-1, 1, 2),
        H
    ).reshape(-1, 2)


print("==============================================")
print("PAIR 02 — SUPERGLUE GEOGUIDED RESCUE TEST")
print("==============================================")

print(
    "Device:",
    DEVICE
)

# ------------------------------------------------------------
# Load images
# ------------------------------------------------------------

A = clahe(
    load_gray(
        DATA_ROOT
        / "Images_PNG"
        / f"{A_NAME}.png"
    )
)

B = clahe(
    load_gray(
        DATA_ROOT
        / "Images_PNG"
        / f"{B_NAME}.png"
    )
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


# ------------------------------------------------------------
# Load strict geospatial correspondences
# ------------------------------------------------------------

geo = pd.read_csv(GEO_FILE)

geo = geo[
    geo["geo_distance_deg"]
    <= GEO_THRESHOLD
].copy()

print()
print(
    "Strict geo threshold:",
    f"{GEO_THRESHOLD:.5f}°"
)

print(
    "Geo correspondences:",
    len(geo)
)

if len(geo) < 8:
    raise RuntimeError(
        "Too few geo correspondences."
    )


# ------------------------------------------------------------
# Fit temporary geospatial affine
# Used ONLY for tile placement.
# ------------------------------------------------------------

geo_src = geo[
    ["A_x", "A_y"]
].to_numpy(
    dtype=np.float32
)

geo_dst = geo[
    ["B_x", "B_y"]
].to_numpy(
    dtype=np.float32
)

H_geo, geo_mask = cv2.findHomography(
    geo_src,
    geo_dst,
    cv2.RANSAC,
    3.0,
    maxIters=10000,
    confidence=0.995
)

if H_geo is None:
    raise RuntimeError(
        "Could not fit geospatial homography."
    )

geo_mask = (
    geo_mask.ravel().astype(bool)
)

print()
print("GEOSPATIAL TILE-GUIDANCE MODEL")
print("--------------------------------")

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


# ------------------------------------------------------------
# Interior support
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Load SuperGlue
# ------------------------------------------------------------

print()
print("Loading SuperGlue...")

config = {
    "superpoint": {
        "nms_radius": 4,
        "keypoint_threshold": 0.005,
        "max_keypoints": 2048,
    },
    "superglue": {
        "weights": "outdoor",
        "sinkhorn_iterations": 20,
        "match_threshold": 0.20,
    },
}

model = Matching(
    config
).eval().to(DEVICE)


# ------------------------------------------------------------
# Run 8 guided tiles
# ------------------------------------------------------------

all_A = []
all_B = []

tile_results = []


for tile_id, (x_center, y_fraction) in enumerate(
    [
        (x, f)
        for f in Y_FRACTIONS
        for x in X_CENTERS
    ],
    start=1
):

    a_center_y = (
        common_y_min
        + y_fraction
        * (
            common_y_max
            - common_y_min
        )
    )

    A_x0, A_y0, A_x1, A_y1 = (
        clamp_tile(
            x_center,
            a_center_y,
            wa,
            ha
        )
    )

    A_tile = A[
        A_y0:A_y1,
        A_x0:A_x1
    ]

    center_a = np.array(
        [[
            (A_x0 + A_x1) / 2.0,
            (A_y0 + A_y1) / 2.0
        ]],
        dtype=np.float32
    )

    center_b = apply_homography(
        center_a,
        H_geo
    )[0]

    B_x0, B_y0, B_x1, B_y1 = (
        clamp_tile(
            center_b[0],
            center_b[1],
            wb,
            hb
        )
    )

    B_tile = B[
        B_y0:B_y1,
        B_x0:B_x1
    ]

    print()
    print(
        f"Tile {tile_id}: "
        f"A=({A_y0}:{A_y1}, {A_x0}:{A_x1}) "
        f"B=({B_y0}:{B_y1}, {B_x0}:{B_x1})"
    )

    # --------------------------------------------------------
    # Prepare tensors
    # --------------------------------------------------------

    A8_h = A_tile.shape[0] - (
        A_tile.shape[0] % 8
    )

    A8_w = A_tile.shape[1] - (
        A_tile.shape[1] % 8
    )

    B8_h = B_tile.shape[0] - (
        B_tile.shape[0] % 8
    )

    B8_w = B_tile.shape[1] - (
        B_tile.shape[1] % 8
    )

    A_crop = A_tile[
        :A8_h,
        :A8_w
    ]

    B_crop = B_tile[
        :B8_h,
        :B8_w
    ]

    t0 = torch.from_numpy(
        A_crop.astype(np.float32)
        / 255.0
    )[None, None].to(DEVICE)

    t1 = torch.from_numpy(
        B_crop.astype(np.float32)
        / 255.0
    )[None, None].to(DEVICE)

    with torch.inference_mode():
        pred = model({
            "image0": t0,
            "image1": t1,
        })

    k0 = (
        pred["keypoints0"][0]
        .cpu()
        .numpy()
    )

    k1 = (
        pred["keypoints1"][0]
        .cpu()
        .numpy()
    )

    matches0 = (
        pred["matches0"][0]
        .cpu()
        .numpy()
    )

    scores0 = (
        pred["matching_scores0"][0]
        .cpu()
        .numpy()
    )

    valid = matches0 > -1

    n_matches = int(
        np.sum(valid)
    )

    print(
        "  Keypoints A:",
        len(k0)
    )

    print(
        "  Keypoints B:",
        len(k1)
    )

    print(
        "  Matches:",
        n_matches
    )

    if n_matches < 4:
        print(
            "  RANSAC: insufficient matches"
        )
        continue

    mk0 = k0[valid].copy()
    mk1 = k1[
        matches0[valid]
    ].copy()

    conf = scores0[valid]

    # Convert tile coordinates to full image coordinates.
    mk0[:, 0] += A_x0
    mk0[:, 1] += A_y0

    mk1[:, 0] += B_x0
    mk1[:, 1] += B_y0

    H_tile, tile_mask = cv2.findHomography(
        mk0,
        mk1,
        cv2.RANSAC,
        3.0,
        maxIters=10000,
        confidence=0.995
    )

    if (
        H_tile is None
        or tile_mask is None
    ):
        print(
            "  RANSAC: failed"
        )
        continue

    tile_mask = (
        tile_mask.ravel().astype(bool)
    )

    n_inl = int(
        tile_mask.sum()
    )

    ratio = (
        n_inl / n_matches
    )

    print(
        "  RANSAC inliers:",
        n_inl
    )

    print(
        "  Inlier ratio:",
        f"{100 * ratio:.2f}%"
    )

    all_A.append(
        mk0[tile_mask]
    )

    all_B.append(
        mk1[tile_mask]
    )

    tile_results.append({
        "tile_id": tile_id,
        "matches": n_matches,
        "inliers": n_inl,
        "inlier_ratio": ratio,
        "mean_confidence": float(
            conf.mean()
        ),
    })


# ------------------------------------------------------------
# Combine
# ------------------------------------------------------------

if not all_A:
    raise RuntimeError(
        "SuperGlue produced no valid tile geometry."
    )

all_A = np.vstack(all_A)
all_B = np.vstack(all_B)


print()
print("==============================================")
print("COMBINED SUPERGLUE RESCUE RESULTS")
print("==============================================")

print(
    "Tiles with valid geometry:",
    len(tile_results)
)

print(
    "Combined inlier correspondences:",
    len(all_A)
)


H_visual, visual_mask = cv2.findHomography(
    all_A,
    all_B,
    cv2.RANSAC,
    3.0,
    maxIters=10000,
    confidence=0.995
)

if (
    H_visual is None
    or visual_mask is None
):
    raise RuntimeError(
        "Global SuperGlue homography failed."
    )

visual_mask = (
    visual_mask.ravel().astype(bool)
)

print(
    "Global RANSAC inliers:",
    int(visual_mask.sum()),
    "/",
    len(all_A)
)

print(
    "Global inlier ratio:",
    f"{100 * visual_mask.mean():.2f}%"
)


# ------------------------------------------------------------
# Compare visual model vs geospatial model
# ------------------------------------------------------------

sample_src = (
    geo_src
    if len(geo_src) <= 1000
    else geo_src[
        np.random.default_rng(42).choice(
            len(geo_src),
            1000,
            replace=False
        )
    ]
)

pred_geo = apply_homography(
    sample_src,
    H_geo
)

pred_visual = apply_homography(
    sample_src,
    H_visual
)

model_difference = np.linalg.norm(
    pred_visual - pred_geo,
    axis=1
)


print()
print("==============================================")
print("SUPERGLUE vs GEOSPATIAL MODEL")
print("==============================================")

print(
    f"Median difference: "
    f"{np.median(model_difference):.3f} px"
)

print(
    f"Mean difference:   "
    f"{np.mean(model_difference):.3f} px"
)

print(
    f"P90 difference:    "
    f"{np.percentile(model_difference, 90):.3f} px"
)

print(
    f"Maximum difference: "
    f"{np.max(model_difference):.3f} px"
)


print()
print("INTERPRETATION")
print("--------------")

median_diff = float(
    np.median(model_difference)
)

if median_diff < 10:
    print(
        "SuperGlue is broadly consistent "
        "with the geospatial model."
    )

elif median_diff < 50:
    print(
        "SuperGlue shows moderate "
        "geospatial disagreement."
    )

else:
    print(
        "SuperGlue shows STRONG "
        "geospatial disagreement."
    )

print()
print("This is a rescue diagnostic,")
print("not a final Pair 02 benchmark.")