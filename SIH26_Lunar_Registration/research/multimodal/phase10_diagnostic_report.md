# LunarReg Phase 10 — Detector vs Descriptor Diagnostic

## Scope

Phase 10 separates keypoint repeatability from descriptor rotation consistency under frozen Phase 7/8 SSC and Phase 9 rotation-normalized SSC settings.

## Frozen settings

- Detector: Independent Sobel-gradient + FAST, threshold=10, fallback=5, margin=8, max=1500.
- SSC: frozen 21-D descriptor, 7x7 patches, R=4 px, six fixed neighbours.
- Matching: KNN k=2/k=1, mutual check, NNDR=0.90.
- Phase 9 orientation: Sobel structure tensor, 7x7 Gaussian sigma=1.5, coherence<0.15 or trace<1e-4 -> theta=0, R(+theta).
- Downstream: RANSAC 3.0 px, confidence 0.995, 3x3 spatial selection, max 6/cell, seeds 1-5.

## Interpretation

Use detector repeatability and descriptor-only distances as evidence about component contribution. Do not treat these diagnostics as proofs of causality.

### Integrated diagnostic
Diagnosis is intentionally left for evidence review. Compare Track A detector repeatability, Track B descriptor-only rotation consistency, Track C controlled correspondence recovery, and Track D end-to-end behavior. Do not apply a post-hoc numeric winner threshold to force a detector-dominant or descriptor-dominant label.

## Production boundary

Phase 10 is research-only. No production routing, quality gates, Locked LoFTR, or common downstream code is changed by this diagnostic.

### Outputs

- phase10_detector_diagnostic_results.csv
- phase10_descriptor_diagnostic_results.csv
- phase10_controlled_matching_results.csv
- phase10_end_to_end_results.csv