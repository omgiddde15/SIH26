# 05 — Physical / Geodetic Investigation

## 5.1 Title Slide for This Section

> **Why Physical Geometry Matters:**
> *Delivered image pixels are not arbitrary bitmaps — they encode a camera-ray-to-planetary-surface intersection. If the reference frame is uncertain, the matcher cannot alone solve registration.*

## 5.2 Full Projection Chain (Audited & Verified)

```
┌───────────────────────────────────────────────────────────────────────┐
│  Delivered Source Pixel  (u_src, v_src)                                │
│        ├── native detector geometry → 3D camera vector                │
│        ├── spacecraft position (SPICE ephemeris)                      │
│        ├── spacecraft attitude (PDS4 quaternions / star tracker)      │
│        └── back-projected RAY through the pixel                       │
└─────────────────────────────┬─────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│  Lunar DEM intersection (ray-vs-DEM)                                  │
│        ├── produces (X, Y, Z) body-fixed point                        │
│        └── converted to (lat, lon, height)                            │
└─────────────────────────────┬─────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│  Reference Map Projection (Polar Stereographic South)                 │
│        ├── CRS interpretation: EPSG-like Polar Stereo                 │
│        ├── λ₀ = 0° longitude of origin                                │
│        ├── k₀ = 1.0 scale factor at pole                              │
│        ├── R = 1,737,400 m (lunar radius, audited)                    │
│        └── produces (Easting, Northing) map metres                    │
└─────────────────────────────┬─────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│  Reference Pixel Footprint (u_ref, v_ref)  →  NOMINAL CENTRE          │
│        ├── this is the starting point for the Phase 24A lattice       │
│        └── NOT shifted by Phase 23A.6 fitted translations             │
└───────────────────────────────────────────────────────────────────────┘
```

- Phase 23A yielded **91.7%** ray-to-DEM intersection yield across the 4 OHRC pairs.
- The audited projection is **reused verbatim** for the Phase 24A coarse lattice; no new projection math was invented.

## 5.3 CRS Semantics (Phase 23B.2 — Verified)

**Audited with GDAL, Rasterio, and PROJ — all three agree.**

| GeoTIFF Key / Parameter | Audited Interpretation |
|:---|:---|
| Projection | `Polar Stereographic` (variant: South Pole) |
| `λ₀` (longitude of origin) | **0.0°** |
| `k₀` (scale factor at natural origin, GeoKey 3092) | **1.0** |
| Sphere radius | **1,737,400 m** |
| False easting / false northing | 0, 0 |
| Units | Metre |

**Important correction (Phase 23B.2 finding):**
> GeoKey 3092 was initially hypothesized to mean "1° longitude-related offset" by an early draft. Audited CRS reader semantics show it is the **scale factor k₀**. The earlier 1° hypothetical offset **did not** explain the observed residuals.

## 5.4 What Remains Unresolved (HONEST)

The honest result of the 8-track provenance audit (Phase 23B.3) is:

### Final Status Block — PRESERVED UNCHANGED

```
REFERENCE_PRODUCT_UNRESOLVED
  → No direct provenance link to an authoritative upstream map product
    could be recovered from:
      • TIFF tags (all provenance tags absent from all 4 reference GeoTIFFs)
      • PDS4 labels (use generic <ReferenceUsed>System</ReferenceUsed>)
      • local candidate raster fingerprint comparison
      • external open-data product registries

REFERENCE_GEODETIC_REALIZATION = UNKNOWN
  → Because the upstream product is unidentified, we cannot pin
    the lunar body-fixed frame (mean-vs-DE421, orientation history, etc.)

REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
  → An explicit link to the lunar mean-ellipsoid / DE421 ephemeris
    orientation would require the upstream product's provenance.

PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

**Allowed wording for PPT:**
- "The delivered reference GeoTIFF uses a standard Polar Stereographic projection."
- "GDAL, Rasterio, and PROJ agree with our audited CRS interpretation."
- "The specific upstream map product has not yet been identified."
- "Geodetic body-fixed realization remains under review."

**Forbidden wording (DO NOT USE):**
- ❌ "reference product identified"
- ❌ "geodetically correct"
- ❌ "we solved the geodetic offset"
- ❌ any reference to an explicit upstream product name unless explicitly cross-validated

## 5.5 Why This Matters for the Matcher

If the reference GeoTIFF's **absolute** placement is uncertain by even ±1–2 km, a matcher that appears to "fail" may actually be correct relative to its actual content. This is the core motivation for Phase 24A:

> Instead of running an expensive 676-candidate brute force LoFTR search (original Phase 24 plan), we designed a **cheap deterministic coarse prefilter** to test 196 predefined image-space hypotheses and only promote 16 of them to expensive LoFTR verification (see `07_phase24a_summary.md`).
