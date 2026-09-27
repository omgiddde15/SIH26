# LunarReg SIH 2026 — Submission Package README

**Project:** LunarReg / SIH26166 — Adaptive Lunar Image Registration with Evidence-Based Matching and Safe Rejection
**Submission Date:** 2026-09-24 (Deadline: 2026-09-30)
**Mode:** RESEARCH FREEZE / SUBMISSION PREPARATION — No further research experiments will be run for this submission cycle.

---

## Contents

| # | File | What it contains |
|:---|:---|:---|
| — | `README.md` | This file. Navigation + governance summary. |
| 01 | `01_executive_summary.md` | 1-page elevator pitch for judges. |
| 02 | `02_problem_and_solution.md` | Problem statement, why existing methods struggle, proposed solution. |
| 03 | `03_architecture.md` | Production pipeline architecture, adaptive router, quality gates. |
| 04 | `04_research_findings.md` | Strongest validated research findings (multimodal, scale, sub-pixel). |
| 05 | `05_geodetic_findings.md` | Physical/geodetic investigation: rays → DEM → Polar Stereographic. |
| 06 | `06_mentor_benchmark.md` | 6 mentor production benchmark results table + safe-rejection analysis. |
| 07 | `07_phase24a_summary.md` | Coarse prefilter (196 hypotheses) methodology + outcome. |
| 08 | `08_demo_plan.md` | Step-by-step demo flow for judges — no fake mentor success. |
| 09 | `09_limitations_and_future_work.md` | Clear limitations + 6 future-work areas. |
| 10 | `10_ppt_slide_outline.md` | 17-slide PPT outline with speaker notes. |
| — | `final_evidence_registry.csv` | Machine-readable claim audit (claim → evidence file → allowed/forbidden wording). |

---

## Governing Status Block (PRESERVED UNCHANGED)

```
PRODUCTION CODE ................ FROZEN (4-core set git-clean)
MENTOR BENCHMARK ............... 6/6 SAFE REJECTION (0 validated mentor registrations)
Phase 23B ...................... BLOCKED_PENDING_GEODETIC_REVIEW
  REFERENCE_PRODUCT_UNRESOLVED
  REFERENCE_GEODETIC_REALIZATION = UNKNOWN
  REFERENCE_TO_MOON_ME_DE421      = NOT_VERIFIED
Phase 24 (original) ............ DEFERRED_COMPUTATIONAL_COST / INCONCLUSIVE
Phase 24A (coarse prefilter) ... VERIFICATION_FAILED (196 hypotheses, 16 SCREEN_PASS, 0 QG)
Submission mode ................ RESEARCH FREEZE — no new experiments
```

---

## Production Code Freeze Set (DO NOT MODIFY)

```
app/app.py
app/adaptive_adapter.py
app/registration_core.py
research/adaptive_matcher/adaptive_engine.py
```

Verified with:

```
git diff --exit-code -- \
  app/app.py \
  app/adaptive_adapter.py \
  app/registration_core.py \
  research/adaptive_matcher/adaptive_engine.py
echo $?  # expected 0
```

---

## PPT Assembly Instructions

1. Start with `10_ppt_slide_outline.md` — 17 slide structure.
2. Pull exact verbatim text blocks from the matching numbered file:
   - Slides 1–3 → `01_executive_summary.md`, `02_problem_and_solution.md`
   - Slide 4–6 → `03_architecture.md`
   - Slides 7–9 → `04_research_findings.md`
   - Slide 10 → `05_geodetic_findings.md`
   - Slide 11 → `06_mentor_benchmark.md`
   - Slide 12 → `07_phase24a_summary.md`
   - Slide 13 → `09_limitations_and_future_work.md` (Limitations)
   - Slide 14 → `09_limitations_and_future_work.md` (Future Work)
   - Slide 15 → `08_demo_plan.md`
   - Slides 16–17 → Novelty / Impact sections from `01_executive_summary.md`
3. **Audit every claim** against `final_evidence_registry.csv` before PPT export.
4. For images: reuse `app/assets/production_architecture_fig1.png` for architecture slide.
5. Keep total deck ≤ 20 slides. Appendix slides (claim audit table, raw mentor telemetry) allowed after.

---

## Claim Audit Cheat-Sheet (Before PPT Export)

If the PPT says any of these, **DELETE IT** unless a specific row in `final_evidence_registry.csv` supports it:

❌ "fully solved" / "complete solution"
❌ "guaranteed" / "100% accurate"
❌ "sub-pixel lunar accuracy" (sub-pixel *on controlled data* OK)
❌ "scale invariant" / "sun-angle invariant"
❌ "reference product identified"
❌ "geodetically correct"
❌ "mentor registration successful"
❌ "production validated on all mentor pairs"

---

## Final Verdict (For Presenters)

> **Do not bluff.** The scientifically defensible story is:
> "We built a rigorous, reliable registration system that knows when it doesn't know.
>  On 6 mentor datasets, it correctly and safely refused to produce unreliable registrations.
>  On controlled known-transform data, it registered successfully and validated independently.
>  Future work: GPU-accelerated search, authoritative reference linkage, broader sensor validation."
