import time
import cv2
import numpy as np
import torch
import streamlit as st
import matplotlib.pyplot as plt
from kornia.feature import LoFTR

# ============================================================
# 1. CORE REGISTRATION ENGINE (Logically Intact)
# ============================================================

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@st.cache_resource
def load_loftr_matcher():
    matcher = LoFTR(pretrained="outdoor").to(_DEVICE)
    matcher.eval()
    return matcher

def preprocess_image(image):
    if image is None: raise ValueError("Input image is None.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return gray, clahe.apply(gray)

def calculate_spatial_grid(points, image_shape, rows=3, cols=3):
    h, w = image_shape
    grid = np.zeros((rows, cols), dtype=int)
    for x, y in points:
        col = min(int(x / (w / cols)), cols - 1)
        row = min(int(y / (h / rows)), rows - 1)
        grid[row, col] += 1
    return grid

def register_images(source_image, reference_image, max_per_cell=6, ransac_threshold=3.0):
    start_time = time.perf_counter()
    _MATCHER = load_loftr_matcher()
    source_gray, source_clahe = preprocess_image(source_image)
    reference_gray, reference_clahe = preprocess_image(reference_image)

    source_tensor = torch.from_numpy(source_clahe.astype(np.float32) / 255.0)[None, None].to(_DEVICE)
    reference_tensor = torch.from_numpy(reference_clahe.astype(np.float32) / 255.0)[None, None].to(_DEVICE)

    with torch.no_grad():
        output = _MATCHER({"image0": source_tensor, "image1": reference_tensor})

    mkpts0, mkpts1, confidence = output["keypoints0"].cpu().numpy(), output["keypoints1"].cpu().numpy(), output["confidence"].cpu().numpy()
    H_initial, mask_initial = cv2.findHomography(mkpts0, mkpts1, cv2.RANSAC, ransac_threshold)
    if H_initial is None: raise RuntimeError("Initial RANSAC failed.")

    inlier_ids = np.where(mask_initial.ravel() == 1)[0]
    proj = cv2.perspectiveTransform(mkpts0[inlier_ids].reshape(-1, 1, 2), H_initial).reshape(-1, 2)
    errors = np.linalg.norm(proj - mkpts1[inlier_ids], axis=1)
    quality_score = confidence[inlier_ids] / (1.0 + errors)

    h, w = source_clahe.shape
    cells = {(r, c): [] for r in range(3) for c in range(3)}
    for local_idx, original_idx in enumerate(inlier_ids):
        col, row = min(int(mkpts0[original_idx][0] / (w / 3)), 2), min(int(mkpts0[original_idx][1] / (h / 3)), 2)
        cells[(row, col)].append(local_idx)

    selected_local = []
    for cell, indices in cells.items():
        selected_local.extend(sorted(indices, key=lambda i: quality_score[i], reverse=True)[:max_per_cell])

    selected_ids = inlier_ids[selected_local]
    H_final, mask_final = cv2.findHomography(mkpts0[selected_ids], mkpts1[selected_ids], cv2.RANSAC, ransac_threshold)
    final_inlier_ids = selected_ids[mask_final.ravel() == 1]

    src_f, ref_f = mkpts0[final_inlier_ids], mkpts1[final_inlier_ids]
    proj_f = cv2.perspectiveTransform(src_f.reshape(-1, 1, 2), H_final).reshape(-1, 2)
    final_errs = np.linalg.norm(proj_f - ref_f, axis=1)

    reg_img = cv2.warpPerspective(source_gray, H_final, (reference_gray.shape[1], reference_gray.shape[0]))

    s_v, r_v = cv2.cvtColor(source_clahe, cv2.COLOR_GRAY2BGR), cv2.cvtColor(reference_clahe, cv2.COLOR_GRAY2BGR)
    canvas = np.zeros((max(s_v.shape[0], r_v.shape[0]), s_v.shape[1] + r_v.shape[1], 3), dtype=np.uint8)
    canvas[:s_v.shape[0], :s_v.shape[1]], canvas[:r_v.shape[0], s_v.shape[1]:] = s_v, r_v
    for i in final_inlier_ids:
        cv2.line(canvas, (int(mkpts0[i][0]), int(mkpts0[i][1])), (int(mkpts1[i][0] + s_v.shape[1]), int(mkpts1[i][1])), (0, 255, 255), 1)

    return {
        "registered_image": reg_img, "match_visualization": canvas, "spatial_grid": calculate_spatial_grid(src_f, source_clahe.shape),
        "candidate_matches": len(mkpts0), "initial_inliers": len(inlier_ids), "selected_matches": len(selected_ids), "final_inliers": len(final_inlier_ids),
        "final_inlier_ratio": len(final_inlier_ids)/len(selected_ids), "rmse": float(np.sqrt(np.mean(final_errs**2))), "mean_error": float(np.mean(final_errs)),
        "median_error": float(np.median(final_errs)), "max_error": float(np.max(final_errs)), "occupancy_ratio": np.count_nonzero(calculate_spatial_grid(src_f, source_clahe.shape))/9,
        "spatial_cv": np.std(calculate_spatial_grid(src_f, source_clahe.shape))/np.mean(calculate_spatial_grid(src_f, source_clahe.shape)), "runtime": time.perf_counter() - start_time, "device": _DEVICE,
        "occupied_cells": int(np.count_nonzero(calculate_spatial_grid(src_f, source_clahe.shape))), "total_cells": 9
    }

# ============================================================
# 2. POLISHED MISSION CONTROL UI
# ============================================================

st.set_page_config(page_title="Lunar Registration System", page_icon="🌙", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e6ed; }
    .stMetric { background-color: #1c2128; border: 1px solid #30363d; padding: 10px; border-radius: 5px; }
    [data-testid='stMetricValue'] { color: #00f2ff; font-family: 'Courier New', monospace; }
    .img-container { border: 1px solid #30363d; padding: 5px; border-radius: 4px; background: #161b22; }
    .stButton>button { background-color: #008bcf; color: white; border: none; font-weight: bold; width: 100%; height: 3.5em; }
    h1, h2, h3 { color: #58a6ff; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

st.title("🌙 Lunar Image Registration System")
st.markdown("**Chandrayaan-2 ↔ Lunar Reference Image Registration**")
st.caption("Pipeline: CLAHE → LoFTR → RANSAC → Quality + Spatial Selection → Homography")
st.divider()

# --- Input Section ---
col_in1, col_in2 = st.columns(2)
with col_in1: src_file = st.file_uploader("Source / Moving Image", type=["jpg","jpeg","png","tif"], key="u_source")
with col_in2: ref_file = st.file_uploader("Reference / Fixed Image", type=["jpg","jpeg","png","tif"], key="u_reference")

if src_file and ref_file:
    s_img = cv2.imdecode(np.frombuffer(src_file.read(), np.uint8), cv2.IMREAD_COLOR)
    r_img = cv2.imdecode(np.frombuffer(ref_file.read(), np.uint8), cv2.IMREAD_COLOR)
    
    c_pre1, c_pre2 = st.columns(2)
    c_pre1.image(cv2.cvtColor(s_img, cv2.COLOR_BGR2RGB), caption="Source Preview", use_container_width=True)
    c_pre2.image(cv2.cvtColor(r_img, cv2.COLOR_BGR2RGB), caption="Reference Preview", use_container_width=True)

    if st.button("🚀 INITIATE ALIGNMENT SEQUENCE", type="primary"):
        st.session_state.pop("registration_result", None)
        with st.spinner("Executing Scientific Pipeline..."):
            try:
                res = register_images(s_img, r_img)
                st.session_state["registration_result"] = res
                st.session_state["reference_img_data"] = r_img
            except Exception as e:
                st.error(f"Alignment Failed: {str(e)}")

# --- Result Section ---
if "registration_result" in st.session_state:
    res = st.session_state["registration_result"]
    r_img = st.session_state["reference_img_data"]
    st.success("Registration Locked.")

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("LoFTR Matches", res["candidate_matches"])
    m_c2.metric("Final Inliers", res["final_inliers"])
    m_c3.metric("Inlier Ratio", f"{res['final_inlier_ratio']*100:.2f}%")
    m_c4.metric("RMSE", f"{res['rmse']:.3f} px")

    m_c5, m_c6, m_c7, m_c8 = st.columns(4)
    m_c5.metric("Selected Subset", res["selected_matches"])
    m_c6.metric("Spatial Coverage", f"{res['occupancy_ratio']*100:.1f}%")
    m_c7.metric("Spatial CV", f"{res['spatial_cv']:.3f}")
    m_c8.metric("Runtime", f"{res['runtime']:.2f}s")

    st.subheader("Alignment Verification")
    r_col1, r_col2 = st.columns(2)
    r_col1.image(res["registered_image"], caption="Registered Source", use_container_width=True)
    r_col2.image(cv2.cvtColor(r_img, cv2.COLOR_BGR2GRAY), caption="Reference", use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Alignment Overlay", "Correspondence Set", "Spatial Heatmap"])
    with tab1:
        ref_g = cv2.cvtColor(r_img, cv2.COLOR_BGR2GRAY)
        overlay = cv2.addWeighted(ref_g.astype(float), 0.5, res["registered_image"].astype(float), 0.5, 0).astype(np.uint8)
        st.image(overlay, caption="Composite Blend (50/50)", use_container_width=True)
    with tab2:
        st.image(cv2.cvtColor(res["match_visualization"], cv2.COLOR_BGR2RGB), caption="RANSAC Verified Pairs", use_container_width=True)
    with tab3:
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#1c2128')
        im = ax.imshow(res["spatial_grid"], cmap="Blues")
        for (j,i), v in np.ndenumerate(res["spatial_grid"]): ax.text(i,j,str(v),ha='center',va='center',color='white',fontweight='bold')
        ax.axis('off'); st.pyplot(fig)

    with st.expander("Technical Analytics"):
        st.json({k: v for k, v in res.items() if isinstance(v, (int, float, str))})
