# Phase 23B — Reference Geodetic Realization / Geodetic Link Review

**Generated:** 2026-09-24T05:37:49Z  
**Script:** `run_phase23b_geodetic_link_review.py`  
**Governing Status:** RESEARCH-ONLY  
**Production Code:** FROZEN — `app/app.py`, `app/adaptive_adapter.py`, `app/registration_core.py`, `research/adaptive_matcher/adaptive_engine.py`  

---

## 1. Scope and Governance

**Objective:** Determine whether the delivered 5 m Polar Stereographic reference rasters can be geodetically linked to an authoritative lunar reference frame/product using independently supported metadata, raster geometry, authoritative kernels, coordinate-frame definitions, and documented product provenance.

**Constraints:**
- Do NOT modify production code.
- Do NOT perform image matching as evidence of geodetic truth.
- Do NOT fit an empirical transform to reduce residuals.
- Do NOT select or promote a winning reference product.
- All conclusions explicitly classified as VERIFIED, DERIVED, UNKNOWN, or UNRESOLVED.
- Preserve Phase 23A.9 conclusions: `REFERENCE_PRODUCT_UNRESOLVED`, `REFERENCE_GEODETIC_REALIZATION = UNKNOWN`, `REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED`.

---

## 2. Inputs Audited

| Input | Status |
|-------|--------|
| 4 × `*_reference_at_5m.tif` GeoTIFF files | AUDITED |
| 4 × PDS4 `.xml` product labels | AUDITED |
| Phase 23A.7 SPICE frame reconciliation results | IMPORTED (VERIFIED) |
| Phase 23A.9 candidate product registry | IMPORTED (VERIFIED) |
| GeoKeyDirectoryTag (34735) decoded | AUDITED |
| GeoDoubleParams (34736) decoded | AUDITED |
| GeoAsciiParams (34737) decoded | AUDITED |

---

## 3. Track 1 — Reference-Raster Metadata Audit

### 3.1 Verified GeoTIFF Parameters (identical for all 4 pairs)

| Parameter | Value | Status |
|-----------|-------|--------|
| ModelPixelScaleTag (33550) | `(5.0, 5.0, 0.0)` m | **VERIFIED** |
| Pixel interpretation (GeoKey 1025) | `1 = RasterPixelIsArea` | **VERIFIED** |
| Model type (GeoKey 1024) | `1 = Projected` | **VERIFIED** |
| Projection transform (GeoKey 3075) | `15 = Polar Stereographic` | **VERIFIED** |
| Natural origin latitude (GeoKey 3081) | `-90.0 deg` | **VERIFIED** |
| False easting (GeoKey 3082) | `0.0 m` | **VERIFIED** |
| False northing (GeoKey 3083) | `0.0 m` | **VERIFIED** |
| Linear units (GeoKey 3076) | `9001 = metres` | **VERIFIED** |
| Semi-major axis (GeoKey 2057) | `1,737,400.0 m` | **VERIFIED** |
| Semi-minor axis (GeoKey 2058) | `1,737,400.0 m` | **VERIFIED** |
| Sphere flattening (Key 2061) | `0.0` (perfect sphere) | **VERIFIED** |
| Datum (GeoKey 2050) | `32767 = user-defined` | **VERIFIED** |
| Geographic CRS (GeoKey 2048) | `32767 = user-defined` | **VERIFIED** |
| Projected CRS (GeoKey 3072) | `32767 = user-defined` | **VERIFIED** |
| GeoAsciiParams | `GCS_Moon / D_Moon / Moon Ellipsoid` | **VERIFIED** |
| **ProjStraightVertPoleLong (GeoKey 3092)** | **`1.0 deg`** | **ANOMALOUS** |

> [!IMPORTANT]
> `GeoKey 3092 = 1.0 deg` is **non-standard**. The conventional value for a canonical
> south-pole stereographic map is `0.0 deg`. This was not previously flagged in Phase 23A.
> See Track 4 for displacement analysis.

### 3.2 Per-Pair Tiepoints and Dimensions

| Pair | W × H (px) | E₀ (m) | N₀ (m) | E₀ mod 5 | N₀ mod 5 |
|------|-----------|--------|--------|----------|----------|
| OHRC_PAIR_01 | 5916 × 4232 | -19187.0 | -3603.0 | 3.0 | 2.0 |
| OHRC_PAIR_02 | 2593 × 6279 | 67338.0 | 150047.0 | 3.0 | 2.0 |
| OHRC_PAIR_03 | 2416 × 6316 | 61478.0 | 153132.0 | 3.0 | 2.0 |
| OHRC_PAIR_04 | 3164 × 6322 | 86683.0 | 164952.0 | 3.0 | 2.0 |

### 3.3 Absent Provenance Tags

All provenance GeoTIFF tags are **ABSENT** in all 4 reference rasters:

| Tag | ID | Status |
|-----|----|--------|
| TIFFTAG_SOFTWARE | 305 | **ABSENT** |
| TIFFTAG_DATETIME | 306 | **ABSENT** |
| TIFFTAG_IMAGEDESCRIPTION | 270 | **ABSENT** |
| TIFFTAG_ARTIST | 315 | **ABSENT** |
| GDAL_METADATA | 42112 | **ABSENT** |
| ModelTransformation | 34264 | **ABSENT** |

**Conclusion:** No software, date, mission, or product identifier is embedded in any delivered reference raster. The geodetic realization cannot be determined from GeoTIFF tag provenance alone.

---

## 4. Track 2 — Authoritative Candidate-Source Audit

| ID | Product | Classification | Rationale Summary |
|----|---------|---------------|-------------------|
| CAND_B01 | ISRO TMC-2 Polar Mosaic (5 m, South Pole) | **COMPATIBLE_BUT_UNVERIFIED** | Scale (5 m), projection, and radius are identical to the delivered rasters. |
| CAND_B02 | NASA LROC WAC Global Mosaic / Polar Mosaic (100 m, resampled to 5 m) | **MISMATCH** | Native resolution is 100 m/px — 20× coarser than the delivered 5 m rasters. |
| CAND_B03 | NASA LROC NAC Polar Mosaic (0.5–2 m native) | **COMPATIBLE_BUT_UNVERIFIED** | A 5 m resampled LROC NAC south-polar mosaic is geometrically plausible. |
| CAND_B04 | NASA LOLA LDEM 5 m Polar DEM | **MISMATCH** | LOLA is an elevation (laser altimeter) product — not optical imagery. |
| CAND_B05 | USGS Astropedia / Integrated Lunar Mosaic (various resolutions) | **INSUFFICIENT_INFORMATION** | USGS publishes multiple lunar mosaic products. |
| CAND_B06 | Mentor Benchmark Delivery Container (SIH 2026 Package) | **DIRECTLY_SUPPORTED** | The delivery container (benchmark package) is directly identified: synthetic filenames, absent GeoTIFF provenance tags, and consistent packaging structure uniquely identify the benchmark delivery layer. |
| CAND_B07 | ISRO CH-2 TMC-2 Single-Strip Ortho-Image | **MISMATCH** | The PDS4 XML source fields (level0_dataset, corners) are for the OHRC SOURCE raster — the moving OHRC observation. |

> [!NOTE]
> No candidate achieves `DIRECTLY_SUPPORTED` classification for the upstream cartographic
> source product. `CAND_B06` (Delivery Container) is `DIRECTLY_SUPPORTED` only as the
> packaging layer — the upstream geodetic source remains `UNKNOWN`.

---

## 5. Track 3 — Geodetic-Frame Reconciliation

*(Reuses Phase 23A.7 verified results. No novel SPICE calls.)*

| Frame Pair | Max Surface Displacement | vs Observed Residual | Classification |
|------------|------------------------|----------------------|----------------|
| IAU_MOON ↔ MOON_ME_DE421 | **66.0 m** | 15.2%–4.0% of residual | **NOT_SUFFICIENT_TO_EXPLAIN** |
| MOON_ME_DE421 ↔ MOON_ME | 0 m (same frame alias) | N/A | NOT_A_DISTINCT_FRAME |
| IAU_MOON ↔ ULCN2005 | Unknown | — | INSUFFICIENT_INFORMATION |

> **The IAU_MOON <-> MOON_ME_DE421 frame rotation produces a maximum surface displacement of 66.0 m at the south pole (Phase 23A.7 verified). This is 15.2%–4.0% of the observed 435–1634 m residual. The frame effect cannot explain the kilometre-scale registration residual. No additional frame transformations are available within the verified SPICE kernel set that would produce a larger displacement.**

**Additional frame candidates examined:**

- **MOON_ME_DE421 vs MOON_ME (generic):** NOT_A_DISTINCT_FRAME — MOON_ME in the SPICE kernel moon_080317.tf is defined as an alias of MOON_ME_DE421 (TKFRAME_-31001_RELATIVE = 'MOON_ME_DE421'). These are the same physical frame — no separate rotation exists.
- **IAU_MOON vs MOON_PA_DE421:** INTERMEDIATE_FRAME — MOON_PA_DE421 is the principal-axis frame from DE421. IAU_MOON is a low-degree Euler-angle approximation. MOON_ME_DE421 is derived from MOON_PA_DE421 with a small offset. Combined IAU_MOON → MOON_PA_DE421 → MOON_ME_DE421 chain was verified in Phase 23A.7 with the same upper-bound result.
- **ULCN2005 vs MOON_ME_DE421:** INSUFFICIENT_INFORMATION — ULCN2005 (Unified Lunar Control Network 2005) is an older control network realization. The delivered GeoTIFF contains no reference to ULCN2005. If the reference raster was tied to ULCN2005, an offset of unknown magnitude could exist. No transformation from ULCN2005 to MOON_ME_DE421 is available in the audited SPICE kernels. Status: INSUFFICIENT_INFORMATION.

---

## 6. Track 4 — Raster-Grid / Coordinate-Origin Audit

### 6.1 Standard Convention Verification

| Convention | Value | Status |
|-----------|-------|--------|
| Raster pixel type | `RasterPixelIsArea` (GeoKey 1025 = 1) | **VERIFIED** |
| Tiepoint pixel reference | Centre of pixel (col=0, row=0) | **VERIFIED** |
| False easting | 0.0 m | **VERIFIED** |
| False northing | 0.0 m | **VERIFIED** |
| Scale factor at pole | 1.0 | **VERIFIED** |
| Linear units | metres | **VERIFIED** |
| Row direction | Top-to-bottom (N decreases downward) | **VERIFIED** |
| Column direction | Left-to-right (E increases rightward) | **VERIFIED** |
| Grid phase (E mod 5) | 3.0 m (all 4 pairs) | **VERIFIED** |
| Grid phase (N mod 5) | 2.0 m (all 4 pairs) | **VERIFIED** |
| PixelIsPoint half-pixel offset | 2.5 m (sub-pixel, negligible) | **VERIFIED (negligible)** |

### 6.2 Non-Standard Finding: ProjStraightVertPoleLong = 1.0 deg

GeoKey 3092 (ProjStraightVertPoleLong) = 1.0 deg instead of the conventional 0.0 deg. This shifts the map orientation by 1 degree. At the south pole, a 1 deg rotation of the stereographic projection axes produces a surface displacement of 0 m at the pole itself and grows with distance from the pole. At 150 km from the pole (typical for these rasters): disp = 150000 * sin(1 deg) = 2617.9 m. This is a sub-kilometre effect, not a kilometre-scale systematic offset.

**Azimuthal displacement at 150 km from pole:** `2617.9 m` (azimuthal direction; affects map orientation, not pole position)

> [!WARNING]
> This is a **NEW ANOMALOUS FINDING** in Phase 23B. GeoKey 3092 = 1.0 deg is non-standard.
> The surface-displacement consequence at typical raster distances from the pole is
> sub-kilometre to ~2.6 km. This cannot be confirmed as the source of the km-scale
> residual without an authoritative external reference product for comparison.

---

## 7. Track 5 — Provenance-Link Audit

| Item Searched | Result | Status |
|--------------|--------|--------|
| GeoTIFF TIFFTAG_SOFTWARE (tag 305) | ABSENT in all 4 pairs. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| GeoTIFF TIFFTAG_DATETIME (tag 306) | ABSENT in all 4 pairs. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| GeoTIFF TIFFTAG_IMAGEDESCRIPTION (tag 270) | ABSENT in all 4 pairs. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| GeoTIFF TIFFTAG_ARTIST (tag 315) | ABSENT in all 4 pairs. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| GeoTIFF GDAL_METADATA (tag 42112) | ABSENT in all 4 pairs. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| PDS4 XML <ReferenceUsed> | 'System' in all 4 pairs — does not name the external reference product. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| PDS4 XML <AutoLCP> block (orthorectification control points) | AutoLCP block present but contains only a StartTime; no GCP list or reference product ID. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| PDS4 XML <SelenoTagging> block | SelenoTagging timestamps present (start/stop). | **NOT_FOUND_IN_AUDITED_INPUTS** |
| PDS4 XML processing log / provenance chain | No explicit processing log or full provenance chain embedded in the XML. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| Bundle-adjustment / GCP metadata | No bundle-adjustment or GCP metadata found. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| Map-generation software / version string | No software version string found in any file. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| Original orthorectification DEM identification | Not recorded. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| GeoKeyDirectoryTag — ProjectedCSTypeGeoKey (3072) | 32767 (user-defined) — no EPSG code assigned. | **FOUND_BUT_NON_IDENTIFYING** |
| GeoKeyDirectoryTag — GeographicTypeGeoKey (2048) | 32767 (user-defined) — no standard geographic CRS code. | **FOUND_BUT_NON_IDENTIFYING** |
| GeoKeyDirectoryTag — GeogGeodeticDatumGeoKey (2050) | 32767 (user-defined) — datum coded as user-defined. | **FOUND_BUT_NON_IDENTIFYING** |
| GeoKeyDirectoryTag — Key_2054 (angular units) | 9102 (Angular_Degree) — standard value, non-identifying. | **FOUND_BUT_NON_IDENTIFYING** |
| GeoKeyDirectoryTag — ProjStraightVertPoleLong (3092) | 1. | **FOUND_ANOMALOUS** |

> [!NOTE]
> Absence of provenance metadata is documented as `NOT_FOUND_IN_AUDITED_INPUTS`.
> This does NOT imply that such metadata never existed — it may exist in ISRO internal
> processing archives not available to this audit.

---

## 8. Track 6 — Pair 02/03 Consistency Check

### 8.1 Verified Identical-Overlap Result (IMMUTABLE)

| Measurement | Value |
|-------------|-------|
| Overlap polygon E (m) | [67338.0, 73558.0] |
| Overlap polygon N (m) | [121552.0, 150047.0] |
| Overlap dimensions | `1,244 × 5,699` pixels |
| Total pixels | `7,089,556` |
| Identical pixels | `7,089,556` (`100.00%`) |
| Mean diff | `0.0000` |
| RMS diff | `0.0000` |
| Status | **`100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP`** |

### 8.2 Supported Inferences

- The reference rasters for Pair 02 and Pair 03 share identical pixel values over their verified geometric overlap. This is consistent with both rasters drawing from common pre-existing reference content.
- The common 5 m grid phase (E mod 5 = 3.0, N mod 5 = 2.0) across all 4 pairs confirms all rasters are phase-aligned to the same 5 m projected coordinate lattice.
- The identical content is consistent with both rasters having been extracted from the same underlying reference mosaic or an identical replication thereof.

### 8.3 Unsupported Inferences (Explicitly Excluded)

- The identical overlap does NOT prove the geodetic realization of the common reference content. Two rasters drawn from the same mosaic share the same geodetic errors as well as the same pixel values.
- The identical overlap does NOT identify the upstream optical mosaic product from which the reference content was derived.
- The identical overlap does NOT prove that the reference content is linked to MOON_ME_DE421 or any other named geodetic frame.
- The identical overlap does NOT prove that the reference rasters represent a static pre-existing mosaic (as opposed to a dynamically reprocessed product that happens to produce identical results over this overlap).

**Geodetic implication:** NEUTRAL. The Pair 02/03 content identity is evidence of consistent reference content delivery. It provides no new information about the absolute geodetic realization of that content.

---

## 9. Track 7 — Final Classification Decision Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| A | Geodetic realization directly identified | ✗ |
| B | Geodetic realization constrained but not identified | ✗ |
| **C** | **Geodetic realization remains unresolved** | **✓** |

**Selected:** `C — Geodetic realization remains unresolved`

**Evidentiary basis:**

1. Track 1 — All GeoTIFF provenance tags (Software, DateTime, Artist, ImageDescription, GDAL_METADATA) are ABSENT. GeoAsciiParams is generic 'GCS_Moon / D_Moon' — used by multiple ISRO/USGS pipeline variants.
2. Track 2 — No candidate product achieves DIRECTLY_SUPPORTED classification for the upstream cartographic source. CAND_B01 (TMC-2 Polar Mosaic) and CAND_B03 (LROC NAC Mosaic) are COMPATIBLE_BUT_UNVERIFIED. CAND_B06 (Delivery Container) is DIRECTLY_SUPPORTED as the packaging layer only — not as the upstream geodetic source.
3. Track 3 — The IAU_MOON <-> MOON_ME_DE421 frame rotation (max 66.0 m) cannot explain the km-scale observed residual. No additional frame transformations are available in the audited kernel set.
4. Track 4 — Raster conventions are internally consistent (PixelIsArea, false E/N = 0, scale = 1.0). ANOMALY: ProjStraightVertPoleLong = 1.0 deg (non-standard). This could imply a ~2.6 km azimuthal displacement at 150 km from the pole, but cannot be confirmed or ruled out without external reference product comparison.
5. Track 5 — Provenance-link audit found no processing logs, GCP lists, software version strings, or product identifiers in any delivered file. PDS4 <ReferenceUsed>System</ReferenceUsed> does not name the external mosaic.
6. Track 6 — Pair 02/03 identical overlap is evidence of consistent reference content; it provides no new information about geodetic realization.

---

## 10. New Finding — ProjStraightVertPoleLong Anomaly

**Finding:** ProjStraightVertPoleLong = 1.0 deg (GeoKey 3092)  
**Status:** `ANOMALOUS — NEW FINDING IN PHASE 23B`  

If interpreted as a real azimuthal map orientation offset (not a pipeline encoding artifact), a 1 deg rotation of the stereographic frame would produce a displacement of distance_from_pole * sin(1 deg) in the azimuthal direction. At 150 km from the pole, this is ~2,618 m. This is of the same order of magnitude as the observed km-scale residual. HOWEVER: (1) This parameter may be a GeoTIFF encoding convention rather than a real rotation. (2) Without an authoritative reference product to compare against, the effect cannot be separated from other sources of the residual. (3) This finding is classified ANOMALOUS and requires further investigation in a future phase. It does NOT constitute a resolved explanation.

**Action:** No correction applied. No empirical transform fitted. This finding is recorded for future investigation.

---

## 11. What This Audit Does NOT Prove

- This audit does NOT prove the reference rasters are linked to MOON_ME_DE421.
- This audit does NOT prove the reference rasters are linked to IAU_MOON.
- This audit does NOT prove the reference rasters are linked to ULCN2005.
- This audit does NOT identify the upstream optical mosaic source product.
- This audit does NOT establish the absolute geodetic accuracy of the reference rasters.
- This audit does NOT prove or disprove any candidate product hypothesis.
- The ProjStraightVertPoleLong = 1.0 anomaly does NOT, by itself, explain the km-scale registration residual — it is a necessary but not sufficient explanation.
- The identical Pair 02/03 overlap does NOT prove the reference is a specific product.

---

## 12. Unresolved Items Carried Forward

| Item | Status |
|------|--------|
| Upstream cartographic source product identity | `UNRESOLVED` |
| Reference geodetic realization (frame name) | `UNKNOWN` |
| Reference raster → MOON_ME_DE421 linkage | `NOT_VERIFIED` |
| ProjStraightVertPoleLong = 1.0 deg anomaly | `ANOMALOUS — FUTURE INVESTIGATION` |
| ULCN2005 vs MOON_ME_DE421 offset | `INSUFFICIENT_INFORMATION` |
| ISRO SelenoTagging reference product | `NOT_FOUND_IN_AUDITED_INPUTS` |
| AutoLCP reference product | `NOT_FOUND_IN_AUDITED_INPUTS` |

---

## 13. Final Status Block

> [!IMPORTANT]
> **`REFERENCE_PRODUCT_UNRESOLVED`**  
> **`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`**  
> **`REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED`**  
> **`PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW`**  
>
> Phase 23B executed a full multi-track geodetic link review. The geodetic realization
> remains unresolved. Phase 23B is NOT considered complete merely because this audit ran.
> Production registration remains frozen.

---

## 14. Reproducibility

- **Script:** `run_phase23b_geodetic_link_review.py`
- **Python:** standard library + PIL (Pillow) only
- **No GDAL, no SPICE, no image matching performed**
- **Input data:** delivered mentor benchmark TIFFs + PDS4 XMLs (unmodified)
- **Frame data:** Phase 23A.7 verified constants (no new SPICE calls)

---

> # **`PHASE 23B EXECUTED — GEODETIC REALIZATION REMAINS UNRESOLVED`**

