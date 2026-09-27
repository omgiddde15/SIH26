# Phase 23A.5 — DEM Resolution Sensitivity Report (Pair 01)

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.5 — Physical Projection Residual Attribution Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report isolates the sensitivity of forward ray-terrain intersection to DEM resolution, comparing NASA LOLA `LDEM_80S_20M` (20 m/pixel) and `LDEM_875S_5M` (5 m/pixel) on `OHRC_PAIR_01`. **Results are strictly restricted to Pair 01 and not generalized.**

---

## 2. Quantitative Comparison Telemetry

| Evaluation Component | 20m vs 5m Measured Metric | Value | Pixel Ratio ($5.0\text{ m}$) |
| :--- | :--- | :---: | :---: |
| **Vertical Elevation Difference** | Mean $\Delta h = h_{\text{5m}} - h_{\text{20m}}$ | **$-0.01\text{ m}$** (Std dev $0.62\text{ m}$) | — |
| **Horizontal Ground Displacement** | Mean $\Delta r_{\text{hz}}$ | **$0.11\text{ m}$** (Range $0.00 - 0.36\text{ m}$) | **$0.02\times$ pixel** |
| **3D Vector Displacement** | Mean $\Delta r_{\text{3D}}$ | **$0.42\text{ m}$** (Range $0.02 - 1.35\text{ m}$) | **$0.08\times$ pixel** |

---

## 3. Physical Findings & Scope Discipline

1. **Sub-Meter Horizontal Agreement:** For the tested Pair 01 samples, the 20m and 5m DEMs produced sub-meter horizontal intersection differences (mean $0.11\text{ m}$).
2. **Topographic Smoothness in Polar Core:** The terrain traversed by `OHRC_PAIR_01` is relatively smooth polar rolling plains without multi-kilometer sheer escarpments.
3. **Scope Discipline:** This sub-meter agreement is demonstrated **strictly on Pair 01**. It must not be assumed to hold across rugged, high-relief crater walls (e.g. Pairs 02–04) where 5m DEM coverage does not exist.

> **Verdict:** For the tested Pair 01 samples, the 20m and 5m DEMs produced sub-meter horizontal intersection differences. DEM resolution is quantified strictly as an experimental property.
