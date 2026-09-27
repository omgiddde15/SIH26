# LunarReg Phase 16 — Cross-Sensor Representation Ablation Report

**Anchor pairs used**: 12 (reused from Phase 11 / 14 / 15 LoFTR-derived diagnostic anchors)

## Scientific Purpose & Protocol
This experiment evaluates whether changing the underlying image representation supplied to the frozen Phase 7 SSC descriptor reduces the native IIRS↔OHRC cross-sensor descriptor mismatch.

### Exact Transformations Used:
- **Condition A (Baseline Grayscale)**: Standard 2D uint8 grayscale representation identical to Phase 7 baseline.
- **Condition B (Baseline CLAHE)**: Contrast Limited Adaptive Histogram Equalization with `clipLimit=2.0, tileGridSize=(8, 8)`.
- **Condition C (Histogram Normalized)**: Global cumulative histogram equalization via `cv2.equalizeHist`.
- **Condition D (Gradient Magnitude)**: Spatial Sobel gradient magnitude normalized to [0, 255].
- **Condition E (Local Gradient Normalized)**: Sobel gradient magnitude normalized by local standard deviation (15×15 window, eps=10.0, 99.9th percentile clip).

## Aggregate Results (5 Tested Representations)

| condition_code | representation               | anchor_pairs_total | valid_anchor_count | cross_sensor_mean_l2 | cross_sensor_median_l2 | cross_sensor_p90_l2 | cross_sensor_max_l2 | delta_vs_baseline_mean | delta_vs_baseline_median | delta_vs_baseline_p90 | same_sensor_rep_shift_mean | same_sensor_rep_shift_median |
| -------------- | ---------------------------- | ------------------ | ------------------ | -------------------- | ---------------------- | ------------------- | ------------------- | ---------------------- | ------------------------ | --------------------- | -------------------------- | ---------------------------- |
| Condition A    | Baseline Grayscale (Phase 7) | 12                 | 12                 | 0.4021               | 0.4342                 | 0.4903              | 0.5416              | 0.0000                 | 0.0000                   | 0.0000                | 0.0000                     | 0.0000                       |
| Condition B    | Baseline CLAHE               | 12                 | 12                 | 0.3985               | 0.4399                 | 0.4638              | 0.5356              | -0.0036                | 0.0020                   | 0.0229                | 0.0611                     | 0.0577                       |
| Condition C    | Histogram Normalized         | 12                 | 12                 | 0.3936               | 0.3777                 | 0.5616              | 0.6018              | -0.0085                | -0.0307                  | 0.0637                | 0.1071                     | 0.0879                       |
| Condition D    | Gradient Magnitude           | 12                 | 12                 | 0.3836               | 0.3837                 | 0.5626              | 0.6007              | -0.0185                | -0.0278                  | 0.0775                | 0.3201                     | 0.3401                       |
| Condition E    | Local Gradient Normalized    | 12                 | 12                 | 0.3925               | 0.3866                 | 0.5101              | 0.6204              | -0.0095                | 0.0145                   | 0.0510                | 0.3247                     | 0.3229                       |

## Per-Anchor Results Summary
Per-anchor results saved to [`phase16_per_anchor_results.csv`](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase16_results/phase16_per_anchor_results.csv) (60 rows).

## Production Boundary
- Zero production code, routing, quality gates, Locked LoFTR, RANSAC, or downstream registration modified.
- No automatic winner or production decision applied.