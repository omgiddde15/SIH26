# Mentor Dataset Case Report: OHRC_PAIR_02

**Dataset ID:** `OHRC_PAIR_02`  
**Instrument:** OHRC (Optical High Resolution Camera, Chandrayaan-2)  
**Case Classification:** **`SAFE REJECTION`**  
**Pipeline Mode:** Frozen Adaptive Production Engine  
**Execution Timestamp:** September 23, 2026  

---

## 1. Case Provenance & Input Metadata

| Parameter | Source (Moving Image) | Reference (Target Image) |
| :--- | :--- | :--- |
| **Filename** | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif` | `OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif` |
| **Dimensions** | `648x5059 px` | `2593x6279 px` |
| **Native GSD** | `0.27 m/px` | `5.0` |
| **Effective GSD** | `5.0 m/px` | `5.0` |
| **Effective Scale** | **Verified 1:1 effective pixel scale: 5.0 m/px source <-> 5.0 m/px reference** | |
| **Raw Dtype** | `uint8` | `uint8` |
| **Normalized Dtype**| `uint8` (display & matcher representation) | `uint8` |
| **Illumination** | Sun El: `5.10 deg`, Solar Inc: `84.90 deg` | Unverified |
| **Lunar Area** | `South Pole` | `South Pole` |
| **Metadata Status**| `VERIFIED` | |

---

## 2. Separated Telemetry Progression

```
Candidate Matches:        221
       ↓
Initial Matcher Inliers:  5 (2.26%)  [Threshold: >= 8 pts, >= 20.0%]
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
- **Failure Reason:** Initial inliers below threshold (5 < 8); Inlier ratio below threshold (2.26% < 20.0%). Large-image fallback matchers (SIFT, SuperGlue) blocked by resource policy (ref max_dim=6279 > 4000 px).
- **Execution Latency:** `30.17 s`

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
- **Factor Analysis:** Results are consistent with substantial illumination/shadow differences, but this benchmark does not isolate illumination as the causal factor.
