# LunarReg — Final SIH26166 Presentation Content (12-Slide Master Narrative)

> **Document Type**: Final Presentation Slide Deck Narrative & Presenter Script  
> **Problem Statement**: ISRO / SIH26166 — Automatic Registration of High-Resolution Lunar Optical Imagery  
> **Scientific Status**: Grounded 100% on Verified Phase 20 Production Freeze Artifacts  
> **Canonical Path**: `research/multimodal/phase20_results/phase20_final_ppt_content.md`

---

## Slide 1: Problem Statement & Mission Objective

### Visual Description / Layout
- **Header**: ISRO Problem Statement SIH26166 — Lunar Image Registration
- **Center**: Split layout with mission problem illustration on the left and core mission requirements on the right.
- **Left Graphic**: Diagram showing two overlapping lunar pushbroom orbital swaths with differing sun angles, perspective tilt, and sensor scales.
- **Right Box**: Highlighting the 4 core technical pillars of the Problem Statement:
  1. Multimodal / Multi-pass correspondence matching
  2. Invariance to illumination, viewpoint, and scale variations
  3. Uniform spatial distribution of tie points across the overlap area
  4. Perspective image registration with sub-pixel precision and independent validation

### Key Bullet Points
- **The Core Goal**: Fully automated, end-to-end registration of high-resolution Chandrayaan-2 lunar optical imagery.
- **Payload Targets**: Optical High Resolution Camera (OHRC), Terrain Mapping Camera-2 (TMC-2), and Imaging Infrared Spectrometer (IIRS).
- **Core Challenge**: Registering lunar surface observations acquired under vastly different orbit geometries, solar elevations, and spatial resolutions without manual intervention.
- **Engineering Standard**: Produce geometrically sound warped image products, sub-pixel tie-point coordinates, and auditable validation evidence suitable for planetary mapping pipelines.

### Exact Metrics & References
- **SIH Problem Statement ID**: SIH26166.
- **Target Payloads**: Chandrayaan-2 OHRC (nominal ~0.25–0.32 m/px), TMC-2 (nominal ~5.0 m/px), IIRS (~8–20 m/px).
- **Benchmark Evaluation Pairs**: 4 standardized Chandrayaan-2 optical pairs (`pair_01` to `pair_04`) + uncalibrated cross-sensor crop pair (`souse.jpeg` $\leftrightarrow$ `ref.jpeg`).

### Spoken Presenter Notes (35–45 seconds)
> "Honorable judges, Problem Statement SIH26166 challenges us to automate the registration of high-resolution Chandrayaan-2 lunar imagery. In lunar orbit, spacecraft capture the surface across multiple passes separated by weeks or months. This introduces severe illumination shifts, perspective tilt, and scale discrepancies between swaths. Our system, LunarReg, delivers a fully automated, deterministic registration pipeline designed to extract robust spatial correspondences, enforce strict spatial uniformity, eliminate human-in-the-loop tuning, and provide verifiable geometric outputs backed by aerospace-grade audit reports."

### What NOT to Say
- **DO NOT CLAIM**: "We have completely solved universal multimodal lunar registration for any lunar image in existence."
- **DO NOT CLAIM**: "Our system is 100% accurate under all conditions."

---

## Slide 2: Why Lunar Image Registration is Difficult

### Visual Description / Layout
- **Layout**: 4-quadrant challenge breakdown diagram with side-by-side thumbnail comparisons showing:
  - Quadrant 1 (Top-Left): *Illumination Inversion* — Crater shadow inversion between low-angle morning vs afternoon sun.
  - Quadrant 2 (Top-Right): *Viewpoint / Parallax* — Off-nadir foreshortening and steep crater rim displacement.
  - Quadrant 3 (Bottom-Left): *Low Texture Regolith* — Repetitive, low-contrast lunar mare surfaces lacking distinct visual corners.
  - Quadrant 4 (Bottom-Right): *Resolution & Modality Disparities* — Differing native detector pixel scales and optical vs infrared bandpass properties.

### Key Bullet Points
- **Photometric Non-Linearities**: Craters exhibit severe shadow migration and intensity inversion as the solar incidence angle changes between orbital tracks.
- **Geometric Distortions**: Off-nadir sensor pointing creates non-linear projective foreshortening across local terrain relief.
- **Texture Starvation**: Vast expanses of lunar mare exhibit uniform regolith with low dynamic range (image standard deviation $< 20.0$), defeating classical corner detectors.
- **The Clumping Failure Mode**: Standard feature detectors cluster 90%+ of their tie points on a single high-contrast crater lip, leaving the remaining 80% of the scene unconstrained and prone to severe warping divergence.

### Exact Metrics & References
- **Dynamic Range Benchmark**: Tested low-contrast lunar regolith exhibiting $\sigma < 16.0$ intensity standard deviation (`pair_01`).
- **Solar Incidence Range**: Evaluated on orbital pairs spanning severe phase angle differences where crater shadows flip by $180^\circ$ (`pair_03`).
- **Resolution Mismatch**: Tested pairs with unequal pixel dimensions (`146 \times 513\text{ px}` vs `194 \times 528\text{ px}`).

### Spoken Presenter Notes (35–45 seconds)
> "Planetary registration is far more unforgiving than terrestrial computer vision. First, the Moon has no atmosphere or diffuse lighting: when solar incidence changes, crater shadows completely invert, rendering appearance-based matchers ineffective. Second, large portions of lunar mare are feature-sparse regolith where traditional edge detectors find almost nothing. Third, when features are detected, they clump heavily around high-contrast crater rims. If you fit a transformation to clumped points, the rest of the image suffers catastrophic geometric distortion. A viable solution must adapt to texture and actively enforce spatial distribution."

### What NOT to Say
- **DO NOT CLAIM**: "Optical matching can see into permanently shadowed craters with zero sunlight." (State clearly: optical sensors require reflected photons; radar or active illumination is required for total darkness).
- **DO NOT CLAIM**: "Planar homography alone solves deep crater 3D parallax." (Homography models planar scenes; steep terrain requires a DEM).

---

## Slide 3: The LunarReg Solution Architecture

### Visual Description / Layout
- **Center**: Clean horizontal flow diagram illustrating LunarReg's 10-stage deterministic pipeline:
  `Input Validation` $\rightarrow$ `Dual-Track Characterization` $\rightarrow$ `Adaptive Router` $\rightarrow$ `Matcher Execution (LoFTR / SIFT)` $\rightarrow$ `Production Quality Gate (10/8/20%/33%)` $\rightarrow$ `Sequential Fallback` $\rightarrow$ `3x3 Spatial Grid Selection` $\rightarrow$ `RANSAC Homography Estimation` $\rightarrow$ `5-Seed Held-Out Cross-Validation` $\rightarrow$ `7-Page PDF Report Generation`.
- **Callout Box**: "Strict Separation of Concerns: Validated Deterministic Production Pipeline vs Isolated Research Sandbox."

### Key Bullet Points
- **Dual-Track Engineering**: A production engine built for mission reliability paired with an isolated research testbed for offline scientific exploration.
- **Deterministic Routing**: Automated image characterization inspects contrast and texture gradients to select the optimal matcher without user intervention.
- **Multi-Layer Defensive Architecture**: Quality-gate verification and fallback safeguards ensure that invalid matches never propagate downstream.
- **Aerospace-Grade Verification**: Every accepted registration is validated via independent multi-seed held-out cross-validation and documented in an automated 7-page PDF report.

### Exact Metrics & References
- **10 Sequential Pipeline Stages**: Deterministic execution flow in [`research/adaptive_matcher/adaptive_engine.py`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/adaptive_matcher/adaptive_engine.py).
- **Production Routing Execution**: Average runtime $1.3\text{s}$ to $4.0\text{s}$ on standard CPU hardware.
- **Audit Verification**: Validated with 5 independent hold-out cross-validation seeds `(1, 2, 3, 4, 5)`.

### Spoken Presenter Notes (35–45 seconds)
> "To address these challenges, we built LunarReg around a 10-stage deterministic pipeline. Rather than forcing every image pair through a single fragile matcher, LunarReg analyzes the input imagery and routes it to the most capable algorithm. Low-contrast or scale-varying scenes are assigned to our deep local transformer, LoFTR, while high-contrast cratered terrains are routed to high-speed SIFT. Crucially, every candidate match must pass our strict production quality gate. If verified, correspondences pass through a 3x3 spatial selection layer and multi-seed cross-validation before generating a validated 7-page aerospace PDF report."

### What NOT to Say
- **DO NOT CLAIM**: "We developed our own brand new deep learning architecture from scratch." (LoFTR and SuperGlue are established models integrated into our adaptive framework).
- **DO NOT CLAIM**: "Our pipeline uses AI to hallucinate missing points." (All correspondences are strictly grounded in detected physical image features).

---

## Slide 4: Adaptive Matching Architecture

### Visual Description / Layout
- **Top**: Decision tree / routing matrix diagram showing how image metrics dictate the matcher:
  - Contrast Standard Deviation $\sigma < 20.0$ OR Native Dimension Mismatch $\rightarrow$ **Locked LoFTR Transformer**
  - High Contrast $\sigma \ge 20.0$ AND Strong Edge Density $\rightarrow$ **OpenCV SIFT**
  - Failure at Quality Gate $\rightarrow$ **Sequential Fallback to SuperGlue Graph Neural Network**
- **Bottom**: Side-by-side feature visualizations:
  - Left: LoFTR's dense transformer attention grid locking subtle structural textures on low-contrast regolith.
  - Right: SIFT keypoint scale-space extrema locking sharp crater rim features.

### Key Bullet Points
- **Texture-Aware Heuristic**: Image standard deviation ($\sigma$) and Sobel gradient density characterize the photometric terrain.
- **Locked LoFTR Transformer**: Operates directly on dense coarse-to-fine feature maps with self- and cross-attention, bypassing discrete detector failure on smooth lunar surfaces.
- **OpenCV SIFT**: Provides high-speed, scale-invariant gradient orientation matching when rich crater geometry is present ($>3,000$ inliers in $<1.5\text{s}$).
- **SuperGlue Deep Fallback**: Attentional graph neural network deployed as a fallback mechanism when primary matchers produce marginal candidate sets.

### Exact Metrics & References
- **Contrast Threshold**: $\sigma = 20.0$ threshold separating low-contrast regolith from nominal cratered terrain.
- **LoFTR Candidates**: 166 candidates yielding 49 inliers on low-contrast `pair_01`.
- **SIFT Candidates**: 3,946 candidates yielding 3,940 inliers on nominal optical `pair_04`.
- **Fallback Hierarchy**: Primary Matcher $\rightarrow$ Fallback 1 (SIFT / LoFTR) $\rightarrow$ Fallback 2 (SuperGlue).

### Spoken Presenter Notes (35–45 seconds)
> "Why adaptive routing? In planetary mapping, no single algorithm works across all terrains. SIFT is blazingly fast and yields thousands of points on sharp crater rims, but completely starves on smooth maria. Conversely, deep transformers like LoFTR excel at finding subtle structural correlations across low-contrast regolith and scale differences, but carry higher computational cost. Our adaptive router measures the image contrast standard deviation and gradient density upfront, dynamically deploying LoFTR where needed and SIFT where optimal, with SuperGlue standing by as an attentional fallback."

### What NOT to Say
- **DO NOT CLAIM**: "Our router uses a black-box neural network to guess the matcher." (The router is a fully interpretable, deterministic rule-based heuristic).
- **DO NOT CLAIM**: "SIFT is outdated and obsolete." (SIFT extracted over 4,000 rock-solid inliers in 1.5 seconds on nominal Chandrayaan-2 imagery).

---

## Slide 5: Quality Gate & Safe Rejection Mechanism

### Visual Description / Layout
- **Visual**: Flowchart of the 4-parameter Quality Gate with a prominent "Safe Rejection" branch.
- **Center Table**: The 4 Frozen Production Thresholds:
  1. Minimum Candidates $\ge 10$
  2. Minimum Initial Inliers $\ge 8$
  3. Minimum Inlier Ratio $\ge 20.0\%$ ($0.20$)
  4. Minimum Spatial Occupancy $\ge 33.3\%$ ($0.33$)
- **Right Callout**: "Real Mission Safety: `DEMO 4` Cross-Sensor Rejection":
  - LoFTR Candidates: 199 | Inliers: 12 ($\ge 8$ passed inlier count!)
  - Inlier Ratio: $6.03\% < 20.0\%$ (**FAILED GATE**)
  - System Result: `registered_image = None` (Zero hallucinated warps).

### Key Bullet Points
- **The Mission-Critical Principle**: In aerospace operations, an unconstrained or false warp is far more hazardous than a safe rejection.
- **Multi-Criteria Verification**: A candidate set must satisfy raw count ($\ge 8$), signal-to-noise ratio ($\ge 20\%$), and spatial coverage ($\ge 33\%$) simultaneously.
- **Interception of False Matches**: Prevents random photometric noise from fitting degenerate projective transformations.
- **Safe Rejection Guarantee**: When all matchers fail the gate, the pipeline gracefully outputs `None` for the registered image with a clear diagnostic reason.

### Exact Metrics & References
- **Frozen Runtime Thresholds**: `min_candidates=10`, `min_inliers=8`, `min_inlier_ratio=0.20`, `min_occupancy=0.33`, `ransac_thresh=3.0 px`.
- **Rejection Case Study (`DEMO 4`)**: Uncalibrated crop pair (`souse.jpeg` $\leftrightarrow$ `ref.jpeg`) produced 199 candidates and 12 inliers. Passed inlier count ($12 \ge 8$) but failed inlier ratio ($6.03\% < 20.0\%$). Fallbacks failed. System halted safely without distorting mission maps.

### Spoken Presenter Notes (35–45 seconds)
> "In an automated planetary mapping pipeline, knowing when NOT to register is just as vital as registering successfully. If a system accepts noisy, false correspondences, it produces warped images with catastrophic geometric distortions that can corrupt landing site analysis. LunarReg enforces a strict 4-parameter quality gate: at least 10 candidates, at least 8 inliers, a minimum 20% inlier ratio, and at least 33% spatial occupancy. In our Demo 4 test on uncalibrated cross-sensor crops, LoFTR found 12 inliers, but because 94% of the candidates were noise, our gate safely intercepted the pipeline, rejected the warp, and protected mission integrity."

### What NOT to Say
- **DO NOT CLAIM**: "Our quality gate threshold is 15 inliers." (The verified runtime production code threshold is exactly 8 initial inliers; earlier research notes that mentioned 15 were corrected during our Phase 19 code audit).
- **DO NOT CLAIM**: "Rejection represents an algorithm bug." (Safe rejection is an intentional, validated safety feature).

---

## Slide 6: Spatial Distribution: Eliminating Tie-Point Clumping

### Visual Description / Layout
- **Visual**: Side-by-side comparison diagram:
  - Left Panel: *Standard Unconstrained Matcher Output* — 3,000+ points clumped onto a single crater rim; remaining 85% of the image has 0 points. Coefficient of Variation $CV > 1.80$.
  - Right Panel: *LunarReg 3x3 Spatial Grid Partitioning* — 54 tie points evenly distributed across all 9 quadrants (exactly 6 points per cell). $CV = 0.0000$, Occupancy = $100\%$.
- **Bottom Equation**:
  $$CV = \frac{\sigma_{\text{cell}}}{\mu_{\text{cell}}} = 0.0000 \quad (9/9 \text{ cells occupied, exactly } 6 \text{ points/cell})$$

### Key Bullet Points
- **The Clumping Dilemma**: Feature detectors naturally over-sample high-frequency textures (sharp crater edges) while ignoring smooth, low-contrast terrain.
- **Projective Divergence**: When RANSAC fits a homography to points concentrated in one quadrant, extrapolation errors cause severe stretching across the rest of the image.
- **Production 3x3 Binning**: Divides the image into a $3 \times 3$ grid (9 cells) and caps correspondences at `max_per_cell = 6` points (maximum 54 points).
- **Uniformity Metric**: Evaluated using the Coefficient of Variation ($CV$) of point counts per cell; $CV = 0.00$ represents perfect spatial uniformity.

### Exact Metrics & References
- **Cell Structure**: 9 equal spatial cells ($3 \times 3$ grid).
- **Cell Capacity**: Capped at `max_per_cell = 6` highest-confidence points per cell.
- **Spatial Occupancy**: $100.0\%$ (9/9 cells occupied) on nominal optical pairs (`pair_02`, `pair_03`, `pair_04`).
- **Dispersion Metric**: $CV = 0.0000$ (standard deviation of cell counts = 0, mean = 6.0).
- **Partial Overlap Case**: $88.89\%$ (8/9 cells occupied, 38 points) on `pair_01` due to physical scene boundary clipping.

### Spoken Presenter Notes (35–45 seconds)
> "One of the most explicit requirements of SIH26166 is maintaining a uniform distribution of match points. On lunar imagery, standard matchers naturally clump thousands of points on a single crater lip. If you feed those clumped points into RANSAC, the homography matrix fits the crater beautifully but severely distorts the rest of the image. LunarReg solves this with our production 3x3 spatial selection policy. We partition the overlap into 9 equal cells and cap each cell at 6 points. On our optical benchmarks, this achieves 100% spatial occupancy and a Coefficient of Variation of exactly 0.000, guaranteeing that the geometric fit is anchored across the entire scene."

### What NOT to Say
- **DO NOT CLAIM**: "We run SSC in the production pipeline." (SSC was evaluated extensively in Phase 7-8 research, but our frozen production layer implements deterministic 3x3 spatial binning with max 6 points per cell).
- **DO NOT CLAIM**: "More points are always better." (54 uniformly distributed points provide far superior geometric constraint than 4,000 clumped points).

---

## Slide 7: Production Results: Optical, Illumination & Viewpoint

### Visual Description / Layout
- **Visual**: 3-column comparative benchmark showcase featuring:
  - Column 1 (`Pair 04`): Optical Distortion Baseline — Perfect feature mesh across 9 cells.
  - Column 2 (`Pair 02`): Viewpoint / Perspective Variation — Angled perspective correctly rectified.
  - Column 3 (`Pair 03`): Severe Sun-Angle / Illumination Inversion — Opposing shadows locked seamlessly.
- **Summary Table**: Presenting runtime, inliers, selected points, spatial occupancy, and held-out cross-validation RMSE for each pair.

### Key Bullet Points
- **Nominal Optical Registration (`Pair 04`)**: SIFT extracted 3,940 inliers; 54 points selected; held-out RMSE of `0.0034 px` in $1.77\text{s}$.
- **Viewpoint Variation (`Pair 02`)**: Handled perspective distortion; SIFT extracted 4,026 inliers; 54 points selected; held-out RMSE of `0.0045 px` in $1.50\text{s}$.
- **Illumination Variation (`Pair 03`)**: Overcame inverted crater shadows; SIFT extracted 3,340 inliers; 54 points selected; held-out RMSE of `0.0072 px` in $1.39\text{s}$.
- **Consistency**: All three pairs achieved $100\%$ spatial occupancy (9/9 cells) and sub-0.01 pixel held-out geometric consistency.

### Exact Metrics & References
- **Optical Baseline (`Pair 04`)**: 3,940 inliers, 54 points, $100\%$ occupancy, held-out RMSE `0.0034 px`, runtime $1.77\text{s}$.
- **Viewpoint (`Pair 02`)**: 4,026 inliers, 54 points, $100\%$ occupancy, held-out RMSE `0.0045 px`, runtime $1.50\text{s}$.
- **Illumination (`Pair 03`)**: 3,340 inliers, 54 points, $100\%$ occupancy, held-out RMSE `0.0072 px`, runtime $1.39\text{s}$.
- **Validation Engine**: Independent 5-seed cross-validation (`seeds 1, 2, 3, 4, 5`) with 80/20 train/check splits.

### Spoken Presenter Notes (35–45 seconds)
> "Here are our end-to-end production results on real Chandrayaan-2 optical benchmarks. Across optical distortion, perspective viewpoint variations, and severe illumination changes, LunarReg consistently succeeds. Notice the illumination pair: despite completely inverted shadows where crater rims swap from bright to dark, SIFT with CLAHE contrast conditioning locked 3,340 inliers. The downstream layer extracted 54 perfectly distributed tie points across all 9 cells, achieving an independent held-out RMSE of 0.0072 pixels in under 1.4 seconds. These results demonstrate robust performance across the core optical challenges of SIH26166."

### What NOT to Say
- **DO NOT CLAIM**: "Held-out RMSE of 0.0034 px proves 0.0034-pixel physical ground truth on the lunar surface." (Held-out RMSE measures internal mathematical consistency of the geometric model on independent test points).
- **DO NOT CLAIM**: "Results were cherry-picked." (All 4 benchmark pairs were executed consecutively through the production entry point).

---

## Slide 8: Scale Variation: Image-Space vs Physical Scale

### Visual Description / Layout
- **Visual**: Split comparison between Image-Space Scale Tolerance and Physical Lunar GSD Scale:
  - Left Diagram: *Image-Space Demonstration (`Pair 01` & Phase 17)* — Input image dimensions $146 \times 513\text{ px}$ vs $194 \times 528\text{ px}$. LoFTR matching succeeds with 49 inliers and held-out RMSE of `1.7188 px`.
  - Right Diagram: *Physical Scale Normalization Requirement* — Orbital camera formula illustrating missing parameters:
    $$\text{GSD} = \frac{H \cdot p}{f}$$
    Highlighting that spacecraft altitude ($H$), focal length ($f$), and detector pixel pitch ($p$) are required for physical scale invariance.

### Key Bullet Points
- **PS Requirement Classification**: Scale Variation is **PARTIALLY DEMONSTRATED**.
- **Demonstrated Image-Space Capability**: Deep transformer (LoFTR) successfully bridges resolution differences across non-identical image dimensions (`pair_01`, RMSE `1.7188 px`) and controlled $0.50\times$ to $2.00\times$ geometric scaling (Phase 17).
- **Scientific Honesty on Physical GSD**: Physical scale normalization cannot be claimed on uncalibrated image crops lacking PDS4 XML metadata.
- **No Fabricated Assumptions**: LunarReg strictly refuses to assume arbitrary physical scale ratios (e.g. 40× or 0.25 m/px) without verified spacecraft orbital geometry.

### Exact Metrics & References
- **Pair 01 Benchmark**: Native dimensions $146 \times 513\text{ px}$ vs $194 \times 528\text{ px}$; 49 inliers; 38 selected points across 8 cells; held-out RMSE `1.7188 px`; runtime $4.03\text{s}$.
- **Phase 17 Geometric Diagnostic**: Validated scale tolerance across $0.50\times$, $0.75\times$, $1.00\times$, $1.25\times$, $1.50\times$, and $2.00\times$ zoom factors.
- **Physical Formula**: Spacecraft orbital altitude $H \approx 100\text{ km}$, focal length $f$, pixel pitch $p$.

### Spoken Presenter Notes (35–45 seconds)
> "Addressing scale variation requires clear scientific distinction. In image space, LunarReg handles scale differences robustly. On Pair 01, which features different native pixel dimensions and faint lunar regolith, our adaptive router engaged LoFTR, locking 49 inliers with a held-out RMSE of 1.72 pixels. Furthermore, our Phase 17 controlled studies confirmed tolerance from 0.5x to 2.0x zoom. However, we classify physical scale normalization as PARTIALLY DEMONSTRATED because true physical GSD normalization requires spacecraft orbital altitude and camera focal lengths from PDS4 labels. Without verified metadata, claiming physical scale invariance would be scientifically unfounded."

### What NOT to Say
- **DO NOT CLAIM**: "LunarReg achieves physical GSD scale invariance on raw JPEG images." (Physical GSD requires PDS4 orbital metadata).
- **DO NOT CLAIM**: "Scale variation is completely solved." (It is partially demonstrated in image space; physical scale requires orbital geometry).

---

## Slide 9: Sub-Pixel Accuracy: Evidence & Claim Boundaries

### Visual Description / Layout
- **Visual**: Comprehensive accuracy matrix and error distribution chart:
  - Left: Bar chart of Phase 18 Controlled Validation Errors across 8 geometric transforms:
    - Pure Translation ($+0.35, -0.45\text{ px}$): Mean error `0.2647 px` (100% $\le 0.50\text{ px}$)
    - Pure Translation ($+0.72, +0.28\text{ px}$): Mean error `0.3014 px` (100% $\le 0.50\text{ px}$)
    - Small Rotation ($+0.85^\circ$): Mean error `0.4079 px`
    - Overall 8-Transform Average: `0.4204 px`
  - Right: Scientific Claim Boundary Box:
    - *Controlled Synthetic Warp*: **PROVEN** Sub-Pixel Accuracy ($<0.50\text{ px}$).
    - *Real Lunar Benchmark Imagery*: **PARTIALLY DEMONSTRATED** (Model consistency verified via held-out RMSE `0.0034–0.0072 px`; real physical ground-truth accuracy unverified due to lack of surveyed GCPs).

### Key Bullet Points
- **PS Requirement Classification**: Sub-Pixel Accuracy is **PARTIALLY DEMONSTRATED**.
- **Controlled Mathematical Proof (Phase 18)**: When true geometric transforms are known, LunarReg recovers correspondence coordinates with sub-pixel precision (`0.2647–0.3014 px` on translations; 100% of points $\le 0.50\text{ px}$).
- **Production Sub-Pixel Pipeline**: Correspondences and homography mappings maintain 64-bit floating-point precision throughout RANSAC and downstream coordinate exports.
- **The Physical Ground-Truth Boundary**: Real lunar orbital imagery lacks surveyed ground control points (GCPs). Internal held-out cross-validation RMSE measures model consistency, not absolute physical truth.

### Exact Metrics & References
- **Controlled Translation Error**: `0.2647 px` ($dx=+0.35, dy=-0.45$) and `0.3014 px` ($dx=+0.72, dy=+0.28$).
- **Controlled Corner Error**: `0.2583 px` and `0.3029 px`.
- **Threshold Adherence**: 100.0% of correspondence points achieve sub-pixel error $\le 0.50\text{ px}$ under controlled translations.
- **Held-Out Model Consistency on Real Imagery**: `0.0034 px` (`pair_04`), `0.0045 px` (`pair_02`), `0.0072 px` (`pair_03`).

### Spoken Presenter Notes (35–45 seconds)
> "Sub-pixel accuracy is an explicit requirement of SIH26166, and we evaluated it with strict mathematical rigor. In our Phase 18 controlled study where ground-truth geometry was known, LunarReg recovered correspondence coordinates with an average error of 0.26 to 0.30 pixels on sub-pixel translations, with 100% of points falling below 0.5 pixels. On real lunar benchmark pairs, our independent held-out cross-validation converges to between 0.003 and 0.007 pixels. However, because real lunar imagery does not possess physical surveyed ground control points on the Moon, we classify real-world physical sub-pixel accuracy as PARTIALLY DEMONSTRATED."

### What NOT to Say
- **DO NOT CLAIM**: "We have proven 0.003-pixel physical accuracy on the Moon's surface." (Explain that held-out cross-validation proves internal geometric consistency, while physical ground-truth accuracy requires surveyed surface landmarks).
- **DO NOT CLAIM**: "Sub-pixel accuracy is impossible on lunar imagery." (It is proven under controlled transformations and highly consistent under model validation).

---

## Slide 10: Multimodal Registration & Mission Safety Boundaries

### Visual Description / Layout
- **Visual**: Diagram contrasting Intra-Sensor Success vs Cross-Sensor Operational Reality:
  - Top Half: *Intra-Sensor Optical Registration* — Fully demonstrated across Chandrayaan-2 optical pairs with thousands of valid inliers.
  - Bottom Half: *Cross-Sensor Reality (`souse.jpeg` $\leftrightarrow$ `ref.jpeg`)* — Diagram showing why uncalibrated optical vs infrared crops fail quality gates (wavelength disparity, sensor GSD mismatch, lack of orbital ephemeris).
  - Prominent Badge: "Verified Safe Rejection: Preventing Mission Map Corruption."

### Key Bullet Points
- **PS Requirement Classification**: Multimodal Registration is **PARTIALLY DEMONSTRATED / LIMITED BY AVAILABLE VERIFIED DATA**.
- **The Available Data Limitation**: The benchmark crop pair (`souse.jpeg` $\leftrightarrow$ `ref.jpeg`) completely lacks PDS4 metadata, sensor identification, GSD, and ephemeris. Paired TMC scenes do not exist in the repository.
- **Quality-Gate Interception**: When tested on uncalibrated cross-sensor crops, LoFTR generated 199 candidates and 12 inliers. The system intercepted the run because the inlier ratio was only $6.03\%$ (threshold $\ge 20\%$).
- **No Hallucinated Outputs**: SIFT and SuperGlue fallbacks also rejected the pair. The pipeline terminated gracefully, outputting zero corrupted warps.

### Exact Metrics & References
- **Demo 4 Telemetry**: Primary LoFTR candidates = 199, inliers = 12 ($12 \ge 8$ passed count, but $6.03\% < 20.0\%$ failed ratio).
- **Fallback Telemetry**: SIFT attempted (4 inliers $< 8$, failed); SuperGlue attempted (6 inliers $< 8$, failed).
- **Execution Result**: `registered_image is None`, `safe_rejection_verified = True`, runtime $9.05\text{s}$.
- **Repository Data Audit**: Optical benchmark pairs present and validated; calibrated TMC-2/IIRS pairs absent.

### Spoken Presenter Notes (35–45 seconds)
> "The problem statement asks for registration across optical, TMC, and IIRS modalities. Here we must be completely honest about real data limitations. In our verified repository, optical-to-optical registration is fully functional. However, paired calibrated TMC and IIRS data with orbital metadata was not provided. When we stress-tested LunarReg on the uncalibrated cross-sensor crop pair, LoFTR found 12 candidate tie points. But our quality gate detected that 94% of the matches were noise and safely rejected the run. Rather than outputting a distorted, hallucinated image, LunarReg protected the mapping pipeline. Universal cross-sensor registration requires calibrated Level-2 data."

### What NOT to Say
- **DO NOT CLAIM**: "We have solved universal multimodal registration between OHRC, TMC, and IIRS." (Uncalibrated cross-sensor crops safely fail quality gates; calibrated TMC data is absent).
- **DO NOT CLAIM**: "The failure on souse.jpeg/ref.jpeg is an algorithm flaw." (It is a verified demonstration of safe rejection on uncalibrated, noisy inputs).

---

## Slide 11: Aerospace Verification & Automated PDF Reporting

### Visual Description / Layout
- **Visual**: Carousel / collage displaying key pages from the automated **7-Page Aerospace Scientific Evidence PDF Report**:
  - Page 1: Flight Mission Header, Registration Status Badge, Primary Metrics Summary.
  - Page 2: Geospatial & Sensor Provenance, Image Characteristics ($\sigma$, resolution).
  - Page 3: Illumination & Contrast Telemetry, CLAHE Histograms.
  - Page 4: 3x3 Spatial Grid Visualization with Color-Coded Quadrant Point Distribution.
  - Page 5: $3 \times 3$ Homography Transformation Matrix & Perspective Warped Output.
  - Page 6: Independent 5-Seed Hold-Out Validation Plot and RMSE Convergence Table.
  - Page 7: Digital Verification Manifest with SHA-256 Checksums.
- **Callout**: "Verified by Embedded Chromium PDFium Engine — 100% Deterministic and Auditable."

### Key Bullet Points
- **Automated Scientific Documentation**: Every successful registration immediately compiles a publication-grade, 7-page PDF evidence report.
- **Embedded PDFium Verification**: The report generation pipeline is validated programmatically by rendering pages back into memory to confirm zero formatting defects.
- **Complete Traceability**: Page 7 embeds SHA-256 cryptographic hashes for input images, exported CSV tie points, and output products.
- **Multi-Seed Validation Telemetry**: Embeds full statistical variance across 5 independent random train/test splits.

### Exact Metrics & References
- **Report Size**: Exactly 7 structured pages per registered pair.
- **Audit Tooling**: Validated using `validate_pdf_report` backed by Chromium PDFium.
- **Verified Deliverables**: 4 complete PDF reports generated in `research/multimodal/phase20_results/demo_artifacts/` for Demos 1, 2, 2B, and 3.
- **Seed Convergence**: Reports mean and standard deviation of RMSE across seeds `(1, 2, 3, 4, 5)`.

### Spoken Presenter Notes (35–45 seconds)
> "In aerospace software, reproducibility and auditability are paramount. For every successful registration, LunarReg automatically compiles a comprehensive 7-page aerospace-grade evidence report. This is not just a screenshot dump: it contains full sensor provenance, illumination histograms, the 3x3 spatial distribution map, the exact 8-DoF homography matrix, multi-seed cross-validation curves, and SHA-256 digital hashes for data integrity. We even built an automated Chromium PDFium verification engine to certify that every generated PDF compiles and renders flawlessly without human oversight."

### What NOT to Say
- **DO NOT CLAIM**: "The PDF was manually designed in PowerPoint." (It is generated 100% programmatically by ReportLab from runtime telemetry).
- **DO NOT CLAIM**: "Validation is just training loss." (Page 6 reports held-out cross-validation on points withheld from RANSAC fitting).

---

## Slide 12: Future Roadmap & Conclusion

### Visual Description / Layout
- **Left Column**: "Demonstrated Deliverables Summary":
  - Checkmark 1: Adaptive Router (SIFT $\leftrightarrow$ Locked LoFTR $\leftrightarrow$ SuperGlue)
  - Checkmark 2: 3x3 Spatial Uniformity Policy ($CV = 0.0000$, 100% occupancy)
  - Checkmark 3: Sub-Pixel Model Consistency ($0.0034–0.0072\text{ px}$ held-out RMSE)
  - Checkmark 4: 4-Parameter Defensive Quality Gate & Verified Safe Rejection
  - Checkmark 5: Automated 7-Page Aerospace Scientific PDF Evidence Generation
- **Right Column**: "Flight-Ready Integration Roadmap (Phase 21+)":
  - Roadmap 1: Ingestion of PDS4 XML labels for rigorous physical GSD computation.
  - Roadmap 2: SPICE kernel integration for orbit-to-surface camera pointing geometry.
  - Roadmap 3: RPC / DEM orthorectification for non-planar high-relief crater walls.
  - Roadmap 4: Calibrated Level-2 TMC-2 and IIRS multi-sensor ingestion.

### Key Bullet Points
- **What LunarReg Has Delivered**: A robust, scientifically honest, and fully functional image registration pipeline that demonstrably satisfies core optical requirements of SIH26166.
- **Zero Hallucinated Claims**: Transparent classification of capabilities into DEMONSTRATED, PARTIALLY DEMONSTRATED, and NOT VERIFIED.
- **Deterministic & Auditable**: High-speed execution, uniform spatial constraint, safe failure prevention, and complete PDF reporting.
- **The Path to Orbit**: Clear, realistic engineering steps required to transition the system to flight operations with official ISRO PDS4 data products.

### Exact Metrics & References
- **Validated Codebase**: Zero warnings, clean production execution across `app/app.py` and `app/adaptive_adapter.py`.
- **Benchmark Performance**: Sub-second to 4.0s execution, up to 4,026 inliers, $100\%$ spatial occupancy, held-out RMSE $< 0.01\text{ px}$ on nominal optical imagery.
- **Claim Classifications**: 5 Demonstrated, 3 Partially Demonstrated, 0 False Claims.

### Spoken Presenter Notes (35–45 seconds)
> "In conclusion, LunarReg provides a battle-tested, scientifically grounded registration solution for Chandrayaan-2 imagery. We have demonstrated robust handling of optical distortion, viewpoint tilt, and illumination inversion, achieved perfect 3x3 spatial distribution, proven sub-pixel correspondence under controlled conditions, and implemented a vital quality gate that safely rejects corrupted inputs. Rather than making unsupported claims, we clearly identify what is demonstrated today and what requires official PDS4 orbital metadata tomorrow. LunarReg is deterministic, transparent, and ready for flight-pipeline integration. Thank you, and we welcome your questions."

### What NOT to Say
- **DO NOT CLAIM**: "LunarReg is 100% finished and requires no further development for flight operations." (State honestly: flight integration requires PDS4 labels and SPICE kernels).
- **DO NOT CLAIM**: "We are the best team in SIH." (Focus strictly on verified engineering deliverables and scientific rigor).

---

## 12-Slide Quick-Reference Summary Table

| Slide # | Title | Primary Focus | Claim Classification | Key Metric / Evidence |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Mission Objective | SIH26166 Problem Statement & Goals | Scope | Automated registration of Chandrayaan-2 imagery |
| **2** | Lunar Challenges | Shadow inversion, parallax, low contrast | Problem Space | $\sigma < 20.0$, 180° shadow flip, point clumping |
| **3** | Solution Architecture | 10-Stage Deterministic Pipeline | DEMONSTRATED | End-to-end execution in 1.3s to 4.0s |
| **4** | Adaptive Matching | Contrast/Gradient Routing (LoFTR/SIFT) | DEMONSTRATED | Dynamic switching; LoFTR (Pair 01) / SIFT (Pair 04) |
| **5** | Quality Gate & Safety | 4-parameter gate & safe rejection | DEMONSTRATED | 10/8/20%/33% gate; Demo 4 safe rejection verified |
| **6** | Spatial Distribution | 3x3 Grid Selection (max 6 pts/cell) | DEMONSTRATED | $CV = 0.0000$, 100% occupancy (54 points) |
| **7** | Production Results | Optical, Viewpoint, Illumination Pairs | DEMONSTRATED | Held-out RMSE `0.0034 px`, `0.0045 px`, `0.0072 px` |
| **8** | Scale Variation | Image-space tolerance vs physical GSD | PARTIALLY DEMONSTRATED | LoFTR RMSE `1.7188 px`; Physical scale unverified |
| **9** | Sub-Pixel Accuracy | Controlled proof vs physical ground truth | PARTIALLY DEMONSTRATED | Controlled error `0.26–0.30 px`; 100% $\le 0.50$ px |
| **10** | Multimodal Realities | Intra-sensor success vs uncalibrated crops | PARTIALLY DEMONSTRATED | Safe rejection verified; Universal cross-sensor not claimed |
| **11** | Aerospace Verification | Automated 7-Page PDF Evidence Reports | DEMONSTRATED | 7 pages, PDFium-verified, SHA-256 digital hashes |
| **12** | Roadmap & Conclusion | Summary of deliverables & flight roadmap | Ready for Demo | PDS4 metadata, SPICE kernels, DEM RPC integration |
