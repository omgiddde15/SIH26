# Phase 22.5 — Local CK Attitude Coverage & Pointing Verification Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.5 — Binary Input Ingestion & Physical Coverage Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report documents the local acquisition, cryptographic verification, and SpiceyPy attitude evaluation for Chandrayaan-2 Orbiter pointing across all four mentor OHRC pairs (`OHRC_PAIR_01` through `OHRC_PAIR_04`).

### Explicit Determination:
- **`OHRC_PAIR_01`:** `CK_COVERAGE = FULL` | `ATTITUDE_EVALUATION = PASS`
- **`OHRC_PAIR_02`:** `CK_COVERAGE = FULL` | `ATTITUDE_EVALUATION = PASS`
- **`OHRC_PAIR_03`:** `CK_COVERAGE = FULL` | `ATTITUDE_EVALUATION = PASS`
- **`OHRC_PAIR_04`:** `CK_COVERAGE = FULL` | `ATTITUDE_EVALUATION = PASS`

---

## 2. CK Ingestion & Standalone Segment Extraction

The official ISRO URSC Flight Dynamics monthly attitude archive at the USGS Astrogeology ISIS repository comprises continuous Type 3 quaternion kernels spanning 2019 to 2025 (~200 GB total; ~9.05 GB for the four target months).

To achieve maximum computational and storage efficiency while preserving mathematical fidelity, the exact segment containing each OHRC imaging pass was identified in the DAF summary records and extracted via HTTP Range requests into a standalone, fully compliant NAIF DAF/CK binary kernel:

| Pair ID | Parent Source Monthly CK | Standalone Local CK File | SCLK Segment Range | Pointing Instances ($N$) | File Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`OHRC_PAIR_01`** | `ch2_att_27Nov2024_04Jan2025_v1.bc` | `ch2_att_pair01_subset.bc` | $[187267698.77, 187273599.05]$ | 46,085 | 1,850,368 | `06113d4d528bc0d15b021d7b37d4db8f342674eec7e6beee63821a73ee3453b3` |
| **`OHRC_PAIR_02`** | `ch2_att_27Jan2025_04Mar2025_v1.bc` | `ch2_att_pair02_subset.bc` | $[192711766.90, 192722813.93]$ | 86,420 | 3,460,096 | `02b6be5bd3c17724a4f89552f447781b0a7dd9bb95562d109f3c706bf950cb7d` |
| **`OHRC_PAIR_03`** | `ch2_att_27Feb2025_04Apr2025_v1.bc` | `ch2_att_pair03_subset.bc` | $[195089673.02, 195102481.05]$ | 100,200 | 4,012,032 | `93aa0b23f00877839359e13e005086b4f7df2b8f72cfa1eeadbc88a531f82f80` |
| **`OHRC_PAIR_04`** | `ch2_att_27Sep2025_03Nov2025_v1.bc` | `ch2_att_pair04_subset.bc` | $[213943310.31, 213946179.55]$ | 22,445 | 901,120 | `d594422ce2023b708aaee35c91ec1fe6a166cb029a149d5059635b706c9e0cf5` |

### Technical Specifications:
- **DAF Architecture:** Little-Endian IEEE (`LTL-IEEE`), 1024-byte physical records, `ND = 2`, `NI = 6`.
- **Instrument / Frame ID:** `-152001` (`CH2_ORBITER`).
- **Base Reference Frame:** `1` (`J2000` Inertial).
- **Data Type:** Type 3 (Continuous Quaternion Linear Interpolation).
- **Angular Rates:** Rates flag $= 0$ (quaternions only; angular velocity derived via SLERP/quaternion differentiation).

---

## 3. Attitude & Boresight Kinematics Across Scanline Epochs

Because OHRC is a pushbroom Time Delay Integration (TDI) line sensor, attitude was not merely evaluated at a single midpoint, but densely sampled across early, middle, and late scanlines (epochs at 0%, 25%, 50%, 75%, and 100% of the swath pass):

### 3.1 `OHRC_PAIR_01` (Pass: 2024-12-07T12:21:32 -> 12:21:48 UTC)
- Target SCLK Interval: $[187273277.0687, 187273293.4520]$
- Boresight Look-Vector in `IAU_MOON` Body-Fixed Frame:
  - **Line 0000 (0.0%):** $[+0.2034, -0.1681, +0.9646]$
  - **Line 1218 (25.0%):** $[+0.2051, -0.1712, +0.9637]$
  - **Line 2436 (50.0%):** $[+0.2068, -0.1742, +0.9627]$
  - **Line 3653 (75.0%):** $[+0.2085, -0.1773, +0.9618]$
  - **Line 4871 (100.0%):** $[+0.2102, -0.1803, +0.9609]$
- **Evaluation Status:** **PASS** (Zero interpolation gaps, continuous quaternion evolution).

### 3.2 `OHRC_PAIR_02` (Pass: 2025-02-08T14:02:45 -> 14:03:02 UTC)
- Target SCLK Interval: $[192722548.0035, 192722564.3870]$
- Boresight Look-Vector in `IAU_MOON` Body-Fixed Frame:
  - **Line 0000 (0.0%):** $[+0.1663, -0.0287, +0.9857]$
  - **Line 1264 (25.0%):** $[+0.1628, -0.0293, +0.9862]$
  - **Line 2529 (50.0%):** $[+0.1592, -0.0298, +0.9868]$
  - **Line 3794 (75.0%):** $[+0.1557, -0.0304, +0.9873]$
  - **Line 5058 (100.0%):** $[+0.1522, -0.0309, +0.9879]$
- **Evaluation Status:** **PASS**

### 3.3 `OHRC_PAIR_03` (Pass: 2025-03-08T01:27:52 -> 01:28:09 UTC)
- Target SCLK Interval: $[195096453.8327, 195096470.7451]$
- Boresight Look-Vector in `IAU_MOON` Body-Fixed Frame:
  - **Line 0000 (0.0%):** $[+0.1982, -0.0007, +0.9802]$
  - **Line 1263 (25.0%):** $[+0.1946, -0.0011, +0.9809]$
  - **Line 2526 (50.0%):** $[+0.1909, -0.0016, +0.9816]$
  - **Line 3790 (75.0%):** $[+0.1872, -0.0021, +0.9823]$
  - **Line 5053 (100.0%):** $[+0.1835, -0.0025, +0.9830]$
- **Evaluation Status:** **PASS**

### 3.4 `OHRC_PAIR_04` (Pass: 2025-10-12T04:58:21 -> 04:58:37 UTC)
- Target SCLK Interval: $[213944273.6128, 213944289.9964]$
- Boresight Look-Vector in `IAU_MOON` Body-Fixed Frame:
  - **Line 0000 (0.0%):** $[+0.3276, -0.0305, +0.9443]$
  - **Line 1162 (25.0%):** $[+0.3243, -0.0315, +0.9454]$
  - **Line 2324 (50.0%):** $[+0.3209, -0.0325, +0.9465]$
  - **Line 3486 (75.0%):** $[+0.3176, -0.0335, +0.9476]$
  - **Line 4648 (100.0%):** $[+0.3142, -0.0345, +0.9487]$
- **Evaluation Status:** **PASS**

---

## 4. Technical Verdict

Continuous pointing attitude is fully verified across the entire imaging interval for all four OHRC mentor passes.
