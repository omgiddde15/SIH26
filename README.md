# LunarReg — Adaptive Lunar Image Registration System

**Adaptive, resource-aware and evidence-driven image registration for Chandrayaan-2 lunar imagery.**

**Core principle: Reliability > Forced Alignment**

| Project | Details |
|---|---|
| SIH Problem Statement | **SIH26166** — Multi-modal, sun-angle and scale-invariant image correspondence using Chandrayaan-2 imagery (OHRC, TMC/TMC-2 and IIRS) |
| Team | **DRISHTI_1.0** |
| Status | Research / prototype evaluation |
| Interface | Streamlit |
| Main technologies | Python, PyTorch, OpenCV, NumPy, Streamlit |

**Live demo:** https://rqq6zmr3n7eb7pnnovkqxx.streamlit.app/ 
**GitHub repository:** https://github.com/omgiddde15/SIH26

> LunarReg is a research prototype. It does not claim official SIH ground-truth validation, guaranteed performance on every lunar image pair, universal sun-angle invariance, or successful registration across all OHRC/TMC/IIRS combinations.

---

## Project Overview

LunarReg is designed to align a **source (moving) image** with a **reference (fixed) image**. Images of the same lunar terrain can look different because of sensor modality, spatial resolution, scale, illumination, viewpoint, texture and acquisition conditions.

Rather than accepting every mathematically possible warp, LunarReg evaluates correspondence quality and geometry before releasing a registration product.

The production workflow:

1. Reads the source and reference images and any available metadata.
2. Characterizes resolution, scale, contrast, texture, image dimensions and resource requirements.
3. Prepares images using the preprocessing actually selected for the current execution.
4. Selects a suitable matcher/recovery path based on image conditions and resource constraints.
5. Generates and evaluates feature correspondences.
6. Applies correspondence-quality and spatial-coverage gates.
7. Uses RANSAC and homography estimation for geometric registration.
8. Warps the source into the reference frame only when acceptance criteria pass.
9. Checks the result using independent hold-out observations.
10. Presents metrics and, where supported, exports the registered image and evidence package.

**If the evidence is insufficient, LunarReg safely rejects the run instead of forcing an untrusted registration.**

## Why the Problem Is Difficult

The SIH26166 problem focuses on multi-modal, sun-angle and scale-invariant correspondence using Chandrayaan-2 imaging instruments.

- **Illumination variation:** changes in solar azimuth/elevation and shadowing alter surface appearance.
- **Scale variation:** different imaging altitudes and native resolutions create large scale differences.
- **Viewpoint variation:** acquisition geometry can shift, rotate, scale or distort terrain features.
- **Multi-modal imagery:** OHRC, TMC/TMC-2 and IIRS can represent the same scene with substantially different image characteristics.
- **Large rasters:** full-image deep matching can exceed the available memory or compute budget.
- **Unreliable matches:** many candidate matches do not necessarily mean a correct geometric alignment.

The system is designed to make these decisions inspectable through quality metrics, validation results and safe-rejection reasons.

## Key Features

### Adaptive Matching and Resource-Aware Routing

- **LoFTR:** primary deep correspondence path for suitable inputs.
- **SIFT:** guarded recovery path where classical local features are appropriate.
- **SuperGlue:** available as a guarded/experimental recovery path.
- **Resource checks:** avoid unsafe full-image execution on inputs that exceed the allowed processing budget.

The adaptive router selects the execution path based on the current image pair and resource conditions. Research experiments do not automatically become production routing rules.

### Memory-Safe Large-Image Processing

For large inputs, LunarReg can use an overlapping tiled LoFTR strategy in supported local research runs. Tile-level correspondences are mapped back to global image coordinates and merged before downstream verification.

**Online limitation:** Tycho and Large Image Tiled LoFTR stress cases are locked from live online execution to protect the CPU-constrained deployment. Their documented local results or recorded walkthroughs may be used for demonstration; selecting a locked case online does not mean that the expensive registration has run live.

### Correspondence Quality and Spatial Distribution

The frozen production gate checks evidence such as:

| Check | Production criterion |
|---|---:|
| Minimum candidate correspondences | 10 |
| Minimum initial inliers | 8 |
| Minimum initial inlier ratio | 20% |
| Minimum spatial occupancy | 33.3% |
| RANSAC reprojection threshold | 3.0 px |
| Spatial selection | 3 × 3 grid |
| Maximum selected points per cell | 6 |
| Resource reference ceiling | 2.60 GB |

These are the documented production criteria; they are not automatically tuned during a normal run.

### Independent Hold-Out Validation

Fit quality and independent consistency are reported separately. Hold-out observations are not used to fit the final transform. Metrics can include held-out RMSE, median error, maximum error, inlier count, inlier ratio, spatial occupancy and validation status.

A held-out RMSE is an **image-space geometric consistency measurement**. It is not automatically physical ground-truth accuracy on the lunar surface.

### Safe Rejection

If candidate count, inlier quality, spatial coverage, resource limits or validation criteria are insufficient, LunarReg withholds the accepted registration product. A rejected case should not display a fabricated registered image or an unverified homography.

### Metadata and Evidence Export

Where supported by the current application, users can attach Chandrayaan-2/PDS4 XML metadata for source/reference images. The application includes XML parsing and reports available metadata rather than inventing missing mission information.

Successful runs can provide an evidence bundle containing:

- Registered PNG/image output
- Correspondence CSV
- Homography JSON
- Structured evidence JSON
- Scientific PDF report
- ZIP package where enabled

The PDF/reporting path also supports explicit safe-rejection reporting.

---

## Current Research Lab

The first Research Lab tab follows this presentation sequence:

### 1. Mentor OHRC 2D Image View

Shows the original mentor OHRC reference/source rasters and the metadata available for the selected scene. Mentor data are benchmark/research evidence, not proof of a successful registration.

**Deployment note:** mentor rasters may be stored outside the Git repository. The 2D image view is available online only when the required raster assets are accessible to the deployed application. A path on a developer's PC is not accessible automatically from Streamlit Cloud.

### 2. Mentor OHRC Lunar Terrain — 3D

Uses the supplied standalone Plotly HTML artifact based on OHRC imagery and an LROC DEM to provide physical terrain and geometric context.

**This 3D visualization is research-only. It does not generate correspondences, calculate the production registration transform, or modify the production matcher, quality gates, homography or validation.**

### 3. Registration Evidence & Production Preprocessing

Displays production execution evidence, including the actual image pair, preprocessing outputs and telemetry captured by the registration run, routing decisions, correspondences, quality gates, geometry, registered product and validation state.

The evidence view should show the real execution outputs—not a separately reconstructed preprocessing pipeline. Rejected executions should display rejection status and should not show a fake registered image.

Other Research Lab areas support controlled benchmark, ablation, matcher diagnostics, locked baseline, LOPO-style validation, multimodal/feasibility experiments, mentor benchmark and geodetic research, depending on the current application build.

Research modules are separate from production. A research result is not automatically adopted into the production algorithm.

---

## Verified Prototype Evidence

The following examples are case-specific and should not be interpreted as universal performance guarantees.

### Pair 04 — Optical Nominal

The current production evidence view reports:

- Selected matcher: **SIFT**
- Candidate matches: **3,946**
- Initial inliers: **3,940**
- Initial inlier ratio: **99.85%**
- Selected correspondences: **54**
- Spatial occupancy: **100% (9/9 cells)**
- Fit RMSE: **0.0032 px**
- Held-out RMSE: **0.0034 px**
- Outcome: **Accepted** for this recorded execution

### Pair 03 — Illumination Variation

A canonical demonstration case used to show the pipeline's behaviour under an illumination-change condition. Results must be reported from the exact run being demonstrated.

### Pair 01 — Scale / Resolution Example

A canonical scale-handling demonstration. The earlier documented run reported 166 candidates, 49 initial inliers (29.52%), 38 final selected inliers, 8/9 spatial occupancy, 1.437 px fit RMSE and 1.7188 px held-out RMSE. That particular result was validated but **not sub-pixel**.

### Pair 02 — Memory-Safe Failure

A controlled safe-rejection example. The quality gate rejected the available correspondence evidence; no accepted registered product was generated.

### Pair 05 — Real Lunar / OHRC

The project report documents a real-lunar prototype run with 54 final selected correspondences, 9/9 spatial occupancy, 0.4412 px fit RMSE and **0.4623 px held-out RMSE**. This is case-specific evidence, not a universal accuracy guarantee.

### Mentor Benchmark

Six mentor datasets (four OHRC and two IIRS) were evaluated under the frozen production configuration:

| Result | Count |
|---|---:|
| Mentor datasets evaluated | 6 |
| Registered and independently validated | 0 |
| Safe rejections | 6 / 6 |
| Runtime crashes | 0 |

**Interpretation:** all six mentor cases were safely rejected under the frozen production quality criteria. Successful mentor-dataset registration has not yet been demonstrated. This is safe-failure evidence, not mentor registration accuracy.

### Phase 24A — Coarse Placement Verification

The research study screened 196 deterministic placement hypotheses. Sixteen candidates passed the inexpensive screening stage and were checked with LoFTR; **zero** passed the frozen quality gate and independent hold-out validation. The result was classified as `VERIFICATION_FAILED`. Phase 24A was a coarse prefilter, not an exhaustive search of every possible continuous placement.

---

## Known Limitations and Scientific Claim Boundaries

- Successful mentor multimodal registration has not yet been demonstrated.
- Universal registration across all OHRC, TMC/TMC-2 and IIRS combinations is not claimed.
- Guaranteed sun-angle invariance or physical scale invariance is not claimed.
- Sub-pixel results are case-specific and must not be generalized to every lunar image pair.
- Official SIH ground-truth accuracy is not claimed.
- The upstream identity and absolute geodetic realization of some reference products remain unresolved.
- The original exhaustive ±3 km LoFTR placement search was deferred because of computational cost.
- A planar homography does not fully model arbitrary three-dimensional lunar terrain relief.
- Online CPU/compute constraints limit heavy tiled LoFTR stress runs.

## Technology Stack

| Layer | Technology |
|---|---|
| User interface | Streamlit |
| Language | Python |
| Deep correspondence | PyTorch / Kornia / LoFTR |
| Classical computer vision | OpenCV / SIFT |
| Numerical processing | NumPy |
| Visualization | Matplotlib / Plotly for selected research views |
| Reporting | ReportLab |
| Authentication | SQLite-backed application accounts |
| Geospatial research | GDAL, Rasterio, PROJ and relevant lunar raster/PDS4 metadata tools |

The current production geometry uses **OpenCV RANSAC and homography estimation**. Do not assume that proposed alternatives such as MAGSAC++ or TPS are part of the production path.

---

## Try LunarReg

### Online Demo

Open **https://sih26.streamlit.app**.

- Use **Quick Demo Access** if it is available on the login page.
- Start with a lightweight canonical example.
- Inspect correspondence counts, inliers, spatial coverage and validation.
- Use the safe-rejection case to see how the app handles insufficient evidence.
- Heavy stress cases are locked from live online execution; use the linked recorded evidence where provided.

The deployed application may take time to wake up. Availability and resource limits are controlled by the hosting environment.

### Run Locally on Windows

Use Python 3.13 as the tested project environment. From the repository root:

```powershell
cd SIH26_Lunar_Registration
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app\app.py
```

Then open **http://localhost:8501**.

If PowerShell blocks virtual-environment activation, run Streamlit with the environment's Python executable as shown above; activation is not required.

### Run Tests

From the repository root, confirm the correct test directory exists, then run:

```powershell
py -3.13 -m pytest tests -v
```

Some tests use local mentor data or deployment-sensitive paths. A test that requires unavailable external rasters may need the appropriate data files; do not replace missing data with fabricated samples.

### Configuration and Secrets

- The project uses `.streamlit/config.toml` to set the Streamlit application theme to dark.
- Configure any required bootstrap account through Streamlit secrets or the deployment's secure secret store.
- Never commit real passwords, private API keys, authentication databases or personal credentials to GitHub.
- Use only the public demo-access flow for reviewers; do not publish private account credentials.

---

## Repository Structure

The repository contains the application, test suites, datasets and research material. A representative project structure is:

```text
SIH26/
├── .streamlit/
│   └── config.toml
├── SIH26_Lunar_Registration/
│   ├── app/
│   │   ├── app.py
│   │   ├── auth.py
│   │   ├── adaptive_adapter.py
│   │   ├── registration_core.py
│   │   ├── metadata_parser.py
│   │   ├── pdf_generator.py
│   │   └── assets/
│   │       └── OHRC_Lunar_3D_Terrain.html
│   ├── data/
│   ├── research/
│   └── requirements.txt
├── tests/
└── README.md
```

Actual contents can differ as the repository evolves. Check the current Git tree before assuming that optional raw data directories are included.

## Future Work

- Expand independently validated cross-sensor experiments across OHRC, TMC/TMC-2 and IIRS.
- Investigate modality-aware representations and matching methods for difficult cross-sensor pairs.
- Test solar-geometry-aware photometric normalization when authoritative metadata and suitable validation data are available.
- Explore terrain-aware/local geometric refinement after correspondence evidence is sufficiently dense and reliable.
- Improve runtime and GPU/accelerator support for large-image processing.
- Strengthen independent geodetic and physical ground-truth validation.
- Improve offline deployment and experiment reproducibility.

## Project Status

**Current status: Prototype / Research Evaluation**

The production pipeline is intentionally conservative and evidence-driven. The application demonstrates successful registration on selected prototype cases, memory-aware handling for supported large-image research runs, independent validation, and safe rejection when the evidence is inadequate. Mentor multimodal registration remains an open validation gap.

**Match → Verify → Align → Validate.**

For scientific reuse, preserve the distinction between measured evidence, research experiments and future work.

## License

No open-source license is claimed here unless one is explicitly added to the repository. Contact the project team before reusing project-specific assets or research data.

## Team

Developed by **DRISHTI_1.0** for Smart India Hackathon 2026, Problem Statement **SIH26166**.
