# Phase 22.6 — OHRC Boresight & Frame Convention Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.6 — OHRC Delivered-Raster Camera Model & Timing Convention Audit  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report defines and verifies the optical boresight vector, instrument coordinate axes, and frame handedness for the Chandrayaan-2 Orbiter High Resolution Camera (OHRC) as specified by the authoritative ISRO Space Applications Centre (SAC) and URSC Flight Dynamics Group SPICE kernels.

### Explicit Determination:
- **SPICE Instrument Frame:** `CH2_OHRC` (NAIF ID `-152270`)
- **Parent Spacecraft Frame:** `CH2_ORBITER` (NAIF ID `-152001`)
- **Relative Alignment:** Identically co-aligned ($\mathbf{R}_{	ext{CH2\_ORBITER} \to \text{CH2\_OHRC}} = \mathbf{I}_{3\times 3}$, Euler angles $(0.0^\circ, 0.0^\circ, 0.0^\circ)$)
- **Optical Boresight Vector:** $+X_{\text{OHRC}} = [1.0, 0.0, 0.0]^T$
- **Along-Track Flight Direction:** $+Y_{\text{OHRC}} = [0.0, 1.0, 0.0]^T$
- **Cross-Track Detector Axis:** $+Z_{\text{OHRC}} = [0.0, 0.0, 1.0]^T$
- **Coordinate Handedness:** Right-handed Cartesian reference frame ($\hat{X} \times \hat{Y} = \hat{Z}$)
- **Classification:** **`BORESIGHT_CONVENTION_VERIFIED`** across all four pairs (`OHRC_PAIR_01` to `OHRC_PAIR_04`).

---

## 2. Authoritative Kernel Pool Definitions

The frame hierarchy and geometric definitions are extracted directly from the official ISRO SPICE kernels:
- Frames Kernel: `ch2_v01.tf` (SAC/URSC, Version 1.0, June 19, 2023)
- Instrument Kernel: `ch2_ohr_v01.ti` (SAC/URSC, Version 1.0, June 19, 2023)

### 2.1 Frame Hierarchy & Rotation Matrix
In `ch2_v01.tf` (lines 208–232):
```text
The OHRC camera detector frames, CH2_OHRC are defined as follows:
   - +X axis points along the detector boresight;
   - +Z axis is parallel to the detector lines;
   - +Y axis completes the right handed frame;
   - the origin of the frame is located at the camera focal point.

FRAME_CH2_OHRC               = -152270
FRAME_-152270_NAME           = 'CH2_OHRC'
FRAME_-152270_CLASS          =  4
FRAME_-152270_CLASS_ID       = -152270
FRAME_-152270_CENTER         = -152
TKFRAME_-152270_RELATIVE     = 'CH2_ORBITER'
TKFRAME_-152270_SPEC         = 'ANGLES'
TKFRAME_-152270_UNITS        = 'DEGREES'
TKFRAME_-152270_ANGLES       = ( 0.0, 0.0, 0.0 )
TKFRAME_-152270_AXES         = ( 1,   2,   3   )
```
Because the Euler rotation angles are strictly $(0.0, 0.0, 0.0)$, the transformation between the spacecraft bus frame `CH2_ORBITER` and the instrument camera frame `CH2_OHRC` is the identity matrix $\mathbf{I}$:
$$\mathbf{R}_{\text{CH2\_ORBITER} \to \text{CH2\_OHRC}} = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix}$$

### 2.2 Field of View & Boresight Definition
In `ch2_ohr_v01.ti` (lines 217–228):
```text
INS-152270_FOV_CLASS_SPEC   = 'ANGLES'
INS-152270_FOV_SHAPE        = 'RECTANGLE'
INS-152270_FOV_FRAME        = 'CH2_OHRC'
INS-152270_BORESIGHT        = ( 1.0, 0.0, 0.0 )
INS-152270_FOV_REF_VECTOR   = ( 0.0, 1.0, 0.0 )
INS-152270_FOV_REF_ANGLE    = ( 0.0 )
INS-152270_FOV_CROSS_ANGLE  = ( 0.86 )
INS-152270_FOV_ANGLE_UNITS  = ( 'DEGREES' )
```
- `INS-152270_BORESIGHT` is explicitly defined as vector $[1.0, 0.0, 0.0]^T$.
- `FOV_CROSS_ANGLE` $= 0.86^\circ$ corresponds to the half-angle across the 12,000-pixel detector array in the cross-track ($\pm Z$) direction, yielding the full $1.72^\circ$ FOV:
  $$\theta_{\text{half}} = \arctan\left(\frac{12000 \times 0.0052\text{ mm} / 2}{2080.0\text{ mm}}\right) = \arctan\left(\frac{31.2}{2080}\right) = \arctan(0.0150) = 0.85938^\circ \approx 0.86^\circ$$
- `FOV_REF_ANGLE` $= 0.0^\circ$ corresponds to the along-track dimension (a 1-line pushbroom array).

---

## 3. Mathematical Line-of-Sight Ray Vector Formulation

For any pixel sample in the delivered source raster $u_{\text{tiff}} \in [0, W_{\text{tiff}}-1]$:

1. **Native Sample Coordinate (0-indexed):**
   $$u_{\text{native}} = s_x \cdot u_{\text{tiff}} + \frac{s_x - 1}{2}$$
   where $s_x = \frac{12000}{W_{\text{tiff}}}$.

2. **Pixel-Center Sample Coordinate:**
   $$u_{\text{center}} = u_{\text{native}} + 0.5$$

3. **Physical Focal Plane Offset along $\hat{Z}_{\text{OHRC}}$:**
   $$Z_{\text{fp}}(u) = (u_{\text{center}} - 6000.0) \times p$$
   where $p = 0.0052\text{ mm}$ is the detector pixel pitch, and $6000.0$ is the calibrated array optical center from `INS-152270_CENTER`.

4. **Unnormalized Instrument Look-Vector:**
   $$\mathbf{r}_{\text{OHRC}}(u) = \begin{bmatrix} f \\ 0.0 \\ Z_{\text{fp}}(u) \end{bmatrix} = \begin{bmatrix} 2080.0\text{ mm} \\ 0.0 \\ (u_{\text{native}} + 0.5 - 6000.0) \times 0.0052\text{ mm} \end{bmatrix}$$

5. **Normalized Unit Look-Vector in `CH2_OHRC`:**
   $$\hat{\mathbf{v}}_{\text{OHRC}}(u) = \frac{\mathbf{r}_{\text{OHRC}}(u)}{\|\mathbf{r}_{\text{OHRC}}(u)\|}$$

6. **Inertial Look-Vector in `J2000` at line center time $t$:**
   $$\hat{\mathbf{v}}_{\text{J2000}}(u, t) = \mathbf{R}_{\text{CH2\_ORBITER} \to \text{J2000}}(t) \cdot \mathbf{R}_{\text{CH2\_OHRC} \to \text{CH2\_ORBITER}} \cdot \hat{\mathbf{v}}_{\text{OHRC}}(u) = \mathbf{R}_{\text{CH2\_ORBITER} \to \text{J2000}}(t) \cdot \hat{\mathbf{v}}_{\text{OHRC}}(u)$$

7. **Lunar Fixed Look-Vector in `MOON_ME` at line center time $t$:**
   $$\hat{\mathbf{v}}_{\text{MOON}}(u, t) = \mathbf{R}_{\text{J2000} \to \text{MOON\_ME}}(t) \cdot \hat{\mathbf{v}}_{\text{J2000}}(u, t)$$

---

## 4. Verification Matrix

| Dataset | Frame ID | Boresight Vector | Cross-Track Axis | Along-Track Axis | Handedness | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `OHRC_PAIR_01` | `CH2_OHRC` (`-152270`) | $[1.0, 0.0, 0.0]^T$ | $[0.0, 0.0, 1.0]^T$ | $[0.0, 1.0, 0.0]^T$ | Right-handed | **VERIFIED** |
| `OHRC_PAIR_02` | `CH2_OHRC` (`-152270`) | $[1.0, 0.0, 0.0]^T$ | $[0.0, 0.0, 1.0]^T$ | $[0.0, 1.0, 0.0]^T$ | Right-handed | **VERIFIED** |
| `OHRC_PAIR_03` | `CH2_OHRC` (`-152270`) | $[1.0, 0.0, 0.0]^T$ | $[0.0, 0.0, 1.0]^T$ | $[0.0, 1.0, 0.0]^T$ | Right-handed | **VERIFIED** |
| `OHRC_PAIR_04` | `CH2_OHRC` (`-152270`) | $[1.0, 0.0, 0.0]^T$ | $[0.0, 0.0, 1.0]^T$ | $[0.0, 1.0, 0.0]^T$ | Right-handed | **VERIFIED** |
