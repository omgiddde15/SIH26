# Phase 3 RIFT2 Research: Angle & Viewpoint Test Pairs

This directory contains lunar image pairs specifically curated for **research benchmarking** of the RIFT2 multimodal correspondence matcher under geometric and illumination variations.

## IMPORTANT CONSTRAINTS
- **Research Only**: These image pairs are strictly decoupled from production verification.
- **Never placed in `data/validation_pairs/`**: The standard validation pairs belong to the regression test suite and production router evaluation.
- **Scientific Grounding**: No physical Sun angles, sensor viewpoints, or GSD values are fabricated. If values are not verified from telemetry headers, fields are stored as `null`.

## Directory Structure
- `angle_pairs/pair_01/`: Controlled rotation change (`rotation_change`)
- `angle_pairs/pair_02/`: Tycho perspective/viewpoint variation (`viewpoint_change`)
- `angle_pairs/pair_03/`: Multi-pass OHRC solar illumination variation (`sun_angle_change`)
- `angle_pairs/pair_04_incomplete/`: Test directory with missing reference image to verify loader validation
