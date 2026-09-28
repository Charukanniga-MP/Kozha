# WLASL & MS-ASL Dataset Integration Guide

This guide documents how to integrate the **WLASL (Word-Level ASL)** and **MS-ASL (Microsoft ASL)** datasets with Kozha.

---

## About the Datasets

### 1. WLASL (Word-Level American Sign Language)
- **Paper**: *Word-Level Deep Sign Language Recognition from Video: Performance Benchmark and Analysis* (Li et al., WACV 2020).
- **Scale**: 2,000 ASL words across 21,000+ video clips.
- **GitHub Repository**: [`dxli94/WLASL`](https://github.com/dxli94/WLASL) (`WLASL_v0.3.json`).

### 2. MS-ASL (Microsoft American Sign Language)
- **Paper**: *MS-ASL: A Large-Scale Data Set for American Sign Language Recognition* (Vaezi Joze et al., BMVC 2019).
- **Scale**: 1,000 ASL words across 25,000+ video clips.
- **Kaggle Annotations**: [`redoan/msasl-official-annotations`](https://www.kaggle.com/datasets/redoan/msasl-official-annotations) (`MSASL_train.json`).

---

## 1. Accessing the Datasets

1. **WLASL**: Download `WLASL_v0.3.json` from [`dxli94/WLASL`](https://github.com/dxli94/WLASL).
2. **MS-ASL**: Download `MSASL_train.json` from Microsoft Research or Kaggle.
3. Save the annotation files into `data/sources/asl_datasets/`.

---

## 2. Directory Layout

```
data/
└── sources/
    └── asl_datasets/
        ├── WLASL_v0.3.json
        └── MSASL_train.json
```

---

## 3. Running the WLASL & MS-ASL Integrator

To process WLASL and MS-ASL dataset annotations:

```bash
# Ingest annotations from data/sources/asl_datasets/
python scripts/wlasl_msasl_integrate.py

# Ingest custom file paths
python scripts/wlasl_msasl_integrate.py --wlasl path/to/WLASL.json --msasl path/to/MSASL.json

# Initialize sample dataset files for testing
python scripts/wlasl_msasl_integrate.py --init-sample
```

---

## 4. Generated Artifacts

Running `scripts/wlasl_msasl_integrate.py` produces and updates the following Kozha ASL dataset files:

- [`data/ASL_wlasl_msasl_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/ASL_wlasl_msasl_authored.sigml): Active SiGML XML collection for WLASL/MS-ASL signs.
- [`data/ASL_wlasl_msasl_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/ASL_wlasl_msasl_authored.sigml.meta.json): Provenance and citation sidecar.

---

## 5. Automated Verification

To run unit test verification:

```bash
python -m pytest scripts/tests/test_wlasl_msasl_integrate.py
```
