
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
    """Load Phase 11 anchors without regenerating them.

    Supports aligned Nx2 arrays (pts0/pts1 and common aliases), Nx4 arrays,
    lists of [x0,y0,x1,y1], and explicit source/reference pair objects.
    """
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
                    pairs.append((float(a[i,0]), float(a[i,1]), float(b[i,0]), float(b[i,1])))
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
            # Common aligned array encodings.
            aliases = [
                ("pts0", "pts1"),
                ("source_points", "reference_points"),
                ("source_pts", "reference_pts"),
                ("source_points", "target_points"),
                ("source_keypoints", "reference_keypoints"),
                ("mkpts0", "mkpts1"),
                ("points0", "points1"),
            ]
            for k0, k1 in aliases:
                if k0 in obj and k1 in obj:
                    add_aligned(obj[k0], obj[k1])

            # Common single-pair encodings.
            if all(k in obj for k in ("x0","y0","x1","y1")):
                try:
                    vals = [float(obj[k]) for k in ("x0","y0","x1","y1")]
                    if np.all(np.isfinite(vals)):
                        pairs.append(tuple(vals))
                except Exception:
                    pass

            if "source" in obj and "reference" in obj:
                s, r = obj["source"], obj["reference"]
                if isinstance(s, dict) and isinstance(r, dict):
                    if all(k in s for k in ("x","y")) and all(k in r for k in ("x","y")):
                        try:
                            pairs.append((float(s["x"]), float(s["y"]), float(r["x"]), float(r["y"])))
                        except Exception:
                            pass
                elif isinstance(s, (list, tuple)) and isinstance(r, (list, tuple)):
                    if len(s) >= 2 and len(r) >= 2:
                        try:
                            pairs.append((float(s[0]), float(s[1]), float(r[0]), float(r[1])))
                        except Exception:
                            pass

            for k, v in obj.items():
                walk(v, f"{path_str}.{k}")

        elif isinstance(obj, list):
            # Entire list may itself be Nx4.
            add_nx4(obj)
            # Or it may be a list of explicit [x,y,x,y] pairs.
            for item in obj:
                if isinstance(item, (list, tuple)) and len(item) == 4:
                    try:
                        vals = [float(x) for x in item]
                        if np.all(np.isfinite(vals)):
                            pairs.append(tuple(vals))
                    except Exception:
                        pass
                walk(item, f"{path_str}[]")

    walk(data)

    # Deduplicate while preserving discovery order.
    unique: List[Tuple[float, float, float, float]] = []
    seen = set()
    for p in pairs:
        key = tuple(round(float(v), 6) for v in p)
        if key not in seen:
            seen.add(key)
            unique.append(tuple(float(v) for v in p))

    if len(unique) < 8:
        raise RuntimeError(
            f"Could not extract a sufficient set of explicit Phase 11 anchors from {path}. "
            f"Found {len(unique)} usable pairs. Run the artifact-inspection command "
            f"below before changing the scientific experiment."
        )

    # Phase 11 used 12 anchors for this diagnostic.
    return np.asarray(unique[:12], dtype=np.float32)


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
    theta: Optional[float] = None,
    stat: Optional[Dict[str, Any]] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
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

    img_f = gray.astype(np.float32) / 255.0
    base_offsets = np.column_stack([
        RADIUS * np.cos(np.radians([0, 60, 120, 180, 240, 300])),
        RADIUS * np.sin(np.radians([0, 60, 120, 180, 240, 300])),
    ]).astype(np.float32)

    offsets = rotate_ssc_offsets(
        base_offsets,
        theta_val,
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

    return desc, stat_out


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

    # Native baseline orientations and length verification.
    thetas_base, stats_base = estimate_keypoint_orientations(_gray(source), src_base, p9_cfg)
    thetas_ref, stats_ref = estimate_keypoint_orientations(_gray(reference), ref_pts, p9_cfg)

    if len(thetas_base) != len(src_base) or len(stats_base) != len(src_base):
        raise ValueError(
            f"Base orientation length mismatch: points={len(src_base)}, "
            f"thetas={len(thetas_base)}, stats={len(stats_base)}"
        )
    if len(thetas_ref) != len(ref_pts) or len(stats_ref) != len(ref_pts):
        raise ValueError(
            f"Ref orientation length mismatch: points={len(ref_pts)}, "
            f"thetas={len(thetas_ref)}, stats={len(stats_ref)}"
        )

    # Native baseline descriptors at fixed anchors.
    base_p7 = [p7_descriptor(source, tuple(p)) for p in src_base]
    base_p9: List[np.ndarray] = []
    for idx, p in enumerate(src_base):
        d, _ = p9_descriptor(source, tuple(p), p9_cfg, theta=float(thetas_base[idx]), stat=stats_base[idx])
        base_p9.append(d)

    ref_p7 = [p7_descriptor(reference, tuple(p)) for p in ref_pts]
    ref_p9: List[np.ndarray] = []
    for idx, p in enumerate(ref_pts):
        d, _ = p9_descriptor(reference, tuple(p), p9_cfg, theta=float(thetas_ref[idx]), stat=stats_ref[idx])
        ref_p9.append(d)

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

        # Estimate rotated keypoint orientations and verify lengths
        thetas_rot, stats_rot = estimate_keypoint_orientations(_gray(rotated), transformed, p9_cfg)
        if len(thetas_rot) != len(transformed) or len(stats_rot) != len(transformed):
            raise ValueError(
                f"Rotated orientation length mismatch: points={len(transformed)}, "
                f"thetas={len(thetas_rot)}, stats={len(stats_rot)}"
            )

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
                    theta_rot_i = float(thetas_rot[i])
                    st_rot_dict = stats_rot[i]
                    d_rot, st_rot = p9_descriptor(rotated, pt_rot, p9_cfg, theta=theta_rot_i, stat=st_rot_dict)
                    d_base = base_p9[i]
                    d_ref = ref_p9[i]

                    # Base and rotated orientation diagnostics.
                    st_base = stats_base[i]
                    st_base_status = st_base.get("status", "unknown")
                    st_rot_status = st_rot.get("status", "unknown")

                    orientation_total += 1
                    orientation_valid += int(st_rot_status == "valid")
                    if st_base_status == "valid" and st_rot_status == "valid":
                        theta_base_i = float(thetas_base[i])
                        angle_errors.append(
                            axial_angle_error(
                                theta_base_i,
                                theta_rot_i,
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
        _df_to_markdown_table(df),
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
