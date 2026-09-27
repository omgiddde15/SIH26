# Phase 23A.8 — Master Synthesis & Reference Geodetic Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary & Resolution of Investigation Objectives

Phase 23A.8 was executed to resolve the open uncertainty from Phase 23A.7: `REFERENCE_GEODETIC_REALIZATION = UNKNOWN`. Using embedded GeoTIFF metadata, accompanying delivery files, empirical overlap analysis, and official literature, all required questions have been rigorously answered:

| Investigation Objective | Audit Finding | Supporting Evidence | Scientific Classification |
| :--- | :---: | :--- | :---: |
| **1. Originating mission / product?** | **`UNKNOWN`** | The delivered 5 m/px reference products are cartographically compatible with multiple lunar mapping products; their actual source product remains unverified. Basemap provenance must not be inferred from 5 m/px, projection, radius, geographic extent, or visual appearance. | **`UNCONFIRMED`** |
| **2. Geodetic frame / realization?** | **`UNKNOWN`** | `GCS_Moon` / `D_Moon` generic strings; realization unrecorded. | **`REFERENCE_FRAME_UNRESOLVED`** |
| **3. Datum and radius used?** | **`VERIFIED`** | Horizontal sphere $R = 1,737,400.0\text{ m}$; vertical datum unrecorded. | **`DATUM_SPHERE_VERIFIED`** |
| **4. Map-generation mechanism?** | **`UNKNOWN`** | No GCPs, bundle adjustment logs, or DTM metadata present. | **`UNQUANTIFIED`** |
| **5. Directly tied to DE421 MOON_ME?** | **`NO`** | No tiepoint or declaration links raster to DE421. | **`GEODETIC_LINK_NOT_VERIFIED`** |
| **6. Documented transform to DE421?** | **`NONE IDENTIFIED`** | No documented transformation was identified in the audited local inputs and accompanying product material. | **`NO_DOCUMENTED_TRANSFORM_IDENTIFIED_IN_AUDITED_INPUTS`** |
| **7. Published accuracy vs residual?** | **`CONTEXTUAL ONLY`** | Published accuracies of other products contextual only; pointing does not independently account for full residual. | **`COMBINED_CONTRIBUTION_UNRESOLVED`** |

---

## 2. Master Scientific Classifications

### A. Primary Reference Frame Classification:
> **`Classification: REFERENCE_FRAME_UNRESOLVED`**  

> Embedded GeoTIFF metadata defines the mathematical cartographic projection (Polar Stereographic, $R = 1,737,400.0\text{ m}$), but leaves the physical lunar geodetic reference realization (`MOON_ME_DE421` vs `IAU_MOON` vs `ULCN2005`) completely unrecorded.

### B. Geodetic Uncertainty Characterization:
> 1. **Authoritative frame realization shift (`IAU_MOON` $\leftrightarrow$ `MOON_ME_DE421`):** **`TOO SMALL TO EXPLAIN THE RESIDUAL`** ($22.7–66.0\text{ m}$, accounting for only $1.04\%–5.22\%$ of the residual).  

> 2. **Published accuracies of other lunar cartographic products:** Contextual only; not an established uncertainty bound for the mentor reference raster because its lineage remains unresolved.  

> 3. **System-corrected pointing uncertainty:** Does not independently account for the full residual under the cited bound; combined error contribution remains unresolved.  

> 4. **Delivered mentor reference canvas georeferencing:** **`UNQUANTIFIED`** in metadata, and **`POTENTIALLY MATERIAL`** as an uncalibrated systemic contributor to the observed offset.

### C. Preserved Previous Phase Findings:
> - **Phase 23A.6 Geometric Classification:** **`B — Rigid translation plus a measurable non-rigid component.`**  

> - **Phase 23A.7 Primary Frame Conclusion:** **`C — The tested DE421 lunar-frame difference is too small to explain the observed discrepancy.`**  

> - **Reference-Content Consistency (Empirical):** **`100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP`** (7,089,556 / 7,089,556 pixels identical in Pair 02 / Pair 03 overlap, `Mean diff = 0.0000`). The two delivered reference rasters are identical over the verified overlap, consistent with a common static basemap or identical upstream source. This does not by itself establish the absolute geodetic realization of that common reference. The differential 435.01 m translation between Pair 02 and Pair 03 is not attributable to a difference between the two delivered reference raster contents over their verified common overlap. A common absolute geodetic offset shared by the reference raster remains possible because the reference geodetic realization is unresolved.

---

## 3. Phase 23B Readiness Gate Assessment

| Gate Criterion | Verification Finding | Compliance Status |
| :--- | :--- | :---: |
| **1. Reference raster metadata audited** | All GeoTIFF tags, GeoKeys, and header fields fully parsed | **`SATISFIED`** |
| **2. Product lineage evaluated** | Evaluated via metadata, delivery context, and empirical overlap | **`SATISFIED`** |
| **3. Geodetic realization audited** | Conclusively bounded as unrecorded / unresolved | **`SATISFIED`** |
| **4. Datum and radius audited** | Horizontal sphere $R = 1,737,400\text{ m}$ verified; vertical datum unknown | **`SATISFIED`** |
| **5. Control-point provenance audited** | Documented as absent; ad-hoc fitting strictly rejected | **`SATISFIED`** |
| **6. Linkage to DE421 MOON_ME audited** | Explicitly bounded as unverified; no documented transform exists | **`SATISFIED`** |
| **7. Residual scale comparison completed** | Known uncertainties proven not sufficient to explain residual | **`SATISFIED`** |

> ### **Phase 23B Gate Conclusion:**
> # **`PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW`**  

> Phase 23B registration experiments remain strictly blocked. Automated image matching, image warping, and homography optimization must NOT proceed without an authorized geodetic handling strategy.

---

## 4. Production Freeze & Provenance Audit

- **Canonical Production Freeze Set:**
  - `app/app.py`
  - `app/adaptive_adapter.py`
  - `app/registration_core.py`
  - `research/adaptive_matcher/adaptive_engine.py`
- **Explicit Status of `app/adaptive_engine.py`:**
  - **`app/adaptive_engine.py = NOT PRESENT IN CANONICAL PROJECT`** (Status: NON-EXISTENT / NOT PART OF CANONICAL PROJECT).
- **Production Integrity & Baseline Provenance:**
  - **`PRODUCTION_BASELINE_PROVENANCE = NOT_INDEPENDENTLY_VERIFIED`**
  - `git diff --exit-code -- app/app.py app/adaptive_adapter.py app/registration_core.py research/adaptive_matcher/adaptive_engine.py` -> **`CLEAN`** (Exit code 0).
  - `git status --short --untracked-files=all`: None of the canonical production files appear as untracked files.
- **Zero Production Modification:** All production files untouched; LoFTR weights, RANSAC thresholds, and quality gates 100% frozen.
- **Zero Registration Claims:** No feature matching, image warping, pose optimization, or homography fitting was performed.

---

> # **`PHASE 23A.8 COMPLETE — REFERENCE GEODETIC REALIZATION REMAINS UNRESOLVED`**
