# Phase 23A.9 — External Reference Product Lineage & Candidate Audit

**Project:** LunarReg — Chandrayaan-2 OHRC Registration Benchmark  
**Phase:** 23A.9 — External Reference Product Provenance Identification  
**Status:** **`COMPLETE & AUDITED`**  
**Date:** September 24, 2026  
**Governing Discipline:** Research-Only — Production Code Frozen for this audit; historical baseline provenance not independently verified.  

---

## 1. Candidate Class Lineage Investigation

In accordance with Phase 23A.9 requirements, six distinct candidate classes were investigated without presupposing any candidate as the winner:

### Class A: Chandrayaan-2 TMC/TMC-2 Mapping Products
- **Source Institution:** ISRO / ISSDC / SAC.
- **Available Products:** Level-2 ortho-images (`_d_oth_`) and Level-2 DEMs (`_d_dtm_`) archived under PDS4 standard.
- **Analysis:** Single TMC-2 swaths ($20\text{ km}$, $4,000\text{ px}$) cannot account for Pair 01 ($29.58\text{ km}$, $5,916\text{ px}$). A multi-strip mosaic is geometrically required to cover the area.
- **Lineage Finding:** Candidate single-strip products are **`REJECTED`**; candidate multi-strip mosaic remains **`PLAUSIBLE BUT UNVERIFIED`** due to zero embedded metadata.

### Class B: LROC NAC Polar Mosaics
- **Source Institution:** NASA / Arizona State University (ASU) / LROC Science Operations Center.
- **Available Products:** Controlled and Uncontrolled South Pole Mosaics (84°S–90°S).
- **Analysis:** Official LROC NAC polar mosaics are produced and archived at $1.0\text{ m/px}$ or $2.0\text{ m/px}$. No official $5.0\text{ m/px}$ LROC NAC image mosaic is distributed by ASU/PDS.
- **Lineage Finding:** Rejected as a direct product source (**`MISMATCH ON SCALE`**). Can only be hypothesized as a secondary resampled derivative, which cannot be verified without resampling parameters.

### Class C: LROC/LOLA-Derived Polar Products
- **Source Institution:** NASA GSFC / PDS Geosciences.
- **Available Products:** LOLA LDEM South Pole 5m DEMs (Barker et al., 2021) and shaded relief.
- **Analysis:** LOLA LDEM provides high geodetic accuracy (tied to MOON_ME_DE421), but is an elevation raster (topographic heights), not optical surface reflectance.
- **Lineage Finding:** Conclusively **`REJECTED`** due to sensor modality mismatch.

### Class D: Other Official South-Polar Lunar Map/Mosaic Products
- **Candidate Datasets:** KPLO ShadowCam (PSR-only), Chang'e-2/7 (7m global DOM), Clementine 750nm (100m).
- **Lineage Finding:** Conclusively **`REJECTED`** (resolution, coverage, or radiometric incompatibilities).

### Class E: Derived Web GIS Basemaps
- **Candidate Platforms:** ASU QuickMap, USGS Map-a-Planet / Astropedia.
- **Analysis:** Web GIS platforms can export user-defined bounding boxes at $5.0\text{ m/px}$ using GDAL MapServer, which generates GeoTIFFs with generic ESRI GeoKeys and stripped identity tags.
- **Lineage Finding:** Functionally compatible with the export artifact characteristics, but provides zero definitive product lineage without transaction logs.

### Class F: Custom Mentor Benchmark Reference Product
- **Source Institution:** SIH 2026 Problem Statement Organizers / ISRO SAC Mentors.
- **Delivery Evidence:** Zip archive `data_for_sih_2026.zip` contains 4 reference GeoTIFFs created on Feb 17, 2026.
- **Packaging Audit:** The file naming convention (`OHRXXD..._reference_at_5m.tif`) mirrors the OHRC moving source strip product IDs, demonstrating that the reference files were customized and titled specifically for benchmark evaluation.
- **Lineage Finding:** Candidate 07 identifies the benchmark delivery container, but upstream cartographic product provenance remains unresolved.

---

## 2. Mandatory Non-Inference Enforcement

Phase 23A.9 strictly prohibits inferring basemap provenance from:
1. $5.000\text{ m/px}$ resolution (compatible with TMC-2, downsampled LROC, or custom GIS exports);
2. Polar Stereographic projection (standard cartographic projection for all lunar polar products);
3. $1,737,400.0\text{ m}$ spherical radius (official IAU/ISRO/NASA lunar reference sphere);
4. South Pole geographic coverage (common to all polar missions);
5. Visual or textural appearance (lunar regolith morphology is identical across sensors).

> ### **Lineage Conclusion:**
> In the absence of positive product-level metadata (such as sensor name, processing pipeline version, or PDS4 label), the originating cartographic source of the mentor reference rasters remains **`UNRESOLVED`**.
