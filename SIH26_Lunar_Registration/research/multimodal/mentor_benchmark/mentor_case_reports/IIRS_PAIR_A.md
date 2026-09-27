# Mentor Dataset Case Report: IIRS_PAIR_A

**Dataset ID:** `IIRS_PAIR_A`  
**Instrument:** IIRS (Imaging Infrared Spectrometer, Chandrayaan-2)  
**Case Classification:** **`SAFE REJECTION`**  
**Pipeline Mode:** Frozen Adaptive Production Engine  
**Execution Timestamp:** September 23, 2026  

---

## 1. Case Provenance & Input Metadata

| Parameter | Source (Moving Image) | Reference (Target Image) |
| :--- | :--- | :--- |
| **Filename** | `IIRXXD18CHO2686502NNNN25244140531312_V2_1_source.tif` | `IIRXXD18CHO2686502NNNN25244140531312_V2_1_reference.tif` |
| **Dimensions** | `250x7783 px` | `960x7681 px` |
| **Native GSD** | `93.74 m/px` | `NOT VERIFIED` |
| **Effective GSD** | `93.74 m/px` | `NOT VERIFIED` |
| **Effective Scale** | **Source GSD verified; reference GSD NOT VERIFIED** | |
| **Raw Dtype** | `float32` | `float32` |
| **Normalized Dtype**| `uint8` (display & matcher representation) | `uint8` |
| **Illumination** | Sun El: `25.94 deg`, Solar Inc: `64.06 deg` | Unverified |
| **Lunar Area** | `Equatorial` | `Equatorial` |
| **Metadata Status**| `PARTIALLY VERIFIED` | |

---

## 2. Separated Telemetry Progression

```
Candidate Matches:        45
       ↓
Initial Matcher Inliers:  5 (11.11%)  [Threshold: >= 8 pts, >= 20.0%]
       ↓
Spatial Selection:        BYPASSED
       ↓
Spatial Occupancy:        22.2%  [Threshold: >= 33.3%, 3/9 cells]
       ↓
Quality Gate Outcome:     REJECTED SAFELY (Insufficient inlier consensus)
       ↓
Final Geometric Model:    UNAVAILABLE (Estimation Withheld)
       ↓
Warp Operation:           BYPASSED (No transformation applied)
       ↓
Registered Image:         UNAVAILABLE (Safe Rejection)
       ↓
Held-Out Validation:      UNAVAILABLE (Validation Unavailable, RMSE: N/A)
```

---

## 3. Router & Execution Diagnostics

- **Primary Matcher Selected:** `LoFTR`
- **Resource Guard Mode:** `Standard LoFTR (Downscaled Workspace)`
- **Fallback Status:** `BLOCKED — RESOURCE POLICY (max_dim > 4000 px)`
- **Failure Stage:** `quality_gate`
- **Failure Reason:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (11.11% < 20.0%); Spatial occupancy below threshold (22.22% < 33.33%, 2/9 cells). Large-image fallback matchers (SIFT, SuperGlue) blocked by resource policy (source max_dim=7783 > 4000 px).
- **Execution Latency:** `7.65 s`

---

## 4. Multi-Seed Hold-Out Validation (Seeds 1–5)

In accordance with frozen production discipline, hold-out validation is not performed on rejected candidates to prevent spurious metric generation:

- **Held-Out Check RMSE:** `N/A` (never defaulted to 0.0000 px)
- **Validation Status:** `UNAVAILABLE`
- **Seeds 1–5:** `UNAVAILABLE` across all seeds.

---

## 5. Potential Contributing Factors

- **Classification:** **`SAFE REJECTION`**
- **Safety Determination:** The system safely rejected this pair without emitting geometric distortion, ungrounded homography matrices, or blurred registered rasters.
- **Factor Analysis:** Results are consistent with a cross-sensor representation/modality mismatch, but this benchmark does not isolate causality.
