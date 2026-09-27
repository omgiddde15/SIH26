# Phase 23A.7 — Reference Raster Cartographic & Geodetic Realization Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit examines whether the mentor-supplied reference rasters (`ref_pair_01.tif` to `ref_pair_04.tif`) possess an authoritative geodetic frame definition that connects them to either `MOON_ME_DE421` or `IAU_MOON`.

> ### **Most Important Audit Result:**
> **`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`**  
> The GeoTIFF cartographic parameters (Polar Stereographic, $R = 1,737,400\text{ m}$, $k_0 = 1.0$) are verified, but the specific lunar geodetic realization, sensor source, and bundle adjustment solution are unrecorded in metadata.

---

## 2. Reference GeoTIFF Cartographic Property Matrix

| Cartographic Field | Tag / Key | Declared Value | Classification | Meaning |
| :--- | :---: | :---: | :---: | :--- |
| **Projection Type** | GeoKey 1024 / 3075 | `CT_PolarStereographic` | **`VERIFIED`** | Polar Stereographic projected coordinate system |
| **Reference Radius ($R$)** | GeoKey 2057 / 2058 | $1,737,400.0\text{ m}$ | **`VERIFIED`** | Spherical Moon reference surface |
| **Central Meridian ($\lambda_0$)** | GeoKey 3095 | $0.0^\circ$ | **`VERIFIED`** | Straight vertical pole longitude |
| **Latitude of Origin ($\phi_0$)** | GeoKey 3081 | $-90.0^\circ$ | **`VERIFIED`** | South pole standard projection origin |
| **Scale Factor ($k_0$)** | GeoKey 3092 | $1.000000$ | **`VERIFIED`** | Nominal scale preserved at the pole |
| **False Easting / Northing** | GeoKey 3082 / 3083 | $0.0\text{ m}, 0.0\text{ m}$ | **`VERIFIED`** | Coordinate system origin centered at pole |
| **Pixel Scale ($s_x, s_y$)** | Tag 33550 | $5.000\text{ m/px}, 5.000\text{ m/px}$ | **`VERIFIED`** | Delivered raster resolution |
| **Raster Area Convention** | GeoKey 1025 | `RasterPixelIsArea` | **`VERIFIED`** | Integer pixel bounds outer edge |
| **Raster Orientation** | Tag 33922 | North-Up ($+X$ East, $+Y$ North) | **`VERIFIED`** | Standard cartographic canvas |
| **Geodetic Realization** | Missing | Absent | **`UNKNOWN`** | Realization frame unrecorded |

---

## 3. LOLA / Reference / Physical Linkage Consistency Matrix

| System Linkage | Source System | Target System | Linkage Status | Connecting Evidence / Mechanism |
| :--- | :--- | :--- | :---: | :--- |
| **Link 1** | OHRC Physical Instrument | `IAU_MOON` | **`VERIFIED`** | ISRO SPICE CK, FK (`ch2_v01.tf`), SCLK, and `pck00010.tpc` |
| **Link 2** | `IAU_MOON` | `MOON_ME_DE421` | **`VERIFIED`** | NAIF `moon_080317.tf`, `moon_pa_de421_1900-2050.bpc`, `de421.bsp` |
| **Link 3** | LOLA DEM Surface | `MOON_ME_DE421` | **`VERIFIED`** | LOLA PDS labels declare Mean Earth / Polar Axis DE421 trajectory |
| **Link 4** | LOLA DEM Surface | `IAU_MOON` | **`VERIFIED`** | Evaluated via Link 2 rotation ($10.39" - 11.03"$) |
| **Link 5** | Mentor Reference GeoTIFF | `MOON_ME_DE421` | **`UNKNOWN`** | Realization absent from GeoTIFF tags |
| **Link 6** | Mentor Reference GeoTIFF | `IAU_MOON` | **`UNKNOWN`** | Realization absent from GeoTIFF tags |

> ### **Overall Linkage Conclusion:**
> # **`GEODETIC_LINK_NOT_VERIFIED`**  
> While physical modeling to `IAU_MOON` and `MOON_ME_DE421` is 100% verified, the geodetic realization of the reference mosaic basemap is unrecorded in mentor metadata. It cannot be assumed to be on the DE421 or IAU frame without independent empirical verification.
