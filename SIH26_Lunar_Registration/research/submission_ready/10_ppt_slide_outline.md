# 10 — PPT Slide Outline (17 Slides + Appendix)

**Target audience mix:** SIH judges (non-technical / semi-technical; possible medical, engineering, industry, student composition).
**Guideline per slide:** ≤ 6 lines of bullet text. Use diagrams and tables. Keep jargon out of bullets; use speaker notes for jargon.

---

## Slide 1 — Title Slide

- **Title:** Adaptive Lunar Image Registration with Evidence-Based Matching and Safe Rejection
- **Subtitle:** SIH Problem Code: SIH26166 — LunarReg
- **Team line, Institute line, Date line.**
- **Background:** Moon south-polar Mosaic thumbnail (no overclaiming; credit NASA/ISRO if used).

**Speaker notes (30 s):** *"Hello. We present LunarReg: a lunar image-registration system designed around one principle that we think matters more than accuracy — reliability. Today we show you where it works, where it safely refuses, and where it needs to go next."*

---

## Slide 2 — The Problem (§02)

- **3 Chandrayaan-2 sensors** (OHRC ~0.25 m, TMC2 ~5 m, IIRS ~85 m) → reference maps
- **Extreme illumination** near south pole (sun elev −0.3° to +5° → shadows dominate)
- **Uncertain reference provenance:** we don't know exactly what upstream map product generated the reference GeoTIFFs
- **Pressure:** 6000×6000 px GeoTIFFs break naive memory plans

**Speaker notes (45 s):** *"Why is this hard? Three reasons. Different sensors see the same terrain differently. Near the lunar south pole the sun is so low that one orbit's 'shadows' are another orbit's 'illumination'. And critically, we don't even have a pinned upstream provenance for the reference product. So a matcher failure might be the matcher — or it might be the reference frame. A production system must survive all three."*

---

## Slide 3 — Why Existing Single-Matcher Pipelines Struggle (§02)

- One matcher assumption → fails on some modality / texture combinations
- No memory policy → OOM crash on 6k × 6k reference
- Threshold relaxation **after failure** → false, degenerate homographies
- No spatial check → 5 inliers in one corner "passes" a count gate
- No independent validation → "looks good" slideware

**Speaker notes (30 s):** *"The classic approach is: pick a matcher, run it, relax thresholds until it passes. That works on clean datasets. On planetary data, every bullet on this slide has caused a published false alignment. We built the opposite architecture."*

---

## Slide 4 — Our Solution: Reliability > Forced Alignment (§02)

- Either register with independently verifiable evidence
- **OR** explicitly refuse (SAFE REJECTION) — no homography, no warp
- Three defensive layers: adaptive routing → 5-stage evidence gate → physical audit

**Speaker notes (20 s):** *"The motto is: Reliability > Forced Alignment. We will not produce a registration unless five independent checks agree. If they don't, we proudly say SAFE REJECTION and hand back full telemetry."*

---

## Slide 5 — Production Architecture (§03)

Show the 11-box pipeline diagram from §3.1. Text bullets summarizing:

- Input → Validate → Characterize → Adaptive Router → Resource Guard
- Primary matcher (SIFT/LoFTR/SuperGlue) → Initial RANSAC →
- **Quality Gate (G1–G5)** → 3×3 Spatial Selection → Final H →
- Independent 5-seed Hold-Out Validation →
- ✅ Registered + Evidence  OR  ❌ Safe Rejection (no H, no warp)

**Speaker notes (60 s):** *"This is the architecture. Input images come in, we validate headers, characterize content, route to appropriate matcher, respect memory limits, run matcher, run initial RANSAC, hit a **five-stage frozen quality gate**, do 3×3 spatial selection, compute final H, then do independent 5-seed hold-out. At any point if thresholds fail, we classify SAFE REJECTION and produce geometric output. This is deliberate. Full telemetry is always logged."*

---

## Slide 6 — The Frozen Quality Gate (§3.2)

Show the threshold table from §3.2 as 6 big green tiles:

- **G1 ≥ 10 candidates**
- **G2 ≥ 8 initial inliers**
- **G3 ≥ 20 % inlier ratio**
- **G4 ≥ 33 % spatial occupancy (3/9 cells)**
- **G5 ≥ 4 final inliers + 5-seed 75/25 hold-out**
- **RANSAC = 3.0 px; max 6 pts / cell; seeds 1-5**

Call out: THRESHOLDS NEVER LOWERED.

**Speaker notes (30 s):** *"These are the gates. Every number here was fixed BEFORE the benchmark. We never lowered them for any mentor case. This discipline is why we can honestly show you 6/6 safe rejections later — because the gate is a fair, fixed, independently reproducible measurement."*

---

## Slide 7 — Why One Matcher Is Not Enough (§04 Finding 1)

- Multiple research representations explored: RIFT2, FAST+ZMUV, rotation-SSC, Sobel-gradient NCC, phase correlation, structural ablations…
- Each method improved a subset — none closed the gap universally
- → Motivated the **adaptive router** (not one matcher)

**Speaker notes (30 s):** *"We tested many research representations. Every single one helped on a subset and hurt somewhere else. This is exactly why the architecture picks matchers adaptively rather than defaulting to the deepest network."*

---

## Slide 8 — Initial Matches ≠ Validated (§04 Finding 2)

- High initial inlier ratio can still worsen **independent** hold-out RMSE
- → 5-stage gate (§3.2) holds final registration hostage until G5 passes
- → This is why 3×3 spatial occupancy + 5-seed hold-out exist

**Speaker notes (20 s):** *"Key finding: a good initial match count is necessary, but not sufficient. We must independently validate with held-out data. Otherwise we fool ourselves."*

---

## Slide 9 — Sub-Pixel on Controlled Data Only (§04 Finding 3)

- Controlled pair: synthetic rotation 2°, tx=10, ty=10 px (§08 / CONTROL_2)
- Result: **1867 inliers, hold-out RMSE < 1 px across all 5 seeds**
- Sub-pixel correspondence localization **on controlled data only**
- (Disclaimer box: NOT claimed for real lunar imagery — need real ground truth)

**Speaker notes (20 s):** *"Sub-pixel localization works beautifully when we pin the ground truth. On real Chandrayaan data we will not make that claim until we have independent control points — which we don't. Honest."*

---

## Slide 10 — Why Physical Geometry Matters (§05)

Projection chain diagram from §5.2:

- Pixel → Detector vector → Camera ray → Spacecraft ephemeris/attitude → DEM intersection → Polar Stereographic → Nominal reference-footprint center

**2 bullets:**
- Polar Stereographic South (λ₀=0°, k₀=1, R=1,737,400 m)
- **But:** Reference product provenance unresolved → absolute body-fixed frame unknown (§5.3 block)

**Speaker notes (30 s):** *"A pixel isn't just bits. We audited the full projection chain. The CRS semantics are standard Polar Stereographic. But the specific upstream product that generated the references is unidentified, so we honestly record REFERENCE_PRODUCT_UNRESOLVED. This is why Phase 24A matters: we test image-space hypotheses numerically rather than claiming a geodetic offset."*

---

## Slide 11 — Mentor Production Benchmark (§06)

The 6-row telemetry table from §6.2.

Color code:
- **Green column = Result** → all 6 rows: `SAFE REJECTION`
- **Red columns = gates that failed** (initial inliers, ratio, occupancy)

Quote banner at bottom:
> *"All six mentor cases were safely rejected under frozen criteria; successful mentor registration has not yet been demonstrated."*

**Speaker notes (45 s):** *"Here are all 6 mentor datasets. Zero tuning, zero threshold relaxation. All six were safely rejected. This is not failure — this is a production system correctly saying 'I don't know' instead of guessing. Zero false registrations. Zero crashes."*

---

## Slide 12 — Phase 24A: 196 Coarse Hypotheses (§07)

Show a funnel:
- 196 coarse image-space hypotheses (49 × 4 pairs, ±3 km lattice)
    → 16 SCREEN_PASS (cheap structure)
    → 16 LoFTR runs
    → 0 Initial QG passes
    → 0 full QG / hold-out

**Bottom line quote:**
> *"Coarse image-space placement uncertainty alone did not yield validated registration under the tested hypotheses."*

**Speaker notes (30 s):** *"So you might ask: maybe the projection is off by a kilometer or two, and that's the real problem? We tested exactly that. 196 predeclared lattice hypotheses covering ±3 km, 49 per pair. 16 showed cheap structural evidence. None survived the frozen LoFTR quality gate. So simple translational error alone is not the full explanation."*

---

## Slide 13 — Technical Novelty (§01)

7 bullets (icon + one-liner):
1. Adaptive matcher selection by image characterization
2. 5-stage frozen geometric quality gate
3. 3×3 spatially distributed correspondence selection
4. Independent 5-seed 75/25 hold-out validation (first-class)
5. Resource-aware matcher + tiled-LoFTR memory guard
6. Evidence-based safe rejection (H completely withheld)
7. Physical / geodetic audit layer for lunar imagery

**Speaker notes (20 s):** *"These are the seven technical novelties. The first six are architectural. The seventh is the geodetic layer that keeps image registration honest about what it does and doesn't know about the body-fixed frame."*

---

## Slide 14 — Current Limitations (§9.1)

Top 4 only (keep slide uncluttered):
1. ❌ No validated mentor registration demonstrated yet (6/6 safe rejection)
2. ❌ Delivered reference product provenance unresolved
3. ❌ Absolute geodetic realization unknown
4. ❌ Phase 24 exhaustive search deferred (computational cost)

**Speaker notes (20 s):** *"Limitations. We list them clearly. Honesty is a strength."*

---

## Slide 15 — Future Work (§9.2)

Top 4 only:
1. GPU-accelerated exhaustive ±3 km search (Phase 24)
2. Authoritative reference-product linkage (upstream)
3. Stronger camera/geodetic calibration (SPICE)
4. Cross-sensor representation learning (fine-tune / multimodal)

**Speaker notes (20 s):** *"Next steps. Clear, bounded, well-defined investments."*

---

## Slide 16 — Demo Preview / Plan (§08)

2-column layout:
- **LEFT: Where it works reliably (CONTROL_2 synthetic):** 1867 inliers, full pass, overlay ✓
- **RIGHT: How it safely refuses (OHRC mentor):** 6 inliers, 1.72% ratio → gate fails → H withheld ✓

Quote banner: *"Reliability > Forced Alignment"*

**Speaker notes (20 s):** *"The demo you'll see in our next slot: two systems. One where we register with strong evidence — and one where the system proudly refuses because the evidence isn't there."*

---

## Slide 17 — Impact + Close / Thank You

- **ISRO users:** Safety-critical first stage for planetary mapping
- **Community:** Reproducible frozen benchmark with telemetry at every stage
- **Safety pattern generalizes** to any vision/navigation where miss < wrong-alignment
- Thank you + Questions?

**Speaker notes (20 s):** *"In closing. Reliability > Forced Alignment. Thank you for your time. Questions?"*

---

## APPENDIX Slides (Optional, after Slide 17)

- **App-A:** Full mentor benchmark table (all 6 rows, §6.2) + runtime
- **App-B:** Phase 24A per-pair failure classes table (§7.5)
- **App-C:** Claim audit table summary from `final_evidence_registry.csv` — 5 or 6 key rows (Claim, Evidence File, Allowed wording)
- **App-D:** System screenshot — app/assets/production_architecture_fig1.png or the Flask UI
