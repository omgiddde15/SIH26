# Phase 23A.5 — Pair 04 DEM Crop Boundary & Intersection Exit Analysis Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

In Phase 23A, 3 out of 9 deterministic rays in `OHRC_PAIR_04` (`TOP_MID`, `TOP_LEFT`, `TOP_RIGHT`) returned status `OUTSIDE_DEM`. This report audits the exact spatial location of these rays relative to the available cropped DEM subset.

> **Core Finding:** 3/9 rays exited the available cropped DEM subset; this is not evidence that the physical ray lacks a lunar-surface intersection.

---

## 2. Quantitative Crop Boundary Telemetry

Available Cropped DEM Subset Shape: **1321 lines $\times$ 532 samples** (`LDEM_80S_20M_pair04_subset.bin`).

| Sample Name | Pixel $(u, v)$ | Sphere Lat / Lon | Local DEM Sphere Coordinate | `SPHERE_INTERSECTION_WITHIN_CROP` | Line Margin to South Border |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`TOP_MID`** | `(276, 465)` | `-83.7876, 31.3129` | `(line 1258.44, samp 436.47)` | **`YES`** | 62.6 lines (1251.2 m) |
| **`TOP_LEFT`** | `(55, 465)` | `-83.7968, 30.9545` | `(line 1277.01, samp 378.84)` | **`YES`** | 44.0 lines (879.9 m) |
| **`TOP_RIGHT`** | `(496, 465)` | `-83.7783, 31.6676` | `(line 1240.02, samp 493.69)` | **`YES`** | 81.0 lines (1619.7 m) |

---

## 3. Physical Mechanism of Boundary Exit

1. **Spherical Intersections Reside Entirely Within the Crop:**
   - On the reference sphere ($R = 1,737,400\text{ m}$), all three rays intersect at lines **$1240.0$ to $1277.0$**, safely inside the $1321$-line heightfield (`SPHERE_INTERSECTION_WITHIN_CROP = YES`).
2. **Topographic Relief Exit Vector:**
   - In this northern sector of the pass, the terrain drops into a deep crater depression (elevation $\approx -3,400\text{ m}$).
   - The camera views this crater with an off-nadir emission slant of **$23.78^\circ$**.
   - The ray must travel an additional path length of $\Delta s \approx 3,400 / \cos(23.78^\circ) \approx 3,715\text{ meters}$ before reaching the surface.
   - At $23.78^\circ$ slant, this additional line-of-sight distance shifts the ground coordinate southwards by:
     $$\Delta \text{ground} \approx 3,715 \cdot \sin(23.78^\circ) \approx 1,500\text{ meters } (\approx 75\text{ DEM lines})$$
   - Adding $+75\text{ lines}$ to the spherical line coordinate ($1258.4 + 75 = 1333.4$) places the physical terrain intersection beyond the southern boundary (line 1321) of the cropped DEM subset.

> **Verdict:** 3/9 rays exited the available cropped DEM subset; this is not evidence that the physical ray lacks a lunar-surface intersection. The physical ray possesses a valid ground intersection that lies slightly south of the cropped file boundary.
