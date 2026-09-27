# LunarReg — Production Architecture & Research Separation (SIH26166)

## 1. Production Pipeline Architecture

The LunarReg production architecture executes an automated, 10-stage deterministic flow without manual intervention:

```
[Raw Source & Reference Images]
               │
               ▼
   [Stage 1: Input Validation Guard]
   • Validates 2D/3D numpy arrays, min dimensions >= 32x32 px
               │
               ▼
   [Stage 2: Image Characterization & Profile Classification]
   • Measurable metrics: contrast std dev, entropy, edge gradient density
   • Classifies difficulty profile: NORMAL, LOW_CONTRAST, HIGH_CONTRAST, HIGH_TEXTURE
               │
               ▼
   [Stage 3: Rule-Based Adaptive Router]
   • Selects primary matcher based on factual image profile
   • Low-contrast / scale-varying -> LoFTR; High-contrast / rich-texture -> SIFT
               │
               ▼
   [Stage 4: Resource Policy & Memory-Safe Tiling Guard]
   • Checks max_dim <= 4000 px and pixel budget <= 1.8M px
   • Prevents OOM crashes; invokes Memory-Safe Tiled LoFTR or blocks heavy fallbacks
               │
               ▼
   [Stage 5: Primary Feature Matching & Quality Gate Evaluation]
   • Executes primary matcher (Locked LoFTR or SIFT)
   • Evaluates Quality Gate against FROZEN production thresholds:
     - min_candidate_matches = 10
     - min_initial_inliers = 8
     - min_inlier_ratio = 0.20 (20%)
     - min_spatial_occupancy = 0.33 (33%)
               │
               ├─────────────────────────────────────────┐
         (Gate PASSED)                             (Gate FAILED)
               │                                         │
               │                                         ▼
               │                    [Stage 6: Multi-Fallback Sequential Router]
               │                    • Sequentially attempts remaining matchers:
               │                      ['LoFTR', 'SIFT', 'SuperGlue']
               │                    • Evaluates each candidate through Quality Gate
               │                    • If all fail -> HALTS SAFELY (no invalid warp)
               │                                         │
               └─────────────────────────────────────────┘
               │
               ▼
   [Stage 7: Common Downstream — 3x3 Spatial Selection]
   • Partitions inliers across 3x3 spatial grid
   • Selects top inliers per cell: max_per_cell = 6 (strict cap at 54 points)
   • Enforces bounded, uniform spatial distribution
               │
               ▼
   [Stage 8: Common Downstream — RANSAC Homography Estimation]
   • Fits 8-DoF Projective Homography (cv2.RANSAC)
   • Reprojection error threshold = 3.0 px, confidence = 0.995
   • Requires at least 4 valid inliers at each geometric stage
               │
               ▼
   [Stage 9: Independent Multi-Seed Held-Out Cross-Validation]
   • Evaluates homography consistency across 5 distinct random seeds (1, 2, 3, 4, 5)
   • 80% train / 20% check split per seed; reports mean held-out RMSE
               │
               ▼
   [Stage 10: Perspective Warping & Aerospace Artifact Export]
   • Warps source image into reference coordinate frame (cv2.warpPerspective)
   • Generates side-by-side match canvas with correspondence vectors
   • Exports floating-point sub-pixel correspondence coordinates (CSV/JSON)
   • Generates 7-page aerospace-grade scientific evidence PDF report (with PDFium check)
```

---

## 2. Research vs. Production Separation Inventory

All exploratory investigations from Phases 1 through 18 are preserved strictly in `research/` as diagnostic evidence. They are **NOT** required or invoked by the production registration flow.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   LUNARREG DEPLOYABLE SYSTEM                           │
├───────────────────────────────────┬────────────────────────────────────┤
│ PRODUCTION (Active, Mission Flow) │ RESEARCH-ONLY (Frozen Diagnostics) │
├───────────────────────────────────┼────────────────────────────────────┤
│ • adaptive_engine.py              │ • RIFT2 Log-Gabor matching (Ph 3-5)│
│ • Locked LoFTR (outdoor weights)  │ • MIND-style self-similarity (Ph 6)│
│ • SIFT baseline matcher           │ • SSC descriptor matching (Ph 7-8) │
│ • SuperGlue fallback matcher      │ • Structure Tensor Rotation (Ph 9) │
│ • Resource / Memory Guard         │ • Phase 16 Representation Ablations│
│ • Frozen Quality Gate (10/8/20/33)│ • Phase 17 Scale Diagnostic Study  │
│ • 3x3 Spatial Selector (cap 54)   │ • Phase 18 Sub-Pixel Study         │
│ • RANSAC Homography (thresh=3.0px)│                                    │
│ • Multi-seed Validation (seeds 1-5│                                    │
│ • Perspective Warping             │                                    │
│ • 7-Page PDF Evidence Generator   │                                    │
│ • Streamlit Mission UI            │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

> [!IMPORTANT]
> No temporary research branch is required to run the production system.
> The production pipeline operates directly from the repository root:
> `c:\Users\Dell\Videos\SIH26_Lunar_Registration`
