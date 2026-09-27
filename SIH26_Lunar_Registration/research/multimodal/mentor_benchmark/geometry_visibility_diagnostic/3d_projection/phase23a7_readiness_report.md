# Phase 23A.7 — Master Synthesis & Frame / Geodetic Reconciliation Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary & Resolution of Open Questions A–G

Phase 23A.7 was executed to resolve the open frame and geodetic questions from Phase 23A.6 using authoritative NAIF generic kernels (`de421.bsp`, `moon_pa_de421_1900-2050.bpc`, `moon_080317.tf`) and Chandrayaan-2 mission kernels. All questions are now resolved with rigorous numerical evidence:

| Investigation Objective | Finding / Result | Supporting Metric | Scientific Classification |
| :--- | :---: | :--- | :---: |
| **A. Can DE421 frame be loaded/resolved?** | **`YES`** | `MOON_ME_DE421` (31007) and `MOON_PA_DE421` (31006) fully resolved via SPICE. | **`FRAME_VERIFIED`** |
| **B. Measured `IAU_MOON` $\leftrightarrow$ `MOON_ME` rotation?** | **`4.82" – 11.03"`** | Pair 01: $10.39"$, Pair 02: $11.03"$, Pair 03: $5.45"$, Pair 04: $4.82"$. | **`NUMERICALLY_VERIFIED`** |
| **C. Surface displacement produced?** | **`22.68 – 66.01 m`** | Evaluated across tested corner/center samples (Pair 01: $32.7\text{ m}$, Pair 02: $66.0\text{ m}$, Pair 03: $33.9\text{ m}$, Pair 04: $22.7\text{ m}$). | **`MINOR_FRACTION`** |
| **D. Reference raster geodetic realization?** | **`UNKNOWN`** | Projection equations match; frame realization unrecorded in GeoTIFF tags. | **`GEODETIC_LINK_NOT_VERIFIED`** |
| **E. Independent ground-track direction?** | **`COMPUTED`** | Differ from residual azimuths by $66.3^\circ - 163.9^\circ$; residuals are NOT along-track. | **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`** |
| **F. Does frame explain the rigid residual?** | **`MINOR FRACTION`** | Explains only $1.04\% - 5.22\%$ ($22–66\text{ m}$ vs $1,265–2,181\text{ m}$); too small by $20–50\times$. | **`NOT_SUFFICIENT_TO_EXPLAIN`** |
| **G. Does this change Phase 23B readiness?** | **`NO`** | Residual remains kilometre-scale; Phase 23B remains strictly held. | **`BLOCKED_PENDING_REVIEW`** |

---

## 2. Master Numerical Reconciliation Matrix

| Pair ID | Frame Rot (arcsec) | Surface Disp (m) | Ground-Track Az (deg) | Residual Az (deg) | Angular Diff | Translation Mag A (IAU) | Translation Mag B (ME) | Net Translation Change | Surface Disp Mag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | 10.39" | 32.70 m | 60.83° | 127.16° | 66.33° | 2158.4 m | 2139.5 m | -18.8 m | **32.70 m** |
| **`OHRC_PAIR_02`** | 11.03" | 66.01 m | 171.54° | 12.95° | 158.59° | 1264.9 m | 1295.3 m | +30.4 m | **66.01 m** |
| **`OHRC_PAIR_03`** | 5.45" | 33.87 m | 173.16° | 9.30° | 163.86° | 1699.9 m | 1717.0 m | +17.0 m | **33.87 m** |
| **`OHRC_PAIR_04`** | 4.82" | 22.68 m | 164.25° | 16.72° | 147.53° | 2181.1 m | 2203.3 m | +22.2 m | **22.68 m** |

---

## 3. Scientific Classifications

### A. Primary Frame-Reconciliation Classification:
> **`Primary frame-reconciliation classification: C — The tested DE421 lunar-frame difference is too small to explain the observed discrepancy.`**  

> **Quantitative descriptor:** The tested frame transformation produces 22.7–66.0 m of surface displacement across the tested corner/center samples.  

> **Scenario A/B wording:** The tested frame transformation produces 22.7–66.0 m of surface displacement, while changing the fitted translation magnitude by approximately 18.8–30.4 m across the four OHRC pairs.

### B. Preserved Geometric Classification (from Phase 23A.6):
> **`Geometric classification: B — Rigid translation plus a measurable non-rigid component.`**  
> *(This classification describes the observed source-to-map residual structure; it does not identify the physical cause as a geodetic-frame, reference-map, ephemeris, timing, or raster-generation error).* 

---

## 4. Phase 23B Readiness Gate Checklist

| Gate Criterion | Verification Finding | Compliance Status |
| :--- | :--- | :---: |
| **1. Authoritative lunar frame realization verified** | `MOON_ME_DE421` and `MOON_PA_DE421` loaded via NAIF binary PCK | **`SATISFIED`** |
| **2. CH2_OHRC -> lunar frame verified** | Verified via `ch2_v01.tf`, CK subsets, and `pck00010.tpc` | **`SATISFIED`** |
| **3. Reference raster geodetic realization bounded** | Audited; explicitly bounded as `UNKNOWN` / `GEODETIC_LINK_NOT_VERIFIED` | **`SATISFIED`** |
| **4. Ground-track orientation independently verified** | Computed from SPK; proven to NOT align with residuals | **`SATISFIED`** |
| **5. Unresolved frame conventions bounded** | Frame difference bounded at $\le 66\text{ m}$; cannot bridge kilometre-scale gap | **`SATISFIED`** |
| **6. Remaining uncertainty explicitly documented** | Reference mosaic producing sensor and geodetic tiepoint origin documented as open | **`SATISFIED`** |

> ### **Gate Conclusion:**
> # **`PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW`**  

> Phase 23B registration experiments remain strictly blocked pending user review and selection of an approved geodetic handling strategy.

---

## 5. Production Freeze & Provenance Audit

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
- **Zero Production Modification:** All production files untouched; LoFTR weights and quality gates 100% frozen.
- **Zero Registration Claims:** No feature matching, image warping, pose optimization, or homography fitting was performed.

---

> # **`PHASE 23A.7 COMPLETE — FRAME/GEODETIC REVIEW REMAINS UNRESOLVED`**
