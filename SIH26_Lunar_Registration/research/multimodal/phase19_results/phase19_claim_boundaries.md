# LunarReg — Formal Claim Boundaries Document (SIH26166)

This document establishes the verified scientific boundary of LunarReg.
Under strict scientific methodology, no claim is made without reproducible evidence.

---

## 1. Sub-Pixel Accuracy Claim Boundary

### What Is Experimentally Demonstrated:
- **Sub-pixel correspondence localization demonstrated under controlled known-transform conditions.**
- On real lunar imagery subjected to predetermined sub-pixel translations, small rotations, and affine perturbations where true coordinates $P_{gt} = M_{inv} [P_{src}, 1]^T$ are mathematically verified:
  - Mean correspondence localization error: **`0.4204 px`** across all 8 conditions (`0.2647 px` – `0.3014 px` on pure translations).
  - Over **`90.97%`** of correspondences are $\le 1.00\text{ px}$, and **`80.56%`** are $\le 0.50\text{ px}$ (`100%` on translations).
  - Global homography registration corner error: **`0.6687 px`** (`0.2583 px` – `0.3029 px` on translations).
  - Multi-seed held-out cross-validation RMSE: **`0.0298 px`** across seeds 1–5.

### What Cannot Be Claimed:
- **"LunarReg has proven sub-pixel accuracy on real Chandrayaan-2 imagery."**
  - Physical correspondence ground truth (independently surveyed ground control points or sub-milliradian pointing models) is **absent** from the uncalibrated benchmark pair.
  - Held-out cross-validation RMSE on real crops (~`1.24–1.34 px`) measures internal model consistency, **NOT** ground-truth error.
  - Therefore, real-image sub-pixel physical accuracy remains **UNVERIFIED**.

---

## 2. Geometric & Physical Scale Claim Boundary

### What Is Experimentally Demonstrated:
- **Synthetic image-space scale sensitivity has been thoroughly evaluated.**
- Under controlled geometric scaling ($0.50\times, 0.75\times, 1.00\times, 1.25\times, 1.50\times, 2.00\times$), structural descriptor distance increases monotonically with upscale factor ($0.3801 \rightarrow 0.5543$), and only native $1.00\times$ achieves sufficient inliers to pass independent held-out validation.

### What Cannot Be Claimed:
- **"LunarReg achieves physical lunar scale invariance."**
- Physically grounded scale normalization (e.g. resampling nominal 0.25 m/px OHRC to 10 m/px IIRS) is **not reproducible** on the current benchmark because verified sensor metadata, camera focal length ($f$), detector pixel pitch ($p$), and spacecraft orbital altitude ($H$) are completely missing.
- No arbitrary physical scale factor (e.g., 40×, 320×, 0.25 m/px, 10 m/px) may be claimed as ground truth for uncalibrated crops.

---

## 3. Sensor & Cross-Modal Claim Boundary

### What Is Experimentally Demonstrated:
- **Intra-sensor optical registration on Chandrayaan-2 imagery is fully operational.**
  - Benchmarks across illumination variation, viewpoint distortion, and optical scale variation register with high confidence (up to 4,026 inliers, held-out RMSE < 0.01 px).

### What Cannot Be Claimed:
- **"LunarReg solves multimodal OHRC-to-IIRS or OHRC-to-TMC registration."**
  - Uncalibrated cross-sensor crops fail the 20% inlier ratio quality gate in production.
  - TMC-OHRC and TMC-IIRS calibrated pairs are **not available** in the current verified repository data.
