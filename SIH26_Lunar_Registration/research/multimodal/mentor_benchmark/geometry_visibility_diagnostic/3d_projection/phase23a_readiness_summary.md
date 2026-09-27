# Phase 23A — Synthesis & Final Readiness Summary

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A — OHRC Physical Projection Sanity Test  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  
**Phase 23B Recommendation:** **`AWAITING GEOMETRY REVIEW`**  

---

## 1. Synthesis of Phase 23A Objectives & Results

Phase 23A executed the first rigorous physical sensor-to-ground projection experiment for Chandrayaan-2 OHRC across all four mentor benchmark pairs (`OHRC_PAIR_01` to `OHRC_PAIR_04`).

| Audit Question | Finding | Technical Evidence |
| :--- | :---: | :--- |
| **1. Are source rays physically well-defined?** | **YES** | Official IK focal length ($2080.0\text{ mm}$), verified FK co-alignment, audited 12K array sample mapping ($u_{\text{center}} = s_x(u+0.5)$), and exposure-centered line timing produce stable look vectors. |
| **2. Are DEM intersections stable?** | **YES** | **33 / 36 rays (91.7%)** successfully intersected the LOLA DEM with zero numerical divergences. In Pair 04, 3/9 rays exited the available cropped DEM subset; this is not evidence that the physical ray lacks a lunar-surface intersection. |
| **3. Does terrain relief materially alter projection?** | **YES** | Topography displaces 3D surface points by **up to 4,580 meters** and horizontal ground coordinates by **180 m to 1,450 m** relative to a reference sphere. |
| **4. Does 5m vs 20m DEM materially affect positions?** | **NO** | In Pair 01, 5m vs 20m DEM intersection differs by only **0.11 m** horizontally (0.02x pixel scale). |
| **5. Is source-to-reference map geometry self-consistent?** | **YES** | 100% of successful projections fell within reference-raster bounds; bounds containment is not a geolocation validation. |
| **6. What geolocation residuals exist?** | **~1.9 – 3.6 km** | The source-to-map residual is currently unexplained and may contain contributions from ephemeris, attitude, timing, raster geometry, projection convention, DEM datum, and mentor map geolocation. |

---

## 2. Phase 23A Readiness Decision Matrix

| Pair ID | Ray Definition | DEM Intersections | Sphere vs DEM Relief | 5m vs 20m Sensitivity | Map Canvas Overlay | Phase 23A Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | **PASS** | **9 / 9 (100%)** | $\Delta = 983\text{ m}$ | $\Delta = 0.11\text{ m}$ (Quantified) | **100% IN-BOUNDS** | **PASS** |
| **`OHRC_PAIR_02`** | **PASS** | **9 / 9 (100%)** | $\Delta = 4,580\text{ m}$ | N/A (North of 87.5°S) | **100% IN-BOUNDS** | **PASS** |
| **`OHRC_PAIR_03`** | **PASS** | **9 / 9 (100%)** | $\Delta = 4,004\text{ m}$ | N/A (North of 87.5°S) | **100% IN-BOUNDS** | **PASS** |
| **`OHRC_PAIR_04`** | **PASS** | **6 / 9 (66.7%)** | $\Delta = 3,760\text{ m}$ | N/A (North of 87.5°S) | **100% IN-BOUNDS** | **PASS** |

---

## 3. Mandatory Governance & Production Safeguards

- **Zero Production Modification:**
  - `app/adaptive_engine.py`: **UNTOUCHED**
  - `app/registration_core.py`: **UNTOUCHED**
  - `app/app.py`: **UNTOUCHED**
  - `research/adaptive_matcher/adaptive_engine.py`: **UNTOUCHED**
  - Quality gates, thresholds, and LoFTR weights: **100% FROZEN**
- **Zero Registration Claims:** No feature matching, NCC alignment, or homography fitting was performed.
- **Distortion Caveat Maintained:** *'Optical distortion is not modeled; distortion uncertainty is unquantified.'*

---

## 4. Phase 23B Gate Status

> # **`PHASE 23A COMPLETE — AWAITING GEOMETRY REVIEW`**  
> *(Phase 23B is NOT automatically started; strictly held pending user review).*
