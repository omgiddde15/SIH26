# 09 — Limitations & Future Work

> **Presentation rule:** If a limitation is clear, the judges will fill it in themselves and respect your honesty. If you hide it, they will find it and trust nothing else.

## 9.1 Limitations (Clearly Stated)

| # | Limitation | Why It Matters |
|:---|:---|:---|
| L1 | **Successful mentor cross-sensor registration is not yet demonstrated.** 6/6 mentor datasets were safely rejected. | This is the headline limitation. The strongest evidence for "solved" would be a 6/6 or even 1/6 validated mentor registration. We don't have it — honest. |
| L2 | **Delivered reference product provenance remains unresolved.** No TIFF tags, generic PDS4 ReferenceUsed=System, failed local candidate fingerprint match. | Without knowing what upstream map product generated the reference GeoTIFFs, absolute lunar geodetic placement cannot be audited. |
| L3 | **Absolute geodetic realization remains unresolved.** REFERENCE_GEODETIC_REALIZATION=UNKNOWN. REFERENCE_TO_MOON_ME_DE421=NOT_VERIFIED. | Even if we got a perfect image match, we cannot honestly claim a specific body-fixed frame. |
| L4 | **Mentor dataset has limited direct ground truth / control point information.** | Every claim of "true alignment" is weaker than it would be with surveyed lunar control points. |
| L5 | **Phase 24 exhaustive ±3 km LoFTR search was deferred due to computational cost.** Status: DEFERRED_COMPUTATIONAL_COST / INCONCLUSIVE. | The single 676-candidate brute-force experiment that would conclusively rule out translational hypotheses was not run. Phase 24A (196-candidate cheap prefilter) took its place; we know 196 hypotheses didn't work, but not the remaining ~480. |
| L6 | **Sub-pixel only demonstrated on controlled known-transform data.** | Sub-pixel accuracy on real Chandrayaan imagery would require ground truth that we do not have. |
| L7 | **IIRS reference GSD unverified.** Results recorded with an unverified reference scale for the two IIRS mentor cases. | IIRS_A and IIRS_B safe rejections are counted as such; absolute pixel-scale interpretation remains weaker for those two. |
| L8 | **Large-image SIFT / SuperGlue fallbacks were deliberately blocked by resource policy for the benchmark.** | We know LoFTR 6/6 fails under these rules; we don't know what SIFT or SuperGlue would have done on the same 6 mentor images because the resource policy blocked them above 4000 px to keep the comparison deterministic. The architecture supports them for smaller imagery. |
| L9 | **Only 2 secondary IIRS cases in mentor benchmark set.** Sensor distribution is OHRC-heavy. | Fewer data points for cross-modal claims. |
| L10 | **Causality for illumination / modality mismatch not isolated.** We say "consistent with" — never "caused by." | All contributing-factor statements are correlational. Isolating them would require dedicated control ablations beyond the submission scope. |

### This Is A Strength (If Presented Clearly)

Openness about these limitations demonstrates:
1. **Engineering discipline** (we know what we don't know)
2. **Auditability** (every claim has a reference file)
3. **Research integrity** (we didn't tune thresholds to pass the benchmark)

## 9.2 Future Work (Clearly Labelled)

| # | Area | What It Would Deliver | Status Label |
|:---|:---|:---|:---|
| FW1 | **GPU-accelerated exhaustive ±3 km image-space search (Phase 24 proper).** Run the original 676-candidate LoFTR (or prefilter → LoFTR) per pair on a GPU worker. | **FUTURE WORK** (not started; deferred due to computational cost for this submission) |
| FW2 | **Authoritative reference-product linkage.** Engage with upstream ISRO / planetary-map archives to obtain the exact GeoTIFF source product and provenance. | **FUTURE WORK** (Phase 23B.3 8-track audit found no local link; external follow-up required) |
| FW3 | **Stronger physical camera / geodetic calibration.** Incorporate SPICE ephemeris + PDS attitude directly into the registration cost function rather than only at the prefilter stage. | **FUTURE WORK** (Phase 23A projection is currently a first-pass localization; deeper integration unimplemented) |
| FW4 | **Broader OHRC / TMC2 / IIRS validation across more orbits.** Extend the 6-case mentor benchmark to a 20+ case multi-instrument production regression suite. | **FUTURE WORK** (Current production code supports it; need more labeled mentor data / ISRO releases) |
| FW5 | **Independent geolocation ground truth.** Acquire / simulate lunar control points for absolute hold-out. | **FUTURE WORK** (Needed before any sub-pixel claim on real data) |
| FW6 | **Improved cross-sensor representation learning.** Explore modern contrastive-learned descriptors (e.g., LoFTR fine-tune on synthetic lunar multi-sensor domain-transfer pairs, joint optical-IR multimodal embeddings). | **FUTURE WORK** (Current FAST + ZMUV + RIFT2 explorations showed per-subset improvements only; representation learning would be the next step) |

### Presenter Script for §13/14 Slides

> **"The system we built today reliably does two things: it validates strong registrations, and it safely rejects weak ones.
>  The next steps—GPU search, reference linkage, broader sensor validation—are well-defined, and that's a strength, not a weakness:
>  we know exactly where to invest effort."**
