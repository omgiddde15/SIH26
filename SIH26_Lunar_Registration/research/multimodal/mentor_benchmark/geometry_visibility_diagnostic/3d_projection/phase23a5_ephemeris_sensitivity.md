# Phase 23A.5 — Spacecraft Ephemeris Position Sensitivity Analysis Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report measures the sensitivity of the forward physical projection to controlled perturbations in the spacecraft position $\vec{R}(t)$ across along-track, cross-track, and radial directions. **No position optimization or fitting was performed.**

---

## 2. Quantitative Sensitivity Telemetry

| Spacecraft Perturbation Axis | Position Offset $\Delta \vec{R}$ | Resulting Ground Displacement | Transfer Ratio (Ground / SC) |
| :--- | :---: | :---: | :---: |
| Spacecraft along-track position | **+1.0 m** | **1.00 m** | 1.000 |
| Spacecraft cross-track position | **+1.0 m** | **1.00 m** | 1.000 |
| Spacecraft radial altitude | **+1.0 m** | **0.26 m** | 0.260 |
| Spacecraft along-track position | **+10.0 m** | **10.03 m** | 1.003 |
| Spacecraft cross-track position | **+10.0 m** | **10.00 m** | 1.000 |
| Spacecraft radial altitude | **+10.0 m** | **2.60 m** | 0.260 |
| Spacecraft along-track position | **+50.0 m** | **50.17 m** | 1.003 |
| Spacecraft cross-track position | **+50.0 m** | **50.02 m** | 1.000 |
| Spacecraft radial altitude | **+50.0 m** | **12.98 m** | 0.260 |
| Spacecraft along-track position | **+100.0 m** | **100.34 m** | 1.003 |
| Spacecraft cross-track position | **+100.0 m** | **100.04 m** | 1.000 |
| Spacecraft radial altitude | **+100.0 m** | **25.96 m** | 0.260 |
| Spacecraft along-track position | **+500.0 m** | **501.69 m** | 1.003 |
| Spacecraft cross-track position | **+500.0 m** | **500.21 m** | 1.000 |
| Spacecraft radial altitude | **+500.0 m** | **129.81 m** | 0.260 |
| Spacecraft along-track position | **+1000.0 m** | **1003.34 m** | 1.003 |
| Spacecraft cross-track position | **+1000.0 m** | **1000.41 m** | 1.000 |
| Spacecraft radial altitude | **+1000.0 m** | **259.63 m** | 0.260 |
| Spacecraft along-track position | **-1.0 m** | **1.00 m** | 1.000 |
| Spacecraft cross-track position | **-1.0 m** | **1.00 m** | 1.000 |
| Spacecraft radial altitude | **-1.0 m** | **0.26 m** | 0.260 |
| Spacecraft along-track position | **-10.0 m** | **10.03 m** | 1.003 |
| Spacecraft cross-track position | **-10.0 m** | **10.00 m** | 1.000 |
| Spacecraft radial altitude | **-10.0 m** | **2.60 m** | 0.260 |
| Spacecraft along-track position | **-50.0 m** | **50.17 m** | 1.003 |
| Spacecraft cross-track position | **-50.0 m** | **50.02 m** | 1.000 |
| Spacecraft radial altitude | **-50.0 m** | **12.98 m** | 0.260 |
| Spacecraft along-track position | **-100.0 m** | **100.34 m** | 1.003 |
| Spacecraft cross-track position | **-100.0 m** | **100.04 m** | 1.000 |
| Spacecraft radial altitude | **-100.0 m** | **25.96 m** | 0.260 |
| Spacecraft along-track position | **-500.0 m** | **501.73 m** | 1.003 |
| Spacecraft cross-track position | **-500.0 m** | **500.23 m** | 1.000 |
| Spacecraft radial altitude | **-500.0 m** | **129.81 m** | 0.260 |
| Spacecraft along-track position | **-1000.0 m** | **1003.49 m** | 1.003 |
| Spacecraft cross-track position | **-1000.0 m** | **1000.46 m** | 1.000 |
| Spacecraft radial altitude | **-1000.0 m** | **259.62 m** | 0.260 |

---

## 3. Physical Interpretation & Scaling Limits

1. **Horizontal Position Transfer (1:1 Ratio):**
   - Shifting the orbiter position horizontally along-track or cross-track translates the ground intersection by an identical amount ($1.003\times$ due to lunar curvature).
   - An ephemeris error of $100\text{ m}$ produces $100.3\text{ m}$ of ground shift; an error of $1,000\text{ m}$ produces $1,003\text{ m}$ of ground shift.
2. **Radial Altitude Transfer:**
   - Radial altitude perturbations transfer into ground displacement scaled by $\tan(\theta_{\text{emission}})$.
   - For near-nadir swaths ($	heta \approx 15^\circ$), a $100\text{ m}$ altitude error produces $\approx 27.5\text{ m}$ of ground shift.
3. **Attribution Assessment:**
   - Raw reconstructed Chandrayaan-2 SPK ephemeris (orbit determination) commonly exhibits baseline offsets of $\approx 50 - 200\text{ meters}$ relative to Lunar Reconnaissance Orbiter (LRO) basemaps.
   - A pure $1.9 - 3.6\text{ km}$ translation would require an orbital position error of $1.9 - 3.6\text{ km}$, which exceeds certified SPK orbit determination errors, indicating that ephemeris alone does not fully explain the residual.

> **Verdict:** Ephemeris offsets translate directly into ground displacement at a 1:1 ratio, but certified SPK trajectory precision indicates position error is only one component of a multi-source residual.
