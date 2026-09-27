# Phase 13 Integration

Place the files under:

`research/multimodal/`

Compile:

```powershell
py -3.13 -m py_compile `
research\multimodal\phase13_angle_footprint_diagnostic.py `
research\multimodal\phase13_diagnostic_benchmark.py
```

Run:

```powershell
py -3.13 -m research.multimodal.phase13_diagnostic_benchmark `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg"
```

Outputs:

`research\multimodal\phase13_results\`
- phase13_angle_footprint_results.csv
- phase13_angle_footprint_report.md
- phase13_design.json

The benchmark is intentionally conservative: it imports the existing Phase 7 / Phase 9 research implementations and inspects their callable/configuration signatures at runtime. If the installed Phase 9 implementation does not expose a controlled footprint parameter, the script stops with an explicit diagnostic instead of silently changing code or pretending the compact Phase 9 condition was evaluated.
