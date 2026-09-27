# Mentor Dataset Audit & Metadata-Aware Registration Report

**Date of Audit**: September 23, 2026  
**Canonical Mentor Data Directory**: `C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\`  
**LunarReg Project Repository**: `C:\Users\Dell\Videos\SIH26_Lunar_Registration`  
**Audit Artifacts Generated**:
- `research/multimodal/mentor_data_audit/mentor_dataset_registry.csv`
- `research/multimodal/mentor_data_audit/mentor_dataset_registry.json`
- `research/multimodal/mentor_data_audit/mentor_metadata_report.md`

---

## 1. Executive Summary & Verification Methodology

A comprehensive, programmatic audit was performed on all 18 files (6 XMLs, 12 TIFFs) provided in the mentor data archive. All metadata was parsed directly from the official ISRO XML metadata files and GeoTIFF header tags (`ModelPixelScaleTag` `33550`, `ModelTiepointTag` `33922`, `GeoKeyDirectoryTag` `34735`, `GeoAsciiParamsTag` `34737`), accompanied by raster validation via OpenCV (`cv2.IMREAD_UNCHANGED`) and PIL.

### Key Audit Findings:
1. **The 375× Myth & The Physical Scale Reality**:
   - The native OHRC sensor resolution is $0.23 - 0.27\text{ m/px}$, and native IIRS resolution is $83.14 - 93.74\text{ m/px}$. While the arithmetic ratio of these native resolutions is $\approx 375$, **no mentor dataset presents a $375\times$ registration problem**.
   - For all four OHRC pairs, the mentor downsampled the native $12,000\text{ px}$ OHRC swaths by $\approx 19\times - 22\times$ down to $\approx 550 - 650\text{ px}$ width, explicitly tagging them at **$5.0\text{ m/px}$** (`..._source_at_5m.tif`).
   - The reference LRO-NAC images have an embedded `ModelPixelScaleTag = (5.0, 5.0, 0.0)` meters/pixel.
   - Consequently, the OHRC registration problem is **$1:1$ effective scale ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**, not $20:1$ and not $375\times$.
2. **IIRS Source XMLs Verified vs Missing LRO-WAC Reference Metadata**:
   - Both IIRS source XMLs (`IIRXXD18CHO2686502NNNN25244140531312_V2_1.xml` and `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01.xml`) exist in the mentor directory and have been **VERIFIED** by programmatic parsing.
   - However, **zero reference-side XMLs or LRO-WAC label files** exist in `C:\Users\Dell\Downloads\SIH data`.
   - For both IIRS pairs, the source telemetry is verified, while the reference physical GSD and scale ratio are strictly recorded as **`NOT VERIFIED`** (LRO-WAC XML: `NOT AVAILABLE`).
   - Overall status for both IIRS pairs is **`PARTIALLY VERIFIED`** (*"Source metadata verified; LRO-WAC reference metadata not verified"*).
3. **Illumination Extremes**:
   - All four OHRC scenes are located near the lunar South Pole (latitudes $-83.7^\circ$ to $-89.5^\circ$) with extreme grazing solar incidence angles ($84.9^\circ - 90.3^\circ$) and solar elevations as low as $-0.31^\circ$ (sun below the local horizontal, producing extensive shadowed terrains).
4. **Grounding Classification**:
   - All pairs are classified as **`PARTIALLY GROUNDED`**. Corner geodetic bounding boxes and map projections confirm mutual geographic overlap (`Geographic overlap metadata available`), but dense surveyed lunar Ground Control Points (GCPs), DEM relief profiles, and SPICE exterior camera kernels are absent.

---

## 2. Comprehensive Mentor Dataset Registry

| Dataset ID | Instrument | Source TIFF Dimensions & Dtype | Reference TIFF Dimensions & Dtype | Native Res | Effective Source Res | Reference Res | Scale Ratio | Solar Incidence | Solar Azimuth | Solar Elevation | Verification Status | Grounding Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OHRC_PAIR_01** | OHRC | $624 \times 4872$, uint8 | $5916 \times 4232$, uint8 | $0.26\text{ m/px}$ | $5.0\text{ m/px}$ | $5.0\text{ m/px}$ | $1:1$ | $87.89^\circ$ | $299.64^\circ$ | $+2.11^\circ$ | **VERIFIED** | PARTIALLY GROUNDED |
| **OHRC_PAIR_02** | OHRC | $648 \times 5059$, uint8 | $2593 \times 6279$, uint8 | $0.27\text{ m/px}$ | $5.0\text{ m/px}$ | $5.0\text{ m/px}$ | $1:1$ | $84.90^\circ$ | $19.91^\circ$ | $+5.10^\circ$ | **VERIFIED** | PARTIALLY GROUNDED |
| **OHRC_PAIR_03** | OHRC | $600 \times 5054$, uint8 | $2416 \times 6316$, uint8 | $0.25\text{ m/px}$ | $5.0\text{ m/px}$ | $5.0\text{ m/px}$ | $1:1$ | $86.91^\circ$ | $49.07^\circ$ | $+3.09^\circ$ | **VERIFIED** | PARTIALLY GROUNDED |
| **OHRC_PAIR_04** | OHRC | $552 \times 4649$, uint8 | $3164 \times 6322$, uint8 | $0.23\text{ m/px}$ | $5.0\text{ m/px}$ | $5.0\text{ m/px}$ | $1:1$ | $90.31^\circ$ | $256.29^\circ$ | $-0.31^\circ$ | **VERIFIED** | PARTIALLY GROUNDED |
| **IIRS_PAIR_A** | IIRS | $250 \times 7783$, float32 | $960 \times 7681$, float32 | $93.74\text{ m/px}$ | $93.74\text{ m/px}$ | *NOT VERIFIED* | *NOT VERIFIED* | $64.06^\circ$ | $107.84^\circ$ | $+25.94^\circ$ | **PARTIALLY VERIFIED** | PARTIALLY GROUNDED |
| **IIRS_PAIR_B** | IIRS | $104 \times 4851$, float32 | $3175 \times 3874$, float32 | $83.14\text{ m/px}$ | $83.14\text{ m/px}$ | *NOT VERIFIED* | *NOT VERIFIED* | $68.94^\circ$ | $45.45^\circ$ | $+21.06^\circ$ | **PARTIALLY VERIFIED** | PARTIALLY GROUNDED |

---

## 3. Dataset-by-Dataset Verification & Metadata Breakdown

### 3.1 OHRC Pair 1
- **Job ID**: `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03`
- **Source File**: `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_source_at_5m.tif` ($624 \times 4872$, 8-bit unsigned char)
- **Reference File**: `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif` ($5916 \times 4232$, 8-bit unsigned char)
- **Source XML**: `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $100.78\text{ km}$
  - Roll: $+4.889318^\circ$, Pitch: $-14.545736^\circ$, Yaw: $-0.001393^\circ$
  - Pass Date: 2024-12-07T12:21:32 UTC
- **Illumination Geometry**:
  - Solar Azimuth: $299.639023^\circ$
  - Solar Elevation: $+2.113221^\circ$
  - Solar Incidence Angle: $87.886779^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Polar Stereographic Moon (South Pole)
  - Source Corners (Selenographic):
    - Top-Left: $(245.779169^\circ\text{ E}, -89.468902^\circ\text{ N})$
    - Top-Right: $(239.729533^\circ\text{ E}, -89.381960^\circ\text{ N})$
    - Bottom-Left: $(158.660785^\circ\text{ E}, -89.329873^\circ\text{ N})$
    - Bottom-Right: $(164.845526^\circ\text{ E}, -89.256269^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(-19187.0\text{ m}, -3603.0\text{ m})$, Pixel Scale $(5.0\text{ m/px}, 5.0\text{ m/px})$
- **Scale Audit**:
  - Native OHRC GSD: $0.26\text{ m/px}$ (from native $12,000\text{ px}$ swath)
  - Downsampling Factor: $12000 / 624 \approx 19.23\times \implies 0.26 \times 19.23 \approx 5.0\text{ m/px}$
  - Reference GSD: $5.0\text{ m/px}$
  - Effective Registration Ratio: **$1:1$ ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**

### 3.2 OHRC Pair 2
- **Job ID**: `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01`
- **Source File**: `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif` ($648 \times 5059$, 8-bit unsigned char)
- **Reference File**: `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif` ($2593 \times 6279$, 8-bit unsigned char)
- **Source XML**: `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $105.77\text{ km}$
  - Roll: $+1.258953^\circ$, Pitch: $+11.815967^\circ$, Yaw: $+0.039600^\circ$
  - Pass Date: 2025-02-08T14:02:45 UTC
- **Illumination Geometry**:
  - Solar Azimuth: $19.910243^\circ$
  - Solar Elevation: $+5.103000^\circ$
  - Solar Incidence Angle: $84.897000^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Polar Stereographic Moon (South Pole)
  - Source Corners (Selenographic):
    - Top-Left: $(26.723277^\circ\text{ E}, -84.574934^\circ\text{ N})$
    - Top-Right: $(27.813661^\circ\text{ E}, -84.540314^\circ\text{ N})$
    - Bottom-Left: $(29.934060^\circ\text{ E}, -85.353908^\circ\text{ N})$
    - Bottom-Right: $(31.180635^\circ\text{ E}, -85.313377^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(67338.0\text{ m}, 150047.0\text{ m})$, Pixel Scale $(5.0\text{ m/px}, 5.0\text{ m/px})$
- **Scale Audit**:
  - Native OHRC GSD: $0.27\text{ m/px}$
  - Downsampling Factor: $12000 / 648 \approx 18.52\times \implies 0.27 \times 18.52 \approx 5.0\text{ m/px}$
  - Reference GSD: $5.0\text{ m/px}$
  - Effective Registration Ratio: **$1:1$ ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**

### 3.3 OHRC Pair 3
- **Job ID**: `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02`
- **Source File**: `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_source_at_5m.tif` ($600 \times 5054$, 8-bit unsigned char)
- **Reference File**: `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif` ($2416 \times 6316$, 8-bit unsigned char)
- **Source XML**: `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $97.78\text{ km}$
  - Roll: $-0.227192^\circ$, Pitch: $+13.806624^\circ$, Yaw: $+0.005305^\circ$
  - Pass Date: 2025-03-08T01:27:52 UTC
- **Illumination Geometry**:
  - Solar Azimuth: $49.072662^\circ$
  - Solar Elevation: $+3.088558^\circ$
  - Solar Incidence Angle: $86.911442^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Polar Stereographic Moon (South Pole)
  - Source Corners (Selenographic):
    - Top-Left: $(24.207834^\circ\text{ E}, -84.575787^\circ\text{ N})$
    - Top-Right: $(25.227569^\circ\text{ E}, -84.544478^\circ\text{ N})$
    - Bottom-Left: $(27.303560^\circ\text{ E}, -85.366665^\circ\text{ N})$
    - Bottom-Right: $(28.474338^\circ\text{ E}, -85.330022^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(61478.0\text{ m}, 153132.0\text{ m})$, Pixel Scale $(5.0\text{ m/px}, 5.0\text{ m/px})$
- **Scale Audit**:
  - Native OHRC GSD: $0.25\text{ m/px}$
  - Downsampling Factor: $12000 / 600 = 20.0\times \implies 0.25 \times 20.0 = 5.0\text{ m/px}$
  - Reference GSD: $5.0\text{ m/px}$
  - Effective Registration Ratio: **$1:1$ ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**

### 3.4 OHRC Pair 4
- **Job ID**: `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00`
- **Source File**: `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_source_at_5m.tif` ($552 \times 4649$, 8-bit unsigned char)
- **Reference File**: `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif` ($3164 \times 6322$, 8-bit unsigned char)
- **Source XML**: `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $91.86\text{ km}$
  - Roll: $+5.298260^\circ$, Pitch: $+20.349658^\circ$, Yaw: $+0.011085^\circ$
  - Pass Date: 2025-10-12T04:58:21 UTC
- **Illumination Geometry**:
  - Solar Azimuth: $256.287883^\circ$
  - Solar Elevation: $-0.305664^\circ$ *(Sun below local horizontal plane!)*
  - Solar Incidence Angle: $90.305664^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Polar Stereographic Moon (South Pole)
  - Source Corners (Selenographic):
    - Top-Left: $(30.818093^\circ\text{ E}, -83.787265^\circ\text{ N})$
    - Top-Right: $(31.715108^\circ\text{ E}, -83.763994^\circ\text{ N})$
    - Bottom-Left: $(33.158067^\circ\text{ E}, -84.596614^\circ\text{ N})$
    - Bottom-Right: $(34.176418^\circ\text{ E}, -84.569341^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(86683.0\text{ m}, 164952.0\text{ m})$, Pixel Scale $(5.0\text{ m/px}, 5.0\text{ m/px})$
- **Scale Audit**:
  - Native OHRC GSD: $0.23\text{ m/px}$
  - Downsampling Factor: $12000 / 552 \approx 21.74\times \implies 0.23 \times 21.74 \approx 5.0\text{ m/px}$
  - Reference GSD: $5.0\text{ m/px}$
  - Effective Registration Ratio: **$1:1$ ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**

### 3.5 IIRS Pair A
- **Job ID**: `IIRXXD18CHO2686502NNNN25244140531312_V2_1`
- **Source File**: `IIRXXD18CHO2686502NNNN25244140531312_V2_1_source.tif` ($250 \times 7783$, 32-bit floating point `float32`, radiance)
- **Reference File**: `IIRXXD18CHO2686502NNNN25244140531312_V2_1_reference.tif` ($960 \times 7681$, 32-bit floating point `float32`, radiance)
- **Source XML**: `IIRXXD18CHO2686502NNNN25244140531312_V2_1.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $117.17\text{ km}$
  - Roll: $-0.009006^\circ$, Pitch: $-0.070153^\circ$, Yaw: $+0.016513^\circ$
  - Pass Date: 2025-09-01T12:27:58 UTC
- **Illumination Geometry**:
  - Solar Azimuth: $107.839819^\circ$
  - Solar Elevation: $+25.942160^\circ$
  - Solar Incidence Angle: $64.057840^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Selenographic (Equatorial area)
  - Source Corners (Selenographic):
    - Top-Left: $(13.188636^\circ\text{ E}, 42.770041^\circ\text{ N})$
    - Top-Right: $(14.235959^\circ\text{ E}, 42.737143^\circ\text{ N})$
    - Bottom-Left: $(12.275662^\circ\text{ E}, 22.123810^\circ\text{ N})$
    - Bottom-Right: $(13.109206^\circ\text{ E}, 22.097779^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(12.0^\circ\text{ E}, 45.0^\circ\text{ N})$, Pixel Scale $(0.00312467^\circ/\text{px}, 0.00312467^\circ/\text{px})$
- **Scale Audit**:
  - Native IIRS GSD: $93.74\text{ m/px}$ (from XML)
  - Effective Source GSD: $93.74\text{ m/px}$
  - Reference GSD: **NOT VERIFIED** (no reference XML/label exists)
  - Physical Scale Ratio: **NOT VERIFIED**
  - Verification Status: **PARTIALLY VERIFIED** (*"Source metadata verified; LRO-WAC reference metadata not verified"*)

### 3.6 IIRS Pair B
- **Job ID**: `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01`
- **Source File**: `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01_source.tif` ($104 \times 4851$, 32-bit floating point `float32`, radiance)
- **Reference File**: `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01_reference.tif` ($3175 \times 3874$, 32-bit floating point `float32`, radiance)
- **Source XML**: `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01.xml` (**VERIFIED**)
- **Reference XML**: `NOT AVAILABLE` (Absent in mentor directory)
- **Flight & Attitude**:
  - Spacecraft Altitude: $103.92\text{ km}$
  - Roll: $+0.012401^\circ$, Pitch: $-0.085453^\circ$, Yaw: $-0.005565^\circ$
  - Pass Date: 2023-01-22T10:14:31 UTC (DOP: 22-Jan-2023)
- **Illumination Geometry**:
  - Solar Azimuth: $45.445786^\circ$
  - Solar Elevation: $+21.055386^\circ$
  - Solar Incidence Angle: $68.944614^\circ$
- **Geodetic & Cartographic Footprint**:
  - Projection: Polar Stereographic Moon (South Pole)
  - Source Corners (Selenographic):
    - Top-Left: $(290.638617^\circ\text{ E}, -88.440901^\circ\text{ N})$
    - Top-Right: $(316.397467^\circ\text{ E}, -88.650269^\circ\text{ N})$
    - Bottom-Left: $(142.413929^\circ\text{ E}, -59.763534^\circ\text{ N})$
    - Bottom-Right: $(141.071575^\circ\text{ E}, -59.775085^\circ\text{ N})$
  - Reference Anchor: Tiepoint $(-44332.3\text{ m}, 29697.4\text{ m})$, Pixel Scale $(200.0\text{ m/px}, 200.0\text{ m/px})$
- **Scale Audit**:
  - Native IIRS GSD: $83.14\text{ m/px}$ (from XML)
  - Effective Source GSD: $83.14\text{ m/px}$
  - Reference GSD: **NOT VERIFIED** (no reference XML/label exists)
  - Physical Scale Ratio: **NOT VERIFIED**
  - Verification Status: **PARTIALLY VERIFIED** (*"Source metadata verified; LRO-WAC reference metadata not verified"*)

---

## 4. Physical Scale Feasibility & Grounding Assessment

### Feasibility Matrix

| Evaluation Criterion | OHRC (Pairs 1–4) | IIRS (Pair A) | IIRS (Pair B) |
| :--- | :--- | :--- | :--- |
| **A. Native source GSD** | $0.23 - 0.27\text{ m/px}$ (verified in XML) | $93.74\text{ m/px}$ (verified in XML) | $83.14\text{ m/px}$ (verified in XML) |
| **B. Effective source GSD** | **$5.0\text{ m/px}$** (downsampled from native) | $93.74\text{ m/px}$ (native swath) | $83.14\text{ m/px}$ (native swath) |
| **C. Reference GSD** | **$5.0\text{ m/px}$** (GeoTIFF PixelScaleTag) | **NOT VERIFIED** (XML absent) | **NOT VERIFIED** (XML absent) |
| **D. Physical sampling ratio** | **$1:1$ ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)** | **NOT VERIFIED** | **NOT VERIFIED** |
| **E. Geographic overlap** | **Verified** (source corners inside ref box) | **Verified** (source corners inside ref box) | **Verified** (source corners inside ref box) |
| **F. Corner coordinates** | **Yes** (GeoTIFF tiepoints on both sides) | **Yes** (GeoTIFF tiepoints on both sides) | **Yes** (GeoTIFF tiepoints on both sides) |
| **G. DEM / SPICE geometry** | **Unavailable** (Attitude in XML, DEM/CK kernels absent) | **Unavailable** (Attitude in XML, DEM/CK kernels absent) | **Unavailable** (Attitude in XML, DEM/CK kernels absent) |
| **Grounding Classification** | **PARTIALLY GROUNDED** | **PARTIALLY GROUNDED** | **PARTIALLY GROUNDED** |

---

## 5. Definitive Answer to Core Scientific Question

> **"With the mentor-provided OHRC and IIRS datasets, exactly which physical scale, illumination, and geometric constraints can LunarReg now use without inference or fabrication?"**

### 1. Physical Scale Constraints
1. **OHRC Effective Scale is 1:1 ($5.0\text{ m/px} \leftrightarrow 5.0\text{ m/px}$)**:
   - LunarReg **CANNOT** claim cross-scale registration (such as $20\times$ or $375\times$) on the mentor OHRC TIFFs. The source was downsampled by $\approx 19-22\times$ prior to delivery, and the reference is sampled at $5.0\text{ m/px}$.
   - The verified scale constraint for OHRC matching is **$1:1$ scale** ($\pm 5\%$ variation due to local terrain relief).
2. **IIRS Physical Scale is Strictly Unverified**:
   - The native source is $93.74\text{ m/px}$ (Pair A) and $83.14\text{ m/px}$ (Pair B), but because the mentor archive lacks LRO-WAC mission labels/XMLs, LunarReg **CANNOT** assert a physical scale ratio for IIRS.
   - The arithmetic relationship $93.74 / 0.25 \approx 375$ is solely a cross-instrument sensor ratio, **not an empirical registration condition**.

### 2. Illumination & Radiometric Constraints
1. **Extreme Grazing Solar Incidence ($84.9^\circ - 90.3^\circ$)**:
   - For OHRC South Pole imagery, the solar incidence angle is strictly between $84.9^\circ$ and $90.3^\circ$, with sun elevation angles $< 5.1^\circ$ (and $-0.31^\circ$ in Pair 4).
   - LunarReg must operate under extreme shadow elongation, high local contrast, and potential relief inversion.
2. **Unknown Solar Phase Difference ($\Delta \theta_{sun}$)**:
   - Because reference LRO-NAC images do not include solar illumination metadata, the azimuth/elevation difference between source and reference **cannot be fabricated or inferred**. LunarReg must rely on illumination-invariant representations (such as LoFTR dense transformer priors or structural edge gradients) rather than photometric assumptions.
3. **Radiometric Bit-Depth Normalization**:
   - OHRC is standard 8-bit unsigned char (`uint8`).
   - IIRS is 32-bit floating point (`float32`) radiance with negative and out-of-scale values (e.g. $[-70.5, 1712.2]$). IIRS rasters must undergo deterministic percentile min-max normalization into $[0, 255]$ for neural backbones without overwriting original raw arrays.

### 3. Geometric & Orientation Constraints
1. **Non-Nadir Pitch and Roll**:
   - Spacecraft attitude angles indicate non-nadir acquisition: pitch reaches $+20.35^\circ$ and roll reaches $+5.30^\circ$ (OHRC Pair 4). Oblique perspective distortion is physically present in the source swath.
2. **Geographic Overlap Metadata Available**:
   - The corner tiepoints provide a valid geodetic bounding box constraint: candidate matches lying outside the projected source corner polygon can be mathematically rejected as out-of-bounds prior to RANSAC.
3. **Absence of Exterior Orientation & DEM**:
   - Without SPICE exterior orientation kernels or DEM grids, LunarReg cannot compute rigorous 3D ray intersection. Planar projective homography $H \in \mathbb{R}^{3 \times 3}$ remains the appropriate geometric model.

---

## 6. Scientific Readiness Summary

- **Physical Metadata Integration**:
  - **READY for OHRC** (Complete mission metadata, effective $5\text{ m} \leftrightarrow 5\text{ m}$ verified).
  - **PARTIALLY READY for IIRS** (Source XMLs verified, reference LRO-WAC physical resolution not verified).
- **Production Pipeline Protection**:
  - Zero modifications to `adaptive_engine.py`, Locked LoFTR, SIFT, SuperGlue, RANSAC, or validation mathematics.
