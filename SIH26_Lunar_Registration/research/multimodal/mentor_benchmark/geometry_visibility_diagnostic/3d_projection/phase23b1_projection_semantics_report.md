# Phase 23B.1 -- Projection Semantics Report: GeoKey 3092

**Generated:** 2026-09-24T06:03:17Z  
**Script:** `run_phase23b1_geokey3092_sensitivity.py`  

## 1. GeoKey Identity

| Field | Value |
|-|-|
| GeoKey ID | 3092 |
| Name | ProjStraightVertPoleLongGeoKey |
| Delivered Value | 1.0 deg |
| Conventional Value | 0.0 deg |

## 2. Authoritative Definitions

### [R1] OGC GeoTIFF Standard 1.1 (OGC 19-008r4)
- **Clause:** Section 8.7.5 — Requirement Class: Projected CRS GeoKeys
- **URL:** <https://docs.ogc.org/is/19-008r4/19-008r4.html>
- **Definition:** ProjStraightVertPoleLongGeoKey (3092): Longitude of the straight vertical line from the pole used in Polar Stereographic and Stereographic projections. Corresponds to EPSG parameter 'Longitude of natural origin' in Polar Stereographic Variant A (EPSG:9810).

### [R2] EPSG Geodesy Parameter Dataset — Guidance Note 7 Part 2
- **Clause:** Section 1.3.6 — Polar Stereographic (Variant A), EPSG Method 9810
- **URL:** <https://epsg.org/guidance-notes.html>
- **Definition:** Longitude of natural origin (lam_0): The longitude of the point from which the values of both the geodetic coordinates on the ellipsoid and the grid coordinates on the projection are deemed to increment or decrement. For Polar Stereographic, this is the straight vertical pole longitude. Projection equations (spherical approximation):   rho = 2*R*tan(pi/4 + phi/2)  [south pole case]   E   = rho * sin(lam - lam_0)   N   = rho * cos(lam - lam_0) The parameter lam_0 is NOT additive to false easting/northing; it is a rotation of the coordinate axes around the pole.

### [R3] Snyder, J.P. (1987). Map Projections -- A Working Manual
- **Clause:** Chapter 21, Polar Stereographic, Equations 21-12 (south-pole sphere)
- **URL:** <https://pubs.usgs.gov/pp/1395/report.pdf>
- **Definition:** For south pole: rho = 2*R*tan(45 + phi/2); x = rho*sin(lam - lam_0); y = rho*cos(lam - lam_0). lam_0 is the central meridian (straight vertical pole long). When lam_0 = 0, the Y axis points toward lon = 0; when lam_0 = 1, the Y axis points toward lon = 1 deg.

## 3. Semantics Verdict

| Property | Verdict |
|-|-|
| Is a rotation of projected coordinate axes | `True` |
| Is a translation (constant offset) | `False` |
| Is a false-origin shift | `False` |
| Changes physical pixel geolocation | `True` |

> **Effect:** GeoKey 3092 = lam_0 rotates the projected coordinate system (E/N axes) around the south pole by lam_0 degrees. This changes the (E, N) coordinates assigned to every geographic point. Pixels with encoded coordinates (E0, N0) geolocate to DIFFERENT geographic points depending on whether lam_0 = 0 or 1.

> **Note:** Unlike a false easting/northing (which shifts all coordinates by a constant), lam_0 introduces a SPATIALLY VARYING displacement: it is a rotation, so the displacement is proportional to distance from the pole and is zero at the pole itself. The direction of the displacement is perpendicular to the radial (pole-to-point) direction, i.e. purely azimuthal.

## 4. Is 1.0 deg Unusual?

**Unusual:** `True`

For canonical south-polar products (LROC NAC, LOLA, TMC-2 documented examples), lam_0 = 0.0 deg is standard. A value of 1.0 deg is non-standard and unusual. The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation.

## 5. Does 1 deg Justify Treatment as Real Orientation?

The delivered GeoKey 3092 = 1.0 deg is formally a valid projection parameter per OGC 19-008r4. A conforming GeoTIFF reader should use lam_0 = 1.0 deg when projecting coordinates from this raster. However, whether the ISRO pipeline INTENDED this value, or whether downstream tools (including any reference-product generator) actually honoured it, remains UNVERIFIED.

## 6. Mathematical Implementation

South-polar stereographic (spherical, Snyder 1987 Eq. 21-12):

```
rho = 2 * R * tan(pi/4 + phi/2)      [phi = latitude in radians]
E   = rho * sin(lam - lam_0)          [lam = longitude in radians]
N   = rho * cos(lam - lam_0)          [lam_0 = GeoKey 3092 in radians]
```

Condition A (Control): `lam_0 = 0.0 deg` (prior assumption)
Condition B (Test):    `lam_0 = 1.0 deg` (delivered GeoKey 3092)

