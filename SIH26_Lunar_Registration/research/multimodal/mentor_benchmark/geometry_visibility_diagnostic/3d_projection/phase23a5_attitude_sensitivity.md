# Phase 23A.5 — Attitude Pointing Sensitivity Analysis Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report provides a controlled sensitivity analysis quantifying how angular pointing perturbations in the spacecraft attitude model impact the lunar surface ground-intersection coordinates. **No attitude optimization or fitting was performed.**

---

## 2. Quantitative Sensitivity Telemetry

| Parameter Domain | Angular Perturbation | Surface Ground Displacement | Equivalent Ground Scale |
| :--- | :---: | :---: | :---: |
| Pitch (cross-track rotation) | **+0.001 deg** | **1.83 m** | 0.37 delivered pixels |
| Yaw (along-track rotation) | **+0.001 deg** | **1.88 m** | 0.38 delivered pixels |
| Pitch (cross-track rotation) | **+0.005 deg** | **9.14 m** | 1.83 delivered pixels |
| Yaw (along-track rotation) | **+0.005 deg** | **9.40 m** | 1.88 delivered pixels |
| Pitch (cross-track rotation) | **+0.010 deg** | **18.28 m** | 3.66 delivered pixels |
| Yaw (along-track rotation) | **+0.010 deg** | **18.80 m** | 3.76 delivered pixels |
| Pitch (cross-track rotation) | **+0.050 deg** | **91.41 m** | 18.28 delivered pixels |
| Yaw (along-track rotation) | **+0.050 deg** | **93.97 m** | 18.79 delivered pixels |
| Pitch (cross-track rotation) | **-0.001 deg** | **1.83 m** | 0.37 delivered pixels |
| Yaw (along-track rotation) | **-0.001 deg** | **1.88 m** | 0.38 delivered pixels |
| Pitch (cross-track rotation) | **-0.005 deg** | **9.14 m** | 1.83 delivered pixels |
| Yaw (along-track rotation) | **-0.005 deg** | **9.40 m** | 1.88 delivered pixels |
| Pitch (cross-track rotation) | **-0.010 deg** | **18.28 m** | 3.66 delivered pixels |
| Yaw (along-track rotation) | **-0.010 deg** | **18.80 m** | 3.76 delivered pixels |
| Pitch (cross-track rotation) | **-0.050 deg** | **91.40 m** | 18.28 delivered pixels |
| Yaw (along-track rotation) | **-0.050 deg** | **94.01 m** | 18.80 delivered pixels |

---

## 3. Physical Interpretation & Scaling Limits

1. **Linear Pointing Scale Factor:** At nominal orbiter altitudes ($H \approx 100\text{ km}$), an angular pointing deflection of $\delta \theta$ produces a ground displacement of:
   $$\Delta x \approx H \cdot \delta \theta \approx 1.83\text{ meters per } 0.001^\circ\text{ (3.6 arcsec)}$$
2. **Audited Attitude Uncertainty Bound:**
   - The Phase 22.6 C-kernel audit confirmed that the verified standalone CK files match the parent mission files to within **$\le 0.006147\text{ arcsec}$** ($< 2.5\text{ mm}$ on the ground).
   - Spacecraft star-tracker pointing knowledge is nominally accurate to within $\approx 1 - 5\text{ arcsec}$ ($0.0003^\circ - 0.0014^\circ$), producing at most **$\approx 0.5 - 2.5\text{ meters}$** of surface displacement.
3. **Attitude Attribution Limit:**
   - To explain a $\approx 2,000\text{ meter}$ ($2\text{ km}$) ground residual through attitude pointing error alone would require a systematic pointing offset of:
     $$\delta \theta = \frac{2000\text{ m}}{100,000\text{ m}} \approx 0.020\text{ rad} \approx 1.15^\circ\text{ (4,100 arcseconds)}$$
   - Such an enormous attitude discrepancy is **two to three orders of magnitude larger** than certified Chandrayaan-2 star tracker pointing uncertainties.

> **Verdict:** While attitude uncertainty contributes a small ground variance ($\le 2.5\text{ m}$), nominal pointing uncertainty **cannot alone account for** the observed $\approx 1.9 - 3.6\text{ km}$ residual.
