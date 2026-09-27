# Phase 23A.7 — Independent Spacecraft Ground-Track Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

In earlier phases, sensitivity extrapolations were formulated as 1-D hypothetical equivalents under the label `REQUIRED-OFFSET MAGNITUDE`, but ground-track alignment was explicitly marked as `UNVERIFIED`. This audit computes the **exact physical ground-track direction** directly from the reconstructed Chandrayaan-2 SPK ephemeris and evaluates whether the observed residual translation vectors align with the spacecraft trajectory.

> ### **Ground-Track Alignment Finding:**
> # **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`**  
> The independently derived ground-track directions differ from the observed residual translation azimuths by **$66.33^\circ$ to $163.86^\circ$**.  
> The residual vectors are **NOT** aligned with the spacecraft flight path and must **NOT** be interpreted as along-track trajectory errors.

---

## 2. Spacecraft Trajectory & Ground-Track Azimuth Table

| Pair ID | Spacecraft Altitude | Ground Speed | Ground-Track Azimuth (IAU) | Ground-Track Azimuth (ME) | Residual Translation Azimuth | Angular Difference | Alignment Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | 100.77 km | 1543.95 m/s | **60.83°** | 60.83° | **127.16°** | **66.33°** | **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`** |
| **`OHRC_PAIR_02`** | 105.86 km | 1536.84 m/s | **171.54°** | 171.54° | **12.95°** | **158.59°** | **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`** |
| **`OHRC_PAIR_03`** | 97.88 km | 1551.44 m/s | **173.16°** | 173.16° | **9.30°** | **163.86°** | **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`** |
| **`OHRC_PAIR_04`** | 91.80 km | 1561.74 m/s | **164.25°** | 164.25° | **16.72°** | **147.53°** | **`GROUND_TRACK_ALIGNMENT_NOT_VERIFIED`** |

---

## 3. Physical & Methodological Implications

1. **Disproof of Along-Track Hypothesis:**
   - In Pairs 02, 03, and 04, the spacecraft moves south-southeast toward the lunar south pole with ground-track azimuths of $164^\circ - 173^\circ$.
   - The residual translation vectors point north-northeast with azimuths of $9^\circ - 17^\circ$.
   - The angular difference ($147.5^\circ - 163.9^\circ$) is nearly antiparallel, but significantly rotated away from pure opposite collinearity ($180^\circ$). In Pair 01, the angular difference is $66.33^\circ$ (cross-track dominant).
2. **De-coupling of Timing / Along-Track Errors:**
   - An along-track timing error of $\Delta t$ shifts the ground image strictly in the direction of motion (along the track).
   - Because the measured translation is rotated by up to $66^\circ$ from the track, a simple clock drift or along-track position shift **cannot** explain the 2D offset vector.
3. **Governance Rule Maintained:**
   - Track 7 sensitivity equivalent values remain purely hypothetical scalar metrics; they are definitively **not** true along-track orbital errors.
