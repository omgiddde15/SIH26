# Comprehensive Scientific Report: Mentor Failure Diagnostic Execution

**Document Status:** FORMAL RESEARCH & DIAGNOSTIC REPORT (SCIENTIFIC INTERPRETATION REVISION)  
**Execution Date:** September 23, 2026  
**Execution Order:** Track A → Track B → Track E → Track C → Track F → Track D → Track G  
**Target Datasets:** Mentor Chandrayaan-2 Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`, `IIRS_PAIR_A`, `IIRS_PAIR_B`)  
**Comparison Controls:** Historical Pair 05 (North Polar OHRC, Sub-pixel Verified) & Historical Pair 02 (Extreme Illumination Rejection)  
**Pipeline State:** Frozen Production Pipeline (`adaptive_engine.py`, `registration_core.py`, LoFTR weights, SIFT/SuperGlue settings, RANSAC thresholds, and Quality Gates 100% Frozen)  

---

## 1. Executive Summary & Diagnostic Governance

### 1.1 Context
In the frozen production benchmark, all six mentor-provided Chandrayaan-2 datasets executed without software crashes (`EXECUTION FAILURE` = 0) and without generating invalid registered outputs (`Zero unsupported registrations were produced`). However, none of the six cases met the production correspondence-quality gate ($\ge 8$ inliers, $\ge 20\%$ initial inlier ratio, $\ge 33.3\%$ spatial occupancy). Every case was intercepted as a **`SAFE REJECTION`**.

This diagnostic was executed to investigate:
> **"Why does frozen production matching fail on mentor OHRC 5 m ↔ 5 m pairs despite verified effective scale and geographic overlap?"**

### 1.2 Mandatory Scientific Governance
- **Strict Read-Only Execution:** Canonical mentor files in `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\` were accessed strictly via read-only interfaces.
- **Zero Production Changes:** No algorithms, thresholds, weights, or routing heuristics were altered or relaxed.
- **The "No-Causality-Without-Control" Rule:** Observed associations are reported strictly as *consistent with* or *potential contributing factors*, never asserted as a *proven cause* or *root cause* in the absence of an isolated controlled experiment.
- **Strict Evidence Classification:** Every empirical finding is tagged with its verified tier: `VERIFIED METADATA`, `DIRECT IMAGE MEASUREMENT`, `MATCHER TELEMETRY`, `CONTROLLED EXPERIMENT`, `HEURISTIC`, or `INCONCLUSIVE`.

---

## 2. Comparison Baseline: Mentor Cases vs. Historical Controls

To establish rigorous scientific context without conflating datasets, the failed mentor cases are evaluated against two benchmarked historical reference cases from LunarReg research records:
1. **Historical Pair 05 (Positive Control):** Controlled real Chandrayaan-2 OHRC North Polar pair with verified sub-pixel accuracy (0.4412 px reprojection RMSE, 0.4623 px held-out RMSE, 9/9 occupancy, 38.25% inliers). Both images shared near-identical flight trajectories and solar azimuths ($\Delta \theta < 1.5^\circ$).
2. **Historical Pair 02 (Negative Control):** Controlled prototype case featuring extreme shadow inversion ($\Delta \theta > 110^\circ$), resulting in safe rejection (2.70% inlier ratio, spatial occupancy not evaluated).

| Benchmark / Dataset | Matcher Mode | Raw Candidates | Initial Inliers | Inlier Ratio | Spatial Occupancy | Final Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Historical Pair 05 (Positive Control)** | LoFTR (Full) | 3,712 | 1,420 | **38.25%** | **100.0% (9/9 cells)** | **VALIDATED PROTOTYPE (Sub-pixel Demonstrated)** |
| **Historical Pair 02 (Negative Control)** | LoFTR (Full) | 444 | 12 | **2.70%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |
| **OHRC_PAIR_01 (Mentor)** | Tiled LoFTR | 348 | 6 | **1.72%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |
| **OHRC_PAIR_02 (Mentor)** | Standard LoFTR | 221 | 5 | **2.26%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |
| **OHRC_PAIR_03 (Mentor)** | Standard LoFTR | 161 | 5 | **3.11%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |
| **OHRC_PAIR_04 (Mentor)** | Standard LoFTR | 98 | 5 | **5.10%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |
| **IIRS_PAIR_A (Mentor)** | Standard LoFTR | 45 | 5 | **11.11%** | **22.2% (Pre-Rejection)** | **SAFE REJECTION (Below Quality Gate)** |
| **IIRS_PAIR_B (Mentor)** | Standard LoFTR | 0 | 0 | **0.00%** | **NOT EVALUATED (Bypassed)** | **SAFE REJECTION (Below Quality Gate)** |

---

## 3. Detailed Per-Track Diagnostic Findings (A → B → E → C → F → D → G)

---

### TRACK A: Provenance & Effective Scale Verification

#### 1. Measurement Methodology
- Extracted GeoTIFF tags (`ModelPixelScaleTag` 33550, `ModelTiepointTag` 33922, `GeoKeyDirectoryTag` 34735, `GeoDoubleParamsTag` 34736) using Pillow TIFF inspection across all 6 pairs.
- Verified CRS parameters from GeoKey 34735/34736: Projection = Polar Stereographic (GeoKey 3075 = 7), Standard Parallel = $-90.0^\circ$ (GeoKey 3078 = $-90.0$), Central Meridian = $0.0^\circ$ (GeoKey 3079 = $0.0$), Scale at Natural Origin $k_0 = 1.0$ (GeoKey 3093 = $1.0$), Reference Sphere Radius $R = 1737400.0\text{ m}$ (GeoKey 2057/2058).
- Computed the exact local map-projection scale factor $k(\phi)$ using the Snyder (1987, USGS PP 1395, p. 157) South Polar Stereographic formula on the spherical lunar datum ($k_0 = 1.0, \phi_0 = -90^\circ$):
  $$k = \frac{2 k_0}{1 + \sin\phi_0 \sin\phi} = \frac{2}{1 - \sin\phi} = \frac{2}{1 + \sin(|\phi|)} \quad (\text{for } \phi < 0)$$
- Analyzed and verified ISRO Chandrayaan-2 PDS4 XML tags: `<..._latitude_en>` and `<..._longitude_en>`. Confirmed these store projected coordinates: **Northing and Easting in meters** in the South Polar Stereographic grid.
- Project lon/lat coordinates to $(X, Y)$ using Snyder forward equations:
  $$X = 2 R k_0 \tan\left(\frac{\pi}{4} - \frac{|\phi|}{2}\right) \sin\lambda, \quad Y = 2 R k_0 \tan\left(\frac{\pi}{4} - \frac{|\phi|}{2}\right) \cos\lambda$$
  Cross-checked XML Northing/Easting against Snyder projected coordinates; agreement is within $5.9 - 6.5\text{ m}$ in width ($< 0.2\%$) and $48 - 49\text{ m}$ in height ($< 0.2\%$).
- Evaluated GeoTIFF Tag 33922 tiepoint ordering versus XML corners, revealing that GeoTIFF pixel $(0, 0)$ maps to XML `<topright>` and pixel $(W, 0)$ maps to XML `<topleft>`, confirming a column-axis scanline index reversal.

#### 2. Separation of Three Distinct Scale Concepts
To avoid ambiguity, the diagnostic strictly distinguishes three different scale concepts:
1. **Concept A: Nominal Raster Scale ($5.000\text{ m/px}$):**
   An idealized nadir detector-sampling ratio applied uniformly during cropping and downsampling. In the mentor dataset, this deliverable scale was derived from the native instrument swath ($W_{\text{native}} = 12,000\text{ px}$) using nominal nadir GSD:
   $$W_{\text{deliverable}} = 12000 \times \frac{\text{res}_{\text{native}}}{5.0\text{ m/px}}$$
   - Pair 01: $12000 \times 0.26 / 5.0 = 624\text{ px} \implies 5.0000\text{ m/px}$
   - Pair 02: $12000 \times 0.27 / 5.0 = 648\text{ px} \implies 5.0000\text{ m/px}$
   - Pair 03: $12000 \times 0.25 / 5.0 = 600\text{ px} \implies 5.0000\text{ m/px}$
   - Pair 04: $12000 \times 0.23 / 5.0 = 552\text{ px} \implies 5.0000\text{ m/px}$
2. **Concept B: Projected-Coordinate Span ($5.12 - 5.51\text{ m/px}$):**
   The Euclidean ground distance between georeferenced footprint corners in the map projection plane divided by the deliverable raster pixel dimensions:
   $$\text{Span}_x = \frac{\Delta X_{\text{corner}}}{W_{\text{deliverable}}}, \quad \text{Span}_y = \frac{\Delta Y_{\text{corner}}}{H_{\text{deliverable}}}$$
3. **Concept C: Physical Ground Sampling Scale:**
   The true instantaneous surface distance represented per pixel on the rugged 3D lunar topography, governed by spacecraft orbit altitude, off-nadir camera pointing (pitch and roll), scanline velocity, and local Digital Elevation Model (DEM) terrain slope.

#### 3. Rigorous 4-Pair Comparison Table (Pairs 1–4)

| Dataset | Nominal Raster Scale (Concept A) | XML `_en` Projected Span (Concept B) | Snyder Projected Span (Concept B) | Mean Lat ($\phi$) | Local Projection Scale Factor ($k$) | Reference GeoTIFF Pixel Scale |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | **$5.0000\text{ m/px}$** ($12000 \times 0.26 / 624$) | $3217.6\text{ m} \times 25336.3\text{ m}$<br>$\implies \mathbf{5.156\text{ m/px} \times 5.200\text{ m/px}}$ | $3211.3\text{ m} \times 25286.7\text{ m}$<br>$\implies \mathbf{5.146\text{ m/px} \times 5.190\text{ m/px}}$ | $-89.36^\circ$ | **$1.000031$** ($+0.0031\%$) | $5.000\text{ m/px}$ |
| **`OHRC_PAIR_02`** | **$5.0000\text{ m/px}$** ($12000 \times 0.27 / 648$) | $3323.6\text{ m} \times 25208.2\text{ m}$<br>$\implies \mathbf{5.129\text{ m/px} \times 4.983\text{ m/px}}$ | $3317.1\text{ m} \times 25159.8\text{ m}$<br>$\implies \mathbf{5.119\text{ m/px} \times 4.973\text{ m/px}}$ | $-84.95^\circ$ | **$1.001948$** ($+0.195\%$) | $5.000\text{ m/px}$ |
| **`OHRC_PAIR_03`** | **$5.0000\text{ m/px}$** ($12000 \times 0.25 / 600$) | $3097.1\text{ m} \times 25444.4\text{ m}$<br>$\implies \mathbf{5.162\text{ m/px} \times 5.035\text{ m/px}}$ | $3091.1\text{ m} \times 25395.6\text{ m}$<br>$\implies \mathbf{5.152\text{ m/px} \times 5.025\text{ m/px}}$ | $-84.95^\circ$ | **$1.001941$** ($+0.194\%$) | $5.000\text{ m/px}$ |
| **`OHRC_PAIR_04`** | **$5.0000\text{ m/px}$** ($12000 \times 0.23 / 552$) | $3042.9\text{ m} \times 25681.7\text{ m}$<br>$\implies \mathbf{5.512\text{ m/px} \times 5.524\text{ m/px}}$ | $3037.0\text{ m} \times 25632.7\text{ m}$<br>$\implies \mathbf{5.502\text{ m/px} \times 5.514\text{ m/px}}$ | $-84.18^\circ$ | **$1.002585$** ($+0.258\%$) | $5.000\text{ m/px}$ |

*(For IIRS pairs: Pair A source native resolution is $93.74\text{ m/px}$ vs reference $94.75\text{ m/px}$, ratio $0.9893$; Pair B source native resolution is $83.14\text{ m/px}$ vs reference $200.0\text{ m/px}$, ratio $0.4157$.)*

#### 4. Scientific Status & Evaluation of Potential Contributing Factors
- **Map Projection Dilation ($k$):** Map projection scale distortion accounts for only $+0.003\%$ (Pair 01) to $+0.26\%$ (Pair 04). Map projection distortion mathematically cannot account for the $3\% - 10\%$ discrepancy between nominal raster scale ($5.000\text{ m/px}$) and projected footprint span ($5.12 - 5.51\text{ m/px}$).
- **Spacecraft Attitude & Perspective Geometry:** PDS4 XML records off-nadir spacecraft attitude angles (e.g. Pair 01 Pitch = $-14.55^\circ$, Roll = $+4.89^\circ$ at altitude $100.78\text{ km}$). Off-nadir perspective geometry geometrically dilates the projected ground footprint compared to nadir.  
  *Governance Rule (No-Causality-Without-Control):* Spacecraft attitude is identified as a **geometrical hypothesis**, NOT yet a proven explanation. Decoupling perspective dilation from 3D DEM relief displacement requires complete SPICE ray-tracing kernels and DEM terrain intersection.
- **Track A Status:** **`PARTIALLY RECONCILED`**.
  The mathematical origin of Concept A ($5.000\text{ m/px}$ from nominal detector swath downscaling) and Concept B ($5.12 - 5.51\text{ m/px}$ from corner ground coordinates) is verified and understood, but they describe different physical quantities. The observed 3%–10% difference between nominal and projected-coordinate span warrants controlled testing, but this diagnostic does not establish that it degrades the matcher. Gross scale mismatch cannot be declared falsified until its operational impact is tested.

#### 5. Uncertainty / Limitations
Without full 3D camera-surface ray tracing against an authoritative lunar Digital Elevation Model (e.g. SLDEM2015), the true physical ground sampling scale (Concept C) cannot be completely decoupled from topographic parallax displacement.

#### 6. Evidence Classification
- Nominal $5.000\text{ m/px}$ Deliverable Configuration (Concept A): **`VERIFIED METADATA`**
- Projected Coordinate Span ($5.12 - 5.51\text{ m/px}$, Concept B): **`DIRECT IMAGE MEASUREMENT`**
- Local Map-Projection Scale Factor ($k$): **`DIRECT IMAGE MEASUREMENT`** / Mathematical Formula
- Spacecraft Attitude Perspective Dilation: **`HEURISTIC`** / Geometrical Hypothesis
- Reference Scale Tolerance ($\pm 0.01\text{ m/px}$): **`HEURISTIC`** *(Reference Tolerance)*

---

### TRACK B: Geographic Coordinate Overlap

#### 1. Measurement
- Extracted georeferenced corner coordinates and projected selenographic tiepoints into Polar Stereographic coordinates.
- Computed axis-aligned projected bounding boxes for source and reference rasters.
- Evaluated bounding box intersection area, source-in-reference bounding coverage fraction ($f_{\text{src\_in\_ref}}$), reference-in-source bounding coverage ($f_{\text{ref\_in\_src}}$), and symmetric bounding IoU.

#### 2. Observed Evidence
- **Axis-Aligned Bounding Box Analysis:**
  - `OHRC_PAIR_01`: Source projected bounding box $X \in [-16186.0, 7394.5]\text{ m}$, $Y \in [-21768.5, -6607.1]\text{ m}$ is entirely inside Reference $X \in [-19187.0, 10393.0]\text{ m}$, $Y \in [-24763.0, -3603.0]\text{ m}$. Bounding containment: **$100.00\%$** (Bounding IoU: $57.12\%$).
  - `OHRC_PAIR_02`: Bounding containment: **$100.00\%$** (Bounding IoU: $43.46\%$).
  - `OHRC_PAIR_03`: Bounding containment: **$100.00\%$** (Bounding IoU: $40.77\%$).
  - `OHRC_PAIR_04`: Bounding containment: **$100.00\%$** (Bounding IoU: $50.30\%$).
  - `IIRS_PAIR_A`: Source selenographic bounds fall entirely inside reference raster coverage (**$100.00\%$**).
  - `IIRS_PAIR_B`: Geographic coordinates unverified in mentor files.

#### 3. Corrected Interpretation
> **“Gross geographic non-overlap is not supported by the bounding-box analysis.”**

#### 4. Uncertainty / Limitation
- **Bounding Box vs. Exact Polygon:** This calculation evaluates axis-aligned projected bounding box containment. The actual source footprint is an oriented, tilted quadrilateral strip rather than an axis-aligned box.
- **Not Correspondence Ground Truth:** Bounding box containment establishes that the source sensor aimed at territory within the reference raster perimeter. It is **not exact physical footprint ground truth**, and **not correspondence ground truth**. Ephemeris pointing errors (hundreds of meters) and lack of surface feature correspondence mean visual alignment is not guaranteed.

#### 5. Evidence Classification
- Bounding Coordinates: **`VERIFIED METADATA`**
- Bounding Box Intersection & Coverage ($100.0\%$): **`DIRECT IMAGE MEASUREMENT`**

#### 6. Supporting / Weakening / Inconclusive Analysis
- *Weakening Observation:* In all 4 OHRC cases, bounding box containment is $100.00\%$. Gross geographic non-overlap is not supported by the bounding-box analysis.
- *Supporting Observation:* None for gross non-overlap.

---

### TRACK E: Image Shape / Aspect Ratio & Downsampling Distortion

#### 1. Measurement
- Measured native raster dimensions ($W, H$) and computed native aspect ratios ($\text{AR} = \max(W,H)/\min(W,H)$).
- Computed **Image Shape / Aspect-Ratio Difference**: $\delta_{\text{AR}} = \max(\text{AR}_s, \text{AR}_r) / \min(\text{AR}_s, \text{AR}_r)$.
- Evaluated actual matching-path resizing transformations applied by `compute_matching_scale((H, W), max_dim=1600, max_budget=1800000)`: scale factors ($s_x, s_y$), relative scale ratio ($s_{\text{src}} / s_{\text{ref}}$), and non-conformal stretching anisotropy $\alpha = |s_x - s_y| / \max(s_x, s_y)$.

#### 2. Observed Evidence
- **Image Shape / Aspect-Ratio Differences:**
  - `OHRC_PAIR_01`: Source $\text{AR} = 7.808$ ($624 \times 4872$) vs. Reference $\text{AR} = 1.398$ ($5916 \times 4232$). Image Shape AR Difference: **$5.585\times$**.
  - `OHRC_PAIR_02`: Source $\text{AR} = 7.807$ vs. Reference $\text{AR} = 2.422$. Image Shape AR Difference: **$3.224\times$**.
  - `OHRC_PAIR_03`: Source $\text{AR} = 8.423$ vs. Reference $\text{AR} = 2.614$. Image Shape AR Difference: **$3.222\times$**.
  - `OHRC_PAIR_04`: Source $\text{AR} = 8.422$ vs. Reference $\text{AR} = 1.998$. Image Shape AR Difference: **$4.215\times$**.
  - `IIRS_PAIR_A`: Image Shape AR Difference: **$3.891\times$**.
  - `IIRS_PAIR_B`: Image Shape AR Difference: **$38.228\times$**.
- **Resampling Anisotropy ($\alpha$):**
  - For all 4 OHRC pairs, $\alpha < 0.0004$ (negligible). The loader applies equal scaling to width and height, preserving conformal geometry without non-conformal stretching.
- **Actual Matcher Downscaling Disparity ($s_{\text{src}} / s_{\text{ref}}$):**
  - Because source and reference rasters differ in total pixel count, budget-constrained downscaling reduced them by unequal factors:
    - Pair 01: Source scale $0.3284$, Reference scale $0.2681$ $\implies$ Relative scale disparity inside LoFTR: **$1.2248\times$** ($+22.5\%$).
    - Pair 02: Source scale $0.3163$, Reference scale $0.2548$ $\implies$ Relative scale disparity: **$1.2412\times$** ($+24.1\%$).
    - Pair 03: Source scale $0.3166$, Reference scale $0.2533$ $\implies$ Relative scale disparity: **$1.2497\times$** ($+25.0\%$).
    - Pair 04: Source scale $0.3442$, Reference scale $0.2531$ $\implies$ Relative scale disparity: **$1.3599\times$** ($+36.0\%$).

#### 3. Corrected Interpretation
Non-conformal $x/y$ stretching is negligible ($\alpha < 0.0004$), confirming that circular craters are not distorted into ellipses. However, the image shape difference and disparate pixel budgets introduce an actual $22.5\% - 36.0\%$ relative scale difference between source and reference inside the LoFTR matcher canvas. Physical pixel scale is distinct from image-shape and loader downscaling disparity. Nonzero anisotropy or scale difference alone does not explain failure without controlled comparison.

#### 4. Uncertainty / Limitation
Deep feature matchers possess varying tolerance to minor scale variations; without an isolated ablation varying only the downscaling budget, this scale difference remains a potential contributing factor rather than a proven cause.

#### 5. Evidence Classification
- Native Dimensions & Aspect Ratios: **`VERIFIED METADATA`**
- Computed Scale Factors & Anisotropy: **`DIRECT IMAGE MEASUREMENT`**

---

### TRACK C: Radiometric Appearance & Contrast Dynamics

#### 1. Measurement
- Computed normalized 256-bin intensity histograms, Shannon entropy ($\mathcal{H} = -\sum p_k \log_2 p_k$), shadow fraction ($< 10\text{ DN}$), saturation fraction ($> 245\text{ DN}$), and Sobel median gradient magnitudes for all rasters.

#### 2. Observed Evidence
- **Shadow & Dynamic Range Telemetry:**
  - `OHRC_PAIR_01`: Source shadow fraction = **$62.01\%$**, Reference shadow fraction = **$6.05\%$** (Disparity: $+55.96\%$). Source entropy = $5.13\text{ bits}$ vs. Reference = $7.10\text{ bits}$. Reference gradient contrast is $12.0\times$ higher than source.
  - `OHRC_PAIR_02`: Source shadow = **$40.63\%$**, Reference = **$12.92\%$** (Disparity: $+27.71\%$). Source entropy = $6.18\text{ bits}$ vs. Reference = $7.17\text{ bits}$.
  - `OHRC_PAIR_03`: Source shadow = **$69.70\%$**, Reference = **$13.56\%$** (Disparity: $+56.14\%$). Source entropy = $4.30\text{ bits}$ vs. Reference = $6.99\text{ bits}$. Reference gradient contrast is $10.4\times$ higher.
  - `OHRC_PAIR_04`: Source shadow = **$69.21\%$**, Reference = **$39.06\%$** (Disparity: $+30.15\%$). Source entropy = $4.27\text{ bits}$ vs. Reference = $6.01\text{ bits}$. Reference gradient contrast is $10.0\times$ higher.
- **Comparison to Historical Controls:**
  - Positive Control (Pair 05): Shadow fraction was only $14.2\%$, entropy was $7.18\text{ bits}$, and contrast ratio was $1.15\times$.
  - Negative Control (Pair 02): Shadow fraction was $52.8\%$, entropy was $4.95\text{ bits}$.

#### 3. Corrected Interpretation
> **“High low-intensity/shadow fraction with reduced measured entropy.”**  
All four OHRC source images exhibit substantial low-intensity shadow fractions ($40.63\% - 69.70\%$ of pixels have $\text{DN} < 10$). In Pairs 01, 03, and 04, over half the image provides near-zero gradient information. The reference rasters, by contrast, display balanced histograms with Shannon entropy $> 6.0 - 7.1\text{ bits}$.

#### 4. Uncertainty / Limitation
Entropy and shadow fraction thresholds are descriptive diagnostics. A high shadow percentage correlates strongly with low inlier counts, but this observation does not mathematically isolate whether failure is driven by shadow truncation or shadow vector reversal.

#### 5. Evidence Classification
- Raster Histograms, Entropy, Shadow/Saturation %: **`DIRECT IMAGE MEASUREMENT`**
- Diagnostic Cutoffs: **`HEURISTIC`** *(Uncalibrated Descriptive Diagnostic)*

---

### TRACK F: Extreme Low-Sun Illumination Divergence

#### 1. Measurement
- Parsed authoritative mission PDS4 XML metadata for solar elevation, solar incidence, and solar azimuth.
- Computed image-derived shadow direction proxies ($\theta_{\text{proxy}}$) using Sobel orientation gradient histograms on shadow boundary edges.
- Calculated apparent proxy angular disparity: $\Delta \theta_{\text{proxy}} = \min(|\theta_s - \theta_r|, 360^\circ - |\theta_s - \theta_r|)$.

#### 2. Observed Evidence
- **Authoritative XML Metadata (Source):**
  - `OHRC_PAIR_01`: Solar Elevation = **$2.11^\circ$**, Solar Incidence = **$87.89^\circ$**, Solar Azimuth = $299.64^\circ$.
  - `OHRC_PAIR_02`: Solar Elevation = **$5.10^\circ$**, Solar Incidence = **$84.90^\circ$**, Solar Azimuth = $19.91^\circ$.
  - `OHRC_PAIR_03`: Solar Elevation = **$3.09^\circ$**, Solar Incidence = **$86.91^\circ$**, Solar Azimuth = $17.84^\circ$.
  - `OHRC_PAIR_04`: Solar Elevation = **$-0.31^\circ$**, Solar Incidence = **$90.31^\circ$**, Solar Azimuth = $12.35^\circ$.
  - `IIRS_PAIR_A`: Solar Elevation = $25.94^\circ$, Solar Incidence = $64.06^\circ$, Solar Azimuth = $121.72^\circ$.
  - `IIRS_PAIR_B`: Solar Elevation = $21.06^\circ$, Solar Incidence = $68.94^\circ$, Solar Azimuth = $290.76^\circ$.
- **Reference XML Status:** `NOT AVAILABLE` in mentor directory. Metadata-derived disparity is strictly `UNAVAILABLE`.
- **Image-Derived Shadow Proxies (`HEURISTIC`):**
  - `OHRC_PAIR_01`: Source proxy = $115.0^\circ$, Reference proxy = $265.0^\circ$ $\implies$ Apparent Disparity: **$150.0^\circ$**.
  - `OHRC_PAIR_02`: Source proxy = $135.0^\circ$, Reference proxy = $95.0^\circ$ $\implies$ Apparent Disparity: **$40.0^\circ$**.
  - `OHRC_PAIR_03`: Source proxy = $165.0^\circ$, Reference proxy = $55.0^\circ$ $\implies$ Apparent Disparity: **$110.0^\circ$**.
  - `OHRC_PAIR_04`: Source proxy = $185.0^\circ$, Reference proxy = $125.0^\circ$ $\implies$ Apparent Disparity: **$60.0^\circ$**.

#### 3. Corrected Interpretation
> **“The image-derived gradient-direction proxy shows large angular differences and is consistent with substantial image-domain appearance/edge-orientation differences; the proxy is not a validated solar-shadow measurement.”**

Solar incidence $> 80^\circ$ in source metadata defines descriptive polar grazing illumination; **it is NOT a demonstrated matcher-failure threshold**. In Pairs 01 and 03, the image-derived proxies suggest substantial angular divergence, but without reference mission XML or SPICE ephemeris validation, illumination difference cannot be declared the isolated root cause.

#### 4. Uncertainty / Limitation
- Image-derived shadow direction is a `HEURISTIC` proxy that can be confounded by local crater wall slopes.
- Reference illumination angles are not verified from metadata.

#### 5. Evidence Classification
- Source XML Solar Angles: **`VERIFIED METADATA`**
- Image-Derived Shadow Proxies: **`HEURISTIC`**

---

### TRACK D: Correspondence Spatial Distribution & Quality Gate Dynamics

#### 1. Measurement
- Extracted production matcher telemetry from frozen benchmark logs: candidate count ($N_{\text{cand}}$), initial inliers ($N_{\text{init\_inliers}}$), inlier ratio, and spatial selection execution path.

#### 2. Observed Evidence
- **Telemetry Progression:**
  - `OHRC_PAIR_01`: 348 candidates $\to$ 6 initial inliers ($1.72\%$). Selection: **`BYPASSED`**, Occupancy: **`NOT EVALUATED`**.
  - `OHRC_PAIR_02`: 221 candidates $\to$ 5 initial inliers ($2.26\%$). Selection: **`BYPASSED`**, Occupancy: **`NOT EVALUATED`**.
  - `OHRC_PAIR_03`: 161 candidates $\to$ 5 initial inliers ($3.11\%$). Selection: **`BYPASSED`**, Occupancy: **`NOT EVALUATED`**.
  - `OHRC_PAIR_04`: 98 candidates $\to$ 5 initial inliers ($5.10\%$). Selection: **`BYPASSED`**, Occupancy: **`NOT EVALUATED`**.
  - `IIRS_PAIR_A`: 45 candidates $\to$ 5 initial inliers ($11.11\%$). Selection: **`BYPASSED`**, Occupancy: **`22.2%`** (Pre-rejection check: 2/9 cells).
  - `IIRS_PAIR_B`: 0 candidates $\to$ 0 initial inliers ($0.00\%$). Selection: **`BYPASSED`**, Occupancy: **`NOT EVALUATED`**.

#### 3. Interpretation
In all six mentor datasets, production failure occurred at the **initial inlier consensus stage** (prior to spatial selection). The frozen quality gate mandates $N_{\text{init\_inliers}} \ge 8$ and inlier ratio $\ge 20.0\%$. Because inliers remained between $0$ and $6$, spatial selection was **bypassed**. Spatial occupancy was **`NOT EVALUATED`** for all OHRC pairs and IIRS Pair B. Post-selection metrics cannot be used to explain pre-selection failures.

#### 4. Uncertainty / Limitation
Telemetry records the decision point; it does not measure whether rejected candidate pairs represent near-miss visual matches or completely unrelated features.

#### 5. Evidence Classification
- Matcher Telemetry & Quality Gate Status: **`MATCHER TELEMETRY`**

---

### TRACK G: Terrain / Content Overlap (Multiscale Template Correlation)

#### 1. Measurement
- Extracted sub-window crops along the moving source image to accommodate elongation.
- Executed multi-scale Normalized Cross-Correlation (NCC) against the reference raster at $16\times$ pyramid downscaling.
- Computed correlation response surface $\mathcal{C}(x, y)$, maximum correlation coefficient, mean and standard deviation of sidelobes outside the peak neighborhood, and Peak-to-Sidelobe Ratio (PSR).

#### 2. Observed Evidence
- **Peak-to-Sidelobe Ratios (PSR):**
  - `OHRC_PAIR_01`: Maximum PSR = **$3.08$** (Peak: $0.46$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
  - `OHRC_PAIR_02`: Maximum PSR = **$2.67$** (Peak: $0.38$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
  - `OHRC_PAIR_03`: Maximum PSR = **$2.88$** (Peak: $0.41$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
  - `OHRC_PAIR_04`: Maximum PSR = **$3.35$** (Peak: $0.45$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
  - `IIRS_PAIR_A`: Maximum PSR = **$3.50$** (Peak: $0.48$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
  - `IIRS_PAIR_B`: Maximum PSR = **$2.88$** (Peak: $0.36$). Status: **Noise-Dominated / Diffuse (PSR < 5.0)**.
- Across all six datasets, **zero prominent correlation peaks were detected** ($\text{PSR} \ge 10.0$ was nowhere approached).

#### 3. Corrected Interpretation
> **“The tested multiscale translation-only NCC diagnostic did not produce a strong isolated correlation peak.”**  
This experiment evaluated only multi-scale translation matching; **it does not test rotation-compensated, illumination-normalized, nonlinear, or geometrically warped correspondence**. Given orbital flight rotation ($-29^\circ$ to $-98^\circ$) and severe shadow asymmetry ($40\% - 69\%$), translation-only linear intensity correlation is expected to produce diffuse surfaces.

#### 4. Uncertainty / Limitation
PSR is diagnostic evidence only; it is **NOT registration ground truth**. A diffuse correlation surface does not prove that mutual terrain is absent, only that simple translation-only correlation cannot detect it.

#### 5. Evidence Classification
- Correlation Surface & PSR: **`DIRECT IMAGE MEASUREMENT`**
- PSR Thresholds ($\ge 10.0, < 5.0$): **`HEURISTIC`** *(Operational Diagnostic Signpost)*

---

## 4. Synthesis of Diagnostic Evidence

### 4.1 Findings Supported by `VERIFIED METADATA`
1. **Nominal Configuration:** Reference GeoTIFFs explicitly encode $5.000\text{ m/px}$ isotropic resolution in Polar Stereographic projection.
2. **Extreme Grazing Solar Incidence:** PDS4 XML metadata confirms OHRC source imagery was acquired at solar incidence angles of $84.90^\circ$ to $90.31^\circ$ (elevation $< 5^\circ$).
3. **Reference XML Absence:** Reference GeoTIFFs lack mission XML labels, precluding metadata-derived solar angle difference calculations.

### 4.2 Findings Supported by `DIRECT IMAGE MEASUREMENT`
1. **Bounding Box Overlap:** Across all four OHRC pairs and IIRS Pair A, projected bounding box intersection demonstrates that the moving source footprint is enclosed within the reference image bounding box.
2. **Distinct Scale Concepts & Ground Span Span ($5.12 - 5.51\text{ m/px}$):** Projected-coordinate ground span from georeferenced footprint corners is $5.12 - 5.51\text{ m/px}$, mathematically distinct from nominal nadir downscaled raster scale ($5.000\text{ m/px}$). Map projection dilation accounts for $< 0.26\%$. Decoupling perspective attitude dilation from topographic relief requires 3D ray tracing.
3. **High Shadow / Low-DN Fraction:** OHRC source images contain $40.63\% - 69.70\%$ pixels with $\text{DN} < 10$, with Shannon entropy suppressed to $4.27 - 5.13\text{ bits}$ and gradient contrast up to $12\times$ lower than reference rasters.
4. **Orbital Flight Track Rotation:** Source strips possess flight trajectory azimuths ($-29.16^\circ$ for Pair 01, $\approx -98^\circ$ for Pairs 02–04), introducing substantial geometric rotation relative to the north-up map grid.
5. **Negligible Resampling Anisotropy:** Loader downscaling is strictly conformal ($\alpha < 0.0004$), but image dimension differences introduce a $22.5\% - 36.0\%$ relative resolution difference inside the LoFTR matcher canvas.
6. **Weak Translation-Only NCC Response:** Multi-scale translation-only template cross-correlation yields diffuse response surfaces ($\text{PSR} = 2.67 - 3.50 < 5.0$).

### 4.3 Findings Supported by `MATCHER TELEMETRY`
1. **Pre-Selection Gate Interception:** All six cases failed at the preliminary inlier consensus stage ($0 - 6$ initial inliers, $0.00\% - 5.10\%$ inlier ratio, strictly below the $20.0\%$ threshold).
2. **Spatial Occupancy Bypassed:** Spatial selection was completely bypassed; spatial occupancy was **`NOT EVALUATED`** for all OHRC pairs and IIRS Pair B.

### 4.4 Findings Supported by `CONTROLLED EXPERIMENT`
- **No controlled experiment has yet been performed on mentor data.** All observations in this report are observational diagnostics on canonical datasets. Under the *No-Causality-Without-Control* rule, no measured association is declared a confirmed cause.

### 4.5 Heuristic and Inconclusive Findings
- **Image-Derived Shadow Proxies (`HEURISTIC`):** Directional gradient histograms suggest large apparent shadow disparities ($150^\circ$ for Pair 01, $110^\circ$ for Pair 03), but proxies are unverified against SPICE/ephemeris and remain uncalibrated.
- **Radiometric Cutoffs (`HEURISTIC`):** Specific entropy thresholds ($6.5\text{ bits}$) and shadow cutoffs ($20\%$) are descriptive benchmarks requiring empirical calibration on lunar regolith.

---

## 5. Status of Hypotheses & Unresolved Explanations

### 5.1 Hypotheses Status Summary
1. **Nominal 5 m/px Metadata vs. Ground Span:** **PARTIALLY RECONCILED.** Nominal $5.000\text{ m/px}$ raster scale (Concept A) and corner-derived projected span ($5.12 - 5.51\text{ m/px}$, Concept B) are mathematically distinct concepts whose origins are understood. Map projection dilation is $< 0.26\%$. The observed 3%–10% difference between nominal and projected-coordinate span warrants controlled testing, but this diagnostic does not establish that it degrades the matcher. Gross scale mismatch cannot be declared falsified until controlled testing is conducted.
2. **Gross Geographic Non-Overlap:** **NOT SUPPORTED BY BOUNDING-BOX ANALYSIS.** The axis-aligned bounding box containment shows $100\%$ inclusion, though exact polygon footprints and correspondence ground truth remain unverified.
3. **Non-Conformal Pixel Stretching:** **FALSIFIED.** Resampling anisotropy is negligible ($\alpha < 0.0004$); craters are not stretched into ellipses.

### 5.2 Supported Diagnostic Observations
- Negligible resampling anisotropy ($\alpha < 0.0004$).
- High OHRC source shadow / low-DN fraction ($40\% - 69\%$).
- Extreme grazing illumination in source metadata ($84.9^\circ - 90.3^\circ$).
- Initial correspondence failure before spatial selection ($N_{\text{inliers}} < 8$, ratio $\le 5.1\%$).
- Weak translation-only NCC peak ($\text{PSR} < 3.5$).

---

## 6. Concluding Scientific Statement

> **“Several factors are consistent with the observed mentor-dataset rejection, particularly high shadow/low-DN fraction and large image-domain appearance differences. However, the available diagnostic does not isolate causality. The relationship between nominal 5 m/px metadata and corner-derived projected ground span is partially reconciled, but gross scale mismatch remains an unisolated potential factor until controlled testing is completed.”**

---

## 7. Document & Governance Verification

- **Production Integrity:** 100% Frozen.  
  `app/adaptive_engine.py`, `app/registration_core.py`, `research/adaptive_matcher/adaptive_engine.py`, LoFTR weights, SIFT/SuperGlue settings, RANSAC thresholds ($3.0\text{ px}$), validation seeds 1–5, and the $20\%$ quality gate were **NOT MODIFIED**.
- **No Promotion:** No diagnostic method, template correlation heuristic, or threshold relaxation was introduced into production.
- **Traceability:** Raw measurements are fully preserved in `diagnostic_results.json` and `diagnostic_results.csv`.
