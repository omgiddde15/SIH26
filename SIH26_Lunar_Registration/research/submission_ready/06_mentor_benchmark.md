# 06 — Mentor Production Benchmark Results

**Benchmark Date:** 2026-09-23
**Pipeline Mode:** Frozen Production Engine (zero tuning, thresholds unchanged)
**Total Mentor Cases Evaluated:** 6 (4 OHRC + 2 IIRS)

## 6.1 Final Classification (Direct Quote for PPT)

> **"All six mentor cases were safely rejected under the frozen production quality criteria; successful mentor registration has not yet been demonstrated."**

| Classification | Count | Datasets |
|:---|---:|:---|
| **REGISTERED + VALIDATED** | **0** | None |
| **REGISTERED + VALIDATION LIMITED** | **0** | None |
| **SAFE REJECTION** | **6** | `OHRC_PAIR_01`, `OHRC_PAIR_02`, `OHRC_PAIR_03`, `OHRC_PAIR_04`, `IIRS_PAIR_A`, `IIRS_PAIR_B` |
| **EXECUTION FAILURE / CRASH** | **0** | None |
| **NOT RUN** | **0** | None |

## 6.2 Benchmark Telemetry Matrix (Slide 11 Table)

| Pair | Instrument | Matcher Path | Candidates | Initial Inliers | Initial Ratio | Spatial Occupancy | Result |
|:---|:---|:---|---:|---:|---:|---:|:---|
| OHRC_PAIR_01 | OHRC (0.26→5 m) | LoFTR, Memory-Safe Tiled | 348 | **6** | 1.72 % | NOT EVALUATED | **SAFE REJECTION** (G2+G3 fail) |
| OHRC_PAIR_02 | OHRC (0.27→5 m) | LoFTR, Standard WS | 221 | **5** | 2.26 % | NOT EVALUATED | **SAFE REJECTION** (G2+G3 fail) |
| OHRC_PAIR_03 | OHRC (0.25→5 m) | LoFTR, Standard WS | 161 | **5** | 3.11 % | NOT EVALUATED | **SAFE REJECTION** (G2+G3 fail) |
| OHRC_PAIR_04 | OHRC (0.23→5 m) | LoFTR, Standard WS | 98 | **5** | 5.10 % | NOT EVALUATED | **SAFE REJECTION** (G2+G3 fail) |
| IIRS_PAIR_A | IIRS (93.74 m) | LoFTR, Standard WS | 45 | **5** | 11.11 % | 22.2 % | **SAFE REJECTION** (G2+G3+G4 fail) |
| IIRS_PAIR_B | IIRS (83.14 m) | LoFTR, Standard WS | 0 | 0 | 0.00 % | NOT EVALUATED | **SAFE REJECTION** (G1+G2 fail) |

**Frozen thresholds used:** G1 ≥ 10 cand, G2 ≥ 8 inl, G3 ≥ 20 %, G4 ≥ 33 % (3/9 cells), G5 ≥ 4 final inl + 5-seed hold-out.

## 6.3 Why Safe Rejection Is A Design Feature (Not A Failure)

On every safety-critical vision pipeline, **the two possible outputs are:**
1. **Validated registration** — with independent evidence.
2. **Safe rejection** — with full telemetry but no geometric output.

A system that only had output (1) and never (2) is a system that silently produces false alignments. LunarReg prioritizes (2) in ambiguous cases.

For the 6 mentor cases this matters because:
- **OHRC 01–04**: all have verified 1:1 effective pixel scale at 5 m/px. But correspondence consensus remains below 20% (ratios 1.72%–5.10%). Producing a registration here would be misleading.
- **IIRS_A**: spatial occupancy only 22.2% (2/9 cells). Even if initial inliers were above threshold, the fit would likely be degenerate.
- **IIRS_B**: matcher returned 0 candidates. Any forced output here would be pure guesswork.

## 6.4 Operational Observations (Resource)

1. **Memory-Safe Tiled LoFTR** kicked in for OHRC_PAIR_01 (ref width 5916 px → 3.15 GB estimated full-image footprint). Completed without OOM in 58.86 s.
2. **SIFT / SuperGlue fallbacks** were BLOCKED by resource policy for all cases with max_dim > 4000 px. This was **intentional** for the benchmark to keep the comparison fair.
3. Runtime range: **7.65 s → 58.86 s** (mean 30.61 s).
4. **Zero** software defects, **zero** unhandled exceptions across all 6 large-format GeoTIFFs.

## 6.5 Contributing Factors (Honest, Non-Causal)

| Instrument | Plausible Contributing Factor | Causality Proven? |
|:---|:---|:---:|
| OHRC (4 pairs) | Substantial illumination / shadow differences across different orbits (sun elevations −0.31° → 5.10°) | ❌ No (benchmark does not isolate) |
| IIRS (2 pairs) | Cross-sensor representation / modality mismatch (IR radiance ↔ pan reference) | ❌ No (benchmark does not isolate) |

## 6.6 Source Evidence Files

| File | Path |
|:---|:---|
| Full benchmark report | [mentor_production_benchmark.md](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/mentor_production_benchmark.md) |
| Benchmark summary | [mentor_benchmark_summary.md](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/mentor_benchmark_summary.md) |
| Raw telemetry CSV | [mentor_production_results.csv](file:///C:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/mentor_benchmark/mentor_production_results.csv) (6 rows) |
