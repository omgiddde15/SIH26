# 🌙 LunarReg — Adaptive Lunar Image Registration System

> **Adaptive, resource-aware and evidence-driven image registration for Chandrayaan-2 lunar imagery.**
>
> **Core principle:** **Reliability > Forced Alignment**

[![Status](https://img.shields.io/badge/status-research%20prototype-blue)](#project-status)
[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch-orange)](https://pytorch.org/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV-green)](https://opencv.org/)

## Project Overview

**LunarReg** is a prototype system for registering lunar images acquired under different imaging conditions, scales, resolutions and illumination states. It treats registration as a **correspondence + geometric verification** problem rather than accepting a visually plausible warp as success.

The system:

1. characterizes the source and reference images,
2. selects an appropriate matching path,
3. checks computational safety before expensive matching,
4. extracts and evaluates correspondences,
5. applies strict geometric quality gates,
6. distributes selected correspondences spatially,
7. estimates a final homography with RANSAC,
8. validates the result on independent hold-out observations, and
9. exports machine-readable and human-readable evidence.

When the evidence is insufficient, LunarReg **withholds the registration product and reports a safe rejection** instead of forcing an alignment.

> **Important:** LunarReg is a research/prototype system. It does **not** claim official SIH ground-truth validation, universal matcher performance, or guaranteed registration for every lunar image pair.

---

## Problem Statement

The SIH 2026 problem addressed by LunarReg concerns **multi-modal, sun-angle and scale-invariant image correspondence using Chandrayaan-2 optical images (OHRC, TMC and IIRS)**.

The practical difficulty is that two images of the same lunar terrain can differ because of:

- sensor modality,
- native image resolution and scale,
- contrast and dynamic range,
- illumination / shadow geometry,
- viewpoint and acquisition conditions,
- terrain texture and overlap,
- image dimensions, and
- available compute resources.

A registration algorithm can therefore produce a geometrically plausible but incorrect warp if correspondence quality is not measured independently.

LunarReg is designed around the opposite rule:

> **Do not register because a transform can be computed. Register only when the evidence passes the frozen production criteria.**

---

## What Makes LunarReg Different

### 1. Resource-Aware Routing

The matcher is selected after image characterization and a resource check. Expensive full-image deep matching is not blindly attempted on arbitrarily large lunar rasters.

### 2. Memory-Safe Processing

A token/resource estimate is used before full-image LoFTR. Large inputs can be redirected to a controlled tiled strategy rather than forcing an unsafe multi-gigabyte allocation.

The demonstrated tiled approach uses overlapping tiles, maps tile-local correspondences back to global coordinates, merges them, and sends the combined evidence through the same downstream verification logic.

### 3. Strict Quality Gates

LunarReg rejects weak or spatially concentrated correspondences before accepting a geometric product.

### 4. Spatially Distributed Correspondences

The selected correspondences are distributed through a **3×3 image grid**, with a maximum of **6 points per cell**, limiting the effect of matches clustered on a single crater rim or local texture structure.

### 5. Independent Hold-Out Validation

The final transform is checked on observations that were not used to fit it. The application reports held-out geometric consistency separately from the fit error.

### 6. Safe Rejection

A difficult pair is allowed to fail. A failed registration does not feed an untrusted warp into the output stage.

### 7. Evidence Export

A successful run can produce the registered image together with correspondence CSV, JSON evidence and a scientific PDF report. The workflow is designed to be auditable rather than a black-box “alignment” button.

---

## Production Architecture

```text
Source Image + Reference Image
            │
            ▼
   Image Characterization
   ├─ resolution / scale
   ├─ contrast / texture
   └─ image-size / resource indicators
            │
            ▼
      Adaptive Router
            │
            ▼
    Resource / Memory Guard
       ┌────┴────┐
       │         │
    Direct   Controlled tiles
       │      (when required)
       └────┬────┘
            ▼
      Feature Matching
   ┌────────┼────────┐
   │        │        │
 LoFTR     SIFT   SuperGlue
 Primary   Fallback  Guarded
   │        │        │
   └────────┴────────┘
            │
            ▼
        Quality Gate
   candidates / inliers /
   ratio / spatial coverage
            │
       ┌────┴────┐
       │         │
      PASS      FAIL
       │         │
       ▼         ▼
  3×3 Spatial   SAFE REJECTION
   Selection
       │
       ▼
 RANSAC Homography
       │
       ▼
  Image Warp
       │
       ▼
 Independent Hold-Out
     Validation
       │
   ┌───┴────┐
   │        │
 VALID    INVALID
   │        │
   ▼        ▼
Registered  Reject
 Product    Product
   │
   ▼
Evidence / Export
```

The **Safe Rejection** branch is terminal: a failed case does not proceed to an accepted registration product.

---

## Frozen Production Configuration

The production geometry and acceptance criteria are intentionally frozen for reproducibility.

| Parameter | Production value |
|---|---:|
| Minimum candidates | **10** |
| Minimum initial inliers | **8** |
| Minimum initial inlier ratio | **20%** |
| Minimum spatial occupancy | **33.3%** |
| RANSAC threshold | **3.0 px** |
| Downstream geometric minimum | **4 final inliers** |
| Spatial partition | **3×3 grid** |
| Maximum selected points per cell | **6** |
| Validation seeds | **1, 2, 3, 4, 5** |
| Resource reference ceiling | **2.60 GB RAM** |

These criteria are not tuned automatically during a normal production run.

---

## Matching and Routing

### Primary / Recovery Paths

- **LoFTR** — primary deep correspondence path for suitable inputs.
- **SIFT** — guarded recovery path for cases where classical local features are more appropriate.
- **SuperGlue** — available as an experimental / guarded recovery path.
- **Locked LoFTR** — fixed research baseline used for comparison and repeatability, not as an adaptive research winner.

### Adaptive Routing

The adaptive engine considers image characteristics and resource constraints before matching. This allows the system to distinguish between:

- normal-sized inputs where direct matching is reasonable,
- large inputs where resource safety becomes dominant,
- cases where fallback matching should be evaluated, and
- cases where the evidence should be rejected.

The adaptive system does **not** silently change the validated downstream registration mathematics.

---

## Large-Image and Heavy-Compute Handling

LunarReg has demonstrated memory-aware and tiled processing on large lunar imagery, but the current online deployment is CPU/compute constrained.

Therefore, the heaviest demonstrations are intentionally separated from the live production path:

| Heavy case | Online behaviour | Demonstration |
|---|---|---|
| **Tycho Research / Stress Test** | **Locked from live online execution** | Recorded Drive result / walkthrough |
| **Large Image LoFTR Stress Test** | **Locked from live online execution** | Recorded Drive result / walkthrough |

The application preserves the documented results and explains why the cases are locked. This prevents a resource-heavy demo from destabilizing the main online application.

> **Tiled LoFTR:** locally demonstrated; online CPU and compute-cost limits currently restrict deployment.

The heavy-case lock is a deployment-safety decision, not a claim that the algorithms are unsupported in research environments.

---

## Quality Gate and Geometry

The production decision is deliberately multi-stage.

### Correspondence Gate

A candidate set must satisfy the minimum candidate count, initial inlier count and initial inlier ratio.

### Spatial Gate

Correspondences must occupy enough of the image domain. Concentrated points are not sufficient even when a local homography can be fitted.

### Spatial Selection

Up to six high-quality points are selected per cell of a 3×3 grid, providing a bounded and spatially distributed fitting set.

### Homography

The final geometric model is a planar homography:

\[
\mathbf{x}' \sim H\mathbf{x}
\]

where \(H\) is a 3×3 projective transformation.

RANSAC is used to estimate a robust consensus model with a **3.0-pixel** threshold.

### Warp Integrity

A valid transform must pass the production checks before a registered image is released.

---

## Independent Hold-Out Validation

LunarReg separates **fit quality** from **independent geometric consistency**.

The validation stage uses held-out observations not used to fit the final transformation and reports metrics including:

- held-out RMSE,
- median error,
- maximum error,
- inlier count,
- inlier ratio,
- spatial occupancy, and
- validation status.

A held-out RMSE value is an **image-space geometric consistency measurement**. It is not automatically a physical ground-truth accuracy measurement on the lunar surface.

### Sub-Pixel Wording Discipline

The project only uses sub-pixel wording for **specific successful validated runs** whose held-out RMSE satisfies the project's stated case-level criterion.

It does **not** claim that every lunar image pair is sub-pixel accurate.

---

## Verified Prototype Evidence

The following results are retained as evidence from controlled and prototype runs. They are deliberately separated from unsupported universal claims.

### Pair 01 — Scale / Resolution Example

A documented production run used a source of approximately **146×513 px** and a reference of **194×528 px**.

Observed telemetry included:

- **166** candidate correspondences,
- **49** initial inliers,
- **29.52%** initial inlier ratio,
- **38** final selected correspondences,
- **8/9** spatial occupancy,
- **1.437 px** final fit reprojection RMSE,
- **1.7188 px** held-out validation RMSE.

This is a successful validated registration example, but it is **not** a sub-pixel case.

### Controlled Positive Validation

A controlled known-transform experiment demonstrated that the pipeline can recover a deliberately imposed geometric transformation and pass the frozen gates. One documented control produced **1,867 inliers** under the synthetic positive condition.

This proves pipeline operation under controlled known-transform conditions; it does not establish universal lunar-scene performance.

### Controlled Negative Validation

A deliberately non-overlapping control was safely rejected. This demonstrates that the pipeline has a meaningful negative outcome rather than forcing a transform when correspondence support is absent.

### Controlled Sub-Pixel Correspondence Localization

Sub-pixel correspondence localization was demonstrated on controlled known-transform data. The evidence should be interpreted as **controlled correspondence localization**, not as independently validated physical sub-pixel accuracy on the lunar surface.

---

## Mentor Benchmark — Safe Rejection Evidence

The mentor benchmark is important because it tests not only whether the system can register, but also whether it can **refuse to register** when the evidence is inadequate.

Across the audited mentor set:

| Metric | Result |
|---|---:|
| Mentor datasets evaluated | **6** |
| Registered + independently validated | **0** |
| Safe rejections | **6 / 6** |
| False registration products released | **0** |
| Runtime crashes | **0** |

The correct interpretation is:

> **All six mentor cases were safely rejected under the frozen production quality criteria; successful mentor registration has not yet been demonstrated.**

This is evidence of **safe-failure behaviour**, not mentor registration accuracy.

---

## Phase 24A — Coarse Placement Verification

Phase 24A investigated whether simple image-space placement offsets could explain the difficult mentor cases before paying the cost of full LoFTR evaluation.

### Search

- **196 deterministic hypotheses**
- 49 hypotheses per pair × 4 OHRC pairs
- 7×7 lattice covering **±3 km** in 1 km steps
- Corresponding image-space offset range of approximately **±600 px** under the tested 5 m/px reference scale

### Screening

- **16** candidates passed the cheap screening stage.
- Only those 16 candidates were sent to LoFTR.
- **0 / 16** passed the frozen initial quality gate.
- **0 / 16** passed the full quality gate.
- **0 / 16** passed the independent hold-out stage.

Classification:

**`VERIFICATION_FAILED`**

Important methodological boundary:

> Phase 24A is a **coarse prefilter characterization**. It does **not** prove that every possible ±3 km continuous transformation has been exhausted. The original exhaustive Phase 24 search remained computationally deferred.

---

## Geodetic / 3D Research Track

LunarReg also contains research-only work on the physical geometry surrounding orbital imagery.

The research track examined aspects such as:

- delivered raster and geospatial metadata,
- pixel → detector geometry,
- camera ray / spacecraft state chains,
- DEM intersection,
- polar stereographic projection,
- reference-product provenance,
- footprint-implied ground resolution,
- coarse spatial-offset hypotheses.

### Current Scientific Boundary

These studies remain **research-only** and do not silently alter production registration.

No unsupported physical GSD, illumination-angle or geodetic normalization claim is promoted into the production pipeline without verified metadata and independent evidence.

### GeoScale Finding

A documented research analysis found a stable footprint-implied ground resolution range of approximately **0.254–0.277 m/px** across the audited OHRC orbital passes. For one analyzed pair, the metadata-declared value and footprint-implied value differed by about **10.4%**.

This is useful as a **scale-characterization diagnostic**, not as a complete physical scale-invariant registration solution.

### 3D Terrain Visualization

An optional Plotly-based 3D terrain visualization can present lunar elevation context using OHRC imagery and a DEM. It is useful for research communication and terrain interpretation, but it is **not part of the production registration algorithm**.

---

## Research Lab

The Research Lab is explicitly separated from production.

Available research areas include:

- Matcher Benchmark
- Ablation Study
- Adaptive Matcher diagnostics
- Locked LoFTR Baseline
- LOPO-style validation
- multimodal / representation experiments
- scale feasibility studies
- sub-pixel controlled experiments
- geodetic / 3D investigations
- historical benchmark traceability

### Research Governance

Research experiments:

- are labeled as research,
- do not silently promote a winner,
- do not lower the production quality gate,
- do not modify the Locked LoFTR baseline,
- do not modify validated downstream mathematics, and
- do not automatically become production routing rules.

This separation is intentional: a promising experimental result is not automatically a production-safe result.

---

## Application Workflow

The Streamlit application is organized as a user-facing sequence:

1. **Authentication**
2. **Overview**
3. **Source + Reference Inputs**
4. **Metadata / Geo Information**
5. **Illumination + Preprocessing**
6. **Feature Correspondence Matching**
7. **Geometric Estimation**
8. **Homography + Registration**
9. **Independent Validation**
10. **Results + Export**
11. **Research Lab**

The interface is designed to show the actual runtime state rather than pretending that later stages have completed before they run.

Mission metadata is never fabricated. If authoritative metadata is unavailable, the application should state that explicitly.

---

## Evidence Export

A successful run can produce an evidence package containing:

- registered PNG/image output,
- correspondence CSV,
- homography JSON,
- machine-readable evidence JSON,
- scientific PDF report,
- ZIP package where enabled.

The exported evidence records the actual run rather than silently substituting a historical canonical result.

---

## Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Language | Python |
| Deep matching | PyTorch / Kornia / LoFTR |
| Classical vision | OpenCV / SIFT |
| Numerical processing | NumPy |
| Visualization | Matplotlib / Plotly for selected research views |
| Reporting | ReportLab |
| Authentication | SQLite-backed application accounts |
| Research / experiments | Python scripts, controlled datasets and notebooks as applicable |
| Development | VS Code / local Windows environment / Google Colab & Drive for selected research work |

Implementation note: the production geometry uses **OpenCV RANSAC + homography estimation**. `pyRANSAC-3D` is not part of the current production implementation.

---

## Repository Structure

A representative top-level structure is:

```text
.
├── app/
│   ├── app.py                       # Streamlit application / UI / runner
│   ├── auth.py                      # Authentication helpers
│   ├── adaptive_adapter.py          # Production routing bridge
│   └── registration_core.py         # Geometry, metrics and validation core
│
├── research/
│   ├── adaptive_matcher/            # Adaptive matcher implementation / research modules
│   ├── multimodal/                  # Benchmark and multimodal experiments
│   └── submission_ready/            # Judge-ready research summaries and evidence index
│
├── tests/
│   ├── ...                          # Automated regression and application tests
│   └── test_locked_heavy_cases.py   # Heavy-case online-lock regression tests
│
├── requirements.txt
├── .gitignore
└── README.md
```

The exact repository may contain additional research scripts and experiment artifacts.

---

## Local Setup

### Requirements

- Python **3.13+** recommended for the current prototype environment.
- CPU execution is supported for the demonstrated workflow, but heavy LoFTR cases can be computationally expensive.
- A working Git installation is recommended.

### Windows — Recommended Setup

From the repository root:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the application without requiring PowerShell activation:

```powershell
.venv\Scripts\python.exe -m streamlit run app\app.py
```

The application is normally available at:

```text
http://localhost:8501
```

### Alternative: activate the environment

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app\app.py
```

If PowerShell blocks script activation, use the first method and run Streamlit through the environment's Python executable.

---

## Authentication and Secrets

The application includes SQLite-backed authentication and a Quick Demo Access path.

For deployment environments that use an initial bootstrap account, configure the required Streamlit secrets rather than committing credentials to Git.

Expected bootstrap secret names:

```toml
LUNARREG_BOOTSTRAP_NAME = "Your Name"
LUNARREG_BOOTSTRAP_EMAIL = "your-email@example.com"
LUNARREG_BOOTSTRAP_PASSWORD = "use-a-strong-password"
```

### Security Rules

- **Never commit `users.db`.**
- Never hard-code real passwords, API keys or private tokens.
- Use Streamlit Secrets or another secure deployment secret store.
- Demo credentials should be separated from real user credentials.

---

## Streamlit Cloud / Online Deployment

Use the Streamlit entry point:

```text
app/app.py
```

Typical deployment steps:

1. Connect the GitHub repository to Streamlit Cloud.
2. Set the main file to `app/app.py`.
3. Configure the required Streamlit secrets.
4. Deploy the application.
5. Verify authentication, Quick Demo Access, a normal lightweight registration case, safe rejection, and evidence export.

### Online Resource Discipline

The online deployment is intentionally conservative:

- large heavy cases are not allowed to destabilize the main application,
- Tycho and the Large Image LoFTR stress test are locked from live online registration,
- their recorded results remain available for demonstration,
- research-only experiments are not part of the online production route.

---

## Testing

Run the test suite from the repository root:

```powershell
py -3.13 -m pytest tests -v
```

The heavy-case lock has a dedicated regression suite covering:

- Tycho remains locked,
- Large Image LoFTR remains locked,
- recorded telemetry is preserved,
- normal production cases are not globally disabled, and
- the lock path does not silently execute the heavy matcher online.

The dedicated heavy-case lock suite was verified with **10/10 tests passing** before the deployment-lock commit was pushed.

---

## Current Demonstration Strategy

For a judge or technical reviewer, the recommended presentation flow is:

### Live / Lightweight

1. Open LunarReg.
2. Show the problem and workflow.
3. Load a standard verified pair such as the documented Pair 01 example.
4. Show image characterization and routing.
5. Run registration.
6. Show candidate count, inliers and inlier ratio.
7. Show 3×3 spatial occupancy.
8. Show homography / registered output.
9. Show independent hold-out RMSE.
10. Export the evidence package.
11. Demonstrate a difficult input that is **safely rejected**.

### Recorded / Research

Use the recorded Drive demonstrations for:

- Tycho heavy stress testing,
- Large Image LoFTR stress testing,
- other CPU-intensive research runs.

This keeps the online demonstration responsive while preserving the actual technical evidence.

---

## What LunarReg Can and Cannot Claim

### Supported Claims

- Adaptive matching and routing are implemented in the prototype.
- Resource-aware matching safeguards are implemented.
- Tiled LoFTR has been demonstrated in local research/stress workflows.
- Strict candidate / inlier / ratio / occupancy gates are used in production.
- 3×3 spatial selection is part of the production geometry path.
- Independent hold-out validation is part of the production workflow.
- Safe rejection is a first-class outcome.
- Six audited mentor datasets were safely rejected with no released false registration product and no runtime crashes.
- Controlled positive and negative cases have been used to validate pipeline behaviour.
- Controlled data demonstrates sub-pixel correspondence localization under known transforms.

### Claims That Are Not Supported

- Universal registration across all Chandrayaan-2 sensor combinations.
- Guaranteed sun-angle invariance.
- Guaranteed physical GSD/scale invariance.
- Guaranteed physical sub-pixel lunar accuracy.
- Official SIH ground-truth accuracy.
- Complete physical geodetic normalization when authoritative metadata is missing.
- Exhaustive elimination of every possible kilometre-scale placement hypothesis.

These boundaries are part of the project's scientific integrity.

---

## Known Limitations

1. **Mentor registration success is not yet demonstrated.** The audited mentor set is currently evidence of safe rejection.
2. **Resource constraints remain important.** Heavy LoFTR workloads are not appropriate for every CPU-only online environment.
3. **Reference-product provenance is not completely resolved for all research inputs.**
4. **Absolute geodetic realization is not claimed where the input metadata chain is incomplete or unresolved.**
5. **The original exhaustive ±3 km LoFTR search remains computationally deferred.**
6. **Matcher-selection evidence is still limited in scope and should not be generalized to all lunar scenes.**
7. **Sub-pixel evidence is case-specific and controlled; it is not a universal performance guarantee.**
8. **Planar homography is an approximation and does not fully model arbitrary 3D lunar terrain relief.**

---

## Future Work

### Near-Term

- Expand the validated benchmark across more real lunar image pairs.
- Strengthen independent geodetic and physical ground-truth validation.
- Improve large-image acceleration on GPU / AI-accelerator infrastructure.
- Expand sensor-specific preprocessing and matcher policies.
- Improve robust terrain-aware geometric models beyond a single planar homography.

### Research Direction

- Terrain-aware / elevation-aware registration.
- Better physical camera and orbital geometry integration.
- More principled multimodal descriptors.
- Wider leave-one-pair-out and cross-mission generalization studies.
- Offline deployment for institutions with restricted connectivity.

---

## Research and Reproducibility Discipline

The project intentionally keeps a distinction between:

**Production**

- frozen thresholds,
- stable downstream mathematics,
- deterministic quality gates,
- safe failure,
- auditable outputs.

**Research**

- controlled experiments,
- ablations,
- new representations,
- geodetic investigations,
- alternative matchers,
- baseline comparisons.

A research experiment does not become production simply because it reports a better number on one pair.

---

## References and Related Resources

The project was developed around Chandrayaan-2 and lunar-image registration workflows, using mission and research resources including:

- ISRO / Chandrayaan mission resources
- Indian Space Science Data Centre / PRADAN resources
- Chandrayaan Data Explorer
- LROC / QuickMap resources
- relevant research literature on lunar image registration and feature matching

For the detailed experiment trail, see the research documentation under:

```text
research/submission_ready/
```

Recommended detailed documents include the architecture summary, mentor benchmark, geodetic findings, Phase 24A summary, limitations / future work, and evidence registry.

---

## Project Status

**Current status:** **Prototype / Research Evaluation**

The production pipeline is frozen around the validated acceptance criteria described in this README. Heavy stress cases are intentionally locked from live online execution. Research experiments remain separated from the production path.

> **LunarReg's main engineering contribution is not “always produce a registration.” It is to produce a registration when the evidence is strong enough — and to refuse when it is not.**

---

## License

Add the project's intended license here before publishing the repository publicly. Do not assume an open-source license unless one has been explicitly selected by the team.

---

## Team / Acknowledgement

Developed as an SIH 2026 prototype for Chandrayaan-2 lunar image registration research.

For technical or scientific reuse, please preserve the distinction between **measured evidence**, **research experiments**, and **future work** described in this repository.
