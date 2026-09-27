# Phase 23A.8 — Reference Raster to MOON_ME_DE421 Linkage Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.8 — Reference Raster Geodetic Provenance & Map-Generation Audit  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit assesses whether the mentor reference rasters are directly tied to the NASA NAIF authoritative `MOON_ME_DE421` frame realization, and whether a documented mathematical transformation exists between them.

> ### **Primary Linkage Finding:**
> # **`GEODETIC_LINK_NOT_VERIFIED`**  
> # **`NO_DOCUMENTED_TRANSFORM_IDENTIFIED_IN_AUDITED_INPUTS`**  
> No documented transformation was identified in the audited local inputs and accompanying product material.

---

## 2. Multi-System Linkage Traceability Matrix

| System 1 | System 2 | Connecting Mechanism / Kernel | Measured Linkage Status | Discrepancy Scale |
| :--- | :--- | :--- | :---: | :---: |
| **OHRC Instrument** | `IAU_MOON` | SPICE CK (`ch2_att_*.bc`), FK (`ch2_v01.tf`), SCLK (`ch2_sclk_v1.tsc`), PCK (`pck00010.tpc`) | **`VERIFIED`** | Exact forward rays |
| **`IAU_MOON`** | `MOON_ME_DE421` | NAIF Binary PCK (`moon_pa_de421_1900-2050.bpc`), FK (`moon_080317.tf`) | **`VERIFIED`** | $4.82" - 11.03"$ ($22.7 - 66.0\text{ m}$) |
| **LOLA DEM** | `MOON_ME_DE421` | NASA GSFC Orbit Solution / PDS Label declaration | **`VERIFIED`** | Native DE421 trajectory |
| **Mentor Reference Raster** | `MOON_ME_DE421` | Absent from metadata | **`UNKNOWN`** | $1,295.3 - 2,203.3\text{ m}$ residual |
| **Mentor Reference Raster** | `IAU_MOON` | Absent from metadata | **`UNKNOWN`** | $1,264.9 - 2,181.1\text{ m}$ residual |

---

## 3. Comparison of Uncertainties Against the Observed Residual

| Uncertainty Source | Published / Measured Magnitude | Relative Scale vs Residual | Classification |
| :--- | :---: | :---: | :---: |
| **Authoritative Frame Shift (`IAU_MOON` $\leftrightarrow$ `MOON_ME_DE421`)** | **$22.7 - 66.0\text{ m}$** | $1.04\% - 5.22\%$ of residual | **`NOT_SUFFICIENT_TO_EXPLAIN`** |
| **Published Accuracies of Other Lunar Products (LROC NAC / LOLA)** | Contextual only ($\le 20 - 50\text{ m}$) | Contextual literature only | Published accuracies of other lunar cartographic products — contextual only; not an established uncertainty bound for the mentor reference raster because its lineage remains unresolved. |
| **System-Corrected Pointing Uncertainty (ISRO CH-2 Literature)** | Nominal $\sim 100 - 500\text{ m}$ range | Contextual literature only | Does not independently account for the full residual under the cited bound; combined error contribution remains unresolved. |
| **Delivered Mentor Canvas Georeferencing Offset** | **`UNQUANTIFIED`** | Up to $100\%$ of residual | **`POTENTIALLY_MATERIAL`** |

> ### **Evaluation of Geodetic Uncertainty:**
> 1. **Authoritative planetary frame differences:** **`TOO SMALL TO EXPLAIN THE RESIDUAL`** ($22.7 - 66.0\text{ m} \ll 1,265 - 2,181\text{ m}$).
> 2. **Published accuracies of other lunar cartographic products:** Contextual only; not an established uncertainty bound for the mentor reference raster because its lineage remains unresolved.
> 3. **System-corrected pointing uncertainty:** Does not independently account for the full residual under the cited bound; combined error contribution remains unresolved.
> 4. **Delivered reference canvas georeferencing:** **`UNQUANTIFIED`** in metadata and **`POTENTIALLY MATERIAL`** as an uncalibrated source of the kilometre-scale discrepancy.
