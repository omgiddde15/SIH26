from pathlib import Path
import cv2

from adaptive_engine import (
    compute_pair_characteristics,
    classify_difficulty_profile,
    rule_based_router,
    AdaptiveConfig,
)


KAGGLE_ROOT = Path(
    r"C:\Users\Notebook\Notebook\Unlabeled_data"
)

A_PATH = KAGGLE_ROOT / "Images_PNG" / (
    "ch2_ohr_ncp_20251109T0909533595.png"
)

B_PATH = KAGGLE_ROOT / "Images_PNG" / (
    "ch2_ohr_ncp_20251109T1305444583.png"
)


source = cv2.imread(
    str(A_PATH),
    cv2.IMREAD_GRAYSCALE
)

reference = cv2.imread(
    str(B_PATH),
    cv2.IMREAD_GRAYSCALE
)

if source is None:
    raise RuntimeError(
        f"Could not load source image:\n{A_PATH}"
    )

if reference is None:
    raise RuntimeError(
        f"Could not load reference image:\n{B_PATH}"
    )


config = AdaptiveConfig()

pair_chars = compute_pair_characteristics(
    source,
    reference
)

profile = classify_difficulty_profile(
    pair_chars,
    config
)

decision = rule_based_router(
    profile,
    pair_chars,
    config
)


print("==============================================")
print("KAGGLE PAIR 01 — ADAPTIVE ROUTER")
print("==============================================")

print()
print("IMAGE SIZES")
print("-----------")
print("Source:", (source.shape[1], source.shape[0]))
print("Reference:", (reference.shape[1], reference.shape[0]))

print()
print("DIFFICULTY PROFILE")
print("------------------")
print(profile)

print()
print("ROUTING DECISION")
print("----------------")
print("Selected matcher:", decision["selected_matcher"])
print("Rule:", decision["rule_triggered"])

print()
print("Reasons")
print("-------")

for reason in decision["reasons"]:
    print("-", reason)
