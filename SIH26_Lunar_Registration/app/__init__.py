"""
Lunar Image Registration System - Core Package.
Provides pure computer-vision registration utilities decoupled from the Streamlit UI.
"""

from .registration_core import (
    _DEVICE,
    load_loftr_matcher,
    compute_matching_scale,
    preprocess_image,
    calculate_spatial_grid,
    split_spatially_balanced,
    run_independent_checkpoint_validation,
    register_images,
)

__all__ = [
    "_DEVICE",
    "load_loftr_matcher",
    "compute_matching_scale",
    "preprocess_image",
    "calculate_spatial_grid",
    "split_spatially_balanced",
    "run_independent_checkpoint_validation",
    "register_images",
]
