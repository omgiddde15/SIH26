# Phase 23A.9 — Reference Raster Content Fingerprint & Grid Analysis

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.9 — External Reference Product Provenance Identification  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Discrete Raster Grid Alignment Analysis

An exhaustive mathematical audit of the ModelTiepointTag $(i=0, j=0, k=0, E_0, N_0, 0)$ across all four mentor reference rasters reveals that all four rasters share an identical discrete sampling grid:

| Mentor Reference Raster | Width × Height (px) | Easting Origin $E_0$ (m) | Northing Origin $N_0$ (m) | $E_0 \pmod 5$ | $N_0 \pmod 5$ | Grid Offset $[\Delta E, \Delta N]$ | Master Grid Indices $[k_x, k_y]$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | 5916 × 4232 | -19187.0 | -3603.0 | 3.0 | 2.0 | `[+3.0 m, +2.0 m]` | `[-3838, -721]` |
| **`OHRC_PAIR_02`** | 2593 × 6279 | 67338.0 | 150047.0 | 3.0 | 2.0 | `[+3.0 m, +2.0 m]` | `[13467, 30009]` |
| **`OHRC_PAIR_03`** | 2416 × 6316 | 61478.0 | 153132.0 | 3.0 | 2.0 | `[+3.0 m, +2.0 m]` | `[12295, 30626]` |
| **`OHRC_PAIR_04`** | 3164 × 6322 | 86683.0 | 164952.0 | 3.0 | 2.0 | `[+3.0 m, +2.0 m]` | `[17336, 32990]` |

> ### **Mathematical Grid Deduction:**
> Every pixel boundary across all four independent reference rasters satisfies the exact linear Diophantine relation:
> $$E_{\text{pixel}}(i) = 3.0\text{ m} + 5.0 \cdot (k_x + i)$$
> $$N_{\text{pixel}}(j) = 2.0\text{ m} - 5.0 \cdot (-k_y + j)$$
> where $k_x, k_y \in \mathbb{Z}$.
> This mathematical invariant **proves that all four delivered reference rasters are phase-aligned to the same 5 m projected coordinate lattice**. The modulo-5 tiepoint analysis demonstrates common grid phase, not common master-file provenance.

---

## 2. Empirical Overlap Fingerprint Verification (Pair 02 vs Pair 03)

The verified overlap analysis between `OHRC_PAIR_02` (acquired Feb 8, 2025) and `OHRC_PAIR_03` (acquired Mar 8, 2025) is strictly preserved:
- **Overlap Polygon:** Easting `[67,338.0, 73,558.0] m`, Northing `[121,552.0, 150,047.0] m`.
- **Overlap Dimensions:** `1,244 × 5,699 pixels` (7,089,556 pixels total).
- **Exact Identical Pixel Count:** **`7,089,556 / 7,089,556 pixels (100.00%)`** (**`100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP`**).
- **Pixel Difference Statistics:** `Mean diff = 0.0000`, `Min diff = 0.0`, `Max diff = 0.0`, `RMS diff = 0.0000`.

> ### **Content Fingerprint Implication:**
> 1. **Reference-Content Consistency:** The identical Pair 02/03 overlap (**`100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP`**, 7,089,556 / 7,089,556 pixels, Mean diff = 0.0000, RMS diff = 0.0000) is consistent with both references drawing from common pre-existing reference content; the upstream acquisition and mosaic-generation history remains unverified.
> 2. **Absence of Candidate Raster:** Because no external candidate product was delivered in the benchmark package to compare pixel-for-pixel against this 7.08-megapixel fingerprint, content-level confirmation of an external candidate is impossible without unauthorized data acquisition.
> 3. **Content Match Classification:** `CONTENT_MATCH_STATUS = UNVERIFIED` for external candidates; `MATCH` for the local delivery container.
