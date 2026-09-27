"""
LunarReg Phase 12 — Controlled Local-Footprint / Cross-Sensor Representation Diagnostic
Research-only. No production routing or thresholds are changed.

Question:
Does the local image footprint used by the frozen Phase 7 SSC and Phase 9
rotation-normalized SSC representations materially affect native IIRS <-> OHRC
cross-sensor descriptor compatibility?

Design:
- Reuse the exact Phase 11 LoFTR-derived anchors from
  phase11_loftr_anchor_pairs.json. Anchors are NOT ground truth.
- Fixed-anchor track varies only the SSC local footprint using a pre-declared
  4-condition matrix. The Phase 9 structure-tensor orientation estimator stays
  frozen at its Phase 9 settings; only SSC sampling footprint changes.
- No adaptive selection, no tuning, no production modification.
- End-to-end runs are secondary confirmation only; they are not used to select
  a footprint.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np

from research.adaptive_matcher.adaptive_engine import execute_common_downstream
from research.multimodal.ssc_matcher import (
    SSCConfig,
    compute_ssc_descriptors,
    run_ssc_matching,
)
from research.multimodal.ssc_rotation import (
    SSCRotationConfig,
    compute_rotation_normalized_ssc_descriptors,
    run_ssc_rotation_matching,
)


@dataclass(frozen=True)
class FootprintCondition:
    """Pre-declared local SSC sampling footprint."""

    label: str
    patch_size: int
    radius: float


# LOCKED BEFORE EXECUTION. No condition is promoted automatically.
FOOTPRINT_MATRIX: Tuple[FootprintCondition, ...] = (
    FootprintCondition("compact", 5, 3.0),
    FootprintCondition("baseline", 7, 4.0),
    FootprintCondition("medium", 9, 5.0),
    FootprintCondition("broad", 11, 7.0),
)

# Frozen Phase 9 orientation-estimator settings. These are intentionally NOT
# scaled with the footprint so that Phase 12 isolates the descriptor footprint.
PHASE9_TENSOR_WINDOW = 7
PHASE9_TENSOR_SIGMA = 1.5
PHASE9_COHERENCE_THRESHOLD = 0.15
PHASE9_TRACE_THRESHOLD = 1e-4
PHASE9_ORIENTATION_SIGN = 1.0

RANSAC_THRESH = 3.0
SEEDS = (1, 2, 3, 4, 5)
MIN_HELDOUT_INLIERS = 8


def _load_color(path: str) -> np.ndarray:
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise FileNotFoundError(f"Failed to decode image: {path}")
    return image


def _safe_float(value: Any) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _write_json(path: Path, payload: Any) -> None:
    def convert(v: Any) -> Any:
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, dict):
            return {str(k): convert(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [convert(x) for x in v]
        return v

    path.write_text(json.dumps(convert(payload), indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_phase11_anchors(anchor_path: Path) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    if not anchor_path.exists():
        raise FileNotFoundError(
            "Phase 11 anchor file not found. Expected: "
            f"{anchor_path}. Run Phase 11 first; Phase 12 deliberately does not regenerate anchors."
        )

    payload = json.loads(anchor_path.read_text(encoding="utf-8"))
    if payload.get("anchor_is_ground_truth") is not False:
        raise ValueError("Phase 11 anchor metadata must explicitly mark anchors as not ground truth.")
    if payload.get("anchor_source") != "existing LoFTR matcher":
        raise ValueError("Unexpected Phase 11 anchor source; refusing to substitute another source.")

    pts0 = np.asarray(payload.get("source_points", []), dtype=np.float32)
    pts1 = np.asarray(payload.get("reference_points", []), dtype=np.float32)
    if pts0.ndim != 2 or pts1.ndim != 2 or pts0.shape[1:] != (2,) or pts1.shape[1:] != (2,):
        raise ValueError("Phase 11 anchor points must have shape (N, 2).")
    if len(pts0) != len(pts1):
        raise ValueError("Source/reference anchor counts differ.")
    if len(pts0) < MIN_HELDOUT_INLIERS:
        raise ValueError(
            f"Only {len(pts0)} Phase 11 anchors found; Phase 12 requires at least {MIN_HELDOUT_INLIERS}."
        )

    return pts0, pts1, payload


def _footprint_margin(condition: FootprintCondition) -> int:
    # Same boundary-guard logic used by the SSC detector, generalized to the
    # larger research-only descriptor footprints.
    return (condition.patch_size // 2) + int(math.ceil(condition.radius)) + 1


def _validate_anchor_geometry(
    points: np.ndarray,
    shape: Tuple[int, int],
    condition: FootprintCondition,
    side: str,
) -> None:
    h, w = shape
    margin = _footprint_margin(condition)
    if len(points) == 0:
        raise ValueError(f"No {side} anchors available.")
    bad = []
    for idx, (x, y) in enumerate(points):
        if not (margin <= float(x) <= w - 1 - margin and margin <= float(y) <= h - 1 - margin):
            bad.append((idx, float(x), float(y)))
    if bad:
        raise ValueError(
            f"{len(bad)} {side} Phase 11 anchors are outside the safe sampling margin "
            f"for footprint {condition.label} (margin={margin}). No anchors are dropped."
        )


def _make_phase7_config(condition: FootprintCondition) -> SSCConfig:
    return SSCConfig(
        patch_size=condition.patch_size,
        radius=condition.radius,
        margin=_footprint_margin(condition),
    )


def _make_phase9_config(condition: FootprintCondition) -> SSCRotationConfig:
    return SSCRotationConfig(
        ssc=_make_phase7_config(condition),
        tensor_window=PHASE9_TENSOR_WINDOW,
        tensor_sigma=PHASE9_TENSOR_SIGMA,
        coherence_threshold=PHASE9_COHERENCE_THRESHOLD,
        trace_threshold=PHASE9_TRACE_THRESHOLD,
        orientation_sign=PHASE9_ORIENTATION_SIGN,
    )


def _summary(values: np.ndarray) -> Dict[str, float | int | None]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"count": 0, "mean": None, "median": None, "p90": None, "max": None}
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(np.max(arr)),
    }


def _fixed_anchor_condition(
    source_gray: np.ndarray,
    reference_gray: np.ndarray,
    pts0: np.ndarray,
    pts1: np.ndarray,
    condition: FootprintCondition,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    _validate_anchor_geometry(pts0, source_gray.shape[:2], condition, "source")
    _validate_anchor_geometry(pts1, reference_gray.shape[:2], condition, "reference")

    cfg7 = _make_phase7_config(condition)
    cfg9 = _make_phase9_config(condition)

    d7_0 = compute_ssc_descriptors(source_gray, pts0, cfg7)
    d7_1 = compute_ssc_descriptors(reference_gray, pts1, cfg7)
    d9_0, st9_0 = compute_rotation_normalized_ssc_descriptors(source_gray, pts0, cfg9)
    d9_1, st9_1 = compute_rotation_normalized_ssc_descriptors(reference_gray, pts1, cfg9)

    dist7 = np.linalg.norm(d7_0 - d7_1, axis=1)
    dist9 = np.linalg.norm(d9_0 - d9_1, axis=1)
    paired_delta = dist9 - dist7

    orient = list(st9_0) + list(st9_1)
    valid_count = sum(str(s["status"]) == "valid" for s in orient)
    low_count = sum(str(s["status"]) == "low_confidence" for s in orient)
    flat_count = sum(str(s["status"]) == "flat" for s in orient)

    summary = {
        "footprint": condition.label,
        "patch_size": condition.patch_size,
        "radius": condition.radius,
        "margin": _footprint_margin(condition),
        "anchor_pairs": int(len(pts0)),
        "phase7_mean_l2": float(np.mean(dist7)),
        "phase7_median_l2": float(np.median(dist7)),
        "phase7_p90_l2": float(np.percentile(dist7, 90)),
        "phase7_max_l2": float(np.max(dist7)),
        "phase9_mean_l2": float(np.mean(dist9)),
        "phase9_median_l2": float(np.median(dist9)),
        "phase9_p90_l2": float(np.percentile(dist9, 90)),
        "phase9_max_l2": float(np.max(dist9)),
        "phase9_minus_phase7_mean_delta": float(np.mean(paired_delta)),
        "phase9_minus_phase7_median_delta": float(np.median(paired_delta)),
        "phase9_better_anchor_count": int(np.sum(dist9 < dist7)),
        "phase9_equal_anchor_count": int(np.sum(np.isclose(dist9, dist7, atol=1e-7))),
        "phase9_worse_anchor_count": int(np.sum(dist9 > dist7)),
        "phase9_valid_orientation_count": int(valid_count),
        "phase9_low_confidence_orientation_count": int(low_count),
        "phase9_flat_orientation_count": int(flat_count),
        "phase9_orientation_valid_fraction": float(valid_count / max(1, len(orient))),
    }

    per_anchor: List[Dict[str, Any]] = []
    for idx, (a, b, x7, x9, dd) in enumerate(zip(pts0, pts1, dist7, dist9, paired_delta)):
        per_anchor.append(
            {
                "footprint": condition.label,
                "patch_size": condition.patch_size,
                "radius": condition.radius,
                "anchor_index": idx,
                "source_x": float(a[0]),
                "source_y": float(a[1]),
                "reference_x": float(b[0]),
                "reference_y": float(b[1]),
                "phase7_l2": float(x7),
                "phase9_l2": float(x9),
                "phase9_minus_phase7_l2": float(dd),
                "phase9_better": bool(x9 < x7),
            }
        )

    return summary, per_anchor


def _end_to_end_condition(
    source_bgr: np.ndarray,
    reference_bgr: np.ndarray,
    condition: FootprintCondition,
) -> List[Dict[str, Any]]:
    cfg7 = _make_phase7_config(condition)
    cfg9 = _make_phase9_config(condition)

    p7 = run_ssc_matching(
        source_bgr,
        reference_bgr,
        scale_source=1.0,
        scale_reference=1.0,
        config=cfg7,
        ransac_thresh=RANSAC_THRESH,
        seeds=SEEDS,
        pair_label=f"IIRS <-> OHRC | Native | Phase 7 SSC | {condition.label}",
    )
    p9 = run_ssc_rotation_matching(
        source_bgr,
        reference_bgr,
        scale_source=1.0,
        scale_reference=1.0,
        config=cfg9,
        ransac_thresh=RANSAC_THRESH,
        seeds=SEEDS,
        pair_label=f"IIRS <-> OHRC | Native | Phase 9 Rot-Norm SSC | {condition.label}",
    )

    rows = []
    for phase_name, result in (("Phase 7 SSC", p7), ("Phase 9 Rot-Norm SSC", p9)):
        held = result.get("independent_held_out_rmse")
        rows.append(
            {
                "footprint": condition.label,
                "patch_size": condition.patch_size,
                "radius": condition.radius,
                "method": phase_name,
                "candidates": int(result.get("candidates", 0)),
                "initial_inliers": int(result.get("initial_inliers", 0)),
                "initial_inlier_ratio": _safe_float(result.get("initial_inlier_ratio")),
                "spatial_occupancy": _safe_float(result.get("spatial_occupancy")),
                "fit_rmse": _safe_float(result.get("fit_rmse")),
                "heldout_rmse": _safe_float(held),
                "heldout_valid": bool(result.get("success", False)),
                "failure_stage": result.get("failure_stage"),
                "failure_reason": result.get("failure_reason"),
                "runtime_sec": _safe_float(result.get("total_runtime")),
            }
        )
    return rows


def _write_report(
    path: Path,
    anchor_meta: Dict[str, Any],
    summaries: List[Dict[str, Any]],
    end_rows: List[Dict[str, Any]],
) -> None:
    lines: List[str] = []
    lines.append("# LunarReg Phase 12 — Controlled Local-Footprint Diagnostic")
    lines.append("")
    lines.append("## Research question")
    lines.append(
        "Does the local image footprint used by the frozen Phase 7 SSC and Phase 9 "
        "rotation-normalized SSC representations materially affect native IIRS ↔ OHRC "
        "cross-sensor descriptor compatibility?"
    )
    lines.append("")
    lines.append("## Frozen / controlled elements")
    lines.extend([
        "- Exact Phase 11 LoFTR-derived anchor pairs are reused; anchors are not ground truth.",
        "- Phase 7 descriptor formula, 21-D dimension, matching policy, and detector remain unchanged.",
        "- Phase 9 orientation estimator remains at tensor window 7, sigma 1.5, coherence threshold 0.15, trace threshold 1e-4, orientation sign +1.",
        "- RANSAC threshold = 3.0 px; seeds = 1–5; common downstream unchanged.",
        "- No production routing, quality gate, or Locked LoFTR modification.",
        "- No footprint is selected or promoted automatically.",
    ])
    lines.append("")
    lines.append("## Pre-declared footprint matrix")
    lines.append("| Condition | Patch size | Radius |")
    lines.append("|---|---:|---:|")
    for c in FOOTPRINT_MATRIX:
        lines.append(f"| {c.label} | {c.patch_size}×{c.patch_size} | {c.radius:.1f} px |")
    lines.append("")
    lines.append("## Track A — Anchor provenance")
    lines.append(f"- Anchor source: {anchor_meta.get('anchor_source')}")
    lines.append(f"- Anchor is ground truth: {anchor_meta.get('anchor_is_ground_truth')}")
    lines.append(f"- Anchor pairs reused: {anchor_meta.get('anchor_pairs', len(anchor_meta.get('source_points', [])))}")
    lines.append("")
    lines.append("## Track B — Fixed-anchor descriptor footprint sensitivity")
    lines.append(
        "Lower L2 means greater descriptor similarity. The key diagnostic is the paired Phase 9 − Phase 7 distance difference at the same anchors."
    )
    lines.append("")
    lines.append("| Footprint | P7 mean L2 | P9 mean L2 | P9−P7 mean | P9 better / equal / worse | P9 orientation valid |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in summaries:
        lines.append(
            f"| {r['footprint']} | {r['phase7_mean_l2']:.6f} | {r['phase9_mean_l2']:.6f} | "
            f"{r['phase9_minus_phase7_mean_delta']:.6f} | "
            f"{r['phase9_better_anchor_count']} / {r['phase9_equal_anchor_count']} / {r['phase9_worse_anchor_count']} | "
            f"{r['phase9_orientation_valid_fraction']:.4f} |"
        )
    lines.append("")
    lines.append("## Interpretation rules")
    lines.extend([
        "- The fixed-anchor track isolates descriptor-footprint effects because the anchor locations are held constant.",
        "- A consistent reduction in the Phase 9 − Phase 7 descriptor-distance gap across multiple pre-declared footprints would support footprint sensitivity as a contributor.",
        "- Failure to reduce that gap across the matrix would weaken the hypothesis that footprint size alone explains the Phase 11 transfer problem.",
        "- These are descriptive patterns, not an automatic winner-selection rule.",
    ])
    lines.append("")
    lines.append("## Track C — Secondary end-to-end confirmation")
    lines.append(
        "End-to-end runs are shown for context only. They are not used to choose a footprint because detector behavior and downstream registration are also involved."
    )
    lines.append("")
    lines.append("| Footprint | Method | Candidates | Initial inliers | Ratio | Fit RMSE | Held-out RMSE | Valid |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for r in end_rows:
        lines.append(
            f"| {r['footprint']} | {r['method']} | {r['candidates']} | {r['initial_inliers']} | "
            f"{r['initial_inlier_ratio']} | {r['fit_rmse']} | {r['heldout_rmse']} | {r['heldout_valid']} |"
        )
    lines.append("")
    lines.append("## Production boundary")
    lines.append(
        "Phase 12 is research-only. No production router, 20% quality gate, Locked LoFTR baseline, RANSAC mathematics, or common downstream implementation is modified."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_phase12(
    source_path: str,
    reference_path: str,
    anchor_path: str,
    output_dir: str,
    run_end_to_end: bool = True,
) -> Dict[str, Any]:
    source_bgr = _load_color(source_path)
    reference_bgr = _load_color(reference_path)
    source_gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
    reference_gray = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2GRAY)

    pts0, pts1, anchor_meta = _load_phase11_anchors(Path(anchor_path))
    anchor_meta = dict(anchor_meta)
    anchor_meta["anchor_pairs"] = int(len(pts0))

    # Validate every pre-declared condition before generating any result, so no
    # condition silently drops a different anchor subset.
    for condition in FOOTPRINT_MATRIX:
        _validate_anchor_geometry(pts0, source_gray.shape[:2], condition, "source")
        _validate_anchor_geometry(pts1, reference_gray.shape[:2], condition, "reference")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    _write_json(
        out / "phase12_design.json",
        {
            "question": "Does local image footprint affect native IIRS-OHRC cross-sensor descriptor compatibility?",
            "anchor_source": anchor_meta.get("anchor_source"),
            "anchor_is_ground_truth": False,
            "footprint_matrix": [asdict(c) for c in FOOTPRINT_MATRIX],
            "phase9_orientation_settings": {
                "tensor_window": PHASE9_TENSOR_WINDOW,
                "tensor_sigma": PHASE9_TENSOR_SIGMA,
                "coherence_threshold": PHASE9_COHERENCE_THRESHOLD,
                "trace_threshold": PHASE9_TRACE_THRESHOLD,
                "orientation_sign": PHASE9_ORIENTATION_SIGN,
            },
            "ransac_threshold": RANSAC_THRESH,
            "seeds": list(SEEDS),
            "automatic_selection": False,
        },
    )
    _write_json(out / "phase12_anchor_reuse.json", anchor_meta)

    summaries: List[Dict[str, Any]] = []
    per_anchor_rows: List[Dict[str, Any]] = []
    for condition in FOOTPRINT_MATRIX:
        summary, per_anchor = _fixed_anchor_condition(
            source_gray, reference_gray, pts0, pts1, condition
        )
        summaries.append(summary)
        per_anchor_rows.extend(per_anchor)

    _write_csv(out / "phase12_fixed_anchor_footprint_results.csv", summaries)
    _write_csv(out / "phase12_anchor_pair_distances.csv", per_anchor_rows)

    end_rows: List[Dict[str, Any]] = []
    if run_end_to_end:
        for condition in FOOTPRINT_MATRIX:
            end_rows.extend(_end_to_end_condition(source_bgr, reference_bgr, condition))
    _write_csv(out / "phase12_end_to_end_results.csv", end_rows)

    _write_report(out / "phase12_diagnostic_report.md", anchor_meta, summaries, end_rows)

    return {
        "footprints": [asdict(c) for c in FOOTPRINT_MATRIX],
        "anchor_pairs": int(len(pts0)),
        "output_dir": str(out),
        "end_to_end_runs": bool(run_end_to_end),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="LunarReg Phase 12 local-footprint diagnostic")
    parser.add_argument("--iirs-source", required=True)
    parser.add_argument("--ohrc-reference", required=True)
    parser.add_argument(
        "--anchor-file",
        default=None,
        help="Phase 11 anchor JSON. Default: research/multimodal/phase11_results/phase11_loftr_anchor_pairs.json",
    )
    parser.add_argument(
        "--output-dir",
        default="research/multimodal/phase12_results",
    )
    parser.add_argument(
        "--skip-end-to-end",
        action="store_true",
        help="Run fixed-anchor diagnostic only; no secondary end-to-end confirmation.",
    )
    args = parser.parse_args()

    anchor_file = args.anchor_file or str(
        Path("research") / "multimodal" / "phase11_results" / "phase11_loftr_anchor_pairs.json"
    )

    result = run_phase12(
        source_path=args.iirs_source,
        reference_path=args.ohrc_reference,
        anchor_path=anchor_file,
        output_dir=args.output_dir,
        run_end_to_end=not args.skip_end_to_end,
    )
    print(
        f"Phase 12 complete. Anchor pairs={result['anchor_pairs']}; "
        f"footprints={len(result['footprints'])}; output={result['output_dir']}"
    )
    print("Diagnosis is intentionally left for evidence review; no automatic winner or production decision was applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
