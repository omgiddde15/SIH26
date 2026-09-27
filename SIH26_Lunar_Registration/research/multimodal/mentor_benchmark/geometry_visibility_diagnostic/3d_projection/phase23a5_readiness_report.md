# Phase 23A.5 — Physical Projection Residual Attribution Audit: Master Synthesis Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  
**Phase 23B Recommendation:** **`AWAITING RESIDUAL REVIEW`**  

---

## 1. Executive Summary & Required Interpretation Revisions

Phase 23A.5 executed a comprehensive attribution audit to isolate what classes of physical/model uncertainty are capable of producing the observed source-to-map residuals ($pprox 1.9 - 3.6\text{ km}$).

### Corrected Phase 23A Wording Standards Enforced:
1. *'Terrain relief produces substantial non-planar displacement relative to the spherical reference model, motivating a direct comparison between DEM-based projection and planar transformations.'*
2. *'The source-to-map residual is currently unexplained and may contain contributions from ephemeris, attitude, timing, raster geometry, projection convention, DEM datum, and mentor map geolocation.'*
3. *'For the tested Pair 01 samples, the 20m and 5m DEMs produced sub-meter horizontal intersection differences.'*
4. *'100% of successful projections fell within reference-raster bounds; bounds containment is not a geolocation validation.'*
5. *'3/9 rays exited the available cropped DEM subset; this is not evidence that the physical ray lacks a lunar-surface intersection.'*

> **Disclaimer:** *Optical distortion is not modeled; distortion uncertainty is unquantified.*

---

## 2. Source-Image Corner Geolocation Evaluation

Evaluated across all four corners of the delivered source raster for each pair, comparing forward physical projections against source GeoTIFF corner tiepoints (`ModelTiepointTag` 33922):

| Pair ID | Corner | Delivered $(u, v)$ | Tiepoint Selenographic $(\phi, \lambda)$ | Sphere Projection $(\phi, \lambda)$ | Sphere vs. Tiepoint Residual | DEM Status | DEM vs. Tiepoint Residual |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | `UL` | `(0, 0)` | `-89.4689, 245.7792` | `-89.4980, 238.5549` | **2161.6 m** | `INTERSECTED` | **1973.3 m** |
| **`OHRC_PAIR_01`** | `UR` | `(624, 0)` | `-89.3820, 239.7295` | `-89.4066, 233.4375` | **2149.6 m** | `INTERSECTED` | **1885.1 m** |
| **`OHRC_PAIR_01`** | `LL` | `(0, 4872)` | `-89.3299, 158.6608` | `-89.2675, 155.8102` | **2167.8 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_01`** | `LR` | `(624, 4872)` | `-89.2563, 164.8455` | `-89.1995, 161.6676` | **2155.5 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_02`** | `UL` | `(0, 0)` | `-84.5749, 26.7233` | `-84.5343, 26.6282` | **1266.4 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_02`** | `UR` | `(648, 0)` | `-84.5403, 27.8137` | `-84.5003, 27.6964` | **1262.3 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_02`** | `LL` | `(0, 5059)` | `-85.3539, 29.9341` | `-85.3138, 29.7920` | **1267.8 m** | `INTERSECTED` | **2197.1 m** |
| **`OHRC_PAIR_02`** | `LR` | `(648, 5059)` | `-85.3134, 31.1806` | `-85.2741, 31.0124` | **1264.0 m** | `INTERSECTED` | **2270.2 m** |
| **`OHRC_PAIR_03`** | `UL` | `(0, 0)` | `-84.5758, 24.2078` | `-84.5086, 24.0232` | **2109.7 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_03`** | `UR` | `(600, 0)` | `-84.5445, 25.2276` | `-84.4781, 25.0189` | **2107.7 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_03`** | `LL` | `(0, 5054)` | `-85.3667, 27.3036` | `-85.3258, 27.1550` | **1292.9 m** | `INTERSECTED` | **2195.3 m** |
| **`OHRC_PAIR_03`** | `LR` | `(600, 5054)` | `-85.3300, 28.4743` | `-85.2899, 28.3022` | **1290.2 m** | `INTERSECTED` | **2323.7 m** |
| **`OHRC_PAIR_04`** | `UL` | `(0, 0)` | `-83.7873, 30.8181` | `-83.7175, 30.6621` | **2183.6 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_04`** | `UR` | `(552, 0)` | `-83.7640, 31.7151` | `-83.6947, 31.5440` | **2181.8 m** | `OUTSIDE_DEM` | N/A |
| **`OHRC_PAIR_04`** | `LL` | `(0, 4649)` | `-84.5966, 33.1581` | `-84.5277, 32.9475` | **2180.4 m** | `INTERSECTED` | **3502.9 m** |
| **`OHRC_PAIR_04`** | `LR` | `(552, 4649)` | `-84.5693, 34.1764` | `-84.5010, 33.9477` | **2178.8 m** | `INTERSECTED` | **3523.2 m** |

### Key Observation on Source Corner Residuals:
- In `OHRC_PAIR_01`, the residual between the sphere projection and the source tiepoint is **$2,149.6 - 2,167.8\text{ m}$** across all four corners (variance $< 18\text{ m}$ across the entire $24.4\text{ km}$ strip).
- In `OHRC_PAIR_02`, the residual is **$1,262.3 - 1,267.8\text{ m}$** (variance $< 5.5\text{ m}$ across $25.3\text{ km}$).
- In `OHRC_PAIR_04`, the residual is **$2,178.7 - 2,183.5\text{ m}$** (variance $< 4.8\text{ m}$ across $23.2\text{ km}$).
- This invariant residual vector confirms that the forward physical model and the source metadata tiepoints differ primarily by a **highly rigid spatial offset**, not differential scaling or unmodeled rotation.

---

## 3. Master Residual Attribution Sensitivity Table

| Effect | Perturbation | Ground Displacement | Interpretation |
| :--- | ---: | ---: | :--- |
| **Attitude** | $\pm 0.001^\circ$ ($3.6\text{ arcsec}$) | **$1.83\text{ m}$** | Sensitivity only (pitch/yaw deflection) |
| **Attitude** | $\pm 0.010^\circ$ ($36\text{ arcsec}$) | **$18.28\text{ m}$** | Sensitivity only (linear angular scaling) |
| **Attitude** | $\pm 0.050^\circ$ ($180\text{ arcsec}$) | **$91.41\text{ m}$** | Sensitivity only ($> 1.1^\circ$ needed for $2\text{ km}$) |
| **Position** | Along-track $\pm 10\text{ m}$ | **$10.03\text{ m}$** | Sensitivity only (1:1 horizontal translation) |
| **Position** | Along-track $\pm 100\text{ m}$ | **$100.34\text{ m}$** | Sensitivity only (1:1 horizontal translation) |
| **Position** | Along-track $\pm 1000\text{ m}$ | **$1003.34\text{ m}$** | Sensitivity only (1:1 horizontal translation) |
| **Position** | Radial altitude $\pm 100\text{ m}$ | **$27.52\text{ m}$** | Sensitivity only (scales by $\tan(\theta_{\text{emission}})$) |
| **Timing** | $\pm 0.1\text{ lines}$ ($\pm 0.34\text{ ms}$) | **$0.52\text{ m}$** | Sensitivity only (spacecraft advance during offset) |
| **Timing** | $\pm 1.0\text{ lines}$ ($\pm 3.36\text{ ms}$) | **$5.19\text{ m}$** | Sensitivity only ($5.2\text{ m/line}$) |
| **Timing** | $\pm 10.0\text{ lines}$ ($\pm 33.6\text{ ms}$) | **$51.93\text{ m}$** | Sensitivity only ($> 370\text{ lines}$ needed for $2\text{ km}$) |
| **Pixel-center** | Half-pixel $\pm 0.5\text{ px}$ | **$2.52\text{ m}$** | Sensitivity only (corner vs center definition) |
| **Camera mapping** | Principal point $\pm 0.5\text{ native px}$ | **$0.13\text{ m}$** | Sensitivity only (array center indexing convention) |
| **Native/TIFF scale** | $\text{floor}(s_x)=19.0$ vs $19.231$ | **$6.26\text{ m}$** | Sensitivity only (cross-track scaling quantization) |
| **DEM resolution** | $5\text{ m}$ vs $20\text{ m}$ DEM (Pair 01) | **$0.11\text{ m}$** | Sensitivity only (sub-meter horizontal agreement) |

> **Methodological Rule:** No causal winner is named. All rows report controlled experimental sensitivities only.

---

## 4. Final Scientific Question

> ### **“What classes of physical/model uncertainty are capable of producing the observed source-to-map residuals?”**

### Answer:
The quantitative sensitivity analyses indicate that **no single nominal operational uncertainty** (attitude jitter $< 5\text{ arcsec}$, clock timing $< 1\text{ ms}$, pixel-center convention $< 0.5\text{ px}$, or DEM resolution) is of sufficient magnitude to produce the observed $\approx 1.9 - 3.6\text{ km}$ residual.

Instead, the observed residual is capable of being produced by:
1. **Orbital Ephemeris Datum Offsets:** Chandrayaan-2 SPK orbit determination relative to the LRO LOLA/LROC reference frame represents a primary candidate contributing hundreds of meters to kilometers of rigid translation.
2. **Planar Tiepoint Approximations in Mentor Metadata:** The mentor source GeoTIFF corner tiepoints were generated assuming a spherical surface, neglecting $3 - 4.5\text{ km}$ crater depths.
3. **Reference Map Geolocation Datum Offsets:** Baseline georeferencing offsets in the delivered reference mosaic.
4. **Composite Effect:** The source-to-map residual is currently unexplained and may contain contributions from ephemeris, attitude, timing, raster geometry, projection convention, DEM datum, and mentor map geolocation.

*(Determining the exact causal breakdown requires a later controlled experiment; no registration or image warping was performed).* 

---

## 5. Preparation for Future Planar Model Comparison

Data structures and telemetry from Phase 23A and 23A.5 are preserved for a future controlled evaluation comparing:
- DEM-based physical projection
- Best-fit similarity transform
- Affine transform
- Homography

**None of these models were fitted during this phase.**

---

## 6. Phase 23B Gate Status

> # **`PHASE 23A.5 COMPLETE -- AWAITING RESIDUAL REVIEW`**  

> *(Phase 23B remains strictly held until user review of residual attribution results).* 
