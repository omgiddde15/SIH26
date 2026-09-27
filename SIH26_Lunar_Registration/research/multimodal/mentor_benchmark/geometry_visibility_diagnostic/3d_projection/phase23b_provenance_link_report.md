# Phase 23B — Provenance Link Audit Report

**Generated:** 2026-09-24T05:37:49Z

## Provenance Items Searched

| # | Item | Result | Status |
|---|------|--------|--------|
| 1 | GeoTIFF TIFFTAG_SOFTWARE (tag 305) | ABSENT in all 4 pairs | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 2 | GeoTIFF TIFFTAG_DATETIME (tag 306) | ABSENT in all 4 pairs | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 3 | GeoTIFF TIFFTAG_IMAGEDESCRIPTION (tag 270) | ABSENT in all 4 pairs | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 4 | GeoTIFF TIFFTAG_ARTIST (tag 315) | ABSENT in all 4 pairs | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 5 | GeoTIFF GDAL_METADATA (tag 42112) | ABSENT in all 4 pairs | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 6 | PDS4 XML <ReferenceUsed> | 'System' in all 4 pairs — does not name the external reference product | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 7 | PDS4 XML <AutoLCP> block (orthorectification control points) | AutoLCP block present but contains only a StartTime; no GCP list or reference pr... | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 8 | PDS4 XML <SelenoTagging> block | SelenoTagging timestamps present (start/stop). No reference mosaic product ID wi... | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 9 | PDS4 XML processing log / provenance chain | No explicit processing log or full provenance chain embedded in the XML | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 10 | Bundle-adjustment / GCP metadata | No bundle-adjustment or GCP metadata found | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 11 | Map-generation software / version string | No software version string found in any file | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 12 | Original orthorectification DEM identification | Not recorded. DEM used for selenocentric projection is unknown. | **NOT_FOUND_IN_AUDITED_INPUTS** |
| 13 | GeoKeyDirectoryTag — ProjectedCSTypeGeoKey (3072) | 32767 (user-defined) — no EPSG code assigned | **FOUND_BUT_NON_IDENTIFYING** |
| 14 | GeoKeyDirectoryTag — GeographicTypeGeoKey (2048) | 32767 (user-defined) — no standard geographic CRS code | **FOUND_BUT_NON_IDENTIFYING** |
| 15 | GeoKeyDirectoryTag — GeogGeodeticDatumGeoKey (2050) | 32767 (user-defined) — datum coded as user-defined | **FOUND_BUT_NON_IDENTIFYING** |
| 16 | GeoKeyDirectoryTag — Key_2054 (angular units) | 9102 (Angular_Degree) — standard value, non-identifying | **FOUND_BUT_NON_IDENTIFYING** |
| 17 | GeoKeyDirectoryTag — ProjStraightVertPoleLong (3092) | 1.0 deg (non-standard; conventional value is 0.0 deg) | **FOUND_ANOMALOUS** |

## Summary

- **Items searched:** 17
- **NOT_FOUND_IN_AUDITED_INPUTS:** 12
- **FOUND_BUT_NON_IDENTIFYING:** 4
- **FOUND_ANOMALOUS:** 1

**Conclusion:** No provenance item positively identifies the upstream reference product or its geodetic realization.

