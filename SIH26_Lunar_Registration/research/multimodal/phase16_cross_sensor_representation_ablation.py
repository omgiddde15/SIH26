"""LunarReg Phase 16 — Cross-Sensor Representation Ablation for Frozen SSC.

Research-only diagnostic experiment.
Zero production code, routing, quality gates, Locked LoFTR, RANSAC, or downstream
registration are modified.

Research Question:
"After rotation has been controlled, does changing the image representation
reduce the native IIRS↔OHRC cross-sensor descriptor mismatch?"

Conditions tested:
Condition A: Existing baseline grayscale representation used by Phase 7 SSC.
Condition B: Baseline CLAHE representation (clipLimit=2.0, tileGridSize=(8, 8)).
Condition C: Histogram-normalized representation (global histogram equalization).
Condition D: Gradient-magnitude representation (Sobel spatial gradient magnitude).
Condition E: Local-gradient-normalized representation (Sobel magnitude / local std).

All representations reuse the exact deterministic implementations in
`research.multimodal.multimodal_preprocess`.
The SSC descriptor itself is strictly frozen (7x7 patches, R=4.0 px, 21-D, median V).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.multimodal_preprocess import (
    _ensure_uint8_grayscale,
    to_baseline_clahe,
    to_gradient_magnitude,
    to_histogram_normalized,
    to_local_gradient_normalized,
)

PATCH_SIZE = 7
RADIUS = 4.0
DESCRIPTOR_DIM = 21

BASE_OFFSETS = np.column_stack([
    RADIUS * np.cos(np.radians([0, 60, 120, 180, 240, 300])),
    RADIUS * np.sin(np.radians([0, 60, 120, 180, 240, 300])),
]).astype(np.float32)


def load_anchor_pairs(path: Path) -> np.ndarray:
    """Load exact Phase 11 / Phase 14 / Phase 15 diagnostic anchors."""
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
    offsets: np.ndarray = BASE_OFFSETS,
) -> np.ndarray:
    """Extract frozen 21-D SSC descriptor at a single keypoint."""
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


def run_phase16(
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

    margin = PATCH_SIZE / 2.0 + RADIUS + 1.0
    mask_src = in_bounds(src_base, _ensure_uint8_grayscale(source).shape, margin)
    mask_ref = in_bounds(ref_pts, _ensure_uint8_grayscale(reference).shape, margin)
    valid_idx = np.flatnonzero(mask_src & mask_ref)

    if len(valid_idx) < 8:
        raise RuntimeError(f"Fewer than 8 anchors in-bounds: {len(valid_idx)}")

    conditions: List[Tuple[str, str, Callable[[np.ndarray], np.ndarray]]] = [
        (
            "Condition A",
            "Baseline Grayscale (Phase 7)",
            _ensure_uint8_grayscale,
        ),
        (
            "Condition B",
            "Baseline CLAHE",
            to_baseline_clahe,
        ),
        (
            "Condition C",
            "Histogram Normalized",
            to_histogram_normalized,
        ),
        (
            "Condition D",
            "Gradient Magnitude",
            to_gradient_magnitude,
        ),
        (
            "Condition E",
            "Local Gradient Normalized",
            to_local_gradient_normalized,
        ),
    ]

    # Pre-extract baseline Condition A descriptors for source and reference
    gray_src_base = _ensure_uint8_grayscale(source)
    base_src_desc_cond_A = [
        compute_ssc_patch_descriptor(gray_src_base, tuple(src_base[i]))
        for i in valid_idx
    ]
    gray_ref_base = _ensure_uint8_grayscale(reference)
    base_ref_desc_cond_A = [
        compute_ssc_patch_descriptor(gray_ref_base, tuple(ref_pts[i]))
        for i in valid_idx
    ]
    baseline_A_cross_distances = {
        int(valid_idx[k]): float(np.linalg.norm(base_src_desc_cond_A[k] - base_ref_desc_cond_A[k]))
        for k in range(len(valid_idx))
    }

    per_anchor_rows: List[Dict[str, Any]] = []
    aggregate_rows: List[Dict[str, Any]] = []

    for cond_code, cond_label, transform_fn in conditions:
        # 1. Transform both images with the exact condition representation
        img_src_rep = transform_fn(source)
        img_ref_rep = transform_fn(reference)

        cross_sensor_dists: List[float] = []
        delta_vs_baseline_list: List[float] = []
        same_sensor_rep_shifts: List[float] = []

        for k, i in enumerate(valid_idx):
            pt_src = tuple(src_base[i])
            pt_ref = tuple(ref_pts[i])

            d_src = compute_ssc_patch_descriptor(img_src_rep, pt_src)
            d_ref = compute_ssc_patch_descriptor(img_ref_rep, pt_ref)

            cross_dist = float(np.linalg.norm(d_src - d_ref))
            base_dist_A = baseline_A_cross_distances[int(i)]
            delta_vs_base = cross_dist - base_dist_A

            # Diagnostic control: how much does this representation alter the native IIRS descriptor vs baseline grayscale
            d_src_baseline = base_src_desc_cond_A[k]
            same_sensor_rep_shift = float(np.linalg.norm(d_src - d_src_baseline))

            cross_sensor_dists.append(cross_dist)
            delta_vs_baseline_list.append(delta_vs_base)
            same_sensor_rep_shifts.append(same_sensor_rep_shift)

            per_anchor_rows.append({
                "anchor_id": int(i),
                "condition_code": cond_code,
                "representation": cond_label,
                "cross_sensor_distance": cross_dist,
                "baseline_grayscale_distance": base_dist_A,
                "delta_vs_baseline": delta_vs_base,
                "same_sensor_rep_shift_vs_baseline": same_sensor_rep_shift,
            })

        cm = summarize(cross_sensor_dists)
        dm = summarize(delta_vs_baseline_list)
        sm = summarize(same_sensor_rep_shifts)

        aggregate_rows.append({
            "condition_code": cond_code,
            "representation": cond_label,
            "anchor_pairs_total": len(anchors),
            "valid_anchor_count": len(valid_idx),
            "cross_sensor_mean_l2": cm["mean"],
            "cross_sensor_median_l2": cm["median"],
            "cross_sensor_p90_l2": cm["p90"],
            "cross_sensor_max_l2": cm["max"],
            "delta_vs_baseline_mean": dm["mean"],
            "delta_vs_baseline_median": dm["median"],
            "delta_vs_baseline_p90": dm["p90"],
            "same_sensor_rep_shift_mean": sm["mean"],
            "same_sensor_rep_shift_median": sm["median"],
        })

    df_aggregate = pd.DataFrame(aggregate_rows)
    df_per_anchor = pd.DataFrame(per_anchor_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    df_aggregate.to_csv(output_dir / "phase16_aggregate_results.csv", index=False)
    df_per_anchor.to_csv(output_dir / "phase16_per_anchor_results.csv", index=False)

    design = {
        "phase": 16,
        "research_question": "After rotation has been controlled, does changing the image representation reduce the native IIRS↔OHRC cross-sensor descriptor mismatch?",
        "anchor_source": str(anchor_json),
        "anchor_count": int(len(anchors)),
        "patch_size": PATCH_SIZE,
        "radius": RADIUS,
        "descriptor_dim": DESCRIPTOR_DIM,
        "conditions": [
            {"code": "Condition A", "name": "Baseline Grayscale", "source": "Phase 7 standard grayscale"},
            {"code": "Condition B", "name": "Baseline CLAHE", "source": "cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))"},
            {"code": "Condition C", "name": "Histogram Normalized", "source": "cv2.equalizeHist"},
            {"code": "Condition D", "name": "Gradient Magnitude", "source": "Sobel spatial gradient magnitude normalized to [0, 255]"},
            {"code": "Condition E", "name": "Local Gradient Normalized", "source": "Sobel magnitude / local standard deviation (15x15 box)"},
        ],
        "invariants": {
            "ssc_descriptor_frozen": True,
            "rotation_applied": 0.0,
            "anchor_positions_fixed": True,
            "production_modified": False,
            "automatic_winner_selection": False,
        },
    }
    (output_dir / "phase16_design.json").write_text(
        json.dumps(design, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# LunarReg Phase 16 — Cross-Sensor Representation Ablation Report",
        "",
        f"**Anchor pairs used**: {len(anchors)} (reused from Phase 11 / 14 / 15 LoFTR-derived diagnostic anchors)",
        "",
        "## Scientific Purpose & Protocol",
        "This experiment evaluates whether changing the underlying image representation supplied to the frozen Phase 7 SSC descriptor reduces the native IIRS↔OHRC cross-sensor descriptor mismatch.",
        "",
        "### Exact Transformations Used:",
        "- **Condition A (Baseline Grayscale)**: Standard 2D uint8 grayscale representation identical to Phase 7 baseline.",
        "- **Condition B (Baseline CLAHE)**: Contrast Limited Adaptive Histogram Equalization with `clipLimit=2.0, tileGridSize=(8, 8)`.",
        "- **Condition C (Histogram Normalized)**: Global cumulative histogram equalization via `cv2.equalizeHist`.",
        "- **Condition D (Gradient Magnitude)**: Spatial Sobel gradient magnitude normalized to [0, 255].",
        "- **Condition E (Local Gradient Normalized)**: Sobel gradient magnitude normalized by local standard deviation (15×15 window, eps=10.0, 99.9th percentile clip).",
        "",
        "## Aggregate Results (5 Tested Representations)",
        "",
        _df_to_markdown_table(df_aggregate),
        "",
        "## Per-Anchor Results Summary",
        f"Per-anchor results saved to [`phase16_per_anchor_results.csv`](file:///{output_dir.resolve().as_posix()}/phase16_per_anchor_results.csv) ({len(df_per_anchor)} rows).",
        "",
        "## Production Boundary",
        "- Zero production code, routing, quality gates, Locked LoFTR, RANSAC, or downstream registration modified.",
        "- No automatic winner or production decision applied.",
    ]
    (output_dir / "phase16_cross_sensor_representation_report.md").write_text(
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

    out = Path("research") / "multimodal" / "phase16_results"
    df_agg, df_anchors = run_phase16(
        args.iirs_source,
        args.ohrc_reference,
        Path(args.anchor_json),
        out,
    )

    print(
        f"Phase 16 complete. aggregate_rows={len(df_agg)} per_anchor_rows={len(df_anchors)} "
        f"conditions={df_agg['condition_code'].nunique()} output={out}"
    )
    print(
        "Diagnosis intentionally left for evidence review; "
        "no automatic winner or production decision was applied."
    )


if __name__ == "__main__":
    main()
