# 3D Physical Projection & Geodetic Frame Research Artifacts

**Directory:** `research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/`  
**Mission:** Chandrayaan-2 OHRC Benchmark  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## Directory Overview

This directory contains all code, telemetry datasets, sensitivity analyses, and scientific audit reports generated across **Phases 23A, 23A.5, 23A.6, 23A.7, 23A.8, and 23A.9**.

### 1. Phase 23A — OHRC Physical Projection Sanity Test
- `run_phase23a_projection_test.py` — Test harness for forward physical ray tracing and LOLA DEM intersection.
- `phase23a_ray_samples.csv` / `.json` — 36-record physical look-vector and ground intersection telemetry matrix.
- `phase23a_geometry_report.md` — Sensor-to-ground geometry and relief displacement audit.
- `phase23a_dem_resolution_report.md` — LOLA 20m vs 5m sensitivity report.
- `phase23a_map_consistency_report.md` — Reference map canvas overlay and residual cross-check report.
- `phase23a_readiness_summary.md` — Phase 23A readiness gate assessment.

### 2. Phase 23A.5 — Physical Projection Residual Attribution Audit
- `run_phase23a5_attribution_audit.py` — Test harness for controlled single-parameter sensitivity tests.
- `phase23a5_residual_attribution.csv` / `.json` — 69-record multi-domain sensitivity matrix.
- `phase23a5_map_equation_audit.md` — Polar Stereographic and Selenographic projection equation audit.
- `phase23a5_attitude_sensitivity.md` — Spacecraft attitude perturbation analysis.
- `phase23a5_ephemeris_sensitivity.md` — Trajectory along-track, cross-track, and radial sensitivity analysis.
- `phase23a5_timing_sensitivity.md` — Scanline timing and row period sensitivity analysis.
- `phase23a5_camera_mapping_sensitivity.md` — Pixel-center and scaling quantization analysis.
- `phase23a5_dem_sensitivity.md` — DEM vertical displacement audit.
- `phase23a5_pair04_crop_analysis.md` — Pair 04 uncropped native telemetry audit.
- `phase23a5_readiness_report.md` — Synthesis report and Phase 23A.5 readiness gate assessment.

### 3. Phase 23A.6 — Rigid Geodetic / Frame Offset Reconciliation
- `run_phase23a6_rigid_offset_reconciliation.py` — Test harness for 2D rigid/affine translation fitting and sensitivity extrapolation.
- `phase23a6_rigid_offset.csv` / `.json` — 20-record rigid translation and affine transformation dataset.
- `phase23a6_reference_map_frame_audit.md` — Reference GeoTIFF cartographic and geodetic audit.
- `phase23a6_pair_comparison.md` — Cross-pair comparative analysis and Pair 02 vs Pair 03 audit.
- `phase23a6_spice_frame_audit.md` — SPICE frame-chain and lunar frame audit (`IAU_MOON` vs `MOON_ME`).
- `phase23a6_required_offset_sensitivity.md` — Extrapolated position offset magnitude analysis.
- `phase23a6_readiness_report.md` — Master synthesis report and Phase 23A.6 readiness gate report.

### 4. Phase 23A.7 — Frame / Geodetic Reconciliation Review
- `run_phase23a7_frame_geodetic_reconciliation.py` — Test harness for DE421 frame resolution, surface displacement, ground-track, and scenario testing.
- `phase23a7_frame_reconciliation.csv` / `.json` — Full machine-readable dataset (corners, centers, displacements, scenarios A/B, ground tracks).
- `phase23a7_spice_frame_report.md` — Authoritative kernel inventory and SPICE frame audit (`IAU_MOON` <-> `MOON_ME_DE421` rotation analysis).
- `phase23a7_surface_displacement_report.md` — Surface displacement evaluation and Scenario A vs Scenario B comparison.
- `phase23a7_reference_geodetic_audit.md` — Reference GeoTIFF cartographic and geodetic realization audit (`GEODETIC_LINK_NOT_VERIFIED`).
- `phase23a7_ground_track_audit.md` — Independent spacecraft ground-track computation (`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`).
- `phase23a7_pair02_pair03_frame_comparison.md` — Nominally co-located Pair 02 vs Pair 03 frame test (`NOT_SUFFICIENT_TO_EXPLAIN`).
- `phase23a7_readiness_report.md` — Master synthesis report and Phase 23B readiness gate assessment.

### 5. Phase 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit
- `run_phase23a8_reference_geodetic_audit.py` — Test harness for reference GeoTIFF header parsing, empirical basemap overlap analysis, and evidence compilation.
- `phase23a8_reference_provenance.csv` / `.json` — 15-record claim-evidence provenance database across all audited parameters.
- `phase23a8_product_lineage_audit.md` — Product lineage, sensor identity, delivery context, and 100.00% identical reference content over verified overlap proof.
- `phase23a8_geodetic_realization_audit.md` — Lunar geodetic reference realization audit (`REFERENCE_FRAME_UNRESOLVED`).
- `phase23a8_map_generation_audit.md` — Map-generation provenance, GCP audit, and ad-hoc fitting prohibition / no documented control solution identified.
- `phase23a8_reference_to_moonme_audit.md` — Reference raster to `MOON_ME_DE421` linkage audit and residual scale comparison.
- `phase23a8_readiness_report.md` — Master synthesis report and Phase 23B readiness gate assessment.

### 6. Phase 23A.9 — External Reference Product Provenance Identification
- `run_phase23a9_reference_product_identification.py` — Candidate product registry, metadata comparison, grid analysis, and synthesis script.
- `phase23a9_reference_product_registry.csv` / `.json` — 7-candidate structured external product registry.
- `phase23a9_candidate_metadata_comparison.md` — Property-by-property candidate metadata comparison matrix.
- `phase23a9_product_lineage_report.md` — Multi-mission candidate lineage investigation and non-inference audit.
- `phase23a9_content_fingerprint_report.md` — Discrete sampling grid alignment analysis and 100% overlap proof.
- `phase23a9_geodetic_realization_report.md` — Candidate geodetic realization and MOON_ME_DE421 linkage audit.
- `phase23a9_readiness_report.md` — Master synthesis report and Phase 23B readiness gate assessment.

### 7. Integrity Verification
- `checksums.sha256` — Cryptographic SHA-256 verification hashes across all files in this directory.

---

## Mandatory Governance Guardrails
- Production Freeze Canonical Set: `app/app.py`, `app/adaptive_adapter.py`, `app/registration_core.py`, `research/adaptive_matcher/adaptive_engine.py`.
- Explicit Path Audit: `app/adaptive_engine.py = NOT PRESENT IN CANONICAL PROJECT` (Status: NON-EXISTENT / NOT PART OF CANONICAL PROJECT).
- Production Freeze Provenance: `PRODUCTION_BASELINE_PROVENANCE = NOT_INDEPENDENTLY_VERIFIED`.
- Note: *The current Git snapshot verifies that the tracked production files have not changed since the snapshot commit, but it does not independently establish historical equivalence to the pre-Phase-23A.6 state.*
- Production code (`app/`, `research/adaptive_matcher/`) remains **FROZEN FOR THIS AUDIT**.
- Zero feature matching, zero image warping, zero pose optimization, and zero registration fitting.
- Mandatory distortion caveat: *'Optical distortion is not modeled; distortion uncertainty is unquantified.'*
- Current Concluding Status: **`PHASE 23A.9 COMPLETE — REFERENCE PRODUCT REMAINS UNRESOLVED`**.


## Phase 23B — Reference Geodetic Realization / Geodetic Link Review

**Generated:** 2026-09-24T05:37:49Z  
**Script:** `run_phase23b_geodetic_link_review.py`  
**Status:** EXECUTED — GEODETIC REALIZATION REMAINS UNRESOLVED  

### Outputs

| File | Description |
|------|-------------|
| `phase23b_geodetic_link_review.md` | Main Phase 23B research report (8 tracks) |
| `phase23b_candidate_registry.csv` | Authoritative candidate source audit (7 candidates) |
| `phase23b_candidate_registry.json` | Machine-readable candidate registry |
| `phase23b_coordinate_convention_report.md` | Raster-grid / coordinate-origin audit |
| `phase23b_provenance_link_report.md` | Provenance-link audit findings |
| `phase23b_frame_reconciliation_report.md` | Geodetic-frame reconciliation report |
| `phase23b_readiness_report.md` | Phase gate and final status |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

### New Finding

**ProjStraightVertPoleLong (GeoKey 3092) = 1.0 deg** (non-standard; conventional is 0.0 deg).  
Implies azimuthal displacement of ~2,618 m at 150 km from pole.  
Status: `ANOMALOUS — FUTURE INVESTIGATION REQUIRED`.

## Phase 23B.1 -- GeoKey 3092 Geodetic Sensitivity Test

**Generated:** 2026-09-24T06:03:17Z  
**Script:** `run_phase23b1_geokey3092_sensitivity.py`  
**Status:** EXECUTED -- SENSITIVITY TEST COMPLETE  

### Outputs

| File | Description |
|------|-------------|
| `phase23b1_geokey3092_sensitivity_report.md` | Main sensitivity report |
| `phase23b1_projection_semantics_report.md` | Authoritative GeoKey 3092 semantics |
| `phase23b1_pairwise_metrics.csv` | Per-corner metrics (all pairs) |
| `phase23b1_pairwise_metrics.json` | Machine-readable full dataset |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

## Phase 23B.2 -- Standard CRS / GeoTIFF Reader Semantics Audit

**Generated:** 2026-09-24T07:05:04Z  
**Script:** `run_phase23b2_crs_reader_semantics.py`  
**Classification:** `A -- READER-SEMANTICS-CONFIRMED`  

### Key Discovery

Authoritative OGC GeoTIFF 1.1 Specification and libgeotiff headers resolve the GeoKey identity:
- **GeoKey 3092 IS `ProjScaleAtNatOriginGeoKey`** (Scale at Natural Origin = 1.0).
- **GeoKey 3095 IS `ProjStraightVertPoleLongGeoKey`** (Central Meridian = 0.0 deg).
- The reference GeoTIFF contains no non-standard orientation. All standard readers (GDAL, Rasterio, PROJ) consume the reference rasters with lambda_0 = 0.0 deg and k_0 = 1.0, matching our audited Phase 23A mathematical implementation with zero discrepancy (< 10^-10 m).

### Outputs

| File | Description |
|------|-------------|
| `phase23b2_crs_reader_semantics_report.md` | Authoritative specification and multi-reader audit |
| `phase23b2_coordinate_validation_report.md` | 36-point deterministic coordinate validation |
| `phase23b2_reader_comparison.csv` | Tabular comparison across points and readers |
| `phase23b2_reader_comparison.json` | Complete machine-readable multi-reader dataset |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

## Phase 23B.3 -- Reference Product Geodetic Provenance & Direct Content Fingerprint Audit

**Generated:** 2026-09-24T07:36:30Z  
**Script:** `run_phase23b3_reference_provenance_audit.py`  
**Final Classification:** `D -- UNRESOLVED`  

### Key Finding

Eight evidence tracks (local provenance, PDS4 lineage, content fingerprinting, grid compatibility,
reference content identity, geodetic realization comparison, absolute coordinate constraints,
authoritative documentation) found NO direct provenance link to an upstream map product.

- All TIFF provenance tags absent from all 4 reference GeoTIFFs.
- PDS4 labels record OHRC source ID but use generic `<ReferenceUsed>System</ReferenceUsed>`.
- No authoritative local source file available for pixel-level content comparison.
- The Pair 02/03 identical overlap confirms static common reference content; upstream product unidentified.
- Multiple candidates are geometrically compatible but none is identified.

### Outputs

| File | Description |
|------|-------------|
| `phase23b3_reference_provenance_audit.md` | Main 20-section provenance audit report |
| `phase23b3_geodetic_realization_comparison.md` | Geodetic frame comparison across candidates |
| `phase23b3_candidate_content_fingerprint.csv` | Per-window pixel fingerprints (SHA256, statistics) |
| `phase23b3_candidate_content_fingerprint.json` | Machine-readable fingerprint dataset |
| `phase23b3_provenance_evidence_registry.csv` | Evidence registry (candidates + documentation) |
| `phase23b3_provenance_evidence_registry.json` | Machine-readable evidence registry |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

---

## Phase 24A — Cheap Deterministic Coarse Image-Space Prefilter

**Generated:** 2026-09-24T15:06:12Z
**Script:** `run_phase24a_coarse_localization.py`
**Total Runtime:** 387.55 s (6.5 min)
**Overall Classification:** `VERIFICATION_FAILED`

### Research Question

*"Can a cheap deterministic structural prefilter identify a small set of image-space placement hypotheses that are worth expensive LoFTR verification?"*

### Experimental Design

- **Coarse offset lattice (metres):** `{-3000, -2000, -1000, 0, 1000, 2000, 3000}` → 7×7 = **49 offsets / pair**
- **Total coarse candidates:** **196** (49 × 4 OHRC mentor pairs)
- **Reference scale:** 5 m / px → pixel offsets `{-600,-400,-200,0,200,400,600}` px
- **Search center:** Nominal reference footprint from audited Phase 23 physical projection (NOT moved by Phase 23A.6 translations; those values reported only for comparison)
- **Local window framework:** Deterministic 3×3 source windows (9 windows / pair, 128×128 px each)
- **Cheap diagnostics (per window):**
  - A — Intensity ZMUV NCC (`T_INT_NCC_MIN = 0.08`)
  - B — Sobel gradient NCC (`T_GRAD_NCC_MIN = 0.06`)
  - C — Phase correlation response (`T_PHASE_RESP_MIN = 0.05`)
  - D — FAST+ZMUV structural correspondence count (`T_FAST_N_MIN = 3` per window; `T_FAST_ANY_CANDIDATES = 4`)
- **SCREEN_PASS rule** (predeclared, NOT tuned after):
  - C1: ≥ 3 valid local windows
  - C2: ≥ 3 distinct 3×3 spatial cells
  - C3: finite phase-correlation response
  - C4: structural strength criterion met
  - C5: no invalidating missing support

### Outputs

| File | Description |
|------|-------------|
| `run_phase24a_coarse_localization.py` | Experiment driver (checkpointed, resumable) |
| `phase24a_coarse_localization_report.md` | Aggregate report & interpretation |
| `phase24a_failure_classification.md` | F1–F5 failure drill-down |
| `phase24a_screen_candidates.csv` | 196-row coarse screening telemetry |
| `phase24a_screen_candidates.json` | Machine-readable screen dataset |
| `phase24a_loftr_verification.csv` | LoFTR verification results (SCREEN_PASS only: 16 rows) |
| `phase24a_pair_summary.csv` | 4-row per-pair summary table |
| `phase24a_checkpoint.json` | Resumable deterministic checkpoint |

### Aggregate Counts

| Metric | Count |
|:---|---:|
| Total coarse candidates | **196** |
| SCREEN_PASS | **16** |
| SCREEN_FAIL | 171 |
| INSUFFICIENT_SUPPORT | 9 |
| LoFTR verification runs (SCREEN_PASS ONLY) | **16** |
| Initial QG passes (n_cand≥10 ∧ n_inl≥8 ∧ ratio≥0.20) | 0 |
| Full QG passes (incl. occupancy ≥0.33, final ≥4, held-out) | 0 |
| Hold-out / F5 validated | 0 |

### Per-Pair Results (49 candidates per pair)

| Pair | Coarse | SCREEN_PASS | LoFTR | Initial QG | Full QG | F5 | Failure Class |
|:---|---:|---:|---:|---:|---:|---:|:---|
| OHRC_PAIR_01 | 49 | 0 | 0 | 0 | 0 | 0 | F2 |
| OHRC_PAIR_02 | 49 | 13 | 13 | 0 | 0 | 0 | F3 |
| OHRC_PAIR_03 | 49 | 3 | 3 | 0 | 0 | 0 | F3 |
| OHRC_PAIR_04 | 49 | 0 | 0 | 0 | 0 | 0 | F2 |

### Controls

| Control | Type | Cheap Decision | LoFTR n_inliers | Expected | Observed |
|:---|:---|:---|---:|:---|:---|
| C1 | Negative (non-overlapping far corner) | `SCREEN_FAIL` | 0 | MINIMAL_INLIERS | AS_EXPECTED_NEGATIVE |
| C2 | Synthetic positive (R=2°, tx=10, ty=10) | `SCREEN_PASS` | 1867 | SUBSTANTIAL_INLIERS | AS_EXPECTED_POSITIVE |
| C3 | Same-sensor Pair 02 nominal overlap (dx=dy=0) | `SCREEN_FAIL` | 0 | INDICATOR_OF_SENSITIVITY | n_candidates=0; cross-modal domain-gap indicator |

### Final Classification Block

```
Phase 24A Overall Classification: VERIFICATION_FAILED
  → Coarse structural evidence exists at some predefined placements,
    but reliable correspondence / geometric consistency was not
    demonstrated through the frozen LoFTR quality gate and
    independent hold-out validation.

Phase 24 (original, UNCHANGED — NO CLAIM MADE):
  PHASE_24_STATUS = DEFERRED_COMPUTATIONAL_COST
  PHASE_24_RESEARCH_RESULT = INCONCLUSIVE

Geodetic status (PRESERVED UNCHANGED from Phase 23B):
  REFERENCE_PRODUCT_UNRESOLVED
  REFERENCE_GEODETIC_REALIZATION = UNKNOWN
  REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
  PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

### Interpretation Boundaries

- This phase is **candidate-window screening only**. It is NOT registration, NOT geolocation, NOT geodetic correction, NOT reference-product identification.
- No ranking of candidate offsets is asserted. Multiple candidates may be `SCREEN_PASS`.
- `SCREEN_PASS` ≠ registration. Only `F5 = full frozen QG + independent hold-out` constitutes research-level relative-registration feasibility.
- Production code verified git-clean via `git diff --exit-code -- app/app.py app/adaptive_adapter.py app/registration_core.py research/adaptive_matcher/adaptive_engine.py` → exit_code=0.
- No Phase 23A.6 rigid translation was used to move the search center or choose candidates; grid is strictly the predeclared 7×7 metre lattice.
