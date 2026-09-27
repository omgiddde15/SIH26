# LunarReg Phase 11 — Native Cross-Sensor Transfer Diagnostic

## Scope

Phase 11 tests why the Phase 9 rotation-normalized SSC branch improves controlled rotation matching yet does not produce sufficient native IIRS ↔ OHRC registration.

## Frozen invariants

- Phase 7 SSC detector and descriptor remain unchanged.
- Phase 9 orientation estimator and descriptor remain unchanged.
- RANSAC threshold = 3.0 px; confidence = 0.995; 3×3 spatial selection; max 6 points/cell; seeds 1–5.
- No production routing or quality-gate modification.

## Track A — Anchor feasibility

- Anchor source: existing LoFTR matcher (diagnostic reference only).
- Candidate count: 199.
- Anchor pairs: 12.
- 3×3 source occupancy: 0.5556.
- Anchor status: adequate_for_descriptor_diagnostic.
- The LoFTR-derived anchors are **not ground truth** and were not independently validated as registration ground truth.

## Track B — Cross-sensor descriptor consistency

| Metric | Phase 7 SSC | Phase 9 rotation-normalized SSC |
|---|---:|---:|
| Mean L2 | 0.402052 | 0.486164 |
| Median L2 | 0.434179 | 0.479215 |
| P90 L2 | 0.490319 | 0.622815 |
| Max L2 | 0.541646 | 0.727559 |

For these normalized descriptors, lower L2 indicates greater descriptor similarity.

Phase 9 valid orientation fraction across anchors: **0.916667** (22 of 24 evaluated anchor-side orientations valid; 2 low-confidence; 0 flat).

The native cross-sensor descriptor distances are therefore higher for Phase 9 than Phase 7 across all four reported summary statistics.

This does **not** show that the orientation estimator fails to operate on native IIRS ↔ OHRC data. Most evaluated orientations were classified as valid. Instead, the evidence indicates that applying the orientation-normalized representation does not improve native cross-sensor descriptor consistency in this diagnostic.

## Track C — Fixed-anchor scale sensitivity

The scale matrix was pre-declared and evaluated without selecting or promoting a preferred scale.

| Source scale | Reference scale | Phase 7 mean L2 | Phase 9 mean L2 |
|---:|---:|---:|---:|
| 1.00 | 1.00 | 0.402052 | 0.486164 |
| 1.00 | 1.50 | 0.486728 | 0.497523 |
| 1.00 | 1.25 | 0.429595 | 0.470074 |
| 1.00 | 0.75 | 0.414044 | 0.500520 |
| 1.00 | 0.50 | 0.401065 | 0.503671 |
| 1.50 | 1.00 | 0.524679 | 0.518207 |
| 1.25 | 1.00 | 0.484710 | 0.522008 |
| 0.75 | 1.00 | 0.380075 | 0.495239 |
| 0.50 | 1.00 | 0.358852 | 0.416821 |

Phase 9 has a lower mean L2 than Phase 7 in only one of the nine tested scale conditions (1.50 / 1.00), and the difference there is small. The pre-declared scale matrix therefore does not provide evidence that a simple global rescaling consistently removes the Phase 9 native cross-sensor descriptor gap.

## Track D — End-to-end native IIRS ↔ OHRC

| Method | Candidates | Initial inliers | Ratio | Fit RMSE | Held-out RMSE | Valid |
|---|---:|---:|---:|---:|---:|---|
| Phase 7 SSC | 229 | 10 | 0.0437 | 0.2702 | 1.2399 | True |
| Phase 9 Rot-Norm SSC | 224 | 7 | 0.0312 | 0.8757 | None | False |

Phase 9 did not satisfy the minimum 8-inlier requirement for the independent held-out check (7 < 8). Therefore the Phase 9 fit RMSE of 0.8757 must **not** be treated as a directly comparable validated registration-accuracy result.

The defensible comparison is that Phase 7 completed valid held-out validation, while Phase 9 did not.

## Phase 11 evidence-based diagnosis

The combined evidence supports the following diagnosis:

> **The native IIRS ↔ OHRC limitation is not adequately explained by rotation sensitivity alone. Although rotation-normalized SSC improves controlled rotation consistency, it produces higher descriptor distances at LoFTR-derived native cross-sensor anchors and does not achieve valid end-to-end held-out registration. The pre-declared global scale perturbations do not consistently remove this native descriptor gap. These results support cross-sensor descriptor compatibility as a key limitation. A local-footprint or local-structural-context mismatch remains a plausible contributing hypothesis, but Phase 11 does not isolate or prove that specific cause.**

### What Phase 11 weakens

- The native failure is **not sufficiently explained by rotation sensitivity alone**.
- The native failure is **not sufficiently explained by a single global scale mismatch**.
- The evidence does **not** support claiming that the Phase 9 orientation estimator simply fails on IIRS ↔ OHRC.

### What Phase 11 supports

- Cross-sensor descriptor compatibility is a measured limitation of the tested Phase 9 representation.
- Further research should focus on cross-sensor local representation compatibility rather than simply adding another rotation-normalization variant.
- Local footprint / structural-context mismatch should remain a **research hypothesis**, not a proven diagnosis.

## Production boundary

No production routing, quality gate, Locked LoFTR baseline, or common downstream mathematics is modified.

Recommended project status:

- **Phase 11: COMPLETE**
- **Phase 7 SSC: FROZEN RESEARCH BASELINE**
- **Phase 9 Rot-Norm SSC: FROZEN RESEARCH BRANCH**
- **Production pipeline: UNCHANGED**

No automatic winner, parameter promotion, or production decision is applied.
