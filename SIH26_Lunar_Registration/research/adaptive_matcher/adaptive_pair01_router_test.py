from pathlib import Path
import cv2

from adaptive_engine import (
    compute_pair_characteristics,
    classify_difficulty_profile,
    rule_based_router,
    AdaptiveConfig,
)


ROOT = Path(__file__).resolve().parents[2]

A_PATH = (
    ROOT
    / "data"
    / "large_ch2"
    / "source_ch2_large.png"
)

B_PATH = (
    ROOT
    / "data"
    / "large_ch2"
    / "reference_ch2_large.png"
)


source = cv2.imread(
    str(A_PATH),
    cv2.IMREAD_GRAYSCALE
)

reference = cv2.imread(
    str(B_PATH),
    cv2.IMREAD_GRAYSCALE
)

if source is None or reference is None:
    raise RuntimeError(
        f"Could not load:\n{A_PATH}\n{B_PATH}"
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
print("PAIR 01 — ADAPTIVE ROUTER ONLY")
print("==============================================")

print()
print("SOURCE")
print("------")
print(pair_chars["source"])

print()
print("REFERENCE")
print("---------")
print(pair_chars["reference"])

print()
print("PAIR CHARACTERISTICS")
print("--------------------")
print(pair_chars)

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