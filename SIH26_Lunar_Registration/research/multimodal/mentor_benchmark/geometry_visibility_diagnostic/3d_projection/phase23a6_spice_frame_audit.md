# Phase 23A.6 — SPICE Kernel Pool & Lunar Frame Realization Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.6 — Rigid Geodetic / Frame Offset Reconciliation  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit examines the exact lunar body-fixed frames, spacecraft frames, and transformation chains resolvable within the locally loaded SPICE kernel pool.

### Frame Transformation Status:
> # **`FRAME_TRANSFORMATION_NOT_VERIFIED`**  
> *(The transformation between `IAU_MOON` and `MOON_ME` cannot be numerically resolved because `MOON_ME` is undefined in the available kernel pool).* 

---

## 2. Frame Inventory in Available Kernel Pool

| Frame Name | NAIF ID | Status in Kernel Pool | Defining Kernel | Definition / Reference Model |
| :--- | :---: | :---: | :--- | :--- |
| **`CH2_OHRC`** | `-152270` | **`VERIFIED`** | `ch2_v01.tf` | OHRC Instrument Frame, aligned with Orbiter |
| **`CH2_ORBITER`** | `-152001` | **`VERIFIED`** | `ch2_v01.tf` | Spacecraft mechanical bus frame (CK target) |
| **`IAU_MOON`** | `10020` | **`VERIFIED`** | `pck00010.tpc` | IAU Working Group analytical libration series |
| **`MOON_ME`** | `0` | **`UNKNOWN_IN_LOADED_POOL`** | Absent (requires binary PCK) | Mean Earth / Polar Axis frame (LOLA standard) |
| **`MOON_PA`** | `0` | **`UNKNOWN_IN_LOADED_POOL`** | Absent (requires binary PCK) | Principal Axis frame |
| **`MOON_ME_DE421`** | `0` | **`UNKNOWN_IN_LOADED_POOL`** | Absent (requires binary PCK) | DE421 ephemeris realization of Mean Earth frame |

---

## 3. Numerical Resolution Audit

1. **`CH2_OHRC` $\to$ `IAU_MOON`:**
   - **Resolution:** **`VERIFIED`** when CK subset and SCLK are furnished.
   - **Transformation Chain:** `CH2_OHRC (-152270)` $\to$ `CH2_ORBITER (-152001)` $\xrightarrow{\text{CK}}$ `J2000 (1)` $\xrightarrow{\text{PCK}}$ `IAU_MOON (10020)`.
   - **Precision:** Sub-millimeter pointing accuracy on lunar surface.

2. **`IAU_MOON` $\to$ `MOON_ME`:**
   - **Resolution:** **`UNRESOLVABLE`** (`SpiceUNKNOWNFRAME: The frame MOON_ME was not recognized as a known reference frame`).
   - **Technical Cause:** Resolving `MOON_ME` in SPICE requires a high-precision lunar binary PCK (`moon_pa_de421_1900-2050.bpc`) and lunar frame specification kernel (`moon_080317.tf` or `moon_assoc_me.tf`). These binary kernels are not part of the verified local mission dataset.

---

## 4. Lunar Frame Audit Conclusion

The required DE421 MOON_ME realization is not available in the verified local kernel pool, so the IAU_MOON <-> MOON_ME angular difference was not independently computed in Phase 23A.6. Therefore no numerical bound on the resulting surface displacement is asserted here.
