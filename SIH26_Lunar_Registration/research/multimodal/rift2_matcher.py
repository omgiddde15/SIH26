"""
research/multimodal/rift2_matcher.py
=====================================
RIFT2 implementation with documented LunarReg adaptations
for Experimental Cross-Sensor Lunar Image Registration.

Reference & Published Method:
- Li et al., "RIFT: Multi-Modal Image Matching Based on Radiation-Variation Insensitive Feature Transform",
  IEEE TGRS, 2019 / IEEE TIP, 2020.
- Li et al., "RIFT2: An efficient rotation-invariant multimodal image feature matching method", 2020/2021.

Pipeline (RIFT2 implementation with documented LunarReg adaptations):
1. Input grayscale image.
2. Multi-scale (4 scales), multi-orientation (6 orientations) 2D Log-Gabor wavelet decomposition in frequency domain.
3. Frequency-domain Phase Congruency (PC) computation providing contrast- and radiation-invariant response.
4. Maximum Index Map (MIM) calculation: pixel-wise orientation index of peak energy response (6 discrete indices).
5. FAST keypoint detection directly on normalized Phase Congruency response.
6. Gradient-based dominant orientation assignment per keypoint.
7. RIFT2 dominant MIM-index recoding to achieve rotation invariance without combinatorial matching overhead.
8. Local spatial grid aggregation (96x96 patch, 6x6 spatial sub-cells, 6-bin MIM histogram) -> 216-dimensional descriptor.
9. Deterministic nearest-neighbor descriptor matching (NNDR + mutual cross-check).

Implementation Adaptations & Documentation:
- Descriptor Geometry: 96x96 patch size, 6x6 spatial grid (16x16 px sub-cells), 6 MIM bins = 216 dimensions (conforms strictly to RIFT2 specification).
- FAST on PC: Uses OpenCV FAST with adaptive thresholding on normalized PC to ensure stable feature yield across varied lunar textures.
- Orientation Assignment: Standard gradient orientation histogram with Gaussian spatial weighting around keypoint location.
- Dominant MIM Recoding: MIM values in the rotated patch are circularly shifted by the discrete keypoint orientation index:
    MIM_recoded = (MIM - round(theta / (pi / 6))) % 6.
- Matching Policy: Nearest-Neighbor Distance Ratio (NNDR) with ratio threshold 0.90 (explicit LunarReg adaptation) plus mutual consistency (cross-check).
- Neutral Confidence: confidences=None (no fabricated confidence values; common downstream uses uniform weighting).
"""

import time
import gc
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

# Safe limits for full-image FFT filter bank allocation
_MAX_SAFE_PIXELS = 9_000_000
_MAX_SAFE_DIM = 3500


def build_log_gabor_filter_bank(
    rows: int,
    cols: int,
    n_scales: int = 4,
    n_orientations: int = 6,
    min_wave: float = 3.0,
    mult: float = 1.6,
    sigma_on_f: float = 0.65,
    d_theta_on_sigma: float = 1.2,
) -> List[List[np.ndarray]]:
    """Construct a 2D Log-Gabor filter bank in frequency domain."""
    u, v = np.meshgrid(
        np.fft.fftfreq(cols),
        np.fft.fftfreq(rows)
    )
    radius = np.sqrt(u**2 + v**2)
    radius[0, 0] = 1.0  # Avoid log(0) at DC component
    theta = np.arctan2(-v, u)

    filters: List[List[np.ndarray]] = []
    for o in range(n_orientations):
        angl = o * np.pi / n_orientations
        d_theta = np.abs(theta - angl)
        d_theta = np.minimum(d_theta, 2.0 * np.pi - d_theta)
        # Angular spread function
        spread = np.exp(- (d_theta**2) / (2.0 * (d_theta_on_sigma * (np.pi / n_orientations))**2))

        scale_filters: List[np.ndarray] = []
        for s in range(n_scales):
            wavelength = min_wave * (mult ** s)
            f0 = 1.0 / wavelength
            # Radial log-Gabor function
            log_radial = np.exp(- (np.log(radius / f0))**2 / (2.0 * (np.log(sigma_on_f))**2))
            log_radial[0, 0] = 0.0  # Zero DC component

            flt = (log_radial * spread).astype(np.float32)
            scale_filters.append(flt)
        filters.append(scale_filters)

    return filters


def compute_phase_congruency_and_mim(
    img_gray: np.ndarray,
    filters: List[List[np.ndarray]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute normalized Phase Congruency (PC) and Maximum Index Map (MIM)."""
    rows, cols = img_gray.shape
    f_img = np.fft.fft2(img_gray.astype(np.float32))

    n_orientations = len(filters)
    n_scales = len(filters[0])

    orient_energies = np.zeros((n_orientations, rows, cols), dtype=np.float32)
    total_amp = np.zeros((rows, cols), dtype=np.float32)
    total_energy = np.zeros((rows, cols), dtype=np.float32)

    for o in range(n_orientations):
        sum_e = np.zeros((rows, cols), dtype=np.float32)
        sum_o = np.zeros((rows, cols), dtype=np.float32)
        sum_a = np.zeros((rows, cols), dtype=np.float32)

        for s in range(n_scales):
            flt = filters[o][s]
            resp = np.fft.ifft2(f_img * flt)
            e = np.real(resp).astype(np.float32)
            odd = np.imag(resp).astype(np.float32)
            amp = np.sqrt(e**2 + odd**2)

            sum_e += e
            sum_o += odd
            sum_a += amp

        eo = np.sqrt(sum_e**2 + sum_o**2)
        orient_energies[o] = sum_a
        total_amp += sum_a
        total_energy += eo

    # Maximum Index Map (discrete index in [0, n_orientations - 1])
    mim = np.argmax(orient_energies, axis=0).astype(np.uint8)

    # Normalized Phase Congruency in [0, 1]
    eps = 1e-4
    pc = np.clip(np.maximum(0.0, total_energy) / (total_amp + eps), 0.0, 1.0)

    return pc, mim, orient_energies


def detect_rift2_keypoints(
    pc: np.ndarray,
    max_kps: int = 1500,
    fast_threshold: int = 10,
) -> Tuple[List[cv2.KeyPoint], int]:
    """Detect keypoints using FAST on normalized Phase Congruency map.

    Returns:
    - kps: List of detected cv2.KeyPoint objects (sorted by response)
    - base_count: Raw count before response sorting/capping
    """
    pc_u8 = (pc * 255.0).astype(np.uint8)
    fast = cv2.FastFeatureDetector_create(threshold=fast_threshold, nonmaxSuppression=True)
    kps = fast.detect(pc_u8)

    # Adaptive fallback if texture is low
    if len(kps) < 50:
        fast_low = cv2.FastFeatureDetector_create(threshold=max(4, fast_threshold // 2), nonmaxSuppression=True)
        kps = fast_low.detect(pc_u8)

    base_count = len(kps)
    if base_count > max_kps:
        kps = sorted(kps, key=lambda x: x.response, reverse=True)[:max_kps]

    return kps, base_count


def assign_gradient_orientations(
    img_gray: np.ndarray,
    kps: List[cv2.KeyPoint],
    n_bins: int = 36,
    radius: int = 16,
) -> List[Tuple[float, float, float]]:
    """Assign dominant orientation(s) to keypoints via Gaussian-weighted gradient histogram.

    Returns:
    - oriented_kps: List of (x, y, orientation_rad) tuples (with orientation expansion).
    """
    h, w = img_gray.shape
    # Compute image gradients via Sobel
    gx = cv2.Sobel(img_gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(img_gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    ang = np.arctan2(gy, gx)  # [-pi, pi]
    ang[ang < 0] += 2.0 * np.pi  # [0, 2*pi)

    bin_width = 2.0 * np.pi / n_bins
    sigma = radius / 2.0

    # Gaussian spatial kernel
    coords = np.arange(-radius, radius + 1)
    g_x, g_y = np.meshgrid(coords, coords)
    weights = np.exp(-(g_x**2 + g_y**2) / (2.0 * sigma**2))

    oriented_kps: List[Tuple[float, float, float]] = []

    for kp in kps:
        kx, ky = int(round(kp.pt[0])), int(round(kp.pt[1]))
        if kx - radius < 0 or kx + radius >= w or ky - radius < 0 or ky + radius >= h:
            continue

        patch_mag = mag[ky - radius:ky + radius + 1, kx - radius:kx + radius + 1]
        patch_ang = ang[ky - radius:ky + radius + 1, kx - radius:kx + radius + 1]

        hist = np.zeros(n_bins, dtype=np.float32)
        bin_indices = np.clip((patch_ang / bin_width).astype(int), 0, n_bins - 1)
        w_mag = patch_mag * weights

        for b in range(n_bins):
            hist[b] = np.sum(w_mag[bin_indices == b])

        max_bin = int(np.argmax(hist))
        max_val = float(hist[max_bin])
        if max_val <= 1e-6:
            oriented_kps.append((float(kp.pt[0]), float(kp.pt[1]), 0.0))
            continue

        # Parabolic peak interpolation
        left = float(hist[(max_bin - 1) % n_bins])
        right = float(hist[(max_bin + 1) % n_bins])
        denom = 2.0 * (left - 2.0 * max_val + right)
        peak_offset = -0.5 * (right - left) / denom if abs(denom) > 1e-6 else 0.0
        peak_bin = (max_bin + peak_offset) % n_bins
        dominant_orient = peak_bin * bin_width
        oriented_kps.append((float(kp.pt[0]), float(kp.pt[1]), float(dominant_orient)))

        # Orientation expansion: any peak >= 80% of max
        threshold_peak = 0.80 * max_val
        for b in range(n_bins):
            if b == max_bin:
                continue
            b_val = float(hist[b])
            b_left = float(hist[(b - 1) % n_bins])
            b_right = float(hist[(b + 1) % n_bins])
            if b_val >= threshold_peak and b_val > b_left and b_val > b_right:
                d = 2.0 * (b_left - 2.0 * b_val + b_right)
                p_off = -0.5 * (b_right - b_left) / d if abs(d) > 1e-6 else 0.0
                p_bin = (b + p_off) % n_bins
                oriented_kps.append((float(kp.pt[0]), float(kp.pt[1]), float(p_bin * bin_width)))

    return oriented_kps


def compute_rift2_descriptors(
    img_shape: Tuple[int, int],
    oriented_kps: List[Tuple[float, float, float]],
    mim: np.ndarray,
    patch_size: int = 96,
    grid_size: int = 6,
    n_orientations: int = 6,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute canonical 216-dimensional RIFT2 rotation-invariant descriptors.

    Parameters:
    - patch_size: 96x96
    - grid_size: 6x6 (36 sub-cells)
    - n_orientations: 6 MIM bins
    - Dimension: 6 x 6 x 6 = 216

    Applies RIFT2 dominant MIM-index recoding:
        shift = round(theta / (pi / n_orientations)) % n_orientations
        mim_recoded = (mim - shift) % n_orientations
    """
    h, w = img_shape
    radius = patch_size // 2
    sub_size = patch_size // grid_size  # 16 px per sub-cell

    # Coordinate grid of sub-cell centers relative to patch center
    grid_coords = np.linspace(-radius + sub_size / 2.0, radius - sub_size / 2.0, grid_size)
    gx, gy = np.meshgrid(grid_coords, grid_coords)
    rel_pts = np.vstack([gx.ravel(), gy.ravel()])  # 2 x 36

    valid_pts: List[Tuple[float, float]] = []
    descriptors: List[np.ndarray] = []

    half_sub = sub_size // 2

    for x, y, theta in oriented_kps:
        ix, iy = int(round(x)), int(round(y))
        if ix - radius < 0 or ix + radius >= w or iy - radius < 0 or iy + radius >= h:
            continue

        # Rotation matrix for sub-cell spatial alignment
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s], [s, c]], dtype=np.float32)
        rot_pts = R @ rel_pts

        sub_centers_x = np.clip(np.round(x + rot_pts[0]).astype(int), 0, w - 1)
        sub_centers_y = np.clip(np.round(y + rot_pts[1]).astype(int), 0, h - 1)

        # RIFT2 discrete MIM orientation recoding
        shift = int(np.round((theta % np.pi) / (np.pi / n_orientations))) % n_orientations

        desc_vector = np.zeros(grid_size * grid_size * n_orientations, dtype=np.float32)

        for cell_idx, (sc_x, sc_y) in enumerate(zip(sub_centers_x, sub_centers_y)):
            y1 = max(0, sc_y - half_sub)
            y2 = min(h, sc_y + half_sub + 1)
            x1 = max(0, sc_x - half_sub)
            x2 = min(w, sc_x + half_sub + 1)

            sub_mim = mim[y1:y2, x1:x2]
            if sub_mim.size == 0:
                continue

            # Recode MIM indices relative to dominant orientation
            shifted_mim = (sub_mim.astype(int) - shift) % n_orientations
            hist, _ = np.histogram(shifted_mim, bins=n_orientations, range=(0, n_orientations))

            start_idx = cell_idx * n_orientations
            desc_vector[start_idx:start_idx + n_orientations] = hist.astype(np.float32)

        # Standard RIFT2 L2 normalization with contrast thresholding
        norm = np.linalg.norm(desc_vector)
        if norm > 1e-6:
            desc_vector /= norm
            # Contrast threshold clipping at 0.2
            desc_vector = np.clip(desc_vector, 0.0, 0.2)
            norm2 = np.linalg.norm(desc_vector)
            if norm2 > 1e-6:
                desc_vector /= norm2

        valid_pts.append((x, y))
        descriptors.append(desc_vector)

    pts_arr = np.array(valid_pts, dtype=np.float32) if valid_pts else np.empty((0, 2), dtype=np.float32)
    desc_arr = np.array(descriptors, dtype=np.float32) if descriptors else np.empty((0, 216), dtype=np.float32)

    return pts_arr, desc_arr


def match_rift2_descriptors(
    desc0: np.ndarray,
    desc1: np.ndarray,
    ratio_thresh: float = 0.90,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """Deterministic Nearest-Neighbor Distance Ratio (NNDR) matching with mutual cross-check.

    Parameters:
    - ratio_thresh: 0.90 (LunarReg documented adaptation)
    - Enforces mutual one-to-one correspondence.

    Returns:
    - match_indices0: Indices into desc0
    - match_indices1: Indices into desc1
    - distance_stats: Mean, std, min, max matching distances
    """
    if len(desc0) == 0 or len(desc1) == 0:
        return np.empty(0, dtype=int), np.empty(0, dtype=int), {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

    bf = cv2.BFMatcher(cv2.NORM_L2)

    # 1. Forward matching: desc0 -> desc1 (k=2 for NNDR)
    matches_01 = bf.knnMatch(desc0, desc1, k=2)
    best_01: Dict[int, int] = {}
    dist_01: Dict[int, float] = {}

    for m in matches_01:
        if len(m) == 2:
            if m[0].distance < ratio_thresh * m[1].distance:
                best_01[m[0].queryIdx] = m[0].trainIdx
                dist_01[m[0].queryIdx] = float(m[0].distance)
        elif len(m) == 1:
            best_01[m[0].queryIdx] = m[0].trainIdx
            dist_01[m[0].queryIdx] = float(m[0].distance)

    # 2. Backward matching: desc1 -> desc0 (for mutual cross-check)
    matches_10 = bf.knnMatch(desc1, desc0, k=1)
    best_10: Dict[int, int] = {m[0].queryIdx: m[0].trainIdx for m in matches_10 if len(m) > 0}

    # 3. Filter for mutual consistency
    mutual_0: List[int] = []
    mutual_1: List[int] = []
    distances: List[float] = []

    for idx0, idx1 in best_01.items():
        if best_10.get(idx1) == idx0:
            mutual_0.append(idx0)
            mutual_1.append(idx1)
            distances.append(dist_01[idx0])

    idx0_arr = np.array(mutual_0, dtype=int)
    idx1_arr = np.array(mutual_1, dtype=int)

    dist_stats = {
        "mean": round(float(np.mean(distances)), 4) if distances else 0.0,
        "std": round(float(np.std(distances)), 4) if distances else 0.0,
        "min": round(float(np.min(distances)), 4) if distances else 0.0,
        "max": round(float(np.max(distances)), 4) if distances else 0.0,
    }

    return idx0_arr, idx1_arr, dist_stats


def run_rift2_matching(
    source_img: np.ndarray,
    reference_img: np.ndarray,
    ransac_thresh: float = 3.0,
    max_kps: int = 1500,
    ratio_thresh: float = 0.90,
    scale_mode: str = "native_baseline",
    source_scale: float = 1.0,
    reference_scale: float = 1.0,
) -> Dict[str, Any]:
    """Execute complete RIFT2 feature matching pipeline.

    Contract:
    - Returns raw descriptor correspondences only (pts0, pts1).
    - confidences = None (no fabricated confidence).
    - Does NOT compute final RANSAC inliers, 3x3 spatial selection, homography,
      or held-out validation (those belong to execute_common_downstream).
    """
    t_start = time.perf_counter()

    if source_img is None or reference_img is None:
        raise ValueError("source_img and reference_img must not be None.")

    # Convert to 2D uint8 grayscale
    s_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY) if source_img.ndim == 3 else source_img.copy()
    r_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY) if reference_img.ndim == 3 else reference_img.copy()

    s_h, s_w = s_gray.shape
    r_h, r_w = r_gray.shape

    # Preflight resource guard
    max_pixels = max(s_h * s_w, r_h * r_w)
    max_dim = max(s_h, s_w, r_h, r_w)
    if max_pixels > _MAX_SAFE_PIXELS or max_dim > _MAX_SAFE_DIM:
        return {
            "method": "RIFT2",
            "success": False,
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "confidences": None,
            "n_candidates": 0,
            "runtime": round(time.perf_counter() - t_start, 3),
            "failure_stage": "resource_guard",
            "failure_reason": (
                f"Image dimensions ({s_w}x{s_h} / {r_w}x{r_h}, max_dim={max_dim}) exceed safe RIFT2 limit "
                f"(max_dim={_MAX_SAFE_DIM}, max_pixels={_MAX_SAFE_PIXELS})."
            ),
            "keypoints_source": 0,
            "keypoints_reference": 0,
            "descriptor_dim": 216,
        }

    # Step 1: Log-Gabor Filters & Phase Congruency / MIM
    t0_pc = time.perf_counter()
    flts_s = build_log_gabor_filter_bank(s_h, s_w, n_scales=4, n_orientations=6)
    flts_r = build_log_gabor_filter_bank(r_h, r_w, n_scales=4, n_orientations=6)

    pc_s, mim_s, _ = compute_phase_congruency_and_mim(s_gray, flts_s)
    pc_r, mim_r, _ = compute_phase_congruency_and_mim(r_gray, flts_r)
    t_pc = round(time.perf_counter() - t0_pc, 3)

    # Step 2: FAST Keypoint Detection on Phase Congruency
    t0_det = time.perf_counter()
    kps_s, base_count_s = detect_rift2_keypoints(pc_s, max_kps=max_kps)
    kps_r, base_count_r = detect_rift2_keypoints(pc_r, max_kps=max_kps)
    t_det = round(time.perf_counter() - t0_det, 3)

    if len(kps_s) < 4 or len(kps_r) < 4:
        return {
            "method": "RIFT2",
            "success": False,
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "confidences": None,
            "n_candidates": 0,
            "runtime": round(time.perf_counter() - t_start, 3),
            "failure_stage": "keypoint_detection",
            "failure_reason": f"Insufficient keypoints detected (source={len(kps_s)}, reference={len(kps_r)}).",
            "keypoints_source": len(kps_s),
            "keypoints_reference": len(kps_r),
            "descriptor_dim": 216,
        }

    # Step 3: Gradient-Based Orientation Assignment
    t0_orient = time.perf_counter()
    oriented_s = assign_gradient_orientations(s_gray, kps_s)
    oriented_r = assign_gradient_orientations(r_gray, kps_r)
    t_orient = round(time.perf_counter() - t0_orient, 3)

    # Step 4: RIFT2 Dominant-Index Recoded Descriptor (216-dim)
    t0_desc = time.perf_counter()
    pts_s, desc_s = compute_rift2_descriptors((s_h, s_w), oriented_s, mim_s, patch_size=96, grid_size=6, n_orientations=6)
    pts_r, desc_r = compute_rift2_descriptors((r_h, r_w), oriented_r, mim_r, patch_size=96, grid_size=6, n_orientations=6)
    t_desc = round(time.perf_counter() - t0_desc, 3)

    if len(desc_s) < 4 or len(desc_r) < 4:
        return {
            "method": "RIFT2",
            "success": False,
            "pts0": np.empty((0, 2), dtype=np.float32),
            "pts1": np.empty((0, 2), dtype=np.float32),
            "confidences": None,
            "n_candidates": 0,
            "runtime": round(time.perf_counter() - t_start, 3),
            "failure_stage": "descriptor_generation",
            "failure_reason": f"Insufficient valid descriptors (source={len(desc_s)}, reference={len(desc_r)}).",
            "keypoints_source": len(desc_s),
            "keypoints_reference": len(desc_r),
            "descriptor_dim": 216,
        }

    # Step 5: Descriptor Matching (NNDR + Mutual Cross-Check)
    t0_match = time.perf_counter()
    m0, m1, dist_stats = match_rift2_descriptors(desc_s, desc_r, ratio_thresh=ratio_thresh)
    t_match = round(time.perf_counter() - t0_match, 3)

    pts0 = pts_s[m0]
    pts1 = pts_r[m1]
    n_candidates = len(pts0)
    total_time = round(time.perf_counter() - t_start, 3)

    success = n_candidates >= 4

    # Release intermediate filter arrays
    del flts_s, flts_r, pc_s, pc_r, mim_s, mim_r
    gc.collect()

    return {
        "method": "RIFT2",
        "success": success,
        "pts0": pts0,
        "pts1": pts1,
        "confidences": None,  # Explicitly neutral
        "n_candidates": n_candidates,
        "runtime": total_time,
        "failure_stage": None if success else "descriptor_matching",
        "base_keypoints_source": len(kps_s),
        "base_keypoints_reference": len(kps_r),
        "oriented_features_source": len(desc_s),
        "oriented_features_reference": len(desc_r),
        "keypoints_source": len(desc_s),
        "keypoints_reference": len(desc_r),
        "descriptor_dim": 216,
        "telemetry": {
            "source_shape": (s_h, s_w),
            "reference_shape": (r_h, r_w),
            "requested_keypoints_source": max_kps,
            "requested_keypoints_reference": max_kps,
            "base_keypoints_source": base_count_s,
            "base_keypoints_reference": base_count_r,
            "actual_keypoints_source": len(desc_s),
            "actual_keypoints_reference": len(desc_r),
            "orientation_expanded_source": len(oriented_s),
            "orientation_expanded_reference": len(oriented_r),
            "descriptor_dim": 216,
            "candidate_matches": n_candidates,
            "distance_statistics": dist_stats,
            "matching_policy": f"NNDR (ratio={ratio_thresh}) with mutual cross-check",
            "runtime_phase_congruency": t_pc,
            "runtime_detection": t_det,
            "runtime_orientation": t_orient,
            "runtime_descriptor": t_desc,
            "runtime_matching": t_match,
            "total_runtime": total_time,
            "scale_mode": scale_mode,
            "source_scale": source_scale,
            "reference_scale": reference_scale,
        }
    }
