# Phase 23B.3 -- Geodetic Realization Comparison Report

**Generated:** 2026-09-24T07:36:30Z  
**Script:** `run_phase23b3_reference_provenance_audit.py`  

## Delivered CRS Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| CRS Name | PolarStereographic Moon / GCS_Moon / D_Moon | GeoAsciiParams (Tag 34737) |
| Datum | D_Moon (GeoAsciiParams label) | GeoAsciiParams |
| Radius | 1737400.0 m | GeoDoubleParams[5] (Tag 34736) |
| Geodetic Frame | NOT_EXPLICITLY_DOCUMENTED in GeoTIFF tags | Audit finding |
| MOON_ME_DE421 Link | NOT_VERIFIED -- D_Moon is compatible with multiple lunar geodetic realizations | Audit finding |

## Candidate Frame Comparison

| Candidate | Documented Frame | Radius | MOON_ME_DE421 Verified | Delivered Match | Classification |
|-----------|-----------------|--------|----------------------|----------------|----------------|
| CAND_B01 | IAU_MOON (selenocentric spheri | 1737400.0 m | INFERRED -- IAU2009 recom | COMPATIBLE | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B03 | MOON_ME_DE421 | 1737400.0 m | VERIFIED in LROC product  | COMPATIBLE | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B05 | MOON_ME_DE421 (modern products | 1737400.0 m | VERIFIED for modern USGS  | COMPATIBLE | `COMPATIBLE_BUT_UNVERIFIED` |
| CAND_B06 | UNKNOWN | 1737400.0 m | UNKNOWN -- not recorded i | UNKNOWN | `PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED` |

## Conclusion

The GeoAsciiParams 'D_Moon' datum label and radius 1737400.0 m are compatible with IAU_MOON, MOON_ME, and MOON_ME_DE421. However, none of these specific frame realizations is named in any delivered metadata. The geodetic realization remains UNKNOWN.

```
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
```

