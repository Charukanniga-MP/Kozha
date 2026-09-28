# American Sign Language (ASL) Multi-Dataset Integration Guide

This guide documents how to integrate five major American Sign Language (ASL) datasets into Kozha for expanded word coverage, gesture recognition, and sign translation.

---

## Supported ASL Datasets

### 1. ASL Citizen (Microsoft Research)
- **Scale**: ~84,000 video recordings featuring 2,700 isolated signs recorded by 52 Deaf or hard-of-hearing signers.
- **Details**: One of the largest crowdsourced collections for isolated ASL signs.
- **Link**: [`ASL Citizen on Microsoft Research`](https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-description/).

### 2. WLASL (Word-Level American Sign Language)
- **Citation**: *Word-Level Deep Sign Language Recognition from Video: Performance Benchmark and Analysis* (Li et al., WACV 2020).
- **Scale**: 2,000 common ASL words across 12,000+ video clips performed by 100+ signers.
- **Links**: [`Kaggle Competitions`](https://www.kaggle.com/competitions/sign-language-recognition), [`dxli94/WLASL`](https://github.com/dxli94/WLASL).

### 3. ASL Alphabet (Kaggle by grassknoted)
- **Scale**: 87,000 images across 29 classes: 26 for letters A–Z and 3 for space, delete, and nothing.
- **Best For**: Real-time static classification of hand shapes.
- **Kaggle Link**: [`grassknoted/asl-alphabet`](https://www.kaggle.com/datasets/grassknoted/asl-alphabet).

### 4. ASL-HG (ScienceDirect / Hand Gestures)
- **Scale**: 36,000 images across 36 classes (A–Z and 0–9, separating letter 'O' from digit '0').
- **Details**: High-resolution dataset dedicated to static hand shapes and digits.
- **ScienceDirect Link**: [`ASL-HG on ScienceDirect`](https://www.sciencedirect.com/science/article/pii/S235291482100067X).

### 5. Sign Language MNIST (Kaggle)
- **Scale**: 34,627 rows of 28x28 pixel grayscale images corresponding to ASL alphabets (excluding J and Z which require motion).
- **Kaggle Link**: [`datamunge/sign-language-mnist`](https://www.kaggle.com/datasets/datamunge/sign-language-mnist).

---

## Directory Layout

Place dataset files in their corresponding subdirectories within `data/sources/asl_datasets/`:

```
data/
└── sources/
    └── asl_datasets/
        ├── asl_citizen/
        │   └── asl_citizen_dataset.json
        ├── wlasl/
        │   └── WLASL_v0.3.json
        ├── asl_alphabet/
        │   └── asl_alphabet_metadata.json
        ├── asl_hg/
        │   └── asl_hg_metadata.json
        └── sign_language_mnist/
            └── sign_mnist_metadata.json
```

---

## Running the ASL Multi-Dataset Integrator

To process dataset annotations, unify glosses, map gestures into HamNoSys/SiGML, and update Kozha's ASL database files:

```bash
# Initialize sample datasets for local testing without downloading full video files
python scripts/asl_multi_dataset_integrate.py --init-sample

# Run multi-dataset integration pipeline
python scripts/asl_multi_dataset_integrate.py
```

---

## Generated Artifacts

Running `scripts/asl_multi_dataset_integrate.py` produces and updates:

- [`data/ASL_wlasl_msasl_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/ASL_wlasl_msasl_authored.sigml): Active SiGML XML collection for multi-dataset ASL signs.
- [`data/ASL_wlasl_msasl_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/ASL_wlasl_msasl_authored.sigml.meta.json): Provenance and citation sidecar.
- [`data/American_SL_ASL.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/American_SL_ASL.sigml.meta.json): Updated master ASL metadata sidecar.

---

## Automated Verification

Run unit test verification for the multi-dataset pipeline:

```bash
.\venv\Scripts\python.exe -m pytest scripts/tests/test_asl_multi_dataset_integrate.py -v
```
