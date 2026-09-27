# 07 — Phase 24A Summary: Cheap Deterministic Coarse Prefilter

## 7.1 Why Phase 24A Exists

**Original Phase 24 plan (DEFERRED due to cost):** Brute-force 676-candidate (26×26) LoFTR search over ±3 km image-space. Computationally infeasible on this hardware (estimated 40+ min × 4 pairs = 2.5+ hours).

**Phase 24A replacement (EXECUTED):** A cheap deterministic coarse prefilter to answer:
> *"Can a cheap deterministic structural prefilter identify a small set of image-space placement hypotheses that are worth expensive LoFTR verification?"*

Phase 24A is **candidate-window screening only** — it is NOT registration, NOT geolocation, NOT geodetic correction, and NOT reference-product identification.

## 7.2 Predeclared Lattice (Immutable, 196 Hypotheses)

### Lattice Definition (fixed before any evaluation)

```
dx, dy  ∈  { -3000, -2000, -1000, 0, 1000, 2000, 3000 }  metres
            ⇓  (5 m / reference px; dv_px = -dv_m / 5 sign convention)
du_px, dv_px  ∈  { -600, -400, -200, 0, 200, 400, 600 }  pixels
```

- **Per pair:** 7 × 7 = **49** offset hypotheses → exactly 49 (not 48, not 50)
- **4 pairs (OHRC 01–04):** **49 × 4 = 196 coarse candidates total**
- **Search center:** Audited Phase 23 nominal reference footprint (from physical ray-DEM projection).
- **IMPORTANT DISCIPLINE:** Phase 23A.6 fitted rigid translations were **not** used to move the search center or choose candidates. They are reported alongside each row **for comparison only.**

## 7.3 Cheap Diagnostics (Per 3×3 Source Window)

For every candidate offset, 9 deterministic 3×3 local windows were evaluated:

| ID | Diagnostic | Predeclared Threshold |
|:---|:---|:---|
| A | Intensity ZMUV NCC | `T_INT = 0.08` |
| B | Sobel gradient-magnitude NCC | `T_GRAD = 0.06` |
| C | Hann-windowed phase-correlation response | `T_PHASE = 0.05` |
| D | FAST keypoints → 15×15 ZMUV descriptor → BFM knn Lowe 0.80 ratio | `T_FAST_WIN = 3 / win; T_FAST_ANY = 4 (any window)` |

**SCREEN_PASS rule (all 5 conditions, predeclared — NOT tuned after results):**
1. C1 — ≥ 3 valid local supported windows
2. C2 — ≥ 3 distinct 3×3 spatial cells
3. C3 — finite phase-correlation response
4. C4 — structural strength criterion met
5. C5 — no invalidating missing-support condition

Otherwise: `SCREEN_FAIL` or `INSUFFICIENT_SUPPORT` (F1 proxy).

## 7.4 Controls (Declared Before Evaluation)

| ID | Kind | Cheap Decision | LoFTR n_inliers | Expected | Observed |
|:---|:---|:---|---:|:---|:---|
| C1 | Negative (non-overlap crop) | SCREEN_FAIL | 0 | MINIMAL_INLIERS | AS_EXPECTED_NEGATIVE ✅ |
| C2 | Positive synthetic (R=2°, tx=10, ty=10) | SCREEN_PASS | **1867** | SUBSTANTIAL_INLIERS | AS_EXPECTED_POSITIVE ✅ |
| C3 | Sensitivity (Pair 02 nominal) | SCREEN_FAIL | 0 | INDICATOR | n_cand=0 — cross-modal domain gap |

Sanity confirmed: the control subsystem operates as designed.

## 7.5 Aggregate Results (196 / 196 Evaluated)

| Metric | Count |
|:---|---:|
| Total coarse candidates | **196** ✅ |
| SCREEN_PASS | **16** |
| SCREEN_FAIL | **171** |
| INSUFFICIENT_SUPPORT (F1) | **9** |
| LoFTR verification runs (SCREEN_PASS only) | **16** |
| LoFTR runs on SCREEN_FAIL candidates | **0** ✅ |
| Initial QG passes (n_cand≥10 ∧ n_inl≥8 ∧ ratio≥20%) | **0** |
| Full QG + 5-seed hold-out (F5 — research-validated) | **0** |

### Per-Pair Breakdown

| Pair | Coarse | SCREEN_PASS | LoFTR | Initial QG | Full QG | F5 | Failure Class |
|:---|---:|---:|---:|---:|---:|---:|:---|
| OHRC_PAIR_01 | 49 | 0 | 0 | 0 | 0 | 0 | **F2** |
| OHRC_PAIR_02 | 49 | **13** | 13 | 0 | 0 | 0 | **F3** |
| OHRC_PAIR_03 | 49 | **3** | 3 | 0 | 0 | 0 | **F3** |
| OHRC_PAIR_04 | 49 | 0 | 0 | 0 | 0 | 0 | **F2** |

### Failure Classes

| ID | Meaning | Hit Count |
|:---|:---|---:|
| F1 | Insufficient reference support | 9 individual candidates |
| F2 | No coarse structural recovery from the ±3 km lattice | 2 pairs (01, 04) |
| F3 | Coarse structure exists but LoFTR correspondence insufficient | 2 pairs (02, 03) |
| F4 | Initial passes; hold-out fails | 0 |
| F5 | Research-validated candidate exists | 0 |

## 7.6 Overall Phase 24A Classification

```
VERIFICATION_FAILED

Interpretation:
    Coarse structural evidence exists at some predefined placements
    (OHRC_PAIR_02: 13 offsets; OHRC_PAIR_03: 3 offsets), but reliable
    correspondence / geometric consistency was not demonstrated through
    the frozen LoFTR quality gate and independent hold-out validation.
```

**Honest slide quote (PPT §12):**
> *"Coarse image-space placement uncertainty alone did not yield validated registration under the tested ±3 km hypotheses."*

**DO NOT say:**
- ❌ "All translations ruled out" (we only tested the 196 predeclared lattice points, not the continuous plane)
- ❌ "Phase 24 failed" (Phase 24 remains **DEFERRED_COMPUTATIONAL_COST / INCONCLUSIVE**)

## 7.7 Phase Status Discipline (Unchanged)

```
Phase 24 (original, untouched):
  PHASE_24_STATUS          = DEFERRED_COMPUTATIONAL_COST
  PHASE_24_RESEARCH_RESULT = INCONCLUSIVE

Phase 24A (this experiment):
  Classification = VERIFICATION_FAILED

Phase 23B (geodetic status, preserved verbatim):
  REFERENCE_PRODUCT_UNRESOLVED
  REFERENCE_GEODETIC_REALIZATION = UNKNOWN
  REFERENCE_TO_MOON_ME_DE421      = NOT_VERIFIED
  PHASE_23B_STATUS                = BLOCKED_PENDING_GEODETIC_REVIEW
```

## 7.8 Runtime

- Total experiment runtime: **387.55 s (≈ 6.5 min)**
- Average: ~2 s / coarse candidate; LoFTR adds ~20–30 s / SCREEN_PASS.
- LoFTR model loaded **once per process.**
- SCREEN_FAIL candidates correctly skipped LoFTR.
- Resumable checkpoint mechanism: `phase24a_checkpoint.json` per candidate key `PAIR__dxNm_dyNm`.

## 7.9 Source Evidence Files

| File | Path |
|:---|:---|
| Experiment driver | [run_phase24a_coarse_localization.py](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/run_phase24a_coarse_localization.py) |
| Report | [phase24a_coarse_localization_report.md](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_coarse_localization_report.md) |
| Failure drill-down | [phase24a_failure_classification.md](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_failure_classification.md) |
| Screen CSV (196 rows) | [phase24a_screen_candidates.csv](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_screen_candidates.csv) |
| LoFTR CSV (16 rows) | [phase24a_loftr_verification.csv](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_loftr_verification.csv) |
| Pair summary CSV (4 rows) | [phase24a_pair_summary.csv](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_pair_summary.csv) |
| Resumable checkpoint | [phase24a_checkpoint.json](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_projection/phase24a_checkpoint.json) |
