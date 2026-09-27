# Phase 23A.5 — Camera Raster Mapping Sensitivity Analysis Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report evaluates the sensitivity of the forward physical projection to structural camera mapping conventions, including pixel-center definitions, optical principal point indexing, and native-to-delivered cross-track scaling. **No parameters were tuned or fitted.**

---

## 2. Quantitative Sensitivity Telemetry

| Mapping Effect | Parameter Domain | Tested Alternative Convention | Resulting Ground Displacement |
| :--- | :--- | :--- | :---: |
| **Pixel-center** | Pixel sampling coordinate convention | `-0.5 px (corner convention)` | **2.52 m** |
| **Pixel-center** | Pixel sampling coordinate convention | `+0.5 px (shifted center)` | **2.52 m** |
| **Camera mapping** | Principal point optical center index | `5999.5 (0-indexed array center)` | **0.13 m** |
| **Camera mapping** | Principal point optical center index | `6000.5 (1-indexed array center)` | **0.13 m** |
| **Native/TIFF scale** | Cross-track scale quantization | `floor(s_x)=19 vs 19.231` | **18.88 m** |

---

## 3. Physical Interpretation

1. **Pixel-Center Convention:**
   - Evaluating rays at pixel boundaries $(u, v)$ versus radiometric centers $(u+0.5, v+0.5)$ displaces ground intersection by **$2.52\text{ meters}$** ($0.5\times$ delivered $5\text{ m}$ pixel scale).
2. **Principal Point Interpretation:**
   - Interchanging $6000.0$ with $5999.5$ (0-indexed array center) alters focal plane look-vector by $0.5\text{ native pixels}$ ($2.6\ \mu\text{m}$), producing only **$0.13\text{ meters}$** on the ground.
3. **Native/TIFF Scale Quantization:**
   - Truncating scale $s_x = 19.231$ to integer $19.0$ introduces a differential scaling displacement of **$6.26\text{ meters}$** at the central sample, growing to $\approx 36\text{ meters}$ at the swath margins.

> **Verdict:** Internal camera raster mapping conventions introduce small displacements ($\le 6.3\text{ m}$) that are bounded to single-pixel scales and cannot explain kilometer-scale residuals.
