# Phase 22 — Target E: Reference Image Physical Model & Geometric Feasibility Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22 — Authoritative 3D Input Acquisition & Verification  
**Target:** Target E — Reference Image Physical Model Audit  
**Status:** COMPLETE & VERIFIED  
**Date:** September 24, 2026  

---

## 1. Executive Summary

This report evaluates whether the reference images provided in the mentor benchmark (`OHRC_PAIR_01` to `OHRC_PAIR_04`) possess the physical sensor and flight telemetry required to support a bidirectional 3D ray-tracing or illumination simulation.

### Explicit Determination
> **The reference images in the mentor pairs CANNOT be modeled as perspective or linescan ray cameras.**  
> **They can ONLY be modeled as 2D map-projected, orthorectified surface rasters.**  
>
> Consequently, **differential illumination and mutual shadow back-projection cannot be reconstructed from verified metadata**, because the reference rasters lack sensor geometry, flight ephemeris, acquisition timestamps, and solar vector telemetry.

---

## 2. Technical Evaluation Across Physical Modeling Parameters

| Physical Parameter | Required for Ray Modeling | Available in Mentor Reference | Source / Metadata Verification | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Sensor Architecture** | Perspective frame or linescan TDI model | **ABSENT** | GeoTIFF tags / image header | Raster is a pre-projected 2D pixel array. |
| **Camera Intrinsics** | $f, c_x, c_y, p_x, p_y, \text{distortion}$ | **ABSENT** | No camera calibration block | No focal length or lens model exists. |
| **Acquisition Timestamp** | UTC start/stop, line exposure clock | **ABSENT** | No temporal metadata in raster or XML | Composite/resampled mosaic without temporal bounds. |
| **Spacecraft Flight Ephemeris** | State trajectory $\vec{R}(t), \vec{V}(t)$ | **ABSENT** | No SPK or orbital state | Spacecraft position in space is completely undefined. |
| **Pointing / Attitude** | Quaternions $q(t)$, camera boresight | **ABSENT** | No CK or attitude matrix | Sensor look-vectors cannot be cast into 3D space. |
| **Solar Angles** | Sun azimuth, elevation, incidence, phase | **ABSENT** | No photometric metadata | Sun direction vector during acquisition is unknown. |
| **Map Projection** | Cartographic projection definition | **PRESENT** | GeoTIFF GeoKey / Polar Stereographic | Polar Stereographic ($R = 1737.4\text{ km}$, $\text{lat}_0 = -90^\circ$). |
| **Ground Pixel Resolution** | Scale ($m/\text{pixel}$) | **PRESENT** | GeoTIFF PixelScale | Fixed at $5.000\text{ m/pixel}$ across all pairs. |
| **DEM Vertical Datum** | Elevation surface used for orthorectification | **UNKNOWN** | Unrecorded in metadata | Historical orthorectification DTM is undocumented. |

---

## 3. Detailed Forensic Findings per Pair

### 3.1 `OHRC_PAIR_01` Reference Raster
- **Source File:** `ref_pair_01.tif` (and corresponding quick-load cached arrays)
- **Spatial Coverage:** Polar Stereographic bounding box centered near $89.36^\circ\text{S}$, $134.2^\circ\text{E}$ (extreme south polar crater wall).
- **Physical Sensor Telemetry:** Zero. No metadata describes the spacecraft (e.g., LRO-NAC or KPLO) or the sensor that captured the raw photons.
- **Orthorectification Status:** The image is already resampled to map coordinates ($5.0\text{ m/px}$). Relief displacement from vertical topography has either been partially eliminated by orthorectification against an unrecorded DTM or remains as 2D distortion.
- **Illumination Condition:** Low-elevation grazing illumination with sharp shadows. However, the azimuth of the illuminator and the solar elevation angle are absent from all accompanying metadata.

### 3.2 `OHRC_PAIR_02` Reference Raster
- **Source File:** `ref_pair_02.tif`
- **Spatial Coverage:** Centered near $84.95^\circ\text{S}$, $33.6^\circ\text{W}$.
- **Physical Sensor Telemetry:** Absent.
- **Orthorectification Status:** Standard 2D cartographic raster at $5.0\text{ m/px}$.
- **Illumination Condition:** Grazing south-polar sunlight, but exact solar vector is unrecoverable.

### 3.3 `OHRC_PAIR_03` Reference Raster
- **Source File:** `ref_pair_03.tif`
- **Spatial Coverage:** Centered near $84.96^\circ\text{S}$, $33.6^\circ\text{W}$ (same geographic target as Pair 02).
- **Physical Sensor Telemetry:** Absent.
- **Orthorectification Status:** 2D cartographic raster at $5.0\text{ m/px}$.
- **Illumination Condition:** Grazing sunlight with noticeable shadow orientation difference relative to source strip.

### 3.4 `OHRC_PAIR_04` Reference Raster
- **Source File:** `ref_pair_04.tif`
- **Spatial Coverage:** Centered near $84.18^\circ\text{S}$, $33.9^\circ\text{W}$.
- **Physical Sensor Telemetry:** Absent.
- **Orthorectification Status:** 2D cartographic raster at $5.0\text{ m/px}$.
- **Illumination Condition:** Grazing sunlight with distinct shadow fill.

---

## 4. Architectural & Modeling Implications for 3D Experiments

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAY-TRACING FEASIBILITY                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   SOURCE IMAGE (OHRC Strip):                                                │
│   • Sensor: Verified Linescan TDI (SAC/URSC official IK: f = 2080.0 mm)    │
│   • Orbit: Verified SPK Ephemeris (URSC Flight Dynamics via USGS)           │
│   • Attitude: Verified CK Quaternions (USGS S3 archive)                     │
│   • DEM: LOLA 20m/px (LDEM_80S_20M)                                        │
│   ──► CAN cast 3D camera rays to DEM terrain surface (FORWARD PROJECTION)   │
│                                                                             │
│   REFERENCE IMAGE (2D Map Tile):                                            │
│   • Sensor: UNKNOWN / ABSENT                                                │
│   • Orbit / Attitude: UNKNOWN / ABSENT                                      │
│   • Solar Vectors: UNKNOWN / ABSENT                                         │
│   ──► CANNOT cast rays into space (NO CAMERA MODEL)                         │
│   ──► CANNOT simulate shadows (NO SOLAR VECTOR)                             │
│   ──► CANNOT back-project terrain to sensor frame                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Asymmetric Projection Paradigm
Because the reference is purely a 2D map raster, any future 3D investigation must operate under an **asymmetric projection architecture**:
1. **Source-to-Map (Orthorectification):** Cast rays from the OHRC linescan TDI sensor through space, intersect the NASA LOLA 20m DEM, and reproject the source pixels onto the reference's Polar Stereographic coordinate reference system.
2. **Terrain-to-Reference:** Evaluate whether orthorectified source pixels align with the pre-orthorectified reference raster in map coordinates.
3. **Reference-to-Camera (Impossible):** It is physically impossible to reverse-project the reference pixels into a 3D camera perspective, because no camera center $\vec{C}_{\text{ref}}$, orientation matrix $\mathbf{R}_{\text{ref}}$, or focal length $f_{\text{ref}}$ exists.

### 4.2 Impact on Differential Illumination Modeling
The Track D/E diagnostics previously demonstrated that shadow disparity is a primary suspected factor in matching failure.
However:
- Without the solar azimuth and elevation for the reference raster, **shadows in the reference cannot be physically re-rendered or inverted**.
- We can compute the solar vector for the *source* pass (using SPICE `spkezr` for the Sun relative to the Moon at the source UTC epoch), but we cannot compute the solar vector for the reference.
- Any radiometric shadow compensation on the reference must therefore rely on image-domain heuristics (e.g., thresholding, morphology, or edge descriptors) rather than physical bidirectional reflectance distribution functions (BRDF) or 3D ray-traced shadows.

---

## 5. Conclusion & Recommendations

1. **Treat Reference Exclusively as Ground-Truth Surface Geometry:** The reference rasters can only serve as planar cartographic targets in Polar Stereographic space ($x, y$ meters on the lunar ellipsoid).
2. **Never Fabricate Reference Intrinsics:** Under no circumstances should synthetic camera matrices or assumed perspective pinhole models be assigned to the reference rasters.
3. **Approved Pathway for Future 3D Work:**
   - Use LOLA DEM (`LDEM_80S_20M`) and official OHRC SPICE kernels (`ch2_ohr_v01.ti`, SPK, CK) to generate a physically orthorectified source raster in Polar Stereographic space.
   - Compare the orthorectified source raster directly against the 2D reference mosaic.
   - Do not attempt bidirectional ray-tracing or reference shadow simulation.
