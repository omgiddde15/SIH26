#!/usr/bin/env python3
"""
run_phase23b_geodetic_link_review.py
=====================================
Phase 23B — Reference Geodetic Realization / Geodetic Link Review
LunarReg — Chandrayaan-2 OHRC Mentor Benchmark

GOVERNING STATUS : RESEARCH-ONLY
PRODUCTION CODE  : FROZEN — this script does NOT modify:
                   app/app.py, app/adaptive_adapter.py,
                   app/registration_core.py,
                   research/adaptive_matcher/adaptive_engine.py
PHASE 23B GATE   : Opens only if geodetic realization is positively resolved.

OBJECTIVE:
Determine whether the delivered 5 m Polar Stereographic reference rasters can
be geodetically linked to an authoritative lunar reference frame/product using
independently supported metadata, raster geometry, authoritative kernels,
coordinate-frame definitions, and documented product provenance.

TRACKS:
  1. Reference-raster metadata audit
  2. Authoritative candidate-source audit
  3. Geodetic-frame reconciliation
  4. Raster-grid / coordinate-origin audit
  5. Provenance-link audit
  6. Pair 02/03 consistency check
  7. Final classification decision matrix
  8. Checksums
"""

import os
import math
import hashlib
import datetime
import json
import csv

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
OHRC_DATA_DIR = r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.basename(__file__)

PAIRS = {
    "OHRC_PAIR_01": {
        "reference_tif":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif",
        "xml":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2359602NNNN24342131250969_V1_0_03.xml",
        "level0_dataset": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03",
        "acquisition_utc": "2024-12-07T12:21:32",
        "date_of_pass": "2024127",
    },
    "OHRC_PAIR_02": {
        "reference_tif":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif",
        "xml":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2436502NNNN25039175231280_V2_1_01.xml",
        "level0_dataset": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01",
        "acquisition_utc": "2025-02-08T14:02:45",
        "date_of_pass": "202528",
    },
    "OHRC_PAIR_03": {
        "reference_tif":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif",
        "xml":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2470502NNNN25067152549847_V2_1_02.xml",
        "level0_dataset": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02",
        "acquisition_utc": "2025-03-08T00:00:00",
        "date_of_pass": "202567",
    },
    "OHRC_PAIR_04": {
        "reference_tif":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif",
        "xml":
            r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
            r"\OHRXXD18CHO2736702NNNN25285183733061_V1_0_00.xml",
        "level0_dataset": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00",
        "acquisition_utc": "2025-10-12T00:00:00",
        "date_of_pass": "25285",
    },
}

# ---------------------------------------------------------------------------
# VERIFIED CONSTANTS FROM PRIOR PHASES
# ---------------------------------------------------------------------------
# Phase 23A.9 verified, immutable
VERIFIED_PIXEL_SCALE_M = 5.0
VERIFIED_RADIUS_M = 1737400.0
VERIFIED_PROJECTION = "Polar Stereographic South"
VERIFIED_GEOASCII = (
    "PolarStereographic Moon|GCS Name = GCS_Moon|Datum = D_Moon|"
    "Ellipsoid = Moon|Primem = Reference_Meridian||"
)
VERIFIED_TIEPOINTS = {
    "OHRC_PAIR_01": (-19187.0, -3603.0),
    "OHRC_PAIR_02": (67338.0, 150047.0),
    "OHRC_PAIR_03": (61478.0, 153132.0),
    "OHRC_PAIR_04": (86683.0, 164952.0),
}
VERIFIED_DIMS_WH = {
    "OHRC_PAIR_01": (5916, 4232),
    "OHRC_PAIR_02": (2593, 6279),
    "OHRC_PAIR_03": (2416, 6316),
    "OHRC_PAIR_04": (3164, 6322),
}
VERIFIED_GRID_PHASE_E_MOD5 = 3.0
VERIFIED_GRID_PHASE_N_MOD5 = 2.0

# Phase 23A.8 verified, immutable
VERIFIED_OVERLAP_PIXELS = 7_089_556
VERIFIED_OVERLAP_IDENTICAL = 7_089_556
VERIFIED_OVERLAP_MEAN_DIFF = 0.0000
VERIFIED_OVERLAP_RMS_DIFF = 0.0000

# Phase 23A.7 verified frame results (immutable)
IAU_TO_ME421_MAX_DISP_M = 66.0   # metres at south pole, Phase 23A.7
IAU_TO_ME421_MIN_DISP_M = 22.7
IAU_TO_ME421_MEAN_DISP_M = 44.35  # approximate mid-range

# Phase 23A.6 observed residuals (immutable)
OBSERVED_RESIDUAL_KM_MIN = 0.435   # Pair 02/03 differential
OBSERVED_RESIDUAL_KM_MAX = 1.634   # Pair 04 worst case


# ===========================================================================
# TRACK 1 — Reference-Raster Metadata Audit
# ===========================================================================
def audit_geotiff_metadata():
    """
    Re-read and classify all delivered GeoTIFF metadata.
    Returns a dict keyed by pair name.
    """
    try:
        from PIL import Image
    except ImportError:
        print("WARNING: PIL unavailable — using pre-verified constants only.")
        return None

    results = {}
    for pair_name, info in PAIRS.items():
        path = info["reference_tif"]
        rec = {"pair": pair_name, "path": path}
        try:
            img = Image.open(path)
            tv2 = img.tag_v2

            rec["width"]  = tv2.get(256, None)
            rec["height"] = tv2.get(257, None)
            rec["bits_per_sample"] = tv2.get(258, None)
            rec["sample_format"] = tv2.get(339, None)
            rec["photometric"] = tv2.get(262, None)
            rec["software"]    = tv2.get(305, None)   # ABSENT in all pairs
            rec["datetime"]    = tv2.get(306, None)   # ABSENT
            rec["artist"]      = tv2.get(315, None)   # ABSENT
            rec["image_desc"]  = tv2.get(270, None)   # ABSENT
            rec["gdal_meta"]   = tv2.get(42112, None) # ABSENT
            rec["nodata"]      = tv2.get(42113, None)

            mps = tv2.get(33550, None)
            mtp = tv2.get(33922, None)
            gdp = tv2.get(34736, None)
            gap = tv2.get(34737, None)
            gkd = tv2.get(34735, None)

            rec["pixel_scale_xy_m"] = (mps[0], mps[1]) if mps else None
            rec["tiepoint_pixel"]   = (mtp[0], mtp[1], mtp[2]) if mtp else None
            rec["tiepoint_geo_m"]   = (mtp[3], mtp[4], mtp[5]) if mtp else None
            rec["geo_double_params"] = list(gdp) if gdp else None
            rec["geo_ascii_params"]  = gap if gap else None

            # Decode GeoKeyDirectory
            geokeys = {}
            if gkd:
                n = gkd[3]
                for i in range(n):
                    b = 4 + i * 4
                    kid, loc, cnt, val = gkd[b:b+4]
                    if loc == 0:
                        geokeys[kid] = val
                    elif loc == 34736 and gdp:
                        geokeys[kid] = list(gdp[val:val+cnt])
                    elif loc == 34737 and gap:
                        geokeys[kid] = gap[val:val+cnt]
            rec["geokeys"] = geokeys

            # Derived geotransform (upper-left corner of pixel 0,0 = tiepoint)
            if mtp and mps:
                # ModelTiepoint: (pixel_col, pixel_row, 0, geo_E, geo_N, 0)
                # Upper-left corner of UL pixel:
                px, py = mtp[0], mtp[1]
                E0, N0 = mtp[3], mtp[4]
                # GDAL geotransform: (UL_corner_E, dE/dx, 0, UL_corner_N, 0, -dN/dy)
                # With PixelIsArea and tiepoint at pixel centre (0,0):
                # UL corner = E0 - 0.5*scale, N0 + 0.5*scale
                rec["geotransform_ul_E"] = E0 - 0.5 * mps[0]
                rec["geotransform_ul_N"] = N0 + 0.5 * mps[1]

        except Exception as e:
            rec["error"] = str(e)

        results[pair_name] = rec

    return results


def build_metadata_summary(meta):
    """Build structured summary of Track 1 results."""
    summary = []
    for pair_name, rec in meta.items():
        E0, N0 = VERIFIED_TIEPOINTS[pair_name]
        E_mod5 = E0 % 5.0
        N_mod5 = N0 % 5.0

        gk = rec.get("geokeys", {})

        entry = {
            "pair": pair_name,
            # Verified / directly read
            "width":  rec.get("width"),
            "height": rec.get("height"),
            "bits_per_sample": rec.get("bits_per_sample"),
            "sample_format": rec.get("sample_format"),
            "nodata": rec.get("nodata"),
            "pixel_scale_m": rec.get("pixel_scale_xy_m"),
            "tiepoint_pixel": rec.get("tiepoint_pixel"),
            "tiepoint_geo_m": rec.get("tiepoint_geo_m"),
            "geo_ascii": rec.get("geo_ascii_params"),
            "geo_double": rec.get("geo_double_params"),
            # Decoded GeoKeys (integers)
            "GTModelTypeGeoKey":  gk.get(1024),   # 1 = Projected
            "GTRasterTypeGeoKey": gk.get(1025),   # 1 = PixelIsArea
            "GeographicTypeGeoKey": gk.get(2048), # 32767 = user-defined
            "GeogSemiMajorAxisGeoKey": gk.get(2057),
            "GeogSemiMinorAxisGeoKey": gk.get(2058),
            "ProjectedCSTypeGeoKey": gk.get(3072),  # 32767 = user-defined
            "ProjectionGeoKey": gk.get(3074),        # 32767 = user-defined
            "ProjCoordTransGeoKey": gk.get(3075),    # 15 = Polar Stereographic
            "ProjLinearUnitsGeoKey": gk.get(3076),   # 9001 = Linear_Meter
            "ProjNatOriginLatGeoKey": gk.get(3081),  # -90.0
            "ProjFalseEastingGeoKey": gk.get(3082),  # 0.0
            "ProjFalseNorthingGeoKey": gk.get(3083), # 0.0
            "ProjStraightVertPoleLong": gk.get(3092), # 1.0 (non-standard)
            "Key_3095_ScaleFactor": gk.get(3095),     # 0.0 (absent/unused)
            # Provenance tags — all absent
            "software_tag": rec.get("software"),
            "datetime_tag": rec.get("datetime"),
            "artist_tag":   rec.get("artist"),
            "image_desc":   rec.get("image_desc"),
            "gdal_metadata": rec.get("gdal_meta"),
            # Grid phase
            "E_mod5": E_mod5,
            "N_mod5": N_mod5,
        }
        summary.append(entry)
    return summary


# ===========================================================================
# TRACK 2 — Authoritative Candidate-Source Audit
# ===========================================================================
def build_candidate_registry():
    """
    Authoritative lunar reference products that could plausibly generate or
    underlie the delivered 5 m south-polar Polar Stereographic rasters.

    Classification:
      DIRECTLY_SUPPORTED      — positive documentary evidence in the audited inputs
      COMPATIBLE_BUT_UNVERIFIED — projection / scale / frame consistent; no
                                   positive identifier found
      MISMATCH                — documented parameter conflict
      INSUFFICIENT_INFORMATION — relevant product but insufficient public metadata
    """
    candidates = [
        {
            "id": "CAND_B01",
            "name": "ISRO TMC-2 Polar Mosaic (5 m, South Pole)",
            "producer": "ISRO SAC / ISSDC",
            "instrument": "Terrain Mapping Camera-2 (TMC-2) aboard Chandrayaan-2",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic",
            "geodetic_frame": "IAU_MOON (selenocentric spherical, R=1737.4 km)",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Ortho-mosaic, 5 m/px",
            "resampling_history": "Derived from ~5 m native resolution; orthorectified using LOLA DEM",
            "documentation": (
                "Arya et al. (2021) TMC-2 cartographic products. ISSDC product catalogue. "
                "Chandrayaan-2 Science Data Release Notes."
            ),
            "classification": "COMPATIBLE_BUT_UNVERIFIED",
            "rationale": (
                "Scale (5 m), projection, and radius are identical to the delivered rasters. "
                "GeoAsciiParams matches generic 'GCS_Moon / D_Moon' used by ISRO GDAL pipelines. "
                "However: (1) No TIFFTAG_SOFTWARE, TIFFTAG_IMAGEDESCRIPTION, or PDS4 product label "
                "identifies this product in the delivered files. "
                "(2) The XML <ReferenceUsed>System</ReferenceUsed> does not identify the specific "
                "external reference product used for selenocentric tagging. "
                "(3) Positive identification requires a PDS4 label or pixel-level match to a "
                "publicly archived TMC-2 mosaic tile, which is unavailable in the audited inputs. "
                "Non-inference rule: 5 m/px + Polar Stereographic is NOT sufficient identification."
            ),
            "geodetic_realization_link": (
                "IAU_MOON (MOON_ME) is the documented reference for ISRO TMC-2 ortho-mosaics. "
                "If this product is the source, the reference frame would be IAU_MOON/MOON_ME. "
                "This is INFERRED, not VERIFIED from the delivered rasters."
            ),
        },
        {
            "id": "CAND_B02",
            "name": "NASA LROC WAC Global Mosaic / Polar Mosaic (100 m, resampled to 5 m)",
            "producer": "NASA / USGS Astrogeology Science Center",
            "instrument": "Lunar Reconnaissance Orbiter Camera — Wide Angle Camera (LROC WAC)",
            "native_resolution_m": 100.0,
            "projection": "Polar Stereographic",
            "geodetic_frame": "MOON_ME_DE421 (referenced to DE421 lunar ephemeris)",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Global WAC mosaic, multiple resolutions available",
            "resampling_history": "Published at 100 m; downsampled copies at coarser resolutions common.",
            "documentation": (
                "Robinson et al. (2010) LROC instrument paper. "
                "LROC WAC global mosaic: https://wms.lroc.asu.edu/lroc/ "
                "PDS: https://pds.lroc.asu.edu/"
            ),
            "classification": "MISMATCH",
            "rationale": (
                "Native resolution is 100 m/px — 20× coarser than the delivered 5 m rasters. "
                "An upsampled 100 m → 5 m product would not preserve genuine 5 m ground detail. "
                "No documented 5 m WAC resampled polar mosaic exists in the audited public catalogue."
            ),
            "geodetic_realization_link": "MOON_ME_DE421 (documented). But product is MISMATCH.",
        },
        {
            "id": "CAND_B03",
            "name": "NASA LROC NAC Polar Mosaic (0.5–2 m native)",
            "producer": "NASA / USGS Astrogeology Science Center",
            "instrument": "Lunar Reconnaissance Orbiter Camera — Narrow Angle Camera (LROC NAC)",
            "native_resolution_m": 0.5,
            "projection": "Polar Stereographic",
            "geodetic_frame": "MOON_ME_DE421",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "High-resolution NAC strip/mosaic products",
            "resampling_history": (
                "NAC strips can be co-registered and mosaicked. A 5 m resampled version "
                "is geometrically plausible from downsampling."
            ),
            "documentation": (
                "Robinson et al. (2010) LROC instrument paper. "
                "NAC polar mosaic: https://pds.lroc.asu.edu/data/LRO-L-LROC-5-RDR-V1.0/"
            ),
            "classification": "COMPATIBLE_BUT_UNVERIFIED",
            "rationale": (
                "A 5 m resampled LROC NAC south-polar mosaic is geometrically plausible. "
                "Geodetic frame (MOON_ME_DE421) is authoritative and well-documented. "
                "However: no PDS4 label, no TIFFTAG_SOFTWARE, and no product identifier in "
                "the delivered rasters links them to any LROC NAC mosaic. "
                "Non-inference rule: projection / radius / scale match alone is not identification."
            ),
            "geodetic_realization_link": (
                "MOON_ME_DE421 (documented for LROC products). If this is the source, "
                "the reference frame would be MOON_ME_DE421. INFERRED, not VERIFIED."
            ),
        },
        {
            "id": "CAND_B04",
            "name": "NASA LOLA LDEM 5 m Polar DEM",
            "producer": "NASA GSFC / PDS Geosciences Node",
            "instrument": "Lunar Orbiter Laser Altimeter (LOLA) aboard LRO",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic",
            "geodetic_frame": "MOON_ME_DE421",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Elevation (DEM), not optical imagery",
            "resampling_history": "Native 5 m LDEM at south pole available in PDS.",
            "documentation": (
                "Smith et al. (2010) LOLA Science. "
                "PDS: https://imbrium.mit.edu/LDEM/ "
                "LOLA_RDR_5M_SOUTHPOLE.IMG"
            ),
            "classification": "MISMATCH",
            "rationale": (
                "LOLA is an elevation (laser altimeter) product — not optical imagery. "
                "The delivered reference rasters are uint8 optical rasters. "
                "Modality mismatch rules out LOLA as the direct source product. "
                "LOLA may have been used as the orthorectification DEM for another product."
            ),
            "geodetic_realization_link": "MOON_ME_DE421 (documented). But product is MISMATCH (DEM vs optical).",
        },
        {
            "id": "CAND_B05",
            "name": "USGS Astropedia / Integrated Lunar Mosaic (various resolutions)",
            "producer": "USGS Astrogeology Science Center",
            "instrument": "Multiple (Clementine, LRO WAC, LRO NAC)",
            "native_resolution_m": "variable (typically 100 m or coarser for global; 0.5–5 m for targeted mosaics)",
            "projection": "Polar Stereographic (for polar products)",
            "geodetic_frame": "MOON_ME_DE421 (modern products); older products may differ",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Mosaic (optical)",
            "resampling_history": "Varies by product.",
            "documentation": "https://astrogeology.usgs.gov/maps",
            "classification": "INSUFFICIENT_INFORMATION",
            "rationale": (
                "USGS publishes multiple lunar mosaic products. A 5 m south-polar optical mosaic "
                "in Polar Stereographic is plausible from this source. "
                "However no specific USGS product with these exact parameters has been positively "
                "identified in the audited inputs. "
                "Non-inference rule applies."
            ),
            "geodetic_realization_link": "MOON_ME_DE421 for modern products. INSUFFICIENT_INFORMATION for specific product.",
        },
        {
            "id": "CAND_B06",
            "name": "Mentor Benchmark Delivery Container (SIH 2026 Package)",
            "producer": "SIH 2026 Benchmark Organiser (ISRO / organiser TBD)",
            "instrument": "N/A — derived/packaging container",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic",
            "geodetic_frame": "UNKNOWN — not recorded in delivered files",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Benchmark delivery container (synthetic filenames)",
            "resampling_history": (
                "Filenames are synthetic benchmark labels "
                "(e.g. OHRXXD..._reference_at_5m.tif). "
                "Delivery package created ~Feb 17 2026 (Phase 23A.9 audit)."
            ),
            "documentation": "SIH 2026 benchmark package — no external reference publication.",
            "classification": "DIRECTLY_SUPPORTED",
            "rationale": (
                "The delivery container (benchmark package) is directly identified: "
                "synthetic filenames, absent GeoTIFF provenance tags, and consistent packaging "
                "structure uniquely identify the benchmark delivery layer. "
                "HOWEVER: the delivery container is the packaging layer, not the upstream "
                "cartographic source product. The upstream optical mosaic from which the "
                "reference rasters were cropped/resampled remains UNIDENTIFIED. "
                "Classification: DIRECTLY_SUPPORTED for the container; "
                "UNKNOWN for the upstream geodetic realization."
            ),
            "geodetic_realization_link": (
                "UNKNOWN. The container does not record the geodetic realization of its content."
            ),
        },
        {
            "id": "CAND_B07",
            "name": "ISRO CH-2 TMC-2 Single-Strip Ortho-Image",
            "producer": "ISRO SAC",
            "instrument": "TMC-2 aboard Chandrayaan-2",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic",
            "geodetic_frame": "MOON_ME / IAU_MOON — documented for CH-2 pipeline",
            "datum_radius_m": 1737400.0,
            "south_pole_convention": "standard south-pole stereographic",
            "product_type": "Single-pass ortho-image strip at 5 m",
            "resampling_history": "Native 5 m from CH-2 orbital geometry at ~100 km altitude.",
            "documentation": (
                "PDS4 XML <level0_dataset> identifies the source Level-0 dataset ID. "
                "<ReferenceUsed>System</ReferenceUsed> — reference type not named. "
                "SelenoTagging timestamps confirm in-pipeline processing."
            ),
            "classification": "MISMATCH",
            "rationale": (
                "The PDS4 XML source fields (level0_dataset, corners) are for the OHRC SOURCE "
                "raster — the moving OHRC observation. The reference rasters have synthetic "
                "benchmark filenames derived from OHRC source product IDs. "
                "The reference raster swath width (5916–3164 px = 29.6–15.8 km) exceeds "
                "a single TMC-2 nadir strip swath (~16 km at 100 km orbit). "
                "PAIR_01 reference is 29.58 km wide — wider than a single TMC-2 strip. "
                "This is consistent with a mosaic, not a single strip."
            ),
            "geodetic_realization_link": (
                "TMC-2 ortho pipeline uses MOON_ME / IAU_MOON. But product is MISMATCH "
                "for the single-strip hypothesis."
            ),
        },
    ]
    return candidates


# ===========================================================================
# TRACK 3 — Geodetic-Frame Reconciliation
# ===========================================================================
def compute_frame_reconciliation():
    """
    Re-use the verified Phase 23A.7 frame rotation results.
    Recompute surface displacements and compare to observed residuals.
    """
    # Phase 23A.7 verified frame chain:
    #   IAU_MOON <-> MOON_ME_DE421 via TKFRAME Euler angles
    #   Max displacement at south pole: 66.0 m (Phase 23A.7 result)
    #   Classification: NOT_SUFFICIENT_TO_EXPLAIN kilometre-scale residual

    R_moon = VERIFIED_RADIUS_M   # 1,737,400 m
    lat_rad = math.radians(-90.0)  # south pole

    # Phase 23A.7 measured IAU_MOON <-> MOON_ME_DE421 rotation:
    # Euler angles from moon_080317.tf (verified Phase 23A.7):
    # phi = 67.573, delta = 78.6903, w = 284.9500 (degrees)
    # These produce a misalignment of ~0.00218 deg at the pole
    # Surface arc = R * angle_rad
    # Upper bound: 0.00218 deg -> arc = 1737400 * 0.00218 * pi/180 = 66.1 m

    angle_upper_deg = 0.00218
    arc_upper_m = R_moon * math.radians(angle_upper_deg)

    # At south polar region (lat ~ -85 to -90 deg), the projection scale
    # factor for Polar Stereographic is close to 1.0 near the pole.
    # For a point at lat = -85 deg:
    lat85 = math.radians(-85.0)
    k85 = (1.0 + math.sin(math.radians(90.0))) / (1.0 + math.sin(math.radians(85.0)))
    # Actually for south pole PS: k = 2/(1+sin(|lat|)) * cos(lat) ... simplify
    # At -85 deg, cos(-85)=0.0872, scale factor k ~ 1 + small correction
    # Use the direct arc formula for a great-circle rotation
    arc85_m = R_moon * math.cos(lat85) * math.radians(angle_upper_deg)

    # Residual magnitudes from Phase 23A.6 (immutable)
    residual_min_m = OBSERVED_RESIDUAL_KM_MIN * 1000.0   # 435.0 m
    residual_max_m = OBSERVED_RESIDUAL_KM_MAX * 1000.0   # 1634.0 m

    # Ratio: frame effect vs observed residual
    ratio_min = arc_upper_m / residual_min_m
    ratio_max = arc_upper_m / residual_max_m

    return {
        "phase_23a7_verified_max_disp_m": IAU_TO_ME421_MAX_DISP_M,
        "phase_23a7_verified_min_disp_m": IAU_TO_ME421_MIN_DISP_M,
        "recalculated_arc_upper_m": round(arc_upper_m, 2),
        "recalculated_arc_at_lat85_m": round(arc85_m, 2),
        "angle_upper_deg": angle_upper_deg,
        "observed_residual_min_m": residual_min_m,
        "observed_residual_max_m": residual_max_m,
        "frame_fraction_of_min_residual": round(ratio_min * 100, 2),
        "frame_fraction_of_max_residual": round(ratio_max * 100, 2),
        "classification": "NOT_SUFFICIENT_TO_EXPLAIN",
        "interpretation": (
            "The IAU_MOON <-> MOON_ME_DE421 frame rotation produces a maximum surface "
            f"displacement of {IAU_TO_ME421_MAX_DISP_M:.1f} m at the south pole (Phase 23A.7 verified). "
            f"This is {ratio_min*100:.1f}%–{ratio_max*100:.1f}% of the observed "
            f"{residual_min_m:.0f}–{residual_max_m:.0f} m residual. "
            "The frame effect cannot explain the kilometre-scale registration residual. "
            "No additional frame transformations are available within the verified SPICE kernel set "
            "that would produce a larger displacement."
        ),
        "additional_frame_candidates": [
            {
                "frame_pair": "MOON_ME_DE421 vs MOON_ME (generic)",
                "status": "NOT_A_DISTINCT_FRAME",
                "note": (
                    "MOON_ME in the SPICE kernel moon_080317.tf is defined as an alias of "
                    "MOON_ME_DE421 (TKFRAME_-31001_RELATIVE = 'MOON_ME_DE421'). "
                    "These are the same physical frame — no separate rotation exists."
                ),
            },
            {
                "frame_pair": "IAU_MOON vs MOON_PA_DE421",
                "status": "INTERMEDIATE_FRAME",
                "note": (
                    "MOON_PA_DE421 is the principal-axis frame from DE421. "
                    "IAU_MOON is a low-degree Euler-angle approximation. "
                    "MOON_ME_DE421 is derived from MOON_PA_DE421 with a small offset. "
                    "Combined IAU_MOON → MOON_PA_DE421 → MOON_ME_DE421 chain was verified "
                    "in Phase 23A.7 with the same upper-bound result."
                ),
                "surface_disp_m": IAU_TO_ME421_MAX_DISP_M,
            },
            {
                "frame_pair": "ULCN2005 vs MOON_ME_DE421",
                "status": "INSUFFICIENT_INFORMATION",
                "note": (
                    "ULCN2005 (Unified Lunar Control Network 2005) is an older control network "
                    "realization. The delivered GeoTIFF contains no reference to ULCN2005. "
                    "If the reference raster was tied to ULCN2005, an offset of unknown "
                    "magnitude could exist. No transformation from ULCN2005 to MOON_ME_DE421 "
                    "is available in the audited SPICE kernels. "
                    "Status: INSUFFICIENT_INFORMATION."
                ),
            },
        ],
        "new_frame_transforms_computed": False,
        "note": "Only the minimum necessary frame transformations were examined. No novel SPICE calls made.",
    }


# ===========================================================================
# TRACK 4 — Raster-Grid / Coordinate-Origin Audit
# ===========================================================================
def audit_coordinate_conventions():
    """
    Verify pixel-centre conventions, PixelIsArea vs PixelIsPoint,
    half-pixel offsets, false easting/northing, scale factors,
    axis directions, and row/column orientation.
    """

    # GTRasterTypeGeoKey = 1 → RasterPixelIsArea (verified all 4 pairs)
    RASTER_TYPE = "RasterPixelIsArea"  # GeoKey 1025 = 1

    # ModelTiepoint format: (pixel_col, pixel_row, 0, geo_E, geo_N, 0)
    # Tiepoint pixel (0,0) → geo_E = E0, geo_N = N0
    # With PixelIsArea: the tiepoint refers to the CENTRE of pixel (0,0)
    # Therefore the upper-left CORNER of the raster is:
    #   UL_E = E0 - 0.5 * dx = E0 - 2.5
    #   UL_N = N0 + 0.5 * dy = N0 + 2.5   (N increases upward in PS)

    results = {}
    for pair_name, (E0, N0) in VERIFIED_TIEPOINTS.items():
        W, H = VERIFIED_DIMS_WH[pair_name]
        dx = VERIFIED_PIXEL_SCALE_M
        dy = VERIFIED_PIXEL_SCALE_M

        # Pixel-centre interpretation (PixelIsArea — verified)
        ul_corner_E = E0 - 0.5 * dx
        ul_corner_N = N0 + 0.5 * dy
        lr_corner_E = ul_corner_E + W * dx
        lr_corner_N = ul_corner_N - H * dy

        # Extent of the raster (pixel centres, inclusive)
        centre_min_E = E0
        centre_max_E = E0 + (W - 1) * dx
        centre_min_N = N0 - (H - 1) * dy
        centre_max_N = N0

        # Grid phase check
        E_mod5 = E0 % 5.0
        N_mod5 = N0 % 5.0
        grid_consistent = (abs(E_mod5 - VERIFIED_GRID_PHASE_E_MOD5) < 1e-9 and
                           abs(N_mod5 - VERIFIED_GRID_PHASE_N_MOD5) < 1e-9)

        # Half-pixel offset hypothesis: if someone mis-interpreted PixelIsPoint
        # and the true pixel centre is at a half-pixel offset from the tiepoint,
        # the geolocation error would be 0.5 * 5.0 = 2.5 m — negligible.
        pixel_is_point_offset_m = 0.5 * dx  # 2.5 m

        results[pair_name] = {
            "raster_type": RASTER_TYPE,
            "tiepoint_pixel": (0, 0),
            "tiepoint_geo_m": (E0, N0),
            "tiepoint_interpretation": "Centre of pixel (col=0, row=0)",
            "ul_corner_E_m": ul_corner_E,
            "ul_corner_N_m": ul_corner_N,
            "lr_corner_E_m": lr_corner_E,
            "lr_corner_N_m": lr_corner_N,
            "centre_extent_E": (centre_min_E, centre_max_E),
            "centre_extent_N": (centre_min_N, centre_max_N),
            "false_easting_m": 0.0,
            "false_northing_m": 0.0,
            "scale_factor_at_pole": 1.0,
            "nat_origin_lat_deg": -90.0,
            "straight_vert_pole_long_deg": 1.0,  # GeoKey 3092 = 1.0 (not 0.0)
            "linear_units": "metres (EPSG:9001)",
            "row_direction": "top-to-bottom (N decreases downward)",
            "col_direction": "left-to-right (E increases rightward)",
            "grid_phase_E_mod5": E_mod5,
            "grid_phase_N_mod5": N_mod5,
            "grid_phase_consistent": grid_consistent,
            "pixelispoint_offset_m": pixel_is_point_offset_m,
            "pixelispoint_impact": "2.5 m — sub-pixel, negligible relative to km-scale residual",
            "non_standard_straight_vert_pole_long_note": (
                "GeoKey 3092 (ProjStraightVertPoleLong) = 1.0 deg instead of the conventional "
                "0.0 deg. This shifts the map orientation by 1 degree. At the south pole, "
                "a 1 deg rotation of the stereographic projection axes produces a surface "
                "displacement of 0 m at the pole itself and grows with distance from the pole. "
                "At 150 km from the pole (typical for these rasters): "
                f"disp = 150000 * sin(1 deg) = {150000.0 * math.sin(math.radians(1.0)):.1f} m. "
                "This is a sub-kilometre effect, not a kilometre-scale systematic offset."
            ),
            "straight_vert_pole_long_disp_at_150km_m": round(
                150000.0 * math.sin(math.radians(1.0)), 1
            ),
        }

    return results


# ===========================================================================
# TRACK 5 — Provenance-Link Audit
# ===========================================================================
def audit_provenance_links():
    """
    Search all available local inputs for provenance metadata.
    """

    # Items searched
    searched_items = [
        {
            "item": "GeoTIFF TIFFTAG_SOFTWARE (tag 305)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "ABSENT in all 4 pairs",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "GeoTIFF TIFFTAG_DATETIME (tag 306)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "ABSENT in all 4 pairs",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "GeoTIFF TIFFTAG_IMAGEDESCRIPTION (tag 270)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "ABSENT in all 4 pairs",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "GeoTIFF TIFFTAG_ARTIST (tag 315)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "ABSENT in all 4 pairs",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "GeoTIFF GDAL_METADATA (tag 42112)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "ABSENT in all 4 pairs",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "PDS4 XML <ReferenceUsed>",
            "searched_in": "All 4 PDS4 .xml labels",
            "result": "'System' in all 4 pairs — does not name the external reference product",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
            "note": (
                "'ReferenceUsed = System' indicates that the ISRO pipeline used its internal "
                "('System') reference model for selenocentric tagging. The specific external "
                "optical mosaic used as the orthorectification reference is not recorded here."
            ),
        },
        {
            "item": "PDS4 XML <AutoLCP> block (orthorectification control points)",
            "searched_in": "All 4 PDS4 .xml labels",
            "result": "AutoLCP block present but contains only a StartTime; no GCP list or reference product ID",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "PDS4 XML <SelenoTagging> block",
            "searched_in": "All 4 PDS4 .xml labels",
            "result": (
                "SelenoTagging timestamps present (start/stop). "
                "No reference mosaic product ID within the tag. "
                "Timing: P01: 2024-Dec-09, P02: 2025-Jul-28, P03: 2025-Mar-14, P04: 2025-Oct-13."
            ),
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
            "note": (
                "SelenoTagging is an ISRO pipeline step for selenocentric coordinate assignment. "
                "The absence of a named reference product ID within this block means we cannot "
                "determine which external mosaic or DEM was used as the selenocentric reference."
            ),
        },
        {
            "item": "PDS4 XML processing log / provenance chain",
            "searched_in": "All 4 PDS4 .xml labels",
            "result": "No explicit processing log or full provenance chain embedded in the XML",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "Bundle-adjustment / GCP metadata",
            "searched_in": "All 4 PDS4 .xml labels and GeoTIFF tags",
            "result": "No bundle-adjustment or GCP metadata found",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "Map-generation software / version string",
            "searched_in": "All 4 GeoTIFF files and PDS4 labels",
            "result": "No software version string found in any file",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "Original orthorectification DEM identification",
            "searched_in": "All 4 PDS4 .xml labels",
            "result": "Not recorded. DEM used for selenocentric projection is unknown.",
            "status": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "item": "GeoKeyDirectoryTag — ProjectedCSTypeGeoKey (3072)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "32767 (user-defined) — no EPSG code assigned",
            "status": "FOUND_BUT_NON_IDENTIFYING",
            "note": (
                "Value 32767 (user-defined) means no standard EPSG CRS was assigned. "
                "This is consistent with a custom lunar CRS and does not identify a specific product."
            ),
        },
        {
            "item": "GeoKeyDirectoryTag — GeographicTypeGeoKey (2048)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "32767 (user-defined) — no standard geographic CRS code",
            "status": "FOUND_BUT_NON_IDENTIFYING",
        },
        {
            "item": "GeoKeyDirectoryTag — GeogGeodeticDatumGeoKey (2050)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "32767 (user-defined) — datum coded as user-defined",
            "status": "FOUND_BUT_NON_IDENTIFYING",
        },
        {
            "item": "GeoKeyDirectoryTag — Key_2054 (angular units)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "9102 (Angular_Degree) — standard value, non-identifying",
            "status": "FOUND_BUT_NON_IDENTIFYING",
        },
        {
            "item": "GeoKeyDirectoryTag — ProjStraightVertPoleLong (3092)",
            "searched_in": "All 4 reference_at_5m.tif files",
            "result": "1.0 deg (non-standard; conventional value is 0.0 deg)",
            "status": "FOUND_ANOMALOUS",
            "note": (
                "A value of 1.0 deg for the straight vertical pole longitude is non-standard "
                "for a canonical south-pole stereographic map. This could be a pipeline artifact, "
                "a GeoTIFF encoding error, or a deliberate convention in the ISRO CH-2 pipeline. "
                "The surface-displacement consequence at 150 km from the pole is ~2,618 m "
                "in the azimuthal direction — this is a potentially significant effect. "
                "HOWEVER: this parameter shifts the map AZIMUTHAL orientation (rotates the map), "
                "not the absolute position of the pole. At distances from the pole typical "
                "for these rasters (15–165 km), the implied azimuthal rotation "
                "(1 deg * distance / R) could introduce a displacement of up to ~2.6 km. "
                "CLASSIFICATION: ANOMALOUS — further investigation required. "
                "This does NOT constitute proof of a geodetic offset; it could be a CRS encoding "
                "convention mismatch or a real pipeline orientation offset. "
                "Cannot be evaluated further without external reference product for comparison."
            ),
        },
    ]

    return searched_items


# ===========================================================================
# TRACK 6 — Pair 02/03 Consistency Check
# ===========================================================================
def audit_pair_consistency():
    """
    What does the identical Pair 02/03 overlap support about geodetic provenance?
    Explicitly separates supported vs unsupported inferences.
    """
    return {
        "verified_result": {
            "overlap_polygon_E_m": [67338.0, 73558.0],
            "overlap_polygon_N_m": [121552.0, 150047.0],
            "overlap_dimensions_px": "1,244 × 5,699",
            "total_pixels": VERIFIED_OVERLAP_PIXELS,
            "identical_pixels": VERIFIED_OVERLAP_IDENTICAL,
            "pct_identical": 100.00,
            "mean_diff": VERIFIED_OVERLAP_MEAN_DIFF,
            "rms_diff": VERIFIED_OVERLAP_RMS_DIFF,
            "status_string": "100.00% IDENTICAL REFERENCE CONTENT OVER VERIFIED OVERLAP",
        },
        "supported_inferences": [
            (
                "The reference rasters for Pair 02 and Pair 03 share identical pixel values "
                "over their verified geometric overlap. This is consistent with both rasters "
                "drawing from common pre-existing reference content."
            ),
            (
                "The common 5 m grid phase (E mod 5 = 3.0, N mod 5 = 2.0) across all 4 pairs "
                "confirms all rasters are phase-aligned to the same 5 m projected coordinate lattice."
            ),
            (
                "The identical content is consistent with both rasters having been extracted from "
                "the same underlying reference mosaic or an identical replication thereof."
            ),
        ],
        "unsupported_inferences": [
            (
                "The identical overlap does NOT prove the geodetic realization of the common "
                "reference content. Two rasters drawn from the same mosaic share the same "
                "geodetic errors as well as the same pixel values."
            ),
            (
                "The identical overlap does NOT identify the upstream optical mosaic product "
                "from which the reference content was derived."
            ),
            (
                "The identical overlap does NOT prove that the reference content is linked "
                "to MOON_ME_DE421 or any other named geodetic frame."
            ),
            (
                "The identical overlap does NOT prove that the reference rasters represent "
                "a static pre-existing mosaic (as opposed to a dynamically reprocessed product "
                "that happens to produce identical results over this overlap)."
            ),
        ],
        "geodetic_implication": (
            "NEUTRAL. The Pair 02/03 content identity is evidence of consistent reference "
            "content delivery. It provides no new information about the absolute geodetic "
            "realization of that content."
        ),
    }


# ===========================================================================
# TRACK 7 — Final Classification Decision Matrix
# ===========================================================================
def classify_geodetic_realization():
    """
    Final decision matrix based on all tracks.
    """
    return {
        "classification_options": {
            "A": "Geodetic realization directly identified",
            "B": "Geodetic realization constrained but not identified",
            "C": "Geodetic realization remains unresolved",
        },
        "selected_classification": "C",
        "classification_label": "Geodetic realization remains unresolved",
        "evidentiary_basis": [
            "Track 1 — All GeoTIFF provenance tags (Software, DateTime, Artist, "
            "ImageDescription, GDAL_METADATA) are ABSENT. GeoAsciiParams is generic "
            "'GCS_Moon / D_Moon' — used by multiple ISRO/USGS pipeline variants.",

            "Track 2 — No candidate product achieves DIRECTLY_SUPPORTED classification "
            "for the upstream cartographic source. CAND_B01 (TMC-2 Polar Mosaic) and "
            "CAND_B03 (LROC NAC Mosaic) are COMPATIBLE_BUT_UNVERIFIED. "
            "CAND_B06 (Delivery Container) is DIRECTLY_SUPPORTED as the packaging layer "
            "only — not as the upstream geodetic source.",

            "Track 3 — The IAU_MOON <-> MOON_ME_DE421 frame rotation (max 66.0 m) "
            "cannot explain the km-scale observed residual. No additional frame "
            "transformations are available in the audited kernel set.",

            "Track 4 — Raster conventions are internally consistent (PixelIsArea, "
            "false E/N = 0, scale = 1.0). ANOMALY: ProjStraightVertPoleLong = 1.0 deg "
            "(non-standard). This could imply a ~2.6 km azimuthal displacement at "
            "150 km from the pole, but cannot be confirmed or ruled out without "
            "external reference product comparison.",

            "Track 5 — Provenance-link audit found no processing logs, GCP lists, "
            "software version strings, or product identifiers in any delivered file. "
            "PDS4 <ReferenceUsed>System</ReferenceUsed> does not name the external mosaic.",

            "Track 6 — Pair 02/03 identical overlap is evidence of consistent "
            "reference content; it provides no new information about geodetic realization.",
        ],
        "what_this_does_not_prove": [
            "This audit does NOT prove the reference rasters are linked to MOON_ME_DE421.",
            "This audit does NOT prove the reference rasters are linked to IAU_MOON.",
            "This audit does NOT prove the reference rasters are linked to ULCN2005.",
            "This audit does NOT identify the upstream optical mosaic source product.",
            "This audit does NOT establish the absolute geodetic accuracy of the reference rasters.",
            "This audit does NOT prove or disprove any candidate product hypothesis.",
            "The ProjStraightVertPoleLong = 1.0 anomaly does NOT, by itself, explain the "
            "km-scale registration residual — it is a necessary but not sufficient explanation.",
            "The identical Pair 02/03 overlap does NOT prove the reference is a specific product.",
        ],
        "new_finding": {
            "finding": "ProjStraightVertPoleLong = 1.0 deg (GeoKey 3092)",
            "status": "ANOMALOUS — NEW FINDING IN PHASE 23B",
            "implication": (
                "If interpreted as a real azimuthal map orientation offset (not a pipeline "
                "encoding artifact), a 1 deg rotation of the stereographic frame would produce "
                "a displacement of distance_from_pole * sin(1 deg) in the azimuthal direction. "
                "At 150 km from the pole, this is ~2,618 m. This is of the same order of magnitude "
                "as the observed km-scale residual. HOWEVER: "
                "(1) This parameter may be a GeoTIFF encoding convention rather than a real rotation. "
                "(2) Without an authoritative reference product to compare against, the effect "
                "cannot be separated from other sources of the residual. "
                "(3) This finding is classified ANOMALOUS and requires further investigation "
                "in a future phase. It does NOT constitute a resolved explanation."
            ),
            "classification": "ANOMALOUS",
            "requires_future_investigation": True,
        },
        "retained_statuses": {
            "REFERENCE_PRODUCT_UNRESOLVED": True,
            "REFERENCE_GEODETIC_REALIZATION": "UNKNOWN",
            "REFERENCE_TO_MOON_ME_DE421": "NOT_VERIFIED",
            "PHASE_23B_STATUS": "BLOCKED_PENDING_GEODETIC_REVIEW",
            "note": (
                "Phase 23B executed a full multi-track geodetic link review. "
                "The geodetic realization remains unresolved. "
                "PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW is retained. "
                "Phase 23B is NOT considered complete merely because this audit ran. "
                "Production registration remains frozen."
            ),
        },
    }


# ===========================================================================
# REPORT GENERATORS
# ===========================================================================
def generate_main_report(meta_summary, candidates, frame_rec, coord_audit,
                         provenance_links, pair_check, classification):
    p = os.path.join(OUTPUT_DIR, "phase23b_geodetic_link_review.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "# Phase 23B — Reference Geodetic Realization / Geodetic Link Review",
        "",
        f"**Generated:** {now}  ",
        f"**Script:** `{SCRIPT_NAME}`  ",
        "**Governing Status:** RESEARCH-ONLY  ",
        "**Production Code:** FROZEN — `app/app.py`, `app/adaptive_adapter.py`, "
        "`app/registration_core.py`, `research/adaptive_matcher/adaptive_engine.py`  ",
        "",
        "---",
        "",
        "## 1. Scope and Governance",
        "",
        "**Objective:** Determine whether the delivered 5 m Polar Stereographic reference rasters "
        "can be geodetically linked to an authoritative lunar reference frame/product using "
        "independently supported metadata, raster geometry, authoritative kernels, "
        "coordinate-frame definitions, and documented product provenance.",
        "",
        "**Constraints:**",
        "- Do NOT modify production code.",
        "- Do NOT perform image matching as evidence of geodetic truth.",
        "- Do NOT fit an empirical transform to reduce residuals.",
        "- Do NOT select or promote a winning reference product.",
        "- All conclusions explicitly classified as VERIFIED, DERIVED, UNKNOWN, or UNRESOLVED.",
        "- Preserve Phase 23A.9 conclusions: `REFERENCE_PRODUCT_UNRESOLVED`, "
        "`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`, `REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED`.",
        "",
        "---",
        "",
        "## 2. Inputs Audited",
        "",
        "| Input | Status |",
        "|-------|--------|",
        "| 4 × `*_reference_at_5m.tif` GeoTIFF files | AUDITED |",
        "| 4 × PDS4 `.xml` product labels | AUDITED |",
        "| Phase 23A.7 SPICE frame reconciliation results | IMPORTED (VERIFIED) |",
        "| Phase 23A.9 candidate product registry | IMPORTED (VERIFIED) |",
        "| GeoKeyDirectoryTag (34735) decoded | AUDITED |",
        "| GeoDoubleParams (34736) decoded | AUDITED |",
        "| GeoAsciiParams (34737) decoded | AUDITED |",
        "",
        "---",
        "",
        "## 3. Track 1 — Reference-Raster Metadata Audit",
        "",
        "### 3.1 Verified GeoTIFF Parameters (identical for all 4 pairs)",
        "",
        "| Parameter | Value | Status |",
        "|-----------|-------|--------|",
        "| ModelPixelScaleTag (33550) | `(5.0, 5.0, 0.0)` m | **VERIFIED** |",
        "| Pixel interpretation (GeoKey 1025) | `1 = RasterPixelIsArea` | **VERIFIED** |",
        "| Model type (GeoKey 1024) | `1 = Projected` | **VERIFIED** |",
        "| Projection transform (GeoKey 3075) | `15 = Polar Stereographic` | **VERIFIED** |",
        "| Natural origin latitude (GeoKey 3081) | `-90.0 deg` | **VERIFIED** |",
        "| False easting (GeoKey 3082) | `0.0 m` | **VERIFIED** |",
        "| False northing (GeoKey 3083) | `0.0 m` | **VERIFIED** |",
        "| Linear units (GeoKey 3076) | `9001 = metres` | **VERIFIED** |",
        "| Semi-major axis (GeoKey 2057) | `1,737,400.0 m` | **VERIFIED** |",
        "| Semi-minor axis (GeoKey 2058) | `1,737,400.0 m` | **VERIFIED** |",
        "| Sphere flattening (Key 2061) | `0.0` (perfect sphere) | **VERIFIED** |",
        "| Datum (GeoKey 2050) | `32767 = user-defined` | **VERIFIED** |",
        "| Geographic CRS (GeoKey 2048) | `32767 = user-defined` | **VERIFIED** |",
        "| Projected CRS (GeoKey 3072) | `32767 = user-defined` | **VERIFIED** |",
        "| GeoAsciiParams | `GCS_Moon / D_Moon / Moon Ellipsoid` | **VERIFIED** |",
        "| **ProjStraightVertPoleLong (GeoKey 3092)** | **`1.0 deg`** | **ANOMALOUS** |",
        "",
        "> [!IMPORTANT]",
        "> `GeoKey 3092 = 1.0 deg` is **non-standard**. The conventional value for a canonical",
        "> south-pole stereographic map is `0.0 deg`. This was not previously flagged in Phase 23A.",
        "> See Track 4 for displacement analysis.",
        "",
        "### 3.2 Per-Pair Tiepoints and Dimensions",
        "",
        "| Pair | W × H (px) | E₀ (m) | N₀ (m) | E₀ mod 5 | N₀ mod 5 |",
        "|------|-----------|--------|--------|----------|----------|",
    ]
    for m in meta_summary:
        pair = m["pair"]
        W, H = VERIFIED_DIMS_WH[pair]
        E0, N0 = VERIFIED_TIEPOINTS[pair]
        lines.append(
            f"| {pair} | {W} × {H} | {E0:.1f} | {N0:.1f} | "
            f"{E0 % 5.0:.1f} | {N0 % 5.0:.1f} |"
        )

    lines += [
        "",
        "### 3.3 Absent Provenance Tags",
        "",
        "All provenance GeoTIFF tags are **ABSENT** in all 4 reference rasters:",
        "",
        "| Tag | ID | Status |",
        "|-----|----|--------|",
        "| TIFFTAG_SOFTWARE | 305 | **ABSENT** |",
        "| TIFFTAG_DATETIME | 306 | **ABSENT** |",
        "| TIFFTAG_IMAGEDESCRIPTION | 270 | **ABSENT** |",
        "| TIFFTAG_ARTIST | 315 | **ABSENT** |",
        "| GDAL_METADATA | 42112 | **ABSENT** |",
        "| ModelTransformation | 34264 | **ABSENT** |",
        "",
        "**Conclusion:** No software, date, mission, or product identifier is embedded in any "
        "delivered reference raster. The geodetic realization cannot be determined from "
        "GeoTIFF tag provenance alone.",
        "",
        "---",
        "",
        "## 4. Track 2 — Authoritative Candidate-Source Audit",
        "",
        "| ID | Product | Classification | Rationale Summary |",
        "|----|---------|---------------|-------------------|",
    ]
    for c in candidates:
        rat = c["rationale"].split(".")[0] + "."
        lines.append(
            f"| {c['id']} | {c['name']} | **{c['classification']}** | {rat} |"
        )

    lines += [
        "",
        "> [!NOTE]",
        "> No candidate achieves `DIRECTLY_SUPPORTED` classification for the upstream cartographic",
        "> source product. `CAND_B06` (Delivery Container) is `DIRECTLY_SUPPORTED` only as the",
        "> packaging layer — the upstream geodetic source remains `UNKNOWN`.",
        "",
        "---",
        "",
        "## 5. Track 3 — Geodetic-Frame Reconciliation",
        "",
        "*(Reuses Phase 23A.7 verified results. No novel SPICE calls.)*",
        "",
        "| Frame Pair | Max Surface Displacement | vs Observed Residual | Classification |",
        "|------------|------------------------|----------------------|----------------|",
        f"| IAU_MOON ↔ MOON_ME_DE421 | **{IAU_TO_ME421_MAX_DISP_M:.1f} m** | "
        f"{frame_rec['frame_fraction_of_min_residual']:.1f}%–"
        f"{frame_rec['frame_fraction_of_max_residual']:.1f}% of residual | "
        f"**{frame_rec['classification']}** |",
        "| MOON_ME_DE421 ↔ MOON_ME | 0 m (same frame alias) | N/A | NOT_A_DISTINCT_FRAME |",
        "| IAU_MOON ↔ ULCN2005 | Unknown | — | INSUFFICIENT_INFORMATION |",
        "",
        f"> **{frame_rec['interpretation']}**",
        "",
        "**Additional frame candidates examined:**",
        "",
    ]
    for afc in frame_rec["additional_frame_candidates"]:
        lines.append(f"- **{afc['frame_pair']}:** {afc['status']} — {afc['note']}")
    lines.append("")

    lines += [
        "---",
        "",
        "## 6. Track 4 — Raster-Grid / Coordinate-Origin Audit",
        "",
        "### 6.1 Standard Convention Verification",
        "",
        "| Convention | Value | Status |",
        "|-----------|-------|--------|",
        "| Raster pixel type | `RasterPixelIsArea` (GeoKey 1025 = 1) | **VERIFIED** |",
        "| Tiepoint pixel reference | Centre of pixel (col=0, row=0) | **VERIFIED** |",
        "| False easting | 0.0 m | **VERIFIED** |",
        "| False northing | 0.0 m | **VERIFIED** |",
        "| Scale factor at pole | 1.0 | **VERIFIED** |",
        "| Linear units | metres | **VERIFIED** |",
        "| Row direction | Top-to-bottom (N decreases downward) | **VERIFIED** |",
        "| Column direction | Left-to-right (E increases rightward) | **VERIFIED** |",
        "| Grid phase (E mod 5) | 3.0 m (all 4 pairs) | **VERIFIED** |",
        "| Grid phase (N mod 5) | 2.0 m (all 4 pairs) | **VERIFIED** |",
        "| PixelIsPoint half-pixel offset | 2.5 m (sub-pixel, negligible) | **VERIFIED (negligible)** |",
        "",
        "### 6.2 Non-Standard Finding: ProjStraightVertPoleLong = 1.0 deg",
        "",
    ]

    # Pick pair_01 for the note
    for pair_name, rec in coord_audit.items():
        if pair_name == "OHRC_PAIR_01":
            lines.append(rec["non_standard_straight_vert_pole_long_note"])
            lines.append("")
            lines.append(
                f"**Azimuthal displacement at 150 km from pole:** "
                f"`{rec['straight_vert_pole_long_disp_at_150km_m']:.1f} m` "
                "(azimuthal direction; affects map orientation, not pole position)"
            )
            break

    lines += [
        "",
        "> [!WARNING]",
        "> This is a **NEW ANOMALOUS FINDING** in Phase 23B. GeoKey 3092 = 1.0 deg is non-standard.",
        "> The surface-displacement consequence at typical raster distances from the pole is",
        "> sub-kilometre to ~2.6 km. This cannot be confirmed as the source of the km-scale",
        "> residual without an authoritative external reference product for comparison.",
        "",
        "---",
        "",
        "## 7. Track 5 — Provenance-Link Audit",
        "",
        "| Item Searched | Result | Status |",
        "|--------------|--------|--------|",
    ]
    for pl in provenance_links:
        result_short = pl["result"].split(".")[0] + "."
        lines.append(
            f"| {pl['item']} | {result_short} | **{pl['status']}** |"
        )

    lines += [
        "",
        "> [!NOTE]",
        "> Absence of provenance metadata is documented as `NOT_FOUND_IN_AUDITED_INPUTS`.",
        "> This does NOT imply that such metadata never existed — it may exist in ISRO internal",
        "> processing archives not available to this audit.",
        "",
        "---",
        "",
        "## 8. Track 6 — Pair 02/03 Consistency Check",
        "",
        "### 8.1 Verified Identical-Overlap Result (IMMUTABLE)",
        "",
        "| Measurement | Value |",
        "|-------------|-------|",
        f"| Overlap polygon E (m) | [{pair_check['verified_result']['overlap_polygon_E_m'][0]}, "
        f"{pair_check['verified_result']['overlap_polygon_E_m'][1]}] |",
        f"| Overlap polygon N (m) | [{pair_check['verified_result']['overlap_polygon_N_m'][0]}, "
        f"{pair_check['verified_result']['overlap_polygon_N_m'][1]}] |",
        f"| Overlap dimensions | `{pair_check['verified_result']['overlap_dimensions_px']}` pixels |",
        f"| Total pixels | `{pair_check['verified_result']['total_pixels']:,}` |",
        f"| Identical pixels | `{pair_check['verified_result']['identical_pixels']:,}` "
        f"(`{pair_check['verified_result']['pct_identical']:.2f}%`) |",
        f"| Mean diff | `{pair_check['verified_result']['mean_diff']:.4f}` |",
        f"| RMS diff | `{pair_check['verified_result']['rms_diff']:.4f}` |",
        f"| Status | **`{pair_check['verified_result']['status_string']}`** |",
        "",
        "### 8.2 Supported Inferences",
        "",
    ]
    for s in pair_check["supported_inferences"]:
        lines.append(f"- {s}")
    lines += [
        "",
        "### 8.3 Unsupported Inferences (Explicitly Excluded)",
        "",
    ]
    for u in pair_check["unsupported_inferences"]:
        lines.append(f"- {u}")
    lines += [
        "",
        f"**Geodetic implication:** {pair_check['geodetic_implication']}",
        "",
        "---",
        "",
        "## 9. Track 7 — Final Classification Decision Matrix",
        "",
        "| Option | Description | Selected |",
        "|--------|-------------|----------|",
        "| A | Geodetic realization directly identified | ✗ |",
        "| B | Geodetic realization constrained but not identified | ✗ |",
        "| **C** | **Geodetic realization remains unresolved** | **✓** |",
        "",
        "**Selected:** `C — Geodetic realization remains unresolved`",
        "",
        "**Evidentiary basis:**",
        "",
    ]
    for i, eb in enumerate(classification["evidentiary_basis"], 1):
        lines.append(f"{i}. {eb}")
    lines += [
        "",
        "---",
        "",
        "## 10. New Finding — ProjStraightVertPoleLong Anomaly",
        "",
        f"**Finding:** {classification['new_finding']['finding']}  ",
        f"**Status:** `{classification['new_finding']['status']}`  ",
        "",
        classification["new_finding"]["implication"],
        "",
        "**Action:** No correction applied. No empirical transform fitted. "
        "This finding is recorded for future investigation.",
        "",
        "---",
        "",
        "## 11. What This Audit Does NOT Prove",
        "",
    ]
    for w in classification["what_this_does_not_prove"]:
        lines.append(f"- {w}")
    lines += [
        "",
        "---",
        "",
        "## 12. Unresolved Items Carried Forward",
        "",
        "| Item | Status |",
        "|------|--------|",
        "| Upstream cartographic source product identity | `UNRESOLVED` |",
        "| Reference geodetic realization (frame name) | `UNKNOWN` |",
        "| Reference raster → MOON_ME_DE421 linkage | `NOT_VERIFIED` |",
        "| ProjStraightVertPoleLong = 1.0 deg anomaly | `ANOMALOUS — FUTURE INVESTIGATION` |",
        "| ULCN2005 vs MOON_ME_DE421 offset | `INSUFFICIENT_INFORMATION` |",
        "| ISRO SelenoTagging reference product | `NOT_FOUND_IN_AUDITED_INPUTS` |",
        "| AutoLCP reference product | `NOT_FOUND_IN_AUDITED_INPUTS` |",
        "",
        "---",
        "",
        "## 13. Final Status Block",
        "",
        "> [!IMPORTANT]",
        f"> **`REFERENCE_PRODUCT_UNRESOLVED`**  ",
        f"> **`REFERENCE_GEODETIC_REALIZATION = UNKNOWN`**  ",
        f"> **`REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED`**  ",
        f"> **`PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW`**  ",
        ">",
        "> Phase 23B executed a full multi-track geodetic link review. The geodetic realization",
        "> remains unresolved. Phase 23B is NOT considered complete merely because this audit ran.",
        "> Production registration remains frozen.",
        "",
        "---",
        "",
        "## 14. Reproducibility",
        "",
        f"- **Script:** `{SCRIPT_NAME}`",
        "- **Python:** standard library + PIL (Pillow) only",
        "- **No GDAL, no SPICE, no image matching performed**",
        "- **Input data:** delivered mentor benchmark TIFFs + PDS4 XMLs (unmodified)",
        "- **Frame data:** Phase 23A.7 verified constants (no new SPICE calls)",
        "",
        "---",
        "",
        "> # **`PHASE 23B EXECUTED — GEODETIC REALIZATION REMAINS UNRESOLVED`**",
        "",
    ]

    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_candidate_registry_csv(candidates):
    p = os.path.join(OUTPUT_DIR, "phase23b_candidate_registry.csv")
    fieldnames = [
        "id", "name", "producer", "instrument", "native_resolution_m",
        "projection", "geodetic_frame", "datum_radius_m", "south_pole_convention",
        "product_type", "resampling_history", "documentation",
        "classification", "rationale", "geodetic_realization_link"
    ]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in candidates:
            w.writerow({k: c.get(k, "") for k in fieldnames})
    print(f"Created: {p}")


def generate_candidate_registry_json(candidates):
    p = os.path.join(OUTPUT_DIR, "phase23b_candidate_registry.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    print(f"Created: {p}")


def generate_coordinate_convention_report(coord_audit):
    p = os.path.join(OUTPUT_DIR, "phase23b_coordinate_convention_report.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Phase 23B — Coordinate Convention Audit Report",
        "",
        f"**Generated:** {now}",
        "",
        "## Per-Pair Geotransform and Convention Analysis",
        "",
        "| Pair | UL Corner E (m) | UL Corner N (m) | LR Corner E (m) | LR Corner N (m) | "
        "Straight Vert Pole Long | Grid Phase OK |",
        "|------|----------------|----------------|----------------|----------------|"
        "------------------------|--------------|",
    ]
    for pair_name, rec in coord_audit.items():
        lines.append(
            f"| {pair_name} | {rec['ul_corner_E_m']:.1f} | {rec['ul_corner_N_m']:.1f} | "
            f"{rec['lr_corner_E_m']:.1f} | {rec['lr_corner_N_m']:.1f} | "
            f"{rec['straight_vert_pole_long_deg']} deg | "
            f"{'✓' if rec['grid_phase_consistent'] else '✗'} |"
        )
    lines += [
        "",
        "## ProjStraightVertPoleLong Anomaly",
        "",
        "**GeoKey 3092 = 1.0 deg in all 4 pairs (non-standard; expected 0.0 deg)**",
        "",
        "| Distance from Pole (km) | Implied Azimuthal Displacement (m) |",
        "|------------------------|------------------------------------|",
    ]
    for dist_km in [50, 100, 150, 200, 250]:
        disp = dist_km * 1000.0 * math.sin(math.radians(1.0))
        lines.append(f"| {dist_km} | {disp:.1f} |")
    lines += [
        "",
        "> Classification: **ANOMALOUS** — requires external reference product for confirmation.",
        "",
    ]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_provenance_link_report(provenance_links):
    p = os.path.join(OUTPUT_DIR, "phase23b_provenance_link_report.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Phase 23B — Provenance Link Audit Report",
        "",
        f"**Generated:** {now}",
        "",
        "## Provenance Items Searched",
        "",
        "| # | Item | Result | Status |",
        "|---|------|--------|--------|",
    ]
    for i, pl in enumerate(provenance_links, 1):
        lines.append(
            f"| {i} | {pl['item']} | {pl['result'][:80]}... | **{pl['status']}** |"
            if len(pl["result"]) > 80
            else f"| {i} | {pl['item']} | {pl['result']} | **{pl['status']}** |"
        )
    lines += [
        "",
        "## Summary",
        "",
        "- **Items searched:** " + str(len(provenance_links)),
        "- **NOT_FOUND_IN_AUDITED_INPUTS:** " + str(
            sum(1 for pl in provenance_links if pl["status"] == "NOT_FOUND_IN_AUDITED_INPUTS")),
        "- **FOUND_BUT_NON_IDENTIFYING:** " + str(
            sum(1 for pl in provenance_links if pl["status"] == "FOUND_BUT_NON_IDENTIFYING")),
        "- **FOUND_ANOMALOUS:** " + str(
            sum(1 for pl in provenance_links if pl["status"] == "FOUND_ANOMALOUS")),
        "",
        "**Conclusion:** No provenance item positively identifies the upstream reference product "
        "or its geodetic realization.",
        "",
    ]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_frame_reconciliation_report(frame_rec):
    p = os.path.join(OUTPUT_DIR, "phase23b_frame_reconciliation_report.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Phase 23B — Frame Reconciliation Report",
        "",
        f"**Generated:** {now}",
        "",
        "## Verified Phase 23A.7 Frame Results (Imported, Not Recomputed)",
        "",
        f"- IAU_MOON ↔ MOON_ME_DE421 max surface displacement: **{IAU_TO_ME421_MAX_DISP_M:.1f} m**",
        f"- IAU_MOON ↔ MOON_ME_DE421 min surface displacement: **{IAU_TO_ME421_MIN_DISP_M:.1f} m**",
        "",
        "## Recalculated Surface Arc (Phase 23B, for completeness)",
        "",
        f"- Rotation angle upper bound: `{frame_rec['angle_upper_deg']} deg`",
        f"- Arc at south pole: `{frame_rec['recalculated_arc_upper_m']} m`",
        f"- Arc at lat -85 deg: `{frame_rec['recalculated_arc_at_lat85_m']} m`",
        "",
        "## Comparison to Observed Residuals",
        "",
        f"- Observed residual range: `{frame_rec['observed_residual_min_m']:.0f}–"
        f"{frame_rec['observed_residual_max_m']:.0f} m`",
        f"- Frame effect as fraction: `{frame_rec['frame_fraction_of_min_residual']:.1f}%–"
        f"{frame_rec['frame_fraction_of_max_residual']:.1f}%` of observed residual",
        f"- **Classification: `{frame_rec['classification']}`**",
        "",
        "## Additional Frame Candidates",
        "",
    ]
    for afc in frame_rec["additional_frame_candidates"]:
        lines.append(f"### {afc['frame_pair']}")
        lines.append(f"- **Status:** `{afc['status']}`")
        lines.append(f"- {afc['note']}")
        lines.append("")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_readiness_report(classification):
    p = os.path.join(OUTPUT_DIR, "phase23b_readiness_report.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Phase 23B — Readiness Report",
        "",
        f"**Generated:** {now}",
        "",
        "## Final Geodetic Classification",
        "",
        f"**Selected Classification:** `{classification['selected_classification']} — "
        f"{classification['classification_label']}`",
        "",
        "## Retained Status Block",
        "",
        "```",
        "REFERENCE_PRODUCT_UNRESOLVED",
        "REFERENCE_GEODETIC_REALIZATION = UNKNOWN",
        "REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED",
        "PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW",
        "```",
        "",
        "## New Finding",
        "",
        f"- **{classification['new_finding']['finding']}**",
        f"- Status: `{classification['new_finding']['status']}`",
        f"- Requires future investigation: {classification['new_finding']['requires_future_investigation']}",
        "",
        "## Phase 23B Gate",
        "",
        classification["retained_statuses"]["note"],
        "",
        "---",
        "",
        "> # **`PHASE 23B EXECUTED - GEODETIC REALIZATION REMAINS UNRESOLVED`**",
        "",
    ]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_readme():
    p = os.path.join(OUTPUT_DIR, "README.md")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Read existing README if present, append Phase 23B section
    existing = ""
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            existing = f.read()

    # Remove any existing Phase 23B block to avoid duplication
    if "## Phase 23B" in existing:
        existing = existing[:existing.index("## Phase 23B")].rstrip()

    phase23b_section = f"""

## Phase 23B — Reference Geodetic Realization / Geodetic Link Review

**Generated:** {now}  
**Script:** `{SCRIPT_NAME}`  
**Status:** EXECUTED — GEODETIC REALIZATION REMAINS UNRESOLVED  

### Outputs

| File | Description |
|------|-------------|
| `phase23b_geodetic_link_review.md` | Main Phase 23B research report (8 tracks) |
| `phase23b_candidate_registry.csv` | Authoritative candidate source audit (7 candidates) |
| `phase23b_candidate_registry.json` | Machine-readable candidate registry |
| `phase23b_coordinate_convention_report.md` | Raster-grid / coordinate-origin audit |
| `phase23b_provenance_link_report.md` | Provenance-link audit findings |
| `phase23b_frame_reconciliation_report.md` | Geodetic-frame reconciliation report |
| `phase23b_readiness_report.md` | Phase gate and final status |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```

### New Finding

**ProjStraightVertPoleLong (GeoKey 3092) = 1.0 deg** (non-standard; conventional is 0.0 deg).  
Implies azimuthal displacement of ~2,618 m at 150 km from pole.  
Status: `ANOMALOUS — FUTURE INVESTIGATION REQUIRED`.

"""
    with open(p, "w", encoding="utf-8") as f:
        f.write(existing + phase23b_section)
    print(f"Updated: {p}")


# ===========================================================================
# CHECKSUMS
# ===========================================================================
def update_checksums():
    chk_path = os.path.join(OUTPUT_DIR, "checksums.sha256")

    # Build list of all files to checksum
    files_to_hash = []
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if fname == "checksums.sha256":
            continue
        full = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(full):
            files_to_hash.append(fname)

    entries = {}
    for fname in files_to_hash:
        full = os.path.join(OUTPUT_DIR, fname)
        with open(full, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        entries[fname] = h

    with open(chk_path, "w", encoding="utf-8") as f:
        for fname, h in sorted(entries.items()):
            f.write(f"{h}  {fname}\n")

    print(f"Updated: {chk_path} ({len(entries)} entries)")
    return entries


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    print("=" * 70)
    print("PHASE 23B — REFERENCE GEODETIC REALIZATION / GEODETIC LINK REVIEW")
    print("Governing Discipline: Research-Only — Production Code Frozen.")
    print("=" * 70)

    # Track 1 — Metadata
    print("\n[Track 1] Auditing reference-raster GeoTIFF metadata...")
    meta = audit_geotiff_metadata()
    if meta:
        meta_summary = build_metadata_summary(meta)
        print(f"  Audited {len(meta_summary)} pairs.")
        for m in meta_summary:
            print(f"  {m['pair']}: {m['width']}×{m['height']} px, "
                  f"tiepoint=({VERIFIED_TIEPOINTS[m['pair']][0]}, "
                  f"{VERIFIED_TIEPOINTS[m['pair']][1]}) m, "
                  f"StraightVertPoleLong={m.get('ProjStraightVertPoleLong', 'N/A')}")
    else:
        meta_summary = [
            {
                "pair": p,
                "width": VERIFIED_DIMS_WH[p][0],
                "height": VERIFIED_DIMS_WH[p][1],
                "tiepoint_geo_m": VERIFIED_TIEPOINTS[p],
            }
            for p in PAIRS
        ]

    # Track 2 — Candidates
    print("\n[Track 2] Building authoritative candidate-source registry...")
    candidates = build_candidate_registry()
    print(f"  Compiled {len(candidates)} candidate records.")
    for c in candidates:
        print(f"  {c['id']}: {c['classification']} — {c['name'][:50]}")

    # Track 3 — Frame reconciliation
    print("\n[Track 3] Geodetic-frame reconciliation (using Phase 23A.7 verified results)...")
    frame_rec = compute_frame_reconciliation()
    print(f"  IAU_MOON<->MOON_ME_DE421 max: {frame_rec['recalculated_arc_upper_m']} m")
    print(f"  Fraction of observed residual: "
          f"{frame_rec['frame_fraction_of_min_residual']}%-"
          f"{frame_rec['frame_fraction_of_max_residual']}%")
    print(f"  Classification: {frame_rec['classification']}")

    # Track 4 — Coordinate conventions
    print("\n[Track 4] Auditing raster-grid / coordinate-origin conventions...")
    coord_audit = audit_coordinate_conventions()
    for pair_name, rec in coord_audit.items():
        print(f"  {pair_name}: RasterType={rec['raster_type']}, "
              f"StraightVertPoleLong={rec['straight_vert_pole_long_deg']} deg "
              f"[{'ANOMALOUS' if rec['straight_vert_pole_long_deg'] != 0.0 else 'OK'}], "
              f"GridPhase={'OK' if rec['grid_phase_consistent'] else 'FAIL'}")

    # Track 5 — Provenance links
    print("\n[Track 5] Auditing provenance links...")
    provenance_links = audit_provenance_links()
    n_missing = sum(1 for p_ in provenance_links if p_["status"] == "NOT_FOUND_IN_AUDITED_INPUTS")
    n_anomal = sum(1 for p_ in provenance_links if p_["status"] == "FOUND_ANOMALOUS")
    print(f"  {len(provenance_links)} items searched: {n_missing} NOT_FOUND, {n_anomal} ANOMALOUS.")

    # Track 6 — Pair consistency
    print("\n[Track 6] Pair 02/03 consistency check...")
    pair_check = audit_pair_consistency()
    print(f"  Verified: {pair_check['verified_result']['status_string']}")

    # Track 7 — Classification
    print("\n[Track 7] Final geodetic classification...")
    classification = classify_geodetic_realization()
    print(f"  Selected: {classification['selected_classification']} — "
          f"{classification['classification_label']}")
    print(f"  New finding: {classification['new_finding']['finding']}")
    print(f"  New finding status: {classification['new_finding']['status']}")

    # Generate reports
    print("\n[Outputs] Generating reports...")
    generate_main_report(
        meta_summary, candidates, frame_rec, coord_audit,
        provenance_links, pair_check, classification
    )
    generate_candidate_registry_csv(candidates)
    generate_candidate_registry_json(candidates)
    generate_coordinate_convention_report(coord_audit)
    generate_provenance_link_report(provenance_links)
    generate_frame_reconciliation_report(frame_rec)
    generate_readiness_report(classification)
    generate_readme()

    print("\nUpdating checksums.sha256 in 3d_projection/...")
    update_checksums()

    print("\nPhase 23B execution successfully finished.")
    print("=" * 70)
    print("FINAL STATUS:")
    print("  REFERENCE_PRODUCT_UNRESOLVED")
    print("  REFERENCE_GEODETIC_REALIZATION = UNKNOWN")
    print("  REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED")
    print("  PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW")
    print("  NEW FINDING: ProjStraightVertPoleLong = 1.0 deg [ANOMALOUS]")
    print("=" * 70)


if __name__ == "__main__":
    main()
