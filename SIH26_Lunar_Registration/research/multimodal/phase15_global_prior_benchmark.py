"""LunarReg Phase 15 — Controlled Global Orientation Prior Experiment.

Research-only. Zero production code, routing, or quality gates are modified.

Hypothesis:
"Does decoupling coarse global orientation alignment from local structure-tensor
orientation estimation improve cross-sensor descriptor transfer?"

Condition A: Phase 7 frozen SSC (no orientation normalization).
Condition B: Phase 9 frozen rotation-normalized SSC (local structure tensor).
Condition C: Global orientation prior (Oracle diagnostic using exact known synthetic angle).

Condition C is an oracle / upper-bound diagnostic using theta_global = -radians(phi_applied)
under the verified pixel-coordinate rotation convention. It is NOT a real global orientation
estimator or a deployable solution.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

BASE_OFFSETS = np.column_stack([
    RADIUS * np.cos(np.radians([0, 60, 120, 180, 240, 300])),
    RADIUS * np.sin(np.radians([0, 60, 120, 180, 240, 300])),
]).astype(np.float32)


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
    """Load Phase 11 anchors without regenerating them."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    pairs: List[Tuple[float, float, float, float]] = []

    def add_aligned(a: Any, b: Any) -> bool:
        try:
            a = np.asarray(a, dtype=np.float64)
            b = np.asarray(b, dtype=np.float64)
        except Exception:
            return False
        if a.ndim == 2 and b.ndim == 2 and a.shape[1] >= 2 and b.shape[1] >= 2:
            n = min(a.shape[0], b.shape[0])
            for i in range(n):
                if np.all(np.isfinite(a[i, :2])) and np.all(np.isfinite(b[i, :2])):
                    pairs.append((float(a[i, 0]), float(a[i, 1]), float(b[i, 0]), float(b[i, 1])))
            return n > 0
        return False

    def add_nx4(a: Any) -> bool:
        try:
            a = np.asarray(a, dtype=np.float64)
        except Exception:
            return False
        if a.ndim == 2 and a.shape[1] >= 4:
            for row in a:
                if np.all(np.isfinite(row[:4])):
                    pairs.append((float(row[0]), float(row[1]), float(row[2]), float(row[3])))
            return len(a) > 0
        return False

    def walk(obj: Any, path_str: str = "$") -> None:
        if isinstance(obj, dict):
            if ("source_points" in obj and "reference_points" in obj
                    and add_aligned(obj["source_points"], obj["reference_points"])):
                return
            if ("pts0" in obj and "pts1" in obj and add_aligned(obj["pts0"], obj["pts1"])):
                return
            if ("pts_src" in obj and "pts_ref" in obj and add_aligned(obj["pts_src"], obj["pts_ref"])):
                return
            if ("points_src" in obj and "points_ref" in obj and add_aligned(obj["points_src"], obj["points_ref"])):
                return
            if ("anchor_pairs" in obj and add_nx4(obj["anchor_pairs"])):
                return
            if ("pairs" in obj and add_nx4(obj["pairs"])):
                return
            for k, v in obj.items():
                walk(v, f"{path_str}.{k}")
        elif isinstance(obj, list):
            if add_nx4(obj):
                return
            for item in obj:
                if isinstance(item, (list, tuple)) and len(item) >= 4:
                    try:
                        vals = [float(x) for x in item[:4]]
                        if all(np.isfinite(vals)):
                            pairs.append(tuple(vals))
                    except Exception:
                        pass
                walk(item, f"{path_str}[]")

    walk(data)

    unique: List[Tuple[float, float, float, float]] = []
    seen = set()
    for p in pairs:
        key = tuple(round(float(v), 6) for v in p)
        if key not in seen:
            seen.add(key)
            unique.append(tuple(float(v) for v in p))

    if len(unique) < 8:
        raise RuntimeError(
            f"Could not extract sufficient Phase 11 anchors from {path}. "
            f"Found {len(unique)} usable pairs."
        )

    return np.asarray(unique[:12], dtype=np.float32)


def in_bounds(points: np.ndarray, shape: Tuple[int, int], margin: float) -> np.ndarray:
    h, w = shape
    return (
        (points[:, 0] >= margin)
        & (points[:, 0] < w - margin)
        & (points[:, 1] >= margin)
        & (points[:, 1] < h - margin)
    )


def compute_ssc_patch_descriptor(
    img_gray: np.ndarray,
    point: Tuple[float, float],
    offsets: np.ndarray,
) -> np.ndarray:
    """Extract 21-D SSC descriptor given arbitrary 6-neighbor offsets."""
    img_f = img_gray.astype(np.float32) / 255.0
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
    return s / norm if norm > 1e-6 else np.zeros(DESCRIPTOR_DIM, dtype=np.float32)


def p7_descriptor(img: np.ndarray, point: Tuple[float, float]) -> np.ndarray:
    """Condition A: Frozen Phase 7 un-rotated SSC descriptor."""
    return compute_ssc_patch_descriptor(_gray(img), point, BASE_OFFSETS)


def p9_descriptor(
    img: np.ndarray,
    point: Tuple[float, float],
    cfg: SSCRotationConfig,
    theta: Optional[float] = None,
    stat: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Condition B: Frozen Phase 9 rotation-normalized SSC descriptor."""
    gray = _gray(img)
    if theta is None or stat is None:
        pts = np.asarray([point], dtype=np.float32)
        thetas, stats = estimate_keypoint_orientations(gray, pts, cfg)
        theta_val = float(thetas[0])
        stat_out = dict(stats[0]) if stats else {"status": "unknown"}
    else:
        theta_val = float(theta)
        stat_out = dict(stat)

    stat_out["theta_rad"] = float(theta_val)
    stat_out["theta"] = float(theta_val)

    offsets = rotate_ssc_offsets(
        BASE_OFFSETS,
        theta_val,
        orientation_sign=cfg.orientation_sign,
    )
    desc = compute_ssc_patch_descriptor(gray, point, offsets)
    return desc, stat_out


def p15_global_descriptor(
    img: np.ndarray,
    point: Tuple[float, float],
    theta_global: float,
) -> np.ndarray:
    """Condition C: Global orientation prior (Oracle diagnostic)."""
    gray = _gray(img)
    offsets = rotate_ssc_offsets(
        BASE_OFFSETS,
        theta_global,
        orientation_sign=1.0,
    )
    return compute_ssc_patch_descriptor(gray, point, offsets)


def axial_angle_error(theta_ref: float, theta_rot: float, applied_deg: float) -> float:
    """Smallest axial orientation error in degrees, modulo 180 degrees."""
    delta = theta_rot - theta_ref - math.radians(applied_deg)
    wrapped = (delta + math.pi / 2.0) % math.pi - math.pi / 2.0
    return abs(math.degrees(wrapped))


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


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """Pure-Python markdown table generator without external dependencies."""
    headers = [str(c) for c in df.columns]
    rows: List[List[str]] = []
    for _, row in df.iterrows():
        formatted_row: List[str] = []
        for val in row:
            if pd.isna(val) or val is None:
                formatted_row.append("—")
            elif isinstance(val, (float, np.floating)):
                formatted_row.append(f"{val:.4f}")
            else:
                formatted_row.append(str(val))
        rows.append(formatted_row)

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"
    sep_line = "| " + " | ".join("-" * w for w in col_widths) + " |"
    data_lines = [
        "| " + " | ".join(val.ljust(w) for val, w in zip(row, col_widths)) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line] + data_lines)


def run_phase15(
    iirs_source: str,
    ohrc_reference: str,
    anchor_json: Path,
    output_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    source = cv2.imread(iirs_source)
    reference = cv2.imread(ohrc_reference)
    if source is None or reference is None:
        raise FileNotFoundError("Could not decode IIRS/OHRC images.")

    anchors = load_anchor_pairs(anchor_json)
    src_base = anchors[:, :2]
    ref_pts = anchors[:, 2:]
    p9_cfg = SSCRotationConfig()

    # Precompute Condition B baseline orientations and verify array lengths
    thetas_base_b, stats_base_b = estimate_keypoint_orientations(_gray(source), src_base, p9_cfg)
    thetas_ref_b, stats_ref_b = estimate_keypoint_orientations(_gray(reference), ref_pts, p9_cfg)
    if len(thetas_base_b) != len(src_base) or len(stats_base_b) != len(src_base):
        raise ValueError("Source orientation length mismatch.")
    if len(thetas_ref_b) != len(ref_pts) or len(stats_ref_b) != len(ref_pts):
        raise ValueError("Reference orientation length mismatch.")

    # 1. Condition A baseline descriptors (0 deg)
    base_p7 = [p7_descriptor(source, tuple(p)) for p in src_base]
    ref_p7 = [p7_descriptor(reference, tuple(p)) for p in ref_pts]
    native_cross_A = [float(np.linalg.norm(base_p7[i] - ref_p7[i])) for i in range(len(anchors))]

    # 2. Condition B baseline descriptors (0 deg)
    base_p9 = [
        p9_descriptor(source, tuple(src_base[i]), p9_cfg, theta=float(thetas_base_b[i]), stat=stats_base_b[i])[0]
        for i in range(len(anchors))
    ]
    ref_p9 = [
        p9_descriptor(reference, tuple(ref_pts[i]), p9_cfg, theta=float(thetas_ref_b[i]), stat=stats_ref_b[i])[0]
        for i in range(len(anchors))
    ]
    native_cross_B = [float(np.linalg.norm(base_p9[i] - ref_p9[i])) for i in range(len(anchors))]

    # 3. Condition C baseline descriptors (0 deg: theta_global = 0.0)
    base_p15_c0 = [p15_global_descriptor(source, tuple(p), 0.0) for p in src_base]
    ref_p15_c0 = [p15_global_descriptor(reference, tuple(p), 0.0) for p in ref_pts]
    native_cross_C = [float(np.linalg.norm(base_p15_c0[i] - ref_p15_c0[i])) for i in range(len(anchors))]

    conditions = (
        ("Condition A: Phase 7 Frozen SSC", "Phase 7 Frozen SSC"),
        ("Condition B: Phase 9 Frozen Rot-Norm SSC", "Phase 9 Frozen Rot-Norm SSC"),
        ("Condition C: Global Orientation Prior (Oracle)", "Global Orientation Prior (Oracle)"),
    )

    per_anchor_rows: List[Dict[str, Any]] = []
    aggregate_rows: List[Dict[str, Any]] = []

    for angle in ANGLES_DEG:
        if angle == 0.0:
            rotated = source.copy()
            transformed = src_base.copy()
        else:
            rotated, transformed, _ = rotate_image_and_points(source, src_base, angle)

        mask = in_bounds(transformed, _gray(rotated).shape, margin=PATCH_SIZE / 2.0 + RADIUS + 1.0)
        valid_idx = np.flatnonzero(mask)

        # Estimate rotated keypoint orientations for Condition B
        thetas_rot_b, stats_rot_b = estimate_keypoint_orientations(_gray(rotated), transformed, p9_cfg)
        if len(thetas_rot_b) != len(transformed) or len(stats_rot_b) != len(transformed):
            raise ValueError("Rotated orientation length mismatch.")

        for cond_key, cond_label in conditions:
            same_sensor_list: List[float] = []
            cross_sensor_list: List[float] = []
            cross_delta_list: List[float] = []
            angle_errors: List[float] = []
            orientation_valid_count = 0
            orientation_total_count = 0

            for i in valid_idx:
                pt_rot = tuple(transformed[i])

                if cond_key.startswith("Condition A"):
                    d_rot = p7_descriptor(rotated, pt_rot)
                    d_base = base_p7[i]
                    d_ref = ref_p7[i]
                    native_cross_0 = native_cross_A[i]

                elif cond_key.startswith("Condition B"):
                    theta_rot_i = float(thetas_rot_b[i])
                    st_rot_i = stats_rot_b[i]
                    d_rot, _ = p9_descriptor(rotated, pt_rot, p9_cfg, theta=theta_rot_i, stat=st_rot_i)
                    d_base = base_p9[i]
                    d_ref = ref_p9[i]
                    native_cross_0 = native_cross_B[i]

                    st_base = stats_base_b[i]
                    orientation_total_count += 1
                    is_valid_rot = (st_rot_i.get("status") == "valid")
                    orientation_valid_count += int(is_valid_rot)
                    if st_base.get("status") == "valid" and is_valid_rot:
                        angle_errors.append(
                            axial_angle_error(
                                float(thetas_base_b[i]),
                                theta_rot_i,
                                angle,
                            )
                        )

                else:  # Condition C: Global Orientation Prior (Oracle)
                    # Verified pixel-coordinate convention: theta_global = -radians(angle)
                    theta_global = -math.radians(angle) if angle != 0.0 else 0.0
                    d_rot = p15_global_descriptor(rotated, pt_rot, theta_global)
                    d_base = base_p15_c0[i]
                    d_ref = ref_p15_c0[i]
                    native_cross_0 = native_cross_C[i]

                same_dist = float(np.linalg.norm(d_base - d_rot))
                cross_dist = float(np.linalg.norm(d_rot - d_ref))
                # Safeguard 2: cross_sensor_rotation_delta = cross(phi) - cross(0) separately within each condition
                cross_delta = cross_dist - native_cross_0

                same_sensor_list.append(same_dist)
                cross_sensor_list.append(cross_dist)
                cross_delta_list.append(cross_delta)

                per_anchor_rows.append({
                    "anchor_id": int(i),
                    "rotation_angle": angle,
                    "condition": cond_label,
                    "same_sensor_distance": same_dist,
                    "cross_sensor_distance": cross_dist,
                    "cross_sensor_rotation_delta": cross_delta,
                })

            sm = summarize(same_sensor_list)
            cm = summarize(cross_sensor_list)
            dm = summarize(cross_delta_list)
            am = summarize(angle_errors)

            aggregate_rows.append({
                "angle_deg": angle,
                "condition": cond_label,
                "anchor_pairs_total": len(anchors),
                "valid_anchor_count": len(valid_idx),
                "same_sensor_mean_l2": sm["mean"],
                "same_sensor_median_l2": sm["median"],
                "same_sensor_p90_l2": sm["p90"],
                "same_sensor_max_l2": sm["max"],
                "cross_sensor_mean_l2": cm["mean"],
                "cross_sensor_median_l2": cm["median"],
                "cross_sensor_p90_l2": cm["p90"],
                "cross_sensor_max_l2": cm["max"],
                "cross_sensor_delta_mean_l2": dm["mean"],
                "cross_sensor_delta_median_l2": dm["median"],
                "cross_sensor_delta_p90_l2": dm["p90"],
                "cross_sensor_delta_max_l2": dm["max"],
                "orientation_valid_fraction": (
                    orientation_valid_count / orientation_total_count
                    if orientation_total_count else None
                ),
                "orientation_error_mean_deg": am["mean"],
                "orientation_error_median_deg": am["median"],
                "orientation_error_p90_deg": am["p90"],
                "orientation_error_max_deg": am["max"],
            })

    df_aggregate = pd.DataFrame(aggregate_rows)
    df_per_anchor = pd.DataFrame(per_anchor_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    df_aggregate.to_csv(output_dir / "phase15_aggregate_results.csv", index=False)
    df_per_anchor.to_csv(output_dir / "phase15_per_anchor_results.csv", index=False)

    design = {
        "phase": 15,
        "research_question": "Does decoupling coarse global orientation alignment from local structure-tensor orientation estimation improve cross-sensor descriptor transfer?",
        "anchor_source": str(anchor_json),
        "anchor_count": int(len(anchors)),
        "angles_deg": list(ANGLES_DEG),
        "patch_size": PATCH_SIZE,
        "radius": RADIUS,
        "descriptor_dim": DESCRIPTOR_DIM,
        "conditions": [
            "Condition A: Phase 7 Frozen SSC",
            "Condition B: Phase 9 Frozen Rot-Norm SSC",
            "Condition C: Global Orientation Prior (Oracle Diagnostic)",
        ],
        "safeguards": {
            "condition_c_nature": "Oracle diagnostic using exact known synthetic angle theta_global = -radians(phi_applied)",
            "cross_sensor_delta_definition": "cross_sensor_distance_at_phi - cross_sensor_distance_at_0 computed separately within each condition",
            "angle_search_tuning": False,
            "per_anchor_results_saved": True,
        },
        "production_modified": False,
        "automatic_winner_selection": False,
    }
    (output_dir / "phase15_design.json").write_text(
        json.dumps(design, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# LunarReg Phase 15 — Controlled Global Orientation Prior Experiment Report",
        "",
        f"**Anchor pairs used**: {len(anchors)} (reused from Phase 11 & Phase 14 LoFTR-derived diagnostic anchors)",
        "",
        "## Scientific Purpose & Safeguards",
        "This experiment tests whether decoupling coarse global orientation alignment from local structure-tensor orientation estimation improves cross-sensor descriptor transfer.",
        "",
        "> [!IMPORTANT]",
        "> **Condition C Nature & Limitation**:",
        "> Condition C is an **oracle diagnostic** using the exact known synthetic rotation angle (`theta_global = -radians(phi)`).",
        "> It is NOT a deployable global orientation estimator or an algorithmic solution. It represents an upper-bound diagnostic under controlled synthetic rotation.",
        "",
        "> [!NOTE]",
        "> **Cross-Sensor Delta Definition**:",
        "> `cross_sensor_rotation_delta = cross_sensor_distance_at_phi - cross_sensor_distance_at_0`",
        "> Computed **strictly separately within each condition** (A-A, B-B, C-C).",
        "",
        "## Aggregate Results (5 Angles × 3 Conditions)",
        "",
        _df_to_markdown_table(df_aggregate),
        "",
        "## Per-Anchor Results Summary",
        f"Per-anchor results saved to [`phase15_per_anchor_results.csv`](file:///{output_dir.resolve().as_posix()}/phase15_per_anchor_results.csv) ({len(df_per_anchor)} rows).",
        "",
        "## Production Boundary",
        "- Zero production code, routing, quality gates, Locked LoFTR, RANSAC, or downstream registration modified.",
        "- No automatic winner or production decision applied.",
    ]
    (output_dir / "phase15_global_prior_report.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return df_aggregate, df_per_anchor


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iirs-source", default=None, help="Path to IIRS source image")
    ap.add_argument("--ohrc-reference", default=None, help="Path to OHRC reference image")
    ap.add_argument(
        "--anchor-json",
        default="research/multimodal/phase11_results/phase11_loftr_anchor_pairs.json",
    )
    ap.add_argument(
        "--inspect-anchor",
        action="store_true",
        help="Print the Phase 11 JSON structure and candidate numeric arrays, then exit.",
    )
    args = ap.parse_args()

    if args.inspect_anchor:
        p = Path(args.anchor_json)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        def describe(obj: Any, path_str: str = "$", depth: int = 0) -> None:
            if depth > 3:
                return
            if isinstance(obj, dict):
                print(f"{path_str}: dict keys={list(obj.keys())[:30]}")
                for k, v in obj.items():
                    describe(v, f"{path_str}.{k}", depth + 1)
            elif isinstance(obj, list):
                print(f"{path_str}: list len={len(obj)}")
                try:
                    arr = np.asarray(obj)
                    print(f"  ndarray shape={arr.shape}, dtype={arr.dtype}")
                    if arr.ndim == 2 and arr.shape[1] >= 2:
                        print(f"  first_row={arr[0].tolist() if len(arr) else '[]'}")
                except Exception:
                    pass

        describe(data)
        try:
            loaded_pairs = load_anchor_pairs(p)
            print(f"Successfully loaded {len(loaded_pairs)} anchor pairs from {p}.")
        except Exception as e:
            print(f"Failed to load anchor pairs: {e}")
        return

    if not args.iirs_source or not args.ohrc_reference:
        ap.error("Both --iirs-source and --ohrc-reference are required when not using --inspect-anchor.")

    out = Path("research") / "multimodal" / "phase15_results"
    df_agg, df_anchors = run_phase15(
        args.iirs_source,
        args.ohrc_reference,
        Path(args.anchor_json),
        out,
    )

    print(
        f"Phase 15 complete. aggregate_rows={len(df_agg)} per_anchor_rows={len(df_anchors)} "
        f"angles={df_agg['angle_deg'].nunique()} conditions={df_agg['condition'].nunique()} "
        f"output={out}"
    )
    print(
        "Diagnosis intentionally left for evidence review; "
        "no automatic winner or production decision was applied."
    )


if __name__ == "__main__":
    main()
