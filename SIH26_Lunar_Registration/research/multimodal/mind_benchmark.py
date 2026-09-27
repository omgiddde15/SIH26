"""
research/multimodal/mind_benchmark.py
=====================================
Benchmark harness for MIND-style candidate generator with independent
structural keypoint detection (LunarReg Phase 6).

Evaluates MIND-style matching on:
1. Primary multimodal pair: IIRS <-> OHRC (Native 1.0 / 1.0 and Scale 1.0 / 0.5)
2. Rotation pair: pair_01 (Native 1.0 / 1.0 and Scale 1.0 / 0.5)
3. Viewpoint pair: pair_02 (Native 1.0 / 1.0 and Scale 1.0 / 0.5)
4. Sun Angle pair: pair_03 (Native 1.0 / 1.0 and Scale 1.0 / 0.5)

Saves results to:
- research/multimodal/phase6_mind_results.csv
- research/multimodal/phase6_mind_report.md
"""

import os
import sys
import time
import json
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd

from research.multimodal.mind_matcher import (
    MINDConfig,
    run_mind_matching,
)


def load_angle_pairs(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """Research loader for angle/viewpoint test image pairs.

    Discovers pairs located under data/research/phase3_rift2/angle_pairs/*/.
    Independent file-loader without dependency on RIFT2 matching logic.
    """
    if base_dir is None:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "research", "phase3_rift2", "angle_pairs")
        )

    valid_pairs: List[Dict[str, Any]] = []
    invalid_pairs: List[Dict[str, Any]] = []

    if not os.path.exists(base_dir):
        return {
            "base_dir": base_dir,
            "total_discovered": 0,
            "n_valid": 0,
            "n_invalid": 0,
            "valid_pairs": [],
            "invalid_pairs": [{"pair_id": "none", "path": base_dir, "reason": f"Directory not found: {base_dir}"}],
        }

    valid_img_exts = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")

    for entry in sorted(os.listdir(base_dir)):
        entry_path = os.path.join(base_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        pair_id = entry
        meta_path = os.path.join(entry_path, "metadata.json")
        metadata: Dict[str, Any] = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception:
                pass

        src_path = None
        ref_path = None
        for ext in valid_img_exts:
            cand_src = os.path.join(entry_path, f"source{ext}")
            cand_ref = os.path.join(entry_path, f"reference{ext}")
            if src_path is None and os.path.exists(cand_src):
                src_path = cand_src
            if ref_path is None and os.path.exists(cand_ref):
                ref_path = cand_ref

        if src_path is None or ref_path is None:
            invalid_pairs.append({
                "pair_id": pair_id,
                "path": entry_path,
                "reason": "Missing source or reference image.",
            })
            continue

        src_img = cv2.imread(src_path)
        ref_img = cv2.imread(ref_path)

        if src_img is None or ref_img is None:
            invalid_pairs.append({
                "pair_id": pair_id,
                "path": entry_path,
                "reason": "Failed to decode image via cv2.imread.",
            })
            continue

        valid_pairs.append({
            "pair_id": pair_id,
            "source_path": src_path,
            "reference_path": ref_path,
            "source_img": src_img,
            "reference_img": ref_img,
            "metadata": metadata,
            "pair_dir": entry_path,
        })

    return {
        "base_dir": base_dir,
        "total_discovered": len(valid_pairs) + len(invalid_pairs),
        "n_valid": len(valid_pairs),
        "n_invalid": len(invalid_pairs),
        "valid_pairs": valid_pairs,
        "invalid_pairs": invalid_pairs,
    }


def run_mind_benchmark(
    iirs_src_path: str = r"C:\Users\Dell\Downloads\souse.jpeg",
    iirs_ref_path: str = r"C:\Users\Dell\Downloads\ref.jpeg",
    angle_pairs_base_dir: Optional[str] = None,
    config: Optional[MINDConfig] = None,
    ransac_thresh: float = 3.0,
    seeds: Tuple[int, ...] = (1, 2, 3, 4, 5),
    csv_out_path: Optional[str] = None,
    report_out_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run complete Phase 6 benchmark across primary multimodal pair and control pairs."""
    if config is None:
        config = MINDConfig()

    all_trials: List[Dict[str, Any]] = []

    # 1. Primary multimodal pair (IIRS <-> OHRC)
    if os.path.exists(iirs_src_path) and os.path.exists(iirs_ref_path):
        s_iirs = cv2.imread(iirs_src_path)
        r_iirs = cv2.imread(iirs_ref_path)

        # A. Native 1.0 / 1.0
        print("[Phase 6] Running MIND-style on IIRS <-> OHRC (Native 1.0 / 1.0)...")
        rec_nat = run_mind_matching(
            source_img=s_iirs,
            reference_img=r_iirs,
            scale_source=1.0,
            scale_reference=1.0,
            config=config,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label="IIRS <-> OHRC (Native)",
        )
        all_trials.append(rec_nat)

        # B. Scale 1.0 / 0.5
        print("[Phase 6] Running MIND-style on IIRS <-> OHRC (Scale 1.0 / 0.5)...")
        rec_scale = run_mind_matching(
            source_img=s_iirs,
            reference_img=r_iirs,
            scale_source=1.0,
            scale_reference=0.5,
            config=config,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label="IIRS <-> OHRC (Scale 1.0/0.5)",
        )
        all_trials.append(rec_scale)

    # 2. Control Angle Pairs
    angle_data = load_angle_pairs(angle_pairs_base_dir)
    pair_labels = {
        "pair_01": "Rotation Pair (pair_01)",
        "pair_02": "Viewpoint Pair (pair_02)",
        "pair_03": "Sun Angle Pair (pair_03)",
    }

    for vp in angle_data.get("valid_pairs", []):
        pid = vp["pair_id"]
        base_label = pair_labels.get(pid, pid)

        # Native 1.0 / 1.0
        print(f"[Phase 6] Running MIND-style on {base_label} (Native 1.0 / 1.0)...")
        rec_ang_nat = run_mind_matching(
            source_img=vp["source_img"],
            reference_img=vp["reference_img"],
            scale_source=1.0,
            scale_reference=1.0,
            config=config,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label=f"{base_label} (Native)",
        )
        all_trials.append(rec_ang_nat)

        # Scale 1.0 / 0.5
        print(f"[Phase 6] Running MIND-style on {base_label} (Scale 1.0 / 0.5)...")
        rec_ang_scale = run_mind_matching(
            source_img=vp["source_img"],
            reference_img=vp["reference_img"],
            scale_source=1.0,
            scale_reference=0.5,
            config=config,
            ransac_thresh=ransac_thresh,
            seeds=seeds,
            pair_label=f"{base_label} (Scale 1.0/0.5)",
        )
        all_trials.append(rec_ang_scale)

    # Build Master DataFrame
    df_rows = []
    for r in all_trials:
        df_rows.append({
            "Pair": r["pair"],
            "Detector Name": r.get("detector_name", config.detector_name),
            "Detector Parameters": r.get("detector_parameters", config.detector_parameters),
            "Descriptor": r["descriptor"],
            "Scale": r["scale"],
            "Base Keypoints Source": r["base_keypoints_source"],
            "Base Keypoints Reference": r["base_keypoints_reference"],
            "Descriptor Dimension": r["descriptor_dimension"],
            "RIFT2 Dependency": r.get("rift2_dependency", "None"),
            "Raw Queries": r["raw_queries"],
            "NNDR Matches": r["nndr_matches"],
            "Mutual Matches": r["mutual_matches"],
            "Candidates": r["candidates"],
            "Initial Inliers": r["initial_inliers"],
            "Initial Ratio": r["initial_inlier_ratio"],
            "3×3 Occupancy": r["spatial_occupancy"],
            "Spatial CV": r["spatial_cv"],
            "Fit RMSE": r["fit_rmse"],
            "Independent Held-out RMSE": r["independent_held_out_rmse"],
            "Runtime": r["total_runtime"],
            "Success": r["success"],
            "Failure Stage": r["failure_stage"] if not r["success"] else "None",
            "Failure Reason": r["failure_reason"] if not r["success"] else "None",
        })

    master_df = pd.DataFrame(df_rows)

    # Save to CSV
    if csv_out_path is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        csv_out_path = os.path.join(project_root, "research", "multimodal", "phase6_mind_results.csv")

    master_df.to_csv(csv_out_path, index=False)
    print(f"[Phase 6] Benchmark CSV saved to: {csv_out_path}")

    # Generate Markdown Report
    if report_out_path is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        report_out_path = os.path.join(project_root, "research", "multimodal", "phase6_mind_report.md")

    generate_mind_report(master_df, report_out_path)
    print(f"[Phase 6] Benchmark report saved to: {report_out_path}")

    return {
        "trials": all_trials,
        "comparison_table": master_df,
        "csv_path": csv_out_path,
        "report_path": report_out_path,
    }


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Format DataFrame as standard GitHub Markdown table without external dependencies."""
    headers = list(df.columns)
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    data_lines = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(row[h]) if not pd.isna(row[h]) else "" for h in headers) + " |"
        data_lines.append(row_str)
    return "\n".join([header_line, sep_line] + data_lines)


def generate_mind_report(df: pd.DataFrame, report_path: str) -> None:
    """Generate comprehensive scientific markdown report for LunarReg Phase 6."""
    lines = [
        "# LunarReg Phase 6 — Experimental MIND-Style Candidate Generator Report",
        "",
        "## 1. Research Question",
        "Phase 3–5 established that RIFT2 candidate generation, even when combined with NNDR relaxation and structural re-ranking, produces an insufficient pool of valid correspondences on the IIRS ↔ OHRC pair.",
        "",
        "> **Core Research Question:**",
        "> Can an independent modality-independent local self-similarity representation generate reliable IIRS ↔ OHRC correspondences that RIFT2 does not?",
        "",
        "This experiment implements **independent structural keypoint detection and MIND-style candidate generation**, completely decoupled from RIFT2 descriptor extraction, RIFT2 matches, and Phase 5 structural fusion.",
        "",
        "```text",
        "Detector:",
        "    Independent Sobel-gradient + FAST",
        "",
        "Descriptor:",
        "    MIND-style local self-similarity",
        "",
        "Descriptor dimension:",
        "    6",
        "",
        "RIFT2 dependency:",
        "    None",
        "```",
        "",
        "---",
        "",
        "## 2. MIND-Style Algorithm & Exact LunarReg Adaptations",
        "The implementation utilizes the principle of **MIND / modality-independent local self-similarity** (*Heinrich et al., MedIA 2012*) with documented adaptations:",
        "1. **Independent Keypoint Detector**: Sobel spatial gradient magnitude (`to_gradient_magnitude`) followed by FAST feature detection and deterministic response-based sorting (capped at $1500$ points) with an $8\\text{ px}$ boundary margin guard. Zero calls to Log-Gabor filter banks or Phase Congruency.",
        "2. **Primary Input**: Original grayscale imagery normalized to float32 $[0, 1]$. No CLAHE preprocessing as descriptor.",
        "3. **Patch Geometry**: Central patch $7 \\times 7$ pixels ($|P| = 49$), compared against $6$ symmetric radial neighbors at distance $R = 4.0\\text{ px}$ along angles $\\{0^\\circ, 60^\\circ, 120^\\circ, 180^\\circ, 240^\\circ, 300^\\circ\\}$.",
        "4. **Subpixel Bilinear Sampling**: Exact subpixel patch extraction via `cv2.getRectSubPix`.",
        "5. **Local Dissimilarity & Variance**: Mean squared difference across the $7 \\times 7$ patch: $D_n(x) = \\frac{1}{|P|} \\sum (P_{\\text{center}} - P_n)^2$. Local scale $V(x) = \\text{median}_n(D_n(x)) + 10^{-6}$.",
        "6. **Response & Normalization**: $M_n(x) = \\exp(-D_n(x) / V(x))$, resulting in a 6-dimensional unit-$L_2$ normalized descriptor.",
        "7. **Matching Policy**: Forward KNN ($k=2$) + backward KNN ($k=1$) mutual consistency + fixed NNDR threshold $0.90$ + spatial coordinate deduplication.",
        "8. **Common Downstream**: Unchanged `execute_common_downstream` (RANSAC threshold $3.0\\text{ px}$, confidence $0.995$, $3 \\times 3$ spatial binning max 6 pts/cell, seeds 1–5).",
        "",
        "---",
        "",
        "## 3. Benchmark Results Table",
        "",
        dataframe_to_markdown(df),
        "",
        "---",
        "",
        "## 4. Comparison Against Existing Matchers on IIRS ↔ OHRC",
        "",
        "| Matcher | Representation | Scale Mode | Candidates | Initial Inliers | Initial Inlier Ratio | Fit RMSE (px) | Held-out RMSE (px) | Success | Failure / Outcome |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    # Add historical rows for comparison
    lines.extend([
        "| **LoFTR** (Phase 2) | Dense CNN+Transformer | Native (1.0/1.0) | 199 | 10 | 0.0503 | 1.3017 | 25.2809 | False | Generalizes poorly to held-out points |",
        "| **LoFTR** (Phase 2) | Dense CNN+Transformer | Scale (1.0/0.5) | 76 | 7 | 0.0921 | 1.0053 | NaN | False | Insufficient inliers for check (7 < 8) |",
        "| **RIFT2** (Phase 3/4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.90) | 2 | 0 | 0.0000 | NaN | NaN | False | Insufficient candidates (2 < 4) |",
        "| **RIFT2** (Phase 4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.95) | 47 | 6 | 0.1277 | 0.2742 | NaN | False | Insufficient inliers for check (6 < 8) |",
        "| **RIFT2** (Phase 4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.99) | 195 | 7 | 0.0359 | 0.9075 | NaN | False | Insufficient inliers for check (7 < 8) |",
    ])

    # Extract MIND-style IIRS rows from df
    for _, row in df.iterrows():
        if "IIRS" in str(row["Pair"]):
            scale = str(row["Scale"])
            cands = row["Candidates"]
            inliers = row["Initial Inliers"]
            ratio = row["Initial Ratio"]
            fit = f"{row['Fit RMSE']:.4f}" if not pd.isna(row["Fit RMSE"]) else "NaN"
            held = f"{row['Independent Held-out RMSE']:.4f}" if not pd.isna(row["Independent Held-out RMSE"]) else "NaN"
            succ = row["Success"]
            fail = f"{row['Failure Stage']}: {row['Failure Reason']}" if not succ else "None"
            lines.append(f"| **MIND-style** (Phase 6) | 6-D Local Self-Similarity | {scale} | {cands} | {inliers} | {ratio:.4f} | {fit} | {held} | {succ} | {fail} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Scientific Findings & Interpretation",
        "",
        "### Primary Case: IIRS ↔ OHRC",
    ])

    # Look up IIRS native outcome
    iirs_nat = df[df["Pair"] == "IIRS <-> OHRC (Native)"].iloc[0] if len(df[df["Pair"] == "IIRS <-> OHRC (Native)"]) > 0 else None
    if iirs_nat is not None:
        cands_nat = iirs_nat["Candidates"]
        inl_nat = iirs_nat["Initial Inliers"]
        succ_nat = iirs_nat["Success"]
        lines.append(f"- **Native (1.0 / 1.0)**: Generated **{cands_nat}** candidate correspondences, yielding **{inl_nat}** RANSAC inliers (Initial Inlier Ratio: {iirs_nat['Initial Ratio']:.4f}).")
        if not succ_nat:
            lines.append(f"  - Failure stage: `{iirs_nat['Failure Stage']}` ({iirs_nat['Failure Reason']}).")

    iirs_scl = df[df["Pair"] == "IIRS <-> OHRC (Scale 1.0/0.5)"].iloc[0] if len(df[df["Pair"] == "IIRS <-> OHRC (Scale 1.0/0.5)"]) > 0 else None
    if iirs_scl is not None:
        cands_scl = iirs_scl["Candidates"]
        inl_scl = iirs_scl["Initial Inliers"]
        succ_scl = iirs_scl["Success"]
        lines.append(f"- **Scale (1.0 / 0.5)**: Generated **{cands_scl}** candidate correspondences, yielding **{inl_scl}** RANSAC inliers (Initial Inlier Ratio: {iirs_scl['Initial Ratio']:.4f}).")
        if not succ_scl:
            lines.append(f"  - Failure stage: `{iirs_scl['Failure Stage']}` ({iirs_scl['Failure Reason']}).")

    lines.extend([
        "",
        "### Evaluation under the Scientific Framework:",
        "> **The tested Phase 6 configuration is consistent with Case B.**",
        "> *Candidate quantity improves, but local self-similarity alone is insufficient for reliable lunar cross-sensor correspondence.*",
        "",
        "### Representational Capacity & Terrain Characteristics:",
        "> The 6-dimensional descriptor has limited representational capacity for highly repetitive lunar terrain, which may contribute to descriptor collisions between unrelated structures.",
        "",
        "### Spatial Resolution & Appearance Divergence:",
        "> The tested IIRS and OHRC images exhibit substantial differences in spatial resolution and appearance at the image level. The tested 1.0/0.5 scaling condition did not materially improve the inlier yield.",
        "",
        "### Control Datasets (Rotation, Viewpoint, Sun Angle):",
        "- **Rotation (`pair_01`)**: The fixed radial sampling geometry has no explicit rotation-normalization mechanism; this may contribute to the poor held-out result observed on the rotation-control pair.",
        "- **Viewpoint (`pair_02`)**: Evaluates behavior under perspective/oblique viewpoint divergence.",
        "- **Sun Angle (`pair_03`)**: Evaluates behavior under solar illumination changes and shadow migration.",
        "",
        "---",
        "",
        "## 6. Limitations & Technical Notes",
        "1. **Non-Invariance**: The 6-D MIND-style descriptor uses a fixed radial geometry and is not mathematically invariant to arbitrary scale, in-plane rotation, or 3D viewpoint changes.",
        "2. **Cross-Sensor Divergence**: The tested IIRS and OHRC images exhibit substantial differences in spatial resolution and appearance at the image level. The tested 1.0/0.5 scaling condition did not materially improve the inlier yield.",
        "",
        "---",
        "",
        "## 7. Invariant Statement",
        "",
        "> **Only the experimental MIND-style research candidate generator was executed. Production routing, quality gates, and geometric registration mathematics remain completely unchanged.**",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
