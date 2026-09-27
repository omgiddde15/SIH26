# LunarReg Production Benchmark on Mentor-Provided Datasets

**Benchmark Status:** `COMPLETED`  
**Pipeline Mode:** `FROZEN PRODUCTION ENGINE`  
**Execution Date:** September 23, 2026  
**Canonical Mentor Data Location:** `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\`  

---

## 1. Executive Summary

This report documents the rigorous evaluation of the **frozen LunarReg production pipeline** on all 6 mentor-provided Chandrayaan-2 datasets.
In accordance with production discipline:
- **Zero algorithmic tuning** or threshold relaxation was performed.
- Quality gate thresholds remained strictly at: Candidates >= 10, Initial Inliers >= 8, Inlier Ratio >= 20%, Spatial Occupancy >= 33%, RANSAC threshold = 3.0 px.
- All 6 cases were evaluated sequentially without parallelization or memory cap overrides.

---

## 2. Benchmark Telemetry & Results Matrix

| Dataset ID | Instrument | Source Dims | Ref Dims | Native GSD | Eff GSD | Ref GSD | Matcher | Resource Mode | Cand | Init Inl | Inl Ratio | Spatial Sel | Spatial Occ | Final Inl | Reproj RMSE | Held-Out RMSE | Runtime | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **OHRC_PAIR_01** | OHRC | 624x4872 | 5916x4232 | 0.26m | 5.0m | 5.0m | LoFTR | Tiled LoFTR | 348 | 6 | 1.72% | BYPASSED | NOT EVALUATED | 0 | N/A | N/A | 58.86s | **`SAFE REJECTION`** |
| **OHRC_PAIR_02** | OHRC | 648x5059 | 2593x6279 | 0.27m | 5.0m | 5.0m | LoFTR | Standard LoFTR | 221 | 5 | 2.26% | BYPASSED | NOT EVALUATED | 0 | N/A | N/A | 30.17s | **`SAFE REJECTION`** |
| **OHRC_PAIR_03** | OHRC | 600x5054 | 2416x6316 | 0.25m | 5.0m | 5.0m | LoFTR | Standard LoFTR | 161 | 5 | 3.11% | BYPASSED | NOT EVALUATED | 0 | N/A | N/A | 24.12s | **`SAFE REJECTION`** |
| **OHRC_PAIR_04** | OHRC | 552x4649 | 3164x6322 | 0.23m | 5.0m | 5.0m | LoFTR | Standard LoFTR | 98 | 5 | 5.10% | BYPASSED | NOT EVALUATED | 0 | N/A | N/A | 30.08s | **`SAFE REJECTION`** |
| **IIRS_PAIR_A** | IIRS | 250x7783 | 960x7681 | 93.74m | 93.74m | NOT VERIFIED | LoFTR | Standard LoFTR | 45 | 5 | 11.11% | BYPASSED | 22.2% | 0 | N/A | N/A | 7.65s | **`SAFE REJECTION`** |
| **IIRS_PAIR_B** | IIRS | 104x4851 | 3175x3874 | 83.14m | 83.14m | NOT VERIFIED | LoFTR | Standard LoFTR | 0 | 0 | 0.00% | BYPASSED | NOT EVALUATED | 0 | N/A | N/A | 32.66s | **`SAFE REJECTION`** |

---

## 3. Metric Separation Principle

To ensure total scientific honesty and prevent misleading compression of metrics, all phases are recorded independently:
1. **Candidate Matches ($N_{cand}$)**: Total raw correspondence pairs output by the selected matcher.
2. **Initial Matcher Inliers ($N_{init\_inliers}$)**: Consensus correspondences surviving preliminary RANSAC filtering ($3.0\text{ px}$).
3. **Spatial Selection**: Whether correspondences were routed to $3 \times 3$ spatial filtering.
4. **Spatial Occupancy**: Fraction of cells occupied (evaluated only when correspondences pass initial gating).
5. **Final Geometric Inliers ($N_{final\_inliers}$)**: Consensus points supporting the final $H_{3 \times 3}$ matrix.
6. **Independent Hold-Out Validation**: Spatially balanced 75/25 split evaluated over seeds 1–5.

---

## 4. Case-by-Case Analysis

### 4.1 Case: OHRC_PAIR_01
- **Instrument:** OHRC (Chandrayaan-2)
- **Source / Reference:** `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_source_at_5m.tif` / `...reference_at_5m.tif`
- **Scale:** Verified 1:1 effective pixel scale: 5.0 m/px source ↔ 5.0 m/px reference
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Memory-Safe Tiled LoFTR, runtime 58.86s)
- **Progression:** 348 candidates -> 6 initial inliers (1.72%) -> Spatial Selection: BYPASSED (Occupancy: NOT EVALUATED) -> 0 final inliers.
- **Diagnostics:** Initial inliers below threshold (6 < 8); Inlier ratio below threshold (1.72% < 20.0%). Large-image fallbacks (SIFT, SuperGlue) were blocked by resource policy (max_dim=5916 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.

### 4.2 Case: OHRC_PAIR_02
- **Instrument:** OHRC (Chandrayaan-2)
- **Source / Reference:** `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif` / `...reference_at_5m.tif`
- **Scale:** Verified 1:1 effective pixel scale: 5.0 m/px source ↔ 5.0 m/px reference
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Standard LoFTR, runtime 30.17s)
- **Progression:** 221 candidates -> 5 initial inliers (2.26%) -> Spatial Selection: BYPASSED (Occupancy: NOT EVALUATED) -> 0 final inliers.
- **Diagnostics:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (2.26% < 20.0%). Fallbacks blocked by resource policy (max_dim=6279 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.

### 4.3 Case: OHRC_PAIR_03
- **Instrument:** OHRC (Chandrayaan-2)
- **Source / Reference:** `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_source_at_5m.tif` / `...reference_at_5m.tif`
- **Scale:** Verified 1:1 effective pixel scale: 5.0 m/px source ↔ 5.0 m/px reference
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Standard LoFTR, runtime 24.12s)
- **Progression:** 161 candidates -> 5 initial inliers (3.11%) -> Spatial Selection: BYPASSED (Occupancy: NOT EVALUATED) -> 0 final inliers.
- **Diagnostics:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (3.11% < 20.0%). Fallbacks blocked by resource policy (max_dim=6316 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.

### 4.4 Case: OHRC_PAIR_04
- **Instrument:** OHRC (Chandrayaan-2)
- **Source / Reference:** `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_source_at_5m.tif` / `...reference_at_5m.tif`
- **Scale:** Verified 1:1 effective pixel scale: 5.0 m/px source ↔ 5.0 m/px reference (Extreme grazing illumination, sun elevation -0.31 deg)
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Standard LoFTR, runtime 30.08s)
- **Progression:** 98 candidates -> 5 initial inliers (5.10%) -> Spatial Selection: BYPASSED (Occupancy: NOT EVALUATED) -> 0 final inliers.
- **Diagnostics:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (5.10% < 20.0%). Fallbacks blocked by resource policy (max_dim=6322 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.

### 4.5 Case: IIRS_PAIR_A
- **Instrument:** IIRS (Chandrayaan-2)
- **Source / Reference:** `IIRXXD18CHO2686502NNNN25244140531312_V2_1_source.tif` / `...reference.tif`
- **Scale:** Source GSD verified (93.74 m/px); reference GSD NOT VERIFIED
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Standard LoFTR, runtime 7.65s)
- **Progression:** 45 candidates -> 5 initial inliers (11.11%) -> Spatial Selection: BYPASSED (Occupancy: 22.2%) -> 0 final inliers.
- **Diagnostics:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (11.11% < 20.0%); Spatial occupancy below threshold (22.22% < 33.33%). Fallbacks blocked by resource policy (max_dim=7783 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with a cross-sensor representation/modality mismatch, but this benchmark does not isolate causality.

### 4.6 Case: IIRS_PAIR_B
- **Instrument:** IIRS (Chandrayaan-2)
- **Source / Reference:** `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01_source.tif` / `...reference.tif`
- **Scale:** Source GSD verified (83.14 m/px); reference GSD NOT VERIFIED
- **Classification:** **`SAFE REJECTION`**
- **Matcher Details:** LoFTR (Standard LoFTR, runtime 32.66s)
- **Progression:** 0 candidates (Matcher returned no candidate correspondences) -> 0 initial inliers (0.0%) -> Spatial Selection: BYPASSED (Occupancy: NOT EVALUATED) -> 0 final inliers.
- **Diagnostics:** Matcher returned no candidate correspondences; initial homography estimation failed (0 inliers). Fallbacks blocked by resource policy (max_dim=4851 > 4000 px).
- **Product:** Warp bypassed; homography matrix withheld; registered image unavailable.
- **Potential Contributing Factors:** Results are consistent with a cross-sensor representation/modality mismatch, but this benchmark does not isolate causality.

---

## 5. Architectural & Scientific Conclusions

1. **Effective Scale vs. Correspondence Consensus**:
   - For `OHRC_PAIR_01` to `OHRC_PAIR_04`, effective pixel scale was verified at 1:1 ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$).
   - Despite verified effective scale, initial inlier ratios remained strictly between $1.72\%$ and $5.10\%$, falling far below the frozen $20.0\%$ threshold.
   - **Conclusion:** Verified effective scale alone was insufficient for successful correspondence under the frozen production configuration.

2. **Safe Rejection Integrity**:
   - **Zero unsupported registrations were produced.**
   - The production Quality Gate ($N_{init} \ge 8$, ratio $\ge 20\%$, occupancy $\ge 33\%$) functioned exactly as designed: it prevented spurious affine/projective warping and refused to output unverified homography matrices.

3. **Resource Policy Enforcement**:
   - Large-image dimensions (4800 to 7700 px) were properly protected by the resource guard, which prevented CPU memory exhaustion while blocking unbounded fallback searches.

4. **Final System Status**:
   The frozen production system executed all six mentor-provided datasets without runtime failure. None of the six cases met the production correspondence-quality gate, so no registration was generated for these mentor cases. The system therefore demonstrated safe rejection, but successful mentor-dataset registration has not yet been demonstrated.
