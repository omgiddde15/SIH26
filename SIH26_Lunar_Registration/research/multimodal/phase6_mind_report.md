# LunarReg Phase 6 — Experimental MIND-Style Candidate Generator Report

## 1. Research Question
Phase 3–5 established that RIFT2 candidate generation, even when combined with NNDR relaxation and structural re-ranking, produces an insufficient pool of valid correspondences on the IIRS ↔ OHRC pair.

> **Core Research Question:**
> Can an independent modality-independent local self-similarity representation generate reliable IIRS ↔ OHRC correspondences that RIFT2 does not?

This experiment implements **independent structural keypoint detection and MIND-style candidate generation**, completely decoupled from RIFT2 descriptor extraction, RIFT2 matches, and Phase 5 structural fusion.

```text
Detector:
    Independent Sobel-gradient + FAST

Descriptor:
    MIND-style local self-similarity

Descriptor dimension:
    6

RIFT2 dependency:
    None
```

---

## 2. MIND-Style Algorithm & Exact LunarReg Adaptations
The implementation utilizes the principle of **MIND / modality-independent local self-similarity** (*Heinrich et al., MedIA 2012*) with documented adaptations:
1. **Independent Keypoint Detector**: Sobel spatial gradient magnitude (`to_gradient_magnitude`) followed by FAST feature detection and deterministic response-based sorting (capped at $1500$ points) with an $8\text{ px}$ boundary margin guard. Zero calls to Log-Gabor filter banks or Phase Congruency.
2. **Primary Input**: Original grayscale imagery normalized to float32 $[0, 1]$. No CLAHE preprocessing as descriptor.
3. **Patch Geometry**: Central patch $7 \times 7$ pixels ($|P| = 49$), compared against $6$ symmetric radial neighbors at distance $R = 4.0\text{ px}$ along angles $\{0^\circ, 60^\circ, 120^\circ, 180^\circ, 240^\circ, 300^\circ\}$.
4. **Subpixel Bilinear Sampling**: Exact subpixel patch extraction via `cv2.getRectSubPix`.
5. **Local Dissimilarity & Variance**: Mean squared difference across the $7 \times 7$ patch: $D_n(x) = \frac{1}{|P|} \sum (P_{\text{center}} - P_n)^2$. Local scale $V(x) = \text{median}_n(D_n(x)) + 10^{-6}$.
6. **Response & Normalization**: $M_n(x) = \exp(-D_n(x) / V(x))$, resulting in a 6-dimensional unit-$L_2$ normalized descriptor.
7. **Matching Policy**: Forward KNN ($k=2$) + backward KNN ($k=1$) mutual consistency + fixed NNDR threshold $0.90$ + spatial coordinate deduplication.
8. **Common Downstream**: Unchanged `execute_common_downstream` (RANSAC threshold $3.0\text{ px}$, confidence $0.995$, $3 \times 3$ spatial binning max 6 pts/cell, seeds 1–5).

---

## 3. Benchmark Results Table

| Pair | Detector Name | Detector Parameters | Descriptor | Scale | Base Keypoints Source | Base Keypoints Reference | Descriptor Dimension | RIFT2 Dependency | Raw Queries | NNDR Matches | Mutual Matches | Candidates | Initial Inliers | Initial Ratio | 3×3 Occupancy | Spatial CV | Fit RMSE | Independent Held-out RMSE | Runtime | Success | Failure Stage | Failure Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IIRS <-> OHRC (Native) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 1.0 | 10206 | 10768 | 6 | None | 1500 | 879 | 486 | 486 | 8 | 0.0165 | 0.4444 | 1.7139 | 1.309 | 9.2349 | 1.093 | True | None | None |
| IIRS <-> OHRC (Scale 1.0/0.5) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 0.5 | 10206 | 2790 | 6 | None | 1500 | 862 | 460 | 460 | 6 | 0.013 | 0.4444 | 1.2247 | 0.6945 |  | 1.495 | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) |
| Rotation Pair (pair_01) (Native) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 1.0 | 1628 | 1425 | 6 | None | 1475 | 858 | 433 | 433 | 7 | 0.0162 | 0.6667 | 0.8081 | 1.2361 |  | 1.232 | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) |
| Rotation Pair (pair_01) (Scale 1.0/0.5) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 0.5 | 1628 | 542 | 6 | None | 1475 | 860 | 234 | 234 | 6 | 0.0256 | 0.5556 | 1.0 | 1.1128 |  | 0.858 | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) |
| Viewpoint Pair (pair_02) (Native) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 1.0 | 8379 | 21729 | 6 | None | 1500 | 878 | 382 | 382 | 6 | 0.0157 | 0.3333 | 1.5811 | 0.8253 |  | 1.095 | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) |
| Viewpoint Pair (pair_02) (Scale 1.0/0.5) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 0.5 | 8379 | 6076 | 6 | None | 1500 | 863 | 374 | 374 | 6 | 0.016 | 0.5556 | 1.0 | 0.9719 |  | 1.05 | False | held_out_validation | Insufficient inliers for independent held-out check (6 < 8) |
| Sun Angle Pair (pair_03) (Native) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 1.0 | 49513 | 47910 | 6 | None | 1500 | 910 | 547 | 547 | 31 | 0.0567 | 0.4444 | 1.2321 | 0.7863 | 1.6395 | 1.482 | True | None | None |
| Sun Angle Pair (pair_03) (Scale 1.0/0.5) | Independent Sobel-gradient + FAST | Sobel(ksize=3) -> FAST(thresh=10, nonmax=True, margin=8, max_kps=1500) | MIND-style | 1.0 / 0.5 | 49513 | 11136 | 6 | None | 1500 | 905 | 514 | 514 | 7 | 0.0136 | 0.5556 | 1.178 | 1.3951 |  | 1.221 | False | held_out_validation | Insufficient inliers for independent held-out check (7 < 8) |

---

## 4. Comparison Against Existing Matchers on IIRS ↔ OHRC

| Matcher | Representation | Scale Mode | Candidates | Initial Inliers | Initial Inlier Ratio | Fit RMSE (px) | Held-out RMSE (px) | Success | Failure / Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LoFTR** (Phase 2) | Dense CNN+Transformer | Native (1.0/1.0) | 199 | 10 | 0.0503 | 1.3017 | 25.2809 | False | Generalizes poorly to held-out points |
| **LoFTR** (Phase 2) | Dense CNN+Transformer | Scale (1.0/0.5) | 76 | 7 | 0.0921 | 1.0053 | NaN | False | Insufficient inliers for check (7 < 8) |
| **RIFT2** (Phase 3/4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.90) | 2 | 0 | 0.0000 | NaN | NaN | False | Insufficient candidates (2 < 4) |
| **RIFT2** (Phase 4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.95) | 47 | 6 | 0.1277 | 0.2742 | NaN | False | Insufficient inliers for check (6 < 8) |
| **RIFT2** (Phase 4) | Log-Gabor PC + MIM | Native (1.0/1.0, τ=0.99) | 195 | 7 | 0.0359 | 0.9075 | NaN | False | Insufficient inliers for check (7 < 8) |
| **MIND-style** (Phase 6) | 6-D Local Self-Similarity | 1.0 / 1.0 | 486 | 8 | 0.0165 | 1.3090 | 9.2349 | True | None |
| **MIND-style** (Phase 6) | 6-D Local Self-Similarity | 1.0 / 0.5 | 460 | 6 | 0.0130 | 0.6945 | NaN | False | held_out_validation: Insufficient inliers for independent held-out check (6 < 8) |

---

## 5. Scientific Findings & Interpretation

### Primary Case: IIRS ↔ OHRC
- **Native (1.0 / 1.0)**: Generated **486** candidate correspondences, yielding **8** RANSAC inliers (Initial Inlier Ratio: 0.0165).
- **Scale (1.0 / 0.5)**: Generated **460** candidate correspondences, yielding **6** RANSAC inliers (Initial Inlier Ratio: 0.0130).
  - Failure stage: `held_out_validation` (Insufficient inliers for independent held-out check (6 < 8)).

### Evaluation under the Scientific Framework:
> **The tested Phase 6 configuration is consistent with Case B.**
> *Candidate quantity improves, but local self-similarity alone is insufficient for reliable lunar cross-sensor correspondence.*

### Representational Capacity & Terrain Characteristics:
> The 6-dimensional descriptor has limited representational capacity for highly repetitive lunar terrain, which may contribute to descriptor collisions between unrelated structures.

### Spatial Resolution & Appearance Divergence:
> The tested IIRS and OHRC images exhibit substantial differences in spatial resolution and appearance at the image level. The tested 1.0/0.5 scaling condition did not materially improve the inlier yield.

### Control Datasets (Rotation, Viewpoint, Sun Angle):
- **Rotation (`pair_01`)**: The fixed radial sampling geometry has no explicit rotation-normalization mechanism; this may contribute to the poor held-out result observed on the rotation-control pair.
- **Viewpoint (`pair_02`)**: Evaluates behavior under perspective/oblique viewpoint divergence.
- **Sun Angle (`pair_03`)**: Evaluates behavior under solar illumination changes and shadow migration.

---

## 6. Limitations & Technical Notes
1. **Non-Invariance**: The 6-D MIND-style descriptor uses a fixed radial geometry and is not mathematically invariant to arbitrary scale, in-plane rotation, or 3D viewpoint changes.
2. **Cross-Sensor Divergence**: The tested IIRS and OHRC images exhibit substantial differences in spatial resolution and appearance at the image level. The tested 1.0/0.5 scaling condition did not materially improve the inlier yield.

---

## 7. Invariant Statement

> **Only the experimental MIND-style research candidate generator was executed. Production routing, quality gates, and geometric registration mathematics remain completely unchanged.**