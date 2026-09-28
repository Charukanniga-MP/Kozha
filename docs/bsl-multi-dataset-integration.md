# British Sign Language (BSL) Multi-Dataset Integration Guide

This guide documents how to integrate three major British Sign Language (BSL) datasets into Kozha for expanded word coverage, fingerspelling sequence recognition, and phrase translation.

---

## Supported BSL Datasets

### 1. BOBSL (BBC-Oxford British Sign Language Dataset)
- **Citation**: *BOBSL: BBC-Oxford British Sign Language Dataset* (Albanie et al., Oxford VGG, 2021).
- **Scale**: 1,467 hours of continuous BSL video from BBC broadcasts.
- **Link**: [`Oxford VGG BOBSL Page`](https://www.robots.ox.ac.uk/~vgg/data/bobsl/).

### 2. FS23K Dataset
- **Description**: Specialized derivative of BOBSL containing 23,000 fully spelled-out word instances. Filters out abbreviations to ensure all letters of each targeted word are explicitly present, providing clean data for word recognition and fingerspelling sequences.
- **Project Link**: [`taeinkwon.com/projects/fs23k`](https://taeinkwon.com/projects/fs23k/).

### 3. Sign Language Recognition Dataset (Jordan J. Bird)
- **Description**: Multi-modal native BSL dataset captured via Leap Motion hardware tracking devices alongside computer vision sensors. Covers 18 complex everyday phrases and words across multiple subjects.
- **Links**: [`Kaggle`](https://www.kaggle.com/), [`Jordan James Bird Project Page`](https://jordanjamesbird.com/sign-language-recognition-dataset/).

---

## Directory Layout

Place dataset files in their corresponding subdirectories within `data/sources/bsl_datasets/`:

```
data/
└── sources/
    └── bsl_datasets/
        ├── bobsl/
        │   ├── bobsl_annotations.csv
        │   └── bobsl_annotations.json
        ├── fs23k/
        │   ├── fs23k_dataset.json
        │   └── fs23k_dataset.csv
        └── bird_bsl/
            ├── bird_bsl_dataset.json
            └── bird_bsl_dataset.csv
```

---

## Running the BSL Multi-Dataset Integrator

To process dataset annotations, unify glosses, map gestures into HamNoSys/SiGML, update Kozha's BSL database files, and append to `data/hamnosys_bsl.csv`:

```bash
# Initialize sample datasets for local testing without downloading full video files
python scripts/bsl_multi_dataset_integrate.py --init-sample

# Run multi-dataset integration pipeline
python scripts/bsl_multi_dataset_integrate.py
```

---

## Generated Artifacts

Running `scripts/bsl_multi_dataset_integrate.py` produces and updates:

- [`data/BSL_bobsl_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/BSL_bobsl_authored.sigml): Active SiGML XML collection for multi-dataset BSL signs.
- [`data/BSL_bobsl_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/BSL_bobsl_authored.sigml.meta.json): Provenance and citation sidecar.
- [`data/hamnosys_bsl.csv`](file:///c:/Users/bc/Downloads/Kozha-main/data/hamnosys_bsl.csv): Updated BSL master concept dictionary.

---

## Automated Verification

Run unit test verification for the multi-dataset pipeline:

```bash
.\venv\Scripts\python.exe -m pytest scripts/tests/test_bsl_multi_dataset_integrate.py -v
```
