# Phase 23B.2 -- Standard CRS / GeoTIFF Reader Semantics Report

**Generated:** 2026-09-24T07:05:04Z  
**Script:** `run_phase23b2_crs_reader_semantics.py`  
**Governing Status:** RESEARCH-ONLY  
**Production Code:** FROZEN  

---

## 1. Executive Summary & Root-Cause Resolution

> [!IMPORTANT]
> **CRITICAL ARCHITECTURAL FINDING:**
> A comprehensive audit of the authoritative OGC GeoTIFF 1.1 Specification (OGC 19-008r4) 
> and standard geospatial reader software (GDAL 3.12.4, Rasterio 1.5.1, PROJ 9.8.1, pyproj 3.8.0) 
> resolves the identity and values of the GeoTIFF projection keys in all delivered reference rasters:
> 
> 1. **GeoKey 3092 IS `ProjScaleAtNatOriginGeoKey`** (Scale at Natural Origin). Its value is **`1.0`** 
>    (the standard unit scale factor $k_0 = 1.0$ at the south pole).
> 2. **GeoKey 3095 IS `ProjStraightVertPoleLongGeoKey`** (Straight Vertical Pole Longitude). Its value is **`0.0`** 
>    (the canonical central meridian $\lambda_0 = 0.0^\circ$).
> 3. **The delivered reference rasters contain NO non-standard 1.0 deg pole longitude.**
> 4. All standard software stacks read $\lambda_0 = 0.0^\circ$ and scale factor $= 1.0$.
> 5. Our audited Phase 23A mathematical implementation ($\lambda_0 = 0.0^\circ$) matches standard GDAL/PROJ 
>    readers to **within $0.000000\text{ m}$ ($< 10^{-10}\text{ m}$)**.

---

## 2. Authoritative GeoKey Specification Matrix

| GeoKey ID | Specification Name | Delivered Value | Canonical Meaning | Role in Polar Stereographic |
|---|---|---|---|---|
| **3092** | `ProjScaleAtNatOriginGeoKey` | **`1.0`** | Scale at Natural Origin (k_0) | Unit scale factor at pole (tangent plane) |
| **3095** | `ProjStraightVertPoleLongGeoKey` | **`0.0`** | Central Meridian (lambda_0) | Standard vertical orientation along 0 deg meridian |
| **3081** | `ProjNatOriginLatGeoKey` | **`-90.0`** | Latitude of Origin (phi_0) | Standard south pole (-90.0 deg) |
| **3082** | `ProjFalseEastingGeoKey` | **`0.0`** | False Easting | 0.0 m |
| **3083** | `ProjFalseNorthingGeoKey` | **`0.0`** | False Northing | 0.0 m |
| **2057** | `GeogSemiMajorAxisGeoKey` | **`1737400.0`** | Semi-major Axis | 1,737,400.0 m |
| **2058** | `GeogSemiMinorAxisGeoKey` | **`1737400.0`** | Semi-minor Axis | 1,737,400.0 m |
| **2061** | `GeogInvFlatteningGeoKey` | **`0.0`** | Inverse Flattening | 0.0 (Sphere) |

---

## 3. Explanation of Phase 23B Misidentification

In Phase 23B, an early manual decoding script mapped Key ID 3092 to 'ProjStraightVertPoleLongGeoKey' instead of its true specification definition 'ProjScaleAtNatOriginGeoKey'. In reality, Key 3092 is the unit scale factor (1.0), and Key 3095 is the straight vertical pole longitude (0.0 deg). The delivered reference GeoTIFFs contain NO non-standard 1.0 deg pole longitude.

This completely explains why Phase 23B.1's sensitivity test found that applying $1.0^\circ$ as an azimuthal rotation 
to the source projection increased residuals across all four pairs (+92.8% mean pairwise increase): the delivered GeoTIFF 
CRS does not encode a 1.0 deg straight-vertical-pole-longitude rotation; its interpreted central meridian is 0.0 deg. 
The delivered reference raster is interpreted by standard readers with lambda_0 = 0.0 deg. Source-side projection parameters 
are treated separately unless independently verified.

---

## 4. Software Stack Comparison

Independent verification across all four delivered reference rasters confirms:
- **GDAL (3.12.4):** parses `PARAMETER["central_meridian", 0]`, `PARAMETER["latitude_of_origin", -90]`, `PARAMETER["false_easting", 0]`, `PARAMETER["false_northing", 0]`.
- **Rasterio (1.5.1):** parses `crs.to_dict() = {'proj': 'stere', 'lat_0': -90, 'lat_ts': -90, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'R': 1737400, 'units': 'm', 'no_defs': True}`.
- **PROJ (9.8.1) / pyproj (3.8.0):** parses `Longitude of natural origin = 0.0`, `Scale factor at natural origin = 1.0`.
- **Raw GeoTIFF Parser:** confirms GeoDoubleParams index 1 is `0.0` (Key 3095) and index 2 is `1.0` (Key 3092).

**Conclusion:** 100% agreement across all software stacks and raw metadata.

---

## 5. Final Classification

> # **`A -- READER-SEMANTICS-CONFIRMED`**

- Standard readers consistently consume the GeoTIFF keys according to the official OGC specification.
- The reference rasters use standard $\lambda_0 = 0.0^\circ$ and $k_0 = 1.0$.
- Our audited mathematical implementation matches standard GDAL, Rasterio, and PROJ readers to $0.000000\text{ m}$.

---

## 6. Retained Geodetic Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

The resolution of the GeoKey 3092/3095 identity confirms that the planar map projection parameters are standard and 
free of rotation artifacts. However, it does not identify the upstream lunar mosaic product or its geodetic tie to DE421.

