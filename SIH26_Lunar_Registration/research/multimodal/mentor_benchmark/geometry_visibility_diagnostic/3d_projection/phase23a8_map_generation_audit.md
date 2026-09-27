# Phase 23A.8 — Map-Generation & Control-Point Provenance Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit investigates the mathematical and cartographic mechanisms used to produce the mentor reference rasters, specifically assessing whether coordinates derive from direct camera geometry, bundle adjustment, ground control points (GCPs), mosaic registration, or orthorectification.

> ### **Primary Finding on Map Generation:**
> # **`MAP_GENERATION_PROVENANCE = UNKNOWN`**  
> Zero ground control points, bundle adjustment covariance reports, orthorectification DTM metadata, or processing logs are present in the mentor benchmark delivery.

---

## 2. Technical Evaluation Across Processing Modalities

| Map-Generation Modality | Evidentiary Status in Reference Raster | Supporting Evidence / Audit Finding | Assessment |
| :--- | :---: | :--- | :--- |
| **Direct Camera Geometry** | **`UNKNOWN`** | No camera model, optical intrinsics, or flight state vectors accompany the reference raster. | Raster cannot be back-projected into space. |
| **Bundle Adjustment** | **`UNKNOWN`** | No tie-point residuals, covariance matrices, or network adjustment logs exist. | **Prohibited from inference without evidence.** |
| **Ground Control Points (GCPs)** | **`UNKNOWN`** | No surveyed lunar surface features or retroreflector coordinates are linked. | Basemap absolute accuracy is unanchored. |
| **Mosaic Registration** | **`COMPATIBLE_WITH`** | Overlap test proves identical reference content over verified overlap (100.00% match). | Extracted from a pre-assembled mosaic or identical upstream source. |
| **Orthorectification** | **`PARTIALLY_EVIDENT`** | Raster is delivered in projected map coordinates (5.0 m/px) rather than camera perspective. | DTM elevation model used is unrecorded. |

---

## 3. Ad-Hoc Fitting Prohibition / No Documented Control Solution Identified

In accordance with Phase 23A.8 discipline:
- **Do NOT fit a translation to the reference raster merely to make the residual disappear.**
- **Do NOT estimate an undocumented map offset from the four corners and call it the true geodetic correction.**

> **Scientific Rationale:**  
> The audit did not identify GCP files, bundle-adjustment covariance, or orthorectification-control metadata in the supplied package. This absence does not prove that no such process was used externally.
> Fitting an empirical translation $\vec{T} = [\Delta x, \Delta y]$ to force the OHRC physical projection into visual alignment with the mentor reference raster would contaminate the benchmark. Without independent surveyed ground control, estimating an offset from the observed residual assumes that the reference raster is absolute truth—an assumption contradicted by the complete absence of reference geodetic metadata.
