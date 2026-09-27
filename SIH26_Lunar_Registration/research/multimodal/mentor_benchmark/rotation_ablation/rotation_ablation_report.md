# Scientific Report: Controlled Rotation Ablation on Mentor OHRC

**Document Status:** FORMAL CONTROLLED EXPERIMENT REPORT
**Execution Date:** September 23, 2026
**Research Scope:** Controlled In-Plane Geometric Rotation Investigation
**Target Datasets:** Authoritative Mentor Chandrayaan-2 Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`)
**Production Status:** **100% FROZEN** (`adaptive_engine.py`, `registration_core.py`, quality gates, weights locked)

---

## 1. Core Research Question & Experimental Design

### 1.1 Question Under Investigation
> **"Does geometric in-plane rotation of the mentor OHRC source imagery materially affect LoFTR correspondence recovery?"**

### 1.2 Motivation & Diagnostic Background
In Track F and Track A of the Mentor Failure Diagnostic, it was established that the source OHRC strips were acquired along specific spacecraft ground tracks:
- `OHRC_PAIR_01`: Flight azimuth $-29.16^\circ$
- `OHRC_PAIR_02`: Flight azimuth $-98.43^\circ$
- `OHRC_PAIR_03`: Flight azimuth $-96.81^\circ$
- `OHRC_PAIR_04`: Flight azimuth $-105.68^\circ$

Because reference rasters are projected north-up or orbital-aligned, substantial relative in-plane rotation may exist between moving source strips and fixed reference frames. LoFTR features (convolutional and transformer positional embeddings) are known to exhibit degraded correspondence under large in-plane rotations ($> 20^\circ - 30^\circ$).

### 1.3 Pre-Declared Experimental Conditions (11 Conditions per Pair)
To strictly isolate geometric rotation without introducing confounding resizing or algorithm changes:
1. **Canvas Scale Fixed:** Every condition uses the **exact production matcher-canvas scaling** baseline (`compute_matching_scale()`).
2. **Rotation Timing:** Rotation occurs **AFTER** production-scale images are prepared and **BEFORE** the LoFTR forward pass.
3. **Interpolation & Bounds:** Rotation uses `cv2.INTER_LINEAR` with an expanded canvas bounding box (`cv2.BORDER_CONSTANT` = 0) so **zero valid source pixels are cropped**.
4. **Validity Masking:** A strict nearest-neighbor validity mask rejects all candidate keypoints falling within padded black borders.
5. **Inverse Mapping:** Detected keypoints are mapped back to the unrotated matcher canvas via $M^{-1}$, then unscaled to native image coordinates.
6. **Pre-Declared Angle Set per Pair (11 Conditions):**
   - Baseline: $0^\circ$ (unrotated)
   - Standard Grid: $\pm 15^\circ, \pm 30^\circ, \pm 60^\circ, \pm 90^\circ$
   - Metadata Flight Track Azimuth: $+\theta_{\text{meta}}$ and $-\theta_{\text{meta}}$ (empirical sign testing)

---

## 2. Experimental Results Summary

- **Total Controlled Evaluations:** 44 conditions across 4 OHRC pairs
- **Successful Registrations Produced:** **0**
- **Conditions Passing Production Quality Gate:** **0 / 44**
- **Safe Rejections Intercepted by Frozen Quality Gate:** **44 / 44 (100.0%)**
- **Maximum Observed Initial Inliers:** **7** (Quality Gate threshold: $\ge 8$)
- **Maximum Observed Initial Inlier Ratio:** **5.47%** (Quality Gate threshold: $\ge 20.0\%$)
- **Independent Held-Out Validation Status:** **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**

---

## 3. Comprehensive Per-Case Results Matrix

### 3.1 OHRC_PAIR_01 (OHRC Pair 1)
- **Native Dimensions:** Source: `624x4872 px` | Reference: `5916x4232 px`
- **Flight Azimuth / $\theta_{\text{meta}}$:** `-29.16^\circ` $\implies \pm 29.16^\circ$

| Condition Code | Angle | Category | Pre-Rot Dims | Post-Rot Dims | Valid Px % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ROT_000_DEG` | +0.00° | Baseline / No Rotation | `205x1600 px` | `205x1600 px` | 100.0% | 137 | 137 | 5 | 3.65% | **`SAFE REJECTION`** |
| `ROT_P15_DEG` | +15.00° | Discrete Grid +15 deg | `205x1600 px` | `612x1599 px` | 33.52% | 171 | 166 | 5 | 3.01% | **`SAFE REJECTION`** |
| `ROT_M15_DEG` | -15.00° | Discrete Grid -15 deg | `205x1600 px` | `612x1599 px` | 33.52% | 134 | 133 | 5 | 3.76% | **`SAFE REJECTION`** |
| `ROT_P30_DEG` | +30.00° | Discrete Grid +30 deg | `205x1600 px` | `978x1488 px` | 22.54% | 137 | 135 | 5 | 3.7% | **`SAFE REJECTION`** |
| `ROT_M30_DEG` | -30.00° | Discrete Grid -30 deg | `205x1600 px` | `978x1488 px` | 22.54% | 132 | 132 | 5 | 3.79% | **`SAFE REJECTION`** |
| `ROT_P60_DEG` | +60.00° | Discrete Grid +60 deg | `205x1600 px` | `1488x978 px` | 22.54% | 160 | 159 | 5 | 3.14% | **`SAFE REJECTION`** |
| `ROT_M60_DEG` | -60.00° | Discrete Grid -60 deg | `205x1600 px` | `1488x978 px` | 22.54% | 142 | 138 | 5 | 3.62% | **`SAFE REJECTION`** |
| `ROT_P90_DEG` | +90.00° | Discrete Grid +90 deg | `205x1600 px` | `1600x205 px` | 100.0% | 145 | 145 | 6 | 4.14% | **`SAFE REJECTION`** |
| `ROT_M90_DEG` | -90.00° | Discrete Grid -90 deg | `205x1600 px` | `1600x205 px` | 100.0% | 138 | 138 | 5 | 3.62% | **`SAFE REJECTION`** |
| `ROT_P_THETA_META` | +29.16° | Metadata Flight Azimuth (+29.16 deg) | `205x1600 px` | `959x1497 px` | 22.85% | 165 | 164 | 5 | 3.05% | **`SAFE REJECTION`** |
| `ROT_M_THETA_META` | -29.16° | Metadata Flight Azimuth (-29.16 deg) | `205x1600 px` | `959x1497 px` | 22.85% | 111 | 111 | 5 | 4.5% | **`SAFE REJECTION`** |

### 3.2 OHRC_PAIR_02 (OHRC Pair 2)
- **Native Dimensions:** Source: `648x5059 px` | Reference: `2593x6279 px`
- **Flight Azimuth / $\theta_{\text{meta}}$:** `-98.43^\circ` $\implies \pm 98.43^\circ$

| Condition Code | Angle | Category | Pre-Rot Dims | Post-Rot Dims | Valid Px % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ROT_000_DEG` | +0.00° | Baseline / No Rotation | `205x1600 px` | `205x1600 px` | 100.0% | 221 | 221 | 5 | 2.26% | **`SAFE REJECTION`** |
| `ROT_P15_DEG` | +15.00° | Discrete Grid +15 deg | `205x1600 px` | `612x1599 px` | 33.52% | 273 | 270 | 6 | 2.22% | **`SAFE REJECTION`** |
| `ROT_M15_DEG` | -15.00° | Discrete Grid -15 deg | `205x1600 px` | `612x1599 px` | 33.52% | 278 | 275 | 5 | 1.82% | **`SAFE REJECTION`** |
| `ROT_P30_DEG` | +30.00° | Discrete Grid +30 deg | `205x1600 px` | `978x1488 px` | 22.54% | 250 | 249 | 5 | 2.01% | **`SAFE REJECTION`** |
| `ROT_M30_DEG` | -30.00° | Discrete Grid -30 deg | `205x1600 px` | `978x1488 px` | 22.54% | 194 | 194 | 5 | 2.58% | **`SAFE REJECTION`** |
| `ROT_P60_DEG` | +60.00° | Discrete Grid +60 deg | `205x1600 px` | `1488x978 px` | 22.54% | 311 | 311 | 5 | 1.61% | **`SAFE REJECTION`** |
| `ROT_M60_DEG` | -60.00° | Discrete Grid -60 deg | `205x1600 px` | `1488x978 px` | 22.54% | 171 | 167 | 5 | 2.99% | **`SAFE REJECTION`** |
| `ROT_P90_DEG` | +90.00° | Discrete Grid +90 deg | `205x1600 px` | `1600x205 px` | 100.0% | 192 | 192 | 5 | 2.6% | **`SAFE REJECTION`** |
| `ROT_M90_DEG` | -90.00° | Discrete Grid -90 deg | `205x1600 px` | `1600x205 px` | 100.0% | 175 | 175 | 5 | 2.86% | **`SAFE REJECTION`** |
| `ROT_P_THETA_META` | +98.43° | Metadata Flight Azimuth (+98.43 deg) | `205x1600 px` | `1613x437 px` | 46.53% | 227 | 224 | 5 | 2.23% | **`SAFE REJECTION`** |
| `ROT_M_THETA_META` | -98.43° | Metadata Flight Azimuth (-98.43 deg) | `205x1600 px` | `1613x437 px` | 46.53% | 202 | 202 | 7 | 3.47% | **`SAFE REJECTION`** |

### 3.3 OHRC_PAIR_03 (OHRC Pair 3)
- **Native Dimensions:** Source: `600x5054 px` | Reference: `2416x6316 px`
- **Flight Azimuth / $\theta_{\text{meta}}$:** `-96.81^\circ` $\implies \pm 96.81^\circ$

| Condition Code | Angle | Category | Pre-Rot Dims | Post-Rot Dims | Valid Px % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ROT_000_DEG` | +0.00° | Baseline / No Rotation | `190x1600 px` | `190x1600 px` | 100.0% | 161 | 161 | 5 | 3.11% | **`SAFE REJECTION`** |
| `ROT_P15_DEG` | +15.00° | Discrete Grid +15 deg | `190x1600 px` | `598x1595 px` | 31.87% | 141 | 140 | 5 | 3.57% | **`SAFE REJECTION`** |
| `ROT_M15_DEG` | -15.00° | Discrete Grid -15 deg | `190x1600 px` | `598x1595 px` | 31.87% | 159 | 159 | 5 | 3.14% | **`SAFE REJECTION`** |
| `ROT_P30_DEG` | +30.00° | Discrete Grid +30 deg | `190x1600 px` | `965x1481 px` | 21.27% | 154 | 154 | 5 | 3.25% | **`SAFE REJECTION`** |
| `ROT_M30_DEG` | -30.00° | Discrete Grid -30 deg | `190x1600 px` | `965x1481 px` | 21.27% | 145 | 142 | 5 | 3.52% | **`SAFE REJECTION`** |
| `ROT_P60_DEG` | +60.00° | Discrete Grid +60 deg | `190x1600 px` | `1481x965 px` | 21.27% | 185 | 183 | 5 | 2.73% | **`SAFE REJECTION`** |
| `ROT_M60_DEG` | -60.00° | Discrete Grid -60 deg | `190x1600 px` | `1481x965 px` | 21.27% | 130 | 128 | 7 | 5.47% | **`SAFE REJECTION`** |
| `ROT_P90_DEG` | +90.00° | Discrete Grid +90 deg | `190x1600 px` | `1600x190 px` | 99.47% | 174 | 174 | 5 | 2.87% | **`SAFE REJECTION`** |
| `ROT_M90_DEG` | -90.00° | Discrete Grid -90 deg | `190x1600 px` | `1600x190 px` | 99.94% | 141 | 141 | 5 | 3.55% | **`SAFE REJECTION`** |
| `ROT_P_THETA_META` | +96.81° | Metadata Flight Azimuth (+96.81 deg) | `190x1600 px` | `1611x378 px` | 49.92% | 205 | 201 | 5 | 2.49% | **`SAFE REJECTION`** |
| `ROT_M_THETA_META` | -96.81° | Metadata Flight Azimuth (-96.81 deg) | `190x1600 px` | `1611x378 px` | 49.92% | 174 | 173 | 5 | 2.89% | **`SAFE REJECTION`** |

### 3.4 OHRC_PAIR_04 (OHRC Pair 4)
- **Native Dimensions:** Source: `552x4649 px` | Reference: `3164x6322 px`
- **Flight Azimuth / $\theta_{\text{meta}}$:** `-105.68^\circ` $\implies \pm 105.68^\circ$

| Condition Code | Angle | Category | Pre-Rot Dims | Post-Rot Dims | Valid Px % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ROT_000_DEG` | +0.00° | Baseline / No Rotation | `190x1600 px` | `190x1600 px` | 100.0% | 98 | 98 | 5 | 5.1% | **`SAFE REJECTION`** |
| `ROT_P15_DEG` | +15.00° | Discrete Grid +15 deg | `190x1600 px` | `598x1595 px` | 31.87% | 104 | 103 | 5 | 4.85% | **`SAFE REJECTION`** |
| `ROT_M15_DEG` | -15.00° | Discrete Grid -15 deg | `190x1600 px` | `598x1595 px` | 31.87% | 106 | 104 | 5 | 4.81% | **`SAFE REJECTION`** |
| `ROT_P30_DEG` | +30.00° | Discrete Grid +30 deg | `190x1600 px` | `965x1481 px` | 21.27% | 118 | 113 | 6 | 5.31% | **`SAFE REJECTION`** |
| `ROT_M30_DEG` | -30.00° | Discrete Grid -30 deg | `190x1600 px` | `965x1481 px` | 21.27% | 96 | 94 | 5 | 5.32% | **`SAFE REJECTION`** |
| `ROT_P60_DEG` | +60.00° | Discrete Grid +60 deg | `190x1600 px` | `1481x965 px` | 21.27% | 124 | 122 | 5 | 4.1% | **`SAFE REJECTION`** |
| `ROT_M60_DEG` | -60.00° | Discrete Grid -60 deg | `190x1600 px` | `1481x965 px` | 21.27% | 103 | 102 | 5 | 4.9% | **`SAFE REJECTION`** |
| `ROT_P90_DEG` | +90.00° | Discrete Grid +90 deg | `190x1600 px` | `1600x190 px` | 99.47% | 122 | 122 | 5 | 4.1% | **`SAFE REJECTION`** |
| `ROT_M90_DEG` | -90.00° | Discrete Grid -90 deg | `190x1600 px` | `1600x190 px` | 99.94% | 129 | 129 | 3 | 2.33% | **`SAFE REJECTION`** |
| `ROT_P_THETA_META` | +105.68° | Metadata Flight Azimuth (+105.68 deg) | `190x1600 px` | `1592x615 px` | 31.05% | 111 | 108 | 5 | 4.63% | **`SAFE REJECTION`** |
| `ROT_M_THETA_META` | -105.68° | Metadata Flight Azimuth (-105.68 deg) | `190x1600 px` | `1592x615 px` | 31.05% | 128 | 126 | 5 | 3.97% | **`SAFE REJECTION`** |

---

## 4. Addressing the 9 Key Scientific Questions

### 1. Candidate Recovery
**Did rotating the source image increase raw or valid correspondence candidate density?**
- Candidate counts varied across rotation angles as tensor bounding boxes changed shape, but **no tested rotation angle produced a dramatic recovery of correspondence density**.
- Valid candidate matches remained within typical baseline dispersion ranges across all pairs.

### 2. Inlier Recovery
**Did in-plane rotation increase initial consensus inliers ($N_{\text{init\_inliers}}$)?**
- Across all 44 conditions, initial inliers remained strictly between **0 and 7**.
- RANSAC geometric consensus failed to establish any dense inlier consensus cluster at any rotation angle.

### 3. Frozen Quality Gate Traversal
**Did any condition meet the frozen production quality gate?**
- **Zero conditions (0 / 44) passed the frozen production quality gate** ($N_{\text{cand}} \ge 10, N_{\text{inliers}} \ge 8, \text{ratio} \ge 20\%$).
- All 44 conditions were intercepted safely by the frozen production quality gate.

### 4. Independent Held-Out Validation Status
**Did any condition reach independent 5-seed held-out validation?**
- **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**

### 5. Directly Supported Findings
1. **In-plane geometric rotation alone does not resolve the correspondence failure on mentor OHRC pairs.**
2. Rotating the source image across a comprehensive spectrum ($0^\circ, \pm 15^\circ, \pm 30^\circ, \pm 60^\circ, \pm 90^\circ, \pm \theta_{\text{meta}}$) did not lift initial inliers above 7 or inlier ratio above 5.47% (well below the production quality gate thresholds of $\ge 8$ inliers and $\ge 20\%$ ratio).
3. The frozen production quality gate continues to protect the system against generating spurious registrations under arbitrary rotations.
4. **“Within the tested 2D in-plane rotation conditions, rotation compensation did not recover sufficient correspondence. However, rotated canvas geometry, interpolation, and reduced valid-image support are concurrent changes, so pure rotation has not been isolated from those effects.”**

### 6. Inconclusive Findings / Limitations
1. **Out-of-Plane Perspective / 3D Spacecraft Attitude:** This experiment evaluated 2D planar rotation. It did not simulate non-affine 3D perspective distortion induced by spacecraft off-nadir pitch ($-14.55^\circ$) and roll ($+4.89^\circ$).
2. **Confounding by Illumination:** The uncorrected radiometric disparity between source and reference remains an active confounding factor.

### 7. Crop and Padding Artifact Control
- Expanded bounding boxes prevented any cropping of the valid source image.
- A nearest-neighbor validity mask strictly filtered out any keypoints detected in the black padding border.
- Observed border-filtered candidates confirm that border padding did not introduce false inliers.

### 8. Illumination Confounding Interaction
- All 4 OHRC source rasters feature extreme low-sun grazing illumination (solar incidence $84.9^\circ - 90.3^\circ$) with shadow fractions between $40.6\%$ and $69.7\%$, while reference rasters have higher sun angles and lower shadow fractions.
- When shadow geometry and crater rim highlights diverge severely, rotating the canvas does not align the visual gradient signatures because the physical shadow vectors point in disparate directions relative to the topography.

### 9. Next Controlled Research Experiment
- Having isolated and tested both **canvas scale** and **planar rotation**, neither factor alone was sufficient to recover correspondence.
- The remaining unaddressed primary divergence documented in the diagnostic is **extreme low-sun illumination divergence and shadow disparity (Track C & Track F)**.
- A controlled **radiometric / illumination normalization ablation** (e.g. shadow masking, gradient direction standardization) is recommended as the next rigorous step.

---

## 5. Production Safeguards & Governance Verification

- **Production Code Remains 100% Frozen:**
  - `app/adaptive_engine.py`: **UNTOUCHED**
  - `app/registration_core.py`: **UNTOUCHED**
  - `app/app.py`: **UNTOUCHED**
  - `research/adaptive_matcher/adaptive_engine.py`: **UNTOUCHED**
- **Production Thresholds Untouched:**
  - Candidates $\ge 10$: **LOCKED**
  - Initial Inliers $\ge 8$: **LOCKED**
  - Initial Inlier Ratio $\ge 20.0\%$: **LOCKED**
  - Spatial Occupancy $\ge 33.3\%$: **LOCKED**
  - RANSAC Threshold $3.0\text{ px}$: **LOCKED**
  - Validation Seeds $(1, 2, 3, 4, 5)$: **LOCKED**
- **No Promotion to Production:** Research-only exploration.