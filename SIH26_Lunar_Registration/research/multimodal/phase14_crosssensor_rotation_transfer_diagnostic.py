
"""LunarReg Phase 14 — controlled cross-sensor + rotation transfer diagnostic.

Research-only. No production code is modified.

The diagnostic reuses Phase 11 LoFTR-derived anchors and applies a known
synthetic rotation transform to the IIRS image and its source anchor coordinates.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.ssc_matcher import compute_ssc_descriptors
from research.multimodal.ssc_rotation import (
    SSCRotationConfig,
    estimate_keypoint_orientations,
    rotate_ssc_offsets,
)


ANGLES_DEG = (0.0, 10.0, 20.0, 30.0, -20.0)
PATCH_SIZE = 7
RADIUS = 4.0
DESCRIPTOR_DIM = 21


def _gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def rotate_image_and_points(
    img: np.ndarray,
    points: np.ndarray,
    angle_deg: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    rotated = cv2.warpAffine(
        img,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    ones = np.ones((len(points), 1), dtype=np.float32)
    hp = np.hstack([points.astype(np.float32), ones])
    transformed = (matrix.astype(np.float32) @ hp.T).T
    return rotated, transformed, matrix


def load_anchor_pairs(path: Path) -> np.ndarray:
    """Extract exactly the source/reference coordinate pairs from Phase 11 JSON.

    The loader supports several explicit coordinate encodings but refuses to
    guess from unrelated numeric arrays.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    candidates: List[Dict[str, Any]] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            # Common explicit pair encodings.
            if all(k in obj for k in ("x0", "y0", "x1", "y1")):
                candidates.append(obj)
            elif "source" in obj and "reference" in obj:
                s = obj["source"]
                r = obj["reference"]
                if isinstance(s, (list, tuple)) and isinstance(r, (list, tuple)) and len(s) >= 2 and len(r) >= 2:
                    candidates.append({"x0": s[0], "y0": s[1], "x1": r[0], "y1": r[1]})
                elif isinstance(s, dict) and isinstance(r, dict):
                    if all(k in s for k in ("x", "y")) and all(k in r for k in ("x", "y")):
                        candidates.append({"x0": s["x"], "y0": s["y"], "x1": r["x"], "y1": r["y"]})
            elif "pts0" in obj and "pts1" in obj:
                p0, p1 = obj["pts0"], obj["pts1"]
                if isinstance(p0, (list, tuple)) and isinstance(p1, (list, tuple)):
                    if len(p0) >= 2 and len(p1) >= 2 and all(isinstance(v, (int, float)) for v in p0[:2] + p1[:2]):
                        candidates.append({"x0": p0[0], "y0": p0[1], "x1": p1[0], "y1": p1[1]})
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data)

    # Deduplicate while preserving order.
    unique: List[Tuple[float, float, float, float]] = []
    seen = set()
    for c in candidates:
        try:
            item = tuple(float(c[k]) for k in ("x0", "y0", "x1", "y1"))
        except Exception:
            continue
        if item not in seen:
            seen.add(item)
            unique.append(item)

    if len(unique) < 8:
        raise RuntimeError(
            f"Could not extract a sufficient set of explicit anchor pairs from {path}. "
            f"Found {len(unique)} usable pairs; expected the completed Phase 11 artifact."
        )

    # Phase 11 produced 12 anchors. Use the first 12 only if more are present,
    # but report the number used. We do not regenerate or optimize anchors.
    used = unique[:12]
    return np.asarray(used, dtype=np.float32)


def in_bounds(points: np.ndarray, shape: Tuple[int, int], margin: float) -> np.ndarray:
    h, w = shape
    return (
        (points[:, 0] >= margin)
        & (points[:, 0] < w - margin)
        & (points[:, 1] >= margin)
        & (points[:, 1] < h - margin)
    )


def p7_descriptor(img: np.ndarray, point: Tuple[float, float]) -> np.ndarray:
    cfg = type("Cfg", (), {
        "patch_size": PATCH_SIZE,
        "radius": RADIUS,
        "angles": (0.0, 60.0, 120.0, 180.0, 240.0, 300.0),
        "epsilon": 1e-6,
        "descriptor_dimension": DESCRIPTOR_DIM,
    })()
    d = compute_ssc_descriptors(
        _gray(img),
        np.asarray([point], dtype=np.float32),
        cfg,
    )
    return d[0]


def p9_descriptor(
    img: np.ndarray,
    point: Tuple[float, float],
    cfg: SSCRotationConfig,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    gray = _gray(img)
    pts = np.asarray([point], dtype=np.float32)

    thetas, stats = estimate_keypoint_orientations(gray, pts, cfg)
    theta = float(thetas[0])

    img_f = gray.astype(np.float32) / 255.0
    base_offsets = np.column_stack([
        RADIUS * np.cos(np.radians([0, 60, 120, 180, 240, 300])),
        RADIUS * np.sin(np.radians([0, 60, 120, 180, 240, 300])),
    ]).astype(np.float32)

    offsets = rotate_ssc_offsets(
        base_offsets,
        theta,
        orientation_sign=cfg.orientation_sign,
    )

    all_offsets = np.vstack([
        np.zeros((1, 2), dtype=np.float32),
        offsets,
    ])

    patches = [
        cv2.getRectSubPix(
            img_f,
            (PATCH_SIZE, PATCH_SIZE),
            (float(point[0] + all_offsets[k, 0]), float(point[1] + all_offsets[k, 1])),
        )
        for k in range(7)
    ]

    pair_indices = [(i, j) for i in range(7) for j in range(i + 1, 7)]
    d = np.asarray([
        np.mean((patches[i] - patches[j]) ** 2)
        for i, j in pair_indices
    ], dtype=np.float32)

    v = float(np.median(d)) + 1e-6
    s = np.exp(-d / v)
    norm = float(np.linalg.norm(s))
    desc = s / norm if norm > 1e-6 else np.zeros(DESCRIPTOR_DIM, dtype=np.float32)

    return desc, stats[0]


def axial_angle_error(theta_ref: float, theta_rot: float, applied_deg: float) -> float:
    """Smallest axial orientation error in degrees, modulo 180 degrees."""
    delta = theta_rot - theta_ref - math.radians(applied_deg)
    wrapped = (delta + math.pi / 2.0) % math.pi - math.pi / 2.0
    return math.degrees(wrapped)


def summarize(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"mean": None, "median": None, "p90": None, "max": None}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(np.max(arr)),
    }


def run_phase14(
    iirs_source: str,
    ohrc_reference: str,
    anchor_json: Path,
    output_dir: Path,
) -> pd.DataFrame:
    source = cv2.imread(iirs_source)
    reference = cv2.imread(ohrc_reference)
    if source is None or reference is None:
        raise FileNotFoundError("Could not decode IIRS/OHRC images.")

    anchors = load_anchor_pairs(anchor_json)
    src_base = anchors[:, :2]
    ref_pts = anchors[:, 2:]
    p9_cfg = SSCRotationConfig()

    # Native baseline descriptors at fixed anchors.
    base_p7 = [p7_descriptor(source, tuple(p)) for p in src_base]
    base_p9: List[np.ndarray] = []
    base_stats: List[Dict[str, Any]] = []
    ref_p7 = [p7_descriptor(reference, tuple(p)) for p in ref_pts]
    ref_p9: List[np.ndarray] = []
    ref_stats: List[Dict[str, Any]] = []

    for p in src_base:
        d, st = p9_descriptor(source, tuple(p), p9_cfg)
        base_p9.append(d)
        base_stats.append(st)
    for p in ref_pts:
        d, st = p9_descriptor(reference, tuple(p), p9_cfg)
        ref_p9.append(d)
        ref_stats.append(st)

    rows: List[Dict[str, Any]] = []

    for angle in ANGLES_DEG:
        if angle == 0.0:
            rotated = source.copy()
            transformed = src_base.copy()
        else:
            rotated, transformed, _ = rotate_image_and_points(source, src_base, angle)

        # Keep anchors valid under the largest frozen footprint.
        mask = in_bounds(transformed, _gray(rotated).shape, margin=PATCH_SIZE / 2.0 + RADIUS + 1.0)
        valid_idx = np.flatnonzero(mask)

        for method in ("Phase 7 SSC", "Phase-9-derived Rot-Norm SSC"):
            same_sensor: List[float] = []
            cross_sensor: List[float] = []
            cross_sensor_delta: List[float] = []
            angle_errors: List[float] = []
            orientation_valid = 0
            orientation_total = 0

            for i in valid_idx:
                pt_rot = tuple(transformed[i])
                if method == "Phase 7 SSC":
                    d_rot = p7_descriptor(rotated, pt_rot)
                    d_base = base_p7[i]
                    d_ref = ref_p7[i]
                else:
                    d_rot, st_rot = p9_descriptor(rotated, pt_rot, p9_cfg)
                    d_base = base_p9[i]
                    d_ref = ref_p9[i]

                    # Base and rotated orientation diagnostics.
                    st_base = base_stats[i]
                    orientation_total += 1
                    orientation_valid += int(st_rot.get("status") == "valid")
                    if st_base.get("status") == "valid" and st_rot.get("status") == "valid":
                        angle_errors.append(
                            axial_angle_error(
                                float(st_base["theta"]),
                                float(st_rot["theta"]),
                                angle,
                            )
                        )

                same = float(np.linalg.norm(d_base - d_rot))
                cross = float(np.linalg.norm(d_rot - d_ref))

                if angle == 0.0:
                    native_cross = cross
                else:
                    native_cross = float(np.linalg.norm(d_base - d_ref))

                same_sensor.append(same)
                cross_sensor.append(cross)
                cross_sensor_delta.append(cross - native_cross)

            sm = summarize(same_sensor)
            cm = summarize(cross_sensor)
            dm = summarize(cross_sensor_delta)
            am = summarize(angle_errors)

            rows.append({
                "angle_deg": angle,
                "method": method,
                "anchor_pairs_total": len(anchors),
                "anchor_pairs_valid_after_rotation": len(valid_idx),
                "same_sensor_rotation_mean_l2": sm["mean"],
                "same_sensor_rotation_median_l2": sm["median"],
                "same_sensor_rotation_p90_l2": sm["p90"],
                "cross_sensor_mean_l2": cm["mean"],
                "cross_sensor_median_l2": cm["median"],
                "cross_sensor_p90_l2": cm["p90"],
                "cross_sensor_delta_mean_l2": dm["mean"],
                "cross_sensor_delta_median_l2": dm["median"],
                "orientation_valid_fraction": (
                    orientation_valid / orientation_total
                    if orientation_total else None
                ),
                "orientation_error_mean_deg": am["mean"],
                "orientation_error_median_deg": am["median"],
                "orientation_error_p90_deg": am["p90"],
            })

    df = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / "phase14_anchor_transfer_results.csv", index=False)

    design = {
        "phase": 14,
        "research_question": "Is the remaining angle failure primarily rotation sensitivity or cross-sensor compatibility?",
        "anchor_source": str(anchor_json),
        "anchor_ground_truth": False,
        "anchor_count": int(len(anchors)),
        "angles_deg": list(ANGLES_DEG),
        "patch_size": PATCH_SIZE,
        "radius": RADIUS,
        "methods": ["Phase 7 SSC", "Phase-9-derived Rot-Norm SSC"],
        "production_modified": False,
        "automatic_winner_selection": False,
    }
    (output_dir / "phase14_design.json").write_text(
        json.dumps(design, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# LunarReg Phase 14 — Controlled Cross-Sensor + Rotation Transfer Diagnostic",
        "",
        f"Anchor pairs used: {len(anchors)}",
        "Anchor source: Phase 11 LoFTR-derived diagnostic anchors (not ground truth).",
        "",
        "The central diagnostic is the separation between:",
        "1. same-sensor rotation descriptor change, and",
        "2. cross-sensor descriptor distance after rotation.",
        "",
        "## Results",
        "",
        df.to_markdown(index=False),
        "",
        "## Production boundary",
        "No production routing, quality gate, Locked LoFTR, RANSAC mathematics, or common downstream implementation is modified.",
        "",
        "No automatic winner or production decision is applied.",
    ]
    (output_dir / "phase14_anchor_transfer_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iirs-source", required=True)
    ap.add_argument("--ohrc-reference", required=True)
    ap.add_argument(
        "--anchor-json",
        default="research/multimodal/phase11_results/phase11_loftr_anchor_pairs.json",
    )
    args = ap.parse_args()

    out = Path("research") / "multimodal" / "phase14_results"
    df = run_phase14(
        args.iirs_source,
        args.ohrc_reference,
        Path(args.anchor_json),
        out,
    )

    print(
        f"Phase 14 complete. rows={len(df)} "
        f"angles={df['angle_deg'].nunique()} methods={df['method'].nunique()} "
        f"output={out}"
    )
    print(
        "Diagnosis intentionally left for evidence review; "
        "no automatic winner or production decision was applied."
    )


if __name__ == "__main__":
    main()
