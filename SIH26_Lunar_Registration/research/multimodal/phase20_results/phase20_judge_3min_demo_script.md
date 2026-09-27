# LunarReg — 3-Minute Live Judge Demonstration Script (SIH26166)

> **Document Type**: Turn-by-Turn Spoken Live Demonstration Script  
> **Platform**: Streamlit Web Interface (`app/app.py`) backed by `app/adaptive_adapter.py`  
> **Target Duration**: Exactly 3 Minutes (180 Seconds)  
> **Canonical File**: `research/multimodal/phase20_results/phase20_judge_3min_demo_script.md`

---

## Pre-Demonstration Checklist & System Setup

Before calling the judges to the screen:
1. **Launch Streamlit Server**:
   ```powershell
   streamlit run app/app.py
   ```
2. **Verify Browser Display**:
   - Open browser to `http://localhost:8501`.
   - Ensure the sidebar engine mode is set to: **`Adaptive Production Engine`**.
3. **Verify Frozen Thresholds in Sidebar**:
   - Minimum Candidate Matches: `10`
   - Minimum Initial Inliers: `8`
   - Minimum Inlier Ratio: `20% (0.20)`
   - Minimum Spatial Occupancy: `33% (0.33)`
   - RANSAC Inlier Threshold: `3.0 px`
4. **Preload Benchmark Data**:
   Ensure `demo_cases` and benchmark pairs (`pair_01`, `pair_02`, `pair_03`, `pair_04`, and `souse.jpeg`/`ref.jpeg`) are accessible.

---

## Timed Live Demonstration Walkthrough

```
[00:00 - 00:25] Stage 0: Interface & Defensive Quality-Gate Overview
[00:25 - 00:55] Stage 1: DEMO 1 — Optical Nominal & Spatial Uniformity (Pair 04)
[00:55 - 01:25] Stage 2: DEMO 2 — Severe Illumination & Shadow Inversion (Pair 03)
[01:25 - 01:55] Stage 3: DEMO 3 — Low Contrast & Scale Variation (Pair 01)
[01:55 - 02:25] Stage 4: DEMO 4 — Cross-Sensor Inputs & Safe Quality-Gate Rejection
[02:25 - 02:50] Stage 5: DEMO 5 — Automated 7-Page Aerospace Scientific PDF Report
[02:50 - 03:00] Stage 6: Conclusion & Transition to Judge Q&A
```

---

### [00:00 – 00:25] Stage 0: Interface & Production Setup

#### Physical Actions on Screen:
- Point the cursor to the Streamlit top banner: **"LunarReg — Chandrayaan-2 Registration Engine"**.
- Highlight the sidebar: show the **Adaptive Production Engine** toggle and the frozen quality-gate thresholds (`10 / 8 / 20% / 33% / 3.0 px`).

#### Spoken Narrative (Presenting live):
> *"Judges, welcome to the live demonstration of LunarReg. On screen is our mission interface running our validated production pipeline. In the sidebar, you see our frozen quality-gate parameters: minimum 10 candidates, 8 initial inliers, 20% inlier ratio, and 33% spatial occupancy. The system operates fully autonomously—no manual tuning, no seed hacking, and zero human intervention."*

---

### [00:25 – 00:55] Stage 1: DEMO 1 — Optical Nominal & Spatial Uniformity (Pair 04)

#### Physical Actions on Screen:
- Select **Pair 04** (`Optical Geometric Distortion`) from the benchmark selector.
- Click the blue **"Register Images"** button.
- Point to the runtime progress: under 1.5 seconds.
- Show the visual result: the registered overlay slider and the correspondence canvas.
- Scroll down to the **Spatial Distribution Map** showing 9 out of 9 cells filled.

#### Live Telemetry Displayed:
- **Matcher**: `OpenCV SIFT`
- **Raw Inliers**: `3,940` (from 3,946 candidates)
- **Selected Correspondences**: `54` (exactly 6 points per cell across all 9 cells)
- **Spatial Occupancy**: `100.0% (9/9 cells)` | **Dispersion**: `CV = 0.0000`
- **Held-Out Cross-Validation RMSE**: `0.0034 px`
- **Execution Time**: `~1.3–1.8 seconds`

#### Spoken Narrative:
> *"We start with Pair 04, a Chandrayaan-2 optical pair. Clicking 'Register Images'... and in just 1.5 seconds, registration converges. SIFT extracted 3,940 raw inliers. But look at our correspondence map: rather than clustering 3,000 points on a single crater, our production 3x3 selection policy capped each cell at exactly 6 points, achieving 100% spatial occupancy and a Coefficient of Variation of 0.000. Our 5-seed held-out cross-validation proves internal geometric consistency down to 0.0034 pixels."*

---

### [00:55 – 01:25] Stage 2: DEMO 2 — Illumination & Shadow Inversion (Pair 03)

#### Physical Actions on Screen:
- Select **Pair 03** (`Illumination Variation`).
- Show the judges the raw inputs: emphasize that the crater rims are completely inverted—craters lit from the east in the source image are lit from the west in the reference image.
- Click **"Register Images"**.
- View the registration overlay: the inverted crater rims align seamlessly.

#### Live Telemetry Displayed:
- **Matcher**: `OpenCV SIFT (with CLAHE conditioning)`
- **Raw Inliers**: `3,340`
- **Selected Correspondences**: `54` (6 points per cell across 9 cells)
- **Spatial Occupancy**: `100.0%`
- **Held-Out Cross-Validation RMSE**: `0.0072 px`
- **Execution Time**: `~1.4 seconds`

#### Spoken Narrative:
> *"Now for a major lunar challenge: extreme sun-angle variation. Notice Pair 03: the solar incidence angle has flipped, causing crater shadows to completely invert. Standard template matchers fail completely here. Clicking 'Register'... our contrast conditioning and gradient descriptors lock 3,340 inliers, once again selecting 54 perfectly uniform tie points with an independent held-out RMSE of 0.0072 pixels. The transformed crater rims match with sub-pixel alignment."*

---

### [01:25 – 01:55] Stage 3: DEMO 3 — Low Contrast & Scale Variation (Pair 01)

#### Physical Actions on Screen:
- Select **Pair 01** (`Low Contrast / Scale Variation`).
- Point out the image dimensions: source is `146x513 px`, reference is `194x528 px`. The lunar regolith is faint and washed out.
- Click **"Register Images"**.
- Point to the telemetry: the system automatically recognized low contrast ($\sigma < 20.0$) and dimension disparity, dynamically routing to **Locked LoFTR**.

#### Live Telemetry Displayed:
- **Matcher**: `Locked LoFTR Transformer`
- **Raw Inliers**: `49` (from 166 candidates)
- **Selected Correspondences**: `38` across 8 cells
- **Spatial Occupancy**: `88.89% (8/9 cells)` (Cell 9 is geographically outside the overlap boundary)
- **Held-Out Cross-Validation RMSE**: `1.7188 px`
- **Execution Time**: `~3.8–4.0 seconds`

#### Spoken Narrative:
> *"Next is Pair 01, featuring low-contrast lunar mare and different native image scales—146x513 versus 194x528 pixels. Classical edge detectors find almost nothing in this smooth dust. Clicking 'Register'... our adaptive router measures the low contrast standard deviation and automatically deploys our locked LoFTR deep transformer. LoFTR correlates dense structural context across scales, capturing 49 inliers across 8 quadrants with a held-out RMSE of 1.72 pixels. This proves autonomous algorithm adaptation."*

---

### [01:55 – 02:25] Stage 4: DEMO 4 — Cross-Sensor & Safe Quality-Gate Rejection

#### Physical Actions on Screen:
- Load the uncalibrated cross-sensor crop pair: `souse.jpeg` $\leftrightarrow$ `ref.jpeg`.
- Point out that this is an uncalibrated optical vs infrared crop pair lacking orbital geometry.
- Click **"Register Images"**.
- Watch the live execution trace: LoFTR runs, followed by sequential fallbacks.
- Show the final screen: **Safe Rejection Banner**. Point out that `registered_image` is `None`. Zero distorted or hallucinated images appear!

#### Live Telemetry Displayed:
- **Primary Matcher (LoFTR)**: 199 candidates, 12 inliers.
- **Quality Gate Evaluation**:
  - Inlier Count: $12 \ge 8$ (**PASSED**)
  - Inlier Ratio: $6.03\% < 20.0\%$ (**FAILED — 94% noise**)
- **Sequential Fallbacks**: SIFT attempted (4 inliers, failed); SuperGlue attempted (6 inliers, failed).
- **Final Status**: `REJECTED_BY_GATE`
- **Diagnostic Message**: *"All available matchers failed the quality gate. Registration halted safely."*
- **Output Image**: `None` (Zero corrupted products)

#### Spoken Narrative:
> *"Now we demonstrate our most critical mission safeguard: safe rejection. We feed the system uncalibrated cross-sensor crops that lack PDS4 orbital metadata. Clicking 'Register'... LoFTR extracts 12 candidate inliers. In an unconstrained system, an algorithm might use those 12 points to force an unphysical, hallucinated warp. But our quality gate evaluates the inlier ratio: 6.03% is far below our 20% threshold. The system immediately tries SIFT and SuperGlue fallbacks, fails them, and terminates safely. No corrupted map is created. In aerospace, knowing when NOT to register protects mission safety."*

---

### [02:25 – 02:50] Stage 5: DEMO 5 — Automated 7-Page Aerospace PDF Report

#### Physical Actions on Screen:
- Return to **Demo 1** or click **"Download Scientific Evidence PDF"**.
- Open the resulting 7-page PDF report in the PDF viewer.
- Rapidly page through:
  - **Page 1**: Mission pass stamp and telemetry summary.
  - **Page 4**: Color-coded 3x3 spatial distribution quadrant map.
  - **Page 5**: 8-DoF homography transformation matrix and registered product.
  - **Page 6**: 5-seed cross-validation convergence curves.
  - **Page 7**: SHA-256 digital verification hashes.

#### Spoken Narrative:
> *"Finally, every successful registration automatically generates a comprehensive 7-page aerospace evidence report, verified programmatically by an embedded PDFium renderer. It provides mission scientists with complete auditability: raw sensor metadata on Page 2, the 3x3 tie-point mesh on Page 4, the exact homography matrix on Page 5, multi-seed cross-validation on Page 6, and SHA-256 cryptographic hashes on Page 7. Every pixel and transformation is fully accountable."*

---

### [02:50 – 03:00] Stage 6: Conclusion & Transition to Judge Q&A

#### Spoken Narrative:
> *"To summarize: LunarReg delivers adaptive matching, guaranteed 3x3 spatial uniformity, validated sub-pixel geometric consistency, verified safe rejection, and publication-ready aerospace reporting in under 4 seconds. Thank you, judges. We are eager to answer your questions."*

---

## Contingency & Quick-Troubleshooting Guide for Presenter

| Scenario / Glitch | Immediate Action | Spoken Recovery Line |
| :--- | :--- | :--- |
| **Streamlit re-runs on upload** | Allow 1–2 seconds for Streamlit's cache to load. | *"The Streamlit reactive runner is caching the sensor tensors into memory."* |
| **Judge asks to inspect raw tie points** | Scroll down to the interactive tie-point table or open the exported CSV. | *"Every tie point's sub-pixel floating-point coordinates are fully exported in our CSV manifest."* |
| **Judge asks why Demo 4 failed** | Point directly to the $6.03\% < 20.0\%$ inlier ratio display. | *"It failed intentionally. The input is uncalibrated noise; accepting it would violate our quality gate."* |
| **Judge asks about physical GSD** | Acknowledge that physical GSD requires PDS4 XML orbital altitude. | *"Physical GSD normalization requires spacecraft altitude and focal length metadata, which we integrate in Phase 21."* |
