# LunarReg Phase 12 — Integration Guide

## Copy

Place these files in the canonical project:

```text
research/
  multimodal/
    phase12_local_footprint_diagnostic.py
    phase12_diagnostic_benchmark.py
```

## Prerequisite

Phase 11 must already be complete and these files must exist:

```text
research/multimodal/phase11_results/phase11_loftr_anchor_pairs.json
```

Phase 12 intentionally reuses the exact Phase 11 anchors and does not regenerate them.

## Compile

```powershell
cd "C:\Users\Dell\Videos\SIH26_Lunar_Registration"

py -3.13 -m py_compile `
research\multimodal\phase12_local_footprint_diagnostic.py `
research\multimodal\phase12_diagnostic_benchmark.py
```

## Run

```powershell
py -3.13 -m research.multimodal.phase12_diagnostic_benchmark `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg"
```

The benchmark uses the locked four-condition matrix:

```text
compact  5×5 / radius 3
baseline 7×7 / radius 4
medium   9×9 / radius 5
broad   11×11 / radius 7
```

## Outputs

```text
research\multimodal\phase12_results\
  phase12_design.json
  phase12_anchor_reuse.json
  phase12_fixed_anchor_footprint_results.csv
  phase12_anchor_pair_distances.csv
  phase12_end_to_end_results.csv
  phase12_diagnostic_report.md
```

For a descriptor-only run without the secondary end-to-end confirmation:

```powershell
py -3.13 -m research.multimodal.phase12_diagnostic_benchmark `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg" `
  --skip-end-to-end
```

## Safety boundary

Do not modify `adaptive_engine.py`.

Do not change routing, quality gates, Locked LoFTR, RANSAC thresholds, or common downstream mathematics.

No automatic winner or production decision is applied.
