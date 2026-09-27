# 3D Projection Research — Walkthrough & Phase Guide

**Directory:** `research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/`
**Mission:** Chandrayaan-2 OHRC Benchmark
**Governing Discipline:** RESEARCH-ONLY — Production Code FROZEN

---

## Canonical Production Freeze Set (READ-ONLY)

- `app/app.py`
- `app/adaptive_adapter.py`
- `app/registration_core.py`
- `research/adaptive_matcher/adaptive_engine.py`

Verify with:

```
git diff --exit-code -- app/app.py app/adaptive_adapter.py app/registration_core.py research/adaptive_matcher/adaptive_engine.py
echo $?  # must equal 0
```

---

## Phase Sequence (Historical)

| Phase | Code / Script | Status | Primary Deliverable |
|:---|:---|:---|:---|
| 23A | `run_phase23a_projection_test.py` | COMPLETE | Ray-to-DEM intersection (91.7% yield) |
| 23A.5 | `run_phase23a5_attribution_audit.py` | COMPLETE | Single-parameter residual sensitivity matrix |
| 23A.6 | `run_phase23a6_rigid_offset_reconciliation.py` | COMPLETE | 4-corner rigid / affine translation fit dataset |
| 23A.7 | `run_phase23a7_frame_geodetic_reconciliation.py` | COMPLETE | Frame / geodetic reconciliation audit |
| 23A.8 | `run_phase23a8_reference_geodetic_audit.py` | COMPLETE | Reference raster provenance & map-gen audit |
| 23A.9 | `run_phase23a9_reference_product_identification.py` | COMPLETE | 7-candidate external product registry |
| 23B.1 | `run_phase23b1_geokey3092_sensitivity.py` | COMPLETE | ProjStraightVertPoleLong sensitivity test |
| 23B.2 | `run_phase23b2_crs_reader_semantics.py` | COMPLETE | CRS reader semantics (GDAL/Rasterio/PROJ agree) |
| 23B.3 | `run_phase23b3_reference_provenance_audit.py` | COMPLETE | 8-track provenance fingerprint audit |
| 23B | `run_phase23b_geodetic_link_review.py` | COMPLETE | Geodetic link review (GEODETIC_LINK_NOT_VERIFIED) |
| **24A** | `run_phase24a_coarse_localization.py` | **EXECUTED** | **Cheap deterministic coarse prefilter (this doc)** |
| 24 (original) | `run_phase24_geodetic_uncertainty_search.py` | **DEFERRED** | Computational cost; result INCONCLUSIVE |

---

## Phase 24A — Coarse Deterministic Image-Space Prefilter (Walkthrough)

### 1. Objective

Determine whether predefined image-space placements around the physically predicted reference location contain enough cheap structural evidence to justify an expensive LoFTR verification.

> This phase is candidate-window screening **only**. It is NOT registration, NOT geolocation, NOT geodetic correction, and NOT reference-product identification.

### 2. Predeclared Lattice (Immutable)

```
dx, dy ∈ {-3000, -2000, -1000, 0, 1000, 2000, 3000}  metres
          ⇓  (5 m/ref. px; dv_px = -dv_m/5 due to north-up/south-down)
du_px, dv_px ∈ {-600, -400, -200, 0, 200, 400, 600}  pixels
```

- **Per pair:** 7 × 7 = **49** deterministic offset hypotheses
- **4 pairs (01–04):** **196** coarse candidates total
- **No** Phase 23A.6 translation was used to move the search center or select candidates.
- Phase 23A.6 rigid translations are recorded alongside each candidate **for comparison only**.

### 3. Per-Candidate Cheap Diagnostics (Fixed, Predeclared Thresholds)

For each of 9 deterministic 3×3 source-local windows, compute:

| Code | Diagnostic | Threshold |
|:---|:---|:---|
| A | Intensity zero-mean/unit-variance NCC | `T_INT_NCC_MIN = 0.08` |
| B | Sobel gradient magnitude NCC | `T_GRAD_NCC_MIN = 0.06` |
| C | Hann-windowed phase-correlation response | `T_PHASE_RESP_MIN = 0.05` |
| D | FAST keypoints on Sobel grad + 15×15 ZMUV + Lowe-0.80 BFM knn | `T_FAST_N_MIN = 3` (per window); `T_FAST_ANY_CANDIDATES = 4` (any-window) |

**SCREEN_PASS rule** (all 5 must hold):
1. ≥ 3 valid local supported windows
2. ≥ 3 distinct supported 3×3 spatial cells
3. Finite phase-correlation response
4. Structural strength criterion satisfied
5. No invalidating missing-support condition

Otherwise: `SCREEN_FAIL` or `INSUFFICIENT_SUPPORT` (F1 proxy).

### 4. Frozen LoFTR Quality Gate (UNCHANGED from directive)

Only `SCREEN_PASS` candidates receive LoFTR. `SCREEN_FAIL` candidates **do not** receive LoFTR.

```
min_candidates              = 10
min_initial_inliers         = 8
min_initial_inlier_ratio    = 0.20
min_occupancy               = 0.33
ransac_threshold            = 3.0 px
downstream_min_final_inliers = 4
grid                        = 3x3  (max 6 points / cell)
validation_seeds            = (1, 2, 3, 4, 5)
```

**F5 (research-validated relative-registration candidate) requires ALL of:**
- frozen initial quality gate passes
- downstream geometry succeeds
- spatial occupancy ≥ 0.33
- ≥ 5 independent seed-level hold-out validations pass

### 5. Controls (Declared Before Results)

| ID | Kind | Expected |
|:---|:---|:---|
| C1 | Negative (non-overlapping top-left Pair 01 reference 512×512 crop) | SCREEN_FAIL or minimal inliers |
| C2 | Positive (synthetic: R=2°, tx=10, ty=10 px, 400×400 structured scene) | SCREEN_PASS + substantial inliers |
| C3 | Displaced / sensitivity (Pair 02 source vs nominal reference crop) | Indicator of matcher sensitivity (cross-modal domain gap) |

### 6. Failure Classes

| ID | Meaning |
|:---|:---|
| F1 | Insufficient reference support |
| F2 | No coarse structural recovery |
| F3 | Coarse structure exists but LoFTR correspondence insufficient |
| F4 | LoFTR geometry initially passes but hold-out fails |
| F5 | Validated relative-registration candidate exists |

### 7. Reproducing the Experiment

```powershell
# (a) Verify production freeze (MUST exit 0)
git diff --exit-code -- `
  app/app.py app/adaptive_adapter.py `
  app/registration_core.py research/adaptive_matcher/adaptive_engine.py
echo "Production freeze exit=$LASTEXITCODE"

# (b) Run (resumable via phase24a_checkpoint.json)
py -3 research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/run_phase24a_coarse_localization.py

# (c) Expected footprint on this hardware:
#     ~ 6.5 min (CPU only, 4 Torch threads), ~196 coarse + 16 LoFTR
```

### 8. Expected Outputs

| File | Rows | Purpose |
|:---|---:|:---|
| `phase24a_checkpoint.json` | — | Resumable state; `candidates.{key}.stage ∈ {cheap_done, complete}` |
| `phase24a_screen_candidates.csv` | 196 | Per-candidate cheap screening telemetry + decision |
| `phase24a_screen_candidates.json` | 196 | Machine-readable screen dataset |
| `phase24a_loftr_verification.csv` | 16 | SCREEN_PASS → LoFTR result + QG + downstream + failure-class |
| `phase24a_pair_summary.csv` | 4 | Per-pair counts + F-class + rationale |
| `phase24a_coarse_localization_report.md` | — | Aggregate report & interpretation boundaries |
| `phase24a_failure_classification.md` | — | F1–F5 drill-down + per-candidate LoFTR table |

### 9. Actual Result Summary (This Run)

- **196 / 196** coarse candidates generated (49 × 4 pairs).
- **SCREEN_PASS:** **16** (Pair 02: 13; Pair 03: 3; Pair 01: 0; Pair 04: 0)
- **SCREEN_FAIL:** **171**; **INSUFFICIENT_SUPPORT:** **9**
- **LoFTR runs (SCREEN_PASS only):** **16** (0 LoFTR runs on SCREEN_FAIL).
- **Initial QG (n_cand≥10 ∧ n_inl≥8 ∧ ratio≥0.20):** 0 / 16
- **Full QG + hold-out (F5):** 0 / 16
- **Per-pair failure class:**
  - OHRC_PAIR_01 → **F2** (no coarse recovery from the ±3 km lattice)
  - OHRC_PAIR_02 → **F3** (13 screen-passed → LoFTR but insufficient correspondence)
  - OHRC_PAIR_03 → **F3** (3 screen-passed → LoFTR but insufficient correspondence)
  - OHRC_PAIR_04 → **F2** (no coarse recovery from the ±3 km lattice)
- **Controls:**
  - C1 Negative → SCREEN_FAIL + 0 inliers ✔
  - C2 Synthetic Positive → SCREEN_PASS + 1867 inliers ✔
  - C3 Sensitivity → SCREEN_FAIL + 0 inliers (cross-modal gap indicator) ✔

### 10. Final Classification

```
Phase 24A Overall Classification:
    VERIFICATION_FAILED

Interpretation (CASE B → F3 transition):
    "Coarse structural evidence exists at some predefined placements,
     but reliable correspondence was not demonstrated through the
     frozen LoFTR quality gate and independent hold-out validation."

Phase 24 (original, REMAINS UNCHANGED):
    PHASE_24_STATUS         = DEFERRED_COMPUTATIONAL_COST
    PHASE_24_RESEARCH_RESULT = INCONCLUSIVE

Geodetic Status (PRESERVED UNCHANGED from Phase 23B):
    REFERENCE_PRODUCT_UNRESOLVED
    REFERENCE_GEODETIC_REALIZATION = UNKNOWN
    REFERENCE_TO_MOON_ME_DE421      = NOT_VERIFIED
    PHASE_23B_STATUS                = BLOCKED_PENDING_GEODETIC_REVIEW
```

### 11. Checksum & Integrity

After reproducing, verify with:

```
cd research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection
sha256sum -c checksums.sha256  # or equivalent
```

New Phase 24A hashes are appended to `checksums.sha256`; the historical Phase 23 hashes are **preserved unmodified**.

### 12. Interpretation Boundaries (Must Read)

- Do **NOT** overclaim:
  - No "reference product confirmed" / "geodetically correct" / "production ready" / "winner" / "best candidate" / "true alignment" — these are unsupported.
  - Candidate offsets are **not ranked**; multiple may SCREEN_PASS.
  - SCREEN_PASS ≠ registration; only F5 = research-level feasibility.
  - Phase 24A is a **prefilter**. Its classification is independent of Phase 24.
