# Phase 22.5 — SPICE Physical Frame Chain Verification Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.5 — Binary Input Ingestion & Physical Coverage Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report documents the end-to-end verification of the SPICE physical frame transformation chain required to map 3D pixel look-vectors from the OHRC detector array into the selenographic coordinate frame of the Moon.

### Explicit Determination:
- **Frame Chain Verification:** **PASS** across all four mentor OHRC pairs (`OHRC_PAIR_01` to `OHRC_PAIR_04`).
- **Missing Frame Dependencies:** **NONE**. All required intermediate reference frames and kernel links exist and resolve.
- **Time Conversion Accuracy:** **PASS**. UTC epochs convert deterministically to Ephemeris Time (ET) and Spacecraft Clock ticks (SCLK) without error.

---

## 2. Frame Architecture & NAIF ID Hierarchy

```
                             [1] "J2000"
                          (Inertial Base Frame)
                               /         \
                              /           \
     [PCK: pck00010.tpc]     /             \     [CK: ch2_att_pair0X_subset.bc]
     (Planetary Rotation)   /               \    (Orbiter Attitude Quaternions)
                           v                 v
                 [10020] "IAU_MOON"    [-152001] "CH2_ORBITER"
                 (Lunar Body-Fixed)     (Spacecraft Mechanical Frame)
                                                 |
                                                 | [FK: ch2_v01.tf]
                                                 | (Fixed Alignment)
                                                 v
                                        [-152270] "CH2_OHRC"
                                        (Optical Sensor Frame)
```

| Frame Name | NAIF ID | Frame Class | Center Body ID | Defining Kernel | Definition / Purpose |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`J2000`** | `1` | Inertial (Class 1) | `0` (Solar System Barycenter) | SPICE Built-in | Universal celestial inertial reference frame. |
| **`IAU_MOON`** | `10020` | PCK (Class 2) | `301` (Moon) | `pck00010.tpc` | Standard body-fixed rotating coordinate system for the Moon. |
| **`CH2_ORBITER`** | `-152001` | CK (Class 3) | `-152` (CH2 Orbiter) | `ch2_v01.tf` & CK | Spacecraft dynamic attitude frame (derived from star tracker/gyros). |
| **`CH2_OHRC`** | `-152270` | Fixed (Class 4) | `-152` (CH2 Orbiter) | `ch2_v01.tf` | High-Resolution Camera optical frame ($+X$ along boresight). |

---

## 3. Forensic Frame Transformation Path Audit

Every link in the mathematical transformation path was tested programmatically in Python using CSPICE (`spiceypy`):

### Link 1: Sensor Frame to Spacecraft Frame (`CH2_OHRC` -> `CH2_ORBITER`)
- Evaluated via: `sp.pxform('CH2_ORBITER', 'CH2_OHRC', et)`
- Result:
  $$\mathbf{R}_{\text{CH2\_ORBITER} \to \text{CH2\_OHRC}} = \begin{bmatrix} 1.0 & 0.0 & 0.0 \\ 0.0 & 1.0 & 0.0 \\ 0.0 & 0.0 & 1.0 \end{bmatrix}$$
- Analysis: `CH2_OHRC` optical axes are mechanically aligned with `CH2_ORBITER` structural axes. Zero misalignment or uncalibrated mounting bias is encoded in the official Frame Kernel `ch2_v01.tf`.

### Link 2: Spacecraft Frame to Inertial Frame (`CH2_ORBITER` -> `J2000`)
- Evaluated via: `sp.pxform('CH2_ORBITER', 'J2000', et)`
- Defining Kernel: `ch2_att_pair0X_subset.bc` (Type 3 continuous quaternion interpolation).
- Evaluability: Tested at 0%, 25%, 50%, 75%, and 100% of each OHRC acquisition duration.
- Result: Evaluates deterministically with zero interpolation gaps across all passes.

### Link 3: Inertial Frame to Lunar Body-Fixed Frame (`J2000` -> `IAU_MOON`)
- Evaluated via: `sp.pxform('J2000', 'IAU_MOON', et)`
- Defining Kernel: `pck00010.tpc` (Planetary Constants Kernel).
- Result: Evaluates smoothly as a function of ephemeris time, tracking lunar rotation and pole orientation.

### Composite Transformation: Optical Look-Vector to Lunar Ground Ray
For any pixel look-vector $\vec{v}_{\text{inst}} = [v_x, v_y, v_z]^T$ in `CH2_OHRC`:
$$\vec{v}_{\text{moon}}(t) = \mathbf{R}_{J2000 \to \text{IAU\_MOON}}(t) \cdot \mathbf{R}_{\text{CH2\_ORBITER} \to J2000}(t) \cdot \vec{v}_{\text{inst}}$$
The unit look-vector is fully evaluable at any scanline epoch $t_i$.

---

## 4. Frame Chain Test Results Summary

| Pair ID | Acquisition Epoch (UTC) | Intermediate Frames Evaluated | Look-Vector in `IAU_MOON` | Status |
| :--- | :--- | :--- | :--- | :---: |
| **`OHRC_PAIR_01`** | 2024-12-07T12:21:32 to 12:21:48 | `CH2_OHRC` -> `CH2_ORBITER` -> `J2000` -> `IAU_MOON` | $[+0.2034, -0.1681, +0.9646]$ to $[+0.2102, -0.1803, +0.9609]$ | **PASS** |
| **`OHRC_PAIR_02`** | 2025-02-08T14:02:45 to 14:03:02 | `CH2_OHRC` -> `CH2_ORBITER` -> `J2000` -> `IAU_MOON` | $[+0.1663, -0.0287, +0.9857]$ to $[+0.1522, -0.0309, +0.9879]$ | **PASS** |
| **`OHRC_PAIR_03`** | 2025-03-08T01:27:52 to 01:28:09 | `CH2_OHRC` -> `CH2_ORBITER` -> `J2000` -> `IAU_MOON` | $[+0.1982, -0.0007, +0.9802]$ to $[+0.1835, -0.0025, +0.9830]$ | **PASS** |
| **`OHRC_PAIR_04`** | 2025-10-12T04:58:21 to 04:58:37 | `CH2_OHRC` -> `CH2_ORBITER` -> `J2000` -> `IAU_MOON` | $[+0.3276, -0.0305, +0.9443]$ to $[+0.3142, -0.0345, +0.9487]$ | **PASS** |

---

## 5. Technical Verdict

The complete physical frame chain from the OHRC detector array to the lunar body-fixed coordinate system is verified, evaluable, and free of missing dependencies.
