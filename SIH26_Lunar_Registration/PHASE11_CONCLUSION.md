# Phase 11 Conclusion

Phase 11 completed the native cross-sensor transfer diagnostic.

The main evidence is that Phase 9 rotation-normalized SSC has worse descriptor-level cross-sensor consistency than Phase 7 at the 12 LoFTR-derived diagnostic anchors:

- Mean L2: 0.4862 vs 0.4021
- Median L2: 0.4792 vs 0.4342
- P90 L2: 0.6228 vs 0.4903
- Max L2: 0.7276 vs 0.5416

Phase 9 orientations were still classified as valid for 22/24 evaluated anchor-side orientations, so the result should not be described as a complete orientation-estimation failure.

The pre-declared scale sensitivity matrix also does not show a consistent recovery of Phase 9 cross-sensor descriptor similarity.

End-to-end, Phase 7 completed valid independent held-out validation (RMSE 1.2399), while Phase 9 stopped before that check because it produced only 7 initial inliers (<8).

Therefore:

1. Rotation sensitivity alone is not a sufficient explanation for the native IIRS ↔ OHRC limitation.
2. A simple global scale mismatch is not a sufficient explanation.
3. Cross-sensor descriptor compatibility is a measured limitation of the tested Phase 9 representation.
4. Local-footprint / local-structural-context mismatch remains a hypothesis for future controlled research, not a proven cause.
5. Phase 9 remains research-only and frozen; production remains unchanged.
