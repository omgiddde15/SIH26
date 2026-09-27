
# Phase 14 v3 run instructions

The previous traceback proves the machine was still executing the OLD Phase 14 file:
its exception text was the old `"expected the completed Phase 11 artifact"` message.

This v3 package uses a UNIQUE module filename, so there is no overwrite ambiguity.

## 1. Extract

```powershell
cd "C:\Users\Dell\Videos\SIH26_Lunar_Registration"

$zip = Get-ChildItem "$env:USERPROFILE\Downloads" `
  -Filter "phase14_crosssensor_rotation_transfer_v3*.zip" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

Expand-Archive $zip.FullName -DestinationPath . -Force
```

## 2. Verify the unique module exists

```powershell
Get-Item `
"research\multimodal\phase14_crosssensor_rotation_transfer_diagnostic_v3.py" |
Select-Object FullName, Length, LastWriteTime
```

## 3. Inspect the actual Phase 11 artifact structure first

```powershell
py -3.13 -m research.multimodal.phase14_crosssensor_rotation_transfer_diagnostic_v3 `
  --inspect-anchor
```

This does NOT modify the artifact and does NOT generate anchors.

## 4. Run Phase 14

```powershell
py -3.13 -m research.multimodal.phase14_crosssensor_rotation_transfer_diagnostic_v3 `
  --iirs-source "C:\Users\Dell\Downloads\souse.jpeg" `
  --ohrc-reference "C:\Users\Dell\Downloads\ref.jpeg"
```

The scientific experiment remains unchanged:
- Phase 11 anchors are reused.
- No anchor regeneration.
- 7x7 / R4.
- Phase 7 SSC vs Phase-9-derived Rot-Norm SSC.
- Known rotations +10, +20, +30, -20 plus native.
- No production modifications.
