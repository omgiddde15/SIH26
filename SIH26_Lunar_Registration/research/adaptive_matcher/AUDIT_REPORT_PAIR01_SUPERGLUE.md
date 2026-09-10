# AUDIT REPORT: SuperGlue Benchmark Discrepancy on pair_01

**Project**: SIH26166 — Automated Lunar Image Registration
**Date**: September 9, 2026
**Auditor**: Antigravity AI Agent
**Scope**: Investigation of `pair_01` SuperGlue matching result across Phase B (`multi_pair_analyzer.py`), Phase C (`adaptive_engine.py`), and Phase D (`lopo_validator.py`).

---

## 1. Executive Summary

| Item | Phase B (`failure_analysis.csv`) | Initial Phase D LOPO (`lopo_results.csv`) | Verified Ground Truth Audit |
| :--- | :--- | :--- | :--- |
| **Preprocessing** | Raw Grayscale (`cv2.cvtColor`) | CLAHE Enhanced (`preprocess_image`) | Two distinct preprocessing protocols |
| **Keypoints (Src / Ref)** | 83 / 99 | 86 / 120 | CLAHE amplified micro-contrast |
| **Candidate Matches** | **3 matches** ($< 4$) | **16 matches** | CLAHE enabled 13 additional matches |
| **Initial Inliers** | 0 (Aborted at feature matching) | **6 inliers** (indices `[3, 4, 6, 9, 11, 12]`) | Initial RANSAC converged on 6 points |
| **Final Inliers** | 0 | **6 inliers** | Retained after 3×3 grid selection |
| **Spatial Occupancy** | 0.0 (0/9 cells) | **0.2222** (2/9 cells; bottom row only) | Severely degenerated spatial distribution |
| **Estimation Points** | 0 | **0** (split skipped due to $N < 8$) | No estimation points partitioned |
| **Check Points** | 0 | **0** (split skipped due to $N < 8$) | Zero held-out points evaluated |
| **Reported Check RMSE** | `NaN` (Failed) | **0.8662 px** | **Artifact of fallback to Fit RMSE** |
| **Actual Validation Status** | **Failed** (`3 < 4` matches) | **Failed** (0 check points; $6 < 8$ inliers) | **SuperGlue FAILED under both protocols** |

---

## 2. The Core Questions & Findings

### Q1: How was 0.8662 px produced in the LOPO report?
The value `0.8662 px` is the **training Fit RMSE** of a homography computed over 6 clustered inlier points. It was erroneously reported as `Held-out Check RMSE` due to an unhandled fallback expression in `execute_common_downstream`:
```python
# adaptive_engine.py (line 742, prior to audit fix):
mean_chk_rmse = float(np.mean(seed_chk_rmses)) if seed_chk_rmses else fit_rmse
```
Because the number of selected inliers was $6 < 8$, the multi-seed held-out split loop (`if len(selected_ids) < 8: continue`) skipped all iterations for seeds 1–5. Consequently, `seed_chk_rmses` was completely empty (`[]`), causing the code to silently substitute `fit_rmse = 0.866236 px` in place of the missing check error.

### Q2: Why did `failure_analysis.csv` report failure with 3 matches ($<4$)?
In Phase B (`multi_pair_analyzer.py`), SuperGlue was executed on **raw grayscale images without CLAHE**:
```python
# multi_pair_analyzer.py (lines 291-295):
s_gray = cv2.cvtColor(s_img, cv2.COLOR_BGR2GRAY) if len(s_img.shape) == 3 else s_img
r_gray = cv2.cvtColor(r_img, cv2.COLOR_BGR2GRAY) if len(r_img.shape) == 3 else r_img
s_crop = s_gray[:s_h - (s_h % 8), :s_w - (s_w % 8)]
r_crop = r_gray[:r_h - (r_h % 8), :r_w - (r_w % 8)]
```
`pair_01` is an extreme low-contrast lunar scene (contrast standard deviation $\sigma = 14.02$). On raw grayscale, SuperPoint only detected 83 keypoints on the source and 99 on the reference. SuperGlue's Sinkhorn optimal transport produced only **3 mutual matches**. Because $3 < 4$, Phase B aborted immediately at the feature matching stage, recording:
`pair_01,SuperGlue,feature_matching,insufficient matches (3 < 4)`.

### Q3: Why did Phase C & D obtain 16 matches on the same pair?
In Phase C and D (`adaptive_engine.py` and `lopo_validator.py`), all matchers were routed through the unified production preprocessing pipeline `preprocess_image()`, which applies **CLAHE** (Contrast Limited Adaptive Histogram Equalization with clipLimit=2.0, grid=8×8).
CLAHE boosted local gradient energy around subtle lunar crater rims, increasing keypoints to 86 and 120, which allowed SuperGlue to find **16 candidate matches**.

---

## 3. Step-by-Step Forensic Execution Trace (Phase C / D Pipeline)

1. **Image Dimensions**:
   - Source: $146 \times 513$ px $\to$ Cropped to $144 \times 512$ px (divisible by 8).
   - Reference: $194 \times 528$ px $\to$ Cropped to $192 \times 528$ px (divisible by 8).
2. **SuperPoint Keypoint Extraction**:
   - Source Keypoints: 86
   - Reference Keypoints: 120
3. **SuperGlue Feature Matching**:
   - Valid Matches ($m_0 > -1$): **16 correspondences**.
4. **Initial RANSAC (Threshold = 3.0 px)**:
   - Inliers: **6 correspondences** (indices `[3, 4, 6, 9, 11, 12]`).
   - Inlier Ratio: $6 / 16 = 37.5\%$.
   - Reprojection Errors: $[1.28, 1.24, 1.00, 0.20, 0.29, 0.46]$ px.
5. **3×3 Spatial Selection**:
   - Binning across the 9 spatial cells:
     - Cell $(2, 1)$ (bottom-center): 3 inliers
     - Cell $(2, 2)$ (bottom-right): 3 inliers
     - All other 7 cells: **0 inliers**.
   - Spatial Occupancy: $2 / 9 = 0.2222$ (22.2%).
   - Spatial CV: $1.8708$ (extreme clustering).
   - Selected Points: All 6 inliers retained (`len(selected_ids) == 6`).
6. **Final Homography Estimation**:
   - Evaluated on the 6 points: $H_{final}$ converged with all 6 points as inliers.
   - Final Reprojection Errors: $[1.28, 1.24, 1.00, 0.20, 0.29, 0.46]$ px.
   - **Fit RMSE**: $\sqrt{\frac{1}{6} \sum e_i^2} = \mathbf{0.866236\text{ px}}$.
7. **Held-Out Cross-Validation Loop (Seeds 1 to 5)**:
   - To partition points into $\ge 4$ estimation points and $\ge 4$ check points, at least 8 points are required ($4 + 4 = 8$).
   - Code condition:
     ```python
     for seed in seeds:
         if len(selected_ids) < 8:
             continue
     ```
   - For all seeds $1, 2, 3, 4, 5$: `len(selected_ids) == 6 < 8` evaluated to `True`.
   - The loop skipped every seed.
   - `seed_chk_rmses = []`.
   - **Estimation Points evaluated: 0**.
   - **Check Points evaluated: 0**.
8. **The Fallback Assignment**:
   - `mean_chk_rmse = float(np.mean(seed_chk_rmses)) if seed_chk_rmses else fit_rmse`
   - Evaluated to: `0.866236 px` (rounded to `0.8662 px`).

---

## 4. Verification of Audit Checklist

| Audit Point | Finding | Evidence / Citation |
| :--- | :--- | :--- |
| **1. SuperGlue Correspondences** | **3 (raw) / 16 (CLAHE)** | Deterministically reproduced in test harness |
| **2. RANSAC Inliers** | **6 inliers** | Inlier indices `[3, 4, 6, 9, 11, 12]` |
| **3. Estimation Points** | **0** (in held-out eval); 6 (in fit) | No split occurred due to $N < 8$ |
| **4. Check Points** | **0** | Not a single withheld point was tested |
| **5. Whether Fallback was used** | **YES** | Silent fallback to `fit_rmse` in line 742 |
| **6. Cached/Stale Results Reused?** | **NO** | Fresh dynamic inference on every run |
| **7. Evaluation Protocol Changed?** | **YES** | Preprocessing (Raw $\to$ CLAHE) & Check split logic |

---

## 5. Quality Gate Evaluation for SuperGlue on pair_01

The Adaptive Matcher Quality Gate (`evaluate_quality_gate` in `adaptive_engine.py`) defines strict geometric thresholds:
- `min_candidate_matches` = 30 $\to$ SuperGlue had 16 (**FAIL**)
- `min_initial_inliers` = 15 $\to$ SuperGlue had 6 (**FAIL**)
- `min_inlier_ratio` = 0.25 $\to$ SuperGlue had 0.375 (**PASS**)
- `min_spatial_occupancy` = 0.40 $\to$ SuperGlue had 0.2222 (**FAIL**)

SuperGlue **fails 3 out of 4 Quality Gate criteria**. This confirms that SuperGlue's output on `pair_01` is geometrically invalid and untrustworthy for production registration.

---

## 6. Corrective Actions Implemented

1. **Preservation of Historical Evidence**:
   `research/multi_matcher/failure_analysis.csv` remains completely intact and unedited, correctly preserving Phase B's raw grayscale result (`insufficient matches (3 < 4)`).
2. **Fixed Silent Fallback in Engine**:
   In `research/adaptive_matcher/adaptive_engine.py` (`execute_common_downstream`), the fallback to `fit_rmse` was removed. When `seed_chk_rmses` is empty, `mean_check_rmse`, `median_check_rmse`, and `max_check_error` evaluate to `np.nan`, and `held_out_valid` evaluates to `False`.
3. **Corrected Status Reporting in Benchmark Scripts**:
   Both `research/adaptive_matcher/lopo_validator.py` and `research/adaptive_matcher/run_adaptive_benchmark.py` now verify whether `mean_check_rmse` is `NaN`. If held-out validation cannot be performed, status is explicitly recorded as:
   `Failed: insufficient inliers for held-out validation (6 < 8; 0 check points)` with `Success = 0`.
4. **Re-executed LOPO & Benchmark Pipelines**:
   - `lopo_results.csv`: Fold 1 SuperGlue recorded as `Failed`, Check RMSE = empty (`NaN`).
   - `lopo_summary.csv`: Fold 1 Best Accuracy Method correctly updated to **LoFTR** (1.7188 px).
   - `adaptive_results.csv`: Pair 01 SuperGlue recorded as `Failed`.
   - `failure_analysis.csv`: Added `pair_01, SuperGlue, held_out_validation, insufficient inliers (6 < 8; 0 check points)`.
   - Visualizations regenerated to reflect the true failure without fabricated metric bars.
