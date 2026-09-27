# Phase 23A.9 — Candidate Geodetic Realization & Frame Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.9 — External Reference Product Provenance Identification  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Candidate Geodetic Realizations & Control Ties

| Candidate ID | Product Family | Stated Geodetic Realization | Control Network / Datum | Positional Uncertainty | Link to `MOON_ME_DE421` |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **CAND_01** | ISRO TMC-2 Single Strip | Selenocentric / `IAU_MOON` | Orbital telemetry (`SelenoTagging`) | Nominal ~100–500 m | **`NOT VERIFIED`** |
| **CAND_02** | ISRO TMC-2 Polar Mosaic | `UNKNOWN` (Internal SAC) | Multi-strip tiepoints; LOLA unconfirmed | `UNQUANTIFIED` | **`NOT VERIFIED`** |
| **CAND_03** | NASA LROC NAC 1m Mosaic | `MOON_ME_DE421` | LOLA altimetry tracks + bundle adj. | $\le 20 - 50\text{ m}$ | **`VERIFIED FOR CANDIDATE`** (Candidate rejected on scale) |
| **CAND_04** | NASA LOLA LDEM 5m | `MOON_ME_DE421` | Laser crossover minimization | $\le 10 - 20\text{ m}$ | **`VERIFIED FOR CANDIDATE`** (Candidate rejected on modality) |
| **CAND_07** | Mentor Delivery Container | Generic `GCS_Moon` / `D_Moon` | Unrecorded in GeoTIFF tags | `UNQUANTIFIED` | **`NOT VERIFIED`** |

---

## 2. Geodetic Consequence of Unresolved Status

Because no candidate reference product reaches positive product-level identification, the reference geodetic realization remains strictly unresolved:

> # **`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`**  
> # **`REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED`**  

### Key Scientific Principles Enforced:
1. **No Imputed Realization:** The reference raster cannot be assumed to reside in `MOON_ME_DE421` merely because it is cartographically projected with $R=1,737,400\text{ m}$.
2. **No Empirical Fitting:** Fitting an empirical translation $\vec{T} = [\Delta x, \Delta y]$ between the OHRC physical projection and the mentor reference raster to make the residual vanish is **strictly prohibited**.
3. **Unanchored Benchmark:** Without an established tie between the mentor reference canvas and `MOON_ME_DE421`, the residual cannot be partitioned between spacecraft pointing error and basemap georeferencing offset.
