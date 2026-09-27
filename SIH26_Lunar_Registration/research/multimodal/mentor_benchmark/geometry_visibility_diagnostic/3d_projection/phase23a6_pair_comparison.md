# Phase 23A.6 — Cross-Pair Comparison & Geometric Offset Decomposition Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.6 — Rigid Geodetic / Frame Offset Reconciliation  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This report evaluates whether the kilometre-scale source-to-map residuals observed across the four Chandrayaan-2 OHRC mentor benchmark pairs behave predominantly as a **rigid spatial translation**, a **similarity transform (scale/rotation)**, or an **affine deformation**.

### Key Findings:
1. **For Pairs 01, 02, and 04, the pure-translation model accounts for 98.16%–99.51% of the residual variance, with post-translation RMS residuals of 10.7–34.8 m.**
   - Post-translation RMS residuals across the $23–25\text{ km}$ swaths are only **$10.72\text{ m}$** (Pair 04), **$23.25\text{ m}$** (Pair 02), and **$34.80\text{ m}$** (Pair 01).
2. **Pair 03 exhibits a substantial anisotropic/non-rigid component. Its 3.15% similarity-scale discrepancy is numerically consistent with the difference between the reported flight-duration distance and delivered-raster along-track extent, but causal attribution to line timing or raster generation is not established in Phase 23A.6.**
3. **The differing residual magnitudes for the two nominally co-located acquisitions (`OHRC_PAIR_02` and `OHRC_PAIR_03`, differing by $435.01\text{ m}$) are not consistent with a single static map-offset term being the sole explanation of the observed discrepancies.**
4. **Pairs 02–04 have mutually similar residual-vector azimuths; their alignment with the spacecraft ground track is not independently established by the present report.**

---

## 2. Cross-Pair Geometric Decomposition Matrix

| Pair ID | Target / Latitude | Translation Vector $(dx, dy)$ | Translation Mag | Azimuth | Post-Trans RMS | Post-Trans MAX | Sim Scale Error | Sim Rot | Affine Anisotropy | Affine RMS |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | South Pole Crater (89.5°S) | `(+1720.2, -1303.6) m` | **2158.4 m** | 127.16° | **34.80 m** | 35.52 m | -96.4 ppm | +12.58" | 0.02207 | **0.08 m** |
| **`OHRC_PAIR_02`** | South Polar Highlands (84.9°S, 27°E) | `(+283.6, +1232.7) m` | **1264.9 m** | 12.95° | **23.25 m** | 27.04 m | -321.3 ppm | -67.73" | 0.01379 | **0.01 m** |
| **`OHRC_PAIR_03`** | South Polar Highlands (84.9°S, 25°E) | `(+274.8, +1677.6) m` | **1699.9 m** | 9.30° | **409.32 m** | 409.78 m | +31541.0 ppm | -62.91" | 0.04454 | **0.02 m** |
| **`OHRC_PAIR_04`** | South Polar Highlands (84.2°S, 32°E) | `(+627.4, +2088.9) m` | **2181.1 m** | 16.72° | **10.72 m** | 13.35 m | +21.9 ppm | -49.94" | 0.00682 | **0.01 m** |

---

## 3. Detailed Per-Pair Decomposition

### 3.1 `OHRC_PAIR_01` (South Pole Crater (89.5°S))
- **Acquisition Date:** 2024-11-24 | **Scan Timing Mode:** `forward`
- **Pure Translation Vector:** $\vec{t} = [+1720.20, -1303.61]^T\text{ m}$
- **Magnitude:** **$2158.36\text{ m}$** | **Azimuth:** **$127.16^\circ$**
- **Angular Spread across 4 Corners:** **$1.88^\circ$**
- **Post-Translation Residual:** RMS = **$34.80\text{ m}$**, Max = **$35.52\text{ m}$**
- **Similarity Descriptive Model:** Isotropic scale $s = 0.999904$ ($\Delta s = -96.4\text{ ppm}$), Rotation $\theta = +12.58\text{ arcsec}$, Post-Similarity RMS = **$34.77\text{ m}$**
- **Affine Descriptive Model:** Principal scales $\sigma = [1.000258, 0.978428]$, Determinant = $0.978681$, Anisotropy = $0.02207$, Non-orthogonality = $-1.0489^\circ$, Post-Affine RMS = **$0.08\text{ m}$**

#### Corner Residual Vectors:
| Corner | Delivered Pixel | Metadata $(X, Y)$ (m) | Physical $(X, Y)$ (m) | Vector $(dx, dy)$ (m) | Vector Mag | Post-Trans Res | Sim Res | Affine Res |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `UL` | `UL/UR/LL/LR` | `(-14687.1, -6607.1)` | `(-12985.9, -7940.7)` | `(+1701.2, -1333.6)` | **2161.6 m** | 35.52 m | 34.67 m | 0.08 m |
| `UR` | `UL/UR/LL/LR` | `(-16186.0, -9447.1)` | `(-14453.1, -10719.1)` | `(+1732.9, -1272.0)` | **2149.6 m** | 34.06 m | 34.86 m | 0.08 m |
| `LL` | `UL/UR/LL/LR` | `(7394.5, -18927.6)` | `(9102.2, -20262.9)` | `(+1707.7, -1335.3)` | **2167.8 m** | 34.08 m | 34.88 m | 0.08 m |
| `LR` | `UL/UR/LL/LR` | `(5895.8, -21768.5)` | `(7634.9, -23042.0)` | `(+1739.1, -1273.5)` | **2155.5 m** | 35.51 m | 34.66 m | 0.08 m |

### 3.2 `OHRC_PAIR_02` (South Polar Highlands (84.9°S, 27°E))
- **Acquisition Date:** 2025-02-08 | **Scan Timing Mode:** `inverted`
- **Pure Translation Vector:** $\vec{t} = [+283.56, +1232.74]^T\text{ m}$
- **Magnitude:** **$1264.93\text{ m}$** | **Azimuth:** **$12.95^\circ$**
- **Angular Spread across 4 Corners:** **$2.45^\circ$**
- **Post-Translation Residual:** RMS = **$23.25\text{ m}$**, Max = **$27.04\text{ m}$**
- **Similarity Descriptive Model:** Isotropic scale $s = 0.999679$ ($\Delta s = -321.3\text{ ppm}$), Rotation $\theta = -67.73\text{ arcsec}$, Post-Similarity RMS = **$22.51\text{ m}$**
- **Affine Descriptive Model:** Principal scales $\sigma = [0.999913, 0.986220]$, Determinant = $0.986134$, Anisotropy = $0.01379$, Non-orthogonality = $+0.2417^\circ$, Post-Affine RMS = **$0.01\text{ m}$**

#### Corner Residual Vectors:
| Corner | Delivered Pixel | Metadata $(X, Y)$ (m) | Physical $(X, Y)$ (m) | Vector $(dx, dy)$ (m) | Vector Mag | Post-Trans Res | Sim Res | Affine Res |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `UL` | `UL/UR/LL/LR` | `(74030.8, 147045.0)` | `(74340.9, 148272.8)` | `(+310.1, +1227.9)` | **1266.4 m** | 27.01 m | 22.48 m | 0.01 m |
| `UR` | `UL/UR/LL/LR` | `(77306.5, 146540.1)` | `(77571.4, 147774.4)` | `(+264.9, +1234.2)` | **1262.3 m** | 18.71 m | 22.51 m | 0.01 m |
| `LL` | `UL/UR/LL/LR` | `(70340.6, 122158.0)` | `(70642.9, 123389.2)` | `(+302.2, +1231.2)` | **1267.8 m** | 18.74 m | 22.54 m | 0.01 m |
| `LR` | `UL/UR/LL/LR` | `(73618.9, 121652.0)` | `(73875.9, 122889.7)` | `(+257.0, +1237.6)` | **1264.0 m** | 27.04 m | 22.51 m | 0.01 m |

### 3.3 `OHRC_PAIR_03` (South Polar Highlands (84.9°S, 25°E))
- **Acquisition Date:** 2025-03-08 | **Scan Timing Mode:** `inverted`
- **Pure Translation Vector:** $\vec{t} = [+274.78, +1677.59]^T\text{ m}$
- **Magnitude:** **$1699.94\text{ m}$** | **Azimuth:** **$9.30^\circ$**
- **Angular Spread across 4 Corners:** **$2.39^\circ$**
- **Post-Translation Residual:** RMS = **$409.32\text{ m}$**, Max = **$409.78\text{ m}$**
- **Similarity Descriptive Model:** Isotropic scale $s = 1.031541$ ($\Delta s = +31541.0\text{ ppm}$), Rotation $\theta = -62.91\text{ arcsec}$, Post-Similarity RMS = **$68.96\text{ m}$**
- **Affine Descriptive Model:** Principal scales $\sigma = [1.032197, 0.987226]$, Determinant = $1.019012$, Anisotropy = $0.04454$, Non-orthogonality = $+0.6079^\circ$, Post-Affine RMS = **$0.02\text{ m}$**

#### Corner Residual Vectors:
| Corner | Delivered Pixel | Metadata $(X, Y)$ (m) | Physical $(X, Y)$ (m) | Vector $(dx, dy)$ (m) | Vector Mag | Post-Trans Res | Sim Res | Affine Res |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `UL` | `UL/UR/LL/LR` | `(67495.2, 150128.7)` | `(67842.1, 152209.7)` | `(+346.9, +2081.0)` | **2109.7 m** | 409.77 m | 68.96 m | 0.02 m |
| `UR` | `UL/UR/LL/LR` | `(70561.9, 149764.5)` | `(70869.5, 151849.7)` | `(+307.6, +2085.1)` | **2107.7 m** | 408.87 m | 68.95 m | 0.02 m |
| `LL` | `UL/UR/LL/LR` | `(64482.4, 124913.2)` | `(64724.3, 126183.3)` | `(+241.9, +1270.0)` | **1292.9 m** | 408.86 m | 68.97 m | 0.02 m |
| `LR` | `UL/UR/LL/LR` | `(67551.8, 124548.0)` | `(67754.5, 125822.2)` | `(+202.7, +1274.2)` | **1290.2 m** | 409.78 m | 68.98 m | 0.02 m |

### 3.4 `OHRC_PAIR_04` (South Polar Highlands (84.2°S, 32°E))
- **Acquisition Date:** 2025-10-12 | **Scan Timing Mode:** `inverted`
- **Pure Translation Vector:** $\vec{t} = [+627.35, +2088.93]^T\text{ m}$
- **Magnitude:** **$2181.10\text{ m}$** | **Azimuth:** **$16.72^\circ$**
- **Angular Spread across 4 Corners:** **$0.69^\circ$**
- **Post-Translation Residual:** RMS = **$10.72\text{ m}$**, Max = **$13.35\text{ m}$**
- **Similarity Descriptive Model:** Isotropic scale $s = 1.000022$ ($\Delta s = +21.9\text{ ppm}$), Rotation $\theta = -49.94\text{ arcsec}$, Post-Similarity RMS = **$10.25\text{ m}$**
- **Affine Descriptive Model:** Principal scales $\sigma = [1.000117, 0.993320]$, Determinant = $0.993437$, Anisotropy = $0.00682$, Non-orthogonality = $+0.1931^\circ$, Post-Affine RMS = **$0.01\text{ m}$**

#### Corner Residual Vectors:
| Corner | Delivered Pixel | Metadata $(X, Y)$ (m) | Physical $(X, Y)$ (m) | Vector $(dx, dy)$ (m) | Vector Mag | Post-Trans Res | Sim Res | Affine Res |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `UL` | `UL/UR/LL/LR` | `(96610.0, 161948.5)` | `(97250.6, 164036.0)` | `(+640.6, +2087.5)` | **2183.6 m** | 13.35 m | 10.20 m | 0.01 m |
| `UR` | `UL/UR/LL/LR` | `(99505.6, 161018.3)` | `(100126.3, 163109.9)` | `(+620.7, +2091.6)` | **2181.8 m** | 7.18 m | 10.29 m | 0.01 m |
| `LL` | `UL/UR/LL/LR` | `(89683.7, 137270.2)` | `(90317.7, 139356.4)` | `(+634.0, +2086.2)` | **2180.4 m** | 7.18 m | 10.30 m | 0.01 m |
| `LR` | `UL/UR/LL/LR` | `(92574.8, 136340.3)` | `(93188.9, 138430.7)` | `(+614.1, +2090.4)` | **2178.8 m** | 13.35 m | 10.21 m | 0.01 m |

---

## 4. Focused Comparison: `OHRC_PAIR_02` vs. `OHRC_PAIR_03`

`OHRC_PAIR_02` and `OHRC_PAIR_03` provide a critical scientific control experiment because they image **essentially the identical geographic target** on the lunar surface (near $84.9^\circ\text{S}, 26^\circ\text{E}$):

| Property | `OHRC_PAIR_02` | `OHRC_PAIR_03` | Comparison / Significance |
| :--- | :---: | :---: | :--- |
| **Acquisition Date** | 2025-Feb-08 | 2025-Mar-08 | Acquired exactly 28 days apart |
| **Geographic Target** | 84.95°S, 27.3°E | 84.96°S, 25.1°E | Same south polar terrain |
| **Translation Magnitude** | **$1,264.93\text{ m}$** | **$1,699.94\text{ m}$** | $\Delta = 435.01\text{ m}$ difference in offset |
| **Translation Azimuth** | **$12.95^\circ$** | **$9.30^\circ$** | Mutually similar NNE azimuths ($\Delta = 3.65^\circ$) |
| **Post-Translation RMS** | **$23.25\text{ m}$** | **$409.32\text{ m}$** | Pair 02 is rigidly offset; Pair 03 has along-track scale dilation |
| **Similarity Scale Error** | **$-321.3\text{ ppm}$** ($-0.03\%$) | **$+31,541.0\text{ ppm}$** ($+3.15\%$) | Pair 03 exhibits $+3.15\%$ scale discrepancy |
| **Post-Similarity RMS** | **$22.51\text{ m}$** | **$68.96\text{ m}$** | Similarity absorbs along-track stretch |

### Inferences:
- **The differing residual magnitudes for the two nominally co-located acquisitions are not consistent with a single static map-offset term being the sole explanation of the observed discrepancies.**
- **Pairs 02–04 have mutually similar residual-vector azimuths; their alignment with the spacecraft ground track is not independently established by the present report.**
- **Pair 03 exhibits a substantial anisotropic/non-rigid component. Its 3.15% similarity-scale discrepancy is numerically consistent with the difference between the reported flight-duration distance and delivered-raster along-track extent, but causal attribution to line timing or raster generation is not established in Phase 23A.6.**

---

## 5. Mandatory Methodological Disclaimers

> **Terrain Disclaimer:**  

> *“The tested DEM correction changes the corner residuals only by metres, while the observed residuals are kilometre scale. Therefore the tested topographic correction does not explain the observed rigid source-to-map offset.”*

> **Affine Interpretation Warning:**  

> *“Four corner correspondences provide only 8 scalar observations for a 6-parameter affine model. The affine fit has only 2 residual degrees of freedom and is therefore descriptive/diagnostic, not independent evidence of physical deformation.”*
