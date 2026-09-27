# Phase 23A.9 — Candidate Reference Product Metadata Comparison

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.9 — External Reference Product Provenance Identification  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

Phase 23A.9 evaluates candidate external lunar cartographic products to identify the actual source product used to generate the mentor OHRC reference rasters. A structured evidence registry was constructed across seven candidate products spanning ISRO, NASA, USGS, and custom mentor artifacts.

> ### **Primary Metadata Identification Finding:**
> **Classification:** **`REFERENCE_PRODUCT_UNRESOLVED`**  
> No official candidate product achieves a verified product-level metadata match to the mentor reference rasters. While Candidate 02 (ISRO TMC-2 Polar Mosaic) is contextually compatible in resolution and problem domain, its product identity is unconfirmed in metadata tags. Candidate 07 identifies the benchmark delivery packaging, but leaves the upstream cartographic source unrecorded.

---

## 2. Master Metadata Comparison Matrix

| Evaluation Field | Mentor Reference Rasters | CAND_01: ISRO TMC-2 Single Strip | CAND_02: ISRO TMC-2 Polar Mosaic | CAND_03: NASA LROC NAC 1m Mosaic | CAND_04: NASA LOLA LDEM 5m | CAND_07: Mentor Delivery Container |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Product Name** | `..._reference_at_5m.tif` | `ch2_tmc_..._d_oth_...` | Unofficial SAC polar mosaic | `LROC_NAC_SouthPole_...` | `LDEM_875S_5M` | `..._reference_at_5m.tif` |
| **Product Naming Status** | Synthetic OHRC-derived | **`MISMATCH`** | **`UNKNOWN`** | **`MISMATCH`** | **`MISMATCH`** | **`MATCH`** (Delivery only) |
| **Pixel Scale** | `5.000 m/px` | `5.000 m/px` (**`MATCH`**) | `5.000 m/px` (**`MATCH`**) | `1.000 m/px` (**`MISMATCH`**) | `5.000 m/px` (**`MATCH`**) | `5.000 m/px` (**`MATCH`**) |
| **ModelPixelScaleTag** | `(5.0, 5.0, 0.0)` | `(5.0, 5.0, 0.0)` (**`MATCH`**) | `(5.0, 5.0, 0.0)` (**`MATCH`**) | `(1.0, 1.0, 0.0)` (**`MISMATCH`**) | `(5.0, 5.0, 0.0)` (**`MATCH`**) | `(5.0, 5.0, 0.0)` (**`MATCH`**) |
| **Projection** | Polar Stereographic | Polar Stereographic | Polar Stereographic | Polar Stereographic | Polar Stereographic | Polar Stereographic |
| **Projection Status** | $\phi_0=-90^\circ, \lambda_0=0^\circ$ | **`MATCH`** | **`MATCH`** | **`MATCH`** | **`MATCH`** | **`MATCH`** |
| **Reference Sphere** | $R = 1,737,400.0\text{ m}$ | $R = 1,737,400.0\text{ m}$ (**`MATCH`**) | $R = 1,737,400.0\text{ m}$ (**`MATCH`**) | $R = 1,737,400.0\text{ m}$ (**`MATCH`**) | $R = 1,737,400.0\text{ m}$ (**`MATCH`**) | $R = 1,737,400.0\text{ m}$ (**`MATCH`**) |
| **Data Type** | `Byte` (uint8) | `Byte` / `UInt16` (**`NEAR_MATCH`**) | `Byte` (uint8) (**`MATCH`**) | `Byte` (uint8) (**`MATCH`**) | `Float32`/`Int16` (**`MISMATCH`**) | `Byte` (uint8) (**`MATCH`**) |
| **Image Modality** | Panchromatic optical albedo | Panchromatic optical albedo | Panchromatic optical albedo | Panchromatic optical albedo | Laser Altimetry DEM | Panchromatic optical albedo |
| **Modality Status** | Optical Photography | **`MATCH`** | **`MATCH`** | **`MATCH`** | **`MISMATCH`** (Topography) | **`MATCH`** |
| **Swath / Width** | $2,416 - 5,916\text{ px}$ | $\le 4,000\text{ px}$ (20 km) | Tile-based (>20 km) | $60,000\text{ px}$ tiles | Local landing tiles | $2,416 - 5,916\text{ px}$ |
| **Width Status** | Exceeds single swath | **`MISMATCH`** (Pair 01: 29.5 km) | **`COMPATIBLE`** | **`COMPATIBLE`** (via crop) | **`COMPATIBLE`** | **`MATCH`** |
| **GeoTIFF Tags (305/270)** | `None` / Blank | PDS4 Software / SIS headers | **`UNKNOWN`** | ISIS3 / USGS / ASU tags | PDS Geosciences tags | `None` / Blank (**`MATCH`**) |
| **Tags Status** | Anonymized / Stripped | **`MISMATCH`** | **`UNKNOWN`** | **`MISMATCH`** | **`MISMATCH`** | **`MATCH`** |
| **Geodetic Realization** | `GCS_Moon` (generic) | Selenocentric / `IAU_MOON` | `UNKNOWN` | `MOON_ME_DE421` | `MOON_ME_DE421` | `GCS_Moon` (generic) |
| **Realization Status** | **`UNKNOWN`** | **`MISMATCH`** | **`UNKNOWN`** | **`MISMATCH`** | **`MISMATCH`** | **`MATCH`** (Container) |
| **Accompanying Label** | None for reference | PDS4 XML product label | **`UNKNOWN`** | PDS label (.lbl) | PDS label (.xml/.lbl) | None delivered |
| **Label Status** | Absent | **`MISMATCH`** | **`UNKNOWN`** | **`MISMATCH`** | **`MISMATCH`** | **`MATCH`** |

---

## 3. Detailed Property Classification Rationale

### A. CAND_01 (ISRO TMC-2 Single Strip Ortho-Image) -> **`REJECTED`**
- **Swath Mismatch:** TMC-2 cross-track swath is physically capped at $20\text{ km}$ ($4,000\text{ px}$ at $5\text{ m/px}$). `OHRC_PAIR_01` has a width of $5,916\text{ px}$ ($29.58\text{ km}$), ruling out single-strip origin.
- **Static Multi-Epoch Consistency:** Pairs 02 and 03 observe the same terrain 28 days apart with identical pixel values (difference = 0.0000). A single dynamic pass cannot account for both acquisitions.

### B. CAND_02 (ISRO TMC-2 Polar Mosaic) -> **`UNVERIFIED`**
- **Contextual Compatibility:** Matches resolution ($5.0\text{ m/px}$), projection, radius, and problem domain.
- **Evidentiary Absence:** No official mosaic product ID, PDS4 XML label, or candidate raster is present in the delivery package. In accordance with Phase 23A.8/23A.9 discipline, provenance cannot be inferred from resolution or appearance alone.

### C. CAND_03 (NASA LROC NAC 1m Mosaic) -> **`REJECTED AS DIRECT SOURCE`**
- **Resolution Mismatch:** Published natively at $1.0\text{ m/px}$ or $2.0\text{ m/px}$. ModelPixelScaleTag is $(1.0, 1.0, 0.0) \neq (5.0, 5.0, 0.0)$.
- **Downsampling Dependency:** Derivation would require an unverified 5:1 downsampling filter, which cannot be proven without exact source metadata.

### D. CAND_04 (NASA LOLA LDEM 5m) -> **`REJECTED`**
- **Modality Mismatch:** Laser altimeter elevation model (Float32/Int16 meters) vs 8-bit optical photographic reflectance.

### E. CAND_07 (Mentor Delivery Container) -> **`IDENTIFIED AS PACKAGING CONTAINER ONLY`**
- **Exact Match:** Explains synthetic filename, timestamps (Feb 17, 2026), generic GeoKeys, and stripped tags.
- **Upstream Limitation:** Candidate 07 identifies the benchmark delivery container, but upstream cartographic product provenance remains unresolved.
