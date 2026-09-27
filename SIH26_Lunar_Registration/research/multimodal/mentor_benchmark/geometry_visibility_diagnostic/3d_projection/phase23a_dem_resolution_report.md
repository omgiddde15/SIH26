# Phase 23A — DEM Resolution Sensitivity Report (OHRC_PAIR_01: 20m vs. 5m)

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A — OHRC Physical Projection Sanity Test  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report evaluates the sensitivity of the physical ray-terrain intersection to Digital Elevation Model (DEM) spatial resolution, comparing NASA LOLA `LDEM_80S_20M` (20 m/pixel) and `LDEM_875S_5M` (5 m/pixel) across the 9 deterministic sample rays of `OHRC_PAIR_01`.

### Key Experimental Findings:
- **Mean Elevation Difference ($h_{\text{5m}} - h_{\text{20m}}$):** **-0.01 meters** (Std dev: 0.62 m).
- **Mean 3D Intersection Displacement:** **0.42 meters** (Range: 0.02 m to 1.35 m).
- **Mean Horizontal Ground Displacement:** **0.11 meters** (Range: 0.00 m to 0.36 m).
- **Fraction of Delivered Pixel Scale ($5.0\text{ m}$):** Horizontal displacement averages **0.02x delivered pixel dimension** (sub-pixel precision).

> **Scientific Discipline:** Neither DEM resolution is declared 'better' or a 'winner.' Resolution is quantified strictly as an experimental parameter.

---

## 2. Deterministic Pixel-by-Pixel Comparative Telemetry

| Sample Name | Pixel $(u, v)$ | 20m Elev ($h_{20}$) | 5m Elev ($h_5$) | $\Delta h$ ($h_5 - h_{20}$) | 3D Displacement | Horiz Displacement | Lat / Lon (5m) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `CENTER` | `(312, 2436)` | $-948.3\text{ m}$ | $-948.0\text{ m}$ | **$+0.26\text{ m}$** | **$0.27\text{ m}$** | **$0.07\text{ m}$** | `-89.48677, 190.53904` |
| `TOP_MID` | `(312, 487)` | $-910.8\text{ m}$ | $-910.7\text{ m}$ | **$+0.10\text{ m}$** | **$0.10\text{ m}$** | **$0.03\text{ m}$** | `-89.48479, 228.36631` |
| `BOTTOM_MID` | `(312, 4384)` | $-673.5\text{ m}$ | $-674.8\text{ m}$ | **$-1.30\text{ m}$** | **$1.35\text{ m}$** | **$0.36\text{ m}$** | `-89.30209, 163.43413` |
| `LEFT_MID` | `(62, 2436)` | $-884.2\text{ m}$ | $-884.5\text{ m}$ | **$-0.27\text{ m}$** | **$0.28\text{ m}$** | **$0.07\text{ m}$** | `-89.52629, 188.97574` |
| `RIGHT_MID` | `(561, 2436)` | $-1001.5\text{ m}$ | $-1001.6\text{ m}$ | **$-0.15\text{ m}$** | **$0.15\text{ m}$** | **$0.04\text{ m}$** | `-89.44707, 191.86516` |
| `TOP_LEFT` | `(62, 487)` | $-861.9\text{ m}$ | $-861.9\text{ m}$ | **$+0.02\text{ m}$** | **$0.02\text{ m}$** | **$0.00\text{ m}$** | `-89.52385, 230.08361` |
| `TOP_RIGHT` | `(561, 487)` | $-1026.9\text{ m}$ | $-1026.7\text{ m}$ | **$+0.21\text{ m}$** | **$0.21\text{ m}$** | **$0.06\text{ m}$** | `-89.44553, 226.96231` |
| `BOTTOM_LEFT` | `(62, 4384)` | $-836.6\text{ m}$ | $-835.4\text{ m}$ | **$+1.22\text{ m}$** | **$1.27\text{ m}$** | **$0.34\text{ m}$** | `-89.33275, 160.96717` |
| `BOTTOM_RIGHT` | `(561, 4384)` | $-532.4\text{ m}$ | $-532.5\text{ m}$ | **$-0.15\text{ m}$** | **$0.16\text{ m}$** | **$0.04\text{ m}$** | `-89.27069, 165.67526` |

---

## 3. Physical Interpretation of Resolution Mismatch

1. **Hypsometric Consistency:** Regional elevation agreement between the 20m and 5m products across the 23.6 km x 15.2 km footprint is remarkably tight (mean $\Delta h = -0.01\text{ m}$, std dev $0.62\text{ m}$), confirming inter-dataset calibration.
2. **Impact on Forward Projection:** Vertical elevation differences translate into horizontal ground displacements of only $\approx 0.11\text{ m}$ (0.02x delivered $5\text{ m}$ pixel scale, sub-pixel).
3. **Conclusion for Phase 23B/C:** For the tested Pair 01 samples, the 20m and 5m DEMs produced sub-meter horizontal intersection differences.
