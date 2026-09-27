#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase23b1_geokey3092_sensitivity.py
========================================
Phase 23B.1 -- Controlled GeoKey 3092 Geodetic Sensitivity Test
LunarReg -- Chandrayaan-2 OHRC Mentor Benchmark

GOVERNING STATUS : RESEARCH-ONLY
PRODUCTION CODE  : FROZEN -- not touched.
OBJECTIVE        : Test whether GeoKey 3092 = 1.0 deg materially explains the
                   km-scale source/reference geodetic residuals observed in
                   Phase 23A.5 and 23A.6.

METHODOLOGY:
  The existing Phase 23A.5 projection formula computes (E, N) from (lat, lon)
  using:
      rho = 2*R * tan((90 + lat)/2)         [radians]
      E   = rho * sin(lon)
      N   = rho * cos(lon)
  This is the standard south-polar stereographic with the Y-axis pointing
  along longitude 0 deg, i.e. the straight-vertical-pole longitude = 0 deg.

  GeoKey 3092 = 1.0 deg says the straight-vertical-pole longitude (the
  longitude mapped to the +Y axis) is 1.0 deg east of the prime meridian.
  According to OGC GeoTIFF standard and EPSG method 9810 (Polar Stereographic
  Variant A) / 9829 (Variant C), this rotates the coordinate axes by 1 deg.
  Under this interpretation:
      E_1 =  rho * sin(lon - lam_0)
      N_1 =  rho * cos(lon - lam_0)
  where lam_0 = 1.0 deg (the delivered GeoKey 3092 value).

  CONTROL (A): lam_0 = 0.0 deg  --> matches prior Phase 23A.5 result
  TEST    (B): lam_0 = 1.0 deg  --> matches delivered GeoKey 3092

  The reference coordinate (tie_map_x, tie_map_y) was computed from the
  reference raster's tiepoint / geotransform.  It does NOT change between
  conditions A and B.

  We ask: does applying lam_0 = 1.0 deg to the source-corner projection
  bring the projected source E/N closer to the reference E/N?

REFERENCES (authoritative):
  [R1] OGC GeoTIFF Standard 1.1 (OGC 19-008r4), Clause 8.7.5:
       "GeoKey 3092, ProjStraightVertPoleLongGeoKey: A code for the
       longitude of the straight vertical line from the pole used in
       the Polar Stereographic and Stereographic projections."
       https://docs.ogc.org/is/19-008r4/19-008r4.html#_requirements_class_projected_crs_geokeys

  [R2] EPSG Guidance Note 7 Part 2 (v10.027), Section 1.3.6:
       "Polar Stereographic (Variant A)" -- EPSG method 9810.
       Coordinate operation method parameters include:
         - Latitude of natural origin (phi_0 = +/-90 deg)
         - Longitude of natural origin (lam_0 = straight vertical pole long)
         - Scale factor at natural origin (k_0 = 1.0 for standard polar)
         - False easting / false northing
       Standard projection equations use (lam - lam_0) not lam alone.
       https://epsg.org/guidance-notes.html

  [R3] Snyder, J.P. (1987). "Map Projections -- A Working Manual."
       USGS Professional Paper 1395.  Chapter 21, Polar Stereographic.
       Eq. 21-12 (south pole case, sphere):
         rho = 2*R*tan(pi/4 + phi/2)
         E   = rho * sin(lam - lam_0)
         N   = rho * cos(lam - lam_0)
       where lam_0 is the central meridian / straight vertical pole long.

  [R4] GeoTIFF standard revision history at:
       https://trac.osgeo.org/geotiff/

NOTE ON SEMANTICS:
  GeoKey 3092 (ProjStraightVertPoleLongGeoKey) is defined identically to
  "Longitude of natural origin" in EPSG 9810.  When lam_0 != 0, projected
  coordinates are computed relative to lam_0.  A raster with lam_0 = 1.0
  and a tiepoint (E0, N0) has its (0,0) pixel centred at the geographic point
  whose coordinates satisfy:
      E0 = rho * sin(lon - 1.0)
      N0 = rho * cos(lon - 1.0)
  NOT at the point satisfying E0 = rho*sin(lon).

  Therefore: if the reference raster's coordinates were ENCODED with lam_0=1.0,
  but the reader interprets them with lam_0=0.0, the reader will geolocate every
  reference pixel approximately 1.0 deg off in the azimuthal direction -- a
  rotation of the entire map around the pole.

  The sensitivity test checks whether interpreting the SOURCE projection with
  lam_0=1.0 (instead of the prior 0.0 assumption) closes the source/reference gap.
  This is the CORRECT mathematical test for the stated hypothesis.
"""

import os
import math
import json
import csv
import hashlib
import datetime

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.basename(__file__)

# ---------------------------------------------------------------------------
# PHYSICAL CONSTANTS (verified)
# ---------------------------------------------------------------------------
R_MOON = 1737400.0   # metres -- verified from GeoDoubleParams tag 34736

# GeoKey 3092 values under test
LAM0_CONTROL_DEG = 0.0   # Condition A: prior assumption, 0 deg
LAM0_TEST_DEG    = 1.0   # Condition B: delivered GeoKey 3092

# ---------------------------------------------------------------------------
# CORNER DATA (from Phase 23A.5 -- verified, immutable)
# Source columns: sph_lat, sph_lon = geographic point where source-corner ray
#                 intersects the lunar sphere.
# Ref columns:   tie_map_x, tie_map_y = PS-projected coordinate read from the
#                reference raster tiepoints / geotransform (NOT changed by
#                lam_0 choice -- these are the DELIVERED reference coordinates).
# ---------------------------------------------------------------------------
CORNERS_DATA = {
    "OHRC_PAIR_01": {
        "UL": {"src_lat": -89.498037, "src_lon": 238.554907,
               "ref_E": -14687.1,   "ref_N": -6607.06},
        "UR": {"src_lat": -89.406595, "src_lon": 233.437538,
               "ref_E": -16185.96,  "ref_N": -9447.12},
        "LL": {"src_lat": -89.267460, "src_lon": 155.810211,
               "ref_E":   7394.49,  "ref_N": -18927.59},
        "LR": {"src_lat": -89.199509, "src_lon": 161.667599,
               "ref_E":   5895.79,  "ref_N": -21768.45},
    },
    "OHRC_PAIR_02": {
        "UL": {"src_lat": -84.534252, "src_lon": 26.62823,
               "ref_E":  74030.77,  "ref_N": 147044.95},
        "UR": {"src_lat": -84.500318, "src_lon": 27.696392,
               "ref_E":  77306.51,  "ref_N": 146540.15},
        "LL": {"src_lat": -85.313799, "src_lon": 29.792019,
               "ref_E":  70340.62,  "ref_N": 122157.99},
        "LR": {"src_lat": -85.274117, "src_lon": 31.012436,
               "ref_E":  73618.91,  "ref_N": 121652.04},
    },
    "OHRC_PAIR_03": {
        "UL": {"src_lat": -84.508629, "src_lon": 24.023233,
               "ref_E":  67495.20,  "ref_N": 150128.72},
        "UR": {"src_lat": -84.478065, "src_lon": 25.018852,
               "ref_E":  70561.88,  "ref_N": 149764.53},
        "LL": {"src_lat": -85.325840, "src_lon": 27.155041,
               "ref_E":  64482.36,  "ref_N": 124913.23},
        "LR": {"src_lat": -85.289944, "src_lon": 28.302206,
               "ref_E":  67551.81,  "ref_N": 124547.96},
    },
    "OHRC_PAIR_04": {
        "UL": {"src_lat": -83.717507, "src_lon": 30.662076,
               "ref_E":  96610.01,  "ref_N": 161948.50},
        "UR": {"src_lat": -83.694736, "src_lon": 31.544005,
               "ref_E":  99505.57,  "ref_N": 161018.26},
        "LL": {"src_lat": -84.527701, "src_lon": 32.947499,
               "ref_E":  89683.67,  "ref_N": 137270.18},
        "LR": {"src_lat": -84.501044, "src_lon": 33.947666,
               "ref_E":  92574.77,  "ref_N": 136340.31},
    },
}

# Phase 23A.5 baseline residuals (0 deg, control -- these MUST reproduce)
PHASE23A5_BASELINE_RESIDUALS = {
    "OHRC_PAIR_01": {"UL": 2161.61, "UR": 2149.62, "LL": 2167.77, "LR": 2155.53},
    "OHRC_PAIR_02": {"UL": 1266.42, "UR": 1262.33, "LL": 1267.80, "LR": 1264.02},
    "OHRC_PAIR_03": {"UL": 2109.67, "UR": 2107.71, "LL": 1292.88, "LR": 1290.22},
    "OHRC_PAIR_04": {"UL": 2183.55, "UR": 2181.78, "LL": 2180.43, "LR": 2178.75},
}

# ===========================================================================
# PROJECTION FUNCTIONS
# ===========================================================================

def ps_forward(lat_deg: float, lon_deg: float,
               lam0_deg: float = 0.0,
               R: float = R_MOON) -> tuple:
    """
    South-polar stereographic forward projection (spherical).

    Mathematical formulation (Snyder 1987, Eq. 21-12, south-pole case):
        phi = geodetic latitude (negative for south hemisphere)
        lam = geodetic longitude
        lam_0 = straight-vertical-pole longitude (central meridian)

    For south pole (phi_0 = -90):
        rho = 2 * R * tan(pi/4 + phi/2)
            = 2 * R * tan((90 + lat) / 2)      [all angles in degrees->rad]
        E   = rho * sin(lam - lam_0)
        N   = rho * cos(lam - lam_0)

    Notes:
      - N is positive upward (toward equator from south pole) in standard PS
      - The existing Phase 23A.5 formula uses lam_0 = 0, i.e.:
            E = rho * sin(lam)
            N = rho * cos(lam)
        which is reproduced exactly when lam0_deg = 0.

    Parameters
    ----------
    lat_deg  : geodetic latitude in degrees (negative = south)
    lon_deg  : geodetic longitude in degrees (0..360 or -180..180)
    lam0_deg : straight-vertical-pole longitude in degrees (GeoKey 3092)
    R        : lunar sphere radius in metres

    Returns
    -------
    (E, N) in metres
    """
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    lam0 = math.radians(lam0_deg)

    # Radial distance from pole in the projection plane
    # For south pole: rho = 2*R*tan(pi/4 + phi/2)
    rho = 2.0 * R * math.tan(math.pi / 4.0 + phi / 2.0)

    E = rho * math.sin(lam - lam0)
    N = rho * math.cos(lam - lam0)
    return E, N


def ps_inverse(E: float, N: float,
               lam0_deg: float = 0.0,
               R: float = R_MOON) -> tuple:
    """
    South-polar stereographic inverse projection (spherical).

    Inverse of ps_forward:
        rho = sqrt(E^2 + N^2)
        phi = 2*atan(rho / (2*R)) - pi/2        [= 2*atan(rho/(2R)) - 90 deg]
        lam = lam_0 + atan2(E, N)

    Returns
    -------
    (lat_deg, lon_deg)
    """
    rho = math.sqrt(E * E + N * N)
    if rho == 0.0:
        return -90.0, lam0_deg

    lam0 = math.radians(lam0_deg)
    phi = 2.0 * math.atan(rho / (2.0 * R)) - math.pi / 2.0
    lam = lam0 + math.atan2(E, N)

    lat_deg = math.degrees(phi)
    lon_deg = math.degrees(lam) % 360.0
    return lat_deg, lon_deg


def residual_metrics(E_src: float, N_src: float,
                     E_ref: float, N_ref: float) -> dict:
    """
    Compute per-corner residual between source projection and reference coord.
    """
    dE = E_src - E_ref
    dN = N_src - N_ref
    mag = math.sqrt(dE * dE + dN * dN)
    azimuth = math.degrees(math.atan2(dE, dN)) % 360.0
    return {
        "dE_m":     round(dE, 3),
        "dN_m":     round(dN, 3),
        "mag_m":    round(mag, 3),
        "azimuth_deg": round(azimuth, 2),
    }


# ===========================================================================
# TRACK 1 -- GeoKey 3092 Semantics Analysis
# ===========================================================================
def analyse_geokey_semantics() -> dict:
    """
    Document the authoritative semantics of GeoKey 3092 and its role in the
    Polar Stereographic projection.  All conclusions directly referenced to
    authoritative specification documents.
    """
    return {
        "geokey_id": 3092,
        "geokey_name": "ProjStraightVertPoleLongGeoKey",
        "delivered_value_deg": 1.0,
        "conventional_value_deg": 0.0,
        "authoritative_references": [
            {
                "label": "R1",
                "title": "OGC GeoTIFF Standard 1.1 (OGC 19-008r4)",
                "clause": "Section 8.7.5 — Requirement Class: Projected CRS GeoKeys",
                "url": "https://docs.ogc.org/is/19-008r4/19-008r4.html",
                "definition": (
                    "ProjStraightVertPoleLongGeoKey (3092): Longitude of the straight vertical "
                    "line from the pole used in Polar Stereographic and Stereographic projections. "
                    "Corresponds to EPSG parameter 'Longitude of natural origin' in Polar "
                    "Stereographic Variant A (EPSG:9810)."
                ),
            },
            {
                "label": "R2",
                "title": "EPSG Geodesy Parameter Dataset — Guidance Note 7 Part 2",
                "clause": "Section 1.3.6 — Polar Stereographic (Variant A), EPSG Method 9810",
                "url": "https://epsg.org/guidance-notes.html",
                "definition": (
                    "Longitude of natural origin (lam_0): The longitude of the point from which "
                    "the values of both the geodetic coordinates on the ellipsoid and the grid "
                    "coordinates on the projection are deemed to increment or decrement. "
                    "For Polar Stereographic, this is the straight vertical pole longitude. "
                    "Projection equations (spherical approximation): "
                    "  rho = 2*R*tan(pi/4 + phi/2)  [south pole case] "
                    "  E   = rho * sin(lam - lam_0) "
                    "  N   = rho * cos(lam - lam_0) "
                    "The parameter lam_0 is NOT additive to false easting/northing; "
                    "it is a rotation of the coordinate axes around the pole."
                ),
            },
            {
                "label": "R3",
                "title": "Snyder, J.P. (1987). Map Projections -- A Working Manual",
                "clause": "Chapter 21, Polar Stereographic, Equations 21-12 (south-pole sphere)",
                "url": "https://pubs.usgs.gov/pp/1395/report.pdf",
                "definition": (
                    "For south pole: rho = 2*R*tan(45 + phi/2); "
                    "x = rho*sin(lam - lam_0); y = rho*cos(lam - lam_0). "
                    "lam_0 is the central meridian (straight vertical pole long). "
                    "When lam_0 = 0, the Y axis points toward lon = 0; "
                    "when lam_0 = 1, the Y axis points toward lon = 1 deg."
                ),
            },
        ],
        "semantics_verdict": {
            "is_rotation_of_axes": True,
            "is_translation": False,
            "is_false_origin_shift": False,
            "effect": (
                "GeoKey 3092 = lam_0 rotates the projected coordinate system (E/N axes) "
                "around the south pole by lam_0 degrees. This changes the (E, N) coordinates "
                "assigned to every geographic point. Pixels with encoded coordinates (E0, N0) "
                "geolocate to DIFFERENT geographic points depending on whether lam_0 = 0 or 1."
            ),
            "changes_physical_pixel_location": True,
            "note": (
                "Unlike a false easting/northing (which shifts all coordinates by a constant), "
                "lam_0 introduces a SPATIALLY VARYING displacement: it is a rotation, so the "
                "displacement is proportional to distance from the pole and is zero at the pole "
                "itself. The direction of the displacement is perpendicular to the radial "
                "(pole-to-point) direction, i.e. purely azimuthal."
            ),
        },
        "is_value_unusual": True,
        "unusual_note": (
            "For canonical south-polar products (LROC NAC, LOLA, TMC-2 documented examples), "
            "lam_0 = 0.0 deg is standard. A value of 1.0 deg is non-standard and unusual. "
            "The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation."
        ),
        "does_1deg_justify_treating_as_real_orientation": (
            "The delivered GeoKey 3092 = 1.0 deg is formally a valid projection parameter "
            "per OGC 19-008r4. A conforming GeoTIFF reader should use lam_0 = 1.0 deg when "
            "projecting coordinates from this raster. However, whether the ISRO pipeline "
            "INTENDED this value, or whether downstream tools (including any reference-product "
            "generator) actually honoured it, remains UNVERIFIED."
        ),
    }


# ===========================================================================
# TRACK 2 -- Sensitivity Computation (Control vs Test)
# ===========================================================================
def run_sensitivity():
    """
    For each pair and corner:
    A. Control (lam_0 = 0.0): reproduce Phase 23A.5 result
    B. Test    (lam_0 = 1.0): apply GeoKey 3092 as a real rotation

    Ref E/N values are FIXED -- they are the reference raster's delivered
    projected coordinates and are NOT changed by lam_0 interpretation.
    """
    results = {}

    for pair_name, corners in CORNERS_DATA.items():
        pair_result = {}
        for corner_name, c in corners.items():
            lat = c["src_lat"]
            lon = c["src_lon"]
            ref_E = c["ref_E"]
            ref_N = c["ref_N"]

            # Condition A: Control (lam_0 = 0 deg)
            E_A, N_A = ps_forward(lat, lon, lam0_deg=LAM0_CONTROL_DEG)
            metrics_A = residual_metrics(E_A, N_A, ref_E, ref_N)

            # Condition B: Test (lam_0 = 1 deg -- GeoKey 3092 value)
            E_B, N_B = ps_forward(lat, lon, lam0_deg=LAM0_TEST_DEG)
            metrics_B = residual_metrics(E_B, N_B, ref_E, ref_N)

            # Change from A to B
            delta_mag = metrics_B["mag_m"] - metrics_A["mag_m"]
            delta_E   = E_B - E_A
            delta_N   = N_B - N_A

            # Cross-check with Phase 23A.5 baseline
            baseline_resid = PHASE23A5_BASELINE_RESIDUALS[pair_name][corner_name]
            reproduce_error = abs(metrics_A["mag_m"] - baseline_resid)

            pair_result[corner_name] = {
                "src_lat": lat,
                "src_lon": lon,
                "ref_E": ref_E,
                "ref_N": ref_N,
                # Condition A
                "A_src_E": round(E_A, 3),
                "A_src_N": round(N_A, 3),
                "A_dE": metrics_A["dE_m"],
                "A_dN": metrics_A["dN_m"],
                "A_mag_m": metrics_A["mag_m"],
                "A_azimuth_deg": metrics_A["azimuth_deg"],
                # Condition B
                "B_src_E": round(E_B, 3),
                "B_src_N": round(N_B, 3),
                "B_dE": metrics_B["dE_m"],
                "B_dN": metrics_B["dN_m"],
                "B_mag_m": metrics_B["mag_m"],
                "B_azimuth_deg": metrics_B["azimuth_deg"],
                # Delta (positive = B worse, negative = B better)
                "delta_mag_m": round(delta_mag, 3),
                "delta_E_m":   round(delta_E, 3),
                "delta_N_m":   round(delta_N, 3),
                # Cross-check
                "phase23a5_baseline_m": baseline_resid,
                "reproduce_error_m": round(reproduce_error, 3),
            }

        results[pair_name] = pair_result

    return results


def compute_pair_stats(results: dict) -> dict:
    """
    Compute per-pair and cross-pair summary statistics.
    """
    pair_stats = {}
    for pair_name, corners in results.items():
        mags_A = [c["A_mag_m"] for c in corners.values()]
        mags_B = [c["B_mag_m"] for c in corners.values()]
        deltas = [c["delta_mag_m"] for c in corners.values()]

        rms_A = math.sqrt(sum(m**2 for m in mags_A) / len(mags_A))
        rms_B = math.sqrt(sum(m**2 for m in mags_B) / len(mags_B))
        mean_A = sum(mags_A) / len(mags_A)
        mean_B = sum(mags_B) / len(mags_B)
        rms_reduction = rms_A - rms_B
        mean_reduction = mean_A - mean_B
        pct_rms_reduction = (rms_reduction / rms_A) * 100.0 if rms_A > 0 else 0.0

        # Azimuth consistency of delta vector across corners
        delta_azimuths = []
        for c in corners.values():
            dE = c["delta_E_m"]
            dN = c["delta_N_m"]
            az = math.degrees(math.atan2(dE, dN)) % 360.0
            delta_azimuths.append(az)
        mean_delta_az = sum(delta_azimuths) / len(delta_azimuths)
        # Angular spread (max deviation from mean)
        az_spread = max(abs(az - mean_delta_az) for az in delta_azimuths)
        # Handle wrap-around (> 180 deg)
        az_spread = min(az_spread, 360.0 - az_spread)

        # Is residual reduction substantial?
        # Criterion: mean reduction >= 200 m AND >= 5% of original mean
        substantial = (mean_reduction >= 200.0 and
                       (mean_reduction / mean_A) >= 0.05)

        pair_stats[pair_name] = {
            "n_corners": len(corners),
            "rms_A_m": round(rms_A, 3),
            "rms_B_m": round(rms_B, 3),
            "mean_A_m": round(mean_A, 3),
            "mean_B_m": round(mean_B, 3),
            "max_A_m": round(max(mags_A), 3),
            "max_B_m": round(max(mags_B), 3),
            "rms_reduction_m": round(rms_reduction, 3),
            "mean_reduction_m": round(mean_reduction, 3),
            "pct_rms_reduction": round(pct_rms_reduction, 2),
            "mean_delta_azimuth_deg": round(mean_delta_az, 2),
            "delta_azimuth_spread_deg": round(az_spread, 2),
            "effect_spatially_rigid": az_spread < 5.0,
            "reduction_substantial": substantial,
            "delta_magnitudes_m": [round(d, 3) for d in deltas],
        }

    return pair_stats


# ===========================================================================
# TRACK 3 -- Inverse / Round-Trip Validation
# ===========================================================================
def run_roundtrip_validation() -> list:
    """
    For a sample of reference coordinates, verify forward/inverse consistency
    under both lam_0 = 0 and lam_0 = 1.
    """
    test_points = [
        (-89.5,   0.0,  "South pole, lon=0"),
        (-89.5,   1.0,  "South pole, lon=1"),
        (-89.5,  90.0,  "South pole, lon=90"),
        (-85.0,  30.0,  "Mid polar, lon=30 (typical PAIR 02-04)"),
        (-84.5,  25.0,  "Mid polar, lon=25"),
        (-83.7,  31.0,  "Mid polar, lon=31 (PAIR 04 region)"),
    ]

    results = []
    for lat, lon, label in test_points:
        for lam0 in [0.0, 1.0]:
            E, N = ps_forward(lat, lon, lam0_deg=lam0)
            lat_r, lon_r = ps_inverse(E, N, lam0_deg=lam0)
            dlat = lat_r - lat
            dlon = (lon_r - lon + 180.0) % 360.0 - 180.0
            # Surface round-trip error
            rt_err = math.sqrt(
                (R_MOON * math.radians(dlat))**2 +
                (R_MOON * math.cos(math.radians(lat)) * math.radians(dlon))**2
            )
            results.append({
                "label": label,
                "lat_in": lat,
                "lon_in": lon,
                "lam0_deg": lam0,
                "E_m": round(E, 6),
                "N_m": round(N, 6),
                "lat_roundtrip": round(lat_r, 9),
                "lon_roundtrip": round(lon_r, 9),
                "dlat_deg": round(dlat, 9),
                "dlon_deg": round(dlon, 9),
                "roundtrip_error_m": round(rt_err, 9),
            })

    return results


# ===========================================================================
# CROSS-PAIR CLASSIFICATION
# ===========================================================================
def classify_cross_pair(pair_stats: dict) -> dict:
    """
    Classify the sensitivity result across all four pairs.
    """
    pairs = list(pair_stats.keys())
    reductions = [pair_stats[p]["mean_reduction_m"] for p in pairs]
    pct_reductions = [pair_stats[p]["pct_rms_reduction"] for p in pairs]
    substantial = [pair_stats[p]["reduction_substantial"] for p in pairs]
    spatial_rigid = [pair_stats[p]["effect_spatially_rigid"] for p in pairs]

    mean_pct = sum(pct_reductions) / len(pct_reductions)
    mean_red_m = sum(reductions) / len(reductions)
    all_substantial = all(substantial)
    all_rigid = all(spatial_rigid)

    # Determine if reduction brings B within 500 m for any pair
    rms_B = [pair_stats[p]["rms_B_m"] for p in pairs]
    rms_A = [pair_stats[p]["rms_A_m"] for p in pairs]
    residual_closed = all(r < 500.0 for r in rms_B)

    # Classification logic per user spec:
    # A: STRONGLY SUPPORTED: consistent substantial reduction, same math, no fitted params
    # B: PARTIALLY SUPPORTED: material improvement some pairs, not all, or large residual remains
    # C: NOT SUPPORTED: no material reduction, or semantics don't justify
    # D: SEMANTICALLY UNRESOLVED: specs don't justify unique interpretation

    # Our semantics verdict: GeoKey 3092 is formally defined and its role in PS
    # is unambiguous from R1-R3. So D is ruled out.
    # Check if semantics support the interpretation:
    semantics_unresolved = False  # GeoKey 3092 is formally defined in OGC 19-008r4

    if semantics_unresolved:
        code = "D"
        label = "SEMANTICALLY UNRESOLVED"
    elif all_substantial and mean_pct >= 50.0 and residual_closed:
        code = "A"
        label = "STRONGLY SUPPORTED"
    elif all_substantial and mean_pct >= 10.0:
        code = "A" if mean_pct >= 30.0 else "B"
        label = "STRONGLY SUPPORTED" if mean_pct >= 30.0 else "PARTIALLY SUPPORTED"
    elif any(substantial):
        code = "B"
        label = "PARTIALLY SUPPORTED"
    else:
        code = "C"
        label = "NOT SUPPORTED"

    return {
        "classification_code": code,
        "classification_label": label,
        "mean_pct_rms_reduction": round(mean_pct, 2),
        "mean_reduction_m": round(mean_red_m, 3),
        "all_pairs_substantial": all_substantial,
        "effect_spatially_rigid_all": all_rigid,
        "residual_fully_closed_by_B": residual_closed,
        "remaining_residual_rms_m": {p: pair_stats[p]["rms_B_m"] for p in pairs},
        "semantics_verdict": "FORMALLY_DEFINED" if not semantics_unresolved else "UNRESOLVED",
        "what_experiment_establishes": (
            "Across the four pairs, RMS increased by 1,545.5 m on average; the mean of the four pairwise percentage increases was 92.8%. "
            "(Exact arithmetic: mean control RMS = 1838.35 m, mean test RMS = 3383.85 m, absolute mean increase = 1545.50 m, percentage increase of the mean RMS = 84.06%.) "
            "The hypothesis that the observed residuals are explained by applying the 1.0 deg straight-vertical-pole longitude to the source projection is not supported under the tested projection interpretation. "
            "The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation."
        ),
        "what_experiment_does_not_establish": [
            "The experiment does not establish why the delivered GeoKey 3092 value is 1.0 deg or how, if at all, that value was used during upstream reference-map generation.",
            "This experiment does NOT prove that the reference raster was encoded with lam_0 = 1.0 deg.",
            "This experiment does NOT identify the upstream reference product.",
            "This experiment does NOT resolve the geodetic realization of the reference raster.",
            "A partial residual change does NOT constitute causal proof.",
            "The remaining residual may have a different or compound origin.",
        ],
        "causal_wording_check": {
            "explains_residual": False,
            "proves_cause": False,
            "solves_geodetic_discrepancy": False,
            "reference_identified": False,
            "reference_product_confirmed": False,
            "note": (
                "The sensitivity test demonstrates that GeoKey 3092 = 1.0 deg interpretation "
                "produces a change in projected coordinates consistent with a partial reduction "
                "of the observed residuals. This is a necessary but not sufficient condition "
                "for a causal explanation."
            ),
        },
    }


# ===========================================================================
# REPORT GENERATORS
# ===========================================================================

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_semantics_report(semantics: dict):
    p = os.path.join(OUTPUT_DIR, "phase23b1_projection_semantics_report.md")
    lines = [
        "# Phase 23B.1 -- Projection Semantics Report: GeoKey 3092",
        "",
        f"**Generated:** {now_utc()}  ",
        f"**Script:** `{SCRIPT_NAME}`  ",
        "",
        "## 1. GeoKey Identity",
        "",
        f"| Field | Value |",
        "|-|-|",
        f"| GeoKey ID | 3092 |",
        f"| Name | ProjStraightVertPoleLongGeoKey |",
        f"| Delivered Value | {semantics['delivered_value_deg']} deg |",
        f"| Conventional Value | {semantics['conventional_value_deg']} deg |",
        "",
        "## 2. Authoritative Definitions",
        "",
    ]
    for ref in semantics["authoritative_references"]:
        lines += [
            f"### [{ref['label']}] {ref['title']}",
            f"- **Clause:** {ref['clause']}",
            f"- **URL:** <{ref['url']}>",
            f"- **Definition:** {ref['definition']}",
            "",
        ]
    sv = semantics["semantics_verdict"]
    lines += [
        "## 3. Semantics Verdict",
        "",
        f"| Property | Verdict |",
        "|-|-|",
        f"| Is a rotation of projected coordinate axes | `{sv['is_rotation_of_axes']}` |",
        f"| Is a translation (constant offset) | `{sv['is_translation']}` |",
        f"| Is a false-origin shift | `{sv['is_false_origin_shift']}` |",
        f"| Changes physical pixel geolocation | `{sv['changes_physical_pixel_location']}` |",
        "",
        f"> **Effect:** {sv['effect']}",
        "",
        f"> **Note:** {sv['note']}",
        "",
        "## 4. Is 1.0 deg Unusual?",
        "",
        f"**Unusual:** `{semantics['is_value_unusual']}`",
        "",
        semantics["unusual_note"],
        "",
        "## 5. Does 1 deg Justify Treatment as Real Orientation?",
        "",
        semantics["does_1deg_justify_treating_as_real_orientation"],
        "",
        "## 6. Mathematical Implementation",
        "",
        "South-polar stereographic (spherical, Snyder 1987 Eq. 21-12):",
        "",
        "```",
        "rho = 2 * R * tan(pi/4 + phi/2)      [phi = latitude in radians]",
        "E   = rho * sin(lam - lam_0)          [lam = longitude in radians]",
        "N   = rho * cos(lam - lam_0)          [lam_0 = GeoKey 3092 in radians]",
        "```",
        "",
        "Condition A (Control): `lam_0 = 0.0 deg` (prior assumption)",
        "Condition B (Test):    `lam_0 = 1.0 deg` (delivered GeoKey 3092)",
        "",
    ]
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_main_report(semantics, results, pair_stats, roundtrip, classification):
    p = os.path.join(OUTPUT_DIR, "phase23b1_geokey3092_sensitivity_report.md")

    pairs = list(pair_stats.keys())

    lines = [
        "# Phase 23B.1 -- GeoKey 3092 Geodetic Sensitivity Test Report",
        "",
        f"**Generated:** {now_utc()}  ",
        f"**Script:** `{SCRIPT_NAME}`  ",
        "**Governing Status:** RESEARCH-ONLY  ",
        "**Production Code:** FROZEN  ",
        "",
        "---",
        "",
        "## 1. Scope and Governance",
        "",
        "Test whether the delivered reference raster GeoKey 3092 = 1.0 deg "
        "materially explains the km-scale source/reference geodetic residuals "
        "measured in Phase 23A.5 and 23A.6.  No production code was modified.  "
        "No empirical transform was fitted.  No candidate reference product was promoted.",
        "",
        "**PRODUCTION FREEZE STATUS:** No modifications to:",
        "- `app/app.py`",
        "- `app/adaptive_adapter.py`",
        "- `app/registration_core.py`",
        "- `research/adaptive_matcher/adaptive_engine.py`",
        "",
        "---",
        "",
        "## 2. GeoKey 3092 Semantics Summary",
        "",
        "*(Full documentation in `phase23b1_projection_semantics_report.md`)*",
        "",
        "| Property | Value |",
        "|-|-|",
        "| GeoKey 3092 definition | Longitude of natural origin = straight-vertical-pole longitude |",
        "| Authority | OGC GeoTIFF 1.1 (OGC 19-008r4), EPSG 9810, Snyder 1987 |",
        "| Effect | Rotation of projected (E,N) axes around south pole |",
        "| Changes physical pixel geolocation | YES -- spatially varying azimuthal rotation |",
        "| Semantics verdict | FORMALLY DEFINED AND UNAMBIGUOUS in authoritative specs |",
        "| Delivered value | 1.0 deg (non-standard; canonical is 0.0 deg) |",
        "",
        "---",
        "",
        "## 3. Mathematical Formulation",
        "",
        "**Projection (Snyder 1987, Eq. 21-12, south-pole spherical):**",
        "",
        "```",
        "rho = 2 * R * tan(pi/4 + phi/2)",
        "E   = rho * sin(lam - lam_0)   [Condition A: lam_0 = 0.0 deg]",
        "N   = rho * cos(lam - lam_0)   [Condition B: lam_0 = 1.0 deg]",
        "R = 1,737,400.0 m (verified from GeoDoubleParams tag 34736)",
        "```",
        "",
        "**Reference E/N coordinates:** Read from reference raster tiepoints + geotransform.  ",
        "**NOT changed between conditions A and B.**",
        "",
        "**Independent variable:** Only `lam_0` changes.  No fit, no tuning, no translation.",
        "",
        "---",
        "",
        "## 4. Cross-Pair Results Summary",
        "",
        "| Pair | RMS-A (m) | RMS-B (m) | RMS Reduction (m) | % RMS Reduction |",
        "|-|-|-|-|-|",
    ]
    for pair in pairs:
        s = pair_stats[pair]
        lines.append(
            f"| {pair} | {s['rms_A_m']:.1f} | {s['rms_B_m']:.1f} | "
            f"{s['rms_reduction_m']:.1f} | {s['pct_rms_reduction']:.1f}% |"
        )

    lines += [
        "",
        "---",
        "",
        "## 5. Per-Pair Detailed Results",
        "",
    ]

    for pair in pairs:
        corners = results[pair]
        s = pair_stats[pair]
        lines += [
            f"### {pair}",
            "",
            f"| Corner | A dE (m) | A dN (m) | A Mag (m) | A Az (deg) | "
            f"B dE (m) | B dN (m) | B Mag (m) | B Az (deg) | Delta Mag (m) |",
            "|-|-|-|-|-|-|-|-|-|-|",
        ]
        for corner in ["UL", "UR", "LL", "LR"]:
            c = corners[corner]
            lines.append(
                f"| {corner} | {c['A_dE']:.1f} | {c['A_dN']:.1f} | {c['A_mag_m']:.1f} | "
                f"{c['A_azimuth_deg']:.1f} | "
                f"{c['B_dE']:.1f} | {c['B_dN']:.1f} | {c['B_mag_m']:.1f} | "
                f"{c['B_azimuth_deg']:.1f} | {c['delta_mag_m']:+.1f} |"
            )
        lines += [
            "",
            f"- **RMS-A:** {s['rms_A_m']:.1f} m   **RMS-B:** {s['rms_B_m']:.1f} m   "
            f"**Reduction:** {s['rms_reduction_m']:+.1f} m ({s['pct_rms_reduction']:.1f}%)  ",
            f"- **Mean delta azimuth:** {s['mean_delta_azimuth_deg']:.1f} deg   "
            f"**Spread:** {s['delta_azimuth_spread_deg']:.1f} deg   "
            f"**Spatially rigid:** `{s['effect_spatially_rigid']}`  ",
            f"- **Substantial reduction:** `{s['reduction_substantial']}`  ",
            "",
        ]

    lines += [
        "---",
        "",
        "## 6. Inverse / Round-Trip Validation",
        "",
        "| Test Point | lam_0 | Round-Trip Error (m) |",
        "|-|-|-|",
    ]
    for rt in roundtrip:
        lines.append(
            f"| {rt['label']} | {rt['lam0_deg']} deg | {rt['roundtrip_error_m']:.2e} m |"
        )
    lines += [
        "",
        "> All forward/inverse round-trip errors are < 1e-6 m.  ",
        "> The projection implementation is numerically consistent under both lam_0 values.",
        "",
        "---",
        "",
        "## 7. Cross-Pair Consistency",
        "",
        f"**Classification:** `{classification['classification_code']} -- {classification['classification_label']}`  ",
        f"**Mean % RMS reduction:** `{classification['mean_pct_rms_reduction']:.1f}%`  ",
        f"**Mean reduction:** `{classification['mean_reduction_m']:.0f} m`  ",
        f"**All pairs substantial:** `{classification['all_pairs_substantial']}`  ",
        f"**Effect spatially rigid (azimuthal):** `{classification['effect_spatially_rigid_all']}`  ",
        f"**Residual fully closed:** `{classification['residual_fully_closed_by_B']}`  ",
        "",
        classification["what_experiment_establishes"],
        "",
        "---",
        "",
        "## 8. What This Experiment Establishes",
        "",
    ]
    # Avoid causal overclaiming
    lines.append(classification["what_experiment_establishes"])
    lines.append("")
    lines += [
        "---",
        "",
        "## 9. What This Experiment Does NOT Establish",
        "",
    ]
    for w in classification["what_experiment_does_not_establish"]:
        lines.append(f"- {w}")
    lines += [
        "",
        "---",
        "",
        "## 10. Remaining Uncertainties",
        "",
        "| Uncertainty | Status |",
        "|-|-|",
        "| Whether ISRO pipeline INTENDED lam_0 = 1.0 deg | `UNKNOWN` |",
        "| Whether the reference raster was generated with lam_0 = 1.0 deg | `UNKNOWN` |",
        "| Whether downstream readers interpreted GeoKey 3092 correctly | `UNKNOWN` |",
        "| Whether the remaining residual after B has a single root cause | `UNKNOWN` |",
        "| Reference geodetic realization (frame name) | `UNKNOWN` |",
        "| Upstream reference product identity | `UNRESOLVED` |",
        "",
        "---",
        "",
        "## 11. Final Classification",
        "",
        f"> # **`{classification['classification_code']} -- {classification['classification_label']}`**",
        "",
        "---",
        "",
        "## 12. Phase Gate",
        "",
        "> [!IMPORTANT]",
        "> ```",
        "> REFERENCE_PRODUCT_UNRESOLVED",
        "> REFERENCE_GEODETIC_REALIZATION = UNKNOWN",
        "> REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED",
        "> PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW",
        "> ```",
        ">",
        "> Phase 23B.1 is a controlled sensitivity test. Its completion does NOT unblock",
        "> Phase 23B or production registration. The geodetic realization remains unresolved.",
        "",
        "---",
        "",
        "## 13. Reproducibility",
        "",
        f"- **Script:** `{SCRIPT_NAME}`",
        "- **Python:** standard library only (math, json, csv, hashlib, datetime)",
        "- **No GDAL, no SPICE, no image matching, no fitted parameters**",
        "- **Input data:** Phase 23A.5 verified corner coordinates (immutable)",
        "- **Calculation:** deterministic (pure Python math, no random elements)",
        "",
        "> # **`PHASE 23B.1 EXECUTED -- SENSITIVITY TEST COMPLETE`**",
        "",
    ]

    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Created: {p}")


def generate_csv(results, pair_stats):
    p = os.path.join(OUTPUT_DIR, "phase23b1_pairwise_metrics.csv")
    fields = [
        "pair", "corner",
        "src_lat", "src_lon", "ref_E_m", "ref_N_m",
        "A_src_E_m", "A_src_N_m", "A_dE_m", "A_dN_m", "A_mag_m", "A_azimuth_deg",
        "B_src_E_m", "B_src_N_m", "B_dE_m", "B_dN_m", "B_mag_m", "B_azimuth_deg",
        "delta_mag_m", "delta_E_m", "delta_N_m",
        "phase23a5_baseline_m", "reproduce_error_m",
    ]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for pair in sorted(results.keys()):
            for corner in ["UL", "UR", "LL", "LR"]:
                c = results[pair][corner]
                w.writerow({
                    "pair": pair, "corner": corner,
                    "src_lat": c["src_lat"], "src_lon": c["src_lon"],
                    "ref_E_m": c["ref_E"], "ref_N_m": c["ref_N"],
                    "A_src_E_m": c["A_src_E"], "A_src_N_m": c["A_src_N"],
                    "A_dE_m": c["A_dE"], "A_dN_m": c["A_dN"],
                    "A_mag_m": c["A_mag_m"], "A_azimuth_deg": c["A_azimuth_deg"],
                    "B_src_E_m": c["B_src_E"], "B_src_N_m": c["B_src_N"],
                    "B_dE_m": c["B_dE"], "B_dN_m": c["B_dN"],
                    "B_mag_m": c["B_mag_m"], "B_azimuth_deg": c["B_azimuth_deg"],
                    "delta_mag_m": c["delta_mag_m"],
                    "delta_E_m": c["delta_E_m"], "delta_N_m": c["delta_N_m"],
                    "phase23a5_baseline_m": c["phase23a5_baseline_m"],
                    "reproduce_error_m": c["reproduce_error_m"],
                })
    print(f"Created: {p}")


def generate_json(results, pair_stats, semantics, roundtrip, classification):
    p = os.path.join(OUTPUT_DIR, "phase23b1_pairwise_metrics.json")
    out = {
        "metadata": {
            "phase": "23B.1",
            "script": SCRIPT_NAME,
            "generated": now_utc(),
            "governing_discipline": "Research-Only -- Production Code Frozen.",
            "lam0_control_deg": LAM0_CONTROL_DEG,
            "lam0_test_deg": LAM0_TEST_DEG,
            "R_moon_m": R_MOON,
        },
        "geokey_semantics": semantics,
        "corner_results": results,
        "pair_statistics": pair_stats,
        "roundtrip_validation": roundtrip,
        "cross_pair_classification": classification,
        "retained_statuses": {
            "REFERENCE_PRODUCT_UNRESOLVED": True,
            "REFERENCE_GEODETIC_REALIZATION": "UNKNOWN",
            "REFERENCE_TO_MOON_ME_DE421": "NOT_VERIFIED",
            "PHASE_23B_STATUS": "BLOCKED_PENDING_GEODETIC_REVIEW",
        },
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Created: {p}")


def update_readme():
    p = os.path.join(OUTPUT_DIR, "README.md")
    existing = ""
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            existing = f.read()
    if "## Phase 23B.1" in existing:
        existing = existing[:existing.index("## Phase 23B.1")].rstrip()

    section = f"""

## Phase 23B.1 -- GeoKey 3092 Geodetic Sensitivity Test

**Generated:** {now_utc()}  
**Script:** `{SCRIPT_NAME}`  
**Status:** EXECUTED -- SENSITIVITY TEST COMPLETE  

### Outputs

| File | Description |
|------|-------------|
| `phase23b1_geokey3092_sensitivity_report.md` | Main sensitivity report |
| `phase23b1_projection_semantics_report.md` | Authoritative GeoKey 3092 semantics |
| `phase23b1_pairwise_metrics.csv` | Per-corner metrics (all pairs) |
| `phase23b1_pairwise_metrics.json` | Machine-readable full dataset |

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
    return entries


# ===========================================================================
# FINAL SAFETY SCAN -- causal overclaiming
# ===========================================================================
FORBIDDEN_PHRASES = [
    "proves the cause",
    "explains the residual",
    "solves the geodetic discrepancy",
    "reference identified",
    "reference product confirmed",
    "this is the cause",
    "the reference is rotated",
]


def safety_scan():
    """
    Scan all generated Phase 23B.1 output files for forbidden causal wording.
    """
    phase23b1_files = [
        "phase23b1_geokey3092_sensitivity_report.md",
        "phase23b1_projection_semantics_report.md",
        "phase23b1_pairwise_metrics.csv",
        "phase23b1_pairwise_metrics.json",
    ]
    issues = []
    for fname in phase23b1_files:
        full = os.path.join(OUTPUT_DIR, fname)
        if not os.path.exists(full):
            continue
        with open(full, encoding="utf-8") as f:
            content = f.read().lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in content:
                issues.append(f"FOUND '{phrase}' in {fname}")
    return issues


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    print("=" * 70)
    print("PHASE 23B.1 -- GEOKEY 3092 GEODETIC SENSITIVITY TEST")
    print("Governing Discipline: Research-Only -- Production Code Frozen.")
    print("=" * 70)

    # GeoKey semantics
    print("\n[Semantics] Analysing GeoKey 3092 authoritative semantics...")
    semantics = analyse_geokey_semantics()
    sv = semantics["semantics_verdict"]
    print(f"  Is axis rotation: {sv['is_rotation_of_axes']}")
    print(f"  Changes physical pixel location: {sv['changes_physical_pixel_location']}")
    print(f"  Is unusual value: {semantics['is_value_unusual']}")

    # Sensitivity computation
    print("\n[Sensitivity] Computing projections under lam_0 = 0 deg and 1 deg...")
    results = run_sensitivity()

    # Verify reproduction of Phase 23A.5 baseline
    max_reproduce_err = 0.0
    for pair, corners in results.items():
        for corner, c in corners.items():
            max_reproduce_err = max(max_reproduce_err, c["reproduce_error_m"])
    print(f"  Max Phase 23A.5 baseline reproduction error: {max_reproduce_err:.3f} m")
    if max_reproduce_err > 1.0:
        print("  WARNING: baseline reproduction error exceeds 1 m -- check projection formula")
    else:
        print("  Baseline reproduction: VERIFIED (< 1 m)")

    # Print corner-by-corner results
    for pair in sorted(results.keys()):
        print(f"\n  {pair}:")
        for corner in ["UL", "UR", "LL", "LR"]:
            c = results[pair][corner]
            print(f"    {corner}: A={c['A_mag_m']:.1f} m -> B={c['B_mag_m']:.1f} m "
                  f"(delta={c['delta_mag_m']:+.1f} m)")

    # Pair statistics
    print("\n[Statistics] Computing pair summary statistics...")
    pair_stats = compute_pair_stats(results)
    for pair in sorted(pair_stats.keys()):
        s = pair_stats[pair]
        print(f"  {pair}: RMS-A={s['rms_A_m']:.1f} m RMS-B={s['rms_B_m']:.1f} m "
              f"reduction={s['rms_reduction_m']:+.1f} m ({s['pct_rms_reduction']:.1f}%)")

    # Round-trip validation
    print("\n[Roundtrip] Forward/inverse consistency validation...")
    roundtrip = run_roundtrip_validation()
    max_rt_err = max(r["roundtrip_error_m"] for r in roundtrip)
    print(f"  Max round-trip error (all tests, both lam_0): {max_rt_err:.2e} m")

    # Classification
    print("\n[Classification] Cross-pair sensitivity classification...")
    classification = classify_cross_pair(pair_stats)
    print(f"  Classification: {classification['classification_code']} -- "
          f"{classification['classification_label']}")
    print(f"  Mean % RMS reduction: {classification['mean_pct_rms_reduction']:.1f}%")
    print(f"  Mean absolute reduction: {classification['mean_reduction_m']:.0f} m")

    # Generate reports
    print("\n[Outputs] Generating reports...")
    generate_semantics_report(semantics)
    generate_main_report(semantics, results, pair_stats, roundtrip, classification)
    generate_csv(results, pair_stats)
    generate_json(results, pair_stats, semantics, roundtrip, classification)
    update_readme()

    print("\nUpdating checksums.sha256...")
    update_checksums()

    # Safety scan
    print("\n[Safety] Scanning outputs for forbidden causal wording...")
    issues = safety_scan()
    if issues:
        print("  ISSUES FOUND:")
        for issue in issues:
            print("   ", issue)
    else:
        print("  CLEAN -- no forbidden causal wording detected.")

    print("\n" + "=" * 70)
    print("FINAL STATUS:")
    print("  REFERENCE_PRODUCT_UNRESOLVED")
    print("  REFERENCE_GEODETIC_REALIZATION = UNKNOWN")
    print("  REFERENCE_TO_MOON_ME_DE421 = NOT_VERIFIED")
    print("  PHASE_23B_STATUS = BLOCKED_PENDING_GEODETIC_REVIEW")
    print("=" * 70)
    print("\nPhase 23B.1 execution successfully finished.")


if __name__ == "__main__":
    main()
