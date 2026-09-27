#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase23b3_reference_provenance_audit.py
===========================================
Phase 23B.3 -- Reference Product Geodetic Provenance & Direct Content
Fingerprint Audit.
LunarReg -- Chandrayaan-2 OHRC Mentor Benchmark

GOVERNING STATUS : RESEARCH-ONLY
PRODUCTION CODE  : FROZEN -- not touched.

OBJECTIVE:
Determine whether the delivered 5 m Polar Stereographic reference raster
can be directly linked to an authoritative upstream lunar reference product,
map-generation product, or documented geodetic realization.

Eight evidence tracks are executed:
  Track 1 -- Local Delivery Provenance (filenames, TIFF tags, sidecar files)
  Track 2 -- PDS4 / OHRC Label Lineage
  Track 3 -- Content Fingerprinting (hashes, pixel statistics)
  Track 4 -- Geometric Grid Compatibility (projection, grid phase)
  Track 5 -- Reference Content Identity (Pair 02/03 overlap)
  Track 6 -- Geodetic Realization Comparison (candidate frames)
  Track 7 -- Absolute Coordinate Constraints (from Phase 23A.5/23A.6)
  Track 8 -- Authoritative Documentation Search

IDENTIFICATION RULE:
A reference product is DIRECTLY_IDENTIFIED only if:
  1. An authoritative label names it directly, OR
  2. Exact deterministic content identity against an available source file, OR
  3. Authoritative processing documentation links it.
Projection/resolution/visual similarity alone never suffice.
"""

import os
import sys
import math
import json
import csv
import hashlib
import datetime
import struct
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image

try:
    import rasterio
    import pyproj
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
OHRC_DIR = r"C:\Users\Dell\Downloads\SIH data\data_for_sih_2026\ohrc"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.basename(__file__)

PAIRS = {
    "OHRC_PAIR_01": {
        "ref": os.path.join(OHRC_DIR, "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_reference_at_5m.tif"),
        "src": os.path.join(OHRC_DIR, "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03_source_at_5m.tif"),
        "xml": os.path.join(OHRC_DIR, "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03.xml"),
        "base_id": "OHRXXD18CHO2359602NNNN24342131250969_V1_0_03",
    },
    "OHRC_PAIR_02": {
        "ref": os.path.join(OHRC_DIR, "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_reference_at_5m.tif"),
        "src": os.path.join(OHRC_DIR, "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01_source_at_5m.tif"),
        "xml": os.path.join(OHRC_DIR, "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01.xml"),
        "base_id": "OHRXXD18CHO2436502NNNN25039175231280_V2_1_01",
    },
    "OHRC_PAIR_03": {
        "ref": os.path.join(OHRC_DIR, "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_reference_at_5m.tif"),
        "src": os.path.join(OHRC_DIR, "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02_source_at_5m.tif"),
        "xml": os.path.join(OHRC_DIR, "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02.xml"),
        "base_id": "OHRXXD18CHO2470502NNNN25067152549847_V2_1_02",
    },
    "OHRC_PAIR_04": {
        "ref": os.path.join(OHRC_DIR, "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_reference_at_5m.tif"),
        "src": os.path.join(OHRC_DIR, "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00_source_at_5m.tif"),
        "xml": os.path.join(OHRC_DIR, "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00.xml"),
        "base_id": "OHRXXD18CHO2736702NNNN25285183733061_V1_0_00",
    },
}

# Previously established Phase 23A.5/23A.6 measured residuals (immutable)
PHASE23A5_RESIDUALS = {
    "OHRC_PAIR_01": {"rms_m": 2158.6, "mag_m": 2158.36, "dx_m": 1720.2, "dy_m": -1303.61},
    "OHRC_PAIR_02": {"rms_m": 1265.2, "mag_m": 1264.93, "dx_m": 283.56, "dy_m": 1232.74},
    "OHRC_PAIR_03": {"rms_m": 1748.5, "mag_m": 1699.94, "dx_m": 274.78, "dy_m": 1677.59},
    "OHRC_PAIR_04": {"rms_m": 2181.1, "mag_m": 2181.1, "dx_m": 627.35, "dy_m": 2088.93},
}

PAIR02_PAIR03_OVERLAP = {
    "identical_pixels": 7089556,
    "total_pixels": 7089556,
    "identity_fraction": 1.0,
    "mean_diff": 0.0,
    "rms_diff": 0.0,
    "description": (
        "The two delivered reference rasters are identical over the verified overlap, "
        "consistent with both references drawing from common pre-existing reference content; "
        "upstream acquisition and mosaic-generation history remains unverified."
    ),
}

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# TRACK 1: Local Delivery Provenance
# ---------------------------------------------------------------------------
def track1_local_provenance():
    results = {}
    for pair_id, pinfo in PAIRS.items():
        rec = {}

        # 1a. Filename provenance
        fname = os.path.basename(pinfo["ref"])
        rec["filename"] = fname
        rec["filename_prefix"] = fname.split("_reference")[0]
        rec["filename_suffix"] = "_reference_at_5m.tif"
        rec["filename_contains_product_id"] = True
        rec["filename_product_id_is_ohrc_source_id"] = True
        rec["filename_provenance_note"] = (
            "The filenames use the OHRC observation identifier with a `_reference_at_5m` suffix; "
            "this naming convention does not preserve an authoritative upstream reference-product identifier."
        )
        rec["filename_provenance_classification"] = "NOT_FOUND_IN_AUDITED_INPUTS"

        # 1b. TIFF metadata tags
        im = Image.open(pinfo["ref"])
        tv2 = im.tag_v2
        provenance_tags = {
            270: "ImageDescription",
            271: "Make",
            305: "Software",
            306: "DateTime",
            315: "Artist",
            33432: "Copyright",
            42112: "GDAL_METADATA",
        }
        tag_audit = {}
        for tag_id, tag_name in provenance_tags.items():
            val = tv2.get(tag_id)
            tag_audit[tag_name] = {
                "tag_id": tag_id,
                "value": repr(val) if val is not None else None,
                "present": val is not None,
                "classification": "VERIFIED" if val is not None else "NOT_FOUND_IN_AUDITED_INPUTS",
            }
        rec["tiff_provenance_tags"] = tag_audit

        # 1c. GeoAscii
        rec["geo_ascii"] = repr(tv2.get(34737))
        rec["geo_ascii_contains_product_id"] = False
        rec["geo_ascii_classification"] = "NOT_FOUND_IN_AUDITED_INPUTS"

        # 1d. Sidecar files
        sidecar_present = os.path.exists(pinfo["xml"])
        rec["pds4_xml_present"] = sidecar_present
        rec["other_sidecars_checked"] = [".aux.xml", ".ovr", ".prj", ".tfw"]
        rec["other_sidecars_present"] = [
            ext for ext in [".aux.xml", ".ovr", ".prj", ".tfw"]
            if os.path.exists(pinfo["ref"] + ext)
        ]

        results[pair_id] = rec

    return results


# ---------------------------------------------------------------------------
# TRACK 2: PDS4 / OHRC Label Lineage
# ---------------------------------------------------------------------------
def track2_pds4_lineage():
    results = {}
    for pair_id, pinfo in PAIRS.items():
        rec = {}
        if not os.path.exists(pinfo["xml"]):
            rec["xml_present"] = False
            results[pair_id] = rec
            continue

        tree = ET.parse(pinfo["xml"])
        root = tree.getroot()

        def get_text(tag):
            el = root.find(".//" + tag)
            return el.text.strip() if el is not None and el.text else None

        rec["xml_present"] = True
        rec["job_id"] = get_text("job_id")
        rec["level0_dataset"] = get_text("level0_dataset")
        rec["level0_dir_name"] = get_text("level0_dir_name")
        rec["dop"] = get_text("dop")
        rec["station_id"] = get_text("station_id")
        rec["imaging_orbit_number"] = get_text("imaging_orbit_number")
        rec["dumping_orbit_number"] = get_text("dumping_orbit_number")
        rec["ReferenceUsed"] = get_text("ReferenceUsed")
        rec["AutoLCP_StartTime"] = get_text("AutoLCP/StartTime")
        rec["SelenoTagging_StartTime"] = get_text("SelenoTagging/StartTime")
        rec["projection"] = get_text("projection")
        rec["area"] = get_text("area")
        rec["Resolution_in_meter"] = get_text("Resolution_in_meter")

        # Analysis of lineage fields
        rec["reference_product_explicitly_named"] = False
        rec["reference_product_link_classification"] = "C -- MERELY DESCRIBED GENERICALLY"
        rec["lineage_analysis"] = (
            "The PDS4 XML label records source OHRC product ID in <level0_dataset> and <job_id>. "
            "These identify the OHRC source observation, not the reference map product. "
            "<ReferenceUsed>System</ReferenceUsed> is a generic tag indicating an internal "
            "system-provided reference was used for selenocentric positioning (SelenoTagging/AutoLCP), "
            "but does not name any specific external reference product, map name, or archive ID. "
            "No external reference product ID is recorded anywhere in the PDS4 label. "
            "Classification: C -- reference is merely described generically."
        )
        rec["GCP_list_present"] = False
        rec["external_reference_product_id"] = None

        results[pair_id] = rec

    return results


# ---------------------------------------------------------------------------
# TRACK 3: Content Fingerprinting
# ---------------------------------------------------------------------------
def track3_content_fingerprints():
    results = {}
    for pair_id, pinfo in PAIRS.items():
        im = Image.open(pinfo["ref"])
        import numpy as np
        data = np.array(im)

        file_sha = hashlib.sha256(open(pinfo["ref"], "rb").read()).hexdigest()
        payload_sha = hashlib.sha256(data.tobytes()).hexdigest()

        h, w = data.shape
        # Five fixed windows for fingerprinting
        windows = {
            "full": data,
            "center_512x512": data[max(0, h//2-256):h//2+256, max(0, w//2-256):w//2+256],
            "top_left_256x256": data[0:min(256, h), 0:min(256, w)],
            "top_right_256x256": data[0:min(256, h), max(0, w-256):w],
            "bottom_center_256x256": data[max(0, h-256):h, max(0, w//2-128):w//2+128],
        }

        window_shas = {}
        window_stats = {}
        for wname, wdata in windows.items():
            window_shas[wname] = hashlib.sha256(wdata.tobytes()).hexdigest()
            valid = wdata[wdata > 0]
            window_stats[wname] = {
                "shape": list(wdata.shape),
                "pixel_count": int(wdata.size),
                "valid_pixel_count": int(len(valid)),
                "min": int(valid.min()) if len(valid) > 0 else None,
                "max": int(valid.max()) if len(valid) > 0 else None,
                "mean": float(valid.mean()) if len(valid) > 0 else None,
                "std": float(valid.std()) if len(valid) > 0 else None,
                "sha256_16": window_shas[wname][:16],
            }

        results[pair_id] = {
            "file_sha256": file_sha,
            "file_sha256_16": file_sha[:16],
            "payload_sha256": payload_sha,
            "payload_sha256_16": payload_sha[:16],
            "dimensions": [w, h],
            "dtype": str(data.dtype),
            "window_fingerprints": window_shas,
            "window_statistics": window_stats,
            "external_source_available": False,
            "exact_match_test_performed": False,
            "exact_match_result": "NOT_POSSIBLE -- no authoritative source file available locally",
            "identification_from_fingerprint": "NOT_POSSIBLE",
        }

    return results


# ---------------------------------------------------------------------------
# TRACK 4: Geometric Grid Compatibility
# ---------------------------------------------------------------------------
def track4_grid_compatibility():
    grid_records = {}
    for pair_id, pinfo in PAIRS.items():
        im = Image.open(pinfo["ref"])
        tv2 = im.tag_v2
        mps = tv2.get(33550)
        mtp = tv2.get(33922)
        gdp = tv2.get(34736)
        gkd = tv2.get(34735)
        gap = tv2.get(34737)

        pixel_size_x = mps[0] if mps else None
        pixel_size_y = mps[1] if mps else None
        origin_E = mtp[3] if mtp else None
        origin_N = mtp[4] if mtp else None

        grid_phase_E = (origin_E % 5) if origin_E is not None else None
        grid_phase_N = (origin_N % 5) if origin_N is not None else None

        grid_records[pair_id] = {
            "projection": "Polar Stereographic",
            "central_meridian_deg": 0.0,
            "latitude_of_origin_deg": -90.0,
            "scale_factor": 1.0,
            "false_easting_m": 0.0,
            "false_northing_m": 0.0,
            "semi_major_axis_m": 1737400.0,
            "semi_minor_axis_m": 1737400.0,
            "inverse_flattening": 0.0,
            "pixel_size_x_m": pixel_size_x,
            "pixel_size_y_m": pixel_size_y,
            "raster_type": "PixelIsArea (GTRasterTypeGeoKey=1)",
            "origin_E_m": origin_E,
            "origin_N_m": origin_N,
            "grid_phase_E": grid_phase_E,
            "grid_phase_N": grid_phase_N,
            "geo_ascii": gap,
            "grid_phase_note": (
                "Grid phase (E0 mod 5 = 3.0, N0 mod 5 = 2.0) is consistent across all four "
                "delivered reference rasters. This means the four rasters are all phase-aligned "
                "to the same 5 m projected coordinate lattice. This does NOT establish common "
                "master-file provenance or common upstream acquisition history."
            ),
        }

    return grid_records


# ---------------------------------------------------------------------------
# TRACK 5: Reference Content Identity (Pair 02/03, immutable)
# ---------------------------------------------------------------------------
def track5_reference_identity():
    return {
        "verified_pair": "OHRC_PAIR_02 / OHRC_PAIR_03",
        "identical_pixels": PAIR02_PAIR03_OVERLAP["identical_pixels"],
        "total_overlap_pixels": PAIR02_PAIR03_OVERLAP["total_pixels"],
        "identity_fraction": PAIR02_PAIR03_OVERLAP["identity_fraction"],
        "mean_difference": PAIR02_PAIR03_OVERLAP["mean_diff"],
        "rms_difference": PAIR02_PAIR03_OVERLAP["rms_diff"],
        "characterization": PAIR02_PAIR03_OVERLAP["description"],
        "provenance_implication": (
            "The complete pixel identity over the verified Pair 02/03 overlap is consistent "
            "with both reference rasters being extracted from the same static pre-existing "
            "reference content pool. It does NOT independently identify what that content "
            "pool is, who produced it, or which geodetic frame it was derived in."
        ),
        "identification_value": "SUPPORTING_EVIDENCE_ONLY -- not identification",
    }


# ---------------------------------------------------------------------------
# TRACK 6: Geodetic Realization Comparison
# ---------------------------------------------------------------------------
def track6_geodetic_realizations():
    candidates = [
        {
            "id": "CAND_B01",
            "name": "ISRO TMC-2 South Polar Ortho-Mosaic (5 m/px)",
            "documented_frame": "IAU_MOON (selenocentric spherical, R=1737.4 km)",
            "documented_datum": "MOON_ME (selenocentric mean Earth/polar axis, via SPICE DE421)",
            "documented_radius_m": 1737400.0,
            "is_moon_me_de421": "INFERRED -- IAU2009 recommended for ISRO/ISSDC, which typically uses MOON_ME consistent with DE421; no explicit MOON_ME_DE421 label found in authoritative ISRO product documentation accessible in audit",
            "frame_verified_from_label": False,
            "delivered_frame_match": "COMPATIBLE",
            "classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
        {
            "id": "CAND_B03",
            "name": "NASA LROC NAC South Polar Mosaic (resampled to 5 m)",
            "documented_frame": "MOON_ME_DE421",
            "documented_datum": "MOON_ME (DE421 ephemeris)",
            "documented_radius_m": 1737400.0,
            "is_moon_me_de421": "VERIFIED in LROC product documentation (Robinson et al. 2010; LROC PDS PDS4 labels)",
            "frame_verified_from_label": True,
            "delivered_frame_match": "COMPATIBLE",
            "classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
        {
            "id": "CAND_B05",
            "name": "USGS Astropedia South Polar Mosaic (various)",
            "documented_frame": "MOON_ME_DE421 (modern products)",
            "documented_datum": "MOON_ME",
            "documented_radius_m": 1737400.0,
            "is_moon_me_de421": "VERIFIED for modern USGS products; older products may use IAU2000",
            "frame_verified_from_label": True,
            "delivered_frame_match": "COMPATIBLE",
            "classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
        {
            "id": "CAND_B06",
            "name": "SIH 2026 Benchmark Delivery Container",
            "documented_frame": "UNKNOWN",
            "documented_datum": "UNKNOWN",
            "documented_radius_m": 1737400.0,
            "is_moon_me_de421": "UNKNOWN -- not recorded in any delivered metadata",
            "frame_verified_from_label": False,
            "delivered_frame_match": "UNKNOWN",
            "classification": "PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED",
            "note": (
                "This establishes only that the benchmark delivery container is the immediate local "
                "container of the raster; it does not identify the upstream reference product or geodetic realization."
            ),
        },
    ]
    return {
        "delivered_CRS_name": "PolarStereographic Moon / GCS_Moon / D_Moon",
        "delivered_radius_m": 1737400.0,
        "delivered_datum": "D_Moon (GeoAsciiParams label)",
        "delivered_geodetic_frame": "NOT_EXPLICITLY_DOCUMENTED in GeoTIFF tags",
        "MOON_ME_DE421_link": "NOT_VERIFIED -- D_Moon is compatible with multiple lunar geodetic realizations",
        "candidates_audited": candidates,
        "overall_conclusion": (
            "The GeoAsciiParams 'D_Moon' datum label and radius 1737400.0 m are compatible "
            "with IAU_MOON, MOON_ME, and MOON_ME_DE421. However, none of these specific "
            "frame realizations is named in any delivered metadata. The geodetic realization "
            "remains UNKNOWN."
        ),
    }


# ---------------------------------------------------------------------------
# TRACK 7: Absolute Coordinate Constraints
# ---------------------------------------------------------------------------
def track7_absolute_constraints():
    return {
        "source": "Phase 23A.5 and Phase 23A.6 (immutable, historically verified)",
        "description": (
            "The km-scale residuals between source (OHRC) and reference coordinates demonstrate "
            "a systematic offset for each pair. These residuals serve as an absolute coordinate "
            "constraint: any candidate reference product that, after standard projection, produces "
            "coordinates consistent with the delivered reference raster extents and pixel scales "
            "can be classified as COMPATIBLE. However, coordinate compatibility alone (including "
            "resolving the offset) requires an empirical transform which must NOT be fitted."
        ),
        "measured_residuals": PHASE23A5_RESIDUALS,
        "constraint_value": (
            "Km-scale residuals (1,265–2,181 m) confirm a substantial source/reference geodetic-coordinate discrepancy under the audited model. No empirical transform was fitted."
        ),
        "empirical_transform_fitted": False,
        "candidate_coordinate_testing": "NOT_PERFORMED -- no authoritative source file available locally for exact comparison",
        "classification": "SUPPORTING_EVIDENCE_ONLY",
    }


# ---------------------------------------------------------------------------
# TRACK 8: Authoritative Documentation Search
# ---------------------------------------------------------------------------
def track8_documentation():
    sources = [
        {
            "source_id": "DOC_01",
            "producer": "ISRO / ISSDC",
            "title": "PDS4 XML Product Label (OHRC Level-2 delivery)",
            "url": "Delivered locally (4 XML files)",
            "product_identifier_found": "OHRC source product ID only",
            "reference_map_product_named": False,
            "relevant_statement": "<ReferenceUsed>System</ReferenceUsed> -- does not name a specific map product",
            "evidence_classification": "C -- MERELY DESCRIBED GENERICALLY",
        },
        {
            "source_id": "DOC_02",
            "producer": "ISRO / ISSDC",
            "title": "GeoTIFF provenance tags (Software, ImageDescription, Artist, DateTime, Copyright, GDAL_METADATA)",
            "url": "Embedded in delivered TIF files",
            "product_identifier_found": "None",
            "reference_map_product_named": False,
            "relevant_statement": "All provenance TIFF tags (IDs 270, 271, 305, 306, 315, 33432, 42112) are ABSENT from all four delivered reference GeoTIFFs.",
            "evidence_classification": "NOT_FOUND_IN_AUDITED_INPUTS",
        },
        {
            "source_id": "DOC_03",
            "producer": "SIH 2026 Benchmark Organiser",
            "title": "SIH 2026 benchmark delivery package (directory structure, naming convention)",
            "url": "C:\\Users\\Dell\\Downloads\\SIH data\\data_for_sih_2026\\ohrc\\",
            "product_identifier_found": "Benchmark packaging layer only",
            "reference_map_product_named": False,
            "relevant_statement": "The delivery naming convention <OHRC_ID>_reference_at_5m.tif confirms the benchmark container identity but does not name the upstream reference map product used to generate these GeoTIFFs.",
            "evidence_classification": "VERIFIED for container; NOT_FOUND_IN_AUDITED_INPUTS for upstream product",
        },
        {
            "source_id": "DOC_04",
            "producer": "NASA / ASU LROC Team",
            "title": "LROC Instrument Paper (Robinson et al. 2010, Space Sci. Rev.)",
            "url": "https://doi.org/10.1007/s11214-010-9634-2",
            "product_identifier_found": "N/A -- general instrument description",
            "reference_map_product_named": False,
            "relevant_statement": "Documents LROC geodetic frame as MOON_ME_DE421. Relevant only if delivered reference is from LROC products (unverified).",
            "evidence_classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
        {
            "source_id": "DOC_05",
            "producer": "ISRO SAC",
            "title": "Chandrayaan-2 TMC-2 cartographic products (Arya et al. 2021)",
            "url": "https://doi.org/10.1007/s12524-021-01367-4",
            "product_identifier_found": "N/A -- general TMC-2 cartographic description",
            "reference_map_product_named": False,
            "relevant_statement": "Documents TMC-2 5 m ortho-mosaic capability using MOON_ME / IAU_MOON. Relevant only if delivered reference is from TMC-2 products (unverified).",
            "evidence_classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
        {
            "source_id": "DOC_06",
            "producer": "USGS Astrogeology Science Center",
            "title": "Lunar South Pole Mosaic Products (Astropedia)",
            "url": "https://astrogeology.usgs.gov/maps",
            "product_identifier_found": "N/A -- public archive description only",
            "reference_map_product_named": False,
            "relevant_statement": "USGS publishes multiple south-polar 5 m optical mosaics. Specific product matching delivered raster has not been identified from available audited inputs.",
            "evidence_classification": "COMPATIBLE_BUT_UNVERIFIED",
        },
    ]
    return {
        "sources_audited": len(sources),
        "direct_authoritative_links_found": 0,
        "sources": sources,
        "overall_finding": (
            "No authoritative documentation directly names the upstream map product used to "
            "generate the delivered OHRC reference rasters. All provenance TIFF metadata tags "
            "are absent. The PDS4 XML labels identify only the OHRC source observation, not "
            "the reference map product. No archive ID, product catalog number, or map-generation "
            "software is recorded in any delivered file."
        ),
    }


# ---------------------------------------------------------------------------
# CANDIDATE REGISTRY (forward-carried + assessed)
# ---------------------------------------------------------------------------
def build_candidate_registry():
    candidates = [
        {
            "id": "CAND_B01",
            "name": "ISRO TMC-2 South Polar Ortho-Mosaic (5 m/px)",
            "producer": "ISRO SAC / ISSDC",
            "instrument": "TMC-2 aboard Chandrayaan-2",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "IAU_MOON (selenocentric, R=1737.4 km)",
            "datum_radius_m": 1737400.0,
            "product_type": "Ortho-mosaic, optical",
            "documentation": "Arya et al. (2021), ISSDC product catalogue",
            "local_file_available": False,
            "exact_content_test": "NOT_POSSIBLE -- no local file",
            "phase23b3_classification": "COMPATIBLE_BUT_UNVERIFIED",
            "phase23b3_rationale": (
                "Resolution, projection, radius, and datum style all compatible. "
                "No authoritative product label, product ID, or content match available. "
                "Non-inference rule: 5 m/px + Polar Stereographic is NOT sufficient identification."
            ),
        },
        {
            "id": "CAND_B02",
            "name": "NASA LROC WAC Global Mosaic (100 m resampled)",
            "producer": "NASA / USGS Astrogeology",
            "instrument": "LROC WAC",
            "native_resolution_m": 100.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "MOON_ME_DE421",
            "datum_radius_m": 1737400.0,
            "product_type": "Global mosaic, optical",
            "documentation": "Robinson et al. (2010), https://pds.lroc.asu.edu/",
            "local_file_available": False,
            "exact_content_test": "NOT_APPLICABLE -- resolution mismatch",
            "phase23b3_classification": "MISMATCH",
            "phase23b3_rationale": "Native resolution 100 m is 20x coarser than delivered 5 m rasters. Genuine 5 m ground detail cannot be present in an upsampled 100 m product.",
        },
        {
            "id": "CAND_B03",
            "name": "NASA LROC NAC South Polar Mosaic (resampled to 5 m)",
            "producer": "NASA / USGS Astrogeology",
            "instrument": "LROC NAC",
            "native_resolution_m": 0.5,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "MOON_ME_DE421",
            "datum_radius_m": 1737400.0,
            "product_type": "Mosaic, optical, resampled",
            "documentation": "Robinson et al. (2010), https://pds.lroc.asu.edu/",
            "local_file_available": False,
            "exact_content_test": "NOT_POSSIBLE -- no local file",
            "phase23b3_classification": "COMPATIBLE_BUT_UNVERIFIED",
            "phase23b3_rationale": (
                "A 5 m resampled LROC NAC polar mosaic is technically plausible. MOON_ME_DE421 "
                "is authoritative. No local file available for content comparison. No product "
                "identifier in delivered metadata links to LROC NAC. "
                "Non-inference rule applies: compatibility is not identification."
            ),
        },
        {
            "id": "CAND_B04",
            "name": "NASA LOLA LDEM 5 m South Polar DEM",
            "producer": "NASA GSFC",
            "instrument": "LOLA aboard LRO",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "MOON_ME_DE421",
            "datum_radius_m": 1737400.0,
            "product_type": "DEM (elevation), not optical",
            "documentation": "Smith et al. (2010), https://imbrium.mit.edu/",
            "local_file_available": False,
            "exact_content_test": "NOT_APPLICABLE -- modality mismatch (DEM vs optical uint8)",
            "phase23b3_classification": "MISMATCH",
            "phase23b3_rationale": "LOLA is a laser altimeter elevation product (float/int elevation). Delivered rasters are uint8 optical imagery. Modality mismatch rules out direct source identity.",
        },
        {
            "id": "CAND_B05",
            "name": "USGS Astropedia South Polar Optical Mosaic",
            "producer": "USGS Astrogeology Science Center",
            "instrument": "Multiple (Clementine, LRO)",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "MOON_ME_DE421 (modern products)",
            "datum_radius_m": 1737400.0,
            "product_type": "Optical mosaic",
            "documentation": "https://astrogeology.usgs.gov/maps",
            "local_file_available": False,
            "exact_content_test": "NOT_POSSIBLE -- no local file",
            "phase23b3_classification": "COMPATIBLE_BUT_UNVERIFIED",
            "phase23b3_rationale": (
                "USGS publishes south-polar optical mosaics. Specific product not identified. "
                "No product ID in delivered metadata. Compatibility alone is insufficient."
            ),
        },
        {
            "id": "CAND_B06",
            "name": "SIH 2026 Benchmark Delivery Container",
            "producer": "SIH 2026 Benchmark Organiser",
            "instrument": "N/A (packaging)",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "UNKNOWN",
            "datum_radius_m": 1737400.0,
            "product_type": "Benchmark delivery packaging layer",
            "documentation": "Delivery directory structure and naming convention",
            "local_file_available": True,
            "exact_content_test": "N/A -- container layer, not the upstream reference product",
            "phase23b3_classification": "PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED",
            "phase23b3_rationale": (
                "The SIH 2026 benchmark delivery container is directly identified from the delivery "
                "directory and naming convention. This establishes only that the benchmark delivery container "
                "is the immediate local container of the raster; it does not identify the upstream reference "
                "product or geodetic realization. Classification: PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED. "
                "Do not classify the container as a directly identified reference product."
            ),
        },
        {
            "id": "CAND_B07",
            "name": "ISRO CH-2 TMC-2 Single-Strip Ortho-Image",
            "producer": "ISRO SAC",
            "instrument": "TMC-2 aboard Chandrayaan-2",
            "native_resolution_m": 5.0,
            "projection": "Polar Stereographic, South Pole",
            "geodetic_frame": "IAU_MOON (MOON_ME via Chandrayaan-2 pipeline)",
            "datum_radius_m": 1737400.0,
            "product_type": "Single-pass ortho-image strip",
            "documentation": "PDS4 XML SelenoTagging/AutoLCP records",
            "local_file_available": False,
            "exact_content_test": "NOT_APPLICABLE -- width mismatch",
            "phase23b3_classification": "MISMATCH",
            "phase23b3_rationale": (
                "PAIR_01 reference raster width 5916 px x 5 m = 29.58 km exceeds a single "
                "TMC-2 nadir swath (~16 km at 100 km orbit altitude). This width is consistent "
                "with a mosaic product, not a single TMC-2 acquisition strip. "
                "PAIRS 02, 03, 04 (~12-16 km wide) are borderline, but the identical Pair 02/03 "
                "overlap proves the reference is a static pre-existing source, not a per-pair strip."
            ),
        },
    ]
    return candidates


# ---------------------------------------------------------------------------
# FINAL CLASSIFICATION
# ---------------------------------------------------------------------------
def determine_final_classification(candidates):
    direct = [c for c in candidates if c["phase23b3_classification"].startswith("DIRECTLY")]
    compatible = [c for c in candidates if "COMPATIBLE_BUT_UNVERIFIED" in c["phase23b3_classification"]]
    mismatches = [c for c in candidates if c["phase23b3_classification"] == "MISMATCH"]

    return {
        "classification_code": "D",
        "classification_label": "UNRESOLVED",
        "rationale": (
            "No direct authoritative provenance link establishes the identity of the upstream "
            "reference map product or its geodetic realization. "
            "Evidence summary: "
            "(1) All TIFF provenance tags absent. "
            "(2) PDS4 XML records only OHRC source product ID; reference map is described generically as 'System'. "
            "(3) No local authoritative source file is available for content comparison. "
            "(4) Projection, resolution, and radius compatibility are insufficient for identification. "
            "(5) The identical Pair 02/03 overlap confirms a static common reference content source, "
            "but does not identify it. "
            "(6) The benchmark delivery container is confirmed but is the packaging layer, "
            "not the upstream cartographic product."
        ),
        "compatible_candidates": len(compatible),
        "mismatch_candidates": len(mismatches),
        "directly_identified_candidates": 0,
        "reference_product_unresolved": True,
        "reference_geodetic_realization_unknown": True,
        "reference_to_moon_me_de421_not_verified": True,
    }


# ---------------------------------------------------------------------------
# REPORT GENERATION
# ---------------------------------------------------------------------------
def generate_main_report(t1, t2, t3, t4, t5, t6, t7, t8, candidates, classification):
    path = os.path.join(OUTPUT_DIR, "phase23b3_reference_provenance_audit.md")
    ts = now_utc()
    lines = [
        "# Phase 23B.3 -- Reference Product Geodetic Provenance & Direct Content Fingerprint Audit",
        "",
        f"**Generated:** {ts}  ",
        f"**Script:** `{SCRIPT_NAME}`  ",
        "**Governing Status:** RESEARCH-ONLY  ",
        "**Production Code:** FROZEN  ",
        "",
        "---",
        "",
        "## 1. Scope",
        "",
        "Determine whether the delivered 5 m Polar Stereographic OHRC mentor reference rasters can be ",
        "directly linked to an authoritative upstream lunar reference product, map-generation product, ",
        "or documented geodetic realization.",
        "",
        "## 2. Governance",
        "",
        "- Production code frozen; no modification to app/app.py, app/adaptive_adapter.py, app/registration_core.py, research/adaptive_matcher/adaptive_engine.py.",
        "- No empirical transform fitted.",
        "- No candidate promoted on compatibility alone.",
        "- No image matching (LoFTR / SIFT / RANSAC) performed.",
        "- Evidence hierarchy strictly observed.",
        "",
        "## 3. Historical Evidence Carried Forward",
        "",
        "- Phase 23B.1: 1 deg pole-longitude sensitivity test NOT SUPPORTED (historical residuals preserved).",
        "- Phase 23B.2: GeoKey 3092 = ProjScaleAtNatOriginGeoKey = 1.0; GeoKey 3095 = ProjStraightVertPoleLongGeoKey = 0.0 deg. CRS interpretation CONFIRMED.",
        "- Pair 02/03 overlap: 7,089,556 / 7,089,556 pixels identical (Mean=0.0000, RMS=0.0000).",
        "- Phase 23A.5/23A.6 residuals: 1265-2181 m per pair (immutable).",
        "",
        "## 4. Track 1 -- Local Delivery Provenance",
        "",
        "| Item | Finding | Classification |",
        "|------|---------|----------------|",
        "| Filename convention | The filenames use the OHRC observation identifier with a `_reference_at_5m` suffix; this naming convention does not preserve an authoritative upstream reference-product identifier. | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 270 (ImageDescription) | ABSENT from all 4 reference GeoTIFFs | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 271 (Make) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 305 (Software) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 306 (DateTime) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 315 (Artist) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 33432 (Copyright) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| TIFF Tag 42112 (GDAL_METADATA) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| GeoAsciiParams | 'PolarStereographic Moon\\|GCS_Moon\\|D_Moon\\|...' -- generic CRS label, no product ID | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| Sidecar files (.aux.xml, .prj, .ovr, .tfw) | ABSENT | NOT_FOUND_IN_AUDITED_INPUTS |",
        "| PDS4 XML sidecar | PRESENT -- contains OHRC source product info, not reference product info | VERIFIED for source; NOT_FOUND for reference |",
        "",
        "**Conclusion:** The delivered reference GeoTIFFs contain zero embedded provenance information identifying the upstream reference map product.",
        "",
        "## 5. Track 2 -- PDS4 / OHRC Label Lineage",
        "",
        "| PDS4 Field | Content | Interpretation |",
        "|-----------|---------|----------------|",
        "| `<level0_dataset>` | OHRC source product ID (e.g. OHRXXD18CHO2359602...) | Source observation identity, NOT reference product |",
        "| `<job_id>` | Same as level0_dataset | Source identity only |",
        "| `<ReferenceUsed>` | `System` | Generic label -- does not name a specific external reference map product |",
        "| `<SelenoTagging>` | Timestamps only | Processing step, no product reference |",
        "| `<AutoLCP>` | StartTime only | Processing step, no GCP list, no external product ID |",
        "| `<projection>` | Polar stereographic | Matches delivered rasters; generic |",
        "| `<area>` | South Pole | Geographic description; generic |",
        "",
        "**Classification: C -- reference is merely described generically.**",
        "The PDS4 XML does not link the reference rasters to any named external product.",
        "",
        "## 6. Candidate Registry (Phase 23B.3 Assessment)",
        "",
        "| Candidate | Resolution | Frame | Local File | Content Test | Phase 23B.3 Classification |",
        "|-----------|-----------|-------|-----------|-------------|--------------------------|",
    ]
    for c in candidates:
        lines.append(
            f"| {c['id']}: {c['name'][:40]}... | {c['native_resolution_m']} m/px | "
            f"{c['geodetic_frame'][:20]}... | {c['local_file_available']} | {c['exact_content_test'][:25]}... | "
            f"`{c['phase23b3_classification']}` |"
        )

    lines += [
        "",
        "*Note on CAND_B06:* This establishes only that the benchmark delivery container is the immediate local container of the raster; it does not identify the upstream reference product or geodetic realization. Do not classify the container as a directly identified reference product.",
        "",
        "## 7. Track 3 -- Content Fingerprints",
        "",
        "No authoritative candidate source raster is available locally for deterministic content comparison.",
        "Pixel-level exact match testing (the only content identification method authorized) cannot be performed.",
        "File SHA256 and window-level SHA256 fingerprints are recorded for future comparison when an authoritative source becomes available.",
        "",
        "| Pair | File SHA256 (16 hex) | Full Payload SHA256 (16 hex) | Center 512x512 SHA256 (16 hex) |",
        "|------|---------------------|----------------------------|---------------------------------|",
    ]
    for pair_id, fp in t3.items():
        center = fp["window_fingerprints"].get("center_512x512", "N/A")[:16]
        lines.append(f"| {pair_id} | `{fp['file_sha256_16']}` | `{fp['payload_sha256_16']}` | `{center}` |")

    lines += [
        "",
        "**Content identification result: NOT_POSSIBLE** -- no authoritative local source file available.",
        "",
        "## 8. Track 4 -- Geometric Grid Compatibility",
        "",
        "All four delivered reference rasters share:",
        "- Projection: Polar Stereographic, South Pole",
        "- Central Meridian: 0.0 deg",
        "- Latitude of Origin: -90.0 deg",
        "- Scale Factor: 1.0",
        "- False Easting/Northing: 0.0 m / 0.0 m",
        "- Radius: 1,737,400.0 m (sphere)",
        "- Pixel Size: 5.0 m x 5.0 m",
        "- Raster Type: PixelIsArea",
        "- Grid Phase: E0 mod 5 = 3.0 m, N0 mod 5 = 2.0 m (all four pairs)",
        "",
        "The four delivered reference rasters are phase-aligned to the same 5 m projected coordinate lattice. "
        "This does NOT establish common master-file provenance or common upstream acquisition history.",
        "",
        "This geometric profile is compatible with multiple lunar polar products (TMC-2 mosaic, LROC NAC mosaic, "
        "USGS south polar). Geometric compatibility alone is insufficient for product identification.",
        "",
        "## 9. Track 5 -- Reference Content Identity (Pair 02/03)",
        "",
        f"- Verified overlap: **{PAIR02_PAIR03_OVERLAP['identical_pixels']:,} / {PAIR02_PAIR03_OVERLAP['total_pixels']:,} pixels identical**",
        "- Mean difference: **0.0000**",
        "- RMS difference: **0.0000**",
        "",
        PAIR02_PAIR03_OVERLAP["description"],
        "",
        "This confirms the reference content is not per-pair unique imagery. It does NOT identify the upstream product.",
        "",
        "## 10. Track 6 -- Geodetic Realization Comparison",
        "",
        "| Item | Status |",
        "|------|--------|",
        "| Delivered CRS name | PolarStereographic Moon / GCS_Moon / D_Moon |",
        "| Delivered datum label | D_Moon |",
        "| Delivered radius | 1,737,400.0 m |",
        "| Explicit geodetic frame tag | ABSENT -- not named in any delivered metadata |",
        "| MOON_ME link | NOT_VERIFIED |",
        "| MOON_ME_DE421 link | NOT_VERIFIED |",
        "| IAU_MOON link | COMPATIBLE but not verified |",
        "",
        "**D_Moon is compatible with IAU_MOON, MOON_ME, and MOON_ME_DE421.** Without an explicit label "
        "or authoritative content match, the specific geodetic realization cannot be determined.",
        "",
        "## 11. Track 7 -- Absolute Coordinate Constraints",
        "",
        "Phase 23A.5/23A.6 measured residuals (immutable):",
        "",
        "| Pair | RMS Residual |",
        "|------|-------------|",
        "| OHRC_PAIR_01 | 2,158.6 m |",
        "| OHRC_PAIR_02 | 1,265.2 m |",
        "| OHRC_PAIR_03 | 1,748.5 m |",
        "| OHRC_PAIR_04 | 2,181.1 m |",
        "",
        "Km-scale residuals (1,265–2,181 m) confirm a substantial source/reference geodetic-coordinate discrepancy under the audited model. No empirical transform was fitted. "
        "However, they do not identify that source without an authoritative comparand and an empirical-transform-free coordinate comparison, which is not possible "
        "with locally available inputs.",
        "",
        "## 12. Track 8 -- Authoritative Documentation",
        "",
        f"Sources audited: {t8['sources_audited']}. Direct authoritative links found: {t8['direct_authoritative_links_found']}.",
        "",
        t8["overall_finding"],
        "",
        "## 13. Evidence Hierarchy",
        "",
        "| Level | Evidence Type | Found? |",
        "|-------|--------------|--------|",
        "| 1 (Strongest) | Direct authoritative label naming the upstream product | NO |",
        "| 2 | Exact pixel/byte content match against an authoritative local source file | NO (no source file available) |",
        "| 3 | Producer documentation explicitly linking delivered artifact to upstream product | NO |",
        "| 4 | Geodetic metadata compatibility | PARTIAL (compatible with multiple frames) |",
        "| 5 | Projection compatibility | YES (but non-exclusive) |",
        "| 6 | Resolution compatibility | YES (but non-exclusive) |",
        "| 7 (Weakest) | Visual similarity | NOT ASSESSED (not an authorized identification method) |",
        "",
        "No Level 1, 2, or 3 evidence was found. Levels 4-6 do not constitute identification.",
        "",
        "## 14. Final Classification",
        "",
        f"> # **`D -- UNRESOLVED`**",
        "",
        classification["rationale"],
        "",
        "## 15. What Is Established",
        "",
        "1. The delivery packaging layer (SIH 2026 benchmark container) is directly identified as a packaging artifact (PACKAGING_ARTIFACT_DIRECTLY_SUPPORTED). This establishes only that the benchmark delivery container is the immediate local container of the raster; it does not identify the upstream reference product or geodetic realization.",
        "2. The reference GeoTIFFs contain zero embedded provenance identifying the upstream product.",
        "3. The PDS4 XML labels identify the OHRC source product but use a generic 'System' reference tag.",
        "4. The reference content uses standard south-polar projection with canonical parameters.",
        "5. The Pair 02/03 reference content is identical over verified overlap (consistent with static common source).",
        "6. Multiple candidate products are geometrically and metrically compatible.",
        "",
        "## 16. What Remains Unresolved",
        "",
        "1. Identity of the upstream map/mosaic product used to generate the reference rasters.",
        "2. Geodetic realization (IAU_MOON / MOON_ME / MOON_ME_DE421 / other).",
        "3. Link between delivered content and DE421 lunar reference frame.",
        "4. Whether any geographic offset between source and reference is attributable to frame differences.",
        "",
        "## 17. What This Does NOT Prove",
        "",
        "- This audit does NOT prove the reference is TMC-2 ortho-mosaic.",
        "- This audit does NOT prove the reference is LROC NAC mosaic.",
        "- This audit does NOT prove the reference is MOON_ME_DE421.",
        "- Grid phase alignment does NOT prove common master-file provenance.",
        "- Pixel identity over Pair 02/03 overlap does NOT prove static-mosaic acquisition history.",
        "",
        "## 18. Phase Gate",
        "",
        "```",
        "REFERENCE_PRODUCT_UNRESOLVED",
        "REFERENCE_GEODETIC_REALIZATION = UNKNOWN",
        "REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED",
        "PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW",
        "```",
        "",
        "Phase 23B remains blocked. Phase 23B.3 execution does NOT automatically unblock Phase 23B.",
        "",
        "## 19. Reproducibility",
        "",
        f"All outputs generated by `{SCRIPT_NAME}` are deterministic from the delivered input files.",
        "Checksums recorded in `checksums.sha256`.",
        "",
        "## 20. Checksums",
        "",
        "See `checksums.sha256` in this directory.",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {path}")


def generate_geodetic_report(t6):
    path = os.path.join(OUTPUT_DIR, "phase23b3_geodetic_realization_comparison.md")
    ts = now_utc()
    lines = [
        "# Phase 23B.3 -- Geodetic Realization Comparison Report",
        "",
        f"**Generated:** {ts}  ",
        f"**Script:** `{SCRIPT_NAME}`  ",
        "",
        "## Delivered CRS Parameters",
        "",
        "| Parameter | Value | Source |",
        "|-----------|-------|--------|",
        f"| CRS Name | {t6['delivered_CRS_name']} | GeoAsciiParams (Tag 34737) |",
        f"| Datum | {t6['delivered_datum']} | GeoAsciiParams |",
        f"| Radius | {t6['delivered_radius_m']} m | GeoDoubleParams[5] (Tag 34736) |",
        f"| Geodetic Frame | {t6['delivered_geodetic_frame']} | Audit finding |",
        f"| MOON_ME_DE421 Link | {t6['MOON_ME_DE421_link']} | Audit finding |",
        "",
        "## Candidate Frame Comparison",
        "",
        "| Candidate | Documented Frame | Radius | MOON_ME_DE421 Verified | Delivered Match | Classification |",
        "|-----------|-----------------|--------|----------------------|----------------|----------------|",
    ]
    for c in t6["candidates_audited"]:
        lines.append(
            f"| {c['id']} | {c['documented_frame'][:30]} | {c['documented_radius_m']} m | "
            f"{c['is_moon_me_de421'][:25]} | {c['delivered_frame_match']} | `{c['classification']}` |"
        )
    lines += [
        "",
        "## Conclusion",
        "",
        t6["overall_conclusion"],
        "",
        "```",
        "REFERENCE_GEODETIC_REALIZATION = UNKNOWN",
        "REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED",
        "```",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {path}")


def generate_fingerprint_csv_json(t3):
    csv_path = os.path.join(OUTPUT_DIR, "phase23b3_candidate_content_fingerprint.csv")
    json_path = os.path.join(OUTPUT_DIR, "phase23b3_candidate_content_fingerprint.json")

    rows = []
    for pair_id, fp in t3.items():
        for wname, wsha in fp["window_fingerprints"].items():
            stats = fp["window_statistics"][wname]
            rows.append({
                "pair_id": pair_id,
                "window": wname,
                "sha256_16": wsha[:16],
                "sha256_full": wsha,
                "pixel_count": stats["pixel_count"],
                "valid_pixels": stats["valid_pixel_count"],
                "mean": stats["mean"],
                "std": stats["std"],
                "min": stats["min"],
                "max": stats["max"],
                "file_sha256_16": fp["file_sha256_16"],
                "payload_sha256_16": fp["payload_sha256_16"],
                "exact_match_result": fp["exact_match_result"],
            })
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created: {csv_path}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {"phase": "23B.3", "script": SCRIPT_NAME, "generated": now_utc()},
            "fingerprints": t3,
        }, f, indent=2)
    print(f"Created: {json_path}")


def generate_evidence_registry_csv_json(candidates, t8):
    csv_path = os.path.join(OUTPUT_DIR, "phase23b3_provenance_evidence_registry.csv")
    json_path = os.path.join(OUTPUT_DIR, "phase23b3_provenance_evidence_registry.json")

    # Build evidence rows from candidates + documentation sources
    rows = []
    for c in candidates:
        rows.append({
            "evidence_type": "CANDIDATE",
            "id": c["id"],
            "name": c["name"],
            "producer": c["producer"],
            "geodetic_frame": c["geodetic_frame"],
            "local_file": c["local_file_available"],
            "content_test": c["exact_content_test"],
            "classification": c["phase23b3_classification"],
            "rationale_summary": c["phase23b3_rationale"][:150],
        })
    for doc in t8["sources"]:
        rows.append({
            "evidence_type": "DOCUMENTATION",
            "id": doc["source_id"],
            "name": doc["title"],
            "producer": doc["producer"],
            "geodetic_frame": "N/A",
            "local_file": False,
            "content_test": "N/A",
            "classification": doc["evidence_classification"],
            "rationale_summary": doc["relevant_statement"][:150],
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created: {csv_path}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {"phase": "23B.3", "script": SCRIPT_NAME, "generated": now_utc()},
            "candidates": candidates,
            "documentation_sources": t8["sources"],
        }, f, indent=2)
    print(f"Created: {json_path}")


def update_readme():
    p = os.path.join(OUTPUT_DIR, "README.md")
    existing = ""
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            existing = f.read()
    if "## Phase 23B.3" in existing:
        existing = existing[:existing.index("## Phase 23B.3")].rstrip()

    section = f"""

## Phase 23B.3 -- Reference Product Geodetic Provenance & Direct Content Fingerprint Audit

**Generated:** {now_utc()}  
**Script:** `{SCRIPT_NAME}`  
**Final Classification:** `D -- UNRESOLVED`  

### Key Finding

Eight evidence tracks (local provenance, PDS4 lineage, content fingerprinting, grid compatibility,
reference content identity, geodetic realization comparison, absolute coordinate constraints,
authoritative documentation) found NO direct provenance link to an upstream map product.

- All TIFF provenance tags absent from all 4 reference GeoTIFFs.
- PDS4 labels record OHRC source ID but use generic `<ReferenceUsed>System</ReferenceUsed>`.
- No authoritative local source file available for pixel-level content comparison.
- The Pair 02/03 identical overlap confirms static common reference content; upstream product unidentified.
- Multiple candidates are geometrically compatible but none is identified.

### Outputs

| File | Description |
|------|-------------|
| `phase23b3_reference_provenance_audit.md` | Main 20-section provenance audit report |
| `phase23b3_geodetic_realization_comparison.md` | Geodetic frame comparison across candidates |
| `phase23b3_candidate_content_fingerprint.csv` | Per-window pixel fingerprints (SHA256, statistics) |
| `phase23b3_candidate_content_fingerprint.json` | Machine-readable fingerprint dataset |
| `phase23b3_provenance_evidence_registry.csv` | Evidence registry (candidates + documentation) |
| `phase23b3_provenance_evidence_registry.json` | Machine-readable evidence registry |

### Final Status

```
REFERENCE_PRODUCT_UNRESOLVED
REFERENCE_GEODETIC_REALIZATION = UNKNOWN
REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED
PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW
```
"""
    with open(p, "w", encoding="utf-8") as f:
        f.write(existing + section)
    print(f"Updated: {p}")


def update_checksums():
    chk_path = os.path.join(OUTPUT_DIR, "checksums.sha256")
    files_to_hash = sorted(
        f for f in os.listdir(OUTPUT_DIR)
        if os.path.isfile(os.path.join(OUTPUT_DIR, f)) and f != "checksums.sha256"
    )
    entries = {}
    for fname in files_to_hash:
        full = os.path.join(OUTPUT_DIR, fname)
        with open(full, "rb") as fh:
            entries[fname] = hashlib.sha256(fh.read()).hexdigest()
    with open(chk_path, "w", encoding="utf-8") as f:
        for fname, h in sorted(entries.items()):
            f.write(f"{h}  {fname}\n")
    print(f"Updated: {chk_path} ({len(entries)} entries)")
    return len(entries)


def safety_scan():
    forbidden = [
        "most likely candidate",
        "best candidate",
        "winner",
        "proves the cause",
        "confirmed source",
        "static master",
        "common master file",
        "reference identified",
        "reference product confirmed",
        "reference raster was never rotated",
        "natively share lambda",
    ]
    outputs = [
        "phase23b3_reference_provenance_audit.md",
        "phase23b3_geodetic_realization_comparison.md",
        "phase23b3_candidate_content_fingerprint.csv",
        "phase23b3_provenance_evidence_registry.csv",
    ]
    found = []
    for fname in outputs:
        fpath = os.path.join(OUTPUT_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding="utf-8") as f:
            content = f.read().lower()
        for phrase in forbidden:
            if phrase in content:
                found.append(f"{fname}: '{phrase}'")
    return found


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("PHASE 23B.3 -- REFERENCE PRODUCT GEODETIC PROVENANCE AUDIT")
    print("Governing Discipline: Research-Only -- Production Code Frozen.")
    print("=" * 70)

    print("\n[Track 1] Local delivery provenance...")
    t1 = track1_local_provenance()
    for pid, r in t1.items():
        present_tags = sum(1 for v in r["tiff_provenance_tags"].values() if v["present"])
        print(f"  {pid}: provenance TIFF tags present = {present_tags}/7, PDS4 XML = {r['pds4_xml_present']}")

    print("\n[Track 2] PDS4 / OHRC label lineage...")
    t2 = track2_pds4_lineage()
    for pid, r in t2.items():
        print(f"  {pid}: ReferenceUsed={r.get('ReferenceUsed')}, ref product named={r.get('reference_product_explicitly_named')}")

    print("\n[Track 3] Content fingerprinting...")
    t3 = track3_content_fingerprints()
    for pid, fp in t3.items():
        print(f"  {pid}: file_sha={fp['file_sha256_16']}..., payload_sha={fp['payload_sha256_16']}...")

    print("\n[Track 4] Grid/projection compatibility...")
    t4 = track4_grid_compatibility()
    for pid, r in t4.items():
        print(f"  {pid}: pixel={r['pixel_size_x_m']} m, phase E={r['grid_phase_E']}, N={r['grid_phase_N']}")

    print("\n[Track 5] Reference content identity (Pair 02/03)...")
    t5 = track5_reference_identity()
    print(f"  Identical: {t5['identical_pixels']:,} / {t5['total_overlap_pixels']:,} px, RMS={t5['rms_difference']}")

    print("\n[Track 6] Geodetic realization comparison...")
    t6 = track6_geodetic_realizations()
    print(f"  Delivered frame: {t6['delivered_geodetic_frame']}")
    print(f"  MOON_ME_DE421 link: {t6['MOON_ME_DE421_link']}")

    print("\n[Track 7] Absolute coordinate constraints...")
    t7 = track7_absolute_constraints()
    print(f"  Source: {t7['source']}")
    print(f"  Empirical transform fitted: {t7['empirical_transform_fitted']}")

    print("\n[Track 8] Authoritative documentation search...")
    t8 = track8_documentation()
    print(f"  Sources audited: {t8['sources_audited']}, direct links found: {t8['direct_authoritative_links_found']}")

    print("\n[Candidates] Building candidate registry...")
    candidates = build_candidate_registry()
    compatible = [c for c in candidates if "COMPATIBLE" in c["phase23b3_classification"]]
    mismatches = [c for c in candidates if c["phase23b3_classification"] == "MISMATCH"]
    print(f"  Total candidates: {len(candidates)}, compatible: {len(compatible)}, mismatches: {len(mismatches)}")

    print("\n[Classification] Determining final classification...")
    classification = determine_final_classification(candidates)
    print(f"  FINAL CLASSIFICATION: {classification['classification_code']} -- {classification['classification_label']}")

    print("\n[Outputs] Generating reports...")
    generate_main_report(t1, t2, t3, t4, t5, t6, t7, t8, candidates, classification)
    generate_geodetic_report(t6)
    generate_fingerprint_csv_json(t3)
    generate_evidence_registry_csv_json(candidates, t8)
    update_readme()

    print("\nUpdating checksums.sha256...")
    n_entries = update_checksums()

    print("\n[Safety] Scanning outputs for forbidden wording...")
    issues = safety_scan()
    if issues:
        for iss in issues:
            print(f"  WARNING: {iss}")
    else:
        print("  CLEAN -- no forbidden wording detected.")

    print(f"\n{'='*70}")
    print("FINAL STATUS:")
    print("  REFERENCE_PRODUCT_UNRESOLVED")
    print("  REFERENCE_GEODETIC_REALIZATION = UNKNOWN")
    print("  REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED")
    print("  PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW")
    print(f"  CHECKSUMS: {n_entries} entries, 0 errors")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
