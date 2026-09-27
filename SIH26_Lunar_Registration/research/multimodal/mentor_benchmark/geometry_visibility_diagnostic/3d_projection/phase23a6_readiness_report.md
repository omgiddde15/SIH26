# Phase 23A.6 — Master Synthesis & Frame/Geodetic Readiness Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.6 — Rigid Geodetic / Frame Offset Reconciliation  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary & Audit Objectives

Phase 23A.6 investigated whether the kilometre-scale source-to-map residuals ($pprox 1.2–2.2\text{ km}$) observed between the forward physical model and source metadata are consistent with a **rigid geodetic, reference-frame, or map-generation offset**.

---

## 2. Master Synthesis of Tracks 1–8

| Track | Evaluation Domain | Finding / Result | Key Numerical Metric |
| :--- | :--- | :---: | :--- |
| **Track 1** | Rigid Translation Test | **`PREDOMINANTLY RIGID`** | For Pairs 01, 02, and 04, the pure-translation model accounts for 98.16%–99.51% of the residual variance, with post-translation RMS residuals of 10.7–34.8 m. |
| **Track 2** | Similarity Model | **`MINIMAL DEFORMATION`** | Scale error is $< 322\text{ ppm}$ in Pairs 01, 02, 04; rotation $< 68\text{ arcsec}$. Pair 03 has $+3.15\%$ stretch. |
| **Track 3** | Affine Model | **`DESCRIPTIVE ONLY`** | Affine RMS $< 0.08\text{ m}$; note mandatory 2-DOF warning. |
| **Track 4** | Cross-Pair Comparison | **`AUDITED`** | The differing residual magnitudes for the two nominally co-located acquisitions (Pairs 02 and 03) are not consistent with a single static map-offset term being the sole explanation of the observed discrepancies. |
| **Track 5** | Reference Map Frame Audit | **`PROJECTION UNIFIED`** | Polar Stereographic ($R = 1,737.4\text{ km}$, $k_0 = 1.0$) verified; geodetic realization `UNKNOWN`. |
| **Track 6** | SPICE Frame Audit | **`NOT VERIFIED`** | The required DE421 MOON_ME realization is not available in the verified local kernel pool, so the IAU_MOON <-> MOON_ME angular difference was not independently computed in Phase 23A.6. Therefore no numerical bound on the resulting surface displacement is asserted here. |
| **Track 7** | Required Offset Sensitivity | **`1,261 – 2,174 m`** | 1-D along-track equivalent under Phase 23A.5 sensitivity labeled strictly as `REQUIRED-OFFSET MAGNITUDE` (along-track interpretation status: `UNVERIFIED`). |
| **Track 8** | Terrain Statement | **`VERIFIED RECORDED`** | *"The tested DEM correction changes the corner residuals only by metres, while the observed residuals are kilometre scale. Therefore the tested topographic correction does not explain the observed rigid source-to-map offset."* |

---

## 3. Answer to the Final Scientific Question

> ### **“Is the observed source-to-map discrepancy predominantly consistent with a rigid geodetic/frame/map offset?”**

### Quantitative Answer:
**Geometric classification: B — Rigid translation plus a measurable non-rigid component.**

This classification describes the observed source-to-map residual structure; it does not identify the physical cause as a geodetic-frame, reference-map, ephemeris, timing, or raster-generation error.

- **For Pairs 01, 02, and 04, the pure-translation model accounts for 98.16%–99.51% of the residual variance, with post-translation RMS residuals of 10.7–34.8 m.**
  - Across $23–25\text{ km}$ strips, post-translation RMS residuals are only **$10.72\text{ m}$** (`OHRC_PAIR_04`), **$23.25\text{ m}$** (`OHRC_PAIR_02`), and **$34.80\text{ m}$** (`OHRC_PAIR_01`).
  - Isotropic scale errors are minimal ($-96.4\text{ ppm}$ to $+21.9\text{ ppm}$).
- **Pair 03 exhibits a substantial anisotropic/non-rigid component. Its 3.15% similarity-scale discrepancy is numerically consistent with the difference between the reported flight-duration distance and delivered-raster along-track extent, but causal attribution to line timing or raster generation is not established in Phase 23A.6.**
- **The differing residual magnitudes for the two nominally co-located acquisitions (`OHRC_PAIR_02` and `OHRC_PAIR_03`, differing by $435.01\text{ m}$) are not consistent with a single static map-offset term being the sole explanation of the observed discrepancies.**
- **Pairs 02–04 have mutually similar residual-vector azimuths; their alignment with the spacecraft ground track is not independently established by the present report.**

---

## 4. Mandatory Governance & Production Safeguards

- **Production Canonical Freeze Set:**
  - `app/app.py`
  - `app/adaptive_adapter.py`
  - `app/registration_core.py`
  - `research/adaptive_matcher/adaptive_engine.py`
  - *(Canonical Production Engine Path: `research/adaptive_matcher/adaptive_engine.py`)*
  - *(Production Adapter Path: `app/adaptive_adapter.py`)*

- **Explicit Status of `app/adaptive_engine.py`:**
  - **`app/adaptive_engine.py = NOT PRESENT IN CANONICAL PROJECT`**
  - **Status:** **`NON-EXISTENT / NOT PART OF CANONICAL PROJECT`** (Not tracked in Git; not described as tracked, clean, or verified).

- **Production Integrity & Baseline Provenance Audit:**
  - **`PRODUCTION_BASELINE_PROVENANCE = NOT_INDEPENDENTLY_VERIFIED`**
  - *"The current Git snapshot verifies that the tracked production files have not changed since the snapshot commit, but it does not independently establish historical equivalence to the pre-Phase-23A.6 state."*
  - **Untracked File Audit (`git status --short --untracked-files=all`):** None of the canonical production files appear as untracked files.
  - **Canonical Production File Tracking & Hash Inventory:**
    - `app/app.py`: **TRACKED** | SHA-256 = `2a04c245f9d055cd4a747991757e77c8c5a94c1f2dbc090aadd5d4a834894467` (309,228 bytes, mtime: 2026-09-23 20:08:23).
    - `app/adaptive_adapter.py`: **TRACKED** | SHA-256 = `ab902b3c0e3d1e62a68b2612ee45fd5533e3b2c82feca37d2bd821eb8e9f1724` (22,954 bytes, mtime: 2026-09-20 17:38:43).
    - `app/registration_core.py`: **TRACKED** | SHA-256 = `d68e03161f38ce21621753e20e2ae699dcb9bb93cca789922214731a42ad06a5` (27,988 bytes, mtime: 2026-09-14 10:48:51).
    - `research/adaptive_matcher/adaptive_engine.py`: **TRACKED** | SHA-256 = `56047e8eef70e1feaafc1b80eed7a58fa8d6be7fd37ca43c43de2420480cf549` (70,967 bytes, mtime: 2026-09-22 22:58:43).
  - **Git Snapshot Diff Status:** `git diff --exit-code -- app/app.py app/adaptive_adapter.py app/registration_core.py research/adaptive_matcher/adaptive_engine.py` -> **`CLEAN`** (verifies zero modification since the baseline snapshot commit; no claim of historical equivalence to pre-23A.6 state is asserted).
- **Zero Production Modification:**
  - `app/app.py`: **UNTOUCHED**
  - `app/adaptive_adapter.py`: **UNTOUCHED**
  - `app/registration_core.py`: **UNTOUCHED**
  - `research/adaptive_matcher/adaptive_engine.py`: **UNTOUCHED**
  - Quality gates, thresholds, and LoFTR weights: **100% FROZEN**
- **Zero Registration Claims:** No feature matching, NCC alignment, homography fitting, or image warping was performed.
- **Distortion Caveat Maintained:** *'Optical distortion is not modeled; distortion uncertainty is unquantified.'*
- **Methodological Statement on Along-Track Sensitivity:**
  - *“These values are scalar equivalents obtained by applying the Phase 23A.5 along-track sensitivity coefficient to the observed translation magnitude. Because spacecraft ground-track alignment of the residual vectors was not independently established in Phase 23A.6, these values are not interpreted as actual spacecraft along-track position errors.”*

---

## 5. Phase 23B Gate Assessment

A predominantly rigid residual pattern demonstrates that the source swaths possess high internal geometric integrity, but does **not** automatically make Phase 23B ready. Phase 23B requires an approved geodetic handling strategy for resolving the rigid offset before orthorectification.

> # **`PHASE 23A.6 COMPLETE — AWAITING FRAME/GEODETIC REVIEW`**  

> *(Phase 23B remains strictly held pending user review).* 
