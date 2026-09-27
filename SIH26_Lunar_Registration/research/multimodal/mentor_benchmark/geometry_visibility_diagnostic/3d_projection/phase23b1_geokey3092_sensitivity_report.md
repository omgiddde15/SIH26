# Phase 23B.1 -- GeoKey 3092 Geodetic Sensitivity Test Report

**Generated:** 2026-09-24T06:03:17Z  
**Script:** `run_phase23b1_geokey3092_sensitivity.py`  
**Governing Status:** RESEARCH-ONLY  
**Production Code:** FROZEN  

---

## 1. Scope and Governance

Test whether the delivered reference raster GeoKey 3092 = 1.0 deg materially explains the km-scale source/reference geodetic residuals measured in Phase 23A.5 and 23A.6.  No production code was modified.  No empirical transform was fitted.  No candidate reference product was promoted.

**PRODUCTION FREEZE STATUS:** No modifications to:
- `app/app.py`
- `app/adaptive_adapter.py`
- `app/registration_core.py`
- `research/adaptive_matcher/adaptive_engine.py`

---

## 2. GeoKey 3092 Semantics Summary

*(Full documentation in `phase23b1_projection_semantics_report.md`)*

| Property | Value |
|-|-|
| GeoKey 3092 definition | Longitude of natural origin = straight-vertical-pole longitude |
| Authority | OGC GeoTIFF 1.1 (OGC 19-008r4), EPSG 9810, Snyder 1987 |
| Effect | Rotation of projected (E,N) axes around south pole |
| Changes physical pixel geolocation | YES -- spatially varying azimuthal rotation |
| Semantics verdict | FORMALLY DEFINED AND UNAMBIGUOUS in authoritative specs |
| Delivered value | 1.0 deg (non-standard; canonical is 0.0 deg) |

---

## 3. Mathematical Formulation

**Projection (Snyder 1987, Eq. 21-12, south-pole spherical):**

```
rho = 2 * R * tan(pi/4 + phi/2)
E   = rho * sin(lam - lam_0)   [Condition A: lam_0 = 0.0 deg]
N   = rho * cos(lam - lam_0)   [Condition B: lam_0 = 1.0 deg]
R = 1,737,400.0 m (verified from GeoDoubleParams tag 34736)
```

**Reference E/N coordinates:** Read from reference raster tiepoints + geotransform.  
**NOT changed between conditions A and B.**

**Independent variable:** Only `lam_0` changes.  No fit, no tuning, no translation.

---

## 4. Cross-Pair Results Summary

| Pair | RMS-A (m) | RMS-B (m) | RMS Reduction (m) | % RMS Reduction |
|-|-|-|-|-|
| OHRC_PAIR_01 | 2158.6 | 2414.9 | -256.3 | -11.9% |
| OHRC_PAIR_02 | 1265.2 | 3272.6 | -2007.4 | -158.7% |
| OHRC_PAIR_03 | 1748.5 | 3599.1 | -1850.6 | -105.8% |
| OHRC_PAIR_04 | 2181.1 | 4248.8 | -2067.7 | -94.8% |

---

## 5. Per-Pair Detailed Results

### OHRC_PAIR_01

| Corner | A dE (m) | A dN (m) | A Mag (m) | A Az (deg) | B dE (m) | B dN (m) | B Mag (m) | B Az (deg) | Delta Mag (m) |
|-|-|-|-|-|-|-|-|-|-|
| UL | 1701.2 | -1333.6 | 2161.6 | 128.1 | 1841.8 | -1559.0 | 2413.0 | 130.2 | +251.4 |
| UR | 1732.9 | -1272.0 | 2149.6 | 126.3 | 1922.2 | -1522.6 | 2452.1 | 128.4 | +302.5 |
| LL | 1707.7 | -1335.3 | 2167.8 | 128.0 | 2059.9 | -1173.4 | 2370.7 | 119.7 | +202.9 |
| LR | 1739.1 | -1273.6 | 2155.5 | 126.2 | 2140.1 | -1136.8 | 2423.3 | 118.0 | +267.7 |

- **RMS-A:** 2158.6 m   **RMS-B:** 2414.9 m   **Reduction:** -256.3 m (-11.9%)  
- **Mean delta azimuth:** 106.9 deg   **Spread:** 41.6 deg   **Spatially rigid:** `False`  
- **Substantial reduction:** `False`  

### OHRC_PAIR_02

| Corner | A dE (m) | A dN (m) | A Mag (m) | A Az (deg) | B dE (m) | B dN (m) | B Mag (m) | B Az (deg) | Delta Mag (m) |
|-|-|-|-|-|-|-|-|-|-|
| UL | 310.1 | 1227.9 | 1266.4 | 14.2 | -2288.9 | 2502.7 | 3391.6 | 317.6 | +2125.1 |
| UR | 264.9 | 1234.2 | 1262.3 | 12.1 | -2325.9 | 2565.5 | 3462.9 | 317.8 | +2200.6 |
| LL | 302.2 | 1231.2 | 1267.8 | 13.8 | -1862.0 | 2445.3 | 3073.5 | 322.7 | +1805.7 |
| LR | 257.0 | 1237.6 | 1264.0 | 11.7 | -1899.0 | 2508.2 | 3146.0 | 322.9 | +1882.0 |

- **RMS-A:** 1265.2 m   **RMS-B:** 3272.6 m   **Reduction:** -2007.4 m (-158.7%)  
- **Mean delta azimuth:** 298.3 deg   **Spread:** 2.2 deg   **Spatially rigid:** `True`  
- **Substantial reduction:** `False`  

### OHRC_PAIR_03

| Corner | A dE (m) | A dN (m) | A Mag (m) | A Az (deg) | B dE (m) | B dN (m) | B Mag (m) | B Az (deg) | Delta Mag (m) |
|-|-|-|-|-|-|-|-|-|-|
| UL | 346.9 | 2081.0 | 2109.7 | 9.5 | -2319.9 | 3241.8 | 3986.4 | 324.4 | +1876.7 |
| UR | 307.6 | 2085.1 | 2107.7 | 8.4 | -2353.3 | 3298.9 | 4052.2 | 324.5 | +1944.5 |
| LL | 241.9 | 1270.0 | 1292.9 | 10.8 | -1970.1 | 2380.4 | 3090.0 | 320.4 | +1797.1 |
| LR | 202.7 | 1274.2 | 1290.2 | 9.0 | -2003.5 | 2437.5 | 3155.2 | 320.6 | +1865.0 |

- **RMS-A:** 1748.5 m   **RMS-B:** 3599.1 m   **Reduction:** -1850.6 m (-105.8%)  
- **Mean delta azimuth:** 295.6 deg   **Spread:** 2.2 deg   **Spatially rigid:** `True`  
- **Substantial reduction:** `False`  

### OHRC_PAIR_04

| Corner | A dE (m) | A dN (m) | A Mag (m) | A Az (deg) | B dE (m) | B dN (m) | B Mag (m) | B Az (deg) | Delta Mag (m) |
|-|-|-|-|-|-|-|-|-|-|
| UL | 640.6 | 2087.4 | 2183.5 | 17.1 | -2237.0 | 3759.7 | 4374.9 | 329.2 | +2191.4 |
| UR | 620.7 | 2091.6 | 2181.8 | 16.5 | -2241.2 | 3814.2 | 4424.0 | 329.6 | +2242.2 |
| LL | 634.0 | 2086.2 | 2180.4 | 16.9 | -1811.9 | 3641.2 | 4067.1 | 333.6 | +1886.7 |
| LR | 614.1 | 2090.4 | 2178.7 | 16.4 | -1816.1 | 3695.7 | 4117.8 | 333.8 | +1939.1 |

- **RMS-A:** 2181.1 m   **RMS-B:** 4248.8 m   **Reduction:** -2067.7 m (-94.8%)  
- **Mean delta azimuth:** 301.8 deg   **Spread:** 1.7 deg   **Spatially rigid:** `True`  
- **Substantial reduction:** `False`  

---

## 6. Inverse / Round-Trip Validation

| Test Point | lam_0 | Round-Trip Error (m) |
|-|-|-|
| South pole, lon=0 | 0.0 deg | 0.00e+00 m |
| South pole, lon=0 | 1.0 deg | 0.00e+00 m |
| South pole, lon=1 | 0.0 deg | 0.00e+00 m |
| South pole, lon=1 | 1.0 deg | 0.00e+00 m |
| South pole, lon=90 | 0.0 deg | 0.00e+00 m |
| South pole, lon=90 | 1.0 deg | 0.00e+00 m |
| Mid polar, lon=30 (typical PAIR 02-04) | 0.0 deg | 0.00e+00 m |
| Mid polar, lon=30 (typical PAIR 02-04) | 1.0 deg | 0.00e+00 m |
| Mid polar, lon=25 | 0.0 deg | 0.00e+00 m |
| Mid polar, lon=25 | 1.0 deg | 0.00e+00 m |
| Mid polar, lon=31 (PAIR 04 region) | 0.0 deg | 0.00e+00 m |
| Mid polar, lon=31 (PAIR 04 region) | 1.0 deg | 0.00e+00 m |

> All forward/inverse round-trip errors are < 1e-6 m.  
> The projection implementation is numerically consistent under both lam_0 values.

---

## 7. Cross-Pair Consistency

**Classification:** `C -- NOT SUPPORTED`  
**Mean % RMS reduction:** `-92.8%`  
**Mean reduction:** `-1549 m`  
**All pairs substantial:** `False`  
**Effect spatially rigid (azimuthal):** `False`  
**Residual fully closed:** `False`  

Across the four pairs, RMS increased by 1,545.5 m on average; the mean of the four pairwise percentage increases was 92.8%. (Exact arithmetic: mean control RMS = 1838.35 m, mean test RMS = 3383.85 m, absolute mean increase = 1545.50 m, percentage increase of the mean RMS = 84.06%.) The hypothesis that the observed residuals are explained by applying the 1.0 deg straight-vertical-pole longitude to the source projection is not supported under the tested projection interpretation. The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation.

---

## 8. What This Experiment Establishes

Across the four pairs, RMS increased by 1,545.5 m on average; the mean of the four pairwise percentage increases was 92.8%. (Exact arithmetic: mean control RMS = 1838.35 m, mean test RMS = 3383.85 m, absolute mean increase = 1545.50 m, percentage increase of the mean RMS = 84.06%.) The hypothesis that the observed residuals are explained by applying the 1.0 deg straight-vertical-pole longitude to the source projection is not supported under the tested projection interpretation. The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation.

---

## 9. What This Experiment Does NOT Establish

- The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation.
- This experiment does NOT prove that the reference raster was encoded with lam_0 = 1.0 deg.
- This experiment does NOT identify the upstream reference product.
- This experiment does NOT resolve the geodetic realization of the reference raster.
- A partial residual change does NOT constitute causal proof.
- The remaining residual may have a different or compound origin.

---

## 10. Remaining Uncertainties

| Uncertainty | Status |
|-|-|
| Whether ISRO pipeline INTENDED lam_0 = 1.0 deg | `UNKNOWN` |
| Whether the reference raster was generated with lam_0 = 1.0 deg | `UNKNOWN` |
| Whether downstream readers interpreted GeoKey 3092 correctly | `UNKNOWN` |
| Whether the remaining residual after B has a single root cause | `UNKNOWN` |
| Reference geodetic realization (frame name) | `UNKNOWN` |
| Upstream reference product identity | `UNRESOLVED` |

---

## 11. Final Classification

> # **`C -- NOT SUPPORTED`**

---

## 12. Phase Gate

> [!IMPORTANT]
> ```
> REFERENCE_PRODUCT_UNRESOLVED
> REFERENCE_GEODETIC_REALIZATION = UNKNOWN
> REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
> PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
> ```
>
> Phase 23B.1 is a controlled sensitivity test. Its completion does NOT unblock
> Phase 23B or production registration. The geodetic realization remains unresolved.

---

## 13. Reproducibility

- **Script:** `run_phase23b1_geokey3092_sensitivity.py`
- **Python:** standard library only (math, json, csv, hashlib, datetime)
- **No GDAL, no SPICE, no image matching, no fitted parameters**
- **Input data:** Phase 23A.5 verified corner coordinates (immutable)
- **Calculation:** deterministic (pure Python math, no random elements)

> # **`PHASE 23B.1 EXECUTED -- SENSITIVITY TEST COMPLETE`**

