# LunarReg Phase 14 — Controlled Cross-Sensor + Rotation Transfer Diagnostic

## Research question

Phase 13 showed that changing the local SSC footprint does not resolve the IIRS ↔ OHRC rotation-transfer failure.

Phase 14 now isolates the remaining question:

> When the IIRS image is rotated by a known angle, does the Phase-9-derived rotation-normalized SSC representation fail because of rotation sensitivity itself, or because rotation normalization does not preserve cross-sensor compatibility?

## Why this experiment is different

Phase 14 is a **fixed-anchor descriptor diagnostic**.

It does NOT run the detector or descriptor matcher to discover correspondences.

Instead, it reuses the 12 LoFTR-derived Phase 11 anchor pairs and applies the exact known synthetic rotation transform to the IIRS-side anchor coordinates.

Thus the experiment knows exactly where each original anchor moves under:
- +10°
- +20°
- +30°
- -20°

The anchor locations remain diagnostic references, not ground truth.

## Tracks

### Track A — Same-sensor rotation consistency

For each anchor:

- descriptor on original IIRS at `(x, y)`
- descriptor on rotated IIRS at the exactly transformed anchor `(x', y')`

Compare L2 distance.

This isolates the descriptor's response to rotation without cross-sensor effects.

### Track B — Cross-sensor transfer under rotation

For the same anchor:

- descriptor on rotated IIRS at `(x', y')`
- descriptor on original OHRC at the Phase 11 reference anchor

Compare L2 distance.

Compare this against the native zero-rotation cross-sensor distance.

This isolates the combined cross-sensor + rotation transfer.

### Track C — Orientation diagnostic

For the Phase-9-derived branch record:

- base orientation
- rotated orientation
- valid/low-confidence/flat status
- angular error after accounting for the known synthetic rotation

The orientation is evaluated modulo π because the structure-tensor orientation is axial.

## Methods

1. Phase 7 SSC, baseline 7×7 / R4.
2. Phase-9-derived Rot-Norm SSC, baseline 7×7 / R4.

The Phase-9-derived branch reuses the exact frozen Phase 9 orientation estimator and orientation sign convention, but it is evaluated only as a controlled descriptor diagnostic.

## Frozen

- Phase 7 detector
- Phase 7 21-D SSC descriptor math
- Phase 9 orientation estimator
- 7×7 patch / 4 px radius
- same six radial directions
- no matcher threshold changes
- no RANSAC
- no production changes
- no automatic selection

## Interpretation

The key evidence is:

1. Same-sensor rotation distance.
2. Cross-sensor distance at zero rotation.
3. Cross-sensor distance after known rotation.
4. Increment in cross-sensor distance caused by rotation.

A result showing low same-sensor rotation distance but a large cross-sensor distance would support a cross-sensor compatibility limitation rather than simple rotation sensitivity.

No winner or production decision is applied.
