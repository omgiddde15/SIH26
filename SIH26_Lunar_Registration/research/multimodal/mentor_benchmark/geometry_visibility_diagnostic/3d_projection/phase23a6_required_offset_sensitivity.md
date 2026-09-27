# Phase 23A.6 — Required Position Offset Sensitivity Extrapolation Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.6 — Rigid Geodetic / Frame Offset Reconciliation  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

Using the controlled sensitivity scaling factors rigorously measured in Phase 23A.5, this report evaluates the hypothetical positional displacement magnitude required to reproduce the observed source-to-map residuals.

### Mandatory Nomenclature Rule:
> This value is labeled strictly as **`REQUIRED-OFFSET MAGNITUDE`**.
> It must **NOT** be labeled as *“true ephemeris error”*, *“SPK error”*, or *“spacecraft position error”*, as no independent ground-truth trajectory measurement is performed.

---

## 2. Sensitivity Scaling Basis from Phase 23A.5

In Phase 23A.5, spacecraft position perturbations produced the following linear ground displacement ratios:
- **Along-track position:** Ground displacement factor = **$1.00334\text{ m ground / m orbit}$** ($1:1$ horizontal translation).
- **Cross-track position:** Ground displacement factor = **$1.00000\text{ m ground / m orbit}$** ($1:1$ horizontal translation).
- **Radial altitude:** Ground displacement factor = **$0.2752\text{ m ground / m altitude}$** (scales with $\tan(\theta_{\text{emission}})$).

---

## 3. Extrapolated Required Offset Magnitudes

| Pair ID | Observed Translation Mag | Translation Azimuth | Vector Orientation | 1-D Along-Track Equivalent Under Phase 23A.5 Sensitivity | Along-Track Interpretation Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | **2158.4 m** | 127.16° | Map Polar Stereographic | **2151.2 m** | **UNVERIFIED** |
| **`OHRC_PAIR_02`** | **1264.9 m** | 12.95° | Map Polar Stereographic | **1260.7 m** | **UNVERIFIED** |
| **`OHRC_PAIR_03`** | **1699.9 m** | 9.30° | Map Polar Stereographic | **1694.3 m** | **UNVERIFIED** |
| **`OHRC_PAIR_04`** | **2181.1 m** | 16.72° | Map Polar Stereographic | **2173.8 m** | **UNVERIFIED** |

> **Methodological Statement:**  

> *“These values are scalar equivalents obtained by applying the Phase 23A.5 along-track sensitivity coefficient to the observed translation magnitude. Because spacecraft ground-track alignment of the residual vectors was not independently established in Phase 23A.6, these values are not interpreted as actual spacecraft along-track position errors.”*

---

## 4. Scientific Discussion & Bounds

1. **Magnitude Range:** The 1-D along-track equivalents under Phase 23A.5 sensitivity span **$1,260.7\text{ m}$ to $2,173.8\text{ m}$** (designated strictly as hypothetical `REQUIRED-OFFSET MAGNITUDE`).
2. **Residual Azimuth Distribution:** Pairs 02–04 have mutually similar residual-vector azimuths ($9.30^\circ - 16.72^\circ$); their alignment with the spacecraft ground track is not independently established by the present report.
3. **Physical Interpretation:** While Chandrayaan-2 reconstructed SPK ephemeris and LRO LOLA/LROC reference basemaps are both derived from high-precision orbit determination, systematic baseline differences between Indian DSN tracking solutions and LRO GRAIL-based tracking can introduce offsets of hundreds of meters to kilometers.
4. **Composite Context:** As established in Phase 23A.5, this required offset represents a mathematical equivalence under the sensitivity model, but may in reality represent a composite effect of orbit datum, planar tiepoint approximations in mentor metadata, and reference mosaic georeferencing shifts.
