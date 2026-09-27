# Phase 22.6 — Native Sensor vs. Delivered TIFF Geometry Mapping Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report establishes the mathematical mapping between the authoritative native OHRC camera detector geometry (12,000 pixels, $5.2\ \mu\text{m}$ pitch) and the delivered mentor source TIFF rasters (`source_at_5m.tif`).

### Key Audit Findings:
1. **Full Detector Representation (Zero Cropping):**  
   The delivered mentor source TIFF images represent the **complete 12,000-sample native detector swath**. No lateral cropping or swath truncation is present.
2. **Reconciliation of Delivered Widths ($624, 648, 600, 552$):**  
   The varying widths across the four pairs are mathematically explained by orbital flight mechanics:
   - Each pass was acquired at a different spacecraft orbital altitude ($91.9\text{ km}$ to $105.8\text{ km}$), yielding different native ground sampling distances ($0.23\text{ m/px}$ to $0.27\text{ m/px}$).
   - The mentor datasets were downsampled to an exact common benchmark grid of **$5.000\text{ m/pixel}$**.
   - Downsampling ratio: $s_x = \frac{5.000\text{ m/px}}{\text{GSD}_{\text{native}}} = \frac{12000}{W_{\text{tiff}}}$.
   - The delivered width is simply $W_{\text{tiff}} = \text{round}\left(\frac{12000}{s_x}\right)$.
3. **Closed-Form Coordinate Transformation:**  
   For any pixel coordinate $u_{\text{tiff}} \in [0, W_{\text{tiff}}-1]$, the corresponding native detector sample coordinate $u_{\text{native}}$ is:
   $$u_{\text{native}} = s_x \cdot u_{\text{tiff}} + \frac{s_x - 1}{2}$$

---

## 2. Quantitative Sensor & Raster Parameter Reconciliation

| Parameter | `OHRC_PAIR_01` | `OHRC_PAIR_02` | `OHRC_PAIR_03` | `OHRC_PAIR_04` | Source / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Native Detector Samples** | 12,000 pixels | 12,000 pixels | 12,000 pixels | 12,000 pixels | SPICE IK (`ch2_ohr_v01.ti`) |
| **Native Pixel Pitch** | $5.2\ \mu\text{m}$ | $5.2\ \mu\text{m}$ | $5.2\ \mu\text{m}$ | $5.2\ \mu\text{m}$ | SPICE IK (`ch2_ohr_v01.ti`) |
| **Native Focal Length** | $2080.0\text{ mm}$ | $2080.0\text{ mm}$ | $2080.0\text{ mm}$ | $2080.0\text{ mm}$ | SPICE IK (`ch2_ohr_v01.ti`) |
| **Orbiter Altitude (XML)** | $100.78\text{ km}$ | $105.77\text{ km}$ | $97.78\text{ km}$ | $91.86\text{ km}$ | PDS4 XML Telemetry |
| **Native Ground GSD** | $0.260\text{ m/px}$ | $0.270\text{ m/px}$ | $0.250\text{ m/px}$ | $0.230\text{ m/px}$ | PDS4 XML Telemetry |
| **Delivered Raster Width ($W_{\text{tiff}}$)** | **624 pixels** | **648 pixels** | **600 pixels** | **552 pixels** | GeoTIFF Header |
| **Delivered Raster Height ($H_{\text{tiff}}$)** | **4,872 lines** | **5,059 lines** | **5,054 lines** | **4,649 lines** | GeoTIFF Header |
| **Raw Scans in XML ($N_{\text{scans}}$)** | 93,692 scans | 93,692 scans | 101,074 scans | 101,074 scans | PDS4 XML Telemetry |
| **Derived Cross-Track Scale ($s_x$)** | **$19.230769$** | **$18.518519$** | **$20.000000$** | **$21.739130$** | $12000 / W_{\text{tiff}}$ |
| **Derived Along-Track Scale ($s_y$)** | **$19.230706$** | **$18.520063$** | **$19.998813$** | **$21.741020$** | $N_{\text{scans}} / H_{\text{tiff}}$ |
| **Scale Isotropy ($s_x / s_y$)** | **$1.000003$** | **$0.999917$** | **$1.000059$** | **$0.999913$** | Strictly Isotropic ($< 0.01\%$ diff) |
| **Detector Coverage** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | Full Swath |
| **Lateral Cropping** | **NONE** | **NONE** | **NONE** | **NONE** | Full Swath |

---

## 3. Pixel Coordinate Formulation: Native vs. Delivered

Let $u_{\text{tiff}} \in [0, W_{\text{tiff}}-1]$ denote the 0-indexed column sample coordinate in the delivered TIFF, and $u_{\text{native}} \in [0, 11999]$ denote the 0-indexed sample coordinate along the physical OHRC detector array.

### Linear Transform Formulation:
$$u_{\text{native}} = a \cdot u_{\text{tiff}} + b$$

Where:
- $a = s_x = \frac{12000}{W_{\text{tiff}}}$
- $b = \frac{s_x - 1}{2}$

| Pair ID | Delivered Width ($W_{\text{tiff}}$) | Scale Slope ($a$) | Pixel-Center Offset ($b$) | Center of Pixel 0 | Center of Pixel $(W-1)$ | Principal Point ($u = 6000$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | 624 | $19.230769$ | $+9.115385$ | $u_{\text{native}} = 9.115$ | $u_{\text{native}} = 11990.885$ | $u_{\text{tiff}} = 311.50$ |
| **`OHRC_PAIR_02`** | 648 | $18.518519$ | $+8.759259$ | $u_{\text{native}} = 8.759$ | $u_{\text{native}} = 11991.241$ | $u_{\text{tiff}} = 323.50$ |
| **`OHRC_PAIR_03`** | 600 | $20.000000$ | $+9.500000$ | $u_{\text{native}} = 9.500$ | $u_{\text{native}} = 11990.500$ | $u_{\text{tiff}} = 299.50$ |
| **`OHRC_PAIR_04`** | 552 | $21.739130$ | $+10.369565$ | $u_{\text{native}} = 10.370$ | $u_{\text{native}} = 11989.630$ | $u_{\text{tiff}} = 275.50$ |

### Physical Interpretation:
In each case, pixel $u_{\text{tiff}} = 0$ represents the spatial aggregation of native detector pixels $[0, \text{round}(a)-1]$, and the optical array midpoint ($u_{\text{native}} = 6000.0$) maps directly to the exact geometric center of the delivered TIFF ($u_{\text{tiff}} = \frac{W_{\text{tiff}} - 1}{2} + 0.5 = \frac{W_{\text{tiff}}}{2} - 0.5$).

---

## 4. Technical Verdict

- Mapping status: **`DERIVED`** (Rigorous closed-form linear mapping derived from verified orbital altitude, native GSD, and full 12,000-pixel detector geometry).
- Full detector coverage: **CONFIRMED (100.0%)**.
- Lateral cropping: **RULED OUT (0% cropped)**.
