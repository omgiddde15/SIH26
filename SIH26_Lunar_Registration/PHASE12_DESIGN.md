# LunarReg Phase 12 — Locked Research Design

## Research question

Does the local image footprint used by Phase 7 SSC and Phase 9 rotation-normalized SSC materially affect native IIRS ↔ OHRC cross-sensor descriptor compatibility?

## Why this follows Phase 11

Phase 11 showed that:

- Phase 9 had higher descriptor L2 distances than Phase 7 at the 12 LoFTR-derived native anchors.
- Most Phase 9 anchor-side orientations were still valid.
- The pre-declared global scale matrix did not consistently remove the descriptor gap.

Therefore Phase 12 tests the remaining **local-footprint / local-context hypothesis** directly, without introducing a new matcher.

## Locked anchor policy

Phase 12 reuses the exact Phase 11 file:

```text
research/multimodal/phase11_results/phase11_loftr_anchor_pairs.json
```

The anchors remain a matcher-derived diagnostic reference, not ground truth. Phase 12 deliberately does not regenerate them.

All four footprint conditions use the same anchor pairs. Conditions are rejected rather than silently dropping edge anchors.

## Pre-declared footprint matrix

| Condition | Patch | Radius |
|---|---:|---:|
| compact | 5×5 | 3 px |
| baseline | 7×7 | 4 px |
| medium | 9×9 | 5 px |
| broad | 11×11 | 7 px |

The footprint changes both the sampled patch size and radial extent while preserving the same 7-position, 21-pair SSC structure.

## Controlled elements

Phase 7:

- same SSC formula
- 21-dimensional descriptor
- same self-similarity normalization
- same fixed anchors

Phase 9:

- same structure-tensor orientation estimator as Phase 9
- tensor window = 7
- sigma = 1.5
- coherence threshold = 0.15
- trace threshold = 1e-4
- orientation sign = +1
- only the SSC sampling footprint changes

Common downstream remains unchanged.

## Primary evidence

The primary result is the fixed-anchor descriptor comparison:

```text
Phase 7 mean/median/P90 L2
Phase 9 mean/median/P90 L2
Phase 9 - Phase 7 paired distance
number of anchors where Phase 9 is lower/equal/higher
Phase 9 orientation validity fraction
```

Lower L2 means greater descriptor similarity.

## Interpretation rules

A consistent reduction in the Phase 9 − Phase 7 distance gap across multiple pre-declared footprints would support footprint sensitivity as a contributor.

If the gap remains broadly positive across the matrix, footprint size alone is not sufficient to explain the Phase 11 transfer problem.

No footprint is called optimal or promoted automatically.

## Secondary evidence

The benchmark also runs end-to-end Phase 7 and Phase 9 for every footprint. These runs are secondary because detector behavior and registration geometry also change with the footprint boundary guard.

Do not use end-to-end results to retroactively select a footprint.

## Production boundary

Do not modify:

- `adaptive_engine.py`
- adaptive routing
- the 20% quality gate
- Locked LoFTR
- RANSAC/common downstream mathematics

Phase 12 is research-only.
