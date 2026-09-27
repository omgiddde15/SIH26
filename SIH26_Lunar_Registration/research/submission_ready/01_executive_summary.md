# 01 — Executive Summary

## Project Title

**Adaptive Lunar Image Registration with Evidence-Based Matching and Safe Rejection**
SIH Problem Code: **SIH26166** (LunarReg)

## One Paragraph Elevator Pitch

We present **LunarReg**, a production-grade image-registration system for Chandrayaan-2 imagery that places **reliability above forced alignment**. Given diverse sensors (OHRC, IIRS, TMC), extreme illumination variation, and uncertain reference-product provenance, forced alignment produces dangerous false registrations. LunarReg solves this through three innovations: (1) an **adaptive matcher router** that picks SIFT / LoFTR / SuperGlue based on image characterization, (2) a **multi-stage evidence quality gate** (initial consensus → spatial occupancy → independent hold-out validation) that rejects unreliable results rather than lowering thresholds, and (3) a **physical/geodetic audit layer** for lunar south-polar data. Evaluated on 6 mentor datasets under frozen production criteria, the system **safely rejected all 6** (zero false registrations produced). On controlled known-transform data it produced independently validated sub-pixel alignment. This makes LunarReg suitable as a **safety-critical first stage** in a planetary image-processing pipeline.

## Key Figures (Judge-Friendly)

| What | Number |
|:---|---:|
| Mentor datasets evaluated | **6** (4 OHRC, 2 IIRS) |
| Safe rejections under frozen quality gate | **6 / 6** |
| False registrations produced | **0** |
| Production quality-gate stages | **5** (cand → inl → ratio → occ → hold-out) |
| Adaptive matcher options | **3** (SIFT / LoFTR / SuperGlue) |
| Spatial selection grid | 3×3 cells (max 6 pts / cell) |
| Hold-out validation seeds | 5 (75/25 splits) |
| Coarse image-space hypotheses (Phase 24A) | **196** (±3 km lattice) |
| Production crashes on 7k×7k GeoTIFFs | **0** |

## 7 Strongest Evidence Points (1 slide each in PPT)

1. **Safe rejection integrity.** 6/6 mentor datasets routed through the full pipeline; 0/6 produced a false homography because the gate suppressed output below threshold.
2. **Controlled positive validation.** On a synthetic known-transform scene (rotation 2°, translation 10/10 px, R=2°) the pipeline returned **1867 inliers** and passed hold-out — proving the matcher and gate *do* register when structure exists.
3. **Controlled negative validation.** A deliberately non-overlapping crop produced 0 inliers and SCREEN_FAIL — proving the system detects non-overlap.
4. **Resource guard + memory-safe tiled LoFTR.** Largest mentor (ref 5916×4232) ran without OOM via tiled LoFTR in 58.86 s.
5. **Sub-pixel on controlled data.** Sub-pixel correspondence localization demonstrated on a known-transform controlled pair (NOT asserted on real lunar imagery without ground truth).
6. **Physical projection chain audited.** Delivered pixel → detector geometry → camera ray → spacecraft ephemeris/attitude → DEM intersection → Polar Stereographic reference coordinates: all stages documented.
7. **Coarse prefilter characterization.** 196 deterministic image-space hypotheses tested; 16 showed cheap structural evidence but none passed the frozen LoFTR quality gate — placing a quantitative bound on simple translational explanations.

## Technical Novelty (1 Slide)

1. Adaptive matcher selection characterized by input (not one-size-fits-all)
2. Five-stage geometric quality control with hard thresholds
3. 3×3 spatially distributed correspondence selection to prevent degenerate solutions
4. Independent hold-out validation across 5 random seeds
5. Resource-aware matcher execution (memory-safe tiled LoFTR for large GeoTIFFs)
6. Evidence-based safe rejection (homography completely withheld below gate)
7. Physical/geodetic audit layer for lunar imagery (Phase 23B program)

## Impact / Practical Value (1 Slide)

- **ISRO / ISRO-data users:** Safety-first component that filters out unreliable candidate alignments before downstream mapping or geodetic correction.
- **Planetary remote sensing community:** Reproducible, frozen benchmark with telemetry for every stage (not just final pass/fail) — enables meta-studies of matcher failure modes.
- **Defense/navigation:** The safe-rejection pattern generalizes to any vision-based navigation where a *miss* is less costly than a *wrong* registration (e.g., autonomous landing hazard avoidance).
- **Educational:** Cleanly separated research (adaptive matcher, prefilters) vs production (4-core frozen) — excellent teaching case for evidence-based engineering discipline.
