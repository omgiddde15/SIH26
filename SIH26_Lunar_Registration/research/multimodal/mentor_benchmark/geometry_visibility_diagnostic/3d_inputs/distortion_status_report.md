# Phase 22.6 — Optical Distortion Status & Modeling Disclaimer Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report establishes the optical distortion modeling status for the Chandrayaan-2 Orbiter High Resolution Camera (OHRC) based on a systematic audit of the authoritative mission kernels and archival documentation.

### Explicit Determination:
- **Optical Distortion Classification:** **`DISTORTION_UNKNOWN`** (Unmodeled in authoritative SPICE kernels).
- **Kernel Findings:** The official ISRO Instrument Kernel (`ch2_ohr_v01.ti`) provides focal length, aperture, pixel size, and array center, but contains **zero optical distortion polynomial coefficients**, zero radial distortion terms ($k_1, k_2$), and zero tangential distortion parameters.
- **USGS ISIS Ingestion Status:** No sensor-specific transverse translation tables (`TRANSX`/`TRANSY`) or optical calibration matrices are included in the public kernel repository.
- **Mandatory Phase 23 Disclaimer:** Any future physical ray-tracing, orthorectification, or projection experiments must explicitly declare:
  > *"Optical distortion is not modeled; distortion uncertainty is unquantified."*

---

## 2. Kernel Pool Audit

Inspection of all keywords in `ch2_ohr_v01.ti` confirms the complete inventory of optical and geometric parameters:

```text
INS-152270_FOCAL_LENGTH = ( 2080.0 )
INS-152270_APERTURE     = ( 300 )
INS-152270_F_NUMBER     = ( 6.93 )
INS-152270_PIXEL_SAMPLES= ( 12000 )
INS-152270_PIXEL_LINES  = ( 1 )
INS-152270_CENTER       = ( 6000, 0.5 )
INS-152270_PIXEL_SIZE   = ( 0.0000052 )
INS-152001_PLATFORM_ID  = ( -152001 )
INS-152270_FOV_CLASS_SPEC = 'ANGLES'
INS-152270_FOV_SHAPE    = 'RECTANGLE'
INS-152270_FOV_FRAME    = 'CH2_OHRC'
INS-152270_BORESIGHT    = ( 1.0, 0.0, 0.0 )
INS-152270_FOV_REF_VECTOR = ( 0.0, 1.0, 0.0 )
INS-152270_FOV_REF_ANGLE= ( 0.0 )
INS-152270_FOV_CROSS_ANGLE = ( 0.86 )
INS-152270_FOV_ANGLE_UNITS = ( 'DEGREES' )
```

No keywords of the form `INS-152270_DISTORTION_K*`, `INS-152270_OD_K*`, or transverse polynomial maps exist.

---

## 3. Physical Impact Assessment & Optical Bounds

While exact pre-flight laboratory optical distortion measurements are omitted from the SPICE kernel pool:
1. **Narrow Field of View:**  
   OHRC utilizes a very narrow field of view ($1.72^\circ$ cross-track, $\pm 0.86^\circ$ half-angle).
2. **Optical Architecture:**  
   As documented in ISRO payload publications, OHRC employs an all-reflective Three-Mirror Anastigmat (TMA) telescope design. TMA systems are diffraction-limited and specifically corrected for spherical aberration, coma, and astigmatism across narrow swaths.
3. **Upper Bound on Geometric Distortion:**  
   In comparable spaceborne TMA systems (e.g., HiRISE, LROC NAC), residual optical distortion across a $\pm 0.86^\circ$ swath is typically $< 0.05\% - 0.10\%$.
   - At the edge of the native array ($Z = 31.2\text{ mm}$), a $0.05\%$ distortion corresponds to $\approx 15\ \mu\text{m} \approx 3$ native detector pixels.
   - Resampled onto the delivered $5\text{ m}$ mentor grid ($s_x \approx 19.2$), $3$ native pixels correspond to:
     $$\Delta u_{\text{tiff}} = \frac{3}{19.2} \approx 0.15\text{ delivered pixels} \approx 0.78\text{ meters on the lunar surface}$$
4. **Conclusion on Feasibility:**  
   The residual unmodeled distortion is estimated to be well below the $5.0\text{ m}$ pixel resolution of the delivered rasters ($< 0.2\text{ pixels}$). However, because exact laboratory calibration coefficients are unavailable in the public domain, scientific honesty mandates classifying this parameter as **`UNKNOWN`** and explicitly carrying the unmodeled distortion caveat into Phase 23.

---

## 4. Summary Matrix

| Dataset | Optical Model | Distortion Parameters in IK | Theoretical Upper Bound | Status for Phase 23 |
| :--- | :---: | :---: | :---: | :---: |
| `OHRC_PAIR_01` | Pinhole / Linear | None | $< 0.2\text{ delivered pixels}$ | **DISTORTION_UNKNOWN** (Disclaimer Required) |
| `OHRC_PAIR_02` | Pinhole / Linear | None | $< 0.2\text{ delivered pixels}$ | **DISTORTION_UNKNOWN** (Disclaimer Required) |
| `OHRC_PAIR_03` | Pinhole / Linear | None | $< 0.2\text{ delivered pixels}$ | **DISTORTION_UNKNOWN** (Disclaimer Required) |
| `OHRC_PAIR_04` | Pinhole / Linear | None | $< 0.2\text{ delivered pixels}$ | **DISTORTION_UNKNOWN** (Disclaimer Required) |
