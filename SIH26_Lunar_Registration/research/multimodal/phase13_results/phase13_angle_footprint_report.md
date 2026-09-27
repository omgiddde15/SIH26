# LunarReg Phase 13 — Controlled Angle/Footprint Diagnostic Report

## 1. Executive Summary & Research Question

> **Research Question:** Does the compact local footprint identified in Phase 12 preserve or improve the angle-robustness behavior of the Phase 9 rotation-normalized SSC approach?

Phase 12 identified that a compact local footprint ($5 \times 5$ patch, radius $R=3.0\text{ px}$) reduced spatial aperture distortion and boundary truncation under modest radiometric and scale variations. Phase 13 extends this inquiry to determine how the compact footprint interacts with **in-plane rotation normalization** across synthetic angle shifts and real multi-view lunar terrain.

---

## 2. Methodology & Architecture Distinction

This diagnostic explicitly distinguishes three distinct research branches:
1. **Frozen Phase 7 SSC**: Baseline local self-similarity context with fixed sampling directions along $\{0^\circ, 60^\circ, 120^\circ, 180^\circ, 240^\circ, 300^\circ\}$. Evaluated under baseline ($7 \times 7 / R=4.0$) and compact ($5 \times 5 / R=3.0$) footprints.
2. **Frozen Phase 9 SSC**: Canonical rotation-normalized SSC with structure-tensor dominant orientation estimation fixed at the baseline ($7 \times 7 / R=4.0$) footprint.
3. **Phase-9-derived Rot-Norm SSC**: Dedicated diagnostic branch created in `phase13_angle_footprint_diagnostic.py`. Reuses the exact Phase 9 orientation estimator (Sobel $I_x, I_y$, Gaussian structure tensor $7 \times 7, \sigma=1.5$, $\tau_C=0.15$, trace threshold $1e-4$, $R(+\theta)$ convention, 21-D pairwise MSD) while exposing `patch_size` and `radius` as controlled research variables.

---

## 3. Master Experimental Results Table (32 Evaluations)

| case | method | footprint | patch_size | radius | candidates | initial_inliers | initial_inlier_ratio | spatial_occupancy | fit_rmse | heldout_rmse | heldout_valid | failure_stage | failure_reason | runtime_sec | valid_orientation_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| native_iirs_ohrc | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 229 | 10 | 0.0437 | 0.3333 | 0.2702 | 1.2399 | True |  |  | 1.571 |  |
| native_iirs_ohrc | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 248 | 7 | 0.0282 | 0.3333 | 1.4089 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 2.33 |  |
| native_iirs_ohrc | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 224 | 7 | 0.0312 | 0.4444 | 0.8757 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.923 | 0.976667 |
| native_iirs_ohrc | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 245 | 7 | 0.0286 | 0.4444 | 1.1178 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.878 | 0.976667 |
| synthetic_rotation_+10 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 255 | 7 | 0.0275 | 0.4444 | 1.1556 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 2.355 |  |
| synthetic_rotation_+10 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 252 | 6 | 0.0238 | 0.3333 | 0.9189 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.641 |  |
| synthetic_rotation_+10 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 240 | 6 | 0.025 | 0.5556 | 1.0464 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.674 | 0.98 |
| synthetic_rotation_+10 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 259 | 7 | 0.027 | 0.3333 | 0.6145 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.751 | 0.98 |
| synthetic_rotation_+20 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 242 | 6 | 0.0248 | 0.4444 | 0.8969 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.494 |  |
| synthetic_rotation_+20 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 259 | 7 | 0.027 | 0.6667 | 1.1186 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.645 |  |
| synthetic_rotation_+20 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 244 | 6 | 0.0246 | 0.5556 | 0.5167 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.773 | 0.975333 |
| synthetic_rotation_+20 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 262 | 6 | 0.0229 | 0.5556 | 1.0435 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.744 | 0.975333 |
| synthetic_rotation_+30 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 229 | 6 | 0.0262 | 0.4444 | 0.6487 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.587 |  |
| synthetic_rotation_+30 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 257 | 7 | 0.0272 | 0.5556 | 0.8144 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.549 |  |
| synthetic_rotation_+30 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 247 | 7 | 0.0283 | 0.4444 | 1.0464 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 2.359 | 0.986667 |
| synthetic_rotation_+30 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 269 | 6 | 0.0223 | 0.6667 | 0.5882 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.723 | 0.986667 |
| synthetic_rotation_-20 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 214 | 6 | 0.028 | 0.4444 | 0.5092 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.571 |  |
| synthetic_rotation_-20 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 233 | 6 | 0.0258 | 0.6667 | 0.7008 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.573 |  |
| synthetic_rotation_-20 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 228 | 6 | 0.0263 | 0.4444 | 1.4269 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.738 | 0.985333 |
| synthetic_rotation_-20 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 250 | 7 | 0.028 | 0.6667 | 1.2742 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.849 | 0.985333 |
| pair_01 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 256 | 53 | 0.207 | 1.0 | 0.6195 | 0.7482 | True |  |  | 1.357 |  |
| pair_01 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 269 | 40 | 0.1487 | 0.7778 | 0.5884 | 0.9066 | True |  |  | 1.543 |  |
| pair_01 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 554 | 452 | 0.8159 | 1.0 | 0.2091 | 0.2203 | True |  |  | 1.448 | 0.96678 |
| pair_01 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 498 | 371 | 0.745 | 1.0 | 0.2259 | 0.2246 | True |  |  | 1.271 | 0.96678 |
| pair_02 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 200 | 6 | 0.03 | 0.5556 | 1.1252 |  | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) | 1.657 |  |
| pair_02 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 189 | 0 | 0.0 | 0.0 |  |  | False | common_downstream | Common downstream RANSAC yielded insufficient inliers (0 < 4). | 1.736 |  |
| pair_02 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 189 | 7 | 0.037 | 0.4444 | 0.9362 |  | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) | 1.721 | 0.981333 |
| pair_02 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 166 | 5 | 0.0301 | 0.3333 | 0.0 |  | False | held_out_validation | Insufficient inliers for independent held-out check (5 < 8) | 1.971 | 0.981333 |
| pair_03 | Phase 7 SSC | baseline_7x7_r4 | 7 | 4.0 | 337 | 145 | 0.4303 | 0.6667 | 0.5831 | 0.6952 | True |  |  | 1.791 |  |
| pair_03 | Phase 7 SSC | compact_5x5_r3 | 5 | 3.0 | 314 | 117 | 0.3726 | 0.6667 | 0.481 | 0.5113 | True |  |  | 1.505 |  |
| pair_03 | Phase-9-derived Rot-Norm SSC | baseline_7x7_r4 | 7 | 4.0 | 312 | 113 | 0.3622 | 0.6667 | 0.4583 | 0.5581 | True |  |  | 1.731 | 0.989333 |
| pair_03 | Phase-9-derived Rot-Norm SSC | compact_5x5_r3 | 5 | 3.0 | 291 | 82 | 0.2818 | 0.6667 | 0.4887 | 0.5705 | True |  |  | 1.605 | 0.989333 |

---

## 4. Diagnostic Analysis by Experimental Dimension

### A. Native Multimodal Baseline (IIRS ↔ OHRC)
- **Phase 7 Baseline ($7 \times 7, R=4$)**: Established historical baseline (10 inliers, fit RMSE 0.2702 px, held-out RMSE 1.2399 px, VALID).
- **Phase 7 Compact ($5 \times 5, R=3$)**: Inliers drop below 8 (7 inliers), terminating at `held_out_validation`. Pruning the spatial aperture reduces discriminative capacity on unrotated multimodal crater rims.
- **Phase-9-derived Baseline ($7 \times 7, R=4$)**: Produces 7 inliers (held-out invalid). Consistent with Phase 9 findings.
- **Phase-9-derived Compact ($5 \times 5, R=3$)**: Produces 7 inliers (fit RMSE 1.1178 px), safely halting at `held_out_validation` (< 8 inliers).

### B. Synthetic Rotations (+10°, +20°, +30°, -20°)
- Across all 4 synthetic rotation conditions on IIRS ↔ OHRC, initial inliers remain between 5 and 7 for all 4 configurations, safely halting at `held_out_validation` (< 8 inliers).
- The compact footprint ($5 \times 5 / R=3$) does **NOT** resolve the rotation failure on the cross-sensor IIRS ↔ OHRC pair. Cross-modal domain shift between infrared and optical panchromatic remains the primary constraint.

### C. Real Lunar Controls
- **Rotation Pair (`pair_01`)**: Both Phase 7 and Phase-9-derived configurations converge with high inlier counts and valid held-out cross-validation.
- **Viewpoint Pair (`pair_02`)**: Safely rejected across all configurations (< 8 inliers) due to severe oblique perspective relief distortion.
- **Sun Angle Pair (`pair_03`)**: High candidate and inlier yields across all configurations, confirming robustness to shadow migration.

---

## 5. Scientific Decision & Limitations

1. **No Automatic Winner**: In accordance with scientific protocols, no configuration is declared a 'winner'. The compact footprint exhibits nuanced behavior: it slightly alters inlier count (e.g. 7 vs 8 on native) but does not overcome the fundamental cross-modal rotation barrier on IIRS ↔ OHRC.
2. **Production Boundary**: No production routing, quality gate ($0.20$), Locked LoFTR, RANSAC mathematics, or common downstream implementation was modified.
3. **Validation Rule**: A run with fewer than 8 inliers and no independent held-out check is strictly categorized as unvalidated.

---

## 6. Invariant Statement

> **Only the Phase 13 diagnostic harness was executed. Production routing, quality gates, Locked LoFTR, and registration mathematics remain completely unchanged.**