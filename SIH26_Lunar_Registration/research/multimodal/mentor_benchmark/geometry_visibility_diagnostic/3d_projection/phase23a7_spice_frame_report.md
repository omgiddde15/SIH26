# Phase 23A.7 — SPICE Frame & DE421 Lunar Realization Audit Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.7 — Frame / Geodetic Reconciliation Review  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Executive Summary

This audit definitively resolves the frame-chain question left open by Phase 23A.6: **Can the authoritative DE421 lunar frame realization be loaded and resolved in SPICE?**

By furnishing the official NASA NAIF generic lunar orientation kernels (`moon_080317.tf`, `moon_pa_de421_1900-2050.bpc`, and `de421.bsp`) alongside the verified Chandrayaan-2 mission kernels, all primary spacecraft and lunar frames are now **100% resolvable and verified**.

> ### **Overall Frame Status:** **`FRAME_VERIFIED`**
> The transformation between `IAU_MOON` and `MOON_ME_DE421` is numerically computable and strictly reversible ($|\mathbf{R}\mathbf{R}^T - \mathbf{I}| < 3.4 \times 10^{-16}$).

---

## 2. Authoritative Kernel Inventory & Provenance

| Filename | Kernel Type | File Size | SHA-256 Hash | Download Date | Time Coverage | Source URL / Repository |
| :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| **`moon_080317.tf`** | FK (Frames Kernel) | 21,437 B | `78732477b96f9863...` | 2026-09-24 | Permanent definition | [moon_080317.tf](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf) |
| **`moon_pa_de421_1900-2050.bpc`** | Binary PCK | 1,770,496 B | `656f90616403d75a...` | 2026-09-24 | 1900-01-01 to 2050-01-01 | [moon_pa_de421_1900-2050.bpc](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de421_1900-2050.bpc) |
| **`de421.bsp`** | SPK (Planetary Ephemeris) | 16,790,528 B | `08b20db2ae224886...` | 2026-09-24 | 1900-01-01 to 2050-01-01 | [de421.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp) |
| **`naif0012.tls`** | LSK (Leapseconds Kernel) | 5,257 B | `25a242fc719114ae...` | 2026-09-23 | 1972-01-01 to 2026+ indefinite | [naif0012.tls](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls) |
| **`pck00010.tpc`** | PCK (Planetary Constants) | 126,143 B | `9a0a03ff265eb457...` | 2026-09-23 | Analytical models | [pck00010.tpc](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00010.tpc) |
| **`ch2_v01.tf`** | FK (Frames Kernel) | 13,382 B | `bc0b98eb6fbf5d52...` | 2026-09-23 | Mission lifetime | [ch2_v01.tf](ISRO ISSDC Chandrayaan-2 SPICE PDS4 Archive) |
| **`ch2_sclk_v1.tsc`** | SCLK (Spacecraft Clock) | 718,426 B | `1645e75128080f55...` | 2026-09-23 | 2019-07-22 to 2026+ | [ch2_sclk_v1.tsc](ISRO ISSDC Chandrayaan-2 SPICE PDS4 Archive) |
| **`ch2_ohr_v01.ti`** | IK (Instrument Kernel) | 8,409 B | `022d4f553f18e932...` | 2026-09-23 | Mission lifetime | [ch2_ohr_v01.ti](ISRO ISSDC Chandrayaan-2 SPICE PDS4 Archive) |

---

## 3. Reference Frame Inventory & Resolvability Audit

| Frame Name | NAIF ID | Family | Relative Frame | Source Kernel | Resolution Status |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **`CH2_OHRC`** | `-152270` | Instrument | `CH2_ORBITER` | `ch2_v01.tf` | **`FRAME_VERIFIED`** |
| **`CH2_ORBITER`** | `-152001` | Spacecraft Bus | `J2000` | `ch2_v01.tf` | **`FRAME_VERIFIED`** |
| **`IAU_MOON`** | `10020` | PCK Analytical | `J2000` | `pck00010.tpc` | **`FRAME_VERIFIED`** |
| **`MOON_PA`** | `31000` | TKFRAME Alias | `MOON_PA_DE421` | `moon_080317.tf` | **`FRAME_VERIFIED`** |
| **`MOON_PA_DE421`** | `31006` | Binary PCK | `J2000` | `moon_pa_de421_1900-2050.bpc` | **`FRAME_VERIFIED`** |
| **`MOON_ME`** | `31001` | TKFRAME Alias | `MOON_ME_DE421` | `moon_080317.tf` | **`FRAME_VERIFIED`** |
| **`MOON_ME_DE421`** | `31007` | TKFRAME (3-2-1 Euler) | `MOON_PA_DE421` | `moon_080317.tf` | **`FRAME_VERIFIED`** |

---

## 4. Numerical Frame Difference Analysis (`IAU_MOON` $\leftrightarrow$ `MOON_ME_DE421`)

The rotation matrix $\mathbf{R} = \text{pxform}(\text{"IAU_MOON"}, \text{"MOON_ME_DE421"}, ET)$ was numerically evaluated at the midpoint exposure epoch of each OHRC acquisition:

| Pair ID | Acquisition Epoch (UTC) | Rotation Angle | Rotation Axis $[e_x, e_y, e_z]$ | Euler Angles $(\theta_x, \theta_y, \theta_z)$ | Reversibility Residual |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`OHRC_PAIR_01`** | `2024-12-07T12:21:40.515` | **$10.3921"$** | `[-0.3482, -0.1129, -0.9306]` | `(+3.62", +1.17", +9.67")` | $< 3.4 \times 10^{-16}$ |
| **`OHRC_PAIR_02`** | `2025-02-08T14:02:53.949` | **$11.0302"$** | `[-0.6032, +0.4753, -0.6405]` | `(+6.65", -5.24", +7.06")` | $< 3.4 \times 10^{-16}$ |
| **`OHRC_PAIR_03`** | `2025-03-08T01:28:01.132` | **$5.4519"$** | `[-0.6238, +0.4879, -0.6105]` | `(+3.40", -2.66", +3.33")` | $< 2.3 \times 10^{-16}$ |
| **`OHRC_PAIR_04`** | `2025-10-12T04:58:29.292` | **$4.8201"$** | `[+0.3341, +0.4462, +0.8303]` | `(-1.61", -2.15", -4.00")` | $< 2.3 \times 10^{-16}$ |

> **Methodological Finding:**  
> The true measured rotation angle between the analytical libration series (`IAU_MOON`) and the DE421 Mean Earth / Polar Axis realization (`MOON_ME_DE421`) spans **$4.82"$ to $11.03"$** across the observation epochs.
> It does not exhibit arbitrary or unquantified offsets, and can be evaluated with sub-nanoradian precision.
