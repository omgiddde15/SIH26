# LunarReg Phase 11 — Integration Guide

## Copy

Place these files in the canonical project:

```text
research/
  multimodal/
    phase11_crosssensor_transfer_diagnostic.py
    phase11_diagnostic_benchmark.py
```

Phase 11 expects the already-installed Phase 7 and Phase 9 research modules.

## Compile

```powershell
cd "C:\Users\Dell\Videos\SIH26_Lunar_Registration"

py -3.13 -m py_compile `
research\multimodal\phase11_crosssensor_transfer_diagnostic.py `
research\multimodal\phase11_diagnostic_benchmark.py
```

## Run

```powershell
py -3.13 -m research.multimodal.phase11_diagnostic_benchmark `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg"
```

## Expected outputs

```text
research\multimodal\phase11_results\
  phase11_loftr_anchor_pairs.json
  phase11_anchor_feasibility.json
  phase11_crosssensor_descriptor_results.csv
  phase11_scale_sensitivity_results.csv
  phase11_end_to_end_results.csv
  phase11_diagnostic_report.md
```

## Important interpretation boundary

The anchor pairs are produced by the existing LoFTR matcher. They are **not
ground truth**. They are an external matcher-derived diagnostic reference.

Phase 11 does not:
- change adaptive routing;
- change the 20% quality gate;
- change Locked LoFTR;
- change RANSAC or common downstream mathematics;
- tune or automatically promote a preferred scale or descriptor.

Do not modify `adaptive_engine.py` for Phase 11.
