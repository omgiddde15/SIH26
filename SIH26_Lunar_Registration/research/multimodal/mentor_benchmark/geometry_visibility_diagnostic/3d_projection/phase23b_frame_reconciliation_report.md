# Phase 23B — Frame Reconciliation Report

**Generated:** 2026-09-24T05:37:49Z

## Verified Phase 23A.7 Frame Results (Imported, Not Recomputed)

- IAU_MOON ↔ MOON_ME_DE421 max surface displacement: **66.0 m**
- IAU_MOON ↔ MOON_ME_DE421 min surface displacement: **22.7 m**

## Recalculated Surface Arc (Phase 23B, for completeness)

- Rotation angle upper bound: `0.00218 deg`
- Arc at south pole: `66.1 m`
- Arc at lat -85 deg: `5.76 m`

## Comparison to Observed Residuals

- Observed residual range: `435–1634 m`
- Frame effect as fraction: `15.2%–4.0%` of observed residual
- **Classification: `NOT_SUFFICIENT_TO_EXPLAIN`**

## Additional Frame Candidates

### MOON_ME_DE421 vs MOON_ME (generic)
- **Status:** `NOT_A_DISTINCT_FRAME`
- MOON_ME in the SPICE kernel moon_080317.tf is defined as an alias of MOON_ME_DE421 (TKFRAME_-31001_RELATIVE = 'MOON_ME_DE421'). These are the same physical frame — no separate rotation exists.

### IAU_MOON vs MOON_PA_DE421
- **Status:** `INTERMEDIATE_FRAME`
- MOON_PA_DE421 is the principal-axis frame from DE421. IAU_MOON is a low-degree Euler-angle approximation. MOON_ME_DE421 is derived from MOON_PA_DE421 with a small offset. Combined IAU_MOON → MOON_PA_DE421 → MOON_ME_DE421 chain was verified in Phase 23A.7 with the same upper-bound result.

### ULCN2005 vs MOON_ME_DE421
- **Status:** `INSUFFICIENT_INFORMATION`
- ULCN2005 (Unified Lunar Control Network 2005) is an older control network realization. The delivered GeoTIFF contains no reference to ULCN2005. If the reference raster was tied to ULCN2005, an offset of unknown magnitude could exist. No transformation from ULCN2005 to MOON_ME_DE421 is available in the audited SPICE kernels. Status: INSUFFICIENT_INFORMATION.

