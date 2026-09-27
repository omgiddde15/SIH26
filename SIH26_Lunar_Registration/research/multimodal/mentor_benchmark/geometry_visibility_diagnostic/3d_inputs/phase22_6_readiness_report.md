# Phase 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary & Purpose

Phase 22.6 establishes the exact mathematical, geometric, and temporal mapping connecting the authoritative physical sensor model of the Chandrayaan-2 Orbiter High Resolution Camera (OHRC) to the mentor-delivered source TIFF rasters (`source_at_5m.tif`) across all four benchmark pairs (`OHRC_PAIR_01` to `OHRC_PAIR_04`).

Before any Phase 23 ray-tracing or orthorectification could be considered, six fundamental physical and conventions questions had to be rigorously audited:
1. Native detector coordinate to supplied TIFF sample coordinate mapping.
2. Native camera geometry to delivered 5 m effective raster geometry.
3. Exact pixel-center registration convention.
4. Source line timing and exposure center convention.
5. CK attitude subset equivalence to official mission archives.
6. Optical distortion modeling status.

### Concluding Verdict:
> **`PHASE 23 READY FOR REVIEW`**  
> All physical, geometric, and temporal mappings are rigorously derived, verified, and bounded. Production code remains 100% untouched. Phase 23 is NOT automatically initiated; it is strictly held pending user review.

---

## 2. Complete Phase 22.6 Physical Model Readiness Matrix

| Physical / Modeling Parameter | `OHRC_PAIR_01` | `OHRC_PAIR_02` | `OHRC_PAIR_03` | `OHRC_PAIR_04` | Verification Basis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Native $\to$ TIFF Sample Mapping** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | Full 12,000-sample swath proven; 0% crop; isotropic scaling. |
| **TIFF Pixel-Center Convention** | **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | GeoKey 1025 confirms `RasterPixelIsArea`; center at $(u+0.5, v+0.5)$. |
| **Delivered Line Mapping** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | Along-track scale $s_y = N_{\text{scans}} / H_{\text{tiff}}$ matches $s_x$ to $< 0.01\%$. |
| **Line Timing Convention** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | **`DERIVED`** | Exposure-centered line model eliminates $\approx 2.7\text{ m}$ along-track bias. |
| **CK Subset Equivalence** | **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | Max angular discrepancy $\le 0.006147\text{ arcsec}$ ($< 2.5\text{ mm}$ displacement). |
| **Optical Distortion Status** | **`UNKNOWN`** | **`UNKNOWN`** | **`UNKNOWN`** | **`UNKNOWN`** | Unmodeled in SPICE IK; bounded at $< 0.2\text{ px}$; disclaimer required. |
| **Boresight & Frame Convention**| **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | **`VERIFIED`** | SPICE frame `CH2_OHRC`; boresight $[1, 0, 0]^T$; right-handed. |
| **Phase 22.6 Gate Status** | **PASSED** | **PASSED** | **PASSED** | **PASSED** | Fully verified and ready for Phase 23 review. |

---

## 3. Synthesis of Key Audit Findings

### 3.1 Sensor Geometry & Delivered Raster Widths
- The delivered widths ($624, 648, 600, 552$ pixels) represent the **full native 12,000-detector swath** with zero lateral cropping.
- Width variations are governed strictly by orbital altitude variations ($91.9\text{ km}$ to $105.8\text{ km}$), which alter the native ground sampling distance ($0.23\text{ m}$ to $0.27\text{ m}$). Resampling each swath to the common $5.000\text{ m}$ mentor benchmark grid yields the exact delivered pixel counts.
- The derived resampling is strictly isotropic ($s_x / s_y = 1.0000 \pm 0.0001$).
- Full documentation: [`raster_camera_mapping_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/raster_camera_mapping_report.md).

### 3.2 Pixel-Center Convention
- GeoTIFF Key 1025 confirms `RasterPixelIsArea` across all datasets.
- Integer coordinates $(u, v)$ represent the outer corner boundary; radiometric centers reside at $(u + 0.5, v + 0.5)$.
- The detector optical center is located at sample $6000.0$ in the focal plane.
- Full documentation: [`pixel_center_convention_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/pixel_center_convention_report.md).

### 3.3 Temporal Conventions & Exposure-Center Modeling
- Forensic analysis proved that `<integration_time_ms>` in the PDS4 XML represents microseconds ($\mu\text{s}$), agreeing with pass duration divided by scan count to $99.99\%$.
- Delivered TIFF row period is $\approx 3.24 - 3.52\text{ ms/row}$.
- Evaluating look-vectors at exposure line centers $t_{\text{center}}(v) = t_{\text{start}} + (v + 0.5)\Delta t_{\text{tiff}}$ eliminates an along-track bias of $\approx 2.7\text{ meters}$ ($0.55\text{ pixels}$).
- Full documentation: [`line_timing_convention_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/line_timing_convention_report.md).

### 3.4 Attitude Subset Equivalence
- Standalone C-kernels (`ch2_att_pair0X_subset.bc`) reproduce the continuous raw quaternion stream of the parent multi-gigabyte mission files across all imaging epochs with a maximum discrepancy of $\le 0.006147\text{ arcsec}$.
- The pointing precision is within $< 2.5\text{ millimeters}$ on the lunar surface.
- Full documentation: [`ck_subset_equivalence_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/ck_subset_equivalence_report.md).

### 3.5 Boresight and Optical Distortion Status
- The optical boresight is verified as $[1.0, 0.0, 0.0]^T$ in `CH2_OHRC`, with $+Y$ along-track and $+Z$ cross-track, right-handed. Full documentation: [`ohrc_boresight_convention_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/ohrc_boresight_convention_report.md).
- Distortion is unmodeled in SPICE IK (`DISTORTION_UNKNOWN`). While TMA physics bounds distortion at $< 0.2\text{ pixels}$, a mandatory disclaimer is required for Phase 23. Full documentation: [`distortion_status_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/distortion_status_report.md).

---

## 4. Modeling Constraints & Scientific Language Declarations

### 4.1 Reference Camera Constraint
As determined during the Phase 21/22 audits:
> **Reference camera model unavailable; therefore bidirectional camera-ray modeling is not supported. The planned experiment uses asymmetric OHRC-source-to-map orthorectification.**

### 4.2 Data Integrity Declaration
All binary SPICE kernels, DEM rasters, and derived subsets in this repository are **locally integrity-hashed** via SHA-256 and recorded in `checksums.sha256`.

---

## 5. Phase 23 Gate Determination

All required mathematical links between the delivered rasters and the authoritative physical model are established. Every prerequisite condition for Phase 23 is satisfied or explicitly bounded.

**Final Determination:**
# **`PHASE 23 READY FOR REVIEW`**
*(Phase 23 is NOT automatically started; held pending user review).*
