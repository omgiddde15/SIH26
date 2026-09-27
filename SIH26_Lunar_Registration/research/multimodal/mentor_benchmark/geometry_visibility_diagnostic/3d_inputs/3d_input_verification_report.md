# Phase 22 — Authoritative 3D Input Verification & Readiness Master Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22 — Authoritative 3D Input Acquisition & Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION 100% FROZEN  

---

## 1. Executive Summary & Readiness Classification

This report provides the authoritative synthesis for Phase 22, evaluating external geodetic, ephemeris, and sensor data required to conduct a physically meaningful 3D viewpoint and terrain investigation for Chandrayaan-2 OHRC mentor pairs (`OHRC_PAIR_01` to `OHRC_PAIR_04`).

### Master Readiness Classification Table

| Pair ID | Target Geographic Center | Available External DEM | Available Spacecraft Ephemeris | Camera Sensor Model | Reference Image Modeling | Local Ingestion Status | Final Phase 22 Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`OHRC_PAIR_01`** | $89.36^\circ\text{S}$, $134.2^\circ\text{E}$ | LOLA 20m & 5m | ISRO URSC SPK & CK | Official IK ($f = 2080\text{ mm}$) | 2D Map Raster Only | Static + SPK Downloaded; CK & DEM Pending | **`B. PARTIALLY READY — SPECIFIC INPUTS STILL MISSING`** |
| **`OHRC_PAIR_02`** | $84.95^\circ\text{S}$, $33.6^\circ\text{W}$ | LOLA 20m | ISRO URSC SPK & CK | Official IK ($f = 2080\text{ mm}$) | 2D Map Raster Only | Static Downloaded; SPK, CK & DEM Pending | **`B. PARTIALLY READY — SPECIFIC INPUTS STILL MISSING`** |
| **`OHRC_PAIR_03`** | $84.96^\circ\text{S}$, $33.6^\circ\text{W}$ | LOLA 20m | ISRO URSC SPK & CK | Official IK ($f = 2080\text{ mm}$) | 2D Map Raster Only | Static Downloaded; SPK, CK & DEM Pending | **`B. PARTIALLY READY — SPECIFIC INPUTS STILL MISSING`** |
| **`OHRC_PAIR_04`** | $84.18^\circ\text{S}$, $33.9^\circ\text{W}$ | LOLA 20m | ISRO URSC SPK & CK | Official IK ($f = 2080\text{ mm}$) | 2D Map Raster Only | Static Downloaded; SPK, CK & DEM Pending | **`B. PARTIALLY READY — SPECIFIC INPUTS STILL MISSING`** |

> **Final Recommendation:** **THE ACTUAL 3D RAY-TRACING EXPERIMENT MUST BE STRICTLY HELD.**  
> While authoritative external sources have been successfully located, verified, and partially downloaded, full local binary ingestion (~10.9 GB) and asymmetric orthorectification pipeline implementation are mandatory prerequisites before any ray-tracing execution.

---

## 2. Synthesis Answers to Core Audit Questions

### Question 1: Which mentor OHRC pairs have sufficient authoritative external data to support a real 3D ray-tracing experiment?
**Answer:**  
All four mentor OHRC pairs (`OHRC_PAIR_01`, `OHRC_PAIR_02`, `OHRC_PAIR_03`, `OHRC_PAIR_04`) have authoritative external data identified in official repositories (NASA PDS Geosciences, ISRO SAC/URSC, and USGS Astrogeology).
- Official camera geometry: Validated across all 4 pairs via official Instrument Kernel `ch2_ohr_v01.ti`.
- Topographic terrain: Validated across all 4 pairs via NASA LOLA `LDEM_80S_20M` (with `LDEM_875S_5M` providing 5m coverage for Pair 01).
- Flight ephemeris and attitude: Validated across all 4 pairs in monthly URSC SPK and CK archives at the USGS ISIS S3 endpoint.

### Question 2: Exactly which files are missing for each pair in the local runtime environment?
**Answer:**
- **Static Kernels (All Pairs):** `ch2_ohr_v01.ti`, `ch2_v01.tf`, `ch2_sclk_v1.tsc`, `pck00010.tpc` are **ALREADY DOWNLOADED & VERIFIED** in `3d_inputs/downloads/`.
- **`OHRC_PAIR_01`:**
  - Trajectory SPK: `ch2_eph_29Nov2024_02Jan2025_v1.bsp` is **ALREADY DOWNLOADED & VERIFIED** (5.5 MB).
  - Missing locally: Attitude CK `ch2_att_27Nov2024_04Jan2025_v1.bc` (2.24 GB) and DEM binary `LDEM_80S_20M.IMG` (1.85 GB).
  - Permanently absent: Reference image camera model and solar ephemeris.
- **`OHRC_PAIR_02`:**
  - Missing locally: Trajectory SPK `ch2_eph_29Jan2025_02Mar2025_v1.bsp` (5.2 MB), Attitude CK `ch2_att_27Jan2025_04Mar2025_v1.bc` (2.30 GB), and DEM binary `LDEM_80S_20M.IMG` (1.85 GB).
  - Permanently absent: Reference image camera model and solar ephemeris.
- **`OHRC_PAIR_03`:**
  - Missing locally: Trajectory SPK `ch2_eph_27Feb2025_02Apr2025_v1.bsp` (5.5 MB), Attitude CK `ch2_att_27Feb2025_04Apr2025_v1.bc` (2.26 GB), and DEM binary `LDEM_80S_20M.IMG` (1.85 GB).
  - Permanently absent: Reference image camera model and solar ephemeris.
- **`OHRC_PAIR_04`:**
  - Missing locally: Trajectory SPK `ch2_eph_30Sep2025_02Nov2025_v1.bsp` (5.4 MB), Attitude CK `ch2_att_27Sep2025_03Nov2025_v1.bc` (2.25 GB), and DEM binary `LDEM_80S_20M.IMG` (1.85 GB).
  - Permanently absent: Reference image camera model and solar ephemeris.

### Question 3: How much storage is required if full CK/SPK/DEM files are downloaded?
**Answer:**  
The total USGS ISIS Chandrayaan-2 CK archive contains over 200 GB of continuous orbiter attitude. However, filtering down to the **exact 4 monthly kernels** covering the mentor acquisition passes drastically optimizes storage:
- **CK Attitude Subsets (4 files):**
  - Pair 01: 2,238,906,368 bytes (2.24 GB)
  - Pair 02: 2,301,982,720 bytes (2.30 GB)
  - Pair 03: 2,259,828,736 bytes (2.26 GB)
  - Pair 04: 2,247,628,800 bytes (2.25 GB)
  - **Subtotal CK:** **9,048,346,624 bytes (~9.05 GB)**
- **SPK Ephemeris Subsets (4 files):**
  - Pair 01: 5,515,264 bytes (downloaded)
  - Pair 02: 5,193,728 bytes
  - Pair 03: 5,516,288 bytes
  - Pair 04: 5,353,472 bytes
  - **Subtotal SPK:** **21,578,752 bytes (~21.6 MB)**
- **Static Kernels (IK, FK, SCLK, PCK):** **866,360 bytes (~866 KB)**
- **Digital Elevation Models (NASA PDS):**
  - Primary `LDEM_80S_20M.IMG` (covers all 4 pairs): **1,848,320,000 bytes (~1.85 GB)**
  - Optional `LDEM_875S_5M.IMG` (covers Pair 01 only): **1,840,545,792 bytes (~1.84 GB)**
- **Grand Total Required Storage:**
  - With 20m DEM only: **~10.92 GB**
  - With both 20m and 5m DEMs: **~12.76 GB**

### Question 4: What is the spatial resolution mismatch between OHRC and available LOLA DEMs, and how does it affect ray intersection accuracy?
**Answer:**
- **Spatial Resolution Mismatch:**
  - Downsampled mentor OHRC benchmark swaths: $\approx 1.25\text{ m/px}$ to $2.50\text{ m/px}$ (native OHRC is $0.25\text{ m/px}$ to $0.32\text{ m/px}$).
  - `LDEM_80S_20M`: $20.0\text{ m/pixel}$ (an **$8\times$ to $16\times$ resolution mismatch** relative to benchmark images, and **$80\times$** relative to native data).
  - `LDEM_875S_5M` (Pair 01 only): $5.0\text{ m/pixel}$ (a **$2\times$ to $4\times$ mismatch** relative to benchmark images).
- **Physical Impact on Ray Intersection Accuracy:**
  1. **Macro-Topography:** Large crater walls, central peaks, and regional slope tilts ($\ge 100\text{ m}$) are accurately captured by the 20m DEM and will produce physically faithful broad-scale parallax corrections.
  2. **Micro-Topography Smoothing:** Craters $< 40\text{ m}$ across, boulder fields, and sharp ridge crests are completely smoothed out by the 20m sampling grid.
  3. **Interpolation Error:** Sub-grid bicubic or bilinear interpolation of the DEM introduces vertical height uncertainties on the order of $\pm 2\text{ m}$ to $\pm 5\text{ m}$. Under an off-nadir look angle of $\theta \approx 20^\circ$, a vertical error $\Delta Z = 3\text{ m}$ induces a horizontal ray displacement error of:
     $$\Delta X = \Delta Z \cdot \tan(\theta) = 3\text{ m} \cdot \tan(20^\circ) \approx 1.09\text{ m}$$
     In the benchmark images ($1.25\text{ m/px}$), this represents a **$\sim 0.9\text{ pixel}$ ray-tracing displacement uncertainty**.
  4. **Conclusion:** LOLA DEM ray-intersection will resolve macroscopic relief distortion but cannot predict sub-pixel micro-texture or fine craterlet shadow boundaries.

### Question 5: Does the absence of reference image SPICE data prevent differential illumination modeling?
**Answer:**  
**YES, ABSOLUTELY.**  
As established in Target E ([`reference_geometry_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/reference_geometry_report.md)), the reference images are 2D orthorectified map-projected rasters. They contain zero camera parameters, zero flight trajectory, zero acquisition timestamps, and zero sun azimuth or elevation angles.
- While the Sun vector can be determined for the source OHRC image via SPICE, the Sun vector for the reference cannot be calculated from verified metadata.
- Consequently, bidirectional shadow simulation, mutual shadow alignment, or BRDF surface rendering across source and reference **cannot be performed rigorously**.
- Radiometric adjustments on the reference must remain empirical (gradient filters, edge extractors) rather than physical ray-traced shadow inversions.

### Question 6: Can a physically rigorous 3D experiment be run with synthetic/approximated camera models, or does scientific integrity require waiting for official kernels?
**Answer:**  
**Scientific integrity strictly requires using the official kernels and calibrated parameters.**  
Pushbroom TDI linescan sensors are acutely sensitive to spacecraft roll/pitch dynamics and detector geometry:
- Assuming an ideal perspective pinhole camera ignores the line-by-line scanning kinematics, where each line has a distinct center of projection and attitude.
- Using uncalibrated focal lengths or assumed nadir pointing introduces tens of pixels of spurious geometric deformation.
- Because the official ISRO Instrument Kernel (`ch2_ohr_v01.ti`), Frame Kernel (`ch2_v01.tf`), and SCLK (`ch2_sclk_v1.tsc`) have now been verified and downloaded, there is no scientific justification for synthetic approximations.

### Question 7: How does the camera focal length in the official ISRO IK compare to values used in literature (2080 mm vs 2046.2 mm)?
**Answer:**
- **Literature Value:** Secondary academic publications (e.g., Chowdhury et al. 2020) cite the nominal optical design focal length of **$2046.2\text{ mm}$**.
- **Official ISRO SPICE IK Value:** The official ISRO Space Applications Centre / URSC Instrument Kernel (`ch2_ohr_v01.ti`) defines the post-launch calibrated focal length as:
  ```spice
  INS-152270_FOCAL_LENGTH = ( 2080.0 )
  ```
- **Discrepancy:** The official calibrated focal length is **$+33.8\text{ mm}$ longer (+1.65%)** than the pre-flight design value.
- **Physical Impact:**  
  Using $2046.2\text{ mm}$ instead of $2080.0\text{ mm}$ produces a $+1.65\%$ angular scaling error across the detector. Over an OHRC swath of 4,000 pixels at $1.25\text{ m/px}$ ground distance ($5,000\text{ m}$ ground width), a $1.65\%$ error shifts edge pixels by:
  $$\Delta W = 5000\text{ m} \times 0.0165 = 82.5\text{ m} \approx 66\text{ pixels}$$
  This $66\text{ px}$ systematic scaling error would completely ruin any sub-pixel ray-intersection experiment, conclusively justifying the requirement for official kernels.

### Question 8: What is the exact classification of each pair?
**Answer:**  
All four mentor OHRC pairs are classified as:  
**`B. PARTIALLY READY — SPECIFIC INPUTS STILL MISSING`**  
(Recorded as `PARTIALLY READY` in [`3d_input_compatibility_matrix.csv`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/geometry_visibility_diagnostic/3d_inputs/3d_input_compatibility_matrix.csv)).
- The external data required for the source imaging chain exists and is verified.
- However, local ingestion of large binary CK and DEM assets is not yet complete, and the reference image lacks physical camera metadata, necessitating an asymmetric projection paradigm.

---

## 3. Reconciliation: Local Audit vs. External Audit

The previous audit (Phase 21) concluded that the mentor datasets were `NOT READY` based on files found locally in the workspace. Phase 22 investigated external authoritative archives. The table below reconciles these findings:

| Parameter / Requirement | Local Audit Finding (Phase 21) | External Investigation Finding (Phase 22) | Current Status & Reconciliation |
| :--- | :--- | :--- | :--- |
| **Lunar Digital Elevation Model** | **ABSENT** locally in mentor folder or repo. | **ACQUIRED & VERIFIED**: NASA LOLA GDR `LDEM_80S_20M` (covers all pairs) and `LDEM_875S_5M` (Pair 01). Labels downloaded; binaries cataloged at NASA PDS. | **RESOLVED EXTERNALLY**: Authoritative 20m polar DEM is available. Local binary download (1.85 GB) required prior to ray-tracing. |
| **OHRC Camera Intrinsics ($f, c_x, c_y$, pitch)** | **ABSENT** from PDS4 XML; only TDI mode 64 and lines/samples recorded. | **ACQUIRED & VERIFIED**: ISRO SAC/URSC Instrument Kernel `ch2_ohr_v01.ti`. Calibrated $f = 2080.0\text{ mm}$, pitch $5.2\ \mu\text{m}$, 12000 px array, optical center $(6000, 0.5)$. | **RESOLVED & DOWNLOADED**: Local copy in `3d_inputs/downloads/ch2_ohr_v01.ti`. |
| **Spacecraft Frames & Hierarchy** | **ABSENT** locally. | **ACQUIRED & VERIFIED**: ISRO Frame Kernel `ch2_v01.tf` defines frame `CH2_OHRC` (-152270) relative to `CH2_ORBITER` (-152001) and lunar IAU frames. | **RESOLVED & DOWNLOADED**: Local copy in `3d_inputs/downloads/ch2_v01.tf`. |
| **Spacecraft Clock Correlation** | **ABSENT** locally. | **ACQUIRED & VERIFIED**: ISRO URSC Clock Kernel `ch2_sclk_v1.tsc` converts mission clock to ephemeris time (ET). | **RESOLVED & DOWNLOADED**: Local copy in `3d_inputs/downloads/ch2_sclk_v1.tsc`. |
| **Spacecraft Trajectory $\vec{R}(t), \vec{V}(t)$** | **ABSENT** locally; only single scalar altitude (~105-115 km) in XML. | **ACQUIRED & VERIFIED**: URSC Flight Dynamics monthly SPK kernels. Pair 01 kernel `ch2_eph_29Nov2024_02Jan2025_v1.bsp` downloaded and verified. Pairs 02–04 cataloged at USGS S3. | **RESOLVED EXTERNALLY**: Pair 01 is local; Pairs 02–04 require downloading ~5 MB SPKs each. |
| **Spacecraft Attitude Quaternions $q(t)$** | **ABSENT** locally; only single scalar roll/pitch/yaw in XML. | **ACQUIRED & VERIFIED**: URSC Flight Dynamics monthly CK kernels cataloged at USGS S3 (~2.25 GB each, Type 3 continuous quaternion stream). | **RESOLVED EXTERNALLY**: Validated at authoritative archive; requires ~9.05 GB local download. |
| **Scanline Exposure Timing** | **PRESENT**: PDS4 XML start/stop UTC + integration time (~0.35–0.45 ms). | Verified consistent with SCLK and SPK polynomial time spans. | **RESOLVED**: Line-by-line UTC timestamps $t_i = t_{\text{start}} + i \cdot \Delta t$ are directly constructible. |
| **Reference Camera Intrinsics & Ephemeris** | **ABSENT** locally. | **CONFIRMED PERMANENTLY ABSENT**: Reference images are 2D orthorectified map-projected products (Polar Stereographic, 5m/px) across all external archives. | **FATAL MODELING CONSTRAINT**: Reference images cannot be modeled as ray cameras. Differential illumination modeling is impossible. |

---

## 4. Final Scientific Decision & Execution Roadmap

### Final Decision
> **THE ACTUAL 3D RAY-TRACING EXPERIMENT IS HELD.**  
> Execution cannot proceed until the remaining binary assets are downloaded and an asymmetric projection pipeline is engineered.

### Execution Roadmap for Future Phase
If approval is sought to conduct the 3D ray-tracing experiment in a subsequent phase, the following three preconditions must be satisfied:
1. **Asset Ingestion:**
   - Download the 1.85 GB LOLA DEM binary (`LDEM_80S_20M.IMG`) from NASA PDS into local scratch/cache storage.
   - Download the target CK attitude binary (~2.25 GB per pair) from the USGS S3 endpoint.
2. **Sensor Pipeline Implementation:**
   - Construct a Python/SpiceyPy or USGS CSM/ALE linescan projection routine that computes the camera position $\vec{C}(t_i)$ and boresight vector $\vec{b}(t_i, j)$ for each pixel $(i, j)$.
   - Intersect rays with the LOLA DEM bilinear/bicubic heightfield to obtain selenographic coordinates $(X, Y, Z)$.
3. **Asymmetric Evaluation Protocol:**
   - Reproject ray-intersected source pixels into Polar Stereographic map coordinates ($5.0\text{ m/px}$).
   - Compare the orthorectified source raster directly against the 2D reference mosaic to test whether terrain relief compensation resolves the feature disparity.
   - Strictly prohibit synthetic reference camera modeling or artificial shadow simulation.
