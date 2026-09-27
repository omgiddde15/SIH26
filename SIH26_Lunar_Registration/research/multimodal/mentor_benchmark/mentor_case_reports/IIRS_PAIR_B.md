# Mentor Dataset Case Report: IIRS_PAIR_B

**Dataset ID:** `IIRS_PAIR_B`  
**Instrument:** IIRS (Imaging Infrared Spectrometer, Chandrayaan-2)  
**Case Classification:** **`SAFE REJECTION`**  
**Pipeline Mode:** Frozen Adaptive Production Engine  
**Execution Timestamp:** September 23, 2026  

---

## 1. Case Provenance & Input Metadata

| Parameter | Source (Moving Image) | Reference (Target Image) |
| :--- | :--- | :--- |
| **Filename** | `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01_source.tif` | `IIRXXD32CHO1519402NNNN23022110758606_V1_1_01_reference.tif` |
| **Dimensions** | `104x4851 px` | `3175x3874 px` |
| **Native GSD** | `83.14 m/px` | `NOT VERIFIED` |
| **Effective GSD** | `83.14 m/px` | `NOT VERIFIED` |
| **Effective Scale** | **Source GSD verified; reference GSD NOT VERIFIED** | |
| **Raw Dtype** | `float32` | `float32` |
| **Normalized Dtype**| `uint8` (display & matcher representation) | `uint8` |
| **Illumination** | Sun El: `21.06 deg`, Solar Inc: `68.94 deg` | Unverified |
| **Lunar Area** | `South Pole` | `South Pole` |
| **Metadata Status**| `PARTIALLY VERIFIED` | |

---

## 2. Separated Telemetry Progression

```
Candidate Matches:        0 (Matcher returned no candidate correspondences)
       ↓
Initial Matcher Inliers:  0 (0.00%)  [Threshold: >= 8 pts, >= 20.0%]
       ↓
Spatial Selection:        BYPASSED
       ↓
Spatial Occupancy:        NOT EVALUATED  [Threshold: >= 33.3%, 3/9 cells]
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
- **Failure Reason:** Matcher returned no candidate correspondences. Initial homography estimation failed (0 inliers). Large-image fallback matchers (SIFT, SuperGlue) blocked by resource policy (source max_dim=4851 > 4000 px).
- **Execution Latency:** `32.66 s`

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
