# BOBSL (BBC-Oxford British Sign Language Dataset) Integration Guide

This guide documents how to use the **BOBSL (BBC-Oxford British Sign Language Dataset)** with Kozha.

---

## About BOBSL

- **Authors**: Samuel Albanie, Gül Varol, Liliane Momeni, Hannah Bull, et al. (Oxford VGG, 2021)
- **Scale**: 1,467 hours of continuous BSL video extracted from BBC broadcast television.
- **Content**: Subtitle alignments, BSL gloss annotations, video timestamps, and continuous sign recognition (CSLR) benchmarks.

---

## 1. Requesting Official Dataset Access

The raw BOBSL video clips and official annotations require registration on the official Oxford VGG page:

1. Visit the [Oxford VGG BOBSL Dataset Page](https://www.robots.ox.ac.uk/~vgg/data/bobsl/).
2. Fill out the academic / non-commercial research agreement form.
3. Once approved, download the annotation CSV or JSON files.

---

## 2. Directory Structure

Place downloaded annotation files into `data/sources/bobsl/`:

```
data/
└── sources/
    └── bobsl/
        ├── bobsl_annotations.csv
        └── bobsl_glosses.json
```

---

## 3. Running the BOBSL Integrator

To ingest BOBSL annotations into Kozha's BSL sign library:

```bash
# Ingest annotations from data/sources/bobsl/bobsl_annotations.csv
python scripts/bobsl_integrate.py

# Specify a custom annotation file path
python scripts/bobsl_integrate.py --in data/sources/bobsl/my_custom_bobsl.csv

# Initialize a sample annotation file for testing
python scripts/bobsl_integrate.py --init-sample
```

---

## 4. Generated Artifacts

Running `scripts/bobsl_integrate.py` updates the following Kozha BSL dataset files:

- [`data/BSL_bobsl_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/BSL_bobsl_authored.sigml): Active SiGML XML collection for BOBSL BSL signs.
- [`data/BSL_bobsl_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/BSL_bobsl_authored.sigml.meta.json): Provenance and metadata sidecar.
- [`data/hamnosys_bsl.csv`](file:///c:/Users/bc/Downloads/Kozha-main/data/hamnosys_bsl.csv): Updated BSL concept dictionary.

---

## 5. Running Automated Verification

To test the BOBSL integration pipeline:

```bash
python -m pytest scripts/tests/test_bobsl_integrate.py
```
