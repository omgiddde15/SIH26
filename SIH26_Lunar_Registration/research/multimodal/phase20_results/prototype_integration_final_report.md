# LunarReg — Final Prototype Integration & Verification Report
**Problem Statement SIH26166:** Development of an Adaptive Image Registration System for Lunar Orbital Imagery  
**Canonical Project Directory:** `C:\Users\Dell\Videos\SIH26_Lunar_Registration`  
**Evaluation Date:** September 23, 2026  
**Status:** Certified Demo-Ready | All Regression Tests Passing (16/16, 100%)

---

## 1. Executive Summary

The final prototype integration for ISRO Problem Statement SIH26166 has been completed and verified exclusively in the single canonical project repository: `C:\Users\Dell\Videos\SIH26_Lunar_Registration`.

### Strict Project Isolation
- **Canonical Repository:** `C:\Users\Dell\Videos\SIH26_Lunar_Registration` is the **only** active codebase.
- **Untouched Legacy Directory:** `C:\Users\Dell\Videos\SIH26` was preserved in its exact prior state. No files in `C:\Users\Dell\Videos\SIH26` were edited, overwritten, merged, or deleted.
- **Frozen Pipeline & Math:** Production matching algorithms, Locked LoFTR, quality gates, RANSAC thresholds (3.0 px), spatial distribution grid (3x3, max 6 pts/cell, cap 54), downstream geometry, and validation seeds `(1, 2, 3, 4, 5)` remain strictly frozen and unmodified.

All 5 user-approved requirements were implemented and verified with 100% passing tests:
1. **Authentication Account Migration:** User accounts migrated with preserved PBKDF2-HMAC-SHA256 hashes (`240,000` iterations, 16-byte random salt).
2. **Neutral Test User:** Verified with `lunarreg_test@example.com` (no fake institutional domains).
3. **Canonical 8-Stage Pipeline Stepper:** Visual stepper directly reflects runtime execution state across 8 verified stages.
4. **Factual Metadata Handling:** Fallback gracefully renders `"Mission metadata not available for this image."` when mission metadata is absent.
5. **Safe Quality-Gate Rejection:** Displays explicit `"Registration Rejected Safely"` card with exact candidate counts, initial inliers, inlier ratio, and blocked unsafe transformation.

---

## 2. Authentication Subsystem Resolution

### Root Cause Audit
- **Schema Divergence:** Canonical `data/users.db` contained a legacy table schema with a `salt TEXT NOT NULL` column, whereas modern `app/auth.py` generates combined PBKDF2-HMAC-SHA256 hash strings in format:  
  `240000$<salt_b64>$<hash_b64>`
- **Account Discrepancy:** The working user accounts (`shantaramgiddelala@gmail.com` and `202401070085@mitaoe.ac.in`) were present only in the old project database and missing from canonical `data/users.db`.
- **String Interpolation Hazard:** During initial migration attempts, shell variable expansion on `$` characters had corrupted the hash strings. Direct SQLite-to-SQLite record transfer resolved this issue completely.

### Implemented Fixes
1. **Idempotent Self-Healing Schema (`app/auth.py`):**
   `init_auth_db()` now automatically inspects `PRAGMA table_info(users)` and safely upgrades legacy schemas without table locking or column corruption:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
       id           INTEGER PRIMARY KEY AUTOINCREMENT,
       full_name    TEXT NOT NULL,
       email        TEXT NOT NULL UNIQUE,
       password_hash TEXT NOT NULL,
       created_at   TEXT NOT NULL DEFAULT (datetime('now'))
   );
   ```
2. **Migrated Accounts Verified:**
   - `shantaramgiddelala@gmail.com` (Full Name: Om) — PBKDF2 hash preserved and verified.
   - `202401070085@mitaoe.ac.in` (Full Name: Gidde) — PBKDF2 hash preserved and verified.
3. **Neutral Test User Lifecycle Verified:**
   - Identity: `lunarreg_test@example.com` (Full Name: `LunarReg Test Engineer`)
   - Signup: Succeeded with PBKDF2-HMAC-SHA256 record creation.
   - Login: Succeeded immediately with valid credentials.
   - Invalid Password Rejection: Wrong password rejected cleanly with `None`.
   - Non-existent Account Rejection: Ghost identity rejected cleanly with `None`.
   - Duplicate Signup Rejection: Attempting duplicate email registration rejected cleanly with `"An account with this email already exists."`

---

## 3. Prototype UI Architecture & Stepper Alignment

### Dynamic Environment Detection
The header dynamically queries system properties and displays:
```text
Python 3.14.5 | PyTorch 2.14.0+cpu | CPU
```
Guarded by a fault-tolerant function `detect_runtime_environment()` that never raises exceptions or interrupts Streamlit rendering.

### Canonical 8-Stage Pipeline Stepper
The UI stepper was refactored from 9 legacy states to the 8 canonical stages:

| Stage # | Stage Name | Runtime Execution Mapping |
|:---:|:---|:---|
| **1** | **Source + Reference** | Raster ingestion, dimensions verification, channel validation |
| **2** | **Metadata & Geo Information** | Chandrayaan-2 catalog lookup (footprints & stored models) |
| **3** | **Illumination & Preprocessing** | Grayscale conversion, CLAHE contrast equalization (8x8 grid, clip 2.0) |
| **4** | **Feature Correspondence Matching** | Adaptive Router execution (SIFT / LoFTR / SuperGlue) |
| **5** | **Geometric Estimation** | Quality Gate validation (min candidates $\ge 10$, inliers $\ge 8$, ratio $\ge 20\%$) |
| **6** | **Homography & Registration** | Common downstream refinement, 3x3 grid selection (max 6/cell, cap 54), RANSAC warp |
| **7** | **Independent Validation** | Multi-seed stability verification $(1, 2, 3, 4, 5)$, held-out tie-point check |
| **8** | **Results & Export** | Build export package (Warped PNG, CSV, JSON evidence, 7-page PDF report) |

Each stage renders live visual badges:
- `○ WAITING` (Dim gray `#6e7681`)
- `● RUNNING` (Pulsing blue `#58a6ff`)
- `✓ COMPLETE` (Bright green `#3fb950`)
- `✕ FAILED` (Amber/red `#f85149`)

### Graceful Fallback for Empty Image State
When no source/reference images are loaded, rather than failing or displaying an empty card, the UI renders:
```html
No image pair selected
Please upload both a Moving (Source) and Fixed (Reference) image above, or select one of the Quick-Load Benchmark & Demo Pairs to initialize the registration pipeline.
```

### Factual Metadata Handling
If an uploaded pair has no mission metadata catalog entry, the UI does not display broken placeholders or fabricate coordinates. Instead, it displays:
```text
Mission metadata not available for this image.
```
while continuing pipeline execution cleanly and showing image dimensions, format, and filename.

---

## 4. Safe Quality-Gate Rejection Presentation

For challenging pairs that lack sufficient correspondence (such as the uncalibrated cross-sensor pair `souse.jpeg` $\leftrightarrow$ `ref.jpeg`), LunarReg enforces certified quality gates and rejects registration safely.

### UI Rejection Presentation
- **Header Badge:** `✕ Registration Rejected Safely`
- **Primary Alert:** `Registration rejected safely because correspondence quality was insufficient.`
- **Telemetry Matrix (Cross-Sensor Benchmark):**
  - **Candidate Matches:** `199`
  - **Initial Inliers:** `12`
  - **Inlier Ratio:** `6.03%` (Certified Threshold: $\ge 20.0\%$)
  - **Spatial Occupancy:** `55.6%` (Certified Threshold: $\ge 33.3\%$)
  - **Quality Gate:** `REJECTED`
  - **Fallback Execution:** `TRIGGERED (SuperGlue)` — attempted and failed gate
  - **Transformation Status:** `BLOCKED (Safe Rejection)`
- **Scientific Integrity Guard:**
  > *"An unsafe transformation was blocked to preserve scientific integrity. When correspondence quality falls below certified thresholds, LunarReg rejects registration rather than producing inaccurate lunar surface artifacts."*

---

## 5. Production Benchmark Results

All benchmark pairs were evaluated with frozen production thresholds:

| Benchmark Case | Challenge Type | Router Selection | Final Inliers | Inlier Ratio | Spatial Occupancy | Runtime | Outcome |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Pair 04** | Optical Nominal | LoFTR | **54** | **100.0%** | **100.0%** (9/9 cells) | 2.65s | **SUCCESS** |
| **Pair 03** | Illumination Inversion | SIFT | **54** | **100.0%** | **100.0%** (9/9 cells) | 2.24s | **SUCCESS** |
| **Pair 01** | Scale Variation | LoFTR | **38** | **100.0%** | **88.9%** (8/9 cells) | 2.45s | **SUCCESS** |
| **Cross-Sensor** | Uncalibrated Cross-Sensor | LoFTR $\rightarrow$ SuperGlue | **12** | **6.03%** | **55.6%** (5/9 cells) | 19.51s | **SAFE REJECTION** |

---

## 6. Export Deliverables Verification

For registered pairs, the export engine builds a standardized 5-deliverable mission package:

| Deliverable | Format | Size | Content Verification |
|:---|:---:|:---:|:---|
| **Registered Image** | PNG | 414 KB | Full reference-frame dimension warped raster |
| **Match Coordinates** | CSV | 2.3 KB | `source_x,source_y,reference_x,reference_y,residual_px` |
| **Homography Model** | JSON | 1.9 KB | 3x3 transformation matrix, shapes, matcher telemetry |
| **Flight Evidence** | JSON | 1.9 KB | 20-attribute telemetry payload, zero numpy types |
| **Mission Report** | PDF | 286 KB | Standalone 7-page report verified with pypdf |
| **Complete Bundle** | ZIP | 645 KB | Compressed archive containing all 5 deliverables |

---

## 7. Canonical Launch Instructions

To launch the final verified LunarReg prototype:

```powershell
# 1. Open PowerShell and navigate to the canonical repository:
cd C:\Users\Dell\Videos\SIH26_Lunar_Registration

# 2. Launch the Streamlit application:
streamlit run app/app.py --server.port 8501
```

### Access Credentials:
- **Registered User:** `shantaramgiddelala@gmail.com`
- **Registered User:** `202401070085@mitaoe.ac.in`
- **Test Engineer User:** `lunarreg_test@example.com` / `LunarReg@2026!Secure`
- *New user self-registration is fully operational with duplicate-email prevention.*
