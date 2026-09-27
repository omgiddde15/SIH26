# Pre-Declared Diagnostic Plan: Mentor OHRC Production Correspondence Failure Analysis

**Document Status:** HARDENED PRE-DECLARED DIAGNOSTIC FRAMEWORK (PRE-EXECUTION)  
**Date:** September 23, 2026  
**Target Datasets:** Mentor Chandrayaan-2 OHRC Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`)  
**Pipeline State:** Frozen Production Pipeline (`adaptive_engine.py`, `registration_core.py`, LoFTR, SIFT, SuperGlue, RANSAC, Quality Gates all 100% Frozen)  

---

## 1. Scientific Governance & Diagnostic Methodology

### 1.1 Context & Baseline Observations
In the frozen production benchmark of the six mentor-provided Chandrayaan-2 datasets, the LunarReg production pipeline executed across all pairs with zero unhandled runtime crashes (`EXECUTION FAILURE` = 0) and zero invalid registered images (`Zero unsupported registrations were produced`). Every dataset was safely intercepted by the frozen correspondence-quality gate:
- **OHRC Pairs 1–4:** Initial inliers ranged from $6$ to $18$ ($1.72\%$ to $5.10\%$ inlier ratio, strictly below the $20.0\%$ threshold; spatial selection was bypassed and spatial occupancy was `NOT EVALUATED`).
- **IIRS Pair A:** $5$ initial inliers ($11.11\%$ inlier ratio; pre-rejection spatial occupancy $22.2\% < 33.3\%$).
- **IIRS Pair B:** $0$ candidates, $0$ initial inliers (matcher returned no candidate correspondences; spatial selection was bypassed and spatial occupancy was `NOT EVALUATED`).

**Official Benchmark Baseline Conclusion:**
> *"The frozen production system executed all six mentor-provided datasets without runtime failure. None of the six cases met the production correspondence-quality gate, so no registration was generated for these mentor cases. The system therefore demonstrated safe rejection, but successful mentor-dataset registration has not yet been demonstrated."*

### 1.2 Central Diagnostic Question
> **"Why does frozen production matching fail on mentor OHRC 5 m ↔ 5 m pairs despite verified effective scale and geographic overlap?"**

The previous metadata audit established that for OHRC Pairs 1 through 4, the moving source and reference rasters possess a verified effective pixel scale of **1:1** ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$). Therefore, coarse scale divergence alone cannot account for the low consensus. However, verified effective scale must not be conflated with "scale invariance achieved," nor does geographic footprint overlap guarantee visual correspondence. This plan provides the formal scientific protocol to investigate why consensus was not attained.

### 1.3 Core Methodological Paradigm
To avoid post-hoc rationalization and arbitrary confirmation bias, every diagnostic track adheres strictly to a 4-stage empirical progression:
$$\text{Measurement} \longrightarrow \text{Observed Evidence} \longrightarrow \text{Interpretation} \longrightarrow \text{Uncertainty / Limitation}$$

Under this paradigm:
1. **Measurement:** Concrete, reproducible mathematical or metadata extraction performed directly on canonical data files without modifying algorithms.
2. **Observed Evidence:** Objective numerical or categorical result obtained from the measurement.
3. **Interpretation:** Bounded scientific deduction strictly supported by the observed evidence.
4. **Uncertainty / Limitation:** Explicit declaration of what the measurement cannot determine, confounding variables, and boundary limits.

### 1.4 The "No-Causality-Without-Control" Rule
> **MANDATORY SCIENTIFIC CONSTRAINT:**  
> A measured statistical association or qualitative correlation (e.g., low inlier count occurring alongside large shadow fractions or high aspect ratios) **must not be presented as the confirmed cause of production rejection** unless a controlled experiment isolates that variable while holding all other factors constant. In the absence of an isolated control, observations must be described strictly as *potential contributing factors* or *consistent observations*, never definitive causal drivers.

### 1.5 Evidence Classification Taxonomy
Every piece of data, observation, and result recorded during this diagnostic must be tagged with one of six explicit evidence tiers:

1. **`VERIFIED METADATA`**: Extracted directly from official mission metadata files (e.g., Chandrayaan-2 PDS4 XML labels) or authenticated GeoTIFF header tags (`GeoTransform`, `PROJCS`).
2. **`DIRECT IMAGE MEASUREMENT`**: Computed directly from raster pixel values (e.g., intensity histograms, Shannon entropy, Sobel gradient norms, dimensions).
3. **`MATCHER TELEMETRY`**: Empirical runtime outputs logged during production execution (e.g., candidate coordinates, initial inlier count, RANSAC consensus inlier indices).
4. **`CONTROLLED EXPERIMENT`**: Results from an isolated test where exactly one variable was modified while all other inputs and pipeline settings were held invariant.
5. **`HEURISTIC`**: An empirical rule of thumb, uncalibrated proxy, or informal diagnostic indicator that provides qualitative guidance but lacks rigorous physical derivation.
6. **`INCONCLUSIVE`**: Data or measurements characterized by high variance, confounding variables, or insufficient signal-to-noise ratio to support a definitive conclusion.

### 1.6 Threshold Classification Taxonomy
To eliminate uncalibrated pass/fail declarations, all numerical criteria and thresholds utilized across the diagnostic tracks are classified into one of three rigorous categories:

- **`Verified / Reference Criterion`**: A standard derived from verified ground physics, exact mathematical definitions, authoritative mission metadata, or established planetary science descriptive definitions (e.g., measured GeoTIFF pixel scale matching verified metadata, coordinate reference system identity, exact mathematical definition of non-conformal stretching, standard descriptive definition of polar grazing illumination).
- **`Diagnostic Heuristic / Reference Tolerance`**: A widely used operational benchmark, reference tolerance band, or empirical threshold that serves as a useful diagnostic signpost but does not constitute a physical law (e.g., diagnostic pixel scale tolerance $|dx - 5.0| \le 0.01\text{ m/px}$, aspect ratio tolerance $\rho = 1.0 \pm 0.005$, Peak-to-Sidelobe Ratio $\text{PSR} \ge 10.0$, footprint overlap ratio $\ge 80\%$, convex hull area $> 40\%$).
- **`Criterion Requiring Calibration`**: A parameter whose specific numerical cutoff is uncalibrated for lunar polar surface conditions or deep feature matchers and must be interpreted descriptively rather than deterministically (e.g., Shannon entropy cutoff of $6.5\text{ bits}$, shadow cutoff of $< 10\text{ DN}$, solar azimuth difference $\Delta \theta > 90^\circ$, directional gradient angular difference $\Delta \theta_{\text{proxy}} < 15^\circ$).

### 1.7 Strict Production Safeguards
1. **Zero Algorithm Modifications:** `adaptive_engine.py`, `registration_core.py`, LoFTR model weights, SIFT detector settings, SuperGlue parameters, RANSAC mathematics, and validation split logic remain 100% locked and frozen.
2. **Zero Threshold Lowering:** The production correspondence-quality thresholds ($\ge 10$ candidates, $\ge 8$ inliers, $\ge 20\%$ inlier ratio, $\ge 33.3\%$ spatial occupancy, $3.0\text{ px}$ RANSAC tolerance) will **never** be adjusted or relaxed to manufacture an artificial pass.
3. **Read-Only Operation:** Canonical mentor files in `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\` are accessed strictly in read-only mode (`rasterio.open(..., 'r')`).
4. **Diagnostic Code Isolation:** All diagnostic routines will be developed and executed exclusively in `research/multimodal/mentor_benchmark/diagnostics/` or scratch directories. Under no circumstances will diagnostic logic be promoted to production without explicit governance.

---

## 2. Seven Pre-Declared Diagnostic Tracks

```
┌────────────────────────────────────────────────────────────────────────┐
│                   OHRC CORRESPONDENCE FAILURE INVESTIGATION             │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
  [TRACK A] Provenance        [TRACK B] Geographic        [TRACK C] Radiometric
  Scale & Metadata Invariance Coordinate Footprint &      Contrast & Dynamic Range
                              Mutual Bounding BBoxes      Preprocessing Response
         │                           │                           │
         ├───────────────────────────┼───────────────────────────┤
         │                           │                           │
  [TRACK D] Correspondence    [TRACK E] Native Aspect &   [TRACK F] Extreme Low-Sun
  Spatial Clustering vs       Resolution Resampling       Shadow Inversion &
  Featureless Expanse         Downsampling Distortion     Phase Angle Divergence
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                              [TRACK G] Mutual Terrain
                              Overlap & Crop Verification
```

---

### Track A: Image Provenance & Effective Scale Verification

- **Primary Phenomenon:** Spatial scale and cartographic projection fidelity.
- **Hypothesis:** Despite filenames indicating `5m` and nominal metadata reporting $5.0\text{ m/px}$, local spatial distortions, unmodeled optical distortion, or differing Map Projection definitions (e.g., Polar Stereographic vs. Equirectangular vs. unprojected camera frame) induce spatial scale variance across coordinates.
- **Baseline Evidence:**
  - Filename conventions designate files as `_at_5m.tif`.
  - Verified source native GSD is $0.26\text{ m/px}$; reference is $5.0\text{ m/px}$.
  - Initial inlier ratios in production benchmark were restricted between $1.72\%$ and $5.10\%$.
- **Proposed Diagnostic Measurement:**
  1. Read GeoTIFF tags (`rasterio`/`gdal`) for source and reference across `OHRC_PAIR_01` to `OHRC_PAIR_04`:
     - Coordinate Reference System (`CRS.to_wkt()`, `PROJCS`, `GEOGCS`).
     - Affine transformation matrix parameters (`GeoTransform`: $x_{\text{origin}}, dx, rx, y_{\text{origin}}, ry, dy$).
     - Pixel dimensions along $X$ and $Y$ axes.
  2. Compute pixel aspect ratio: $\rho = |dx / dy|$.
  3. Compute effective scale ratio: $S_{\text{eff}} = dx_{\text{src}} / dx_{\text{ref}}$.
- **Evidence Classification of Data Sources:**
  - Measured/verified mentor GeoTIFF pixel scale ($5.0\text{ m/px}$): **`VERIFIED METADATA`** when the actual dataset metadata shows the effective $5\text{ m/px}$ value.
  - GeoTIFF header tags (`GeoTransform`, `CRS`): **`VERIFIED METADATA`**.
  - Computed scale and aspect ratios: **`DIRECT IMAGE MEASUREMENT`**.
- **Threshold & Tolerance Classification:**
  - Measured mentor GeoTIFF pixel scale ($5.0\text{ m/px}$): **`Verified / Reference Criterion`** (when verified against authoritative dataset metadata).
  - Numerical tolerance band ($5.000\text{ m/px} \pm 0.01\text{ m/px}$): **`Diagnostic Heuristic / Reference Tolerance`** (operational reference tolerance band; not an independently cited mission specification).
  - Isotropic pixel aspect tolerance ($\rho = 1.000 \pm 0.005$): **`Diagnostic Heuristic / Reference Tolerance`** (operational reference tolerance; standard isotropic map projection expectation).
  - CRS string equivalence: **`Verified / Reference Criterion`** (Cartographic/geodetic definition).
- **Methodological Nuances & Scientific Distinctions:**
  - A verified 1:1 pixel scale ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$) verified via dataset metadata establishes *effective sampling resolution equivalence*. It does **not** prove that the pipeline has achieved scale invariance across arbitrary imagery, nor does it guarantee that no optical or terrain elevation distortion exists. The numerical tolerances ($0.01\text{ m/px}$ and $0.005$) are diagnostic reference tolerances rather than externally cited mission limits.
- **Falsification Triplet:**
  - *Supporting Observation:* Source and reference have mismatched projection definitions (e.g., one is Equirectangular, one is Polar Stereographic), anisotropic pixel scales ($dx \neq dy$), or measured ground resolution deviates from $5.0\text{ m/px}$ beyond diagnostic reference tolerance ($|dx - 5.0| > 0.01\text{ m/px}$).
  - *Weakening Observation:* Both rasters share identical, verified Polar Stereographic CRS definitions with measured pixel resolutions matching the verified $5.0\text{ m/px}$ metadata within reference tolerance ($|dx - 5.000| \le 0.01\text{ m/px}$).
  - *Inconclusive Observation:* GeoTIFF headers lack embedded CRS tags or contain generic local pixel coordinate systems, preventing geodetic verification from file headers alone.
- **Limitations & Uncertainties:**
  - Header metadata reflects nominal cartographic projection; it does not quantify terrain relief displacement caused by lunar crater topography (parallax displacement).

---

### Track B: Source-Reference Geographic Coordinate Overlap

- **Primary Phenomenon:** Geographic footprint intersection on the lunar surface.
- **Hypothesis:** Source and reference images possess non-overlapping, marginally overlapping, or offset geographic footprints, causing matchers to search for correspondences across mutually disjoint terrain.
- **Baseline Evidence:**
  - Datasets were provided by mentors as associated source/reference pairs.
  - Matcher returns hundreds of raw candidates ($98$ to $348$), but only $5$ to $6$ survive preliminary RANSAC. Candidate matches across disjoint regions represent random false-positive correlations.
- **Proposed Diagnostic Measurement:**
  1. Extract bounding box corner coordinates in projected map units ($X_{\min}, Y_{\min}, X_{\max}, Y_{\max}$) from GeoTIFF georeferencing.
  2. Compute geographic bounding box intersection polygon: $\mathcal{P}_{\text{inter}} = \mathcal{P}_{\text{src}} \cap \mathcal{P}_{\text{ref}}$.
  3. Calculate footprint overlap metrics:
     - Intersection over Union: $\text{IoU} = \frac{\text{Area}(\mathcal{P}_{\text{inter}})}{\text{Area}(\mathcal{P}_{\text{src}} \cup \mathcal{P}_{\text{ref}})}$
     - Source Coverage Fraction: $f_{\text{src\_in\_ref}} = \frac{\text{Area}(\mathcal{P}_{\text{inter}})}{\text{Area}(\mathcal{P}_{\text{src}})}$
     - Reference Coverage Fraction: $f_{\text{ref\_in\_src}} = \frac{\text{Area}(\mathcal{P}_{\text{inter}})}{\text{Area}(\mathcal{P}_{\text{ref}})}$
- **Evidence Classification of Data Sources:**
  - Georeferenced bounding coordinates: `VERIFIED METADATA`.
  - Computed intersection areas and IoU: `DIRECT IMAGE MEASUREMENT`.
- **Threshold Classification:**
  - $f_{\text{src\_in\_ref}} \ge 80.0\%$: **`Diagnostic Heuristic`** (Operational assumption of high visual overlap).
  - $f_{\text{src\_in\_ref}} < 20.0\%$: **`Diagnostic Heuristic`** (Operational indicator of severe field-of-view truncation).
- **Methodological Nuances & Scientific Distinctions:**
  - **Geographic overlap is NOT ground truth correspondence.** A high geographic overlap fraction (even $100\%$) establishes only that both cameras imaged the same nominal surface coordinates. It does **not** prove that distinctive terrain features are visible, that illumination permits matching, or that image correspondence can succeed.
- **Falsification Triplet:**
  - *Supporting Observation:* Bounding box intersection is null ($\text{Area} = 0$) or source coverage fraction is negligible ($f_{\text{src\_in\_ref}} < 10\%$).
  - *Weakening Observation:* Source bounding box is fully enclosed within reference bounding box ($f_{\text{src\_in\_ref}} \ge 95\%$).
  - *Inconclusive Observation:* Footprint overlap is moderate ($30\% - 70\%$) or GeoTIFF geotransforms exhibit unquantified absolute georeferencing bias (ephemeris pointing offset).
- **Limitations & Uncertainties:**
  - Nominal orbital georeferencing from SPICE kernels may contain pointing/ephemeris uncertainty of hundreds of meters, meaning nominal overlap does not guarantee exact pixel-level alignment.

---

### Track C: Radiometric Appearance & Contrast Dynamics

- **Primary Phenomenon:** Dynamic range, shadow truncation, and image entropy.
- **Hypothesis:** Deep feature matchers (LoFTR) trained on terrestrial photography require rich continuous gradient distributions and fail on lunar polar GeoTIFFs exhibiting extreme bimodal histograms (deep shadowed craters and saturated illuminated ridges).
- **Baseline Evidence:**
  - OHRC images display visible low-sun shadows and high-contrast specular rims.
  - Matcher candidate yields dropped from 348 to 98 across pairs.
- **Proposed Diagnostic Measurement:**
  1. Compute 256-bin normalized intensity histograms $p_k$ for source and reference rasters.
  2. Compute Shannon Entropy (information density):
     $$\mathcal{H} = -\sum_{k=0}^{255} p_k \log_2(p_k + \epsilon)$$
  3. Measure deep shadow fraction: $F_{\text{shadow}} = \sum_{k=0}^{9} p_k$ (pixels with $\text{DN} < 10$).
  4. Measure saturated highlight fraction: $F_{\text{sat}} = \sum_{k=246}^{255} p_k$ (pixels with $\text{DN} > 245$).
  5. Compute median local gradient magnitude using $3\times3$ Sobel filters.
- **Evidence Classification of Data Sources:**
  - Raster pixel values: `DIRECT IMAGE MEASUREMENT`.
  - Computed histograms, entropy, and shadow fractions: `DIRECT IMAGE MEASUREMENT`.
- **Threshold Classification:**
  - Shannon Entropy value: **`Criterion Requiring Calibration`** (Descriptive metric; no established physical cutoff exists for deep matchers on lunar regolith).
  - Shadow fraction $F_{\text{shadow}} > 20\%$: **`Criterion Requiring Calibration`** (Descriptive diagnostic heuristic; uncalibrated).
  - Saturation fraction $F_{\text{sat}} > 10\%$: **`Criterion Requiring Calibration`** (Descriptive diagnostic heuristic; uncalibrated).
- **Methodological Nuances & Scientific Distinctions:**
  - These radiometric values must be treated strictly as **descriptive diagnostics**. In the absence of a controlled benchmark isolating entropy variations on lunar imagery, specific numerical cutoffs (e.g., $6.5\text{ bits}$) must not be asserted as calibrated physical boundaries.
- **Falsification Triplet:**
  - *Supporting Observation:* Both images exhibit severe histogram truncation with $> 50\%$ of pixels collapsed into pure black shadow ($\text{DN} < 10$) and Shannon entropy $< 4.0\text{ bits}$.
  - *Weakening Observation:* Both source and reference rasters display smooth, well-distributed bell-shaped histograms spanning the full dynamic range, with shadow fraction $< 5\%$ and entropy $> 7.2\text{ bits}$.
  - *Inconclusive Observation:* Entropy is intermediate ($5.0 - 6.5\text{ bits}$) or shadow fractions differ moderately between source and reference.
- **Limitations & Uncertainties:**
  - Global entropy does not capture local spatial frequency; an image may have high global entropy due to noise while lacking distinct structural landmarks.

---

### Track D: Correspondence Spatial Distribution & Clustering

- **Primary Phenomenon:** 2D spatial arrangement and geometric conditioning of candidate correspondences.
- **Hypothesis:** Candidate correspondences returned by the matcher are tightly clustered along a localized linear edge or tiny high-contrast feature, creating a degenerate geometric configuration that destabilizes homography estimation.
- **Baseline Evidence:**
  - `OHRC_PAIR_01`: 348 candidates produced only 6 inliers ($1.72\%$).
  - `OHRC_PAIR_02`: 221 candidates produced only 5 inliers ($2.26\%$).
  - Spatial occupancy checks were bypassed because $N_{\text{init\_inliers}} < 8$.
- **Proposed Diagnostic Measurement:**
  1. Extract raw 2D pixel coordinates of all candidate matches: $(x_i^{\text{src}}, y_i^{\text{src}})$ and $(x_i^{\text{ref}}, y_i^{\text{ref}})$.
  2. Compute 2D convex hull area $\mathcal{A}_{\text{hull}}$ of candidate points on source and reference planes relative to total image area.
  3. Evaluate candidate spatial dispersion using normalized coordinate variance:
     $$\sigma_{xy}^2 = \frac{\text{Var}(x)}{W^2} + \frac{\text{Var}(y)}{H^2}$$
  4. Perform collinearity analysis via Principal Component Analysis (ratio of secondary to primary singular value $\lambda_2 / \lambda_1$).
  5. Inspect the spatial distribution of the small subset of consensus inliers ($N \le 6$) separately from the raw candidates.
- **Evidence Classification of Data Sources:**
  - Matcher candidate coordinates: `MATCHER TELEMETRY`.
  - Convex hull, variance, and singular value ratios: `DIRECT IMAGE MEASUREMENT`.
- **Threshold Classification:**
  - Convex hull area ratio $\mathcal{A}_{\text{hull}} / \mathcal{A}_{\text{img}} > 40\%$: **`Diagnostic Heuristic`** (Reference indicator of broad 2D dispersion).
  - Collinearity ratio $\lambda_2 / \lambda_1 < 0.05$: **`Diagnostic Heuristic`** (Indicator of degenerate 1D line arrangement).
  - Spatial Occupancy Threshold ($\ge 33.3\%$ across $3\times3$ grid): **`Verified / Reference Criterion`** (Frozen production quality gate specification).
- **Methodological Nuances & Scientific Distinctions:**
  - **Strict Metric Separation:** Candidate count ($N_{\text{cand}}$), candidate spatial dispersion, and initial RANSAC inlier count ($N_{\text{init\_inliers}}$) are three distinct operational stages.
  - **No Post-Selection Explanations for Pre-Selection Failures:** Because the production pipeline failed at the initial inlier consensus stage ($N_{\text{init\_inliers}} < 8$), spatial selection was **bypassed**. Spatial occupancy was **`NOT EVALUATED`** and must never be reported as `0.0%` or used retroactively to explain why the pre-selection gate failed.
- **Falsification Triplet:**
  - *Supporting Observation:* Candidate matches have an extreme aspect ratio or collinearity ratio $\lambda_2 / \lambda_1 < 0.01$, or occupy $< 2\%$ of the image surface area.
  - *Weakening Observation:* Candidate matches are broadly dispersed across $> 60\%$ of the image frame with $\lambda_2 / \lambda_1 > 0.35$.
  - *Inconclusive Observation:* Candidates are dispersed over an intermediate area ($15\% - 35\%$) but RANSAC inlier consensus fails independently of distribution.
- **Limitations & Uncertainties:**
  - Candidate distribution reflects where the deep neural network found correlation; it does not measure whether those visual features represent genuine co-located physical landmarks.

---

### Track E: Native Image Aspect Ratio & Downsampling Distortion

- **Primary Phenomenon:** Geometric aspect distortion and anisotropic resampling.
- **Hypothesis:** Severe native aspect ratio disparities between source (e.g., $624 \times 4872$, $1:7.8$) and reference (e.g., $5916 \times 4232$, $1.4:1$) introduce non-uniform scaling or severe downsampling compression during matcher preprocessing, destroying the isotropic geometry required for feature extraction.
- **Baseline Evidence:**
  - Native pixel dimensions show extreme elongation:
    - `OHRC_PAIR_01`: Source $624 \times 4872$ vs. Reference $5916 \times 4232$ (Aspect ratio ratio $\approx 5.5\times$).
    - `OHRC_PAIR_04`: Reference $3164 \times 6322$ vs. Source $552 \times 4649$.
  - Memory-safe tiling and workspace constraints downscaled imagery to fit memory budgets.
- **Proposed Diagnostic Measurement:**
  1. Record native pixel dimensions ($W, H$) for source and reference.
  2. Compute native aspect ratios: $\text{AR} = \max(W, H) / \min(W, H)$.
  3. Compute aspect ratio divergence:
     $$\delta_{\text{AR}} = \frac{\max(\text{AR}_{\text{src}}, \text{AR}_{\text{ref}})}{\min(\text{AR}_{\text{src}}, \text{AR}_{\text{ref}})}$$
  4. Measure effective downscaling factors along $X$ and $Y$ applied by the matcher loader ($s_x = W_{\text{model}} / W_{\text{orig}}, s_y = H_{\text{model}} / H_{\text{orig}}$).
  5. Compute anisotropic scaling factor: $\alpha = |s_x - s_y| / \max(s_x, s_y)$.
- **Evidence Classification of Data Sources:**
  - Header dimensions: `VERIFIED METADATA`.
  - Computed aspect ratios and downsampling factors: `DIRECT IMAGE MEASUREMENT`.
- **Threshold Classification:**
  - Aspect ratio divergence $\delta_{\text{AR}} > 3.0$: **`Diagnostic Heuristic`** (Operational indicator of severe dimensional mismatch).
  - Anisotropic scaling factor $\alpha = |s_x - s_y| / \max(s_x, s_y)$: **`Verified / Reference Criterion`** (Exact mathematical definition of non-conformal stretching).
- **Methodological Nuances & Scientific Distinctions:**
  - **Scale vs. Shape:** Distinguish physical pixel scale ($5.0\text{ m/px}$) from image-shape / aspect-ratio effects. Having a verified 1:1 ground sampling distance does **not** protect against distortion if an elongated strip is rescaled non-uniformly into a square neural network canvas.
  - **Nonzero Anisotropy Caveat:** While $\alpha > 0$ mathematically establishes non-conformal stretching, **any nonzero anisotropy is NOT automatically sufficient to explain matching failure**. Deep neural matchers and patch descriptors inherently possess tolerance to minor non-conformal deformation; failure can only be supported when anisotropy is severe ($\alpha \gg 0$) and directly isolates spatial descriptor breakdown under controlled comparison.
- **Falsification Triplet:**
  - *Supporting Observation:* Matcher input pipeline applies severe non-uniform resizing with $\alpha > 0.25$, substantially distorting circular craters into elongated ellipses prior to feature extraction.
  - *Weakening Observation:* Resizing is strictly isotropic ($\alpha = 0.00$) with letterboxing/padding, and aspect ratio divergence is minimal ($\delta_{\text{AR}} < 1.2$), or minor nonzero anisotropy is proven insufficient to degrade descriptor matching.
  - *Inconclusive Observation:* Resizing is isotropic, but uniform downscaling factor is extreme ($s < 0.15$), resulting in loss of high-frequency visual texture.
- **Limitations & Uncertainties:**
  - Aspect ratio analysis evaluates geometry; it does not measure whether the neural network's receptive field is invariant to linear strip inputs.

---

### Track F: Extreme Low-Sun Illumination & Solar Phase Angle Divergence

- **Primary Phenomenon:** Solar incidence angle, azimuth divergence, and cast shadow vectors.
- **Hypothesis:** Source and reference images were captured under substantially different solar azimuths. In lunar polar terrain where solar incidence is extreme ($84.9^\circ - 87.9^\circ$, sun elevation $< 5^\circ$), cast shadows extend for kilometers; inverted shadow vectors alter image gradients by $180^\circ$, causing standard feature descriptors to fail completely.
- **Baseline Evidence:**
  - Verified XML metadata for `OHRC_PAIR_01` source records Solar Elevation $2.11^\circ$ (Incidence $87.89^\circ$).
  - Verified XML metadata for `OHRC_PAIR_02` source records Solar Elevation $5.07^\circ$ (Incidence $84.93^\circ$).
  - Reference XML metadata was not provided by the mentor.
  - Benchmark summary noted: *"Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor."*
- **Proposed Diagnostic Measurement:**
  1. Compile authoritative illumination angles from verified XML files where available: Solar Elevation, Solar Incidence, and Solar Azimuth.
  2. For images lacking XML metadata (e.g., reference rasters), compute an **image-derived shadow direction proxy**:
     - Compute Sobel directional gradients across shadow-illuminated boundaries.
     - Form directional gradient orientation histogram $\Phi(\theta) \in [0, 360^\circ)$.
     - Extract dominant shadow projection angle $\theta_{\text{proxy}} = \arg\max_\theta \Phi(\theta)$.
  3. Compute apparent angular disparity between source and reference:
     $$\Delta \theta = \min(|\theta_{\text{src}} - \theta_{\text{ref}}|, 360^\circ - |\theta_{\text{src}} - \theta_{\text{ref}}|)$$
- **Evidence Classification of Data Sources:**
  - Source XML solar angles (Incidence, Elevation, Azimuth): **`VERIFIED METADATA`** (Extracted directly from authoritative PDS4 XML labels).
  - Image-derived shadow direction proxy ($\theta_{\text{proxy}}$): **`HEURISTIC`** (Image-derived gradient proxy; not verified against SPICE/ephemeris).
  - Disparity $\Delta \theta$: **`VERIFIED METADATA`** if both angles derive from verified XML; **`HEURISTIC`** if computed from image-derived shadow proxies.
- **Threshold Classification:**
  - Solar Incidence $> 80.0^\circ$: **`Verified / Reference Criterion`** (Descriptive planetary science reference definition for low-sun polar grazing illumination; **NOT a demonstrated matcher-failure threshold**).
  - Azimuth difference $\Delta \theta > 90^\circ$: **`Criterion Requiring Calibration`** (Descriptive indicator of severe shadow inversion; exact failure threshold on LoFTR is uncalibrated).
  - Proxy angular difference $\Delta \theta_{\text{proxy}} < 15^\circ$: **`Criterion Requiring Calibration`** (Descriptive heuristic).
- **Methodological Nuances & Scientific Distinctions:**
  - **Descriptive Reference vs. Failure Threshold:** Solar incidence $> 80^\circ$ is a standard descriptive planetary illumination classification identifying polar grazing conditions; **it is NOT a demonstrated matcher-failure threshold**. Deep matchers can match high-incidence pairs if illumination vectors and surface features align.
  - **No False Equivalence:** An image-derived shadow proxy must **never** be reported as the verified solar angle. It is an image-domain proxy that can be confounded by local crater wall slopes.
  - **Separate Reporting:** Metadata-derived solar angles (`VERIFIED METADATA`) must be reported in a separate table from image-derived proxy measurements (`HEURISTIC`).
  - **No Causality Without Control:** Even if $\Delta \theta \approx 180^\circ$, this correlation must not be stated as the sole causal driver of failure without a controlled experiment isolating illumination.
- **Falsification Triplet:**
  - *Supporting Observation:* Verified metadata or dominant shadow proxies establish near-orthogonal or opposing illumination ($\Delta \theta > 90^\circ$), with shadows falling in opposite directions across crater floors.
  - *Weakening Observation:* Verified solar azimuths or shadow proxies match within $\Delta \theta < 10^\circ$, showing nearly identical shadow geometry.
  - *Inconclusive Observation:* Reference image lacks XML metadata, and image-derived shadow proxy exhibits wide dispersion or low confidence due to uniform diffuse terrain.
- **Limitations & Uncertainties:**
  - Cast shadow length is a non-linear function of 3D topography ($L = h / \tan(\theta_{\text{elev}})$); 2D image gradients cannot reconstruct 3D terrain elevation without a Digital Elevation Model (DEM).

---

### Track G: Mutual Terrain Overlap & Sub-Window Crop Verification

- **Primary Phenomenon:** Existence and location of shared visual surface features.
- **Hypothesis:** Moving source images are narrow sub-window crops located in a different sector of the reference image than expected, or cover such a small visual area that coarse-scale feature matchers fail to lock onto shared terrain.
- **Baseline Evidence:**
  - Source rasters represent small dimensional strips ($624 \times 4872$) relative to massive reference rasters ($5916 \times 4232$), covering as little as $\approx 12\%$ of reference area.
- **Proposed Diagnostic Measurement:**
  1. Construct a multi-scale Gaussian image pyramid ($4\times, 8\times, 16\times$ downscaling).
  2. Perform sliding-window Normalized Cross-Correlation (NCC) or Phase Correlation across the reference frame using the downscaled source template.
  3. Extract correlation response surface $\mathcal{C}(x, y)$ and locate global peak $(x^*, y^*)$.
  4. Compute Peak-to-Sidelobe Ratio (PSR):
     $$\text{PSR} = \frac{\max(\mathcal{C}) - \mu_{\mathcal{C}}}{\sigma_{\mathcal{C}}}$$
     where $\mu_{\mathcal{C}}$ and $\sigma_{\mathcal{C}}$ are the mean and standard deviation of the correlation surface outside an exclusion window around the peak.
- **Evidence Classification of Data Sources:**
  - Multi-scale correlation surface: `DIRECT IMAGE MEASUREMENT`.
  - Peak-to-Sidelobe Ratio (PSR): `HEURISTIC`.
- **Threshold Classification:**
  - $\text{PSR} \ge 10.0$: **`Diagnostic Heuristic`** (Standard signal-processing reference indicating a prominent correlation peak; not ground-truth proof).
  - $\text{PSR} < 5.0$: **`Diagnostic Heuristic`** (Indicator of an ambiguous or noise-dominated correlation surface).
- **Methodological Nuances & Scientific Distinctions:**
  - **Correlation is NOT Registration Ground Truth:** A high PSR indicates strong visual pattern similarity at reduced resolution; it does **not** prove that the images are correctly registered at pixel level or that fine-scale correspondence will succeed.
- **Falsification Triplet:**
  - *Supporting Observation:* Multi-scale correlation surface is completely flat or noisy across all scales ($\text{PSR} < 4.0$), with no distinct peak anywhere in the reference frame.
  - *Weakening Observation:* A sharp, isolated correlation peak appears with $\text{PSR} > 15.0$ at coordinates consistent with the nominal georeferenced bounding box.
  - *Inconclusive Observation:* Multiple competing peaks of similar magnitude appear ($\text{PSR} \approx 6.0 - 8.0$), characteristic of repetitive, self-similar cratered regolith.
- **Limitations & Uncertainties:**
  - Standard NCC assumes intensity correlation under linear radiometric changes; it can fail completely in the presence of non-linear shadow inversions even when identical terrain is imaged.

---

## 3. Supporting Methodology Matrix

| Track | Primary Measurement | Data Source | Evidence Tier | Null / Diagnostic Hypothesis | Supporting Observation | Weakening Observation | Limitations & Uncertainties |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | GeoTIFF Affine Transform & CRS | GeoTIFF Headers (`rasterio`) & XML | `VERIFIED METADATA` / `DIRECT MEASUREMENT` | Projection or pixel scale mismatch across coordinate axes. | Discrepant CRS strings, anisotropic pixel size ($dx \neq dy$), or scale deviating from verified $5.0\text{ m/px}$. | Identical Polar Stereographic CRS; pixel scale $5.0\text{ m/px}$ matching verified metadata within diagnostic reference tolerance $|dx - 5.0| \le 0.01\text{ m/px}$. | Header metadata reflects nominal cartography; does not capture terrain parallax. |
| **Track B** | Projected Bounding Polygon IoU | GeoTIFF Headers & Georeference | `VERIFIED METADATA` / `DIRECT MEASUREMENT` | Disjoint or negligible geographic ground footprint overlap. | Bounding box intersection is null or coverage fraction $f_{\text{src\_in\_ref}} < 10\%$. | Source footprint fully enclosed within reference ($f_{\text{src\_in\_ref}} \ge 95\%$). | Orbital ephemeris pointing bias may shift actual footprint relative to nominal tags. |
| **Track C** | Shannon Entropy & Histogram Profile | Raster Pixel Arrays | `DIRECT IMAGE MEASUREMENT` | Severe dynamic range collapse (extreme shadows / saturation). | Shannon entropy $< 4.0\text{ bits}$; shadow fraction $> 50\%$. | Broad multimodal histogram; entropy $> 7.2\text{ bits}$; shadows $< 5\%$. | Global entropy does not measure local spatial frequency or distinctive structural anchors. |
| **Track D** | 2D Candidate Coordinates Convex Hull & SVD | Matcher Runtime Telemetry | `MATCHER TELEMETRY` / `DIRECT MEASUREMENT` | Degenerate 1D linear clustering or extreme localized grouping. | Convex hull area $< 2\%$ of image area; collinearity ratio $\lambda_2 / \lambda_1 < 0.01$. | Broad candidate dispersion across $> 60\%$ of frame; $\lambda_2 / \lambda_1 > 0.35$. | High candidate dispersion does not imply that correspondences are true physical matches. |
| **Track E** | Aspect Ratio Divergence & Resampling Anisotropy | Raster Dimensions & Loader Code | `VERIFIED METADATA` / `DIRECT MEASUREMENT` | Geometric distortion introduced by non-uniform image resizing. | Loader resizes non-uniformly ($\alpha > 0.25$), turning craters into elongated ellipses. | Resizing is strictly isotropic ($\alpha = 0.00$); aspect divergence $\delta_{\text{AR}} < 1.2$. | Evaluates input geometry; does not measure neural network receptive field tolerance. Nonzero anisotropy is not automatically sufficient to explain failure. |
| **Track F** | XML Solar Angles & Gradient Shadow Proxy | PDS4 XML Labels & Pixel Gradients | `VERIFIED METADATA` / `HEURISTIC` | Extreme shadow inversion caused by opposing solar azimuths. | Verified XML or shadow proxy indicates angular difference $\Delta \theta > 90^\circ$. | Verified XML or shadow proxy confirms matching solar azimuths ($\Delta \theta < 10^\circ$). | Grazing incidence ($> 80^\circ$) is a descriptive illumination definition, not a demonstrated matcher failure threshold; shadow proxy is an image-derived heuristic. |
| **Track G** | Multiscale Sliding Template NCC / PSR | Downscaled Rasters | `DIRECT IMAGE MEASUREMENT` / `HEURISTIC` | Moving image is not present within reference raster field of view. | Correlation surface is flat/diffuse with no distinct peak ($\text{PSR} < 4.0$). | Prominent, isolated correlation peak with $\text{PSR} > 15.0$ at expected coordinates. | NCC assumes linear intensity similarity; can fail under non-linear shadow changes despite true co-location. |

---

## 4. Comprehensive Falsification Logic & Decision Boundaries

To maintain scientific integrity, this section explicitly establishes the decision boundaries for each track before any diagnostic code is executed.

```
                  ┌─────────────────────────────────────┐
                  │      DIAGNOSTIC MEASUREMENT         │
                  └──────────────────┬──────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   SUPPORTING    │         │    WEAKENING    │         │  INCONCLUSIVE   │
│   OBSERVATION   │         │   OBSERVATION   │         │   OBSERVATION   │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ Corroborates    │         │ Falsifies       │         │ Insufficient    │
│ hypothesis as   │         │ hypothesis as   │         │ signal; retains │
│ potential factor│         │ primary driver  │         │ hypothesis open │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### Track A: Scale & Projection Invariance
- **Weakens Hypothesis:** Both source and reference files contain identical Polar Stereographic CRS strings and pixel scales matching verified metadata ($5.0\text{ m/px}$) within operational diagnostic reference tolerance:
  $$|dx_{\text{src}} - 5.000| \le 0.01\text{ m}, \quad |dy_{\text{src}} - 5.000| \le 0.01\text{ m}, \quad dx_{\text{src}} == dx_{\text{ref}}$$
  *Conclusion:* Scale and projection mismatch is **falsified as the root cause**.
- **Supports Hypothesis:** CRS strings differ (e.g., mismatched central meridian or projection type) or pixel scales are anisotropic ($|dx - dy| / dx > 0.02$).
- **Remains Inconclusive:** Files lack standard GeoTIFF projection tags and rely entirely on unprojected raster space.

### Track B: Geographic Coordinate Overlap
- **Weakens Hypothesis:** Calculated bounding polygon intersection demonstrates that $\ge 90\%$ of the source footprint is enclosed within the reference raster:
  $$f_{\text{src\_in\_ref}} = \frac{\text{Area}(\mathcal{P}_{\text{src}} \cap \mathcal{P}_{\text{ref}})}{\text{Area}(\mathcal{P}_{\text{src}})} \ge 0.90$$
  *Conclusion:* Geographic non-overlap is **falsified as the root cause**.
- **Supports Hypothesis:** Footprints are disjoint ($\mathcal{P}_{\text{src}} \cap \mathcal{P}_{\text{ref}} = \emptyset$) or overlap fraction $f_{\text{src\_in\_ref}} < 0.20$.
- **Remains Inconclusive:** Overlap fraction is moderate ($0.20 \le f_{\text{src\_in\_ref}} < 0.70$) combined with unquantified SPICE pointing uncertainty.

### Track C: Radiometric Appearance & Contrast Dynamics
- **Weakens Hypothesis:** Rasters exhibit rich continuous histograms across the dynamic range with Shannon entropy $\mathcal{H} > 7.0\text{ bits}$ and shadow fraction $F_{\text{shadow}} < 10\%$.
  *Conclusion:* Global dynamic range collapse is **falsified as the root cause**.
- **Supports Hypothesis:** Severe histogram bimodal truncation with shadow fraction $F_{\text{shadow}} > 45\%$ and Shannon entropy $\mathcal{H} < 4.5\text{ bits}$.
- **Remains Inconclusive:** Intermediate entropy ($5.0 \le \mathcal{H} \le 6.5\text{ bits}$) where local high-contrast features may exist despite moderate global shadows.

### Track D: Correspondence Spatial Distribution
- **Weakens Hypothesis:** Raw candidate correspondences are uniformly dispersed over $> 50\%$ of the image surface area with singular value ratio $\lambda_2 / \lambda_1 > 0.30$.
  *Conclusion:* 1D collinear or localized feature clustering is **falsified as the root cause**.
- **Supports Hypothesis:** Candidates are clustered in a single tight patch ($\mathcal{A}_{\text{hull}} / \mathcal{A}_{\text{img}} < 0.05$) or along a linear edge ($\lambda_2 / \lambda_1 < 0.02$).
- **Remains Inconclusive:** Candidates occupy $10\% - 30\%$ of the frame, leaving it ambiguous whether geometric distribution alone prevented RANSAC convergence.

### Track E: Aspect Ratio & Resampling Distortion
- **Weakens Hypothesis:** Resizing in the matcher data loader is strictly isotropic ($\alpha = 0.00$) with conformal padding, and aspect ratio divergence $\delta_{\text{AR}} \le 1.25$, or minor nonzero anisotropy is proven insufficient to degrade descriptor matching under controlled comparison.
  *Conclusion:* Resampling aspect distortion is **falsified as the root cause**. (Note: minor nonzero anisotropy is not automatically sufficient to explain failure; severe anisotropic distortion $\alpha \gg 0$ is required to support the hypothesis).
- **Supports Hypothesis:** Matcher data loader resizes images directly to a square grid ($W_{\text{model}} = H_{\text{model}}$) without preserving aspect ratio ($\alpha > 0.30$).
- **Remains Inconclusive:** Resizing is isotropic, but uniform downscaling factor is extreme ($s < 0.15$), compressing high-frequency lunar texture.

### Track F: Extreme Low-Sun Illumination Divergence
- **Weakens Hypothesis:** Verified solar azimuths or dominant shadow vectors match within $\Delta \theta < 15^\circ$, and solar elevation angles differ by $< 2^\circ$.
  *Conclusion:* Illumination angle divergence is **falsified as the root cause**. (Note: Solar incidence $> 80^\circ$ is descriptive planetary context, NOT a demonstrated matcher-failure threshold; failure attribution requires demonstrating opposing shadow vectors under controlled comparison).
- **Supports Hypothesis:** Verified solar azimuths or dominant shadow vectors reveal near-orthogonal or opposing illumination ($\Delta \theta > 75^\circ$).
- **Remains Inconclusive:** Reference image lacks XML metadata, and image-derived shadow proxies yield diffuse, multi-modal, or low-confidence distributions.

### Track G: Mutual Terrain Overlap & Sub-Window Crop Verification
- **Weakens Hypothesis:** Multiscale template correlation produces a distinct, unambiguous correlation peak with $\text{PSR} \ge 12.0$ at pixel coordinates matching nominal georeferencing.
  *Conclusion:* Absence of shared terrain in the reference frame is **falsified**.
- **Supports Hypothesis:** Multiscale template correlation produces a completely flat or noise-dominated response surface with $\text{PSR} < 4.0$ across all tested scales.
- **Remains Inconclusive:** Correlation yields multiple ambiguous peaks with moderate $\text{PSR}$ ($5.0 \le \text{PSR} \le 9.0$), typical of self-similar cratered terrain.

---

## 5. Competing Alternative Explanations (Pre-Measurement Analysis)

In strict accordance with scientific governance, no single root cause may be selected prior to empirical measurement. The diagnostic framework explicitly evaluates seven competing alternative hypotheses:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   COMPETING ALTERNATIVE EXPLANATIONS                   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
    ┌────────────────┬───────────────┼───────────────┬────────────────┐
    │                │               │               │                │
┌───┴──────────┐ ┌───┴──────────┐ ┌──┴──────────┐ ┌──┴──────────┐ ┌───┴──────────┐
│ 1. Incomplete│ │ 2. Shadow    │ │ 3. Modality │ │ 4. Resampling│ │ 5. Lack of   │
│ Geographic   │ │ Inversion /  │ │ & Radiometry│ │ & Downscaling│ │ Distinctive │
│ Overlap      │ │ Solar Phase  │ │ Mismatch    │ │ Distortion   │ │ Structure    │
└───┬──────────┘ └───┬──────────┘ └──┬──────────┘ └──┬──────────┘ └───┬──────────┘
    │                │               │               │                │
    └────────────────┼───────────────┴───────────────┼────────────────┘
                     │                               │
             ┌───────┴───────────────┐       ┌───────┴───────────────┐
             │ 6. Matcher Coarse     │       │ 7. Geodetic & SPICE   │
             │ Localization Error    │       │ Pointing Uncertainty  │
             └───────────────────────┘       └───────────────────────┘
```

1. **Incomplete Geographic Overlap:**
   - *Description:* The mentor-provided moving and reference images do not cover the same patch of lunar ground, or share only an insignificant border strip ($< 10\%$).
   - *Plausibility:* Medium. Source rasters have dimensions of $624 \times 4872$, whereas reference rasters span $5916 \times 4232$; if the crop was extracted incorrectly, visual overlap may be minimal.

2. **Extreme Illumination & Shadow Inversion:**
   - *Description:* The lunar South Pole terrain was imaged under opposing solar azimuths at grazing incidence ($> 85^\circ$). Deep shadows that appear on the southern wall of a crater in the source appear on the northern wall in the reference, completely inverting image gradients.
   - *Plausibility:* High. Polar imagery is notoriously susceptible to shadow-driven feature inversion.

3. **Radiometric & Cross-Sensor Appearance Discrepancies:**
   - *Description:* The reference raster underwent unmodeled contrast stretching, tone-mapping, or radiometric calibration differing fundamentally from the raw moving raster.
   - *Plausibility:* Medium. Even within OHRC, differences in processing levels (V1.0 vs. V2.0, calibrated radiance vs. uncalibrated DN) alter texture distributions.

4. **Preprocessing & Resampling Distortion:**
   - *Description:* The pipeline's memory guard or matcher input loader downscaled or stretched the elongated image ($1:7.8$ aspect ratio) into a square canvas, destroying local feature aspect ratios.
   - *Plausibility:* Medium-High. Neural matchers require specific canvas shapes; non-conformal resizing severely corrupts spatial geometry.

5. **Insufficient Distinctive Structure (Featureless Regolith):**
   - *Description:* The mutual ground area covers smooth, uncratered, or shadowed regolith devoid of high-frequency visual landmarks at $5\text{ m/px}$ resolution.
   - *Plausibility:* Medium. Lunar polar plains between large craters often exhibit uniform low-contrast textures.

6. **Correspondence Localization Errors (Deep Feature Aliasing):**
   - *Description:* LoFTR's coarse-to-fine transformer architecture relies on $8\times$ downscaled feature maps ($1/8$ resolution). In repetitive crater fields, attention maps produce multi-modal probability distributions, causing coarse match coordinates to latch onto visually identical nearby craters.
   - *Plausibility:* Medium-High. Self-similarity across lunar crater fields frequently induces false-positive consensus clusters that fail fine RANSAC verification.

7. **Metadata & Footprint Uncertainty (Orbital Pointing Error):**
   - *Description:* The embedded GeoTransform or XML coordinates contain uncorrected orbital pointing offsets (several kilometers), causing geodetic overlap calculations to appear valid when the rasters are physically displaced.
   - *Plausibility:* Low-Medium. Chandrayaan-2 SPICE kernels provide high pointing accuracy, but unrefined lunar polar ephemeris can contain hundreds of meters of residual jitter.

---

## 6. Execution Protocol & Verification Constraints

### 6.1 Pre-Execution Stance
> **IMPORTANT:**  
> This diagnostic plan is currently in **PRE-EXECUTION STANCE**. No diagnostic code, scripts, or experiments shall be executed during this step. Approval of this hardened plan establishes the scientific protocol; execution will be initiated only upon subsequent explicit user direction.

### 6.2 Strict Environmental Constraints (When Approved for Execution)
1. **Isolated Workspace:** All diagnostic routines must be written to:
   `c:\Users\Dell\Videos\SIH26_Lunar_Registration\research\multimodal\mentor_benchmark\diagnostics\`
2. **Read-Only Access:** The canonical mentor data directory:
   `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\`
   must be accessed exclusively via read-only interfaces. No write operations, temporary cache files, or file modifications shall occur in the mentor data tree.
3. **No Production Importation:** Diagnostic scripts will not import or modify `adaptive_engine.py` or production pipeline modules. They will execute standalone mathematical routines using standard scientific libraries (`numpy`, `rasterio`, `scipy`, `cv2`).

### 6.3 Required Deliverables Upon Execution
When the diagnostic is executed, the following standardized artifacts must be generated:
1. `research/multimodal/mentor_benchmark/diagnostics/diagnostic_measurements.json`: Machine-readable repository containing all quantitative measurements, evidence tiers, and threshold classifications.
2. `research/multimodal/mentor_benchmark/mentor_failure_diagnostic_report.md`: Formal analytical report synthesizing observations across Tracks A–G, explicitly reporting falsified hypotheses, corroborated factors, remaining uncertainties, and methodological limitations.

---

## 7. Document Verification & Integrity Audit

- **Production Code Status:** 100% Locked and Frozen.  
  `adaptive_engine.py`, `registration_core.py`, LoFTR model weights, SIFT detector settings, SuperGlue parameters, RANSAC mathematics, validation seeds 1–5, and quality gate thresholds remain completely untouched.
- **Threshold Integrity:** Zero thresholds relaxed. No artificial passing mechanisms introduced.
- **Scientific Standard:** Every measurement is mapped through `Measurement -> Observed Evidence -> Interpretation -> Uncertainty/Limitation`, with explicit Evidence Classifications and Threshold Categorizations.
