# LunarReg — Canonical Claim Boundaries Document (SIH26166 Final Deliverable)

This document establishes the verified scientific boundary of LunarReg.
Under strict scientific methodology, no claim is made without reproducible evidence.
All capabilities are classified strictly as **DEMONSTRATED**, **PARTIALLY DEMONSTRATED**, or **NOT VERIFIED**.

---

## 1. Requirement-by-Requirement Boundary Classifications

### A. Correspondence between Chandrayaan-2 Optical Images
- **Classification**: **DEMONSTRATED** on available validated optical benchmark pairs.
- **Evidence**: Evaluated across optical benchmarks (`pair_01`, `pair_02`, `pair_03`, `pair_04`) yielding 38 to 4,026 confirmed inlier correspondences under frozen production routing (LoFTR / SIFT).
- **Boundary**: Validated on optical images sharing mutual photographic bandpasses. Cross-sensor multimodal correspondence without orbital telemetry is unverified.

### B. Illumination / Sun-Angle Variation
- **Classification**: **DEMONSTRATED** on tested illumination and shadow variation cases.
- **Evidence**: Validated on `pair_03` (severe solar incidence angle changes and shadowing; 3,340 inliers, held-out RMSE `0.0072 px`, 100% spatial occupancy) and Phase 1 contrast stress benchmarks.
- **Boundary**: Optical matching succeeds when physical crater rims cast shadows across different quadrants; permanently shadowed polar regions (PSRs) with zero photon return cannot produce optical tie points without active/radar sensors.

### C. Viewpoint / Perspective Variation
- **Classification**: **DEMONSTRATED** on tested viewpoint/perspective cases.
- **Evidence**: Validated on `pair_02` (viewpoint distortion; 4,026 inliers, held-out RMSE `0.0045 px`, 100% spatial occupancy) and Phase 18 affine/rotation perturbation benchmarks.
- **Boundary**: 8-DoF planar homography models perspective distortion across locally planar terrain. Extreme off-nadir views across crater walls with severe topographic relief require a Digital Elevation Model (DEM) for non-planar orthorectification.

### D. Uniform Spatial Distribution of Correspondence Points
- **Classification**: **DEMONSTRATED** by the production 3x3 selection policy on successful runs.
- **Evidence**: The production downstream common layer enforces 3x3 spatial grid binning with a cap of `max_per_cell=6` points (maximum 54 points). On nominal optical pairs (`pair_02`, `pair_03`, `pair_04`), it achieves 100% spatial occupancy (9/9 cells) and exactly 6 points per cell ($CV = 0.0000$).
- **Boundary**: Where image pairs exhibit partial geographic overlap (`pair_01`), occupancy is bounded by the physical geometric overlap boundary of the two scenes (8/9 cells, 0.8889 occupancy).

### E. Perspective Image Registration & Downstream Output
- **Classification**: **DEMONSTRATED** through perspective warping and independent validation.
- **Evidence**: Full end-to-end downstream registration (`cv2.warpPerspective`), sub-pixel floating-point coordinate exports, match canvas generation, and 7-page PDF evidence report generation operate deterministically across all successful runs.
- **Boundary**: Registered outputs represent 2D image coordinate alignments. Conversion to lunar latitude/longitude surface coordinates requires camera pointing geometry and SPICE kernels.

### F. Scale Variation
- **Classification**: **PARTIALLY DEMONSTRATED**.
- **Evidence**: Image-space scale sensitivity has been systematically tested (Phase 17 diagnostic across $0.50\times$ to $2.00\times$; optical resolution difference in `pair_01` succeeds with held-out RMSE `1.7188 px`).
- **Boundary**: Physical lunar GSD normalization remains **UNVERIFIED** because mission geometry metadata (spacecraft altitude $H$, focal length $f$, detector pixel pitch $p$) is unavailable for the benchmark crop pair. No arbitrary scale factor (e.g., 40×, 320×, 0.25 m/px, 10 m/px) may be claimed as ground truth without official PDS4 metadata.

### G. Sub-Pixel Accuracy
- **Classification**: **PARTIALLY DEMONSTRATED**.
- **Evidence**: Sub-pixel correspondence localization is mathematically proven under controlled known-transform conditions (Phase 18: mean error `0.4204 px` across 8 affine/rotation conditions; `0.2647–0.3014 px` on pure translations; 100% $\le 0.50\text{ px}$; corner error `0.2583–0.3029 px`).
- **Boundary**: Real Chandrayaan-2 physical sub-pixel accuracy is **NOT VERIFIED** on real uncalibrated lunar imagery due to the complete absence of independent physical ground-truth tie points (surveyed GCPs or sub-milliradian pointing models). Held-out cross-validation RMSE measures internal model consistency, not absolute physical truth.

### H. Multimodal Cross-Sensor Registration (OHRC ↔ IIRS ↔ TMC)
- **Classification**: **PARTIALLY DEMONSTRATED / LIMITED BY AVAILABLE VERIFIED DATA**.
- **Evidence**: The production pipeline safely intercepts uncalibrated cross-sensor crops via its strict quality gate (10 candidates, 8 initial inliers, 20% inlier ratio, 33% spatial occupancy), preventing the output of an invalid hallucinated warp.
- **Boundary**: Universal cross-sensor multimodal registration (OHRC ↔ IIRS, OHRC ↔ TMC, TMC ↔ IIRS) is **NOT CLAIMED**. Calibrated, georeferenced TMC pairs do not exist in the current verified repository data. Uncalibrated IIRS-OHRC crops fail production quality gates.

---

## 2. Summary of Prohibited Claims

To ensure complete scientific and professional integrity before judging:
1. **DO NOT CLAIM**: "LunarReg has proven sub-pixel accuracy on real Chandrayaan-2 orbit imagery."
   - *Truth*: Sub-pixel precision is proven on controlled known transformations; real lunar physical sub-pixel error cannot be measured without physical ground-truth GCPs.
2. **DO NOT CLAIM**: "LunarReg achieves physical lunar GSD scale invariance."
   - *Truth*: Image-space scale tolerance is tested; physical scale normalization requires PDS4 XML labels and orbital geometry.
3. **DO NOT CLAIM**: "LunarReg solves universal multimodal OHRC-to-IIRS or TMC registration."
   - *Truth*: Uncalibrated cross-sensor crops safely fail the production quality gate; TMC calibrated pairs are not present in the verified dataset.
4. **DO NOT CLAIM**: Any algorithm is "best", "winner", "optimal", or "guaranteed".
   - *Truth*: Performance is reported factually via measurable statistical metrics (inliers, ratio, spatial CV, held-out RMSE).
