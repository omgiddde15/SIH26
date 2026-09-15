from pathlib import Path
import sys
import time

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

DATA_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adaptive_engine import (
    load_loftr_matcher,
    run_loftr_matching,
)


GEO_THRESHOLD = 0.00020


PAIRS = [
    {
        "name": "Pair 01",
        "a": "ch2_ohr_ncp_20251109T0909533595.png",
        "b": "ch2_ohr_ncp_20251109T1305444583.png",
        "geo": "pair01_actual_geo_matches.csv",
    },
    {
        "name": "Pair 03",
        "a": "ch2_ohr_ncp_20251012T0458211001.png",
        "b": "ch2_ohr_ncp_20251012T0656599480.png",
        "geo": "pair03_actual_geo_matches.csv",
    },
    {
        "name": "Pair 04",
        "a": "ch2_ohr_ncp_20230302T1800381020.png",
        "b": "ch2_ohr_ncp_20230302T1959073730.png",
        "geo": "pair04_actual_geo_matches.csv",
    },
    {
        "name": "Pair 05",
        "a": "ch2_ohr_ncp_20200824T0806596861.png",
        "b": "ch2_ohr_ncp_20200824T1003365280.png",
        "geo": "pair05_actual_geo_matches.csv",
    },
]


def load_gray(name):
    path = DATA_ROOT / "Images_PNG" / name

    img = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise RuntimeError(
            f"Could not load image:\n{path}"
        )

    return img


def build_geo_model(geo_file):
    geo = pd.read_csv(
        DATA_ROOT / geo_file
    )

    geo = geo[
        geo["geo_distance_deg"] <= GEO_THRESHOLD
    ].copy()

    if len(geo) < 8:
        raise RuntimeError(
            f"Too few strict geographic correspondences "
            f"in {geo_file}: {len(geo)}"
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
        dst,
        H_geo,
        mask,
    )


def transform_points(points, H):
    return cv2.perspectiveTransform(
        points.reshape(-1, 1, 2),
        H
    ).reshape(-1, 2)


print("==============================================")
print("QUICKNESS V1 — GLOBAL LoFTR DECISION PROBE")
print("==============================================")

print(
    "Geo threshold:",
    f"{GEO_THRESHOLD:.5f}°"
)


# Load model once.
t0 = time.perf_counter()

loftr_model = load_loftr_matcher()

model_load_time = (
    time.perf_counter() - t0
)

print(
    f"LoFTR model load: "
    f"{model_load_time:.3f} s"
)


all_results = []


for pair in PAIRS:

    print()
    print("==============================================")
    print(pair["name"])
    print("==============================================")

    A = load_gray(pair["a"])
    B = load_gray(pair["b"])

    print(
        "Image A:",
        (A.shape[1], A.shape[0])
    )

    print(
        "Image B:",
        (B.shape[1], B.shape[0])
    )


    # --------------------------------------------------------
    # Geographic model
    # --------------------------------------------------------

    (
        geo,
        geo_src,
        geo_dst,
        H_geo,
        geo_mask,
    ) = build_geo_model(
        pair["geo"]
    )

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


    # --------------------------------------------------------
    # Global LoFTR
    # --------------------------------------------------------

    t0 = time.perf_counter()

    visual = run_loftr_matching(
        A,
        B,
        loftr_model=loftr_model,
        ransac_thresh=3.0,
    )

    loftr_time = (
        time.perf_counter() - t0
    )

    if not visual.get("success", False):
        print(
            "Global LoFTR failed:",
            visual.get("failure_reason")
        )

        all_results.append({
            "pair": pair["name"],
            "loftr_success": False,
            "loftr_runtime_s": loftr_time,
        })

        continue


    H_visual = visual["H"]


    print()
    print("GLOBAL LoFTR")
    print("------------")

    print(
        "Runtime:",
        f"{loftr_time:.3f} s"
    )

    print(
        "Candidates:",
        visual["n_candidates"]
    )

    print(
        "Initial inliers:",
        visual["n_inliers"]
    )

    print(
        "Inlier ratio:",
        f"{100 * visual['inlier_ratio']:.2f}%"
    )

    print(
        "Spatial occupancy:",
        f"{visual['spatial_occupancy']:.4f}"
    )

    print(
        "Spatial CV:",
        f"{visual['spatial_cv']:.4f}"
    )


    # --------------------------------------------------------
    # Compare visual model to geo model
    # --------------------------------------------------------

    if len(geo_src) > 2000:
        rng = np.random.default_rng(42)

        idx = rng.choice(
            len(geo_src),
            size=2000,
            replace=False
        )

        test_src = geo_src[idx]

    else:
        test_src = geo_src


    geo_pred = transform_points(
        test_src,
        H_geo
    )

    visual_pred = transform_points(
        test_src,
        H_visual
    )

    disagreement = np.linalg.norm(
        visual_pred - geo_pred,
        axis=1
    )


    median_disagreement = float(
        np.median(disagreement)
    )

    p90_disagreement = float(
        np.percentile(
            disagreement,
            90
        )
    )

    max_disagreement = float(
        np.max(disagreement)
    )


    print()
    print("GEO/VISUAL CONSISTENCY")
    print("----------------------")

    print(
        "Median disagreement:",
        f"{median_disagreement:.3f} px"
    )

    print(
        "P90 disagreement:",
        f"{p90_disagreement:.3f} px"
    )

    print(
        "Maximum disagreement:",
        f"{max_disagreement:.3f} px"
    )


    # --------------------------------------------------------
    # Provisional classification
    # --------------------------------------------------------

    # IMPORTANT:
    # These are NOT frozen production thresholds.
    # They exist only to visualize the current evidence.
    #
    # A result is provisionally considered suitable for the
    # fast path when:
    #   1. enough inliers exist,
    #   2. coverage is good,
    #   3. spatial distribution is not badly concentrated,
    #   4. visual and geographic models agree reasonably well.

    provisional_fast = (
        visual["inlier_ratio"] >= 0.30
        and visual["spatial_occupancy"] >= 0.7778
        and visual["spatial_cv"] <= 0.80
        and median_disagreement <= 100.0
    )


    if provisional_fast:
        decision = "PROVISIONAL FAST PATH"
    else:
        decision = "PROVISIONAL TILED REFINEMENT"


    print()
    print(
        "PROVISIONAL DECISION:",
        decision
    )


    all_results.append({
        "pair": pair["name"],
        "loftr_success": True,
        "loftr_runtime_s": loftr_time,
        "n_candidates": visual["n_candidates"],
        "n_inliers": visual["n_inliers"],
        "inlier_ratio": visual["inlier_ratio"],
        "spatial_occupancy": visual["spatial_occupancy"],
        "spatial_cv": visual["spatial_cv"],
        "geo_points": len(geo),
        "geo_inlier_ratio": float(geo_mask.mean()),
        "median_geo_visual_disagreement_px":
            median_disagreement,
        "p90_geo_visual_disagreement_px":
            p90_disagreement,
        "max_geo_visual_disagreement_px":
            max_disagreement,
        "provisional_decision":
            decision,
    })


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

summary = pd.DataFrame(
    all_results
)

print()
print("==============================================")
print("QUICKNESS V1 SUMMARY")
print("==============================================")

print(
    summary.to_string(index=False)
)

output = ROOT / "quickness_v1_probe_results.csv"

summary.to_csv(
    output,
    index=False
)

print()
print("Saved:")
print(output)