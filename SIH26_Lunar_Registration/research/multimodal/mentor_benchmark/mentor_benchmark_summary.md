# Mentor Dataset Production Benchmark Summary

**Execution Date:** September 23, 2026  
**Pipeline Mode:** Frozen LunarReg Production Pipeline (Zero Tuning)  
**Total Datasets Evaluated:** 6 (4 Primary OHRC, 2 Secondary Diagnostic IIRS)  

---

## 1. Classification Summary

| Classification | Count | Datasets |
| :--- | :---: | :--- |
| **REGISTERED + VALIDATED** | **0** | None |
| **REGISTERED + VALIDATION LIMITED** | **0** | None |
| **SAFE REJECTION** | **6** | `OHRC_PAIR_01`, `OHRC_PAIR_02`, `OHRC_PAIR_03`, `OHRC_PAIR_04`, `IIRS_PAIR_A`, `IIRS_PAIR_B` |
| **EXECUTION FAILURE** | **0** | None (Zero crashes, zero unhandled exceptions) |
| **NOT RUN** | **0** | None (All 6 cases executed sequentially) |

---

## 2. Matcher Usage & Operational Profile

- **Primary Matcher Selected by Router:** `LoFTR` (6/6 cases)
- **Resource Guard Intervention:**
  - `OHRC_PAIR_01`: Memory-Safe Tiled LoFTR executed (switched from full-image to prevent 3.15 GB CPU allocation).
  - `OHRC_PAIR_02` to `OHRC_PAIR_04`, `IIRS_PAIR_A`, `IIRS_PAIR_B`: Processed via workspace-constrained LoFTR; expensive full-image fallback matchers (SIFT, SuperGlue) were intentionally blocked by resource policy for image dimensions > 4000 px.
- **Runtime Range:** `7.65 s` to `58.86 s` (Mean: `30.61 s`)
- **Held-Out Validation Status:** `UNAVAILABLE` across all 6 cases (Held-out RMSE: `N/A`).

---

## 3. Important Scientific Findings

1. **Effective Scale vs. Correspondence Consensus**:
   - For `OHRC_PAIR_01` to `OHRC_PAIR_04`, effective pixel scale was verified at 1:1 ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$).
   - Despite verified effective scale, initial inlier ratios remained strictly between $1.72\%$ and $5.10\%$, falling far below the frozen $20.0\%$ threshold.
   - **Conclusion:** Verified effective scale alone was insufficient for successful correspondence under the frozen production configuration.

2. **Integrity of Safe Rejection**:
   - **Zero unsupported registrations were produced.**
   - When inlier consensus fell below production safety criteria, the pipeline triggered **`SAFE REJECTION`**, completely suppressing warped image generation and withholding homography matrix estimation.

3. **Potential Contributing Factors**:
   - **For OHRC:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.
   - **For IIRS:** Results are consistent with a cross-sensor representation/modality mismatch, but this benchmark does not isolate causality.

4. **Production Stability**:
   - Zero software defects or runtime crashes occurred across all 6 large-format geospatial GeoTIFFs (up to $7783 \times 960\text{ px}$).

---

## 4. Final Benchmark Conclusion

The frozen production system executed all six mentor-provided datasets without runtime failure. None of the six cases met the production correspondence-quality gate, so no registration was generated for these mentor cases. The system therefore demonstrated safe rejection, but successful mentor-dataset registration has not yet been demonstrated.
