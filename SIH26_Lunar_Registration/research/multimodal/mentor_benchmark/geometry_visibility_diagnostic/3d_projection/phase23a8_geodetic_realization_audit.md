# Phase 23A.8 — Reference Raster Geodetic Realization & Frame Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit examines whether the geodetic reference frame realization of the mentor reference rasters can be determined from GeoTIFF tags, standards documentation, or official planetary cartographic specifications.

> ### **Primary Finding on Geodetic Realization:**
> # **`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`**  
> # **`Classification: REFERENCE_FRAME_UNRESOLVED`**  
> While the cartographic projection (Polar Stereographic) and horizontal reference sphere ($R = 1,737,400.0\text{ m}$) are verified, the physical geodetic realization (`MOON_ME_DE421` vs `IAU_MOON` vs `ULCN2005`) is completely unrecorded.

---

## 2. GeoKey Geodetic Parameters Matrix

| Parameter | GeoKey ID | Declared Value in Reference GeoTIFFs | Standard Interpretation | Realization Status |
| :--- | :---: | :--- | :--- | :---: |
| **Model Type** | 1024 | `1` (`ModelTypeProjected`) | Projected coordinate reference system | **`VERIFIED`** |
| **Raster Type** | 1025 | `1` (`RasterPixelIsArea`) | Integer grid coordinates define pixel area outer bounds | **`VERIFIED`** |
| **Citation** | 1026 | `PolarStereographic Moon\|` | Descriptive projection string | **`VERIFIED`** |
| **Geographic Type** | 2048 | `32767` (`UserDefined`) | Non-standard planetary GCS | **`VERIFIED`** |
| **Geog Citation** | 2049 | `GCS Name = GCS_Moon\|Datum = D_Moon\|Ellipsoid = Moon\|Primem = Reference_Meridian\|\|` | Generic ESRI/GDAL spheroid naming | **`UNKNOWN`** |
| **Geodetic Datum** | 2050 | `32767` (`UserDefined`) | Unassigned datum code | **`UNKNOWN`** |
| **Ellipsoid** | 2056 | `32767` (`UserDefined`) | Unassigned ellipsoid code | **`UNKNOWN`** |
| **Semi-Major Axis** | 2057 | `1737400.0` meters | Reference sphere radius | **`VERIFIED`** |
| **Semi-Minor Axis** | 2058 | `1737400.0` meters | Spherical body ($f = 0.0$) | **`VERIFIED`** |
| **Prime Meridian** | 2061 | `0.0` degrees | Zero longitude reference meridian | **`VERIFIED`** |

---

## 3. Methodological Prohibition: Inferences vs. Evidence

In accordance with Phase 23A.8 governance rules:
1. **Do NOT infer frame realization from projection name alone:** A Polar Stereographic projection can be constructed on `IAU_MOON`, `MOON_ME_DE421`, `MOON_PA_DE421`, or an arbitrary relative frame. The projection name `PolarStereographic Moon` conveys zero information about the realization epoch or libration model.
2. **Do NOT infer DE421 compatibility from matching radius alone:** The spherical radius $R = 1,737,400.0\text{ m}$ is the standard IAU Moon radius adopted by NASA, ISRO, and IAU working groups since 1982. It is used identically in `IAU_MOON` (PCK) and `MOON_ME_DE421`. A matching radius does not indicate DE421 realization.

---

## 4. Geodetic Realization Classification

- **`REFERENCE_FRAME_VERIFIED`**: **REJECTED** (No realization frame tag exists).
- **`REFERENCE_FRAME_PARTIALLY_VERIFIED`**: **APPLIES TO CARTOGRAPHY ONLY** (Projection type, origin, scale, and radius are verified; realization remains absent).
- **`REFERENCE_FRAME_UNRESOLVED`**: **`CONFIRMED AS PRIMARY SCIENTIFIC CLASSIFICATION`**.

> **Conclusion:** Because no authoritative document or tag identifies the lunar coordinate realization of the reference raster, the geodetic reference frame remains officially **`UNRESOLVED`**.
