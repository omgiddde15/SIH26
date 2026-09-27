"""
research/multimodal/multimodal_preprocess.py
=============================================
Multimodal Preprocessing Module for Cross-Sensor & Radiometrically Divergent
Lunar Imagery (LunarReg Phase 1 — Multimodal Research Branch).

Provides deterministic, coordinate-preserving transformations designed to
evaluate representation robustness across sensor modalities (e.g., IIRS ↔ OHRC)
and illumination variations without altering the underlying spatial grid.

Mathematical & Operational Guarantees:
- Input: source/reference uint8 lunar images (2D or 3D BGR/RGB).
- Output: matching-ready uint8 grayscale images (ndim == 2, dtype == np.uint8).
- Dimension preservation: output (H, W) exactly equals input (H, W).
- Coordinate preservation: strict zero-offset identity mapping (no warp, crop, or resize).
- Deterministic: 100% reproducible, zero stochastic operations.
- Descriptive Telemetry: factual photometric & gradient discrepancy metrics.
"""

from typing import Any, Dict, Tuple
import cv2
import numpy as np

MULTIMODAL_REPRESENTATIONS = (
    "baseline_clahe",
    "histogram_normalized",
    "gradient_magnitude",
    "local_gradient_normalized",
)


def _ensure_uint8_grayscale(image: np.ndarray, name: str = "image") -> np.ndarray:
    """Validate and convert an input lunar image to 2D uint8 grayscale.

    Strictly preserves (H, W) dimensions without resizing, warping, or cropping.
    """
    if image is None:
        raise ValueError(f"Input '{name}' is None.")
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Input '{name}' must be a numpy.ndarray, got {type(image).__name__}.")
    if image.size == 0:
        raise ValueError(f"Input '{name}' is empty (0 pixels).")

    # Handle channel dimension without changing spatial dimensions
    if image.ndim == 3:
        if image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif image.shape[2] == 1:
            gray = image[:, :, 0]
        else:
            raise ValueError(f"Unsupported channel depth {image.shape[2]} for '{name}'.")
    elif image.ndim == 2:
        gray = image.copy()
    else:
        raise ValueError(f"Unsupported array dimensionality {image.ndim} for '{name}'.")

    # Ensure strictly uint8 format
    if gray.dtype != np.uint8:
        if np.issubdtype(gray.dtype, np.floating):
            # Safe bounded cast for float images in [0, 1] or [0, 255]
            max_val = float(np.max(gray)) if gray.size > 0 else 0.0
            if max_val <= 1.0:
                gray = np.clip(gray * 255.0, 0, 255).astype(np.uint8)
            else:
                gray = np.clip(gray, 0, 255).astype(np.uint8)
        else:
            gray = np.clip(gray, 0, 255).astype(np.uint8)

    return gray


def to_baseline_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    """1. Baseline CLAHE Representation.

    Applies standard Contrast Limited Adaptive Histogram Equalization matching
    the validated LunarReg baseline configuration.

    Guarantees:
    - Exactly preserves input dimensions (H, W).
    - Returns 2D uint8 grayscale.
    """
    gray = _ensure_uint8_grayscale(image, name="baseline_clahe_input")
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    out = clahe.apply(gray)
    return out


def to_histogram_normalized(image: np.ndarray) -> np.ndarray:
    """2. Histogram Normalized Representation.

    Applies deterministic global cumulative histogram equalization across [0, 255].
    Flattens density imbalances caused by differing sensor sensitivity curves or
    broad exposure shifts across sensors.

    Guarantees:
    - Exactly preserves input dimensions (H, W).
    - Returns 2D uint8 grayscale.
    """
    gray = _ensure_uint8_grayscale(image, name="histogram_normalized_input")
    if np.ptp(gray) == 0:
        return gray.copy()
    out = cv2.equalizeHist(gray)
    return out


def to_gradient_magnitude(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    """3. Gradient Magnitude Representation (Structural).

    Computes spatial Sobel gradient magnitude, reducing dependence on absolute
    intensity while emphasizing geometric and structural transitions such as
    crater rims, ridges, and morphological boundaries.

    Note: This representation reduces dependence on absolute illumination but is
    not mathematically invariant to arbitrary monotonic radiometric transformations.

    Guarantees:
    - Exactly preserves input dimensions (H, W).
    - Returns 2D uint8 grayscale.
    """
    gray = _ensure_uint8_grayscale(image, name="gradient_magnitude_input")
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
    mag = np.sqrt(gx**2 + gy**2)

    max_val = float(np.max(mag))
    if max_val > 1e-6:
        # Bounded deterministic scaling to [0, 255]
        norm_mag = np.clip((mag / max_val) * 255.0, 0, 255).astype(np.uint8)
    else:
        norm_mag = np.zeros_like(gray, dtype=np.uint8)

    return norm_mag


def to_local_gradient_normalized(
    image: np.ndarray,
    ksize: int = 3,
    window_size: int = 15,
    eps: float = 10.0,
) -> np.ndarray:
    """4. Local Gradient Normalized Representation (Locally Normalized Structural).

    Computes Sobel gradient magnitude normalized by local standard deviation.
    Emphasizes high-frequency structural contours while mitigating regional
    contrast bias between brightly lit lunar plains and deeply shadowed crater
    interiors. A bounded epsilon prevents uncontrolled noise amplification in
    flat, zero-texture regions.

    Guarantees:
    - Exactly preserves input dimensions (H, W).
    - Returns 2D uint8 grayscale.
    """
    gray = _ensure_uint8_grayscale(image, name="local_gradient_normalized_input")
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
    mag = np.sqrt(gx**2 + gy**2)

    # Local mean and local standard deviation via spatial box filtering
    gf = gray.astype(np.float32)
    local_mean = cv2.boxFilter(gf, -1, (window_size, window_size))
    local_sq_mean = cv2.boxFilter(gf**2, -1, (window_size, window_size))
    local_var = np.maximum(local_sq_mean - local_mean**2, 0.0)
    local_std = np.sqrt(local_var)

    # Normalize gradient magnitude by local standard deviation with epsilon
    norm_grad = mag / (local_std + float(eps))

    # Robust 99.9th percentile bound to suppress single-pixel spike artifacts
    p999 = float(np.percentile(norm_grad, 99.9))
    if p999 > 1e-6:
        out = np.clip((norm_grad / p999) * 255.0, 0, 255).astype(np.uint8)
    else:
        out = np.zeros_like(gray, dtype=np.uint8)

    return out


def preprocess_representation(image: np.ndarray, rep_type: str) -> np.ndarray:
    """Dispatch preprocessing to the requested experimental representation."""
    if rep_type == "baseline_clahe":
        return to_baseline_clahe(image)
    elif rep_type == "histogram_normalized":
        return to_histogram_normalized(image)
    elif rep_type == "gradient_magnitude":
        return to_gradient_magnitude(image)
    elif rep_type == "local_gradient_normalized":
        return to_local_gradient_normalized(image)
    else:
        raise ValueError(
            f"Unknown representation '{rep_type}'. Must be one of {MULTIMODAL_REPRESENTATIONS}."
        )


def generate_multimodal_representations(image: np.ndarray) -> Dict[str, np.ndarray]:
    """Generate all four experimental representations for an input lunar image.

    Returns dictionary mapping representation name to matching-ready uint8 grayscale.
    """
    return {
        "baseline_clahe": to_baseline_clahe(image),
        "histogram_normalized": to_histogram_normalized(image),
        "gradient_magnitude": to_gradient_magnitude(image),
        "local_gradient_normalized": to_local_gradient_normalized(image),
    }


def compute_pair_condition_telemetry(
    source_img: np.ndarray,
    reference_img: np.ndarray,
) -> Dict[str, Any]:
    """Compute factual, descriptive pair-condition telemetry between two lunar images.

    Metrics:
    - source/reference intensity mean and std
    - histogram_distance: 256-bin normalized Bhattacharyya distance in [0, 1]
    - source/reference gradient mean and std
    - gradient_disagreement: composite gradient distribution disparity in [0, 1]
    - radiometric_gap_class: explainable classification ('LOW', 'MEDIUM', 'HIGH')

    IMPORTANT: These metrics are descriptive research telemetry only and must NOT
    alter production routing or thresholds.
    """
    s_gray = _ensure_uint8_grayscale(source_img, name="source")
    r_gray = _ensure_uint8_grayscale(reference_img, name="reference")

    # 1. Photometric intensity mean and standard deviation
    src_intensity_mean = round(float(np.mean(s_gray)), 2)
    src_intensity_std = round(float(np.std(s_gray)), 2)
    ref_intensity_mean = round(float(np.mean(r_gray)), 2)
    ref_intensity_std = round(float(np.std(r_gray)), 2)

    # 2. Normalized 256-bin Bhattacharyya histogram distance in [0, 1]
    hist_s = cv2.calcHist([s_gray], [0], None, [256], [0, 256])
    hist_r = cv2.calcHist([r_gray], [0], None, [256], [0, 256])
    cv2.normalize(hist_s, hist_s, norm_type=cv2.NORM_L1)
    cv2.normalize(hist_r, hist_r, norm_type=cv2.NORM_L1)
    # cv2.HISTCMP_BHATTACHARYYA yields values in [0, 1] for L1-normalized histograms
    raw_hist_dist = float(cv2.compareHist(hist_s, hist_r, cv2.HISTCMP_BHATTACHARYYA))
    histogram_distance = round(float(np.clip(raw_hist_dist, 0.0, 1.0)), 4)

    # 3. Spatial gradient statistics via Sobel
    gx_s = cv2.Sobel(s_gray, cv2.CV_32F, 1, 0, ksize=3)
    gy_s = cv2.Sobel(s_gray, cv2.CV_32F, 0, 1, ksize=3)
    mag_s = np.sqrt(gx_s**2 + gy_s**2)
    src_gradient_mean = round(float(np.mean(mag_s)), 2)
    src_gradient_std = round(float(np.std(mag_s)), 2)

    gx_r = cv2.Sobel(r_gray, cv2.CV_32F, 1, 0, ksize=3)
    gy_r = cv2.Sobel(r_gray, cv2.CV_32F, 0, 1, ksize=3)
    mag_r = np.sqrt(gx_r**2 + gy_r**2)
    ref_gradient_mean = round(float(np.mean(mag_r)), 2)
    ref_gradient_std = round(float(np.std(mag_r)), 2)

    # 4. Explainable gradient disagreement in [0, 1]
    # Combines normalized gradient histogram divergence and relative mean difference
    grad_u8_s = np.clip(mag_s, 0, 255).astype(np.uint8)
    grad_u8_r = np.clip(mag_r, 0, 255).astype(np.uint8)
    hist_g_s = cv2.calcHist([grad_u8_s], [0], None, [64], [0, 256])
    hist_g_r = cv2.calcHist([grad_u8_r], [0], None, [64], [0, 256])
    cv2.normalize(hist_g_s, hist_g_s, norm_type=cv2.NORM_L1)
    cv2.normalize(hist_g_r, hist_g_r, norm_type=cv2.NORM_L1)
    grad_hist_dist = float(cv2.compareHist(hist_g_s, hist_g_r, cv2.HISTCMP_BHATTACHARYYA))
    rel_grad_diff = abs(src_gradient_mean - ref_gradient_mean) / max(src_gradient_mean, ref_gradient_mean, 1.0)
    gradient_disagreement = round(float(np.clip(0.5 * grad_hist_dist + 0.5 * min(1.0, rel_grad_diff), 0.0, 1.0)), 4)

    # 5. Explainable radiometric gap classification (LOW / MEDIUM / HIGH)
    # Reflects overall radiometric divergence across intensity and gradient structure
    combined_divergence = 0.5 * histogram_distance + 0.5 * gradient_disagreement
    if histogram_distance < 0.25 and gradient_disagreement < 0.25:
        radiometric_gap_class = "LOW"
    elif histogram_distance >= 0.45 or gradient_disagreement >= 0.45 or combined_divergence >= 0.40:
        radiometric_gap_class = "HIGH"
    else:
        radiometric_gap_class = "MEDIUM"

    return {
        "source_intensity_mean": src_intensity_mean,
        "source_intensity_std": src_intensity_std,
        "reference_intensity_mean": ref_intensity_mean,
        "reference_intensity_std": ref_intensity_std,
        "histogram_distance": histogram_distance,
        "source_gradient_mean": src_gradient_mean,
        "source_gradient_std": src_gradient_std,
        "reference_gradient_mean": ref_gradient_mean,
        "reference_gradient_std": ref_gradient_std,
        "gradient_disagreement": gradient_disagreement,
        "radiometric_gap_class": radiometric_gap_class,
    }
