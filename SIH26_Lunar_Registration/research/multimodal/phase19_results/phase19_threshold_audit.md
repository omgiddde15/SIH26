# LunarReg Phase 19 — Production Threshold Consistency Audit

## 1. Executive Summary

This audit establishes the **exact ground-truth runtime thresholds** enforced by the LunarReg production registration engine, resolving the threshold discrepancy between the initial Phase 19 report and previously documented architecture.

**Key Finding**:
The actual current production code defines:
- **`min_candidate_matches` = 10**
- **`min_initial_inliers` = 8**
- **`min_inlier_ratio` = 0.20 (20%)**
- **`min_spatial_occupancy` = 0.33 (33%)**

The initial Phase 19 report contained documentation discrepancies:
1. It cited `minimum inliers = 15` (derived from an exploratory draft audit note in `AUDIT_REPORT_PAIR01_SUPERGLUE.md`), whereas the frozen production code enforces **8**.
2. It cited `minimum spatial occupancy = 30%`, whereas the code enforces **33%** (`0.33`, corresponding to at least 3 of 9 cells).
3. It omitted `minimum candidate matches = 10`.
4. Most crucially: On the cross-sensor benchmark pair (`souse.jpeg` $\leftrightarrow$ `ref.jpeg`), LoFTR produced **12 inliers**, which **passed** the true inlier threshold ($12 \ge 8$). LoFTR was rejected **exclusively** by the inlier ratio threshold ($6.03\% < 20.0\%$), not by inlier count.

**Phase 19 Report Consistency Status**: **`CORRECTED`** (production code remains 100% untouched; documentation updated to reflect ground-truth code).

---

## 2. Exact Runtime Source Code Threshold Definitions

All thresholds are defined as dataclass field defaults in [`research/adaptive_matcher/adaptive_engine.py`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/adaptive_matcher/adaptive_engine.py):

```python
# File: research/adaptive_matcher/adaptive_engine.py (Lines 514-541)
@dataclass
class AdaptiveConfig:
    """Configurable experimental thresholds for the Adaptive Matcher Router."""
    ...
    # Quality gate thresholds
    min_candidate_matches: int = 10     # Line 536
    min_initial_inliers: int = 8        # Line 537
    min_inlier_ratio: float = 0.20      # Line 538
    min_spatial_occupancy: float = 0.33 # Line 539
    ransac_threshold: float = 3.0       # Line 540
```

### Runtime Evaluation Function:
```python
# File: research/adaptive_matcher/adaptive_engine.py (Lines 745-780)
def evaluate_quality_gate(matcher_result: Dict[str, Any], config: Optional[AdaptiveConfig] = None) -> Dict[str, Any]:
    if config is None:
        config = AdaptiveConfig()

    n_cand = matcher_result.get("n_candidates", 0)
    n_inl = matcher_result.get("n_inliers", 0)
    ratio = matcher_result.get("inlier_ratio", 0.0)
    occ = matcher_result.get("spatial_occupancy", 0.0)

    reasons = []
    if n_cand < config.min_candidate_matches:       # 10
        reasons.append(f"Candidate matches below threshold ({n_cand} < {config.min_candidate_matches})")
    if n_inl < config.min_initial_inliers:          # 8
        reasons.append(f"Initial inliers below threshold ({n_inl} < {config.min_initial_inliers})")
    if ratio < config.min_inlier_ratio:             # 0.20
        reasons.append(f"Inlier ratio below threshold ({ratio:.2f} < {config.min_inlier_ratio:.2f})")
    if occ < config.min_spatial_occupancy:          # 0.33
        reasons.append(f"Spatial occupancy below threshold ({occ:.2f} < {config.min_spatial_occupancy:.2f})")
```

### Invocation Pattern:
- In [`run_adaptive_registration`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/adaptive_matcher/adaptive_engine.py#L1400), `config: Optional[AdaptiveConfig] = None`.
- Line 1419: `if config is None: config = AdaptiveConfig()`.
- In production adapter [`app/adaptive_adapter.py`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/app/adaptive_adapter.py#L181), `safe_run_adaptive_registration` calls `run_adaptive_registration` with default `config=None`, using these exact dataclass defaults.
- **Nature of Thresholds**: They are **configurable dataclass defaults** instantiated as configuration objects, with runtime fallbacks to `AdaptiveConfig()`.

### Downstream Layer Thresholds:
In [`execute_common_downstream`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/adaptive_matcher/adaptive_engine.py#L1272):
- Line 1278: `max_per_cell: int = 6`
- Line 1279: `ransac_thresh: float = 3.0`
- Line 1280: `seeds: Tuple[int, ...] = (1, 2, 3, 4, 5)`
- Line 1291: `confidence = 0.995, maxIters = 10000`
- Line 1297: `len(inlier_ids) < 4` (RANSAC geometric feasibility check)
- Line 1321: `len(selected_ids) < 4` (Spatial selection feasibility check)
- Line 1330: `len(final_inlier_ids) < 4` (Final fit feasibility check)

---

## 3. Threshold Cross-Check Comparison

| Parameter | Actual Current Code | Phase 19 Report (Initial) | Previously Validated Architecture | Consistency Status | Explanation / Resolution |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Minimum Candidates** | **10** | *(omitted)* | 10 | **CORRECTED** | Omitted from prose summary; restored to reflect actual code. |
| **Minimum Initial Inliers** | **8** | 15 | 8 | **CORRECTED** | Initial report cited `15` from an exploratory draft note in `AUDIT_REPORT_PAIR01_SUPERGLUE.md`. Actual production code enforces `8`. |
| **Minimum Inlier Ratio** | **0.20 (20%)** | 0.20 (20%) | 0.20 (20%) | **VERIFIED** | Exact match across all references. |
| **Minimum Spatial Occupancy** | **0.33 (33%)** | 0.30 (30%) | 0.33 (33%) | **CORRECTED** | Initial report approximated `0.33` as `30%`. Actual code enforces `0.33` ($\ge 3/9$ cells). |
| **RANSAC Threshold** | **3.0 px** | 3.0 px | 3.0 px | **VERIFIED** | Exact match across all references. |

---

## 4. Cross-Sensor Benchmark Rejection Audit (`souse.jpeg` ↔ `ref.jpeg`)

The exact diagnostic output on the uncalibrated benchmark pair reveals the ground-truth behavior:

```text
Pair: C:\Users\Dell\Downloads\souse.jpeg <-> C:\Users\Dell\Downloads\ref.jpeg

1. Primary Matcher: LoFTR
   - Candidates: 199       [Threshold: >= 10] -> PASSED
   - Initial Inliers: 12   [Threshold: >= 8]  -> PASSED (12 >= 8)
   - Spatial Occupancy: 0.5556 [Threshold: >= 0.33] -> PASSED (5 / 9 cells)
   - Inlier Ratio: 0.0603  [Threshold: >= 0.20] -> FAILED (6.03% < 20.0%)
   -> Quality Gate Failure Reason: ['Inlier ratio below threshold (0.06 < 0.20)']

2. Fallback Matcher 1: SIFT
   - Candidates: 9         [Threshold: >= 10] -> FAILED (9 < 10)
   - Initial Inliers: 4    [Threshold: >= 8]  -> FAILED (4 < 8)
   - Spatial Occupancy: 0.3333 [Threshold: >= 0.33] -> PASSED
   - Inlier Ratio: 0.4444  [Threshold: >= 0.20] -> PASSED
   -> Quality Gate Failure Reasons:
      - 'Candidate matches below threshold (9 < 10)'
      - 'Initial inliers below threshold (4 < 8)'

3. Fallback Matcher 2: SuperGlue
   - Candidates: 18        [Threshold: >= 10] -> PASSED (18 >= 10)
   - Initial Inliers: 6    [Threshold: >= 8]  -> FAILED (6 < 8)
   - Spatial Occupancy: 0.3333 [Threshold: >= 0.33] -> PASSED
   - Inlier Ratio: 0.3333  [Threshold: >= 0.20] -> PASSED
   -> Quality Gate Failure Reason: ['Initial inliers below threshold (6 < 8)']

Final Outcome: All available matchers failed the quality gate.
```

### Critical Insight:
LoFTR achieved **12 inliers**, which was **well above the code threshold of 8**. 
The statement in the initial Phase 19 report claiming that LoFTR failed because *"12 inliers < 15 threshold"* was **factually inaccurate**.
LoFTR failed for exactly one reason: its **inlier ratio was 6.03%**, falling far short of the mandatory **20.0%** threshold (`0.0603 < 0.20`). The quality gate correctly caught that 94% of the candidate matches were spurious outliers, halting registration before an unphysical homography could be fitted.

---

## 5. Origin of the Discrepancy

In `research/adaptive_matcher/AUDIT_REPORT_PAIR01_SUPERGLUE.md` (lines 116–120), a post-hoc analysis of an invalid SuperGlue run had noted:
```markdown
The Adaptive Matcher Quality Gate (`evaluate_quality_gate` in `adaptive_engine.py`) defines strict geometric thresholds:
- `min_candidate_matches` = 30 -> SuperGlue had 16 (FAIL)
- `min_initial_inliers` = 15 -> SuperGlue had 6 (FAIL)
- `min_inlier_ratio` = 0.25 -> SuperGlue had 0.375 (PASS)
- `min_spatial_occupancy` = 0.40 -> SuperGlue had 0.2222 (FAIL)
```
That document recorded an exploratory test of stricter hypothetical thresholds. However, **the actual codebase was never modified to those numbers**. The production dataclass `AdaptiveConfig` in `adaptive_engine.py` has continuously maintained:
`min_candidate_matches = 10`, `min_initial_inliers = 8`, `min_inlier_ratio = 0.20`, and `min_spatial_occupancy = 0.33`.

The initial Phase 19 text conflated the draft numbers (`15 inliers`, `30%`) with the true codebase values.

---

## 6. Regenerated Phase 19 Documentation Inventory

To align documentation with the untouched production code without changing any experimental results:
1. **[`research/multimodal/phase19_results/phase19_threshold_audit.json`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase19_results/phase19_threshold_audit.json)**: Created with complete schema and exact values.
2. **[`research/multimodal/phase19_results/phase19_threshold_audit.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase19_results/phase19_threshold_audit.md)**: Created with complete analysis and cross-check.
3. **[`research/multimodal/phase19_final_integration_audit.py`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase19_final_integration_audit.py)**: Updated to output the exact code thresholds ($10 / 8 / 20\% / 33\%$) and accurate rejection rationale.
4. **[`research/multimodal/phase19_results/phase19_ps_compliance_matrix.csv`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase19_results/phase19_ps_compliance_matrix.csv)**: Updated Requirement A limitation text.
5. **[`research/multimodal/phase19_results/phase19_final_integration_report.md`](file:///c:/Users/Dell/Videos/SIH26_Lunar_Registration/research/multimodal/phase19_results/phase19_final_integration_report.md)**: Updated Stage 5 description, Stage 6 description, Requirement A limitation, and IIRS-OHRC analysis.

---

## 7. Final Statement

- **Current production thresholds are**:
  - Minimum Candidate Matches: **`10`**
  - Minimum Initial Inliers: **`8`**
  - Minimum Initial Inlier Ratio: **`0.20 (20%)`**
  - Minimum Spatial Occupancy: **`0.33 (33%)`**
  - RANSAC Inlier Reprojection Threshold: **`3.0 px`**
  - RANSAC Geometric Minimums: **`4 inliers`** (initial, spatial, and final)

- **Phase 19 report consistency status**: **`CORRECTED`**
