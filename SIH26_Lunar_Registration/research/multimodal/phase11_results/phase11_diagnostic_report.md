# LunarReg Phase 11 — Native Cross-Sensor Transfer Diagnostic

## Scope
Phase 11 tests why the Phase 9 rotation-normalized SSC branch improves controlled rotation matching yet does not produce sufficient native IIRS ↔ OHRC registration.

## Frozen invariants
- Phase 7 SSC descriptor and detector remain unchanged.
- Phase 9 orientation estimator and descriptor remain unchanged.
- RANSAC threshold = 3.0 px; confidence = 0.995; 3×3 selection; max 6 points/cell; seeds 1–5.
- No production routing or quality-gate modification.

## Track A — Anchor feasibility
- Anchor source: existing LoFTR matcher (diagnostic reference only).
- Candidate count: 199
- Anchor pairs: 12
- 3×3 source occupancy: 0.5556
- Anchor status: adequate_for_descriptor_diagnostic

## Track B — Cross-sensor descriptor consistency
| Metric | Phase 7 SSC | Phase 9 rotation-normalized SSC |
|---|---:|---:|
| Mean L2 | 0.4020520746707916 | 0.48616448044776917 |
| Median L2 | 0.43417975306510925 | 0.47921547293663025 |
| P90 L2 | 0.49031829833984375 | 0.6228148937225342 |
| Max L2 | 0.5416451096534729 | 0.7275586128234863 |
- Phase 9 valid orientation fraction across anchors: 0.916667

## Track C — Fixed-anchor scale sensitivity
The scale matrix was pre-declared and evaluated without selecting or promoting a preferred scale.

| Source scale | Reference scale | Phase 7 mean L2 | Phase 9 mean L2 |
|---:|---:|---:|---:|
| 1.00 | 1.00 | 0.4020520746707916 | 0.48616448044776917 |
| 1.00 | 1.50 | 0.4867275059223175 | 0.49752315878868103 |
| 1.00 | 1.25 | 0.42959514260292053 | 0.4700741767883301 |
| 1.00 | 0.75 | 0.4140442907810211 | 0.5005198121070862 |
| 1.00 | 0.50 | 0.4010654389858246 | 0.5036701560020447 |
| 1.50 | 1.00 | 0.5246789455413818 | 0.5182065963745117 |
| 1.25 | 1.00 | 0.4847106635570526 | 0.5220077037811279 |
| 0.75 | 1.00 | 0.38007521629333496 | 0.4952388107776642 |
| 0.50 | 1.00 | 0.35885176062583923 | 0.4168214797973633 |

## Track D — End-to-end native IIRS ↔ OHRC
| Method | Candidates | Initial inliers | Ratio | Fit RMSE | Held-out RMSE | Valid |
|---|---:|---:|---:|---:|---:|---|
| Phase 7 SSC | 229 | 10 | 0.0437 | 0.2702 | 1.2399 | True |
| Phase 9 Rot-Norm SSC | 224 | 7 | 0.0312 | 0.8757 | None | False |

## Interpretation boundary
Phase 11 is diagnostic. It does not declare a winner, tune thresholds, or promote any research branch. Descriptor-level evidence and end-to-end registration evidence must be interpreted together.

## Production boundary
No production routing, quality gate, Locked LoFTR baseline, or common downstream mathematics is modified.