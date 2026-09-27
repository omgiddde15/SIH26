# 03 — System Architecture & Quality Gate

## 3.1 End-to-End Production Pipeline

This is the **frozen** production architecture. All modules are implemented in the 4-core production code set (git-clean):

- `app/app.py` — Flask application, validation, routing
- `app/adaptive_adapter.py` — matcher characterization + rule-based router
- `app/registration_core.py` — 5-stage registration engine (quality gate + spatial selection + hold-out)
- `research/adaptive_matcher/adaptive_engine.py` — Frozen LoFTR (including the quality-gate return fields `n_candidates`, `n_inliers`, `inlier_ratio`)

Pipeline diagram (can be rendered directly from this text in PPT):

```
┌────────────────────────────────────────────────────────────────────────────┐
│  INPUT IMAGES (Source + Reference GeoTIFF)                                 │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  1. IMAGE VALIDATION                                                        │
│     • Magic-number / GeoTIFF header check                                   │
│     • dtype, bounds, CRS, dimensions, non-empty                             │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  2. IMAGE CHARACTERIZATION  ───┬─── dtype, histogram, GSD proxy            │
│  (adaptive adapter inputs)     ├── modality (OHRC / TMC / IIRS) tag         │
│                                ├── max_dim → resource envelope              │
│                                └── valid-pixel coverage (shadow proxy)      │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  3. RULE-BASED ADAPTIVE ROUTER                                              │
│     • If  large dims & texture proxy high  →  LoFTR (standard or tiled)    │
│     • If  small dims & multi-modal         →  SuperGlue (resource OK)       │
│     • If  traditional optical (OHRC) & low resource → SIFT fallback         │
│     • Fallback status recorded; NOT used to "try again" below gate          │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  4. RESOURCE / MEMORY GUARD                                                 │
│     • Estimated RAM allocation per matcher                                  │
│     • If ref.dim > 4000 px → SIFT / SuperGlue BLOCKED by policy             │
│     • LoFTR full-image → switched to MEMORY-SAFE TILED LoFTR automatically │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  5. PRIMARY MATCHER EXECUTION                                               │
│     • SIFT / LoFTR / SuperGlue (as routed)                                  │
│     • Returns:  n_candidates  (total raw correspondence pairs)              │
│     • Writes to telemetry regardless of downstream outcome                  │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  6. INITIAL RANSAC  (3.0 px threshold, FROZEN — not tuned)                 │
│     • Returns:  n_inliers  (consensus correspondence count)                │
│     •           inlier_ratio  = n_inliers / n_candidates                   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────────┐
│  7. INITIAL QUALITY GATE   (FROZEN THRESHOLDS — see §3.2)                  │
│     G1  n_candidates ≥ 10                                                   │
│     G2  n_inliers    ≥ 8                                                    │
│     G3  inlier_ratio ≥ 20 %                                                 │
│     FAIL → SAFE REJECTION → skip stages 8–12, write telemetry, return       │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓  PASS
┌────────────────────────────────────────────────────────────────────────────┐
│  8. 3×3 SPATIAL SELECTION                                                   │
│     • Grid: 9 uniform cells over source image                               │
│     • Max 6 correspondences / cell (prevents corner-cluster degeneracy)     │
│     • Returns: spatial_occupancy  (# occupied cells / 9)                    │
│     G4: spatial_occupancy ≥ 0.33                                            │
│     FAIL → SAFE REJECTION                                                   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓  PASS
┌────────────────────────────────────────────────────────────────────────────┐
│  9. FINAL HOMOGRAPHY (RANSAC, 3.0 px)  on spatially-selected inliers        │
│     • Returns: n_final_inliers,  H_3x3,  reprojection RMSE                  │
│     G5: n_final_inliers ≥ 4                                                 │
│     FAIL → SAFE REJECTION                                                   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓  PASS
┌────────────────────────────────────────────────────────────────────────────┐
│ 10. INDEPENDENT HOLD-OUT VALIDATION   (5 seeds, 1…5)                       │
│     • 75 % fit → predict 25 %  (spatially balanced)                        │
│     • Repeat for 5 deterministic seeds                                      │
│     • Returns: mean / median held-out RMSE                                  │
│     All 5 seeds must produce consistent, finite RMSE                        │
│     FAIL → SAFE REJECTION                                                   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ↓  PASS
┌────────────────────────────────────────────────────────────────────────────┐
│ 11. OUTPUT                                                                  │
│     ✅ Registered image (geometric warp)                                    │
│     ✅ H_3x3  homography matrix                                             │
│     ✅ Evidence packet: n_cand, n_inl, ratio, occ, final_inl, hold-out RMSE │
│     OR                                                                      │
│     ❌ SAFE REJECTION  (all above fields written; warp / H withheld)        │
└────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Frozen Quality-Gate Thresholds (DO NOT LOWER)

| Gate | Parameter | Value | Meaning |
|:---|:---|---:|:---|
| G1 | Minimum candidates | **10** | Enough raw pairs to suspect a consensus exists |
| G2 | Minimum initial inliers | **8** | Enough RANSAC consensus to estimate H |
| G3 | Minimum initial inlier ratio | **20%** | Prevents low-precision matchers leaking |
| G4 | Minimum spatial occupancy | **33%** | ≥ 3/9 cells occupied; blocks single-corner fits |
| G5 | Minimum final inliers | **4** | Minimum to pin a 4-corner homography |
| — | RANSAC threshold | **3.0 px** | Projective-model tolerance |
| — | Hold-out validation seeds | **1,2,3,4,5** | 5 independent 75/25 splits |
| — | Grid selection | 3×3, max 6 pts/cell | Spatially balanced |

## 3.3 Why This Architecture Works

1. **No hidden "try harder" loop.** If LoFTR fails, it does **not** automatically retry with SIFT + relaxed thresholds. Relaxed thresholds are the #1 cause of false registrations in published planetary image pipelines.
2. **Spatial selection before final H.** Rejects the "5 inliers all in the top-left" case that passes a simple count gate.
3. **Hold-out as a first-class citizen.** Hold-out RMSE is not an afterthought — it is required.
4. **Safe rejection is a success.** Classification `SAFE REJECTION` is recorded on the same level as `REGISTERED + VALIDATED`. It indicates the system successfully **detected and neutralized** an unreliable alignment.

## 3.4 Operational Profile (from Mentor Benchmark)

- All 6/6 mentor cases selected **LoFTR** by the router.
- `OHRC_PAIR_01` (ref 5916 px wide) was automatically demoted to **Tiled LoFTR** to stay under the 3.15 GB envelope.
- Remaining 5 cases ran under Standard LoFTR with workspace constraints; SIFT / SuperGlue explicitly **BLOCKED** by resource policy (max_dim > 4000 px) to preserve fairness of comparison.
- Runtime range: 7.65 s (IIRS_PAIR_A) → 58.86 s (OHRC_PAIR_01); mean 30.61 s.
- No OOM; no crash; no unhandled exception.
