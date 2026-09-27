# LunarReg — Live Judge Demonstration Script (SIH26166)

This script provides the exact recommended sequence for presenting LunarReg to judges during the SIH 2026 final evaluation.

---

## Pre-Demo Checklist
1. Launch the application:
   ```powershell
   streamlit run app/app.py
   ```
2. Confirm the UI loads at `http://localhost:8501`.
3. Verify that the mode displays: **`Adaptive Production Engine`**.
4. Confirm default production thresholds in the interface:
   - Candidates: `10`
   - Inliers: `8`
   - Inlier Ratio: `20%`
   - Spatial Occupancy: `33%`
   - RANSAC Threshold: `3.0 px`

---

## DEMO 1: Easy / Nominal Optical Registration (Pair 04)

### What Should the Judge See?
- Load **Pair 04** (`Optical Geometric Distortion`).
- Click **"Register Images"**.
- The Adaptive Router characterizes the image: moderate contrast, standard resolution.
- It automatically selects **SIFT** as the primary matcher.
- SIFT yields **3,940 candidate inliers**.
- The 3x3 Spatial Selector extracts **54 evenly distributed correspondences** across all 9 quadrants.
- The warped source image aligns seamlessly with the reference image.

### What Metric Should Be Shown?
- **Final Inliers**: `54` (from 3,940 raw inliers)
- **Spatial Occupancy**: `100.0%` (9/9 cells, exactly 6 points per cell, $CV = 0.0000$)
- **Held-Out Cross-Validation RMSE**: `0.0034 px` (across 5 random seeds)
- **Runtime**: `~1.3 seconds`

### What Should We Say?
> *"On standard Chandrayaan-2 optical imagery with rich surface texture, LunarReg automatically routes to SIFT, achieving extreme sub-pixel geometric consistency (`0.0034 px` held-out RMSE) in under 1.5 seconds. Crucially, notice the tie points: rather than clumping on a single high-contrast crater rim, our 3x3 spatial selection policy enforces perfect uniformity across the entire overlapping field of view."*

### What Should We NOT Claim?
> *Do NOT claim: "This achieves sub-pixel physical accuracy on the lunar surface." (Explain that `0.0034 px` is internal held-out model consistency, which proves high geometric stability).*

---

## DEMO 2: Illumination & Viewpoint Challenge (Pair 02 & Pair 03)

### What Should the Judge See?
- Load **Pair 03** (`Illumination / Sun-Angle Variation`).
- Point out the drastic difference in solar elevation: craters that appear bright on one side are completely dark and inverted in the other image.
- Click **"Register Images"**.
- CLAHE preprocessing normalizes the local dynamic range.
- SIFT extracts **3,340 inliers**.
- The system fits an 8-DoF planar homography that accurately aligns the inverted shadows.

### What Metric Should Be Shown?
- **Initial Inliers**: `3,340` (100% inlier ratio among accepted candidates)
- **Selected Correspondences**: `54`
- **Spatial Occupancy**: `1.0000` (9/9 cells, $CV = 0.0000$)
- **Held-Out RMSE**: `0.0072 px`

### What Should We Say?
> *"Lunar imagery routinely suffers from extreme illumination changes due to differing solar incidence angles between orbital passes. Standard matchers fail when shadows invert. LunarReg pairs local contrast adaptation with gradient orientation descriptors, successfully locking 3,340 correspondences and achieving `0.0072 px` held-out validation across the entire scene."*

### What Should We NOT Claim?
> *Do NOT claim: "LunarReg can match permanently shadowed craters with zero light." (State honestly that optical methods require reflected photons, and radar/active sensors are needed for total darkness).*

---

## DEMO 3: Scale & Resolution Variation (Pair 01)

### What Should the Judge See?
- Load **Pair 01** (`Low Contrast / Scale Variation`).
- Note the differing native dimensions: `146x513 px` vs. `194x528 px`, with faint, low-contrast lunar regolith.
- Click **"Register Images"**.
- The Adaptive Router identifies low contrast (`std < 20.0`) and non-identical native resolutions.
- It automatically routes to **Locked LoFTR** (deep local transformer matching).
- LoFTR extracts **46 dense inliers**.
- 38 points are selected across 8 occupied quadrants.

### What Metric Should Be Shown?
- **Matcher Used**: `LoFTR`
- **Initial Inliers**: `46` (Inlier ratio: `1.0000`)
- **Selected Points**: `38`
- **Spatial Occupancy**: `88.89%` (8 / 9 cells; 1 cell is geographically outside the overlap area)
- **Held-Out RMSE**: `1.7188 px`
- **Runtime**: `~3.6 seconds`

### What Should We Say?
> *"When lunar scenes have low contrast or differing image resolutions, classical hand-crafted descriptors struggle. LunarReg's adaptive router detects this profile and transitions to our locked LoFTR transformer. LoFTR's dense receptive fields capture subtle structural context across scales, successfully registering the pair with a held-out RMSE of `1.72 px`."*

### What Should We NOT Claim?
> *Do NOT claim: "This proves physical Ground Sample Distance (GSD) scale invariance." (Clarify that this demonstrates image-space scale tolerance. Physical GSD normalization requires spacecraft altitude and focal length metadata).*

---

## DEMO 4: Difficult Cross-Sensor Case & Safe Quality-Gate Rejection

### What Should the Judge See?
- Upload or load the uncalibrated cross-sensor crop pair (`souse.jpeg` <-> `ref.jpeg`).
- Click **"Register Images"**.
- Watch the live telemetry in the terminal or UI:
  1. Primary Matcher (LoFTR) runs: produces 199 candidates, 12 inliers.
  2. Quality Gate evaluates LoFTR:
     - Inlier count: 12 >= 8 (PASSED)
     - Inlier ratio: 6.03% < 20.0% (**FAILED**)
  3. Sequential Fallback Router triggers:
     - Attempts SIFT: 4 inliers < 8 (**FAILED**)
     - Attempts SuperGlue: 6 inliers < 8 (**FAILED**)
  4. System terminates gracefully:
     - **Status**: `Failed Quality Gate`
     - **User Notice**: *"All available matchers failed the quality gate. Registration halted safely to prevent invalid warp."*
     - **Crucial**: NO warped output image or hallucinated homography is displayed!

### What Metric Should Be Shown?
- **LoFTR Candidates**: `199`
- **LoFTR Inliers**: `12`
- **LoFTR Inlier Ratio**: `6.03%` (Threshold: `20.0%`)
- **Rejection Reason**: `'Inlier ratio below threshold (0.06 < 0.20)'`
- **Warped Image**: `None` (Zero invalid artifacts)

### What Should We Say?
> *"In mission-critical aerospace operations, a registration system must know when NOT to register. When presented with uncalibrated cross-sensor crops that lack orbital geometry, LoFTR found 12 candidate tie points. In an unconstrained system, this might produce a severely distorted, hallucinated warp. But LunarReg's production quality gate strictly requires at least a 20% inlier ratio. Because 94% of the candidates were noise, the system safely intercepted the run, tested all fallbacks, and rejected the pair without corrupting downstream mission maps."*

### What Should We NOT Claim?
> *Do NOT claim: "LunarReg has solved multimodal IIRS-to-OHRC registration." (State clearly that reliable cross-sensor registration requires official PDS4 orbital metadata, sensor GSD, and elevation models).*

---

## DEMO 5: Aerospace Evidence Report Export

### What Should the Judge See?
- On any successful run (Demo 1, 2, or 3), click **"Download Scientific Evidence PDF"**.
- Open the downloaded PDF in any standard PDF viewer.
- Show the **7-page aerospace report**:
  - Page 1: Registration Summary & Pass Stamp
  - Page 2: Geospatial & Sensor Provenance
  - Page 3: Illumination & Contrast Telemetry
  - Page 4: Correspondence & Spatial Distribution Map
  - Page 5: Homography Matrix & Registered Pushbroom Product
  - Page 6: Independent Multi-Seed Held-Out Validation
  - Page 7: Artifact Manifest & Digital Verification Hash

### What Should We Say?
> *"Every successful registration produces an automated, 7-page aerospace-grade scientific report verified by an embedded PDFium renderer. It provides mission scientists with complete auditability, from raw sensor telemetry to multi-seed statistical convergence."*
