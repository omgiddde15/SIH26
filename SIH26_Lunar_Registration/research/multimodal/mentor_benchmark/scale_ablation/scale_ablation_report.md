# Scientific Report: Controlled Matcher-Scale Ablation on Mentor OHRC

**Document Status:** FORMAL CONTROLLED EXPERIMENT REPORT (VALIDITY AUDITED)  
**Execution Date:** September 23, 2026  
**Research Scope:** Controlled Investigation of Pre-LoFTR Resizing Policies  
**Target Datasets:** Authoritative Mentor Chandrayaan-2 Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`)  
**Production Status:** **100% FROZEN** (`adaptive_engine.py`, `registration_core.py`, quality gates, weights locked)  

---

## 1. Core Research Question & Experimental Design

### 1.1 Question Under Investigation
> **"Does the current independent LoFTR resizing policy contribute materially to the mentor OHRC correspondence failure?"**

### 1.2 Motivation & Diagnostic Background
In Track E of the Mentor Failure Diagnostic, it was discovered that `compute_matching_scale((H, W), max_dim=1600, max_budget=1800000)` scales source and reference rasters independently based on their aspect ratios and pixel counts. Because OHRC source images are narrow swaths ($624 \times 4872$) whereas reference images are large rectangular tiles ($5916 \times 4232$), source images were downscaled by $\approx 0.328$ while reference images were downscaled by $\approx 0.268$.
This introduced an **actual $22.5\% - 36.0\%$ relative scale difference ($s_{\text{src}} / s_{\text{ref}} = 1.225 - 1.360$) on the LoFTR matcher canvas**, despite both native rasters possessing a verified nominal $5.0\text{ m/px}$ ground pixel scale.

This experiment was designed to isolate and test this factor in a strictly controlled manner without modifying production.

### 1.3 Pre-Declared Experimental Conditions
Four distinct scaling policies were evaluated deterministically on each of the 4 OHRC pairs:
1. **Condition A (CURRENT_PRODUCTION_SCALE):** Existing production behavior using `compute_matching_scale()` independently.
2. **Condition B (COMMON_CANVAS_SCALE):** Equal pre-LoFTR scaling ($s_{\text{src}} = s_{\text{ref}} = \min(s_{\text{src, prod}}, s_{\text{ref, prod}})$), enforcing an **equalized 1:1 matcher-canvas scale**. *(This experiment tests canvas pixel scale equalization and does NOT perform physical GSD normalization).*
3. **Condition C (COMMON_MAX_DIM):** Both images scaled to identical maximum dimension ($1580\text{ px}$), eliminating independent max-dimension disparity while respecting memory caps. *(Relative scale ratios remained approximately $1.21 - 1.36\times$ due to native aspect ratio differences).*
4. **Condition D (EXPLICIT_RELATIVE_SCALE_MATRIX):** Pre-declared discrete relative scale matrix around 1:1 ($\sigma \in \{0.8, 0.9, 1.0, 1.1, 1.2\}$) anchored to common reference scale.

### 1.4 Strict Controls & Scientific Governance
- **Same Canonical Image Data:** Accessed directly from mentor directory.
- **Same Matcher Weights:** Frozen LoFTR outdoor pretrained model.
- **Same Preprocessing:** Grayscale + CLAHE (clip limit 2.0, tile grid 8x8).
- **Same RANSAC & Downstream Gate:** RANSAC reprojection threshold 3.0 px, candidate gate $\ge 10$, inlier gate $\ge 8$, ratio gate $\ge 20\%$, occupancy gate $\ge 33.3\%$.
- **No Automatic Winner Selection:** Results are recorded verbatim without parameter cherry-picking.
- **Strict Scale Concept Separation:** Strictly maintained distinction between:
  1. *Nominal raster scale* ($5.000\text{ m/px}$ deliverable grid)
  2. *Projected-coordinate span* ($5.12 - 5.51\text{ m/px}$)
  3. *Physical ground sampling scale* (3D topography/ray tracing)
  4. *Matcher-canvas resizing scale* (2D array dimensions entering LoFTR).

### 1.5 Validity Audit: Verification of Single Resize & LoFTR Input Tensors
A code-level and empirical audit was conducted on `run_scale_ablation.py` to confirm that **no double scaling occurred**.
- **Execution Path Audit:** The research code applies a single resizing operation (`cv2.resize(..., interpolation=cv2.INTER_AREA)`) and feeds the resulting tensors (`torch.from_numpy(...)[None, None]`) directly into `matcher({"image0": ..., "image1": ...})`. Neither `run_loftr_matching()` nor `compute_matching_scale()` was called downstream.
- **Empirical Tensor Dimensions (Representative Runs on OHRC_PAIR_01, native $624 \times 4872$ / $5916 \times 4232$):**
  - **Condition A (Production):** Source tensor: $[1, 1, 1600, 205]$ (scale $0.3284$) | Ref tensor: $[1, 1, 1135, 1586]$ (scale $0.2681$) $\implies$ Realized relative scale: **$1.2254$** | Second resize factor: **$1.0$ (None)**.
  - **Condition B (Common Canvas):** Source tensor: $[1, 1, 1306, 167]$ (scale $0.2681$) | Ref tensor: $[1, 1, 1135, 1586]$ (scale $0.2681$) $\implies$ Realized relative scale: **$0.9983$** | Second resize factor: **$1.0$ (None)**.
  - **Condition D (0.8x):** Source tensor: $[1, 1, 1045, 134]$ (scale $0.2145$) | Ref tensor: $[1, 1, 1135, 1586]$ (scale $0.2681$) $\implies$ Realized relative scale: **$0.8010$** | Second resize factor: **$1.0$ (None)**.
  - **Condition D (1.2x):** Source tensor: $[1, 1, 1568, 201]$ (scale $0.3218$) | Ref tensor: $[1, 1, 1135, 1586]$ (scale $0.2681$) $\implies$ Realized relative scale: **$1.2015$** | Second resize factor: **$1.0$ (None)**.
- **Audit Finding:** The reported dimensions are exactly the tensors entering LoFTR. The existing 28-run results are scientifically valid and no rerun is required.

---

## 2. Experimental Results Summary

- **Total Controlled Evaluations:** 28 conditions across 4 OHRC pairs  
- **Successful Registrations Produced:** **0**  
- **Independent Held-Out Validation Status:** **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**  
- **Safe Rejections Intercepted by Frozen Quality Gate:** **28 / 28 (100.0%)**  
- **Maximum Observed Initial Inliers:** **5** (Quality Gate threshold: $\ge 8$)  
- **Maximum Observed Initial Inlier Ratio:** **10.64%** (Quality Gate threshold: $\ge 20.0\%$)  

---

## 3. Comprehensive Per-Case Results Matrix

### 3.1 OHRC_PAIR_01 (OHRC Pair 1)
- **Input Dimensions:** Source: `624x4872 px` | Reference: `5916x4232 px`

| Condition Code | Condition Description | $s_{\text{src}}$ | $s_{\text{ref}}$ | Rel Scale ($s_s/s_r$) | Matcher Canvas Dims | Candidates | Init Inliers | Inlier Ratio | Spatial Sel | Occupancy | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `COND_A_CURRENT_PRODUCTION` | Standard compute_matching_scale() with i... | 0.3284 | 0.2681 | **1.2248** | `205x1600 px` / `1586x1135 px` | 137 | 5 | 3.65% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_B_COMMON_CANVAS_SCALE_1.0` | Equal pre-LoFTR scaling (s_src = s_ref =... | 0.2681 | 0.2681 | **1.0000** | `167x1306 px` / `1586x1135 px` | 109 | 5 | 4.59% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_C_COMMON_MAX_DIM_1580` | Both images scaled to identical max dime... | 0.3243 | 0.2671 | **1.2143** | `202x1580 px` / `1580x1130 px` | 157 | 5 | 3.18% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.8` | Explicit relative scale ratio 0.8x (sour... | 0.2145 | 0.2681 | **0.8000** | `134x1045 px` / `1586x1135 px` | 74 | 5 | 6.76% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.9` | Explicit relative scale ratio 0.9x (sour... | 0.2413 | 0.2681 | **0.9000** | `151x1176 px` / `1586x1135 px` | 86 | 5 | 5.81% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.1` | Explicit relative scale ratio 1.1x (sour... | 0.2949 | 0.2681 | **1.1000** | `184x1437 px` / `1586x1135 px` | 127 | 5 | 3.94% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.2` | Explicit relative scale ratio 1.2x (sour... | 0.3218 | 0.2681 | **1.2000** | `201x1568 px` / `1586x1135 px` | 127 | 5 | 3.94% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |

### 3.2 OHRC_PAIR_02 (OHRC Pair 2)
- **Input Dimensions:** Source: `648x5059 px` | Reference: `2593x6279 px`

| Condition Code | Condition Description | $s_{\text{src}}$ | $s_{\text{ref}}$ | Rel Scale ($s_s/s_r$) | Matcher Canvas Dims | Candidates | Init Inliers | Inlier Ratio | Spatial Sel | Occupancy | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `COND_A_CURRENT_PRODUCTION` | Standard compute_matching_scale() with i... | 0.3163 | 0.2548 | **1.2412** | `205x1600 px` / `661x1600 px` | 221 | 5 | 2.26% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_B_COMMON_CANVAS_SCALE_1.0` | Equal pre-LoFTR scaling (s_src = s_ref =... | 0.2548 | 0.2548 | **1.0000** | `165x1289 px` / `661x1600 px` | 171 | 5 | 2.92% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_C_COMMON_MAX_DIM_1580` | Both images scaled to identical max dime... | 0.3123 | 0.2516 | **1.2412** | `202x1580 px` / `652x1580 px` | 238 | 5 | 2.1% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.8` | Explicit relative scale ratio 0.8x (sour... | 0.2039 | 0.2548 | **0.8000** | `132x1031 px` / `661x1600 px` | 138 | 5 | 3.62% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.9` | Explicit relative scale ratio 0.9x (sour... | 0.2293 | 0.2548 | **0.9000** | `149x1160 px` / `661x1600 px` | 149 | 5 | 3.36% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.1` | Explicit relative scale ratio 1.1x (sour... | 0.2803 | 0.2548 | **1.1000** | `182x1418 px` / `661x1600 px` | 177 | 5 | 2.82% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.2` | Explicit relative scale ratio 1.2x (sour... | 0.3058 | 0.2548 | **1.2000** | `198x1547 px` / `661x1600 px` | 216 | 5 | 2.31% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |

### 3.3 OHRC_PAIR_03 (OHRC Pair 3)
- **Input Dimensions:** Source: `600x5054 px` | Reference: `2416x6316 px`

| Condition Code | Condition Description | $s_{\text{src}}$ | $s_{\text{ref}}$ | Rel Scale ($s_s/s_r$) | Matcher Canvas Dims | Candidates | Init Inliers | Inlier Ratio | Spatial Sel | Occupancy | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `COND_A_CURRENT_PRODUCTION` | Standard compute_matching_scale() with i... | 0.3166 | 0.2533 | **1.2497** | `190x1600 px` / `612x1600 px` | 161 | 5 | 3.11% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_B_COMMON_CANVAS_SCALE_1.0` | Equal pre-LoFTR scaling (s_src = s_ref =... | 0.2533 | 0.2533 | **1.0000** | `152x1280 px` / `612x1600 px` | 109 | 5 | 4.59% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_C_COMMON_MAX_DIM_1580` | Both images scaled to identical max dime... | 0.3126 | 0.2502 | **1.2497** | `188x1580 px` / `604x1580 px` | 161 | 5 | 3.11% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.8` | Explicit relative scale ratio 0.8x (sour... | 0.2027 | 0.2533 | **0.8000** | `122x1024 px` / `612x1600 px` | 87 | 5 | 5.75% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.9` | Explicit relative scale ratio 0.9x (sour... | 0.2280 | 0.2533 | **0.9000** | `137x1152 px` / `612x1600 px` | 104 | 4 | 3.85% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.1` | Explicit relative scale ratio 1.1x (sour... | 0.2787 | 0.2533 | **1.1000** | `167x1408 px` / `612x1600 px` | 129 | 5 | 3.88% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.2` | Explicit relative scale ratio 1.2x (sour... | 0.3040 | 0.2533 | **1.2000** | `182x1536 px` / `612x1600 px` | 142 | 5 | 3.52% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |

### 3.4 OHRC_PAIR_04 (OHRC Pair 4)
- **Input Dimensions:** Source: `552x4649 px` | Reference: `3164x6322 px`

| Condition Code | Condition Description | $s_{\text{src}}$ | $s_{\text{ref}}$ | Rel Scale ($s_s/s_r$) | Matcher Canvas Dims | Candidates | Init Inliers | Inlier Ratio | Spatial Sel | Occupancy | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `COND_A_CURRENT_PRODUCTION` | Standard compute_matching_scale() with i... | 0.3442 | 0.2531 | **1.3599** | `190x1600 px` / `801x1600 px` | 98 | 5 | 5.1% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_B_COMMON_CANVAS_SCALE_1.0` | Equal pre-LoFTR scaling (s_src = s_ref =... | 0.2531 | 0.2531 | **1.0000** | `140x1177 px` / `801x1600 px` | 78 | 5 | 6.41% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_C_COMMON_MAX_DIM_1580` | Both images scaled to identical max dime... | 0.3399 | 0.2499 | **1.3599** | `188x1580 px` / `791x1580 px` | 109 | 5 | 4.59% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.8` | Explicit relative scale ratio 0.8x (sour... | 0.2025 | 0.2531 | **0.8000** | `112x941 px` / `801x1600 px` | 47 | 5 | 10.64% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_0.9` | Explicit relative scale ratio 0.9x (sour... | 0.2278 | 0.2531 | **0.9000** | `126x1059 px` / `801x1600 px` | 60 | 5 | 8.33% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.1` | Explicit relative scale ratio 1.1x (sour... | 0.2784 | 0.2531 | **1.1000** | `154x1294 px` / `801x1600 px` | 80 | 5 | 6.25% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |
| `COND_D_REL_SCALE_1.2` | Explicit relative scale ratio 1.2x (sour... | 0.3037 | 0.2531 | **1.2000** | `168x1412 px` / `801x1600 px` | 74 | 5 | 6.76% | `BYPASSED` | `NOT EVALUATED` | **`SAFE REJECTION`** |

---

## 4. Cross-Case Comparison & Scientific Synthesis

### 4.1 Comparative Response Across Relative Scale Spectrum
The table below compares candidate generation and initial inlier consensus across all 4 OHRC pairs under varying relative canvas scale ratios:

| Dataset | Metric | 0.8x Scale | 0.9x Scale | 1.0x (Common Canvas) | 1.1x Scale | 1.2x Scale | Production Baseline (~1.22-1.36x) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **OHRC_PAIR_01** | Candidates | 74 | 86 | 109 | 127 | 127 | 137 |
| | Init Inliers (Ratio) | 5 (6.76%) | 5 (5.81%) | 5 (4.59%) | 5 (3.94%) | 5 (3.94%) | 5 (3.65%) |
| **OHRC_PAIR_02** | Candidates | 138 | 149 | 171 | 177 | 216 | 221 |
| | Init Inliers (Ratio) | 5 (3.62%) | 5 (3.36%) | 5 (2.92%) | 5 (2.82%) | 5 (2.31%) | 5 (2.26%) |
| **OHRC_PAIR_03** | Candidates | 87 | 104 | 109 | 129 | 142 | 161 |
| | Init Inliers (Ratio) | 5 (5.75%) | 4 (3.85%) | 5 (4.59%) | 5 (3.88%) | 5 (3.52%) | 5 (3.11%) |
| **OHRC_PAIR_04** | Candidates | 47 | 60 | 78 | 80 | 74 | 98 |
| | Init Inliers (Ratio) | 5 (10.64%) | 5 (8.33%) | 5 (6.41%) | 5 (6.25%) | 5 (6.76%) | 5 (5.1%) |

---

## 5. Strict Evidence Classification

In accordance with project scientific governance:
- **Controlled Scale Variations ($0.8\times - 1.2\times$, Common Canvas, Common Max Dim):** **`CONTROLLED EXPERIMENT`**
- **Candidate Counts, Inlier Counts, Ratios, Runtimes:** **`DIRECT IMAGE MEASUREMENT`** / **`MATCHER TELEMETRY`**
- **Quality Gate Pass/Fail Criteria:** **`FROZEN PRODUCTION GATE`**
- **Hypothesis Assessments:** Grounded strictly in empirical ablation data.

---

## 6. What Is Supported by the Evidence

1. **Matcher-Canvas Scale Disparity Is Not Sufficient to Explain Failure:**
   - Eliminating the canvas scale disparity completely (Condition B: `COMMON_CANVAS_SCALE`, $s_{\text{src}} = s_{\text{ref}}$, relative scale $= 1.0000$) did **NOT** recover correspondence.
   - Under Condition B, initial inliers remained between $4$ and $5$, and inlier ratios remained between $2.92\%$ and $6.41\%$, strictly failing the production quality gate ($\ge 8$ inliers, $\ge 20\%$ ratio).
   - Every tested condition across all 4 OHRC pairs was safely intercepted as **`SAFE REJECTION`**.
2. **Observed Scale Response Within Tested Range:**
   - **Within the tested OHRC cases and tested matcher-canvas scale range, varying relative canvas scale did not recover sufficient initial consensus correspondence.**
   - Candidate correspondence density and consensus collapse occur regardless of whether source and reference share equalized canvas scales or differ by $25\% - 36\%$.

---

## 7. What Is Weakened by the Evidence

1. **The Hypothesis that Canvas Scale Disparity is the Primary Cause of Rejection:**
   - The hypothesis that "unequal downscaling in `compute_matching_scale()` accounts for failure on mentor OHRC pairs" is **WEAKENED / NOT SUPPORTED**.
   - Setting relative scale to strictly $1.0000$ fails just as definitively as production baseline ($1.22 - 1.36\times$).

---

## 8. What Remains Inconclusive

1. **True Physical Footprint / Attitude Parallax:**
   - This experiment manipulated the digital 2D resizing scale factors before LoFTR.
   - It does not modify or test the underlying 3D physical ground footprint geometry resulting from spacecraft pitch ($-14.55^\circ$) and roll ($+4.89^\circ$).
2. **Illumination and Shadow Inversion:**
   - High low-intensity shadow fractions ($40.6\% - 69.7\%$) and large apparent shadow angle disparities remain unmanipulated in this test.

---

## 9. Material Relevance of Matcher-Canvas Scale Disparity

> **Conclusion on Matcher-Canvas Scale Disparity:**  
> **Matcher-canvas scale disparity was not sufficient to recover correspondence under the tested conditions. Whether scale interacts with other failure factors remains unresolved.**  
> While unequal resizing is present in the production pipeline, enforcing equalized 1:1 canvas scale does not change the failure status. Therefore, matcher-canvas scale disparity alone does not account for the correspondence collapse.

---

## 10. Need for Further Controlled Experiments

Having shown that 2D matcher canvas scale disparity alone does not account for failure:
1. **Next Controlled Step:** A controlled investigation of **geometric rotation alignment** (compensating for the $-29^\circ$ to $-98^\circ$ flight track trajectory angle) and/or **shadow-masked illumination normalization** is required to isolate the active impediments to correspondence.
2. **Strict Protocol:** As with this ablation, any future experiment must remain research-only and leave production 100% frozen.

---

## 11. Production Safeguards & Governance Verification

- **Production Files Untouched:**
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
- **Independent Held-Out Validation Status:**
  - **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**
- **No Promotion:** Zero research conditions were promoted to production.
