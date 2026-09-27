# Phase 23A.7 — Surface Displacement & Scenario Comparison Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This report quantifies the exact ground-surface displacement produced by the transformation from `IAU_MOON` to `MOON_ME_DE421` across the tested corner/center samples, and evaluates whether this frame shift accounts for the observed kilometre-scale residuals.

> ### **Primary Finding:**
> **Primary frame-reconciliation classification:** **`C — The tested DE421 lunar-frame difference is too small to explain the observed discrepancy.`**  

> **Quantitative descriptor:** The tested frame transformation produces **$22.68\text{ m}$ to $66.01\text{ m}$** of surface displacement across the tested corner/center samples.  

> **Scenario A/B wording:** The tested frame transformation produces 22.7–66.0 m of surface displacement, while changing the fitted translation magnitude by approximately 18.8–30.4 m across the four OHRC pairs.

---

## 2. Surface-Coordinate Displacement per Pair

Displacement on the lunar reference sphere ($R = 1,737,400.0\text{ m}$) evaluated across the tested corner/center samples (4 corners plus swath center):

| Pair ID | Rotation Angle | Min Disp (m) | Max Disp (m) | Mean Disp (m) | RMS Disp (m) | Mean Displacement Vector $(dx, dy)$ | Disp Azimuth |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | 10.39" | 32.22 m | 33.18 m | **32.70 m** | **32.70 m** | `(-31.21, -9.75) m` | **252.64°** |
| **`OHRC_PAIR_02`** | 11.03" | 65.59 m | 66.42 m | **66.00 m** | **66.00 m** | `(-51.26, +41.58) m` | **309.04°** |
| **`OHRC_PAIR_03`** | 5.45" | 33.66 m | 34.07 m | **33.86 m** | **33.86 m** | `(-26.33, +21.29) m` | **308.96°** |
| **`OHRC_PAIR_04`** | 4.82" | 22.60 m | 22.75 m | **22.67 m** | **22.67 m** | `(+10.66, +20.02) m` | **28.03°** |

---

## 3. Frame-Corrected Scenario Test (Scenario A vs. Scenario B)

- **Scenario A:** Forward physical projection in `IAU_MOON` frame (Phase 23A baseline).
- **Scenario B:** Forward physical projection rotated to `MOON_ME_DE421` frame before map projection.

| Pair ID | Scenario A Translation | Scenario A Azimuth | Scenario A RMS | Scenario B Translation | Scenario B Azimuth | Scenario B RMS | Net Translation Change | Surface Disp Mag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | **2158.4 m** | 127.16° | 34.80 m | **2139.5 m** | 127.87° | 34.79 m | **-18.8 m** | **32.70 m** |
| **`OHRC_PAIR_02`** | **1264.9 m** | 12.95° | 23.25 m | **1295.3 m** | 10.33° | 23.34 m | **+30.4 m** | **66.01 m** |
| **`OHRC_PAIR_03`** | **1699.9 m** | 9.30° | 409.32 m | **1717.0 m** | 8.32° | 409.32 m | **+17.0 m** | **33.87 m** |
| **`OHRC_PAIR_04`** | **2181.1 m** | 16.72° | 10.72 m | **2203.3 m** | 16.83° | 10.65 m | **+22.2 m** | **22.68 m** |

---

## 4. Detailed Physical Interpretation

1. **Internal Rigidity Across Tested Points:** The differential variation of surface displacement across the tested corner/center samples of each strip is less than $1.0\text{ m}$ (e.g. $65.59\text{ m}$ to $66.42\text{ m}$ in Pair 02). Thus, the frame transformation acts as a nearly pure rigid spatial translation over the tested points.
2. **Vector Direction Decoupling:** In Pairs 02, 03, and 04, the frame displacement vector points in azimuths of $\sim 309^\circ$ and $28^\circ$, whereas the observed translation vectors point in azimuths of $9^\circ - 17^\circ$. Because the frame displacement is partially aligned with the observed translation, rotating into `MOON_ME_DE421` actually *increases* the net translation magnitude slightly (by $+17\text{ m}$ to $+30\text{ m}$).
3. **Order of Magnitude Bound:** Frame realization differences between `IAU_MOON` and `MOON_ME_DE421` are bounded at $\le 66\text{ m}$. They are fundamentally unable to account for the $\sim 1.2–2.2\text{ km}$ offset.
4. **Scenario A/B Effect Summary:** The tested frame transformation produces 22.7–66.0 m of surface displacement, while changing the fitted translation magnitude by approximately 18.8–30.4 m across the four OHRC pairs.
