# 02 — Problem & Proposed Solution

## 2.1 The Problem

Planetary remote-sensing missions routinely deliver images from heterogeneous sensors under extreme, uncontrolled observation conditions. For the Chandrayaan-2 south-polar program these include:

- **Multiple instruments with fundamentally different representations.**
  - OHRC (Optical High Resolution Camera): ~0.25 m native panchromatic → delivered at ~5.0 m reference projection.
  - TMC2 (Terrain Mapping Camera 2): ~5 m stereo.
  - IIRS (Imaging Infrared Spectrometer): ~80–95 m spectral radiance cubes → not physical radiance; normalized for alignment only.
- **Extreme illumination geometry near the lunar south pole.** Sun elevations for delivered OHRC mentor pairs range from **−0.31° to 5.10°**, producing kilometer-long shadows that dominate the visual appearance of the same terrain across different orbits.
- **Reference product provenance uncertainty.** The delivered reference GeoTIFFs embed a Polar Stereographic CRS, but **no authoritative upstream product ID or provenance link** could be recovered from TIFF tags, PDS4 labels, or local candidate raster comparison. Without a pinned reference frame, apparent "alignment errors" may actually be unmodeled reference-product drifts rather than matcher failures.
- **Resource pressure.** Mentor GeoTIFFs extend to ~5916×4232 px (OHRC) and 7783×960 px (IIRS). A naive "run every matcher" strategy exceeds 3 GB single-process RAM and falls outside typical competition hardware envelopes.

### Why Existing Methods Struggle

| Shortcoming of classic single-matcher pipelines | How it manifests on lunar data |
|:---|:---|
| **Single matcher assumption** (e.g., SIFT-only) | Fails on low-texture shadow bands or radiance-domain IIRS imagery. |
| **No memory / resource policy** | OOM crashes on 6k×6k reference rasters. |
| **Threshold relaxation after failure** | Produces visually compelling but geometrically degenerate homographies. |
| **Sparse-inlier degeneracy (all matches in one corner)** | Homography matrix overfits a 1-px region; passes a simple count gate but fails spatially. |
| **No independent validation** | "Looks good to me" slideware passes but cannot be defended quantitatively. |
| **No physical projection context** | Blames the matcher when the real failure is unmodeled reference-frame uncertainty. |

## 2.2 Proposed Solution: The LunarReg System

**Guiding motto:**
> **RELIABILITY > FORCED ALIGNMENT**

LunarReg is a multi-stage production pipeline that either registers an image pair *with independently verifiable evidence*, or explicitly **refuses to produce a registration** and classifies the case as SAFE REJECTION.

The system does **not** attempt to be universal. Instead it implements three defensive layers:

### Layer 1 — Characterization & Adaptive Routing
Every input pair is characterized for:
- bit depth / dtype / valid-pixel mask
- spatial extent → resource envelope
- sensor-inferred modality (OHRC / TMC / IIRS → LoFTR-OK vs SIFT-fallback vs SuperGlue)
- illumination proxy (DN histogram extremes)

A rule-based adaptive router then selects the **matcher most likely to succeed within the resource envelope** rather than defaulting to the deepest network.

### Layer 2 — Five-Stage Evidence Quality Gate
Correspondences must survive five independent checks:

1. **Candidate volume:** at least 10 candidate correspondence pairs
2. **Initial consensus:** at least 8 correspondences survive 3.0-px RANSAC
3. **Inlier ratio:** initial inliers / candidates ≥ 20% (blocks low-precision matchers)
4. **Spatial occupancy (3×3):** ≥ 33% of 9 grid cells occupied (blocks corner-cluster degeneracy)
5. **Independent hold-out (5 seeds):** 75/25 split re-fit → mean RMSE below consensus threshold

If **any** stage fails, the pipeline:
- sets the classification to `SAFE REJECTION`
- **withholds** the homography matrix entirely
- **skips** warp and registered-image generation
- writes full telemetry for post-mortem audit

### Layer 3 — Physical / Geodetic Audit Layer
Even if a registration passes all five quality gates, a separate audit layer records:
- nominal ray-to-DEM intersection footprint
- Polar Stereographic reference coordinates
- reference CRS interpretation (λ₀=0°, k₀=1, R=1,737,400 m)
- unresolved reference-product provenance flag

This allows a future geodetic correction **without modifying the production matcher** — the two concerns are strictly decoupled.

## 2.3 What the Solution Delivers (and What It Doesn't)

| ✅ Delivers (Verified) | ❌ Does NOT Deliver (Honest) |
|:---|:---|
| Safe rejection on 6/6 mentor datasets | Successful mentor registration (not yet — honest) |
| Independently validated alignment on controlled known-transform data | Absolute lunar geodetic accuracy |
| Zero crashes across all 6 large-format mentor GeoTIFFs | Authoritative reference-product identification |
| Resource-safe processing up to ~8k px | Scale/sun-angle invariance proofs |
| Full per-stage telemetry for research (adaptive matching, ablations) | Full OHRC/TMC/IIRS production validation on all six sensors simultaneously |
| Reproducible frozen benchmark (checksums + checkpoints) | "One-click" universal lunar alignment tool |
