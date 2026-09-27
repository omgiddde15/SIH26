# Phase 24A — Coarse Deterministic Image-Space Prefilter Report

**Generated:** 2026-09-24T15:06:12.284045  
**Total Runtime:** 387.55 s (6.5 min)  
**Governing Discipline:** RESEARCH-ONLY — Production Code FROZEN  

---

## 1. Governance Constants (PRESERVED UNCHANGED)

- `REFERENCE_PRODUCT_UNRESOLVED` = True
- `REFERENCE_GEODETIC_REALIZATION` = UNKNOWN
- `REFERENCE_TO_MOON_ME_DE421` = NOT_VERIFIED
- `PHASE_23B_STATUS` = BLOCKED_PENDING_GEODETIC_REVIEW
- `PHASE_24_STATUS` (original, unchanged) = DEFERRED_COMPUTATIONAL_COST
- `PHASE_24_RESEARCH_RESULT` (original, unchanged) = INCONCLUSIVE

## 2. Predeclared Experimental Design

- Coarse offset lattice (metres): `[-3000, -2000, -1000, 0, 1000, 2000, 3000]`
- 7 × 7 = 49 offsets per pair × 4 pairs = **196 coarse candidates**
- Reference scale: 5 m / reference pixel → pixel offsets `{-600,-400,-200,0,200,400,600}` px
- Local framework: 3×3 deterministic source windows, 128×128 px each
- Search center: Nominal reference footprint from audited Phase 23 physical projection (NOT moved by Phase 23A.6 translations)

### 2.1 Predeclared Screening Thresholds (FIXED)

- `T_INT_NCC_MIN` = 0.08
- `T_GRAD_NCC_MIN` = 0.06
- `T_PHASE_RESP_MIN` = 0.05
- `T_FAST_N_MIN` = 3
- `T_VALID_WINDOWS_MIN` = 3
- `T_SPATIAL_CELLS_MIN` = 3
- `T_FAST_ANY_CANDIDATES` = 4
- Thresholds fixed PRE-DECLARATION before evaluation. No tuning performed.

### 2.2 Frozen Quality Gate (UNCHANGED)

- `min_candidates` = 10
- `min_initial_inliers` = 8
- `min_inlier_ratio` = 0.2
- `min_occupancy` = 0.33
- `ransac_threshold` = 3.0
- `downstream_min_inliers` = 4
- `grid` = 3x3
- `max_per_cell` = 6
- `validation_seeds` = (1, 2, 3, 4, 5)

## 3. Controls Summary

### 3.1 CONTROL_1
- **Description:** Known negative: non-overlapping top-left 512x512 corner of Pair 01 reference
- **Cheap Decision:** `SCREEN_FAIL`
- **Supported Windows / Cells:** 2 / 2
- **LoFTR n_candidates / n_inliers:** 0 / 0
- **Expected:** SCREEN_FAIL_OR_MINIMAL_INLIERS
- **Observed:** AS_EXPECTED_NEGATIVE

### 3.2 CONTROL_2
- **Description:** Synthetic known-transform pair (rotation=2.0°, tx=10px, ty=10px)
- **Cheap Decision:** `SCREEN_PASS`
- **Supported Windows / Cells:** 9 / 9
- **LoFTR n_candidates / n_inliers:** 1867 / 1867
- **Expected:** SCREEN_PASS_AND_SUBSTANTIAL_INLIERS
- **Observed:** AS_EXPECTED_POSITIVE

### 3.3 CONTROL_3
- **Description:** Same-sensor Pair 02 nominal crop at (dx=0, dy=0) — known overlap via Phase 23A.9
- **Cheap Decision:** `SCREEN_FAIL`
- **Supported Windows / Cells:** 3 / 3
- **LoFTR n_candidates / n_inliers:** 0 / 0
- **Expected:** INDICATOR_OF_MATCHER_SENSITIVITY
- **Observed:** n_candidates=0, n_inliers=0

## 4. Aggregate Counts

- Total coarse candidates generated: **196**
- `SCREEN_PASS`: **16**
- `SCREEN_FAIL`: 171
- `INSUFFICIENT_SUPPORT`: 9
- LoFTR verification runs (SCREEN_PASS only): **16**
- Initial quality-gate passes (n_cand≥10 ∧ n_inl≥8 ∧ ratio≥0.20): 0
- Full quality-gate passes (incl. occupancy ≥0.33, final ≥4, held-out): 0
- Hold-out validation passes: 0
- Research-validated F5 candidates: **0**

### 4.1 Per-Pair Summary

| Pair | Coarse | SCREEN_PASS | LoFTR | Initial QG | Full QG | F5 | Failure Class |
|:---|---:|---:|---:|---:|---:|---:|:---|
| OHRC_PAIR_01 | 49 | 0 | 0 | 0 | 0 | 0 | F2 |
| OHRC_PAIR_02 | 49 | 13 | 13 | 0 | 0 | 0 | F3 |
| OHRC_PAIR_03 | 49 | 3 | 3 | 0 | 0 | 0 | F3 |
| OHRC_PAIR_04 | 49 | 0 | 0 | 0 | 0 | 0 | F2 |

## 5. Phase 24A Overall Classification

**`VERIFICATION_FAILED`**

Coarse structural evidence exists at some predefined placements, but reliable correspondence / geometric consistency was not demonstrated through the frozen LoFTR quality gate and hold-out validation.

---

## 6. Interpretation Boundaries (IMPORTANT)

- This phase is **candidate-window screening only**. It is NOT registration, NOT geolocation, NOT geodetic correction, NOT reference-product identification.
- No ranking of candidate offsets is asserted. Multiple candidates may be `SCREEN_PASS`.
- `SCREEN_PASS` alone is NOT a registration. Only `F5 = full frozen QG + independent hold-out` constitutes research-level relative-registration feasibility.
- Phase 24 overall remains **DEFERRED_COMPUTATIONAL_COST / INCONCLUSIVE**.
- Geodetic status of the reference product remains **UNRESOLVED / UNKNOWN / NOT_VERIFIED**.
