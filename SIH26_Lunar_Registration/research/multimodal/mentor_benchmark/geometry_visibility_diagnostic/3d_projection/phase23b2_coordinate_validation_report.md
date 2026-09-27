# Phase 23B.2 -- Coordinate Validation & Reader Equivalence Report

**Generated:** 2026-09-24T07:05:04Z  
**Script:** `run_phase23b2_crs_reader_semantics.py`  

## 1. Summary of 36 Deterministic Point Validations

Across 9 deterministic points on each of the 4 reference rasters (36 points total):
- **Rasterio / GDAL affine vs Audited Phase 23A implementation:** Max diff = **`0.000000 m`** (exact to floating point limit).
- **PROJ Transformer vs Audited Phase 23A implementation:** Max diff = **`0.000000 m`** ($< 3 \times 10^{-11}\text{ m}$).
- **Round-trip inversion error:** **`0.00e+00 m`**.

## 2. Detailed Per-Pair Results (Sample)

### OHRC_PAIR_01 (Max diff: 1.500000e-08 m)

| Point | Pixel (col, row) | Rasterio Coords (E, N) m | Our Audited Coords (E, N) m | Delta m | Controlled 0 deg vs 1 deg disp m |
|---|---|---|---|---|---|
| UL_corner | (0, 0) | (-19184.5, -3605.5) | (-19184.5, -3605.5) | `0.000000` | 340.7 m |
| UR_corner | (5915, 0) | (10390.5, -3605.5) | (10390.5, -3605.5) | `0.000000` | 192.0 m |
| LL_corner | (0, 4231) | (-19184.5, -24760.5) | (-19184.5, -24760.5) | `0.000000` | 546.7 m |
| LR_corner | (5915, 4231) | (10390.5, -24760.5) | (10390.5, -24760.5) | `0.000000` | 468.7 m |
| Center | (2958, 2116) | (-4394.5, -14185.5) | (-4394.5, -14185.5) | `0.000000` | 259.2 m |
| Top_mid | (2958, 0) | (-4394.5, -3605.5) | (-4394.5, -3605.5) | `0.000000` | 99.2 m |
| Bottom_mid | (2958, 4231) | (-4394.5, -24760.5) | (-4394.5, -24760.5) | `0.000000` | 438.9 m |
| Left_mid | (0, 2116) | (-19184.5, -14185.5) | (-19184.5, -14185.5) | `0.000000` | 416.4 m |
| Right_mid | (5915, 2116) | (10390.5, -14185.5) | (10390.5, -14185.5) | `0.000000` | 306.9 m |

### OHRC_PAIR_02 (Max diff: 1.000000e-09 m)

| Point | Pixel (col, row) | Rasterio Coords (E, N) m | Our Audited Coords (E, N) m | Delta m | Controlled 0 deg vs 1 deg disp m |
|---|---|---|---|---|---|
| UL_corner | (0, 0) | (67340.5, 150044.5) | (67340.5, 150044.5) | `0.000000` | 2870.4 m |
| UR_corner | (2592, 0) | (80300.5, 150044.5) | (80300.5, 150044.5) | `0.000000` | 2970.2 m |
| LL_corner | (0, 6278) | (67340.5, 118654.5) | (67340.5, 118654.5) | `0.000000` | 2381.2 m |
| LR_corner | (2592, 6278) | (80300.5, 118654.5) | (80300.5, 118654.5) | `0.000000` | 2500.5 m |
| Center | (1296, 3139) | (73820.5, 134349.5) | (73820.5, 134349.5) | `0.000000` | 2675.5 m |
| Top_mid | (1296, 0) | (73820.5, 150044.5) | (73820.5, 150044.5) | `0.000000` | 2918.5 m |
| Bottom_mid | (1296, 6278) | (73820.5, 118654.5) | (73820.5, 118654.5) | `0.000000` | 2439.0 m |
| Left_mid | (0, 3139) | (67340.5, 134349.5) | (67340.5, 134349.5) | `0.000000` | 2622.9 m |
| Right_mid | (2592, 3139) | (80300.5, 134349.5) | (80300.5, 134349.5) | `0.000000` | 2731.7 m |

### OHRC_PAIR_03 (Max diff: 1.000000e-09 m)

| Point | Pixel (col, row) | Rasterio Coords (E, N) m | Our Audited Coords (E, N) m | Delta m | Controlled 0 deg vs 1 deg disp m |
|---|---|---|---|---|---|
| UL_corner | (0, 0) | (61480.5, 153129.5) | (61480.5, 153129.5) | `0.000000` | 2879.9 m |
| UR_corner | (2415, 0) | (73555.5, 153129.5) | (73555.5, 153129.5) | `0.000000` | 2964.9 m |
| LL_corner | (0, 6315) | (61480.5, 121554.5) | (61480.5, 121554.5) | `0.000000` | 2377.4 m |
| LR_corner | (2415, 6315) | (73555.5, 121554.5) | (73555.5, 121554.5) | `0.000000` | 2479.7 m |
| Center | (1208, 3158) | (67520.5, 137339.5) | (67520.5, 137339.5) | `0.000000` | 2671.0 m |
| Top_mid | (1208, 0) | (67520.5, 153129.5) | (67520.5, 153129.5) | `0.000000` | 2920.9 m |
| Bottom_mid | (1208, 6315) | (67520.5, 121554.5) | (67520.5, 121554.5) | `0.000000` | 2426.8 m |
| Left_mid | (0, 3158) | (61480.5, 137339.5) | (61480.5, 137339.5) | `0.000000` | 2626.2 m |
| Right_mid | (2415, 3158) | (73555.5, 137339.5) | (73555.5, 137339.5) | `0.000000` | 2719.1 m |

### OHRC_PAIR_04 (Max diff: 1.000000e-09 m)

| Point | Pixel (col, row) | Rasterio Coords (E, N) m | Our Audited Coords (E, N) m | Delta m | Controlled 0 deg vs 1 deg disp m |
|---|---|---|---|---|---|
| UL_corner | (0, 0) | (86685.5, 164949.5) | (86685.5, 164949.5) | `0.000000` | 3252.2 m |
| UR_corner | (3163, 0) | (102500.5, 164949.5) | (102500.5, 164949.5) | `0.000000` | 3389.4 m |
| LL_corner | (0, 6321) | (86685.5, 133344.5) | (86685.5, 133344.5) | `0.000000` | 2775.8 m |
| LR_corner | (3163, 6321) | (102500.5, 133344.5) | (102500.5, 133344.5) | `0.000000` | 2935.4 m |
| Center | (1582, 3161) | (94595.5, 149144.5) | (94595.5, 149144.5) | `0.000000` | 3082.5 m |
| Top_mid | (1582, 0) | (94595.5, 164949.5) | (94595.5, 164949.5) | `0.000000` | 3318.7 m |
| Bottom_mid | (1582, 6321) | (94595.5, 133344.5) | (94595.5, 133344.5) | `0.000000` | 2853.4 m |
| Left_mid | (0, 3161) | (86685.5, 149144.5) | (86685.5, 149144.5) | `0.000000` | 3010.8 m |
| Right_mid | (3163, 3161) | (102500.5, 149144.5) | (102500.5, 149144.5) | `0.000000` | 3158.5 m |

## 3. Characterization of the 0 deg vs 1 deg Shift

The controlled comparison confirms that a hypothetical $\lambda_0 = 1.0^\circ$ introduces a purely azimuthal displacement 
of $2,000 - 3,500\text{ m}$ at distances of $120 - 200\text{ km}$ from the pole. Because standard readers consume 
the file with $\lambda_0 = 0.0^\circ$, this displacement does NOT exist in the standard reader pipeline.

