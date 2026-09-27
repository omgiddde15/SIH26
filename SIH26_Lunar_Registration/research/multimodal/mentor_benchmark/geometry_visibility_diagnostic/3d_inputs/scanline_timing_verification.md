# Phase 22.5 — Pushbroom / Scanline Timing Verification Report

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 22.5 — Binary Input Ingestion & Physical Coverage Verification  
**Status:** COMPLETE & AUDITED  
**Date:** September 24, 2026  
**Governing Discipline:** RESEARCH-ONLY — PRODUCTION CODE 100% FROZEN  

---

## 1. Executive Summary

This report establishes that the line-by-line temporal progression of the Chandrayaan-2 Orbiter High Resolution Camera (OHRC) pushbroom sensor can be modeled deterministically from the verified mentor PDS4 XML labels and the official Spacecraft Clock (SCLK) kernel `ch2_sclk_v1.tsc`.

### Explicit Determination:
- **`OHRC_PAIR_01`:** `TIMING_READY`
- **`OHRC_PAIR_02`:** `TIMING_READY`
- **`OHRC_PAIR_03`:** `TIMING_READY`
- **`OHRC_PAIR_04`:** `TIMING_READY`

---

## 2. Sensor Kinematics & Timing Parameters per Pair

All timing variables were extracted directly from the verified source XML files and validated against the SPICE SCLK kernel:

| Parameter | `OHRC_PAIR_01` | `OHRC_PAIR_02` | `OHRC_PAIR_03` | `OHRC_PAIR_04` |
| :--- | :--- | :--- | :--- | :--- |
| **Pass Date** | 2024-Dec-07 | 2025-Feb-08 | 2025-Mar-08 | 2025-Oct-12 |
| **Source Image Lines ($H$)** | 4,872 lines | 5,059 lines | 5,054 lines | 4,649 lines |
| **Source Image Samples ($W$)** | 624 samples | 648 samples | 600 samples | 552 samples |
| **TDI Stages** | `TDI64` | `TDI64` | `TDI64` | `TDI64` |
| **Integration Time (XML)** | $174.870\text{ ms}$ | $174.870\text{ ms}$ | $162.100\text{ ms}$ | $162.100\text{ ms}$ |
| **Start Time UTC** | `2024-12-07T12:21:32.323420` | `2025-02-08T14:02:45.757525` | `2025-03-08T01:27:52.675500` | `2025-10-12T04:58:21.100114` |
| **Stop Time UTC** | `2024-12-07T12:21:48.706710` | `2025-02-08T14:03:02.141025` | `2025-03-08T01:28:09.587900` | `2025-10-12T04:58:37.483739` |
| **Total Pass Duration** | $16.383290\text{ seconds}$ | $16.383500\text{ seconds}$ | $16.912400\text{ seconds}$ | $16.383625\text{ seconds}$ |
| **Effective Line Period ($\Delta t$)** | $3.363435\text{ ms/line}$ | $3.239126\text{ ms/line}$ | $3.347002\text{ ms/line}$ | $3.524876\text{ ms/line}$ |
| **Start SCLK Ticks** | `187273277.0687` | `192722548.0035` | `195096453.8327` | `213944273.6128` |
| **Stop SCLK Ticks** | `187273293.4520` | `192722564.3870` | `195096470.7451` | `213944289.9964` |
| **Start ET (Seconds past J2000)** | $786846161.507\text{ s}$ | $792295434.943\text{ s}$ | $794669341.861\text{ s}$ | $813517170.282\text{ s}$ |
| **Stop ET (Seconds past J2000)** | $786846177.890\text{ s}$ | $792295451.326\text{ s}$ | $794669358.773\text{ s}$ | $813517186.666\text{ s}$ |

---

## 3. Mathematical Mapping: Pixel Row to Ephemeris Time

Unlike frame cameras that expose all pixels at a single instantaneous epoch, a pushbroom TDI sensor builds the 2D image line-by-line as the spacecraft sweeps along its orbital track.

For any pixel coordinate $(i, j)$ in the source image where $i \in [0, H-1]$ is the zero-indexed line row:
1. **Continuous Scanline UTC Time ($t_i$):**
   $$t_i = t_{\text{start}} + i \cdot \Delta t = t_{\text{start}} + \frac{i}{H - 1} (t_{\text{stop}} - t_{\text{start}})$$
2. **Continuous Ephemeris Time ($\text{ET}_i$):**
   $$\text{ET}_i = \text{ET}_{\text{start}} + \frac{i}{H - 1} (\text{ET}_{\text{stop}} - \text{ET}_{\text{start}})$$
3. **Spacecraft Clock Ticks ($\text{SCLK}_i$):**
   $$\text{SCLK}_i = \text{sp.sce2c}(-152, \text{ET}_i)$$
4. **Trajectory & Pointing Synchronism:**
   - Spacecraft position $\vec{R}(t_i)$ is evaluated at $\text{ET}_i$ via `sp.spkezr`.
   - Pointing quaternion $\mathbf{q}(t_i)$ is evaluated at $\text{SCLK}_i$ via `sp.ckgp` / `sp.pxform`.

### TDI Integration Consistency:
In `TDI64` mode, 64 physical detector rows integrate the same terrain patch sequentially along track. The nominal line period $\Delta t \approx 3.24 - 3.52\text{ ms}$ represents the downsampled image row progression, which is smooth, strictly monotonic, and spans the entire orbit segment without timing dropouts.

---

## 4. Technical Verdict

Each source image line can be mapped to an exact, continuous Ephemeris Time (ET) with millisecond-level precision, establishing that line-of-sight ray kinematics are fully evaluable.
