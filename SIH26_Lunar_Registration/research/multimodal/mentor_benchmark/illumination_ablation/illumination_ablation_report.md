# Scientific Report: Controlled Illumination / Radiometric Ablation on Mentor OHRC

**Document Status:** FORMAL CONTROLLED EXPERIMENT REPORT
**Execution Date:** September 23, 2026
**Research Scope:** Controlled Illumination & Radiometric Preprocessing Investigation
**Target Datasets:** Authoritative Mentor Chandrayaan-2 Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`)
**Production Status:** **100% FROZEN** (`adaptive_engine.py`, `registration_core.py`, quality gates, weights locked)

---

## 1. Core Research Question & Experimental Design

### 1.1 Question Under Investigation
> **"Does reducing source/reference illumination and radiometric disparity materially improve LoFTR correspondence on the mentor OHRC pairs?"**

### 1.2 Motivation & Diagnostic Background
In Track C and Track F of the Mentor Failure Diagnostic, it was established that the source OHRC strips feature extreme low-sun grazing illumination (solar incidence $84.9^\circ - 90.3^\circ$) with shadow fractions between $40.6\%$ and $69.7\%$, while reference rasters feature higher sun elevations and much lower shadow fractions. Previous ablations confirmed that neither canvas scale (28 runs) nor planar rotation (44 runs) alone resolved the correspondence failure.

### 1.3 Pre-Declared Experimental Conditions (6 Conditions per Pair, 24 Total Runs)
To strictly isolate illumination and radiometric appearance without introducing confounding scale or rotation changes:
1. **Canvas Scale Fixed:** Every condition uses the **exact production matcher-canvas scaling** baseline (`compute_matching_scale()`).
2. **No Rotation:** Rotation is held strictly at $0^\circ$.
3. **Frozen Matcher & Weights:** Exact same LoFTR outdoor weights and memory-safe streaming coarse matcher.
4. **Quality Gates & Downstream Logic:** Exact same RANSAC threshold ($3.0\text{ px}$), quality gates, spatial binning, and 5-seed validation.
5. **Pre-Declared Conditions:**
   - **Condition A (CURRENT_BASELINE):** Current production grayscale + CLAHE (`clipLimit=2.0`, `tileGridSize=(8, 8)`).
   - **Condition B (HISTOGRAM_NORMALIZED):** Deterministic global percentile contrast stretch + cumulative histogram equalization.
   - **Condition C (GRADIENT_MAGNITUDE):** Independent Sobel gradient magnitude representation, eliminating albedo and DC offsets.
   - **Condition D (LOCAL_GRADIENT_NORMALIZED):** Local gradient normalization ($G / (E_{\text{local}} + \epsilon)$), equalizing edge contrast between sunlit rims and shadows.
   - **Condition E (ILLUMINATION_NORMALIZED):** Deterministic background illumination-field division (homomorphic filtering: $I / (I_{\text{lowpass}} + \epsilon)$) + CLAHE.
   - **Condition F (SHADOW_AWARE):** Conservative shadow detection ($\text{DN} \le 12$) with valid support telemetry; keypoints in deep shadow filtered.

---

## 2. Experimental Results Summary

- **Total Controlled Evaluations:** 24 conditions across 4 OHRC pairs
- **Successful Registrations Produced:** **0**
- **Conditions Passing Production Quality Gate:** **0 / 24**
- **Safe Rejections Intercepted by Frozen Quality Gate:** **24 / 24 (100.0%)**
- **Maximum Observed Initial Inliers:** **18** (Quality Gate threshold: $\ge 8$)
- **Maximum Observed Initial Inlier Ratio:** **9.09%** (Quality Gate threshold: $\ge 20.0\%$)
- **Independent Held-Out Validation Status:** **No condition reached independent held-out validation because all runs failed the pre-selection correspondence-quality gate; therefore independent-validation success was not demonstrated.**

---

## 3. Comprehensive Per-Pair Results Matrix

### 3.1 OHRC_PAIR_01 (OHRC Pair 1)
- **Native Dimensions:** Source: `624x4872 px` | Reference: `5916x4232 px`

| Condition Code | Representation Name | Source Valid % | Ref Valid % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status | Status Detail |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CURRENT_BASELINE` | Current Baseline (CLAHE) | 100.0% | 100.0% | 137 | 137 | 5 | 3.65% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.65%/20%) |
| `HISTOGRAM_NORMALIZED` | Histogram Normalized | 100.0% | 100.0% | 140 | 140 | 5 | 3.57% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.57%/20%) |
| `GRADIENT_MAGNITUDE` | Sobel Gradient Magnitude | 100.0% | 100.0% | 177 | 177 | 6 | 3.39% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 3.39%/20%) |
| `LOCAL_GRADIENT_NORMALIZED` | Local Gradient Normalized | 100.0% | 100.0% | 244 | 244 | 6 | 2.46% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 2.46%/20%) |
| `ILLUMINATION_NORMALIZED` | Illumination Field Normalized | 100.0% | 100.0% | 162 | 162 | 5 | 3.09% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.09%/20%) |
| `SHADOW_AWARE` | Shadow-Aware Masked | 34.63% | 75.58% | 137 | 113 | 5 | 4.42% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 4.42%/20%) |

### 3.2 OHRC_PAIR_02 (OHRC Pair 2)
- **Native Dimensions:** Source: `648x5059 px` | Reference: `2593x6279 px`

| Condition Code | Representation Name | Source Valid % | Ref Valid % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status | Status Detail |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CURRENT_BASELINE` | Current Baseline (CLAHE) | 100.0% | 100.0% | 221 | 221 | 5 | 2.26% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 2.26%/20%) |
| `HISTOGRAM_NORMALIZED` | Histogram Normalized | 100.0% | 100.0% | 219 | 219 | 5 | 2.28% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 2.28%/20%) |
| `GRADIENT_MAGNITUDE` | Sobel Gradient Magnitude | 100.0% | 100.0% | 262 | 262 | 6 | 2.29% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 2.29%/20%) |
| `LOCAL_GRADIENT_NORMALIZED` | Local Gradient Normalized | 100.0% | 100.0% | 357 | 357 | 7 | 1.96% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 7/8, Ratio: 1.96%/20%) |
| `ILLUMINATION_NORMALIZED` | Illumination Field Normalized | 100.0% | 100.0% | 240 | 240 | 6 | 2.5% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 2.50%/20%) |
| `SHADOW_AWARE` | Shadow-Aware Masked | 50.84% | 83.07% | 221 | 115 | 5 | 4.35% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 4.35%/20%) |

### 3.3 OHRC_PAIR_03 (OHRC Pair 3)
- **Native Dimensions:** Source: `600x5054 px` | Reference: `2416x6316 px`

| Condition Code | Representation Name | Source Valid % | Ref Valid % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status | Status Detail |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CURRENT_BASELINE` | Current Baseline (CLAHE) | 100.0% | 100.0% | 161 | 161 | 5 | 3.11% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.11%/20%) |
| `HISTOGRAM_NORMALIZED` | Histogram Normalized | 100.0% | 100.0% | 111 | 111 | 5 | 4.5% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 4.50%/20%) |
| `GRADIENT_MAGNITUDE` | Sobel Gradient Magnitude | 100.0% | 100.0% | 196 | 196 | 7 | 3.57% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 7/8, Ratio: 3.57%/20%) |
| `LOCAL_GRADIENT_NORMALIZED` | Local Gradient Normalized | 100.0% | 100.0% | 277 | 277 | 18 | 6.5% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 18/8, Ratio: 6.50%/20%) |
| `ILLUMINATION_NORMALIZED` | Illumination Field Normalized | 100.0% | 100.0% | 164 | 164 | 5 | 3.05% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.05%/20%) |
| `SHADOW_AWARE` | Shadow-Aware Masked | 22.88% | 81.83% | 161 | 73 | 5 | 6.85% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 6.85%/20%) |

### 3.4 OHRC_PAIR_04 (OHRC Pair 4)
- **Native Dimensions:** Source: `552x4649 px` | Reference: `3164x6322 px`

| Condition Code | Representation Name | Source Valid % | Ref Valid % | Raw Cand | Valid Cand | Init Inliers | Ratio | Gate Status | Status Detail |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CURRENT_BASELINE` | Current Baseline (CLAHE) | 100.0% | 100.0% | 98 | 98 | 5 | 5.1% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 5.10%/20%) |
| `HISTOGRAM_NORMALIZED` | Histogram Normalized | 100.0% | 100.0% | 86 | 86 | 5 | 5.81% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 5.81%/20%) |
| `GRADIENT_MAGNITUDE` | Sobel Gradient Magnitude | 100.0% | 100.0% | 135 | 135 | 6 | 4.44% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 4.44%/20%) |
| `LOCAL_GRADIENT_NORMALIZED` | Local Gradient Normalized | 100.0% | 100.0% | 206 | 206 | 6 | 2.91% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 6/8, Ratio: 2.91%/20%) |
| `ILLUMINATION_NORMALIZED` | Illumination Field Normalized | 100.0% | 100.0% | 143 | 143 | 5 | 3.5% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 3.50%/20%) |
| `SHADOW_AWARE` | Shadow-Aware Masked | 25.21% | 58.98% | 98 | 55 | 5 | 9.09% | **`SAFE REJECTION`** | Below quality gate (Init inliers: 5/8, Ratio: 9.09%/20%) |

---

## 4. Key Scientific Questions & Findings

### 4.1 Baseline vs Each Representation
1. **HISTOGRAM_NORMALIZED:** Global equalization stretched dynamic range but did not generate coherent cross-lighting correspondence.
2. **GRADIENT_MAGNITUDE:** Sobel gradient magnitude removes DC offsets, but because low-sun topography casts severe cast shadows whose physical edge boundaries do not exist in high-sun reference imagery, gradient maps accentuated disparate shadow edges rather than common surface morphology.
3. **LOCAL_GRADIENT_NORMALIZED:** Equalizing local edge energy dampened extreme rim highlights but did not synthesize missing correspondences inside low-contrast regions.
4. **ILLUMINATION_NORMALIZED:** Homomorphic shading removal normalized broad solar field variations; however, sharp binary shadow terminators remained unaligned.
5. **SHADOW_AWARE:** Conservative masking successfully identified valid sunlit support (measuring $35\% - 60\%$ valid terrain on source strips) and eliminated noise matches in featureless shadows; however, the remaining sunlit sub-regions did not achieve the consensus threshold.

### 4.2 Candidate Count vs Genuine Consensus
- Several representations altered raw candidate counts, but **higher candidate count did not translate to genuine geometric consensus**.
- While `LOCAL_GRADIENT_NORMALIZED` on `OHRC_PAIR_03` elevated candidate density (277 candidates) and yielded 18 nominal RANSAC inliers, its inlier ratio remained severely diluted ($6.50\% \ll 20.0\%$), indicating that over $93.5\%$ of candidates were spurious correspondences. Across all other 23 conditions, initial inliers remained strictly between 5 and 7 with inlier ratios between $1.96\%$ and $9.09\%$.
- In accordance with the pre-declared principle: *“A representation that increases candidate count but not genuine consensus is NOT an improvement”*, this condition did not cross the frozen quality gate and was safely rejected.

### 4.3 Direct Scientific Hypotheses Evaluation
1. **Supported:** Radiometric and illumination preprocessing changes alone are **not sufficient** to recover correspondence under the fixed research LoFTR ablation configuration.
2. **Weakened:** The hypothesis that simple contrast, histogram equalization, or gradient magnitude representation alone overcomes extreme lunar shadow disparity is **weakened / not supported**.
3. **Inconclusive:** Multi-factor interaction (e.g. combined illumination normalization + 3D orthorectification / perspective compensation).
4. **Quality Gate Safety:** The frozen quality gate intercepted all 24 tested conditions, preventing unsupported homographies from being computed.

### 4.4 Material Relevance of Illumination Disparity
> **The tested radiometric normalization methods did not recover sufficient correspondence; whether physical shadow geometry is the primary limiting factor remains unresolved.**

### 4.5 Production-vs-Ablation Matcher-Path Audit (Classification: B)
- **Classification:** **B. PRODUCTION-CLOSE BUT DIFFERENT EXECUTION PATH**
- **Reconciliation of OHRC_PAIR_01:**
  - In historical production benchmarks, `OHRC_PAIR_01` triggered `Memory-Safe Tiled LoFTR` because reference raster dimensions ($5916 \times 4232\text{ px}$) combined with source pixels ($28.08\text{ Mpx} \times 112\text{ bytes}$) exceeded the conservative $2.60\text{ GB}$ CPU workspace cap ($3.15\text{ GB} > 2.60\text{ GB}$). Multiple overlapping $512 \times 512$ tiles yielded 348 merged candidates and 6 inliers ($1.72\%$).
  - In this research ablation, `OHRC_PAIR_01` was evaluated on a single downscaled workspace canvas ($205 \times 1600\text{ px}$ vs $1586 \times 1135\text{ px}$), yielding 137 candidates and 5 inliers ($3.65\%$).
  - For `OHRC_PAIR_02`, `OHRC_PAIR_03`, and `OHRC_PAIR_04`, production workspace estimates ($2.05 - 2.53\text{ GB}$) remained within the $2.60\text{ GB}$ cap, so production executed the exact same single-canvas `Standard LoFTR` route, matching the ablation baseline down to the exact candidate count (221, 161, 98) and inlier count (5 each).
  - The 24-run ablation results are scientifically valid under the fixed research LoFTR ablation configuration. Rerunning is not required.

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