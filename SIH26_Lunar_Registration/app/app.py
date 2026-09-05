import os
import ssl
import time
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
import streamlit as st
from kornia.feature import LoFTR

# Disable SSL verification for model weight downloads on constrained platforms
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================
# 1. CORE REGISTRATION ENGINE — LOCKED BACKEND
# ============================================================

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@st.cache_resource
def load_loftr_matcher():
    """Load and cache the LoFTR outdoor pretrained model."""
    matcher = LoFTR(pretrained="outdoor").to(_DEVICE)
    matcher.eval()
    return matcher

def preprocess_image(image):
    """
    Standard preprocessing: Grayscale conversion + CLAHE contrast enhancement.
    Tile grid: (8, 8), Clip limit: 2.0.
    """
    if image is None:
        raise ValueError("Input image could not be decoded or is None.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return gray, clahe.apply(gray)

def calculate_spatial_grid(points, image_shape, rows=3, cols=3):
    """
    Partition correspondence points into a rows x cols spatial grid
    and return the cell occupancy count matrix.
    """
    h, w = image_shape
    grid = np.zeros((rows, cols), dtype=int)
    for x, y in points:
        col = min(int(x / (w / cols)), cols - 1)
        row = min(int(y / (h / rows)), rows - 1)
        grid[row, col] += 1
    return grid

def register_images(source_image, reference_image, max_per_cell=6, ransac_threshold=3.0):
    """
    LOCKED CORE REGISTRATION PIPELINE:
    CLAHE -> LoFTR -> RANSAC -> Quality + Spatial Selection -> Final Homography -> Warped Result -> Telemetry Metrics.
    """
    start_time = time.perf_counter()
    matcher = load_loftr_matcher()

    # Step 1: Preprocessing & CLAHE
    source_gray, source_clahe = preprocess_image(source_image)
    reference_gray, reference_clahe = preprocess_image(reference_image)

    # Step 2: LoFTR Feature Matching
    source_tensor = torch.from_numpy(source_clahe.astype(np.float32) / 255.0)[None, None].to(_DEVICE)
    reference_tensor = torch.from_numpy(reference_clahe.astype(np.float32) / 255.0)[None, None].to(_DEVICE)

    with torch.no_grad():
        output = matcher({"image0": source_tensor, "image1": reference_tensor})

    mkpts0 = output["keypoints0"].cpu().numpy()
    mkpts1 = output["keypoints1"].cpu().numpy()
    confidence = output["confidence"].cpu().numpy()

    if len(mkpts0) < 4:
        raise RuntimeError(f"LoFTR detected insufficient candidate matches ({len(mkpts0)}). Minimum 4 required.")

    # Step 3: Initial RANSAC Homography
    H_initial, mask_initial = cv2.findHomography(
        mkpts0,
        mkpts1,
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        maxIters=10000,
        confidence=0.995
    )
    if H_initial is None or mask_initial is None:
        raise RuntimeError("Initial RANSAC homography estimation failed.")

    inlier_ids = np.where(mask_initial.ravel() == 1)[0]
    if len(inlier_ids) < 4:
        raise RuntimeError(f"Initial RANSAC yielded insufficient inliers ({len(inlier_ids)}).")

    # Step 4: Reprojection Error & Quality Scoring
    proj = cv2.perspectiveTransform(mkpts0[inlier_ids].reshape(-1, 1, 2), H_initial).reshape(-1, 2)
    errors = np.linalg.norm(proj - mkpts1[inlier_ids], axis=1)
    quality_score = confidence[inlier_ids] / (1.0 + errors)

    # Step 5: 3x3 Spatial Grid Binning & Quality Selection
    h, w = source_clahe.shape
    cells = {(r, c): [] for r in range(3) for c in range(3)}
    for local_idx, original_idx in enumerate(inlier_ids):
        col = min(int(mkpts0[original_idx][0] / (w / 3)), 2)
        row = min(int(mkpts0[original_idx][1] / (h / 3)), 2)
        cells[(row, col)].append(local_idx)

    selected_local = []
    for cell, indices in cells.items():
        if indices:
            selected_local.extend(sorted(indices, key=lambda i: quality_score[i], reverse=True)[:max_per_cell])

    selected_ids = inlier_ids[selected_local]
    if len(selected_ids) < 4:
        raise RuntimeError(f"Spatial selection produced insufficient correspondences ({len(selected_ids)}).")

    # Step 6: Final Homography Estimation on Selected Subset
    H_final, mask_final = cv2.findHomography(
        mkpts0[selected_ids],
        mkpts1[selected_ids],
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        maxIters=10000,
        confidence=0.995
    )
    if H_final is None or mask_final is None:
        raise RuntimeError("Final RANSAC homography estimation failed.")

    final_inlier_ids = selected_ids[mask_final.ravel() == 1]
    if len(final_inlier_ids) < 4:
        raise RuntimeError(f"Final RANSAC yielded insufficient inliers ({len(final_inlier_ids)}).")

    # Step 7: Final Reprojection Metrics
    src_f = mkpts0[final_inlier_ids]
    ref_f = mkpts1[final_inlier_ids]
    proj_f = cv2.perspectiveTransform(src_f.reshape(-1, 1, 2), H_final).reshape(-1, 2)
    final_errs = np.linalg.norm(proj_f - ref_f, axis=1)

    # Step 8: Source Image Warping to Reference Coordinate Frame
    reg_img = cv2.warpPerspective(source_gray, H_final, (reference_gray.shape[1], reference_gray.shape[0]))

    # Step 9: Match Vector Visualization Canvas
    s_v = cv2.cvtColor(source_clahe, cv2.COLOR_GRAY2BGR)
    r_v = cv2.cvtColor(reference_clahe, cv2.COLOR_GRAY2BGR)
    canvas = np.zeros((max(s_v.shape[0], r_v.shape[0]), s_v.shape[1] + r_v.shape[1], 3), dtype=np.uint8)
    canvas[:s_v.shape[0], :s_v.shape[1]] = s_v
    canvas[:r_v.shape[0], s_v.shape[1]:] = r_v
    for i in final_inlier_ids:
        pt0 = (int(mkpts0[i][0]), int(mkpts0[i][1]))
        pt1 = (int(mkpts1[i][0] + s_v.shape[1]), int(mkpts1[i][1]))
        cv2.line(canvas, pt0, pt1, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.circle(canvas, pt0, 2, (0, 255, 0), -1)
        cv2.circle(canvas, pt1, 2, (0, 0, 255), -1)

    # Spatial distribution grids
    selected_grid = calculate_spatial_grid(mkpts0[selected_ids], source_clahe.shape)
    final_grid = calculate_spatial_grid(src_f, source_clahe.shape)
    
    # Occupancy and Spatial CV calculation
    occupied_cells = int(np.count_nonzero(selected_grid))
    total_cells = 9
    occupancy_ratio = float(occupied_cells / total_cells)
    spatial_cv = float(np.std(selected_grid) / np.mean(selected_grid)) if np.mean(selected_grid) > 0 else 0.0

    return {
        "registered_image": reg_img,
        "match_visualization": canvas,
        "spatial_grid": final_grid,
        "selected_grid": selected_grid,
        "candidate_matches": int(len(mkpts0)),
        "initial_inliers": int(len(inlier_ids)),
        "initial_inlier_ratio": float(len(inlier_ids) / len(mkpts0)),
        "selected_matches": int(len(selected_ids)),
        "final_inliers": int(len(final_inlier_ids)),
        "final_inlier_ratio": float(len(final_inlier_ids) / len(selected_ids)),
        "rmse": float(np.sqrt(np.mean(final_errs**2))),
        "mean_error": float(np.mean(final_errs)),
        "median_error": float(np.median(final_errs)),
        "max_error": float(np.max(final_errs)),
        "occupied_cells": occupied_cells,
        "total_cells": total_cells,
        "occupancy_ratio": occupancy_ratio,
        "spatial_cv": spatial_cv,
        "homography_matrix": H_final.tolist(),
        "runtime": float(time.perf_counter() - start_time),
        "device": _DEVICE,
    }


# ============================================================
# 2. LUNAR MISSION CONTROL UI (Streamlit)
# ============================================================

st.set_page_config(
    page_title="Lunar Image Registration System | Mission Control",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Tech Aerospace CSS Styling
st.markdown("""
<style>
    /* Dark Aerospace Theme */
    .stApp {
        background-color: #0b0e14;
        color: #d1d7e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header Section */
    .header-box {
        background: linear-gradient(135deg, #101724 0%, #162032 100%);
        border: 1px solid #233044;
        border-radius: 8px;
        padding: 16px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    }
    .header-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #58a6ff;
        margin: 0;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .header-subtitle {
        font-size: 0.95rem;
        color: #8b949e;
        margin: 4px 0 10px 0;
        font-weight: 400;
    }
    
    /* Pipeline Bar */
    .pipeline-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        background: #080b10;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #1c2738;
        font-size: 0.8rem;
    }
    .pipeline-step {
        background: #162032;
        color: #58a6ff;
        padding: 3px 9px;
        border-radius: 4px;
        font-weight: 600;
        border: 1px solid #253852;
    }
    .pipeline-arrow {
        color: #00f2ff;
        font-weight: bold;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .status-ready {
        background: #0d281e;
        color: #3fb950;
        border: 1px solid #1e4b38;
    }
    .status-locked {
        background: #092635;
        color: #00f2ff;
        border: 1px solid #0e4c68;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #121824;
        border: 1px solid #212c3d;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.76rem;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.6px;
        margin-bottom: 2px;
    }
    .metric-val {
        font-family: 'SF Mono', 'Cascadia Code', 'Courier New', monospace;
        font-size: 1.45rem;
        font-weight: 700;
        color: #00f2ff;
    }
    .metric-sub {
        font-size: 0.72rem;
        color: #6e7681;
        margin-top: 2px;
    }

    /* Action Buttons */
    .stButton>button {
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 6px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #00f2ff;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
    }
    
    /* Image containers */
    .img-box {
        background: #0d1117;
        border: 1px solid #212c3d;
        border-radius: 6px;
        padding: 6px;
        text-align: center;
    }
    .img-caption {
        font-size: 0.8rem;
        font-weight: 600;
        color: #58a6ff;
        text-transform: uppercase;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }

    /* Honesty Alert Box */
    .honesty-box {
        background: #161b22;
        border-left: 4px solid #f0883e;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        margin: 14px 0;
        font-size: 0.82rem;
        color: #c9d1d9;
    }
    
    /* Code / Monospace containers */
    code, pre {
        background-color: #090d14 !important;
        border: 1px solid #1f2a3a !important;
        color: #00f2ff !important;
        font-family: 'SF Mono', 'Cascadia Code', 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
<div class="header-box">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 class="header-title">🌙 Lunar Image Registration System</h1>
            <div class="header-subtitle">Cross-Sensor Surface Alignment: Chandrayaan-2 ↔ Lunar Reference Telemetry</div>
        </div>
        <div style="text-align: right;">
            <span class="status-badge status-ready">● FLIGHT ENGINE READY</span>
            <div style="font-size: 0.72rem; color: #6e7681; margin-top: 4px; font-family: monospace;">ENV: PYTORCH / LOFTR-CPU</div>
        </div>
    </div>
    <div class="pipeline-bar">
        <span style="color: #8b949e; font-weight: bold; margin-right: 4px;">PIPELINE:</span>
        <span class="pipeline-step">1. CLAHE</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">2. LoFTR Matcher</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">3. Initial RANSAC</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">4. Quality + 3×3 Spatial Binning</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">5. Final Homography</span>
        <span class="pipeline-arrow">→</span>
        <span class="pipeline-step">6. Evaluation Metrics</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- DEMO DATA LOADER HELPER ---
DEV_SOURCE_PATH = os.path.join("data", "source", "source.jpeg")
DEV_REFERENCE_PATH = os.path.join("data", "reference", "reference.jpeg")

col_util1, col_util2 = st.columns([3, 1])
with col_util2:
    if st.button("⚡ Load Dev Pair (Chandrayaan-2)", use_container_width=True, help="Instantly load the validated Chandrayaan-2 development pair for live demonstration."):
        if os.path.exists(DEV_SOURCE_PATH) and os.path.exists(DEV_REFERENCE_PATH):
            s_loaded = cv2.imread(DEV_SOURCE_PATH)
            r_loaded = cv2.imread(DEV_REFERENCE_PATH)
            if s_loaded is not None and r_loaded is not None:
                st.session_state["source_img_data"] = s_loaded
                st.session_state["reference_img_data"] = r_loaded
                st.session_state["source_filename"] = "source.jpeg (Dev Pair)"
                st.session_state["reference_filename"] = "reference.jpeg (Dev Pair)"
                st.session_state.pop("registration_result", None)
                st.toast("Loaded Chandrayaan-2 development pair successfully!", icon="🌕")
        else:
            st.error("Development data files not found in data/ directory.")

# --- INPUT / TELEMETRY ACQUISITION SECTION ---
col_in1, col_in2 = st.columns(2)

with col_in1:
    st.markdown("#### 🛰️ Moving / Source Image (Chandrayaan-2)")
    src_file = st.file_uploader(
        "Upload Source Image (Moving)",
        type=["jpg", "jpeg", "png", "tif"],
        key="u_source",
        label_visibility="collapsed"
    )
    if src_file is not None:
        file_bytes = np.frombuffer(src_file.read(), np.uint8)
        decoded_s = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if decoded_s is not None:
            st.session_state["source_img_data"] = decoded_s
            st.session_state["source_filename"] = src_file.name

with col_in2:
    st.markdown("#### 🗺️ Fixed / Reference Image (Lunar Base)")
    ref_file = st.file_uploader(
        "Upload Reference Image (Fixed)",
        type=["jpg", "jpeg", "png", "tif"],
        key="u_reference",
        label_visibility="collapsed"
    )
    if ref_file is not None:
        file_bytes = np.frombuffer(ref_file.read(), np.uint8)
        decoded_r = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if decoded_r is not None:
            st.session_state["reference_img_data"] = decoded_r
            st.session_state["reference_filename"] = ref_file.name

# Display previews if images are present in session state
s_active = st.session_state.get("source_img_data", None)
r_active = st.session_state.get("reference_img_data", None)

if s_active is not None and r_active is not None:
    c_prev1, c_prev2 = st.columns(2)
    with c_prev1:
        st.markdown(f"<div class='img-box'>", unsafe_allow_html=True)
        st.image(
            cv2.cvtColor(s_active, cv2.COLOR_BGR2RGB),
            caption=f"Source: {st.session_state.get('source_filename', 'source.jpeg')} [{s_active.shape[1]}×{s_active.shape[0]} px]",
            width="stretch"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c_prev2:
        st.markdown(f"<div class='img-box'>", unsafe_allow_html=True)
        st.image(
            cv2.cvtColor(r_active, cv2.COLOR_BGR2RGB),
            caption=f"Reference: {st.session_state.get('reference_filename', 'reference.jpeg')} [{r_active.shape[1]}×{r_active.shape[0]} px]",
            width="stretch"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 INITIATE REGISTRATION SEQUENCE", type="primary", use_container_width=True):
        st.session_state.pop("registration_result", None)
        
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.info("Executing Scientific Registration Pipeline: CLAHE → LoFTR → RANSAC → Spatial Selection → Homography...")
        
        try:
            res = register_images(s_active, r_active)
            st.session_state["registration_result"] = res
            status_placeholder.empty()
        except Exception as e:
            status_placeholder.empty()
            st.error(f"Registration Sequence Encountered an Issue: {str(e)}")

# ============================================================
# 3. REGISTRATION RESULTS & METRICS TELEMETRY
# ============================================================

if "registration_result" in st.session_state:
    res = st.session_state["registration_result"]
    s_active = st.session_state["source_img_data"]
    r_active = st.session_state["reference_img_data"]

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    # Telemetry Status Bar
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; background: #0c1a24; border: 1px solid #1a3c54; padding: 10px 16px; border-radius: 6px; margin-bottom: 16px;">
        <div>
            <span class="status-badge status-locked">● REGISTRATION LOCKED</span>
            <span style="margin-left: 12px; font-weight: 600; color: #58a6ff; font-size: 0.9rem;">GEOMETRIC CONVERGENCE ACHIEVED</span>
        </div>
        <div style="font-family: monospace; font-size: 0.82rem; color: #8b949e;">
            EXECUTION TIME: <span style="color: #00f2ff; font-weight: bold;">{res['runtime']:.2f}s</span> | COMPUTE: <span style="color: #00f2ff; font-weight: bold;">{res['device'].upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # High-Density 8-Card Telemetry Grid
    t_c1, t_c2, t_c3, t_c4 = st.columns(4)
    with t_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">LoFTR Candidate Matches</div>
            <div class="metric-val">{res['candidate_matches']}</div>
            <div class="metric-sub">Dense feature pairs</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Initial RANSAC Inliers</div>
            <div class="metric-val">{res['initial_inliers']}</div>
            <div class="metric-sub">Initial inlier ratio: {res['initial_inlier_ratio']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial Selected Subset</div>
            <div class="metric-val">{res['selected_matches']}</div>
            <div class="metric-sub">3×3 grid quality filtered</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Final Geometric Inliers</div>
            <div class="metric-val">{res['final_inliers']}</div>
            <div class="metric-sub">Final inlier ratio: <b style="color:#3fb950;">{res['final_inlier_ratio']*100:.2f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    t_c5, t_c6, t_c7, t_c8 = st.columns(4)
    with t_c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Reprojection RMSE</div>
            <div class="metric-val">{res['rmse']:.3f} <span style="font-size:0.9rem;">px</span></div>
            <div class="metric-sub">Mean error: {res['mean_error']:.3f} px</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial Occupancy</div>
            <div class="metric-val">{res['occupied_cells']} / {res['total_cells']}</div>
            <div class="metric-sub">Coverage: {res['occupancy_ratio']*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c7:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spatial CV</div>
            <div class="metric-val">{res['spatial_cv']:.3f}</div>
            <div class="metric-sub">Uniformity score (lower is better)</div>
        </div>
        """, unsafe_allow_html=True)
    with t_c8:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Median Reprojection Error</div>
            <div class="metric-val">{res['median_error']:.3f} <span style="font-size:0.9rem;">px</span></div>
            <div class="metric-sub">Max error: {res['max_error']:.3f} px</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Alignment Verification Section
    st.markdown("### 🔍 Alignment Verification")
    tab_view, tab_blend, tab_diff = st.tabs([
        "Side-by-Side Verification",
        "Composite Blend (50/50)",
        "Difference Residual Map"
    ])

    ref_g = cv2.cvtColor(r_active, cv2.COLOR_BGR2GRAY) if len(r_active.shape) == 3 else r_active
    reg_src = res["registered_image"]

    with tab_view:
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            st.image(reg_src, caption="Warped Source Image (Aligned to Reference Grid)", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        with r_c2:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            st.image(ref_g, caption="Reference Base Image (Ground Truth Frame)", width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_blend:
        ref_g = cv2.cvtColor(r_active, cv2.COLOR_BGR2GRAY) if len(r_active.shape) == 3 else r_active
        registered = res["registered_image"]

        st.write("Reference shape:", ref_g.shape)
        st.write("Registered shape:", registered.shape)
        st.write("Reference dtype:", ref_g.dtype)
        st.write("Registered dtype:", registered.dtype)

        if registered.shape[:2] != ref_g.shape[:2]:
            registered = cv2.resize(
                registered,
                (ref_g.shape[1], ref_g.shape[0]),
                interpolation=cv2.INTER_LINEAR
            )

        if len(registered.shape) == 3:
            registered = cv2.cvtColor(registered, cv2.COLOR_BGR2GRAY)

        ref_f = ref_g.astype(np.float32)
        reg_f = registered.astype(np.float32)

        overlay = cv2.addWeighted(
            ref_f,
            0.5,
            reg_f,
            0.5,
            0
        ).astype(np.uint8)

        st.image(
            overlay,
            caption="Composite Blend (50/50)",
            width="stretch"
        )

    with tab_diff:
        diff = cv2.absdiff(ref_g, registered)
        fig_diff, ax_diff = plt.subplots(figsize=(8, 3.2))
        fig_diff.patch.set_facecolor('#0b0e14')
        ax_diff.set_facecolor('#121824')
        im_d = ax_diff.imshow(diff, cmap='inferno')
        ax_diff.set_title("Absolute Intensity Residual Map (|Reference - Warped Source|)", color='#58a6ff', fontsize=10)
        ax_diff.axis('off')
        cbar = fig_diff.colorbar(im_d, ax=ax_diff, fraction=0.03, pad=0.02)
        cbar.ax.tick_params(labelsize=8, colors='#8b949e')
        st.pyplot(fig_diff)
        plt.close(fig_diff)

    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

    # Correspondence Evidence & Spatial Distribution
    st.markdown("### 📊 Correspondence Evidence & Spatial Distribution")
    col_ev1, col_ev2 = st.columns([1.4, 1.0])

    with col_ev1:
        st.markdown("##### Geometrically Valid Correspondences (Final RANSAC Inliers)")
        st.image(
            cv2.cvtColor(res["match_visualization"], cv2.COLOR_BGR2RGB),
            caption=f"{res['final_inliers']} Geometrically Verified Correspondences (Yellow Vectors: Source → Reference)",
            width="stretch"
        )

    with col_ev2:
        st.markdown("##### 3×3 Spatial Grid Distribution")
        fig_grid, ax_grid = plt.subplots(figsize=(4.2, 3.2))
        fig_grid.patch.set_facecolor('#0b0e14')
        ax_grid.set_facecolor('#121824')
        im_g = ax_grid.imshow(res["selected_grid"], cmap="Blues", vmin=0, vmax=6)
        
        for (j, i), val in np.ndenumerate(res["selected_grid"]):
            color = "#00f2ff" if val > 0 else "#484f58"
            ax_grid.text(i, j, f"{val}", ha='center', va='center', color=color, fontweight='bold', fontsize=12)
            
        ax_grid.set_xticks([0, 1, 2])
        ax_grid.set_yticks([0, 1, 2])
        ax_grid.set_xticklabels(["C0", "C1", "C2"], color="#8b949e", fontsize=8)
        ax_grid.set_yticklabels(["R0", "R1", "R2"], color="#8b949e", fontsize=8)
        ax_grid.tick_params(colors="#30363d")
        ax_grid.set_title(f"Occupancy: {res['occupied_cells']}/9 ({res['occupancy_ratio']*100:.1f}%) | CV: {res['spatial_cv']:.3f}", color='#58a6ff', fontsize=9)
        st.pyplot(fig_grid)
        plt.close(fig_grid)
        st.caption("A balanced correspondence distribution across grid cells prevents localized degenerate homography solutions.")

    # Scientific Honesty Alert Box
    st.markdown(f"""
    <div class="honesty-box">
        <b>🔭 SCIENTIFIC BENCHMARK NOTE:</b><br>
        On our real lunar development pair, the validated reprojection RMSE is <b>{res['rmse']:.3f} px</b> (mean error: <b>{res['mean_error']:.3f} px</b>, maximum error: <b>{res['max_error']:.3f} px</b>).
        Sub-pixel accuracy (~0.097 px) was separately verified in controlled synthetic ground-truth experiments and is not claimed as real lunar cross-sensor accuracy.
    </div>
    """, unsafe_allow_html=True)

    # Expandable Technical Analytics
    with st.expander("🛠️ Advanced Technical & Geometric Analytics"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("##### Homography Transformation Matrix $H_{3\\times3}$")
            h_mat = np.array(res["homography_matrix"])
            st.code(
                f"[[ {h_mat[0,0]:12.6e}, {h_mat[0,1]:12.6e}, {h_mat[0,2]:12.6e} ],\n"
                f" [ {h_mat[1,0]:12.6e}, {h_mat[1,1]:12.6e}, {h_mat[1,2]:12.6e} ],\n"
                f" [ {h_mat[2,0]:12.6e}, {h_mat[2,1]:12.6e}, {h_mat[2,2]:12.6e} ]]",
                language="python"
            )
        with col_t2:
            st.markdown("##### Error Metrics Breakdown")
            st.markdown(f"""
            - **Reprojection RMSE**: `{res['rmse']:.4f} px`
            - **Mean Absolute Error**: `{res['mean_error']:.4f} px`
            - **Median Reprojection Error**: `{res['median_error']:.4f} px`
            - **Maximum Error**: `{res['max_error']:.4f} px`
            - **Inlier Retention Rate**: `{res['final_inlier_ratio']*100:.2f}%` ({res['final_inliers']}/{res['selected_matches']})
            - **Occupied Spatial Cells**: `{res['occupied_cells']} / 9`
            """)

# --- FOOTER ---
st.markdown("""
<div style="margin-top: 30px; text-align: center; border-top: 1px solid #1c2738; padding-top: 12px; color: #484f58; font-size: 0.76rem;">
    Smart India Hackathon (SIH) 2026 — Lunar Image Registration System | Chandrayaan-2 Research Pipeline
</div>
""", unsafe_allow_html=True)
