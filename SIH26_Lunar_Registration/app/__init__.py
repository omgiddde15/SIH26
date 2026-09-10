"""
Lunar Image Registration Engine - App Package.
Exports core computer-vision functions for pure-CV consumers and research modules.
DO NOT import app.py here to prevent circular execution and Streamlit duplicate element errors.
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
