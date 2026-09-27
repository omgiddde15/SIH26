# 04 — Research Findings (Strongest Validated Only)

> This slide section summarizes only the **strongest, most defensible** findings from the entire research program (Phases 01–24A). Results with incomplete control or unpublished status are omitted.

## 4.1 Finding 1 — No Single Research Representation Consistently Solves the Native Cross-Sensor Problem

**Experiment coverage:** Multimodal representation tests across RIFT2, rotation-normalized SSC, Sobel-gradient NCC, phase-correlation, FAST+ZMUV structural descriptors, detector-vs-descriptor diagnostics, illumination ablation, rotation ablation, scale ablation.

**Verified finding:**
> *"No single research representation (detector / descriptor / domain transform) was consistently able to close the cross-sensor gap across all 6 mentor datasets. Some methods improved the initial inlier ratio on a subset, but worsened held-out RMSE on others."*

**Allowed wording for PPT:**
- "Multiple candidate representations were explored; each succeeded on a subset."
- "This motivated an adaptive (multi-matcher) design rather than a one-size-fits-all matcher."

**Forbidden wording:**
- ❌ "all methods failed" → (we deliberately do not over-claim failure; some subsets improved)
- ❌ "we proved no representation works"

## 4.2 Finding 2 — Initial Match Quality Alone Is Not Sufficient

**Experiment:** Scale-ablation study and downstream hold-out comparison.

**Verified finding:**
> *"Several scale configurations increased the initial inlier ratio while worsening the independent held-out RMSE. A high initial inlier count is therefore a necessary but NOT sufficient indicator of a correct registration."*

This is the single most important reason for the 5-stage quality gate in production (§3.2).

**Allowed wording for PPT:**
- "Initial match count is not enough; we must independently validate."
- "This is why our architecture holds out 25% across 5 seeds, even if the other 75% looks perfect."

**Forbidden wording:**
- ❌ "scale invariant"
- ❌ "we solved the scale problem"

## 4.3 Finding 3 — Sub-Pixel Correspondence Localization on Controlled Known-Transform Data

**Experiment:** Synthetic controlled pair with known ground truth (rotation 2°, translation tx=10, ty=10 px).

**Verified finding:**
> *"Sub-pixel correspondence localization was demonstrated on controlled known-transform data (CONTROL_2: R=2°, tx=10, ty=10 px → 1867 LoFTR inliers, hold-out validated)."*

**Strictly allowed wording only:**
- "Sub-pixel on controlled known-transform data."
- "Correspondence precision under a pinned, known ground-truth transform."

**Forbidden wording (ABSOLUTELY DO NOT USE IN PPT):**
- ❌ "sub-pixel accuracy on lunar imagery"
- ❌ "sub-pixel ground truth on OHRC"
- ❌ any direct claim of sub-pixel on Chandrayaan data

## 4.4 Finding 4 — Illumination Variation Is Consistent with OHRC Failure

**Experiment:** Illumination ablation on synthetic subsets; mentor OHRC sun elevation −0.31° to 5.10°.

**Verified finding (CAREFUL, CAUSALITY NOT PROVEN):**
> *"OHRC mentor results (1.72%–5.10% initial inlier ratios, all below 20% gate) are **consistent with** substantial illumination/shadow differences across orbits. The benchmark does **not** isolate illumination as the causal factor. Additional controlled experiments would be required to prove causality."*

**Allowed wording for PPT:**
- "Results are consistent with illumination/shadow differences."
- "Illumination is a plausible contributing factor (not yet proven causal)."

**Forbidden wording:**
- ❌ "sun-angle invariant"
- ❌ "illumination caused the failure"

## 4.5 Finding 5 — IIRS Cross-Sensor Representation Mismatch Is Consistent with Failure

**Experiment:** IIRS pairs (A, B) with percentile-normalized radiance-to-uint8 conversion.

**Verified finding (CAREFUL, CAUSALITY NOT PROVEN):**
> *"IIRS mentor results (n_candidates: 45 and 0; ratios 11.11% and 0%) are consistent with a cross-sensor representation/modality mismatch. Causality not isolated."*

**Allowed wording for PPT:**
- "Modality mismatch between spectral radiance (IIRS) and panchromatic reflectance (reference) is a plausible contributing factor."

**Forbidden wording:**
- ❌ "IIRS cannot be registered" → (we only tested 2 cases; a future representation may work)

## 4.6 Finding 6 — Resource-Aware Tiled LoFTR Enables Safe Large-Image Processing

**Verified finding:**
> *"OHRC_PAIR_01 reference 5916×4232 → estimated 3.15 GB full-image LoFTR footprint. Auto-demoted to tiled LoFTR; completed in 58.86 s, no OOM, full telemetry recorded."*

All 6 mentor cases executed with zero runtime crashes.

## 4.7 Finding 7 — Adaptive Router Chooses Sensible Default

**Verified finding:**
> *"Router selected LoFTR 6/6 times on the heterogeneous mentor set. Resource guard correctly blocked SIFT/SuperGlue fallbacks above 4000 px to prevent OOM, ensuring deterministic telemetry."*
