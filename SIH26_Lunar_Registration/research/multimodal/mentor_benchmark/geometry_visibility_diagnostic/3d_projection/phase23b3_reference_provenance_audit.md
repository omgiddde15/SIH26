# Phase 23B.3 -- Reference Product Geodetic Provenance & Direct Content Fingerprint Audit

**Generated:** 2026-09-24T07:36:30Z  
**Script:** `run_phase23b3_reference_provenance_audit.py`  
**Governing Status:** RESEARCH-ONLY  
**Production Code:** FROZEN  

---

## 1. Scope

Determine whether the delivered 5 m Polar Stereographic OHRC mentor reference rasters can be 
directly linked to an authoritative upstream lunar reference product, map-generation product, 
or documented geodetic realization.

## 2. Governance

- Production code frozen; no modification to app/app.py, app/adaptive_adapter.py, app/registration_core.py, research/adaptive_matcher/adaptive_engine.py.
- No empirical transform fitted.
- No candidate promoted on compatibility alone.
- No image matching (LoFTR / SIFT / RANSAC) performed.
- Evidence hierarchy strictly observed.

## 3. Historical Evidence Carried Forward

- Phase 23B.1: 1 deg pole-longitude sensitivity test NOT SUPPORTED (historical residuals preserved).
- Phase 23B.2: GeoKey 3092 = ProjScaleAtNatOriginGeoKey = 1.0; GeoKey 3095 = ProjStraightVertPoleLongGeoKey = 0.0 deg. CRS interpretation CONFIRMED.
- Pair 02/03 overlap: 7,089,556 / 7,089,556 pixels identical (Mean=0.0000, RMS=0.0000).
- Phase 23A.5/23A.6 residuals: 1265-2181 m per pair (immutable).

## 4. Track 1 -- Local Delivery Provenance

| Item | Finding | Classification |
|------|---------|----------------|
| Filename convention | The filenames use the OHRC observation identifier with a `_reference_at_5m` suffix; this naming convention does not preserve an authoritative upstream reference-product identifier. | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 270 (ImageDescription) | ABSENT from all 4 reference GeoTIFFs | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 271 (Make) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 305 (Software) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 306 (DateTime) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 315 (Artist) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 33432 (Copyright) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| TIFF Tag 42112 (GDAL_METADATA) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| GeoAsciiParams | 'PolarStereographic Moon\|GCS_Moon\|D_Moon\|...' -- generic CRS label, no product ID | NOT_FOUND_IN_AUDITED_INPUTS |
| Sidecar files (.aux.xml, .prj, .ovr, .tfw) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |
| PDS4 XML sidecar | PRESENT -- contains OHRC source product info, not reference product info | VERIFIED for source; NOT_FOUND for reference |

**Conclusion:** The delivered reference GeoTIFFs contain zero embedded provenance information identifying the upstream reference map product.

## 5. Track 2 -- PDS4 / OHRC Label Lineage

| PDS4 Field | Content | Interpretation |
|-----------|---------|----------------|
| `<level0_dataset>` | OHRC source product ID (e.g. OHRXXD18CHO2359602...) | Source observation identity, NOT reference product |
| `<job_id>` | Same as level0_dataset | Source identity only |
| `<ReferenceUsed>` | `System` | Generic label -- does not name a specific external reference map product |
| `<SelenoTagging>` | Timestamps only | Processing step, no product reference |
| `<AutoLCP>` | StartTime only | Processing step, no GCP list, no external product ID |
| `<projection>` | Polar stereographic | Matches delivered rasters; generic |
| `<area>` | South Pole | Geographic description; generic |

**Classification: C -- reference is merely described generically.**
The PDS4 XML does not link the reference rasters to any named external product.

## 6. Candidate Registry (Phase 23B.3 Assessment)

| Candidate | Resolution | Frame | Local File | Content Test | Phase 23B.3 Classification |
|-----------|-----------|-------|-----------|-------------|--------------------------|
| CAND_B01: ISRO TMC-2 South Polar Ortho-Mosaic (5 m... | 5.0 m/px | IAU_MOON (selenocent... | False | NOT_POSSIBLE -- no local ... | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B02: NASA LROC WAC Global Mosaic (100 m resam... | 100.0 m/px | MOON_ME_DE421... | False | NOT_APPLICABLE -- resolut... | `MISMATCH` |
| CAND_B03: NASA LROC NAC South Polar Mosaic (resamp... | 0.5 m/px | MOON_ME_DE421... | False | NOT_POSSIBLE -- no local ... | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B04: NASA LOLA LDEM 5 m South Polar DEM... | 5.0 m/px | MOON_ME_DE421... | False | NOT_APPLICABLE -- modalit... | `MISMATCH` |
| CAND_B05: USGS Astropedia South Polar Optical Mosa... | 5.0 m/px | MOON_ME_DE421 (moder... | False | NOT_POSSIBLE -- no local ... | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B06: SIH 2026 Benchmark Delivery Container... | 5.0 m/px | UNKNOWN... | True | N/A -- container layer, n... | `PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED` |
| CAND_B07: ISRO CH-2 TMC-2 Single-Strip Ortho-Image... | 5.0 m/px | IAU_MOON (MOON_ME vi... | False | NOT_APPLICABLE -- width m... | `MISMATCH` |

*Note on CAND_B06:* This establishes only that the benchmark delivery container is the immediate local container of the raster; it does not identify the upstream reference product or geodetic realization. Do not classify the container as a directly identified reference product.

## 7. Track 3 -- Content Fingerprints

No authoritative candidate source raster is available locally for deterministic content comparison.
Pixel-level exact match testing (the only content identification method authorized) cannot be performed.
File SHA256 and window-level SHA256 fingerprints are recorded for future comparison when an authoritative source becomes available.

| Pair | File SHA256 (16 hex) | Full Payload SHA256 (16 hex) | Center 512x512 SHA256 (16 hex) |
|------|---------------------|----------------------------|---------------------------------|
| OHRC_PAIR_01 | `4bebce73338e09e9` | `338f57b94eae1af6` | `3ea6337d09ed6ae4` |
| OHRC_PAIR_02 | `9f69e68be8474cf2` | `7d539b79ae3f09f3` | `3d039fdfa669f51e` |
| OHRC_PAIR_03 | `30417e85f872aaca` | `9a710c7a514526af` | `a8c6b6f78fea7f3d` |
| OHRC_PAIR_04 | `0bc494da1e927fb5` | `fb8c33012480b0fc` | `b7e03ec2c0474b1f` |

**Content identification result: NOT_POSSIBLE** -- no authoritative local source file available.

## 8. Track 4 -- Geometric Grid Compatibility

All four delivered reference rasters share:
- Projection: Polar Stereographic, South Pole
- Central Meridian: 0.0 deg
- Latitude of Origin: -90.0 deg
- Scale Factor: 1.0
- False Easting/Northing: 0.0 m / 0.0 m
- Radius: 1,737,400.0 m (sphere)
- Pixel Size: 5.0 m x 5.0 m
- Raster Type: PixelIsArea
- Grid Phase: E0 mod 5 = 3.0 m, N0 mod 5 = 2.0 m (all four pairs)

The four delivered reference rasters are phase-aligned to the same 5 m projected coordinate lattice. This does NOT establish common master-file provenance or common upstream acquisition history.

This geometric profile is compatible with multiple lunar polar products (TMC-2 mosaic, LROC NAC mosaic, USGS south polar). Geometric compatibility alone is insufficient for product identification.

## 9. Track 5 -- Reference Content Identity (Pair 02/03)

- Verified overlap: **7,089,556 / 7,089,556 pixels identical**
- Mean difference: **0.0000**
- RMS difference: **0.0000**

The two delivered reference rasters are identical over the verified overlap, consistent with both references drawing from common pre-existing reference content; upstream acquisition and mosaic-generation history remains unverified.

This confirms the reference content is not per-pair unique imagery. It does NOT identify the upstream product.

## 10. Track 6 -- Geodetic Realization Comparison

| Item | Status |
|------|--------|
| Delivered CRS name | PolarStereographic Moon / GCS_Moon / D_Moon |
| Delivered datum label | D_Moon |
| Delivered radius | 1,737,400.0 m |
| Explicit geodetic frame tag | ABSENT -- not named in any delivered metadata |
| MOON_ME link | NOT_VERIFIED |
| MOON_ME_DE421 link | NOT_VERIFIED |
| IAU_MOON link | COMPATIBLE but not verified |

**D_Moon is compatible with IAU_MOON, MOON_ME, and MOON_ME_DE421.** Without an explicit label or authoritative content match, the specific geodetic realization cannot be determined.

## 11. Track 7 -- Absolute Coordinate Constraints

Phase 23A.5/23A.6 measured residuals (immutable):

| Pair | RMS Residual |
|------|-------------|
| OHRC_PAIR_01 | 2,158.6 m |
| OHRC_PAIR_02 | 1,265.2 m |
| OHRC_PAIR_03 | 1,748.5 m |
| OHRC_PAIR_04 | 2,181.1 m |

Km-scale residuals (1,265–2,181 m) confirm a substantial source/reference geodetic-coordinate discrepancy under the audited model. No empirical transform was fitted. However, they do not identify that source without an authoritative comparand and an empirical-transform-free coordinate comparison, which is not possible with locally available inputs.

## 12. Track 8 -- Authoritative Documentation

Sources audited: 6. Direct authoritative links found: 0.

No authoritative documentation directly names the upstream map product used to generate the delivered OHRC reference rasters. All provenance TIFF metadata tags are absent. The PDS4 XML labels identify only the OHRC source observation, not the reference map product. No archive ID, product catalog number, or map-generation software is recorded in any delivered file.

## 13. Evidence Hierarchy

| Level | Evidence Type | Found? |
|-------|--------------|--------|
| 1 (Strongest) | Direct authoritative label naming the upstream product | NO |
| 2 | Exact pixel/byte content match against an authoritative local source file | NO (no source file available) |
| 3 | Producer documentation explicitly linking delivered artifact to upstream product | NO |
| 4 | Geodetic metadata compatibility | PARTIAL (compatible with multiple frames) |
| 5 | Projection compatibility | YES (but non-exclusive) |
| 6 | Resolution compatibility | YES (but non-exclusive) |
| 7 (Weakest) | Visual similarity | NOT ASSESSED (not an authorized identification method) |

No Level 1, 2, or 3 evidence was found. Levels 4-6 do not constitute identification.

## 14. Final Classification

> # **`D -- UNRESOLVED`**

No direct authoritative provenance link establishes the identity of the upstream reference map product or its geodetic realization. Evidence summary: (1) All TIFF provenance tags absent. (2) PDS4 XML records only OHRC source product ID; reference map is described generically as 'System'. (3) No local authoritative source file is available for content comparison. (4) Projection, resolution, and radius compatibility are insufficient for identification. (5) The identical Pair 02/03 overlap confirms a static common reference content source, but does not identify it. (6) The benchmark delivery container is confirmed but is the packaging layer, not the upstream cartographic product.

## 15. What Is Established

1. The delivery packaging layer (SIH 2026 benchmark container) is directly identified as a packaging artifact (PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED). This establishes only that the benchmark delivery container is the immediate local container of the raster; it does not identify the upstream reference product or geodetic realization.
2. The reference GeoTIFFs contain zero embedded provenance identifying the upstream product.
3. The PDS4 XML labels identify the OHRC source product but use a generic 'System' reference tag.
4. The reference content uses standard south-polar projection with canonical parameters.
5. The Pair 02/03 reference content is identical over verified overlap (consistent with static common source).
6. Multiple candidate products are geometrically and metrically compatible.

## 16. What Remains Unresolved

1. Identity of the upstream map/mosaic product used to generate the reference rasters.
2. Geodetic realization (IAU_MOON / MOON_ME / MOON_ME_DE421 / other).
3. Link between delivered content and DE421 lunar reference frame.
4. Whether any geographic offset between source and reference is attributable to frame differences.

## 17. What This Does NOT Prove

- This audit does NOT prove the reference is TMC-2 ortho-mosaic.
- This audit does NOT prove the reference is LROC NAC mosaic.
- This audit does NOT prove the reference is MOON_ME_DE421.
- Grid phase alignment does NOT prove common master-file provenance.
- Pixel identity over Pair 02/03 overlap does NOT prove static-mosaic acquisition history.

## 18. Phase Gate

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

Phase 23B remains blocked. Phase 23B.3 execution does NOT automatically unblock Phase 23B.

## 19. Reproducibility

All outputs generated by `run_phase23b3_reference_provenance_audit.py` are deterministic from the delivered input files.
Checksums recorded in `checksums.sha256`.

## 20. Checksums

See `checksums.sha256` in this directory.

