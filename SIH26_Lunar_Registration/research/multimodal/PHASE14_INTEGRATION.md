# Phase 14 Integration

Place:

`phase14_crosssensor_rotation_transfer_diagnostic.py`

under:

`research\multimodal\`

Compile:

```powershell
py -3.13 -m py_compile `
research\multimodal\phase14_crosssensor_rotation_transfer_diagnostic.py
```

Run:

```powershell
py -3.13 -m research.multimodal.phase14_crosssensor_rotation_transfer_diagnostic `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg"
```

The script expects the completed Phase 11 anchor artifact:

`research\multimodal\phase11_results\phase11_loftr_anchor_pairs.json`

It intentionally does NOT regenerate anchors.

Outputs:

`research\multimodal\phase14_results\`
- phase14_anchor_transfer_results.csv
- phase14_anchor_transfer_report.md
- phase14_design.json
