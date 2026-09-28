# iSign (ACL 2024 Indian Sign Language Processing Benchmark) Integration Guide

This guide documents how to integrate the **iSign Benchmark Dataset** for Indian Sign Language (ISL) with Kozha.

---

## About iSign

- **Paper**: *iSign: A Benchmark for Indian Sign Language Processing* (Joshi et al., Findings of ACL 2024; IIT Kanpur / Exploration-Lab).
- **Scale**: 118,000+ ISL sentence/phrase pairs with video, pose, and gloss sequence annotations.
- **Hugging Face Repository**: [`Exploration-Lab/iSign`](https://huggingface.co/datasets/Exploration-Lab/iSign).

---

## 1. Accessing the Dataset

The iSign dataset is hosted on Hugging Face for academic and non-commercial research:

1. Visit [`https://huggingface.co/datasets/Exploration-Lab/iSign`](https://huggingface.co/datasets/Exploration-Lab/iSign).
2. Accept the terms of use and download the dataset JSON / CSV files.
3. Save the annotation files into `data/sources/isign/`.

---

## 2. Directory Layout

```
data/
└── sources/
    └── isign/
        ├── isign_dataset.csv
        └── isign_dataset.json
```

---

## 3. Running the iSign Integrator

To process iSign annotations and update Kozha's ISL sign library:

```bash
# Ingest annotations from data/sources/isign/isign_dataset.csv
python scripts/isign_integrate.py

# Ingest from a custom dataset file path
python scripts/isign_integrate.py --in data/sources/isign/my_custom_isign.csv

# Initialize a sample annotation file for local testing
python scripts/isign_integrate.py --init-sample
```

---

## 4. Generated Artifacts

Running `scripts/isign_integrate.py` produces and updates the following Kozha ISL dataset files:

- [`data/ISL_isign_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/ISL_isign_authored.sigml): Active SiGML XML collection for iSign ISL signs.
- [`data/ISL_isign_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/ISL_isign_authored.sigml.meta.json): Metadata sidecar with ACL 2024 citation & provenance.
- [`data/Indian_SL.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/Indian_SL.sigml): Updated Indian Sign Language database.

---

## 5. Automated Verification

To run unit test verification for the iSign integrator:

```bash
python -m pytest scripts/tests/test_isign_integrate.py
```
