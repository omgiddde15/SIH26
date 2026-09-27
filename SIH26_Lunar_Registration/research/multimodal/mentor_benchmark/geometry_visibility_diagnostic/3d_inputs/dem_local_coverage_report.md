# Phase 22.5 — Local DEM Coverage & Spatial Reference Verification Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.5 — Binary Input Ingestion & Physical Coverage Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report establishes the local acquisition, spatial coverage verification, and binary format integrity of the Digital Elevation Model (DEM) inputs required for `OHRC_PAIR_01` through `OHRC_PAIR_04`.

### Key Conclusions:
1. **Universal 20m Coverage:** NASA LOLA GDR `LDEM_80S_20M` ($20.0\text{ m/pixel}$, 80°S–90°S) provides **100.0% spatial coverage** across all four mentor OHRC pairs.
2. **High-Resolution 5m Demarcation:** NASA LOLA GDR `LDEM_875S_5M` ($5.0\text{ m/pixel}$, 87.5°S–90°S) covers **`OHRC_PAIR_01` ONLY** ($100.0\%$). It covers **$0.0\%$** of Pairs 02, 03, and 04, which are located north of 87.5°S.
3. **Local Binary Ingestion:** The exact binary spatial subsets required for all four pairs have been downloaded from NASA PDS via HTTP Range requests and verified locally:
   - `LDEM_80S_20M_pair01_subset.bin` (799 lines $\times$ 1220 samples, 1.86 MB)
   - `LDEM_80S_20M_pair02_subset.bin` (1310 lines $\times$ 389 samples, 0.97 MB)
   - `LDEM_80S_20M_pair03_subset.bin` (1320 lines $\times$ 345 samples, 0.87 MB)
   - `LDEM_80S_20M_pair04_subset.bin` (1321 lines $\times$ 532 samples, 1.34 MB)
   - `LDEM_875S_5M_pair01_subset.bin` (3114 lines $\times$ 4797 samples, 28.49 MB)
4. **Experimental Property Discipline:** Spatial resolution ($5\text{ m}$ vs $20\text{ m}$) is treated strictly as an experimental property. $5\text{ m}$ is not assumed to be automatically superior, nor is $20\text{ m}$ assumed to be automatically sufficient.

---

## 2. Verified Geographic Footprints & Product Compatibility

Footprints calculated directly from the mentor PDS4 XML metadata:

| Pair ID | Bounding Latitude | Bounding Longitude | Ground Extent ($W \times H$) | `LDEM_80S_20M` Coverage | `LDEM_875S_5M` Coverage | Required Local DEM Asset |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **`OHRC_PAIR_01`** | $[-89.47^\circ, -89.25^\circ]$ | $[158.66^\circ, 245.78^\circ]$ | $23.6\text{ km} \times 15.2\text{ km}$ | **100.0%** | **100.0%** | `LDEM_80S_20M_pair01_subset.bin` & `LDEM_875S_5M_pair01_subset.bin` |
| **`OHRC_PAIR_02`** | $[-85.36^\circ, -84.54^\circ]$ | $[26.72^\circ, 31.18^\circ]$ | $7.0\text{ km} \times 25.4\text{ km}$ | **100.0%** | **0.0%** (North of 87.5°S) | `LDEM_80S_20M_pair02_subset.bin` |
| **`OHRC_PAIR_03`** | $[-85.37^\circ, -84.54^\circ]$ | $[24.21^\circ, 28.47^\circ]$ | $6.1\text{ km} \times 25.6\text{ km}$ | **100.0%** | **0.0%** (North of 87.5°S) | `LDEM_80S_20M_pair03_subset.bin` |
| **`OHRC_PAIR_04`** | $[-84.60^\circ, -83.76^\circ]$ | $[30.82^\circ, 34.18^\circ]$ | $9.8\text{ km} \times 25.6\text{ km}$ | **100.0%** | **0.0%** (North of 87.5°S) | `LDEM_80S_20M_pair04_subset.bin` |

---

## 3. Comparative Evaluation for `OHRC_PAIR_01`: 20m vs. 5m

Because `OHRC_PAIR_01` is situated near the lunar south pole ($89.36^\circ\text{S}$), both LOLA GDR products encompass the entire swath. Both products have been downloaded and analyzed without resampling:

| Parameter | `LDEM_80S_20M` (Pair 01 Subset) | `LDEM_875S_5M` (Pair 01 Subset) | Ratio / Difference |
| :--- | :--- | :--- | :--- |
| **Pixel Resolution** | $20.000\text{ m/pixel}$ | $5.000\text{ m/pixel}$ | $4.0\times$ linear sampling density |
| **Grid Dimensions** | $799\text{ lines} \times 1220\text{ samples}$ | $3114\text{ lines} \times 4797\text{ samples}$ | $15.3\times$ total pixel count |
| **File Size (Binary)** | $1,949,560\text{ bytes}$ ($1.86\text{ MB}$) | $29,875,716\text{ bytes}$ ($28.49\text{ MB}$) | $15.3\times$ storage volume |
| **Minimum Elevation** | $-1846.0\text{ meters}$ | $-1822.0\text{ meters}$ | $\Delta = 24.0\text{ m}$ (crater floor) |
| **Maximum Elevation** | $+863.5\text{ meters}$ | $+808.0\text{ meters}$ | $\Delta = 55.5\text{ m}$ (crater rim) |
| **Mean Elevation** | $-772.6\text{ meters}$ | $-776.6\text{ meters}$ | $\Delta = 4.0\text{ m}$ (regional agreement) |
| **Elevation Standard Dev** | $643.2\text{ meters}$ | $648.7\text{ meters}$ | Topographic variance preserved |

### Observations:
- Both datasets exhibit near-identical regional hypsometry (mean elevation $-772.6\text{ m}$ vs $-776.6\text{ m}$).
- The 5m DEM exhibits steeper local slope gradients along crater rims due to reduced spatial averaging over the 20m footprint.
- In subsequent experimental modeling, both DEMs will allow evaluating whether DEM resolution mismatch ($20\text{ m}$ vs $5\text{ m}$) materially impacts ray intersection accuracy along high-relief terrain features.

---

## 4. Local Binary Files Manifest & Checksums

| File Name | Format | Dimensions | Byte Size | SHA-256 Checksum | Local Path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `LDEM_80S_20M_pair01_subset.bin` | Little-Endian `int16` | $799 \times 1220$ | 1,949,560 | `84ff10df657c12c8bdf7cf2d6a59be5fae3e0477be71676ea3d2f9540bce3ae1` | `downloads/` |
| `LDEM_80S_20M_pair02_subset.bin` | Little-Endian `int16` | $1310 \times 389$ | 1,019,180 | `dbef9ca3e3eea9a2ce0839e55331cbafad785055ba22756f7e436814c9e4726b` | `downloads/` |
| `LDEM_80S_20M_pair03_subset.bin` | Little-Endian `int16` | $1320 \times 345$ | 910,800 | `0dec157921e9625f385c67e91404ea5d710fbe052f55877840134b2f153f3195` | `downloads/` |
| `LDEM_80S_20M_pair04_subset.bin` | Little-Endian `int16` | $1321 \times 532$ | 1,405,544 | `2bffb92dc93f01b7a2d6778f6143c1eeeb8d3fc74d472251121d51b329fcba31` | `downloads/` |
| `LDEM_875S_5M_pair01_subset.bin` | Little-Endian `int16` | $3114 \times 4797$ | 29,875,716 | `bd5ff2ad0f80cd94d3f3f50435a2982d6ca1f26a11e138a06e23b092306d1dbf` | `downloads/` |

---

## 5. Technical Verdict

- `OHRC_PAIR_01`: `DEM_COVERAGE = FULL` (Both 20m and 5m verified locally)
- `OHRC_PAIR_02`: `DEM_COVERAGE = FULL` (20m verified locally; 5m not applicable)
- `OHRC_PAIR_03`: `DEM_COVERAGE = FULL` (20m verified locally; 5m not applicable)
- `OHRC_PAIR_04`: `DEM_COVERAGE = FULL` (20m verified locally; 5m not applicable)
