"""
Thin Phase 10 benchmark entry point.

Run from the LunarReg project root:
py -3.13 -m research.multimodal.phase10_diagnostic_benchmark --iirs-source ... --ohrc-reference ...
"""
from research.multimodal.phase10_detector_descriptor_diagnostic import main

if __name__ == "__main__":
    main()
