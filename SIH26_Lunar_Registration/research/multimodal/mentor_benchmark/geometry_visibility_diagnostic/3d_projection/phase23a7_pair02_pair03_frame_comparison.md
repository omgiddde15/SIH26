# Phase 23A.7 — Pair 02 vs. Pair 03 Controlled Frame Test Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

Benchmark acquisitions `OHRC_PAIR_02` (acquired Feb 8, 2025) and `OHRC_PAIR_03` (acquired Mar 8, 2025) target nominally co-located lunar terrain near $84.95^\circ\text{S}, 26^\circ\text{E}$. However, Phase 23A.6 showed that their observed residual translations differ by **$435.01\text{ meters}$** ($1,264.93\text{ m}$ vs $1,699.94\text{ m}$).

This controlled test evaluates whether the time-dependent frame rotation between `IAU_MOON` and `MOON_ME_DE421` accounts for this cross-pair variation.

> ### **Evaluation Finding:**
> # **`NOT_SUFFICIENT_TO_EXPLAIN`**  
> The measured difference in frame surface displacement between the two acquisitions is **$32.14\text{ meters}$**, which accounts for only **$7.39\%$** of the observed $435.01\text{ m}$ discrepancy.

---

## 2. Comparative Numerical Matrix

| Evaluation Metric | `OHRC_PAIR_02` (Feb 8, 2025) | `OHRC_PAIR_03` (Mar 8, 2025) | Differential (Δ) | Frame Attribution Fraction |
| :--- | :---: | :---: | :---: | :---: |
| **`IAU_MOON` $\leftrightarrow$ `MOON_ME` Rotation** | 11.03" | 5.45" | **5.58"** | N/A |
| **Surface Displacement Magnitude** | 66.01 m | 33.87 m | **32.14 m** | N/A |
| **Observed Translation Magnitude** | 1264.93 m | 1699.94 m | **435.01 m** | **7.39%** |
| **Residual Azimuth** | 12.95° | 9.30° | **3.65°** | Mutually similar |
| **Non-Rigid Component** | Minimal ($s = 0.9997$) | Substantial ($s = 1.0315$) | **$+3.15\%$ stretch** | Unexplained by frame |

---

## 3. Scientific Synthesis

1. **Minor Role of Frame Realization:** While the frame rotation changes by $5.58"$ between the two epochs (altering ground displacement from $66.0\text{ m}$ down to $33.9\text{ m}$), this $32.1\text{ m}$ shift is an order of magnitude smaller than the $435.0\text{ m}$ translation difference.
2. **Pair 03 Anisotropy Unaffected:** The $+3.15\%$ along-track scale stretch in Pair 03 remains completely unaffected by frame transformation, confirming that it represents an internal sensor timing or delivered-raster geometric characteristic, rather than an external planetary frame phenomenon.
3. **Conclusion:** Frame realization shifts do **not** explain the cross-pair variance.
