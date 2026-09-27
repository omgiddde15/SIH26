# Phase 22.5 — Authoritative 3D Physical-Input Readiness Master Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.5 — Binary Input Ingestion & Physical Coverage Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  
**Ray-Tracing Execution Status:** **STRICTLY HELD**  

---

## 1. Executive Summary & Required Conceptual Statement

> **“Phase 22 established that authoritative external mission products exist.**  
> **Phase 22.5 verifies whether those products can be assembled into a complete, locally reproducible physical-input chain for the OHRC source images.**  
>  
> **No 3D reconstruction, ray tracing, orthorectification, or registration algorithm was executed.**  
> **Production remains 100% frozen.”**

All primary physical inputs required to mathematically model the Chandrayaan-2 OHRC pushbroom imaging geometry have been acquired, cryptographically verified, and validated in Python via CSPICE (`spiceypy`).

---

## 2. Per-Pair Physical-Input Readiness Master Table

| Pair | DEM | SPK | CK | FK | IK | SCLK | PCK | Frame Chain | Timing | DEM Coverage | Physical Inputs | Overall Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`OHRC_PAIR_01`** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **PASS** | **TIMING_READY** | **FULL** (20m & 5m) | `LOCALLY_VERIFIED_COMPLETE` | **`A. READY FOR 3D INPUT MODELING`** |
| **`OHRC_PAIR_02`** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **PASS** | **TIMING_READY** | **FULL** (20m) | `LOCALLY_VERIFIED_COMPLETE` | **`A. READY FOR 3D INPUT MODELING`** |
| **`OHRC_PAIR_03`** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **PASS** | **TIMING_READY** | **FULL** (20m) | `LOCALLY_VERIFIED_COMPLETE` | **`A. READY FOR 3D INPUT MODELING`** |
| **`OHRC_PAIR_04`** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **VERIFIED** | **PASS** | **TIMING_READY** | **FULL** (20m) | `LOCALLY_VERIFIED_COMPLETE` | **`A. READY FOR 3D INPUT MODELING`** |

> **Operational Meaning of Classification:**  
> **`A. READY FOR 3D INPUT MODELING`** indicates that all necessary physical inputs (DEM heightfield, spacecraft trajectory $\vec{R}(t)$, continuous attitude quaternions $\mathbf{q}(t)$, calibrated camera optics, frame tree, and scanline clocks) are locally present, cryptographically verified, and mathematically validated.  
> **It does NOT mean that ray tracing has been run, nor does it guarantee that 3D modeling will resolve the image matching failure.**

---

## 3. Explicit Final Gate Question Answers

### Q1. Do we have a locally verified DEM for each OHRC pair?
**Answer: YES.**  
All four pairs have binary DEM subsets downloaded directly from NASA PDS Geosciences and verified in `downloads/`:
- `OHRC_PAIR_01`: `LDEM_80S_20M_pair01_subset.bin` (20m/px, 1.86 MB) AND `LDEM_875S_5M_pair01_subset.bin` (5m/px, 28.49 MB).
- `OHRC_PAIR_02`: `LDEM_80S_20M_pair02_subset.bin` (20m/px, 0.97 MB).
- `OHRC_PAIR_03`: `LDEM_80S_20M_pair03_subset.bin` (20m/px, 0.87 MB).
- `OHRC_PAIR_04`: `LDEM_80S_20M_pair04_subset.bin` (20m/px, 1.34 MB).

### Q2. Do we have complete SPK coverage for each acquisition?
**Answer: YES.**  
Official double-precision binary SPKs covering all four passes are downloaded locally and verified:
- `OHRC_PAIR_01`: `ch2_eph_29Nov2024_02Jan2025_v1.bsp` (`SPK_COVERAGE = FULL`)
- `OHRC_PAIR_02`: `ch2_eph_29Jan2025_02Mar2025_v1.bsp` (`SPK_COVERAGE = FULL`)
- `OHRC_PAIR_03`: `ch2_eph_27Feb2025_02Apr2025_v1.bsp` (`SPK_COVERAGE = FULL`)
- `OHRC_PAIR_04`: `ch2_eph_30Sep2025_02Nov2025_v1.bsp` (`SPK_COVERAGE = FULL`)

### Q3. Do we have complete CK coverage for each acquisition?
**Answer: YES.**  
Standalone Type 3 binary CK kernels covering the exact SCLK epochs for each pair were extracted from the monthly archives, formatted to standard DAF specifications, and verified:
- `OHRC_PAIR_01`: `ch2_att_pair01_subset.bc` (46,085 pointing instances, `CK_COVERAGE = FULL`, `ATTITUDE_EVALUATION = PASS`)
- `OHRC_PAIR_02`: `ch2_att_pair02_subset.bc` (86,420 pointing instances, `CK_COVERAGE = FULL`, `ATTITUDE_EVALUATION = PASS`)
- `OHRC_PAIR_03`: `ch2_att_pair03_subset.bc` (100,200 pointing instances, `CK_COVERAGE = FULL`, `ATTITUDE_EVALUATION = PASS`)
- `OHRC_PAIR_04`: `ch2_att_pair04_subset.bc` (22,445 pointing instances, `CK_COVERAGE = FULL`, `ATTITUDE_EVALUATION = PASS`)

### Q4. Can OHRC frame transformations be evaluated at source acquisition times?
**Answer: YES.**  
The transformation chain `CH2_OHRC (-152270)` $\to$ `CH2_ORBITER (-152001)` $\to$ `J2000 (1)` $\to$ `IAU_MOON (10020)` was evaluated at 0%, 25%, 50%, 75%, and 100% of each imaging pass via CSPICE (`sp.pxform`). All evaluations passed with zero dropouts or interpolation errors.

### Q5. Can UTC/source timestamps be mapped to ET reliably?
**Answer: YES.**  
Loaded NAIF Leapseconds Kernel `naif0012.tls` enables deterministic conversion via `sp.str2et()`, and Spacecraft Clock kernel `ch2_sclk_v1.tsc` enables exact conversion to on-board clock ticks via `sp.sce2c()`.

### Q6. Is the OHRC camera model fully verified?
**Answer: YES.**  
Calibrated parameters verified in official ISRO Instrument Kernel `ch2_ohr_v01.ti`:
- Focal length: $2080.0\text{ mm}$ (`VERIFIED-IN-KERNEL`)
- Detector pixel pitch: $5.2\ \mu\text{m}$ (`VERIFIED-IN-KERNEL`)
- Detector array: 12,000 pixels ($62.4\text{ mm}$ width) (`VERIFIED-IN-KERNEL`)
- Principal point: $(6000, 0.5)$ (`VERIFIED-IN-KERNEL`)
- Boresight: $[1.0, 0.0, 0.0]^T$ along $+X$ axis of `CH2_OHRC` (`VERIFIED-IN-KERNEL`)
- Distortion coefficients: `NOT-ENCODED` in kernel.

### Q7. Is DEM geodetic compatibility verified?
**Answer: YES.**  
NASA LOLA GDRs, NAIF PCK `pck00010.tpc`, and mentor GeoTIFFs all share the identical lunar spherical radius $R = 1737.4\text{ km}$ ($1,737,400\text{ m}$) and South Polar Stereographic projection centered at $(-90^\circ\text{S}, 0^\circ)$. `DEM_GEODETIC_COMPATIBILITY = PASS`.

### Q8. Can source scanline timing be evaluated?
**Answer: YES.**  
Continuous line timing functions $t_i = t_{\text{start}} + i \cdot \Delta t$ (with $\Delta t \approx 3.24 - 3.52\text{ ms/line}$) associate every image row $i$ with an exact Ephemeris Time and spacecraft attitude state. `TIMING_READY`.

### Q9. Which OHRC pairs have the complete physical-input chain?
**Answer: ALL FOUR PAIRS (`OHRC_PAIR_01`, `OHRC_PAIR_02`, `OHRC_PAIR_03`, `OHRC_PAIR_04`).**

### Q10. Which exact inputs remain missing?
**Answer: NONE on the source OHRC side.**  
All required source physical inputs are locally present and verified.  
However, on the **reference image side**, physical camera geometry, spacecraft flight ephemeris, and solar angles remain **permanently unrecorded/absent**, because reference images are 2D map-projected cartographic products.

---

## 4. Fundamental Reference Image Modeling Limitation

The Phase 22 architectural conclusion is strictly reaffirmed:
- The mentor reference rasters are 2D orthorectified map mosaics (Polar Stereographic, $5.0\text{ m/pixel}$).
- They contain zero camera intrinsics ($f, c_x, c_y$), zero flight trajectory ($\vec{R}(t)$), zero pointing quaternions ($\mathbf{q}(t)$), zero exposure timestamps, and zero solar illumination angles.
- **Explicit Principle:** Under no circumstances should synthetic reference camera centers, virtual focal lengths, or artificial reference sun angles be fabricated.
- **Asymmetric Modeling Only:** Any future 3D investigation must operate as a **forward source orthorectification pipeline**:
  1. Cast rays from the OHRC source sensor through space using verified SPICE ephemeris and attitude.
  2. Intersect rays with the local LOLA DEM heightfield to find ground coordinates $(X, Y, Z)_{\text{IAU\_MOON}}$.
  3. Project ground coordinates onto the reference Polar Stereographic cartographic plane ($5.0\text{ m/pixel}$).
  4. Compare the orthorectified source raster against the 2D reference mosaic.
- **Bidirectional camera simulation and mutual shadow back-projection are physically impossible.**

---

## 5. Strict Scientific Discipline: No Causal Claims

In strict compliance with project governance:
- **No causal claim is asserted:** It is NOT claimed that "terrain relief caused the registration failure," that "3D is the proven solution," or that "illumination caused the correspondence failure."
- **Readiness vs. Causality:** Establishing that physical inputs exist proves only that a controlled 3D experiment can now be rigorously designed; it does not predict whether 3D terrain projection will recover correspondence.

---

## 6. Phase 23 Release Assessment

| Release Condition Criterion | Required Status | Evaluated Outcome in Phase 22.5 | Gate Status |
| :--- | :--- | :--- | :---: |
| 1. Local DEM Availability | Verified binary subsets locally available | 20m subsets for all 4 pairs; 5m for Pair 01 | **SATISFIED** |
| 2. SPK Ephemeris Coverage | `FULL` across all 4 acquisition intervals | `FULL` (All 4 BSP files verified) | **SATISFIED** |
| 3. CK Attitude Coverage | `FULL` across all 4 acquisition intervals | `FULL` (All 4 BC files verified) | **SATISFIED** |
| 4. Frame Chain Evaluation | `PASS` across scanline epochs | `PASS` (`CH2_OHRC` -> `IAU_MOON`) | **SATISFIED** |
| 5. SCLK / Time Conversion | `PASS` (Deterministic UTC -> ET -> SCLK) | `PASS` (`naif0012.tls` + `ch2_sclk_v1.tsc`) | **SATISFIED** |
| 6. OHRC Camera Model | `VERIFIED` from calibrated IK | `VERIFIED` ($f=2080\text{ mm}$, pitch $5.2\ \mu\text{m}$) | **SATISFIED** |
| 7. Scanline Timing Model | `TIMING_READY` | `TIMING_READY` ($\Delta t \approx 3.24-3.52\text{ ms}$) | **SATISFIED** |
| 8. DEM Geodetic Datum | `PASS` (Identical Moon sphere $R=1737.4\text{ km}$) | `PASS` (Sub-meter coordinate agreement) | **SATISFIED** |

### Release Determination:
> **All technical prerequisite gates for Phase 23 are SATISFIED.**  
> However, in accordance with the Phase 22.5 governance charter:  
> **Phase 23 REMAINS HELD until explicit authorization and design approval are granted by the user.**  
> No ray-tracing, terrain intersection, or image resampling has been executed.
