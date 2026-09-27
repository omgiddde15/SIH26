# Phase 23A.6 — Reference Map Raster Cartographic & Geodetic Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.6 — Rigid Geodetic / Frame Offset Reconciliation  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit examines the actual GeoTIFF headers, tags, and GeoKeys of the four mentor reference rasters (`ref_pair_01.tif` to `ref_pair_04.tif`) to verify whether their map projection, datum, pixel scale, and geodetic realization match the LOLA DEM and source metadata.

---

## 2. Reference GeoTIFF Cartographic Metadata Audit Table

| Cartographic Property | Declared Reference Value | Classification | Forensic Basis | Cross-Check vs. LOLA DEM |
| :--- | :---: | :---: | :--- | :--- |
| **Projection Type** | `Polar Stereographic` | **`VERIFIED`** | GeoKey 1024 = 1 (`ModelTypeProjected`), Key 3075 = 15 (`CT_PolarStereographic`) | Matches LOLA DEM (`POLAR STEREOGRAPHIC`) |
| **Datum / Spheroid** | `Moon` (Spherical) | **`VERIFIED`** | GeoKey 2057/2058 = $1,737,400.0\text{ m}$, GeoKey 1026 = `PolarStereographic Moon` | Matches LOLA offset ($R = 1,737.4\text{ km}$) |
| **Semi-Major Axis ($A$)** | $1,737,400.0\text{ m}$ | **`VERIFIED`** | GeoKey 2057 (`GeogSemiMajorAxisGeoKey`) | Matches LOLA `A_AXIS_RADIUS` ($1,737.4\text{ km}$) |
| **Semi-Minor Axis ($C$)** | $1,737,400.0\text{ m}$ | **`VERIFIED`** | GeoKey 2058 (`GeogSemiMinorAxisGeoKey`) | Matches LOLA `C_AXIS_RADIUS` ($1,737.4\text{ km}$) |
| **Pixel Scale ($s_x, s_y$)** | $5.000\text{ m/px}, 5.000\text{ m/px}$ | **`VERIFIED`** | Tag 33550 (`ModelPixelScaleTag`) = `(5.0, 5.0, 0.0)` | Exact $4\times$ multiple of LOLA 20m ($20.0\text{ m}$) |
| **False Easting ($X_0$)** | $0.0\text{ m}$ | **`VERIFIED`** | GeoKey 3082 (`ProjFalseEastingGeoKey`) = `0.0` | Matches LOLA center offset ($0.0\text{ m}$) |
| **False Northing ($Y_0$)** | $0.0\text{ m}$ | **`VERIFIED`** | GeoKey 3083 (`ProjFalseNorthingGeoKey`) = `0.0` | Matches LOLA center offset ($0.0\text{ m}$) |
| **Central Meridian ($\lambda_0$)** | $0.0^\circ$ | **`VERIFIED`** | GeoKey 3095 (`ProjStraightVertPoleLongGeoKey`) = `0.0` | Matches LOLA `CENTER_LONGITUDE` ($0^\circ$) |
| **True Scale Latitude ($\phi_{\text{ts}}$)** | $-90.0^\circ$ | **`VERIFIED`** | GeoKey 3081 (`ProjNatOriginLatGeoKey`) = `-90.0`, Key 3092 ($k_0 = 1.0$) | Matches LOLA `CENTER_LATITUDE` ($-90^\circ$) |
| **Pixel Area Convention** | `RasterPixelIsArea` | **`VERIFIED`** | GeoKey 1025 = 1 (`RasterPixelIsArea`) | Integer grid defines pixel outer boundaries |
| **Raster Orientation** | North-Up ($+X$ East, $+Y$ North) | **`VERIFIED`** | Tiepoint defines top-left corner $(X_{\text{min}}, Y_{\text{max}})$ | Consistent standard cartographic canvas |
| **Geodetic Realization Frame** | Undocumented | **`UNKNOWN`** | Absent from GeoTIFF tags and metadata | LOLA specifies DE421 `MOON_ME`; reference is unstated |

---

## 3. Reference Canvas Bounds per Pair

| Pair ID | Raster Dimensions $(W \times H)$ | Tiepoint Origin $(X_0, Y_0)$ (m) | Ground Coverage $X$ (m) | Ground Coverage $Y$ (m) | Physical Ray Containment |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | $5916 \times 4232\text{ px}$ | `(-19187.0, -3603.0)` | $[-19187.0, +10393.0]$ | $[-24763.0, -3603.0]$ | **100% IN-BOUNDS** |
| **`OHRC_PAIR_02`** | $2593 \times 6279\text{ px}$ | `(+67338.0, +150047.0)` | $[+67338.0, +80303.0]$ | $[+118652.0, +150047.0]$ | **100% IN-BOUNDS** |
| **`OHRC_PAIR_03`** | $2416 \times 6316\text{ px}$ | `(+61478.0, +153132.0)` | $[+61478.0, +73558.0]$ | $[+121552.0, +153132.0]$ | **100% IN-BOUNDS** |
| **`OHRC_PAIR_04`** | $3164 \times 6322\text{ px}$ | `(+86683.0, +164952.0)` | $[+86683.0, +102503.0]$ | $[+133342.0, +164952.0]$ | **100% IN-BOUNDS** |

---

## 4. Geodetic Realization Conclusion

While the **mathematical projection equations** (Polar Stereographic, $R = 1,737,400\text{ m}$, $\lambda_0 = 0^\circ$, $\phi_0 = -90^\circ$, $k_0 = 1.0$) are identical between the reference GeoTIFF, LOLA DEM, and source metadata, **the specific geodetic realization of the reference mosaic is unrecorded**.

> **Methodological Rule:** Matching projection names do NOT imply identical geodetic realization. The reference mosaic could be registered to LOLA, LROC WAC, or an autonomous photogrammetric bundle adjustment with residual baseline shifts.
