# Authoritative South Polar Digital Elevation Model (DEM) Verification Report

**Document Status:** FORMAL RESEARCH TERRAIN VERIFICATION REPORT  
**Phase:** 22 — Authoritative 3D Input Acquisition & Verification  
**Mission Context:** Chandrayaan-2 OHRC Mentor Benchmark  
**Production Status:** 100% FROZEN AND UNTOUCHED  

---

## 1. Executive Summary
This report evaluates official lunar topographic models produced by the NASA Lunar Reconnaissance Orbiter (LRO) Lunar Orbiter Laser Altimeter (LOLA) science team at Goddard Space Flight Center (GSFC) and archived at the NASA Planetary Data System (PDS) Geosciences Node.

Two primary candidate products were investigated for 3D ray-terrain intersection:
1. **`LDEM_80S_20M`**: 20 m/pixel Polar Stereographic Gridded Data Record covering $80^\circ\text{S} - 90^\circ\text{S}$.
2. **`LDEM_875S_5M`**: 5 m/pixel Polar Stereographic Gridded Data Record covering $87.5^\circ\text{S} - 90^\circ\text{S}$.

**Key Scientific Determination:**  
The 5 m/pixel DEM covers **only `OHRC_PAIR_01`** (which lies at $89.25^\circ\text{S} - 89.47^\circ\text{S}$). It provides **zero coverage** for `OHRC_PAIR_02`, `OHRC_PAIR_03`, and `OHRC_PAIR_04` (which extend north to $83.76^\circ\text{S} - 85.37^\circ\text{S}$).  
Consequently, **`LDEM_80S_20M` is the ONLY unified, consistent DEM product covering all four mentor OHRC pairs**.

---

## 2. Candidate Product Specifications (Official PDS Metadata)

Both products were audited directly via their official detached PDS3 labels (`.LBL`), which were downloaded and verified locally.

| Specification Attribute | `LDEM_80S_20M` (20 m/px) | `LDEM_875S_5M` (5 m/px) |
| :--- | :--- | :--- |
| **PDS Product ID** | `LRO-L-LOLA-4-GDR-V1.0` (`LDEM_80S_20M`) | `LRO-L-LOLA-4-GDR-V1.0` (`LDEM_875S_5M`) |
| **Producer Organization** | NASA Goddard Space Flight Center (GSFC) / LOLA Team | NASA Goddard Space Flight Center (GSFC) / LOLA Team |
| **Principal Investigator** | Dr. David E. Smith, GSFC | Dr. David E. Smith, GSFC |
| **Binary Data URL** | `https://pds-geosciences.wustl.edu/.../LDEM_80S_20M.IMG` | `https://pds-geosciences.wustl.edu/.../LDEM_875S_5M.IMG` |
| **Label URL** | `https://pds-geosciences.wustl.edu/.../LDEM_80S_20M.LBL` | `https://pds-geosciences.wustl.edu/.../LDEM_875S_5M.LBL` |
| **Label SHA-256** | `0793611cde045e6f8eec1365b2500084522fdc6d515ec30b5ab2427de62a6624` | `3cc0c25bd0e6b6ebb30a66d3628d98191b8229fc5639545a538a9f4af8b94bf1` |
| **Spatial Coverage** | **$80.0^\circ\text{S}$ to $90.0^\circ\text{S}$** ($0^\circ - 360^\circ\text{E}$) | **$87.5^\circ\text{S}$ to $90.0^\circ\text{S}$** ($0^\circ - 360^\circ\text{E}$) |
| **Grid Resolution** | **20.0 m/pixel** ($1516.17\text{ pix/deg}$) | **5.0 m/pixel** ($6064.67\text{ pix/deg}$) |
| **Raster Dimensions** | **30,400 lines $\times$ 30,400 samples** | **30,336 lines $\times$ 30,336 samples** |
| **Total Binary Size** | **$1,848,320,000\text{ bytes}$ (~1.85 GB / 1762.7 MB)** | **$1,840,545,792\text{ bytes}$ (~1.84 GB / 1755.3 MB)** |
| **Data Encoding** | 16-bit signed integer (`LSB_INTEGER`), pixel-registered | 16-bit signed integer (`LSB_INTEGER`), pixel-registered |
| **Map Projection** | Polar Stereographic, true at pole | Polar Stereographic, true at pole |
| **Center Coordinates** | Lat: $-90.0^\circ$, Lon: $0.0^\circ$ | Lat: $-90.0^\circ$, Lon: $0.0^\circ$ |
| **Reference Sphere** | $R_{\text{ref}} = 1737.400\text{ km}$ ($1,737,400.0\text{ m}$) | $R_{\text{ref}} = 1737.400\text{ km}$ ($1,737,400.0\text{ m}$) |
| **Coordinate Frame** | `MEAN EARTH/POLAR AXIS OF DE421` | `MEAN EARTH/POLAR AXIS OF DE421` |
| **Vertical Height Formula** | $\text{Elevation (m)} = \text{DN} \times 0.5$ | $\text{Elevation (m)} = \text{DN} \times 0.5$ |
| **Planetary Radius Formula** | $R = (\text{DN} \times 0.5) + 1,737,400.0\text{ m}$ | $R = (\text{DN} \times 0.5) + 1,737,400.0\text{ m}$ |
| **Altimetry Data Source** | LOLA Laser 1 & 2 through phase `LRO_ES_54` | LOLA Laser 1 & 2 through phase `LRO_ES_54` |
| **Vertical Uncertainty** | Residual point error $\sim 0.5 - 1.0\text{ m}$; GRAIL 900C consistent | Residual point error $\sim 0.5 - 1.0\text{ m}$; GRAIL 900C consistent |

---

## 3. Mentor OHRC Pair Footprint Coverage Analysis

The latitude boundaries of each mentor OHRC source strip were evaluated against the spatial limits of both candidate DEM products:

```
  Pole (-90°S) -----------------------------------------------------------
               |  OHRC_PAIR_01: -89.25° to -89.47°S (COVERED BY 5m & 20m)
 -87.5°S ----- |-----------------------------------------------------------  <- Boundary of LDEM_875S_5M
               |  OHRC_PAIR_02: -84.54° to -85.35°S (COVERED BY 20m ONLY)
               |  OHRC_PAIR_03: -84.54° to -85.37°S (COVERED BY 20m ONLY)
               |  OHRC_PAIR_04: -83.76° to -84.60°S (COVERED BY 20m ONLY)
 -80.0°S ----- |-----------------------------------------------------------  <- Boundary of LDEM_80S_20M
               |  (North of -80°S: Neither polar product covers)
```

### Detailed Per-Pair Evaluation:

### 3.1 OHRC_PAIR_01 (South Pole Core Swath)
- **Latitude Span:** $-89.256269^\circ$ to $-89.468902^\circ\text{S}$
- **Longitude Span:** $158.660785^\circ$ to $245.779169^\circ\text{E}$
- **Coverage by `LDEM_875S_5M`:** **100.0% COVERED** (entire footprint is south of $-87.5^\circ$).
- **Coverage by `LDEM_80S_20M`:** **100.0% COVERED** (entire footprint is south of $-80.0^\circ$).
- **Recommendation:** Suitable for both products. `LDEM_875S_5M` offers matched 5 m spatial resolution; `LDEM_80S_20M` offers multi-pair consistency.

### 3.2 OHRC_PAIR_02 (Amundsen Rim Region)
- **Latitude Span:** $-84.540314^\circ$ to $-85.353908^\circ\text{S}$
- **Longitude Span:** $26.723277^\circ$ to $31.180635^\circ\text{E}$
- **Coverage by `LDEM_875S_5M`:** **0.0% COVERED** (Footprint terminates at $-85.35^\circ$, completely north of the $-87.5^\circ$ cutoff).
- **Coverage by `LDEM_80S_20M`:** **100.0% COVERED** (Entire footprint lies between $-80^\circ$ and $-90^\circ$).
- **Recommendation:** **`LDEM_80S_20M` REQUIRED.**

### 3.3 OHRC_PAIR_03 (Faustini / Shoemaker Region)
- **Latitude Span:** $-84.544478^\circ$ to $-85.366665^\circ\text{S}$
- **Longitude Span:** $24.207834^\circ$ to $28.474338^\circ\text{E}$
- **Coverage by `LDEM_875S_5M`:** **0.0% COVERED** (Completely north of $-87.5^\circ$).
- **Coverage by `LDEM_80S_20M`:** **100.0% COVERED**.
- **Recommendation:** **`LDEM_80S_20M` REQUIRED.**

### 3.4 OHRC_PAIR_04 (Nobile Ridge Region)
- **Latitude Span:** $-83.763994^\circ$ to $-84.596614^\circ\text{S}$
- **Longitude Span:** $30.818093^\circ$ to $34.176418^\circ\text{E}$
- **Coverage by `LDEM_875S_5M`:** **0.0% COVERED** (Completely north of $-87.5^\circ$).
- **Coverage by `LDEM_80S_20M`:** **100.0% COVERED**.
- **Recommendation:** **`LDEM_80S_20M` REQUIRED.**

---

## 4. Multi-Pair Feasibility & Selection Recommendation

1. **Rejection of the 5 m DEM as Primary Baseline:**  
   Although `LDEM_875S_5M` offers 5 m resolution matching the nominal raster GSD of the mentor data, selecting it would force evaluating Pair 01 on a completely different topography source than Pairs 02–04, introducing severe dataset confounding. Furthermore, it cannot support a 4-pair comparative study.
2. **Selection of `LDEM_80S_20M` as Authoritative Unified Baseline:**  
   `LDEM_80S_20M` is the **only single polar DEM that simultaneously covers 100% of all four mentor datasets**. While 20 m/pixel is $4\times$ coarser than the downsampled 5 m rasters (and $\sim 80\times$ coarser than native 0.25 m OHRC data), it captures macro-topographic slopes, crater walls, and ridge crests that govern lunar shadow formation and broad relief displacement.
3. **Storage & Download Strategy:**  
   The binary file is 1.85 GB. Downloading only the localized bounding sub-window covering the mentor footprints ($83.5^\circ\text{S} - 90^\circ\text{S}$, $20^\circ\text{E} - 250^\circ\text{E}$) via GDAL HTTP range requests or Cloud-Optimized GeoTIFF (COG) access on the NASA Planetary Geosciences Data Archive (PGDA) is strongly recommended over storing the entire 1.85 GB global raster locally.

---

## 5. Conclusions
- **Terrain Availability Status:** **RESOLVED BY AUTHORITATIVE EXTERNAL AUDIT.**
- The local deficiency (`DEM_REQUIRED_BUT_NOT_AVAILABLE`) is resolved by identifying NASA's `LDEM_80S_20M` as the verified external terrain model covering all 4 OHRC mentor footprints.
- However, actual DEM downloading, crop extraction, and ray-terrain intersection remain strictly held pending Phase 23 authorization.
