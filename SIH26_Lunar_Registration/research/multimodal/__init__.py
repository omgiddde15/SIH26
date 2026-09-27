"""
research/multimodal/__init__.py
================================
Package exports for LunarReg Multimodal Research Branch (Phases 1 & 2).
"""

from research.multimodal.multimodal_preprocess import (
    MULTIMODAL_REPRESENTATIONS,
    to_baseline_clahe,
    to_histogram_normalized,
    to_gradient_magnitude,
    to_local_gradient_normalized,
    preprocess_representation,
    generate_multimodal_representations,
    compute_pair_condition_telemetry,
)
from research.multimodal.multimodal_benchmark import (
    run_multimodal_benchmark,
)
from research.multimodal.scale_search import (
    ScaleSearchConfig,
    run_scale_search,
)
from research.multimodal.rift2_matcher import (
    run_rift2_matching,
)
from research.multimodal.rift2_benchmark import (
    run_rift2_benchmark,
    load_angle_pairs,
    run_angle_pairs_benchmark,
)
from research.multimodal.rift2_matching_sweep import (
    extract_rift2_features,
    match_descriptors_at_thresholds,
    run_rift2_matching_sweep,
    run_phase4_benchmark,
)
from research.multimodal.rift2_structural_fusion import (
    extract_rift2_and_structural_features,
    match_rift2_with_pair_indices,
    compute_structural_similarity_and_fusion,
    run_rift2_structural_fusion_sweep,
    run_phase5_benchmark,
)
from research.multimodal.mind_matcher import (
    MINDConfig,
    detect_mind_keypoints,
    compute_mind_descriptors,
    match_mind_descriptors,
    run_mind_matching,
)
from research.multimodal.mind_benchmark import (
    run_mind_benchmark,
)
from research.multimodal.ssc_matcher import (
    SSCConfig,
    detect_ssc_keypoints,
    compute_ssc_descriptors,
    match_ssc_descriptors,
    run_ssc_matching,
)
from research.multimodal.ssc_benchmark import (
    run_ssc_benchmark,
)
from research.multimodal.ssc_robustness import (
    apply_brightness,
    apply_contrast,
    apply_gamma,
    apply_gaussian_noise,
    apply_gaussian_blur,
    apply_synthetic_rotation,
    apply_perturbation,
    classify_robustness_status,
    run_ssc_robustness_trial,
)
from research.multimodal.phase8_robustness_benchmark import (
    run_phase8_robustness_benchmark,
)

__all__ = [
    "MULTIMODAL_REPRESENTATIONS",
    "to_baseline_clahe",
    "to_histogram_normalized",
    "to_gradient_magnitude",
    "to_local_gradient_normalized",
    "preprocess_representation",
    "generate_multimodal_representations",
    "compute_pair_condition_telemetry",
    "run_multimodal_benchmark",
    "ScaleSearchConfig",
    "run_scale_search",
    "run_rift2_matching",
    "run_rift2_benchmark",
    "load_angle_pairs",
    "run_angle_pairs_benchmark",
    "extract_rift2_features",
    "match_descriptors_at_thresholds",
    "run_rift2_matching_sweep",
    "run_phase4_benchmark",
    "extract_rift2_and_structural_features",
    "match_rift2_with_pair_indices",
    "compute_structural_similarity_and_fusion",
    "run_rift2_structural_fusion_sweep",
    "run_phase5_benchmark",
    "MINDConfig",
    "detect_mind_keypoints",
    "compute_mind_descriptors",
    "match_mind_descriptors",
    "run_mind_matching",
    "run_mind_benchmark",
    "SSCConfig",
    "detect_ssc_keypoints",
    "compute_ssc_descriptors",
    "match_ssc_descriptors",
    "run_ssc_matching",
    "run_ssc_benchmark",
    "apply_brightness",
    "apply_contrast",
    "apply_gamma",
    "apply_gaussian_noise",
    "apply_gaussian_blur",
    "apply_synthetic_rotation",
    "apply_perturbation",
    "classify_robustness_status",
    "run_ssc_robustness_trial",
    "run_phase8_robustness_benchmark",
]

