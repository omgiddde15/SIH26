# GeoScale Research Experiment Report
**Project:** Chandrayaan-2 Lunar Image Registration (`LunarReg`)  
**Experiment Mode:** Research Lab Diagnostic Only (Production Untouched)  
**Execution Timestamp:** 2026-09-27  
**Output Directory:** `research/geoscale_results/`  
**Classification:** **B. USEFUL DIAGNOSTIC ONLY**

---

## Executive Summary

We executed an independent, verified benchmark of the **modified GeoScale diagnostic script** across all available mentor and project datasets in:
1. `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026` (Mentor OHRC and IIRS datasets)
2. `C:\Users\Dell\Videos\SIH26_Lunar_Registration\data` (Project pairs 01–05, validation pairs, large CH2, Tycho, cross-sensor)

### Key Metrics Summary
- **Total Candidate Datasets Discovered:** 20
- **Compatible Datasets Tested:** 4 (Mentor OHRC Pairs 1, 2, 3, 4)
- **Datasets Skipped (Incompatible / Missing Metadata):** 16
- **Datasets Failed (Crashes / Errors):** 0 (clean error-handling and skip logic)
- **Pair 4 Discrepancy Reproduction:** **REPRODUCED EXACTLY** (+10.33% X, +10.47% Y, mean abs 10.40%)

---

## A. DATASETS TESTED

All 4 primary mentor OHRC pairs were rigorously inspected and processed:

| Dataset ID | Product Job ID | Declared GSD | Footprint Implied GSD X | Footprint Implied GSD Y | Discrepancy X | Discrepancy Y | Mean Abs Discrepancy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mentor OHRC Pair 1** | `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03` | 0.26 m/px | 0.268159 m/px | 0.270418 m/px | +3.14% | +4.01% | 3.57% | CONSISTENT |
| **Mentor OHRC Pair 2** | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01` | 0.27 m/px | 0.276850 m/px | 0.269050 m/px | +2.54% | -0.35% | 1.45% | CONSISTENT |
| **Mentor OHRC Pair 3** | `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02` | 0.25 m/px | 0.257973 m/px | 0.251737 m/px | +3.19% | +0.69% | 1.94% | CONSISTENT |
| **Mentor OHRC Pair 4** | `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00` | 0.23 m/px | 0.253753 m/px | 0.254081 m/px | **+10.33%** | **+10.47%** | **10.40%** | **POTENTIAL DISCREPANCY** |

---

## B. DATASETS SKIPPED

In strict accordance with the scientific guidelines, datasets missing required XML metadata or projected ground corner coordinates were **SKIPPED** without fabricating values:

1. **Mentor IIRS Pairs (Pair 1 & Pair 2):**
   - *Reason:* XML contains `<iir>` metadata rather than `<pan>`, and provides corner coordinates only in angular degrees (latitude/longitude), lacking the projected Cartesian coordinates (`*_latitude_en`, `*_longitude_en`) required by the modified GeoScale diagnostic.
   - *Status:* `SKIPPED — REQUIRED PROJECTED EN CORNER METADATA NOT AVAILABLE`
2. **Project Data (`pair01`, `pair03`, `pair04`):**
   - *Reason:* Target directories contain no image rasters directly.
   - *Status:* `SKIPPED — EMPTY DIRECTORY`
3. **Project Data (`pair02`, `large_ch2`, `validation_pairs 01–04`, `reference/source`, `tycho`, `cross_sensor`, `phase3_angle_pairs`):**
   - *Reason:* Standard unreferenced image files (PNG/JPEG) without accompanying ISRO/PDS4 XML headers or GeoTIFF projection tags.
   - *Status:* `SKIPPED — REQUIRED GEO METADATA NOT AVAILABLE`
4. **Project Data (`pair05`):**
   - *Reason:* Contains PNG swaths. Bounding box coordinates exist in `data/metadata/image_footprints.csv` and 96,397 per-pixel coordinates exist in `data/metadata/pair05_actual_geo_matches.csv`, but no XML metadata is present.
   - *Status:* `SKIPPED FOR GEOSCALE XML ANALYSIS — METADATA CATALOGED SEPARATELY`

---

## C. INPUT TYPES AVAILABLE

1. **OHRC PDS4 XML:** Contains native dimensions (`image_width=12000`, `raw_no_of_scan`), declared nominal resolution (`Resolution_in_meter`), spacecraft orbit parameters (altitude, roll, pitch, yaw, sun angles), and 4-corner bounding coordinates in both geographic degrees and projected Polar Stereographic meters (`*_latitude_en`, `*_longitude_en`).
2. **GeoTIFF Reference Rasters (`*_reference_at_5m.tif`):** Fully ortho-projected lunar base maps in Polar Stereographic Moon (`GCS_Moon`), featuring `ModelPixelScaleTag = (5.0, 5.0, 0.0)` meters/pixel and top-left `ModelTiepointTag`.
3. **Source Swath Rasters (`*_source_at_5m.tif`):** Downsampled swath products with 4 Selenographic corner tie points in `ModelTiepointTag`, resampled to approximately 5 meters/pixel using the declared XML resolution.
4. **CSV Per-Pixel Geometry Grids (`g_grd`):** Not present in the mentor download folders or the active project workspace. (Earlier legacy prototype `876.py` was designed for this input format, whereas `GeoScale.py` operates on XML projected corner coordinates).

---

## D. GEOSCALE METHOD USED

The modified GeoScale method applies **CORNER-BASED FOOTPRINT CONSISTENCY**:
1. Reads native raster dimensions: $W = \text{image\_width}$, $H = \text{raw\_no\_of\_scan}$.
2. Extracts projected 4-corner coordinates $(E_i, N_i)$ from `*_longitude_en` and `*_latitude_en`.
3. Computes Euclidean edge distances:
   - $\text{Width}_{\text{top}} = \|\mathbf{p}_{\text{topright}} - \mathbf{p}_{\text{topleft}}\|$
   - $\text{Width}_{\text{bottom}} = \|\mathbf{p}_{\text{bottomright}} - \mathbf{p}_{\text{bottomleft}}\|$
   - $\text{Height}_{\text{left}} = \|\mathbf{p}_{\text{bottomleft}} - \mathbf{p}_{\text{topleft}}\|$
   - $\text{Height}_{\text{right}} = \|\mathbf{p}_{\text{bottomright}} - \mathbf{p}_{\text{topright}}\|$
4. Computes footprint-implied pixel spacing:
   $$\text{GSD}_x = \frac{\text{Mean Width}}{W}, \quad \text{GSD}_y = \frac{\text{Mean Height}}{H}$$
5. Compares implied spacing against declared XML nominal GSD ($G_0$):
   $$\Delta_x (\%) = \left(\frac{\text{GSD}_x}{G_0} - 1\right) \times 100, \quad \Delta_y (\%) = \left(\frac{\text{GSD}_y}{G_0} - 1\right) \times 100$$
6. **Strict Classification:** This calculation is labeled **FOOTPRINT-IMPLIED RESOLUTION** (macro average), **NOT** True Per-Pixel GSD.

---

## E. RESULTS TABLE (MENTOR OHRC)

| Pair | Native Size (px) | Declared GSD (m) | Nominal Footprint (m) | Actual Footprint (m) | Implied GSD (m/px) | Discrepancy (%) | 5m TIFF Size (px) | 5m Implied Res (m/px) | Altitude (km) | Reference Overlap |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pair 1** | $12000 \times 93692$ | 0.26 | $3120.0 \times 24359.9$ | $3217.9 \times 25336.5$ | X: 0.2682<br>Y: 0.2704 | X: +3.14%<br>Y: +4.01% | $624 \times 4872$ | X: 5.157<br>Y: 5.200 | 100.78 | Fully Enclosed |
| **Pair 2** | $12000 \times 93692$ | 0.27 | $3240.0 \times 25296.8$ | $3322.2 \times 25207.9$ | X: 0.2769<br>Y: 0.2691 | X: +2.54%<br>Y: -0.35% | $648 \times 5059$ | X: 5.127<br>Y: 4.983 | 105.77 | Fully Enclosed |
| **Pair 3** | $12000 \times 101074$ | 0.25 | $3000.0 \times 25268.5$ | $3095.7 \times 25444.0$ | X: 0.2580<br>Y: 0.2517 | X: +3.19%<br>Y: +0.69% | $600 \times 5054$ | X: 5.160<br>Y: 5.034 | 97.78 | Fully Enclosed |
| **Pair 4** | $12000 \times 101074$ | 0.23 | $2760.0 \times 23247.0$ | $3045.0 \times 25680.9$ | X: 0.2538<br>Y: 0.2541 | **X: +10.33%**<br>**Y: +10.47%** | $552 \times 4649$ | **X: 5.516**<br>**Y: 5.524** | 91.86 | Fully Enclosed |

---

## F. OUTLIER / DISCREPANCY CASES: SPECIAL ATTENTION TO PAIR 4

### Did the previous finding reproduce?
**YES, IT REPRODUCED EXACTLY.**

### Exact Measured Values
- **Declared GSD:** `0.230000 m/px`
- **Footprint-Implied GSD X:** `0.253753 m/px` ($+10.33\%$ error)
- **Footprint-Implied GSD Y:** `0.254081 m/px` ($+10.47\%$ error)
- **Mean Absolute Discrepancy:** `10.398%` (~$10.40\%$)

### Scientific Finding
Across all four orbits, the actual physical footprint-implied ground resolution is remarkably stable:
- Pair 1: ~0.269 m/px
- Pair 2: ~0.273 m/px
- Pair 3: ~0.255 m/px
- Pair 4: ~0.254 m/px

In Pair 4, spacecraft altitude was the lowest of the set ($91.86\text{ km}$ vs $\sim 98\text{--}106\text{ km}$). The XML metadata recorded `Resolution_in_meter = 0.23`, likely due to nominal orbit scaling.
However, when the downsampled mentor TIFF `source_at_5m.tif` was generated, the resampling formula:
$$\text{Width}_{5\text{m}} = \text{round}\left(\frac{12000 \times 0.23}{5.0}\right) = 552\text{ pixels}$$
used the nominal 0.23m value rather than the true footprint value ($3045\text{ m} / 5.0\text{ m} \approx 609\text{ pixels}$).

Consequently, in the $5\text{m}$ raster space:
- Reference image resolution = strictly $5.000\text{ m/px}$
- Source image resolution = $\mathbf{5.520\text{ m/px}}$
- **Inter-image scale ratio = $1.104$ ($10.4\%$ scale divergence)!**

---

## G. WHAT IS ACTUALLY DEMONSTRATED

1. **Metadata Inconsistency Detection:** GeoScale conclusively demonstrates that XML declared GSD can deviate significantly ($>10\%$) from actual ground projection footprint geometry.
2. **Effective Scale Ratio Prior:** In Pair 4, GeoScale reveals an intrinsic $1.104$ scale disparity between the prepared source raster and reference raster, proving that the pair is not at an exact 1:1 scale.
3. **Spatial Overlap Enclosure:** In all 4 mentor pairs, the source image ground footprint is mathematically verified to lie strictly within the spatial extents of the reference GeoTIFF.

---

## H. WHAT IS NOT DEMONSTRATED

1. **Not Scale-Invariant Matching:** GeoScale does not match features or solve scale-variant correspondence matching.
2. **Not Viewpoint Invariant:** GeoScale does not model 3D perspective distortion or topography.
3. **Not Sun-Angle Invariant:** Footprint geometry is completely decoupled from illumination conditions.
4. **Not Sub-Pixel Accurate:** GeoScale is a macro-scale geometric sanity check; it provides zero sub-pixel precision.
5. **Not a Per-Pixel Grid:** Without ISRO/PDS4 `g_grd` CSV tables, it does not provide pixel-level geolocation.

---

## I. POSSIBLE USE IN LUNARREG

| Category | Assessment | Explanation |
| :--- | :---: | :--- |
| **A. Scale Variation** | **PARTIAL** | Can provide a pre-matching scale prior (e.g. telling adaptive routing that Pair 4 needs a 1.104 scale normalization before LoFTR/SIFT). |
| **B. Viewpoint Variation** | **NO** | Planar footprint boundary math cannot resolve 3D tilt/obliqueness. |
| **C. Sun-Angle Variation** | **NO** | Unrelated to lighting/shadows. |
| **D. Sub-Pixel Accuracy** | **NO** | Macro footprint averaging has no sub-pixel correspondence ability. |
| **E. Geospatial Validation** | **YES** | Perfect pre-flight validation gate: detects corrupt metadata, scale anomalies, and out-of-bounds swaths before launching heavy neural matchers. |

### Final Recommendation
GeoScale should **REMAIN IN THE RESEARCH LAB ONLY** as an optional diagnostic tool for raw PDS4/ISRO data ingestion. It must **NOT** be integrated into production feature matching, homography estimation, or UI workflows.
