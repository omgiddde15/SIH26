# 08 — Demo Plan for SIH Judges

## 8.1 Golden Rule for the Demo

> **Do NOT depend on a successful mentor registration.**
> We don't have one, and faking it undermines the scientific honesty that is this project's strongest suit.

The demo has **two stories**, and both are run live (or from pre-recorded screen captures if the live environment is unstable):
1. **Where the system registers reliably** (CONTROL_2 synthetic case — positive demo).
2. **How the system proves it** (evidence panel + hold-out validation for the positive case).
3. **How it refuses unreliable data** (OHRC_PAIR_01 mentor case — safe-rejection demo).

## 8.2 Recommended Demo Flow (8–10 Min, Judge-Friendly)

| Time | Step | What the Presenter Says | What the Screen Shows |
|:---|:---|:---|:---|
| 0:00 | (A) Intro hook | *"We built a lunar image-registration system that knows when it doesn't know. Today we show you two things: (1) where it works reliably, and (2) how it safely refuses unreliable data instead of guessing."* | Title slide + LunarReg architecture overview (§3 diagram) |
| 0:45 | (B) Successful controlled registration | *"First, a scene where we control the exact ground truth: a 2-degree rotation plus a 10/10 pixel translation. Let's press RUN."* | Drop two panels side-by-side — source (tilted) and reference. Click `Run Registration`. |
| 1:15 | (C) Wait for LoFTR + pipeline | *"Behind the scenes: the router selected LoFTR; it's doing spatial selection → final H → hold-out validation across 5 seeds."* | Progress screen / log. Wait for completion (should be fast for the small 400×400 scene). |
| 1:45 | (D) Evidence panel for positive case | *"Here's the evidence packet. 1867 inliers, inlier ratio comfortably above 20%, 9/9 cells occupied, hold-out RMSE finite and consistent across all 5 seeds."* | Evidence dashboard. Call out: **n_cand, n_inl, ratio, occupancy, hold-out RMSE**. Compare against the 5 frozen thresholds from §3.2. |
| 3:00 | (E) Overlay / registered output | *"And here is the output image — visually confirmed alignment. But notice we only displayed this because all 5 quality gates passed."* | Warp overlay. Optional: animated blink between reference and warped source. |
| 3:45 | (F) Switch to hard mentor case | *"Now, a real Chandrayaan-2 OHRC mentor pair. This is OHRC_PAIR_01: south-polar scene, 624×4872 source, 5916×4232 reference."* | Two panels (mentor source + reference). Zoom to highlight the long shadow bands; point out sun elevation 2.11°. |
| 4:30 | (G) Run on mentor (safe rejection) | *"Let's run the EXACT same frozen pipeline, same thresholds, same router. No tuning allowed."* | Click `Run Registration`. Wait for completion (~1 min; pre-record if short on time). |
| 5:30 | (H) Rejection evidence panel | *"The system returned SAFE REJECTION. Why? 348 candidates, but only 6 initial inliers (threshold is 8), ratio 1.72% (threshold is 20%). Occupancy was never evaluated because the gate failed earlier."* | Evidence panel for the mentor case. Highlight in RED: 6 < 8 and 1.72% < 20%. |
| 6:15 | (I) What safe rejection DOESN'T output | *"Crucially: no homography was produced, no warp, no registered image. The system withholds these entirely when quality is below gate."* | Empty or grayed-out registered-image panel. Display "Homography WITHHELD" banner. |
| 6:45 | (J) Wrap up + link back to architecture | *"So what did we see? One scene with enough structure: pass, evidence, validated output. One difficult real scene with illumination mismatch: safe rejection, no false output. This is the right behavior for a safety-critical planetary pipeline."* | Return to architecture slide §3, highlight "SAFE REJECTION OR REGISTERED + VALIDATED" output box. |
| 7:15 | (K) Phase 24A 1-slide teaser (if time) | *"We also ran 196 coarse image-space hypotheses to test if a simple translational search would have recovered these pairs. 16 showed structure, 0 passed the frozen gate. Simple translations are not the full answer."* | Quick bar chart: 196 → 16 → 0. |
| 7:45 | (L) Limitations + future work | *"This is research. Mentor cross-sensor registration is not yet solved; reference provenance is unresolved. We now describe the GPU search and authoritative reference linkage we want to do next."* | Limitations / Future slides §9. |
| 8:30 | (M) Questions | *"Thank you. Questions?"* | |

## 8.3 Demo Assets Required

1. **Positive demo scene:** CONTROL_2 synthetic pair (400×400, rotation 2°, translation tx=10, ty=10). Keep it small — judges hate waiting.
2. **Mentor demo scene:** OHRC_PAIR_01 (624×4872 src + 5916×4232 ref). Pre-run it and save screenshots if live processing is too slow.
3. **Evidence dashboard:** Two side-by-side tables — one for the positive case (all green), one for OHRC_PAIR_01 (red where threshold failed):

| Metric (frozen threshold) | Positive Case (CONTROL_2) | Mentor OHRC_PAIR_01 | Status O/01 |
|:---|---:|---:|:---|
| G1 Candidates ≥ 10 | ✅ high | 348 ✅ | Pass / Pass |
| G2 Initial inliers ≥ 8 | ✅ 1867 | **6 ❌** | Pass / Fail |
| G3 Inlier ratio ≥ 20 % | ✅ % | **1.72 % ❌** | Pass / Fail |
| G4 Occupancy ≥ 33 % | ✅ % | **NOT EVALUATED (gate failed)** | Pass / N/A |
| G5 Final inliers ≥ 4 | ✅ | N/A | Pass / N/A |
| Hold-out (5 seeds) | ✅ consistent RMSE | N/A | Pass / N/A |
| **CLASSIFICATION** | **REGISTERED + VALIDATED** | **SAFE REJECTION** | — |

4. **Optional backup slide:** Benchmark table for all 6 mentor cases (§6.2). If a judge asks "What about the other 5?", you have 10 seconds to say "All six safely rejected, zero false registrations, here's the table."

## 8.4 Backup Plan If Live Demo Is Unstable

Pre-record:
- **Clip A (1 min):** Positive CONTROL_2 end-to-end, show evidence dashboard + overlay.
- **Clip B (1 min):** OHRC_PAIR_01 end-to-end, show safe-rejection dashboard + NO homography output.

Play the two clips, then talk over the evidence table. The judges care about the **behavior pattern**, not the GUI aesthetics.

## 8.5 What the Demo MUST NOT Do

❌ Do NOT run OHRC_PAIR_02 with lowered thresholds to get a "near-success" case. Threshold freeze is non-negotiable.
❌ Do NOT show manual Photoshop registration as "what we would have gotten". This undermines the scientific honesty narrative.
❌ Do NOT end with "And with more time we would have registered all 6 mentors". Instead end with "This is what the system reliably does today. The future work makes it stronger."
