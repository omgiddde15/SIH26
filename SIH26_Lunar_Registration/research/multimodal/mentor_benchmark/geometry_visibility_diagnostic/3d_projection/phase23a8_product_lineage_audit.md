# Phase 23A.8 — Reference Raster Product Lineage & Provenance Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

Phase 23A.7 demonstrated that switching between the IAU and DE421 lunar frame realizations produces only $22.7 - 66.0\text{ m}$ of ground displacement ($1.04\% - 5.22\%$ of the observed residual). This audit investigates the **originating product lineage, sensor identity, and processing history** of the mentor reference rasters to determine how the reference canvas was generated.

> ### **Primary Finding on Product Lineage:**
> **Originating Sensor Identity:** **`UNKNOWN`** in embedded GeoTIFF tags.  
> **Delivery Context:** The delivered 5 m/px reference products are cartographically compatible with multiple lunar mapping products; their actual source product remains unverified.  
> **Provenance Non-Inference Policy:** Basemap provenance must NOT be inferred from: 5 m/px resolution, projection, radius, geographic extent, or visual appearance.  
> **Reference-Content Consistency:** **`100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP`** (7,089,556 / 7,089,556 pixels, `Mean diff = 0.0000`). The two delivered reference rasters are identical over the verified overlap, consistent with a common static basemap or identical upstream source. This does not by itself establish the absolute geodetic realization of that common reference.

---

## 2. Embedded GeoTIFF Metadata Audit Matrix

| Pair ID | Reference Raster Filename | Dimensions (W × H) | GSD (m/px) | GeoTIFF Software Tag (305) | Image Description (270) | Artist (315) | Date/Time (306) | Lineage Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif` | 5916 × 4232 | 5.000 m/px | `None` | `None` | `None` | `None` | **`UNKNOWN`** |
| **`OHRC_PAIR_02`** | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif` | 2593 × 6279 | 5.000 m/px | `None` | `None` | `None` | `None` | **`UNKNOWN`** |
| **`OHRC_PAIR_03`** | `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif` | 2416 × 6316 | 5.000 m/px | `None` | `None` | `None` | `None` | **`UNKNOWN`** |
| **`OHRC_PAIR_04`** | `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif` | 3164 × 6322 | 5.000 m/px | `None` | `None` | `None` | `None` | **`UNKNOWN`** |

---

## 3. Accompanying Delivery Archive & Label Audit

| Pair ID | Accompanying XML Label | Product Declared in XML | Declared Resolution | XML `ReferenceUsed` Tag | Audit Finding |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **`OHRXXD18CHO235`** | `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03.xml` | `OHRXXD18CHO2359602NNNN24342131250969_V1_0_03` (OHRC Strip) | 0.26 m | `System` | Label applies to **OHRC source strip**, NOT reference raster. |
| **`OHRXXD18CHO243`** | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01.xml` | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01` (OHRC Strip) | 0.27 m | `System` | Label applies to **OHRC source strip**, NOT reference raster. |
| **`OHRXXD18CHO247`** | `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02.xml` | `OHRXXD18CHO2470502NNNN25067152549847_V2_1_02` (OHRC Strip) | 0.25 m | `System` | Label applies to **OHRC source strip**, NOT reference raster. |
| **`OHRXXD18CHO273`** | `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00.xml` | `OHRXXD18CHO2736702NNNN25285183733061_V1_0_00` (OHRC Strip) | 0.23 m | `System` | Label applies to **OHRC source strip**, NOT reference raster. |

> **Key Architectural Separation:**
> The PDS4 XML files delivered in `data_for_sih_2026/ohrc/` document the **moving source strips** (Chandrayaan-2 OHRC Level-1 `SelenoTagging` products with `<ReferenceUsed>System</ReferenceUsed>`).
> No XML labels, processing logs, or calibration reports were delivered for the **target reference rasters**.

---

## 4. Product Lineage & Empirical Reference-Content Consistency Audit

Because `OHRC_PAIR_02` (acquired Feb 8, 2025) and `OHRC_PAIR_03` (acquired Mar 8, 2025) observe overlapping terrain near $84.95^\circ\text{S}, 26^\circ\text{E}$, their reference rasters were directly compared across their intersection polygon:

- **Overlap Bounding Box:** Easting `[67,338.0, 73,558.0] m`, Northing `[121,552.0, 150,047.0] m`.
- **Overlap Dimensions:** `1244 × 5699 pixels` (7,089,556 pixels total).
- **Identical Pixels:** **`7,089,556 / 7,089,556 (100.00%)`** (100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP).
- **Mean Pixel Difference:** **`0.0000`** (RMS Diff: `0.0000`).
- **Min / Max Pixel Difference:** `0.0 / 0.0`.

> ### **Scientific Implication & Provenance Policy:**
> 1. **Reference-Content Consistency:** The two delivered reference rasters are identical over the verified overlap (7,089,556 / 7,089,556 pixels identical, 100.00%), consistent with a common static basemap or identical upstream source. This does not by itself establish the absolute geodetic realization of that common reference.
> 2. **Differential Translation Attribution:** The differential 435.01 m translation between Pair 02 and Pair 03 is not attributable to a difference between the two delivered reference raster contents over their verified common overlap. A common absolute geodetic offset shared by the reference raster remains possible because the reference geodetic realization is unresolved.
> 3. **Non-Inference Rule:** Basemap provenance must NOT be inferred from 5 m/px resolution, projection, radius, geographic extent, or visual appearance.
