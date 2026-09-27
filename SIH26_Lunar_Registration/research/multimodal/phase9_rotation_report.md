# LunarReg Phase 9 — Rotation-Normalized SSC Research Report

## 1. Scope

> Phase 9 tests whether local structure-tensor orientation normalization improves the rotation robustness of the frozen Phase 7 SSC-style descriptor without changing its detector, descriptor dimension, matching policy, or common downstream geometry.

## 2. Frozen Architecture

- Detector: Independent Sobel-gradient + FAST (Phase 7/8 frozen detector)
- Descriptor: SSC-style 2-D adaptation, 21-D
- Matching: forward KNN k=2 + mutual check + NNDR 0.90
- Orientation estimator: Sobel structure tensor, 7×7 Gaussian window, sigma=1.5
- Coherence threshold: 0.15
- Trace threshold: 0.0001
- Orientation convention: R(+theta) in image pixel coordinates
- RANSAC threshold: 3.0 px
- Spatial selection: 3×3, maximum 6 points/cell
- Held-out seeds: 1–5
- Scale normalization: NOT tested in Phase 9
- RIFT2 dependency: None

## 3. Rotation-Sign Sanity Check

- Synthetic rotation: +20°
- Original tensor angle: 29.8144°
- Rotated tensor angle: 9.9278°
- Observed angle change: -19.8866°
- R(+theta) descriptor distance: 0.004569
- R(-theta) descriptor distance: 0.730538
- Selected convention: R(+theta) in image pixel coordinates
- Sanity status: **PASS**

## 4. Benchmark Matrix

| Pair | Candidates | Inliers | Ratio | Fit RMSE (px) | Held-out RMSE (px) | Valid | Failure Stage |
|---|---:|---:|---:|---:|---:|---|---|
| IIRS <-> OHRC | Native | 224 | 7 | 0.0312 | 0.8757 | NaN | NO_VALID_CHECK | held_out_validation|
| IIRS <-> OHRC | Synthetic Rotation +10 deg | 240 | 6 | 0.0250 | 1.0464 | NaN | NO_VALID_CHECK | held_out_validation|
| IIRS <-> OHRC | Synthetic Rotation +20 deg | 244 | 6 | 0.0246 | 0.5167 | NaN | NO_VALID_CHECK | held_out_validation|
| IIRS <-> OHRC | Synthetic Rotation +30 deg | 247 | 7 | 0.0283 | 1.0464 | NaN | NO_VALID_CHECK | held_out_validation|
| IIRS <-> OHRC | Synthetic Rotation -20 deg | 228 | 6 | 0.0263 | 1.4269 | NaN | NO_VALID_CHECK | held_out_validation|
| pair_01 | Real Control | 554 | 452 | 0.8159 | 0.2091 | 0.2203 | VALID | |
| pair_02 | Real Control | 187 | 7 | 0.0374 | 0.9438 | NaN | NO_VALID_CHECK | held_out_validation|
| pair_03 | Real Control | 312 | 113 | 0.3622 | 0.4583 | 0.5581 | VALID | |

## 5. Interpretation Rules

- Native IIRS↔OHRC quality is compared against the frozen Phase 7/8 SSC baseline, not against the best Phase 9 trial.
- Synthetic rotation results test the proposed orientation normalization but do not establish general rotation invariance.
- `VALID` means the existing independent held-out procedure completed; it does not by itself mean the registration is application-accurate.
- Scale robustness is outside Phase 9 scope.

## 6. Production Boundary

> Phase 9 is research-only. Production routing, quality gates, Locked LoFTR, RANSAC, spatial selection, and common downstream registration remain unchanged.

Primary source: `C:\Users\Dell\Downloads\souse.jpeg`
Primary reference: `C:\Users\Dell\Downloads\ref.jpeg`
