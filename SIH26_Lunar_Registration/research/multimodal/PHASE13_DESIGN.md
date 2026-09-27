# LunarReg Phase 13 — Angle/Footprint Transfer Diagnostic

## Research question

Does the compact local footprint identified in Phase 12 preserve or improve the angle-robustness behavior of the frozen Phase 9 rotation-normalized SSC branch?

## Main objective

The overarching LunarReg objective remains robust image registration when acquisition angle and illumination conditions differ.

Phase 13 is research-only. It does not modify production routing, the 20% quality gate, Locked LoFTR, RANSAC mathematics, or common downstream registration.

## Pre-declared configurations

Four controlled configurations are evaluated:

1. Phase 7 SSC, baseline footprint: patch 7×7, radius 4.0 px
2. Phase 9 rotation-normalized SSC, baseline footprint: patch 7×7, radius 4.0 px
3. Phase 7 SSC, compact footprint: patch 5×5, radius 3.0 px
4. Phase 9 rotation-normalized SSC, compact footprint: patch 5×5, radius 3.0 px

No other footprint is evaluated in Phase 13.

## Test set

### Synthetic in-plane rotations
- +10°
- +20°
- +30°
- -20°

### Real lunar controls
- pair_01: rotation-change
- pair_02: viewpoint-change
- pair_03: sun-angle-change

### Native cross-sensor pair
- IIRS source: souse.jpeg
- OHRC reference: ref.jpeg

The native pair is evaluated at baseline and compact footprints.

## Metrics

For each run:
- candidate count
- initial inliers
- initial inlier ratio
- 3×3 spatial occupancy
- fit RMSE
- independent held-out RMSE
- held-out validity
- failure stage/reason
- runtime

Held-out validation remains the validity criterion. A run with fewer than 8 final/initial inliers that cannot complete the independent held-out check is not treated as a validated registration result.

## Scientific interpretation boundary

Phase 13 does not declare a footprint winner.

The key question is whether the compact footprint changes the behavior of the rotation-normalized branch across multiple angle-controlled cases while preserving or improving native cross-sensor transfer.

A single successful compact run is insufficient to claim general angle robustness.

## Production boundary

No production files are modified by this benchmark.
