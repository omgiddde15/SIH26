# Scientific Report: 3D Viewpoint & Terrain Feasibility / Metadata Sufficiency Audit

**Document Status:** FORMAL RESEARCH FEASIBILITY AUDIT  
**Execution Date:** September 24, 2026  
**Target Datasets:** Chandrayaan-2 OHRC Datasets (`OHRC_PAIR_01` to `OHRC_PAIR_04`), Secondary IIRS (`PAIR_A`, `PAIR_B`)  
**Production Pipeline Status:** **100% FROZEN AND UNTOUCHED**  
**Global Recommendation:** **STRICTLY HOLD 3D RAY-TRACING EXPERIMENT**  

---

## 1. Core Research Question & Scope
> **“Do the mentor datasets contain sufficient verified metadata and terrain information to perform a physically meaningful 3D source/reference visibility and projection analysis?”**

### 1.1 Strict Scientific Separations & Governance Rules
- A 3D ray-tracing experiment is scientifically valid **only if** its physical inputs (DEM, camera intrinsics, spacecraft state vectors, pointing models) are rigorously available from verified telemetry.
- In accordance with strict experimental governance:
  - Do NOT fabricate or invent a DEM.
  - Do NOT fabricate camera intrinsics.
  - Do NOT assume nadir viewing.
  - Do NOT infer SPICE orbit state vectors.
  - Do NOT assume a generic camera model.
  - Do NOT treat scalar altitude + pitch/roll as a complete ray model.
  - Do NOT claim physical accuracy without independent validation.

---

## 2. Track A — Terrain Data Availability
- **Status:** `DEM_REQUIRED_BUT_NOT_AVAILABLE`
- **Audit Scope:** An exhaustive search was conducted across:
  1. The mentor dataset directory (`C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc` and `\IIRS`)
  2. The project repository root (`c:\Users\Dell\Videos\SIH26_Lunar_Registration`)
  3. Project data directories (`data/`, `data/metadata/`, `data/research/`)
  4. Research directories and historical benchmark artifacts (`research/multimodal/`, `research/adaptive_matcher/`)
- **Audit Findings:**
  - Found files matching elevation extensions (`.dem`, `.dtm`, `.grd`, `.h5`, `.nc`): **0 files**.
  - Found external digital elevation models: **None**.
  - Found topographic profile data covering mentor footprints: **None**.
- **Determination:** No usable digital elevation model (DEM) is present. Substituting an arbitrary, planar, or synthetic spherical surface is scientifically impermissible, as it would fabricate the very topographic relief under investigation.

---

## 3. Track B — Camera & Sensor Geometry Audit

| Sensor Parameter | Verified Value (Source) | Classification | Reference Value | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Focal Length ($f$)** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Principal Point ($c_x, c_y$)** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Pixel Pitch ($\mu m$)** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Detector Elements** | 12000 pixels across track | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **TDI Stages** | TDI64 | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Integration Time** | 162.10 – 174.87 ms | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Optical Distortion Coeffs** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Camera Model Formulation** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Sensor Boresight Matrix** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Viewing Angles / Line-of-Sight** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |

- **Key Finding:** While the PDS4 XML labels confirm that OHRC is a pushbroom line scanner operating with TDI64 and an integration time of ~170 ms, **critical intrinsic parameters (focal length, principal point, pixel pitch, and lens distortion) are completely absent**. Inferring intrinsics from raster dimensions is physically invalid.

---

## 4. Track C — Spacecraft State & Ephemeris Audit

| State Parameter | Verified Value (Source) | Classification | Reference Value | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Orbit Number** | Imaging: 23595–27360, Dumping: 23596–27367 | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Spacecraft Altitude** | 91.86 – 105.77 km (scalar) | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Spacecraft Roll** | -0.23° to +5.30° (scalar) | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Spacecraft Pitch** | -14.55° to +20.35° (scalar) | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Spacecraft Yaw** | -0.001° to +0.040° (scalar) | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Acquisition Start/Stop UTC** | Verified UTC timestamps (~16.4s duration) | `VERIFIED METADATA` | Not Present | `NOT PRESENT` |
| **Spacecraft 3D Position $\vec{R}(t)$** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Spacecraft 3D Velocity $\vec{V}(t)$** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **Time-Dependent Pointing $q(t)$** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |
| **SPICE Kernel References (SPK/CK)** | Not Present | `NOT PRESENT` | Not Present | `NOT PRESENT` |

- **Critical Scientific Distinction:**  
  The metadata provides **instantaneous scalar altitude and attitude angles**, which represent an aggregate summary for the ~16-second acquisition pass. This is **not a complete spacecraft state vector**. A pushbroom scanner builds an image line-by-line as the spacecraft orbits at ~1.6 km/s; rigorous ray-tracing requires instantaneous position $\vec{R}(t)$ and attitude quaternion $q(t)$ for every scanline. These are completely absent without validated SPICE SPK/CK kernels.

---

## 5. Track D — Image Geometry & Ray Model Construction
- **Mentor Source Raster:**  
  Classified as an **unorthorectified downsampled image strip with corner selenographic tiepoints**.  
  - Dims: 552–648 px width $\times$ 4649–5059 px length (downsampled ~19.23× from the native 12,000 $\times$ ~95,000 px detector stream).  
  - Georeferencing is defined solely by 4 corner tiepoints in GeoTIFF Tag 33922 (ModelTiepointTag) and PDS4 XML `<corners>`. It does not possess a map projection matrix.
- **Mentor Reference Raster:**  
  Classified as a **resampled map-projected orthorectified mosaic product (Polar Stereographic)**.  
  - ModelPixelScaleTag: 5.0 m/px; ModelTiepointTag: polar stereographic Cartesian coordinates.  
  - It does not contain sensor geometry, detector scanlines, or acquisition parameters.
- **Ray-Model Feasibility:**  
  - **Source:** `UNCONSTRUCTIBLE`. Without camera intrinsics, mounting matrix, and time-dependent trajectory vectors, a pixel-to-ray mapping cannot be mathematically established.  
  - **Reference:** `UNCONSTRUCTIBLE`. The reference image is a resampled 2D cartographic mosaic; it does not correspond to a single optical perspective center.

---

## 6. Track E — Illumination Geometry Audit

| Parameter | Source Image Status | Reference Image Status | Dual-Modality Status |
| :--- | :--- | :--- | :--- |
| **Solar Incidence Angle** | Verified (84.90° – 90.31°) | Not Present | **INCOMPLETE** |
| **Solar Elevation Angle** | Verified (-0.31° to 5.10°) | Not Present | **INCOMPLETE** |
| **Solar Azimuth Angle** | Verified (19.91° – 299.64°) | Not Present | **INCOMPLETE** |
| **Acquisition Timestamp** | Verified UTC string | Not Present | **INCOMPLETE** |
| **Emission / Phase Angle** | Not Present | Not Present | **ABSENT** |

- **Determination:** Although the source XML documents solar incidence, elevation, and azimuth at the time of source pass, the reference image contains **zero illumination metadata**. Consequently, the differential solar vector between source and reference cannot be determined from verified metadata, preventing mutual shadow back-projection or photometric rendering.

---

## 7. Track F — Physical 3D Feasibility Requirements Matrix

| Requirement | Available? | Evidence Source | Confidence | Impact on 3D Ray-Tracing |
| :--- | :---: | :--- | :--- | :--- |
| **Lunar DEM / Elevation Surface** | **NO** | Repository & mentor directories | HIGH (Conclusively Absent) | **FATAL:** Surface intersection target does not exist. |
| **Camera Intrinsics ($f, c_x, c_y$, pitch)** | **NO** | XML & GeoTIFF audit | HIGH (Conclusively Absent) | **FATAL:** Camera rays cannot be cast. |
| **Spacecraft Trajectory Vectors $\vec{R}(t)$** | **NO** | PDS4 XML metadata | HIGH (Conclusively Absent) | **FATAL:** Perspective center origin unknown. |
| **Spacecraft Attitude Quaternions $q(t)$** | **NO** | PDS4 XML metadata | HIGH (Conclusively Absent) | **FATAL:** Ray pointing directions unknown. |
| **Reference Ephemeris & Illumination** | **NO** | Reference GeoTIFF | HIGH (Conclusively Absent) | **FATAL:** Cannot model reference perspective. |
| **Source Acquisition Timestamps** | **YES** | XML `<start_time_utc>` | HIGH (Verified Present) | Sufficient for time-stamping only. |
| **Source Scalar Solar Angles** | **YES** | XML `<Sun_azimuth...>` | HIGH (Verified Present) | Provides nominal source solar direction only. |
| **2D Map Georeferencing** | **YES** | GeoTIFF tags (33922, 33550) | HIGH (Verified Present) | Enables 2D geographic bounding only. |

---

## 8. Track G — Experiment Readiness Classification

| Dataset ID | Instrument | Category | Feasibility Classification | Primary Deficiencies |
| :--- | :--- | :--- | :--- | :--- |
| **`OHRC_PAIR_01`** | OHRC | Primary OHRC | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris $\vec{R}(t), q(t)$; No Ref Metadata |
| **`OHRC_PAIR_02`** | OHRC | Primary OHRC | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris $\vec{R}(t), q(t)$; No Ref Metadata |
| **`OHRC_PAIR_03`** | OHRC | Primary OHRC | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris $\vec{R}(t), q(t)$; No Ref Metadata |
| **`OHRC_PAIR_04`** | OHRC | Primary OHRC | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris $\vec{R}(t), q(t)$; No Ref Metadata |
| **`IIRS_PAIR_A`** | IIRS | Secondary Diagnostic | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris; No Ref Metadata |
| **`IIRS_PAIR_B`** | IIRS | Secondary Diagnostic | **`C. NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`** | No DEM; No Intrinsics; No Ephemeris; No Ref Metadata |

---

## 9. Addressing the 8 Core Audit Questions

### 1. What verified 3D inputs do we actually have?
- For the **Source Raster**: Static scalar altitude (`spacecraft_altitude_in_km`), static spacecraft body attitude angles (`Roll_in_degree`, `Pitch_in_degree`, `Yaw_in_degree`), solar vector angles (`Sun_azimuth`, `Sun_elevation`, `Solar_incidence`), acquisition start/stop UTC timestamps, detector line parameters (`raw_no_of_pix = 12000`, `LUT_TDIStages = TDI64`, `integration_time_ms`), and 4-corner selenographic/projected tiepoints.
- For the **Reference Raster**: 2D cartographic map projection definition (Polar Stereographic Moon), pixel scale ($5.0\text{ m/px}$), raster origin tiepoint, and raster dimensions.

### 2. What critical inputs are missing?
1. **Digital Elevation Model (DEM):** Zero elevation or topography data is available in the mentor dataset or repository (`DEM_REQUIRED_BUT_NOT_AVAILABLE`).
2. **Camera Intrinsics:** Focal length $f$, principal point $(c_x, c_y)$, detector pitch, and optical distortion coefficients are entirely absent.
3. **Sensor Alignment / Boresight:** The rotation matrix relating the sensor optical bench to the spacecraft mechanical frame is missing.
4. **Complete Spacecraft State Trajectory:** 3D orbit position vector $\vec{R}(t)$ and velocity $\vec{V}(t)$ are missing.
5. **Time-Dependent Pointing:** Attitude quaternion stream $q(t)$ across scanlines is missing.
6. **Reference Raster Metadata:** Acquisition date/time, viewing angles, and solar illumination vectors for the reference image are missing.

### 3. Can the mentor source image be ray-modeled?
- **NO.** The source image is a pushbroom line scanner acquired dynamically over ~16 seconds. Casting physical optical rays requires camera intrinsics, sensor mounting calibration, and time-dependent trajectory/attitude vectors for each scanline. None of these parameters is present.

### 4. Can the reference image be ray-modeled?
- **NO.** The reference raster is a pre-existing 2D map-projected orthorectified mosaic. It does not possess a single optical center of projection, camera model, or flight ephemeris.

### 5. Can terrain intersection be computed?
- **NO.** Computing surface intersection requires both mathematical ray definitions and a 3D elevation boundary ($z = f(x, y)$). Because neither rays nor a DEM are available, terrain intersection cannot be calculated.

### 6. Can illumination geometry be computed?
- **PARTIALLY FOR SOURCE, NO FOR REFERENCE.** Source solar angles provide a single nominal illumination vector across the scene. However, the reference image contains zero illumination metadata, preventing differential shadow back-projection or photometric rendering.

### 7. Is a physical 3D experiment ready now?
- **NO (`NOT READY — INSUFFICIENT PHYSICAL MODEL INFORMATION`).** Conducting a "3D ray-tracing experiment" with the currently available data would require inventing a synthetic DEM and guessing camera intrinsics, which violates the strict scientific requirement against data fabrication.

### 8. If not, exactly what verified data are required before proceeding?
To conduct a rigorous, physically validated 3D viewpoint/terrain experiment, the following verified external data must be officially provided and ingested:
1. **High-Resolution Lunar DEM:** A verified polar topographic model (e.g. SLDEM2015 or LOLA Polar DTM at $\le 20\text{ m/px}$) covering latitudes $83^\circ\text{S} - 90^\circ\text{S}$.
2. **PDS4 Instrument Kernel (IK) or Sensor Calibration Report:** Documenting the OHRC optical focal length, principal point, and pixel pitch.
3. **SPICE Kernels (NASA/ISDA / ISRO):**
   - **SPK (Spacecraft and Planet Ephemeris):** Trajectory vector $\vec{R}(t)$ for Chandrayaan-2 orbiter during orbits 23595–27360.
   - **CK (Spacecraft Attitude):** Orientation quaternion $q(t)$ for the orbiter.
   - **FK (Frame Kernel):** Coordinate frame definitions for Chandrayaan-2 and OHRC.
   - **SCLK (Spacecraft Clock):** Accurate conversion between detector scanline times and ephemeris time.
4. **Reference Raster Metadata / Product Label:** Establishing the acquisition epoch and solar illumination angles of the reference mosaic.

---

## 10. Production Safeguards Enforced
- `app/adaptive_engine.py`: **UNTOUCHED**
- `app/registration_core.py`: **UNTOUCHED**
- `app/app.py`: **UNTOUCHED**
- `research/adaptive_matcher/adaptive_engine.py`: **UNTOUCHED**
- Quality gates, thresholds, and LoFTR weights: **100% LOCKED**
