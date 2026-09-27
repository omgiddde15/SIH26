# 3D Inputs & Physical Geodesy Archive

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phases Covered:** Phase 22 (External Acquisition), Phase 22.5 (Coverage Verification), Phase 22.6 (Delivered-Raster Camera Model & Timing Audit)  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Directory Structure

```text
3d_inputs/
├── README.md                              <- Directory guide and artifact index
├── checksums.sha256                       <- SHA-256 integrity hashes of all files and kernels
│
├── authoritative_input_inventory.csv      <- Authoritative source metadata inventory (Phase 22)
├── authoritative_input_inventory.json     <- Machine-readable inventory (Phase 22)
├── 3d_input_readiness_matrix.csv          <- Readiness matrix across all pairs (Phase 22)
├── 3d_input_verification_report.md        <- External source verification report (Phase 22)
├── 3d_input_readiness_report.md           <- Readiness evaluation report (Phase 22)
├── geodetic_compatibility_report.md       <- Selenodetic frame compatibility report (Phase 22)
├── reference_geometry_report.md           <- Reference map geometry audit (Phase 22)
├── ohrc_camera_model_report.md            <- SPICE camera model derivation report (Phase 22)
│
├── binary_input_manifest.csv              <- Locally ingested binary files manifest (Phase 22.5)
├── binary_input_manifest.json             <- Machine-readable manifest (Phase 22.5)
├── 3d_input_compatibility_matrix.csv      <- Physical compatibility classification matrix (Phase 22.5)
├── spice_coverage_report.md               <- SPICE local availability & coverage report (Phase 22.5)
├── spk_local_coverage_report.md           <- Ephemeris coverage & trajectory report (Phase 22.5)
├── ck_local_coverage_report.md            <- Local C-kernel attitude coverage report (Phase 22.5)
├── frame_chain_verification.md            <- Complete SPICE frame-chain transformation report (Phase 22.5)
├── scanline_timing_verification.md        <- Spacecraft position per scanline report (Phase 22.5)
├── terrain_coverage_report.md             <- LROC WAC / GLD100 DEM coverage report (Phase 22.5)
├── dem_local_coverage_report.md           <- LOLA RDR DEM (LDEM_80S_20M / 875S_5M) coverage report (Phase 22.5)
│
├── phase22_6_readiness_matrix.csv         <- Delivered-raster camera model readiness matrix (Phase 22.6)
├── raster_camera_mapping_report.md        <- Native vs delivered TIFF geometry mapping report (Phase 22.6)
├── pixel_center_convention_report.md      <- RasterPixelIsArea & half-pixel convention audit (Phase 22.6)
├── line_timing_convention_report.md       <- Exposure center & row timing convention audit (Phase 22.6)
├── ck_subset_equivalence_report.md        <- CK attitude subset vs parent archive equivalence report (Phase 22.6)
├── ohrc_boresight_convention_report.md    <- Optical boresight vector & frame handedness report (Phase 22.6)
├── distortion_status_report.md            <- Optical distortion status & modeling disclaimer report (Phase 22.6)
├── phase22_6_readiness_report.md          <- Complete Phase 22.6 synthesis & gate report (Phase 22.6)
│
└── downloads/                             <- Locally verified authoritative binary kernels & DEM subsets
    ├── naif0012.tls                       <- Leapseconds kernel (Lola/JPL)
    ├── pck00010.tpc                       <- Planetary constants kernel (IAU/NAIF)
    ├── ch2_sclk_v1.tsc                    <- Spacecraft clock kernel (ISRO URSC)
    ├── ch2_v01.tf                         <- Frames kernel (ISRO SAC/URSC)
    ├── ch2_ohr_v01.ti                     <- OHRC instrument kernel (ISRO SAC/URSC)
    ├── ch2_eph_*.bsp                      <- 4 monthly orbiter ephemeris kernels (ISRO URSC)
    ├── ch2_att_pair0X_subset.bc           <- 4 verified standalone attitude kernels (ISRO URSC/ISIS)
    ├── LDEM_80S_20M.LBL                   <- PDS label for LOLA polar 20 m/px DEM (NASA GSFC)
    ├── LDEM_875S_5M.LBL                   <- PDS label for LOLA polar 5 m/px DEM (NASA GSFC)
    ├── LDEM_80S_20M_pair0X_subset.bin     <- 4 bounded binary DEM subsets at 20 m/px (NASA GSFC)
    └── LDEM_875S_5M_pair01_subset.bin     <- High-resolution binary DEM subset at 5 m/px (NASA GSFC)
```

---

## 2. Phase 22.6 Audit Summary

| Parameter | Pair 01 | Pair 02 | Pair 03 | Pair 04 | Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Native $\\to$ TIFF Sample Mapping** | `DERIVED` | `DERIVED` | `DERIVED` | `DERIVED` | Zero cropping; full 12K array preserved. |
| **TIFF Pixel-Center Convention** | `VERIFIED` | `VERIFIED` | `VERIFIED` | `VERIFIED` | `RasterPixelIsArea` (center at $u+0.5, v+0.5$). |
| **Delivered Line Mapping** | `DERIVED` | `DERIVED` | `DERIVED` | `DERIVED` | Isotropic scaling $s_y \\approx s_x$ ($< 0.01\\%$ diff). |
| **Timing Convention** | `DERIVED` | `DERIVED` | `DERIVED` | `DERIVED` | Center-line model removes $\\approx 2.7\\text{ m}$ bias. |
| **CK Subset Equivalence** | `VERIFIED` | `VERIFIED` | `VERIFIED` | `VERIFIED` | Discrepancy $\\le 0.006147\\text{ arcsec}$ ($< 2.5\\text{ mm}$). |
| **Distortion Status** | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | Unmodeled in IK; disclaimer required. |
| **Boresight Convention** | `VERIFIED` | `VERIFIED` | `VERIFIED` | `VERIFIED` | $[1, 0, 0]^T$ along optical axis in `CH2_OHRC`. |

**Overall Gate Assessment:** **`PHASE 23 READY FOR REVIEW`**
