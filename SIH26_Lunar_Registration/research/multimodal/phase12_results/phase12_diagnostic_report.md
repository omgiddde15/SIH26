# LunarReg Phase 12 — Controlled Local-Footprint Diagnostic

## Research question
Does the local image footprint used by the frozen Phase 7 SSC and Phase 9 rotation-normalized SSC representations materially affect native IIRS ↔ OHRC cross-sensor descriptor compatibility?

## Frozen / controlled elements
- Exact Phase 11 LoFTR-derived anchor pairs are reused; anchors are not ground truth.
- Phase 7 descriptor formula, 21-D dimension, matching policy, and detector remain unchanged.
- Phase 9 orientation estimator remains at tensor window 7, sigma 1.5, coherence threshold 0.15, trace threshold 1e-4, orientation sign +1.
- RANSAC threshold = 3.0 px; seeds = 1–5; common downstream unchanged.
- No production routing, quality gate, or Locked LoFTR modification.
- No footprint is selected or promoted automatically.

## Pre-declared footprint matrix
| Condition | Patch size | Radius |
|---|---:|---:|
| compact | 5×5 | 3.0 px |
| baseline | 7×7 | 4.0 px |
| medium | 9×9 | 5.0 px |
| broad | 11×11 | 7.0 px |

## Track A — Anchor provenance
- Anchor source: existing LoFTR matcher
- Anchor is ground truth: False
- Anchor pairs reused: 12

## Track B — Fixed-anchor descriptor footprint sensitivity
Lower L2 means greater descriptor similarity. The key diagnostic is the paired Phase 9 − Phase 7 distance difference at the same anchors.

| Footprint | P7 mean L2 | P9 mean L2 | P9−P7 mean | P9 better / equal / worse | P9 orientation valid |
|---|---:|---:|---:|---:|---:|
| compact | 0.512050 | 0.544219 | 0.032169 | 7 / 0 / 5 | 0.9167 |
| baseline | 0.402052 | 0.486164 | 0.084112 | 4 / 0 / 8 | 0.9167 |
| medium | 0.362924 | 0.494074 | 0.131151 | 2 / 0 / 10 | 0.9167 |
| broad | 0.350969 | 0.479228 | 0.128259 | 3 / 0 / 9 | 0.9167 |

## Interpretation rules
- The fixed-anchor track isolates descriptor-footprint effects because the anchor locations are held constant.
- A consistent reduction in the Phase 9 − Phase 7 descriptor-distance gap across multiple pre-declared footprints would support footprint sensitivity as a contributor.
- Failure to reduce that gap across the matrix would weaken the hypothesis that footprint size alone explains the Phase 11 transfer problem.
- These are descriptive patterns, not an automatic winner-selection rule.

## Track C — Secondary end-to-end confirmation
End-to-end runs are shown for context only. They are not used to choose a footprint because detector behavior and downstream registration are also involved.

| Footprint | Method | Candidates | Initial inliers | Ratio | Fit RMSE | Held-out RMSE | Valid |
|---|---|---:|---:|---:|---:|---:|---|
| compact | Phase 7 SSC | 249 | 8 | 0.0321 | 0.8448 | 4.9364 | True |
| compact | Phase 9 Rot-Norm SSC | 240 | 8 | 0.0333 | 0.9399 | 2.5773 | True |
| baseline | Phase 7 SSC | 229 | 10 | 0.0437 | 0.2702 | 1.2399 | True |
| baseline | Phase 9 Rot-Norm SSC | 224 | 7 | 0.0312 | 0.8757 | None | False |
| medium | Phase 7 SSC | 231 | 6 | 0.026 | 0.7995 | None | False |
| medium | Phase 9 Rot-Norm SSC | 237 | 6 | 0.0253 | 0.9407 | None | False |
| broad | Phase 7 SSC | 200 | 7 | 0.035 | 1.2788 | None | False |
| broad | Phase 9 Rot-Norm SSC | 226 | 6 | 0.0265 | 0.5003 | None | False |

## Production boundary
Phase 12 is research-only. No production router, 20% quality gate, Locked LoFTR baseline, RANSAC mathematics, or common downstream implementation is modified.