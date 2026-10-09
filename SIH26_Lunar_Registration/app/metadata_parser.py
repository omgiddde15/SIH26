"""
Metadata Parser and Session Manager for LunarReg.

Handles user-uploaded XML metadata (especially Chandrayaan-2/PDS4-style XML),
validates XML integrity, extracts available telemetry fields without fabricating
missing quantities, manages session state, and renders concise UI summaries.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Any, Optional, Tuple, List, Union

try:
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET  # type: ignore

import streamlit as st


# ============================================================
# CANONICAL METADATA FIELD DEFINITIONS
# ============================================================

METADATA_DISPLAY_KEYS: List[Tuple[str, str]] = [
    ("product_identifier", "Product Identifier"),
    ("processing_level", "Processing Level"),
    ("sensor_platform", "Sensor / Platform"),
    ("image_dimensions", "Image Dimensions"),
    ("acquisition_datetime", "Acquisition Date/Time"),
    ("ground_sample_distance", "Ground Sample Distance / Pixel Scale"),
    ("altitude", "Spacecraft Altitude"),
    ("solar_azimuth", "Solar Azimuth"),
    ("solar_elevation", "Solar Elevation"),
    ("incidence_angle", "Incidence Angle"),
    ("observation_geometry", "Observation Geometry"),
    ("coordinate_reference", "Coordinate Reference / Projection"),
]

NOT_AVAILABLE = "Not available"


# ============================================================
# XML VALIDATION & FIELD EXTRACTION
# ============================================================

def validate_xml(content: Union[str, bytes]) -> Tuple[bool, str, Optional[ET.Element]]:
    """
    Validates whether the provided content is well-formed XML.
    Returns (is_valid, error_message, root_element).
    """
    if content is None:
        return False, "Uploaded XML file is empty.", None

    if isinstance(content, bytes):
        if len(content.strip()) == 0:
            return False, "Uploaded XML file is empty.", None
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = content.decode("latin-1")
            except Exception as dec_err:
                return False, f"Unable to decode XML file text: {dec_err}", None
    else:
        content_str = str(content)

    if not content_str.strip():
        return False, "Uploaded XML file is empty.", None

    try:
        root = ET.fromstring(content_str)
        return True, "", root
    except Exception as parse_err:
        return False, f"Invalid XML format: {parse_err}", None


def _find_tag_text(root: ET.Element, candidates: List[str]) -> Optional[str]:
    """Search for matching tag text adhering strictly to candidate priority order."""
    for cand in candidates:
        cand_lower = cand.lower()
        for elem in root.iter():
            tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag_name.lower() == cand_lower:
                txt = elem.text
                if txt and txt.strip():
                    return txt.strip()
    return None


def _find_tag_element(root: ET.Element, tag_name: str) -> Optional[ET.Element]:
    """Search for a tag element by name (case-insensitive, ignoring namespaces)."""
    target = tag_name.lower()
    for elem in root.iter():
        t = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if t.lower() == target:
            return elem
    return None


def _extract_product_id(root: ET.Element) -> Optional[str]:
    candidates = [
        "job_id",
        "product_id",
        "logical_identifier",
        "level0_dataset",
        "dataset_id",
        "Product_Id",
        "Job_Id",
    ]
    return _find_tag_text(root, candidates)


def _extract_processing_level(root: ET.Element) -> Optional[str]:
    candidates = [
        "processing_level",
        "process_level",
        "processing_level_id",
        "processing_level_urn",
    ]
    val = _find_tag_text(root, candidates)
    return val if val else None


def _extract_sensor_platform(root: ET.Element) -> Optional[str]:
    platform_cands = ["platform", "spacecraft_name", "mission_name", "observing_system"]
    platform = _find_tag_text(root, platform_cands)

    sensor_cands = ["instrument_name", "instrument_id", "sensor"]
    sensor = _find_tag_text(root, sensor_cands)

    # Contextual Chandrayaan-2 heuristics strictly from existing tags
    if not sensor:
        if _find_tag_element(root, "ohr") is not None:
            sensor = "OHRC (Optical High Resolution Camera)"
        elif _find_tag_element(root, "iir") is not None:
            sensor = "IIRS (Imaging Infrared Spectrometer)"
        elif _find_tag_element(root, "pan") is not None:
            sensor = "OHRC / PAN"

    if not platform:
        station = _find_tag_text(root, ["station_id"])
        job = _find_tag_text(root, ["job_id", "level0_dataset"])
        if (job and "CHO" in job) or (station and station.startswith("D")):
            platform = "Chandrayaan-2"

    if platform and sensor:
        return f"{sensor} / {platform}"
    elif sensor:
        return sensor
    elif platform:
        return platform
    return None


def _extract_dimensions(root: ET.Element) -> Optional[str]:
    w_txt = _find_tag_text(root, ["image_width", "raw_qube_image_width", "samples", "elements"])
    h_txt = _find_tag_text(root, ["image_height", "raw_no_of_scan", "radiance_qube_image_height", "lines"])

    w_val: Optional[int] = None
    h_val: Optional[int] = None

    if w_txt:
        try:
            w_val = int(float(w_txt))
        except (ValueError, TypeError):
            w_val = None

    if h_txt:
        try:
            h_val = int(float(h_txt))
        except (ValueError, TypeError):
            h_val = None

    if w_val is not None and h_val is not None:
        return f"{w_val} × {h_val} px"
    elif w_val is not None:
        return f"{w_val} px (width)"
    elif h_val is not None:
        return f"{h_val} px (height)"
    return None


def _extract_datetime(root: ET.Element) -> Optional[str]:
    start = _find_tag_text(root, ["start_time_utc", "start_date_time", "StartTime", "date_of_pass", "dop"])
    stop = _find_tag_text(root, ["stop_time_utc", "stop_date_time", "StopTime"])

    if start and stop and start != stop:
        return f"{start} to {stop}"
    elif start:
        return start
    return None


def _extract_gsd(root: ET.Element) -> Optional[str]:
    cands = [
        "Resolution_in_meter",
        "resolution",
        "pixel_resolution",
        "ground_sample_distance",
        "pixel_scale",
        "Spatial_Resolution",
    ]
    txt = _find_tag_text(root, cands)
    if txt:
        try:
            val = float(txt)
            return f"{val:.2f} m/px" if val != int(val) else f"{val} m/px"
        except (ValueError, TypeError):
            return None
    return None


def _extract_altitude(root: ET.Element) -> Optional[str]:
    cands = ["spacecraft_altitude_in_km", "spacecraft_altitude", "altitude"]
    txt = _find_tag_text(root, cands)
    if txt:
        try:
            val = float(txt)
            return f"{val:.2f} km"
        except (ValueError, TypeError):
            return None
    return None


def _extract_solar_azimuth(root: ET.Element) -> Optional[str]:
    cands = ["Sun_azimuth_in_degree", "solar_azimuth", "sun_azimuth"]
    txt = _find_tag_text(root, cands)
    if txt:
        try:
            val = float(txt)
            return f"{val:.2f}°"
        except (ValueError, TypeError):
            return None
    return None


def _extract_solar_elevation(root: ET.Element) -> Optional[str]:
    cands = ["Sun_elevation_in_degree", "solar_elevation", "sun_elevation"]
    txt = _find_tag_text(root, cands)
    if txt:
        try:
            val = float(txt)
            return f"{val:.2f}°"
        except (ValueError, TypeError):
            return None
    return None


def _extract_incidence_angle(root: ET.Element) -> Optional[str]:
    cands = ["Solar_incidence_angle_in_degree", "solar_incidence_angle", "incidence_angle", "solar_incidence"]
    txt = _find_tag_text(root, cands)
    if txt:
        try:
            val = float(txt)
            return f"{val:.2f}°"
        except (ValueError, TypeError):
            return None
    return None


def _extract_observation_geometry(root: ET.Element) -> Optional[str]:
    roll_txt = _find_tag_text(root, ["Roll_in_degree", "roll"])
    pitch_txt = _find_tag_text(root, ["Pitch_in_degree", "pitch"])
    yaw_txt = _find_tag_text(root, ["Yaw_in_degree", "yaw"])
    orbit_dir = _find_tag_text(root, ["orbit_limb_direction"])

    parts = []
    if roll_txt is not None and pitch_txt is not None and yaw_txt is not None:
        try:
            r = float(roll_txt)
            p = float(pitch_txt)
            y = float(yaw_txt)
            parts.append(f"Roll: {r:.2f}°, Pitch: {p:.2f}°, Yaw: {y:.2f}°")
        except (ValueError, TypeError):
            pass

    if orbit_dir:
        parts.append(f"Orbit: {orbit_dir}")

    if parts:
        return " | ".join(parts)
    return None


def _extract_projection(root: ET.Element) -> Optional[str]:
    proj = _find_tag_text(root, ["projection", "map_projection_name", "coordinate_system_name"])
    area = _find_tag_text(root, ["area"])

    if proj and area:
        return f"{proj} ({area})"
    elif proj:
        return proj
    elif area:
        return area
    return None


def _extract_corners(root: ET.Element) -> Optional[Dict[str, Dict[str, float]]]:
    """Extract corner geodetic coordinates if present in <corners>."""
    corners_elem = _find_tag_element(root, "corners")
    if corners_elem is None:
        return None

    corners = {}
    for prefix in ("topleft", "topright", "bottomleft", "bottomright"):
        lat_txt = _find_tag_text(corners_elem, [f"{prefix}_latitude"])
        lon_txt = _find_tag_text(corners_elem, [f"{prefix}_longitude"])
        if lat_txt and lon_txt:
            try:
                corners[prefix] = {
                    "lat": float(lat_txt),
                    "lon": float(lon_txt),
                }
            except (ValueError, TypeError):
                pass

    return corners if len(corners) == 4 else None


# ============================================================
# MAIN METADATA PARSER
# ============================================================

def parse_metadata_xml(content: Union[str, bytes], filename: str = "") -> Dict[str, Any]:
    """
    Parses XML metadata (specifically Chandrayaan-2/PDS4 style).
    Extracts only fields actually present; missing or invalid fields
    are reported as 'Not available'.
    """
    if isinstance(content, bytes):
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = content.decode("latin-1")
            except Exception:
                raw_text = ""
    else:
        raw_text = str(content) if content is not None else ""

    is_valid, err_msg, root = validate_xml(content)
    if not is_valid or root is None:
        return {
            "valid": False,
            "filename": filename,
            "error": err_msg,
            "raw_xml": raw_text,
            "raw_fields": {},
            "display_fields": {label: NOT_AVAILABLE for _, label in METADATA_DISPLAY_KEYS},
            "corners": None,
            "is_uploaded": True if filename else False,
        }

    raw_fields: Dict[str, str] = {}

    extractors = {
        "product_identifier": _extract_product_id,
        "processing_level": _extract_processing_level,
        "sensor_platform": _extract_sensor_platform,
        "image_dimensions": _extract_dimensions,
        "acquisition_datetime": _extract_datetime,
        "ground_sample_distance": _extract_gsd,
        "altitude": _extract_altitude,
        "solar_azimuth": _extract_solar_azimuth,
        "solar_elevation": _extract_solar_elevation,
        "incidence_angle": _extract_incidence_angle,
        "observation_geometry": _extract_observation_geometry,
        "coordinate_reference": _extract_projection,
    }

    display_fields: Dict[str, str] = {}

    for key, label in METADATA_DISPLAY_KEYS:
        extractor = extractors.get(key)
        val = None
        if extractor is not None:
            try:
                val = extractor(root)
            except Exception:
                val = None

        if val is not None and str(val).strip():
            raw_fields[key] = str(val).strip()
            display_fields[label] = str(val).strip()
        else:
            display_fields[label] = NOT_AVAILABLE

    corners = _extract_corners(root)

    return {
        "valid": True,
        "filename": filename,
        "error": None,
        "raw_xml": raw_text,
        "raw_fields": raw_fields,
        "display_fields": display_fields,
        "corners": corners,
        "is_uploaded": True,
    }


def parse_metadata_file(content_or_bytes: Union[str, bytes], filename: str = "") -> Dict[str, Any]:
    """
    Extensible metadata parser entry point.
    Routes by extension (.xml primary; future-ready for .json sidecars).
    """
    ext = os.path.splitext(filename)[1].lower() if filename else ""

    if ext == ".xml":
        return parse_metadata_xml(content_or_bytes, filename=filename)
    elif ext == ".json":
        return {
            "valid": False,
            "filename": filename,
            "error": "JSON sidecar metadata is planned for a future release. Only .xml metadata is currently supported.",
            "raw_xml": None,
            "raw_fields": {},
            "display_fields": {label: NOT_AVAILABLE for _, label in METADATA_DISPLAY_KEYS},
            "corners": None,
            "is_uploaded": True if filename else False,
        }
    else:
        err_msg = f"Unsupported metadata file extension '{ext or 'unknown'}'. Only .xml metadata files are supported."
        return {
            "valid": False,
            "filename": filename,
            "error": err_msg,
            "raw_xml": None,
            "raw_fields": {},
            "display_fields": {label: NOT_AVAILABLE for _, label in METADATA_DISPLAY_KEYS},
            "corners": None,
            "is_uploaded": True if filename else False,
        }


# ============================================================
# SESSION STATE MANAGEMENT
# ============================================================

def handle_uploaded_metadata_file(uploaded_file, role: str, session_state: Any) -> Tuple[bool, Optional[str]]:
    """
    Processes an uploaded metadata file for 'source' or 'reference'.
    Updates session state cleanly, preserving independent replacement.
    """
    if uploaded_file is None:
        return False, None

    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()
    if ext != ".xml":
        err = f"Unsupported file extension '{ext}'. Only .xml metadata files are supported."
        session_state[f"{role}_metadata"] = None
        session_state[f"{role}_metadata_error"] = err
        session_state[f"{role}_metadata_file"] = {"filename": filename, "size_bytes": 0, "content": ""}
        return False, err

    try:
        raw_bytes = uploaded_file.read()
    except Exception as read_err:
        err = f"Unable to read uploaded file: {read_err}"
        session_state[f"{role}_metadata"] = None
        session_state[f"{role}_metadata_error"] = err
        session_state[f"{role}_metadata_file"] = {"filename": filename, "size_bytes": 0, "content": ""}
        return False, err

    if len(raw_bytes.strip()) == 0:
        err = f"Uploaded {role.capitalize()} Metadata file is empty."
        session_state[f"{role}_metadata"] = None
        session_state[f"{role}_metadata_error"] = err
        session_state[f"{role}_metadata_file"] = {"filename": filename, "size_bytes": 0, "content": ""}
        return False, err

    parsed = parse_metadata_xml(raw_bytes, filename=filename)

    session_state[f"{role}_metadata_file"] = {
        "filename": filename,
        "size_bytes": len(raw_bytes),
        "content": parsed.get("raw_xml", ""),
    }

    if parsed.get("valid"):
        session_state[f"{role}_metadata"] = parsed
        session_state[f"{role}_metadata_error"] = None
        return True, None
    else:
        session_state[f"{role}_metadata"] = None
        err = parsed.get("error", "Invalid XML metadata.")
        session_state[f"{role}_metadata_error"] = err
        return False, err


def clear_metadata_state(session_state: Any, role: Optional[str] = None) -> None:
    """
    Clears metadata session state for a given role ('source', 'reference'),
    or clears all metadata state if role is None.
    """
    roles = [role] if role in ("source", "reference") else ["source", "reference"]
    for r in roles:
        session_state.pop(f"{r}_metadata", None)
        session_state.pop(f"{r}_metadata_file", None)
        session_state.pop(f"{r}_metadata_error", None)
        session_state.pop(f"u_{r}_metadata", None)
    if role is None:
        session_state.pop("run_metadata", None)


# ============================================================
# UI RENDERING COMPONENTS
# ============================================================

CARD_DISPLAY_LABELS: Dict[str, str] = {
    "product_identifier": "Product ID",
    "processing_level": "Processing Level",
    "sensor_platform": "Sensor / Platform",
    "image_dimensions": "Image Dimensions",
    "acquisition_datetime": "Acquisition Time",
    "ground_sample_distance": "GSD",
    "altitude": "Spacecraft Altitude",
    "solar_azimuth": "Solar Azimuth",
    "solar_elevation": "Solar Elevation",
    "incidence_angle": "Incidence Angle",
    "observation_geometry": "Observation Geometry",
    "coordinate_reference": "Coordinate Ref",
}

DEFAULT_CARD_FIELDS: List[Tuple[str, str]] = [
    ("product_identifier", "Product ID"),
    ("processing_level", "Processing Level"),
    ("ground_sample_distance", "GSD"),
    ("solar_elevation", "Solar Elevation"),
    ("incidence_angle", "Incidence Angle"),
]


def _render_html(html_str: str) -> None:
    """
    Renders styled HTML component cleanly in Streamlit.
    Removes leading whitespace and blank lines to guarantee that
    CommonMark markdown parsers never misinterpret HTML as indented code blocks.
    Uses st.markdown(..., unsafe_allow_html=True).
    """
    clean_html = "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())
    st.markdown(clean_html, unsafe_allow_html=True)


def get_metadata_card_html(
    role_label: str,
    meta_dict: Optional[Dict[str, Any]],
    error_msg: Optional[str] = None,
    card_bg: str = "#0d1117",
    border_color: str = "#1f2a3a"
) -> str:
    """
    Constructs clean, styled, unindented HTML for a metadata card.
    Guarantees no raw HTML code blocks or visible tags in Streamlit.
    """
    has_meta = meta_dict is not None and bool(meta_dict.get("valid", False))
    fn = meta_dict.get("filename", "") if meta_dict else ""
    err = error_msg or (meta_dict.get("error") if meta_dict and not meta_dict.get("valid") else None)

    if has_meta:
        status_badge = '<span style="background: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid #2ea043; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; font-family: monospace;">● Loaded</span>'
    elif err:
        status_badge = '<span style="background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid #da3633; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; font-family: monospace;">✕ Error</span>'
    else:
        status_badge = '<span style="background: rgba(110, 118, 129, 0.15); color: #8b949e; border: 1px solid #30363d; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; font-family: monospace;">○ Not uploaded</span>'

    if has_meta and fn:
        file_display = f'<span style="font-family: monospace; color: #00f2ff; font-weight: 600;">{fn}</span>'
    elif fn:
        file_display = f'<span style="font-family: monospace; color: #f85149;">{fn}</span>'
    else:
        file_display = '<span style="font-style: italic; color: #8b949e;">No metadata file uploaded</span>'

    field_rows = []
    if has_meta:
        raw_fields = meta_dict.get("raw_fields", {})
        for key, default_label in METADATA_DISPLAY_KEYS:
            if key in raw_fields:
                val = str(raw_fields[key]).strip()
                if val:
                    display_label = CARD_DISPLAY_LABELS.get(key, default_label)
                    field_rows.append((display_label, val, True))
        if not field_rows:
            for key, default_label in DEFAULT_CARD_FIELDS:
                field_rows.append((default_label, NOT_AVAILABLE, False))
    else:
        for key, default_label in DEFAULT_CARD_FIELDS:
            field_rows.append((default_label, NOT_AVAILABLE, False))

    lines = [
        f'<div style="background: {card_bg}; border: 1px solid {border_color}; border-radius: 6px; padding: 12px 14px; box-sizing: border-box; width: 100%; min-height: 280px; display: flex; flex-direction: column;">',
        '<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1c2738; padding-bottom: 8px; margin-bottom: 10px;">',
        f'<div style="font-size: 0.85rem; font-weight: 700; color: #79c0ff; letter-spacing: 0.5px; text-transform: uppercase;">{role_label}</div>',
        f'<div>{status_badge}</div>',
        '</div>',
        f'<div style="font-size: 0.78rem; color: #8b949e; margin-bottom: 10px; word-break: break-all;"><strong style="color: #c9d1d9;">File:</strong> {file_display}</div>',
    ]

    if err:
        lines.append(
            f'<div style="background: rgba(248, 81, 73, 0.1); border: 1px solid #da3633; border-radius: 4px; padding: 6px 10px; margin-bottom: 10px; font-size: 0.76rem; color: #f85149; word-break: break-word;">{err}</div>'
        )

    lines.append('<div style="display: flex; flex-direction: column; flex-grow: 1;">')
    for label, val, is_extracted in field_rows:
        if is_extracted and val != NOT_AVAILABLE:
            val_style = 'color: #58a6ff; font-weight: 600; font-family: monospace;'
        else:
            val_style = 'color: #8b949e; font-style: italic;'
        row_html = (
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.78rem; gap: 8px;">'
            f'<span style="color: #c9d1d9; font-weight: 500; min-width: 105px; max-width: 45%; flex-shrink: 0; line-height: 1.35;">{label}</span>'
            f'<span style="{val_style} text-align: right; word-break: break-word; overflow-wrap: anywhere; flex-grow: 1; line-height: 1.35;" title="{val}">{val}</span>'
            f'</div>'
        )
        lines.append(row_html)
    lines.append('</div>')
    lines.append('</div>')

    return "\n".join(lines)


def render_metadata_card(
    role_label: str,
    meta_dict: Optional[Dict[str, Any]],
    error_msg: Optional[str] = None,
    card_bg: str = "#0d1117",
    border_color: str = "#1f2a3a"
) -> None:
    """
    Renders a concise, professional telemetry card matching LunarReg styling.
    Shows Loaded / Not uploaded, filename, extracted fields, and 'Not available'.
    """
    card_html = get_metadata_card_html(
        role_label=role_label,
        meta_dict=meta_dict,
        error_msg=error_msg,
        card_bg=card_bg,
        border_color=border_color,
    )
    _render_html(card_html)


def render_inputs_metadata_summary(
    src_meta: Optional[Dict[str, Any]],
    ref_meta: Optional[Dict[str, Any]],
    src_err: Optional[str] = None,
    ref_err: Optional[str] = None
) -> None:
    """Renders the concise metadata panel on the Inputs page."""
    with st.expander("Uploaded User Metadata Summary", expanded=True):
        expl_text = (
            "Telemetry and mission parameters parsed from user-uploaded XML files. "
            "Only present tags are extracted; missing quantities are marked as "
            "Not available without extrapolation."
        )
        expl_html = (
            f'<div style="font-size: 0.78rem; color: #8b949e; margin-bottom: 12px; line-height: 1.4;">'
            f'{expl_text}'
            f'</div>'
        )
        _render_html(expl_html)
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            render_metadata_card("Source Metadata", src_meta, error_msg=src_err)
        with col_m2:
            render_metadata_card("Reference Metadata", ref_meta, error_msg=ref_err)


def render_results_metadata_section(res: Dict[str, Any]) -> None:
    """
    Renders the concise Metadata section in the Results view.
    Reflects the exact metadata recorded for the completed run.
    """
    src_meta = res.get("source_metadata")
    ref_meta = res.get("reference_metadata")

    banner_html = (
        '<div style="background: #121824; border: 1px solid #212c3d; border-radius: 6px; padding: 8px 12px 2px 12px; margin-bottom: 6px; margin-top: 8px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f2a3a; padding-bottom: 4px; margin-bottom: 4px;">'
        '<span style="font-size: 0.88rem; font-weight: 700; color: #58a6ff; letter-spacing: 0.5px;">Run Telemetry & Metadata</span>'
        '<span style="font-size: 0.72rem; color: #8b949e; font-family: monospace;">Uploaded Mission Metadata Context</span>'
        '</div>'
        '</div>'
    )
    _render_html(banner_html)

    with st.expander("View Run Telemetry & Metadata", expanded=bool(src_meta or ref_meta)):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            render_metadata_card("Source Metadata", src_meta, error_msg=None)
        with col_r2:
            render_metadata_card("Reference Metadata", ref_meta, error_msg=None)
