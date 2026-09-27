# Phase 22.6 — Pixel-Center & Coordinate Convention Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report explicitly establishes the pixel-center and coordinate registration conventions across the mentor-provided GeoTIFF rasters, the native OHRC detector array, and the SPICE instrument frame.

### Key Conclusions:
1. **Delivered GeoTIFF Convention:**  
   The mentor GeoTIFF files explicitly encode GeoKey `1025` (`GTRasterTypeGeoKey`) $= 1$ (`RasterPixelIsArea`).  
   - Integer coordinate $(u, v)$ represents the **upper-left outer corner** of the pixel.
   - The **photometric / radiometric center** of pixel $(u, v)$ is located at:
     $$(u_{\text{center}}, v_{\text{center}}) = (u + 0.5, v + 0.5)$$
2. **Native SPICE IK Detector Convention:**  
   The official ISRO Instrument Kernel (`ch2_ohr_v01.ti`) defines the optical center as:
   $$\text{INS-152270\_CENTER} = (6000.0, 0.5)$$
   - Samples are 1-indexed in SPICE text convention ($1$ to $12000$).
   - In 0-indexed sample space ($u_{\text{native}} \in [0, 11999]$), the center of pixel $u_{\text{native}}$ is at $u_{\text{native}} + 0.5$.
   - The optical axis / boresight intersects the focal plane exactly at sample $6000.0$.
3. **Declared Modeling Convention for Phase 23:**  
   All future physical ray-tracing and camera projection models must evaluate line-of-sight rays strictly through **pixel centers $(u + 0.5, v + 0.5)$**, avoiding half-pixel systematic parallax offsets.

---

## 2. GeoTIFF Tag Forensic Analysis

Inspection of the TIFF tag directory (`tag_v2`) for all mentor source rasters confirms:

```
GeoKeyDirectoryTag:
  Key 1024 (GTModelTypeGeoKey)   = 2 (ModelTypeGeographic)
  Key 1025 (GTRasterTypeGeoKey)  = 1 (RasterPixelIsArea)
  Key 2048 (GeographicTypeGeoKey)= 32767 (User-Defined Selenographic)
  Key 2054 (GeogAngularUnitsGeoKey) = 9102 (Angular_Degree)
  Key 2057 (GeogSemiMajorAxisGeoKey) = 1737400.0 meters
  Key 2058 (GeogSemiMinorAxisGeoKey) = 1737400.0 meters
```

### Distinction between PixelIsArea and PixelIsPoint:
- In `RasterPixelIsArea`, pixel $(0, 0)$ spans the continuous spatial interval $x \in [0.0, 1.0)$ and $y \in [0.0, 1.0)$.
- The tiepoints recorded in `ModelTiepointTag` (`0.0, 0.0, 0.0 -> Lon, Lat`) attach geographic coordinates to the **outer corner** of pixel $(0, 0)$.
- Therefore, evaluating a ray or map coordinate at integer index $0$ without the $+0.5$ half-pixel shift corresponds to the corner boundary, not the center of the imaged lunar surface patch.

---

## 3. Focal Plane Physical Coordinate Mapping

Let $u_{\text{native}} \in [0, 11999]$ be the 0-indexed detector sample index.  
- Pixel pitch: $p = 5.2\ \mu\text{m} = 0.0052\text{ mm}$.
- Calibrated focal length: $f = 2080.0\text{ mm}$.
- Detector array center: $c_{\text{sample}} = 6000.0$.

### Physical Focal Plane Distance ($X_{\text{fp}}$ along the detector array):
$$X_{\text{fp}}(u_{\text{native}}) = (u_{\text{native}} + 0.5 - c_{\text{sample}}) \cdot p = (u_{\text{native}} - 5999.5) \cdot 0.0052\text{ mm}$$

At extremes:
- First pixel center ($u_{\text{native}} = 0$):  
  $$X_{\text{fp}}(0) = (0.5 - 6000.0) \cdot 0.0052\text{ mm} = -31.1974\text{ mm}$$
- Array midpoint ($u_{\text{native}} = 5999$ and $6000$):  
  $$X_{\text{fp}}(5999) = -0.0026\text{ mm}, \quad X_{\text{fp}}(6000) = +0.0026\text{ mm}$$
- Last pixel center ($u_{\text{native}} = 11999$):  
  $$X_{\text{fp}}(11999) = (11999.5 - 6000.0) \cdot 0.0052\text{ mm} = +31.1974\text{ mm}$$

### Unit Look-Vector in `CH2_OHRC` Instrument Frame:
The optical axis is along $+X$, and the detector array is along $Z$:
$$\vec{v}_{\text{inst}}(u_{\text{native}}) = \frac{1}{\sqrt{f^2 + X_{\text{fp}}^2}} \begin{bmatrix} f \\ 0.0 \\ X_{\text{fp}}(u_{\text{native}}) \end{bmatrix} = \frac{1}{\sqrt{2080.0^2 + X_{\text{fp}}^2}} \begin{bmatrix} 2080.0 \\ 0.0 \\ X_{\text{fp}}(u_{\text{native}}) \end{bmatrix}$$

Maximum cross-track angular deflection at edge:
$$\theta_{\text{max}} = \arctan\left(\frac{31.1974\text{ mm}}{2080.0\text{ mm}}\right) = \arctan(0.01499875) = 0.85936^\circ \approx \pm 0.86^\circ$$
*(This matches `INS-152270_FOV_CROSS_ANGLE = ( 0.86 )` in `ch2_ohr_v01.ti` exactly).*

---

## 4. Declared Mapping Protocol for Delivered TIFF Pixels

When casting a ray for delivered TIFF pixel $(u_{\text{tiff}}, v_{\text{tiff}})$:
1. **Cross-Track Sample (Column):**
   $$u_{\text{native\_center}} = s_x \cdot (u_{\text{tiff}} + 0.5) - 0.5$$
   $$X_{\text{fp}} = (u_{\text{native\_center}} + 0.5 - 6000.0) \cdot 0.0052\text{ mm} = (s_x (u_{\text{tiff}} + 0.5) - 6000.0) \cdot 0.0052\text{ mm}$$
2. **Along-Track Line (Row):**
   The exposure center epoch is evaluated at row center $v_{\text{tiff}} + 0.5$:
   $$t(v_{\text{tiff}}) = t_{\text{start}} + \left(v_{\text{tiff}} + 0.5\right) \cdot \Delta t_{\text{tiff}}$$
3. **Consistency Rule:**
   Zero evaluation on integer boundaries $(u, v)$; always evaluate at half-integers $(u + 0.5, v + 0.5)$.

---

## 5. Technical Verdict

- GeoTIFF pixel convention: **`VERIFIED`** (`RasterPixelIsArea`).
- Native detector optical center: **`VERIFIED`** ($6000.0$ samples).
- Physical look-vector formulation: **`VERIFIED`** ($X_{\text{fp}} = [s_x(u + 0.5) - 6000] \times 5.2\ \mu\text{m}$).
