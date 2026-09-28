# Indian Sign Language (ISL) Multi-Dataset Integration Guide

This guide documents how to integrate five major Indian Sign Language (ISL) datasets into Kozha for expanded word coverage, gesture recognition, character/digit signing, and continuous sign translation.

---

## Supported ISL Datasets

### 1. INCLUDE Dataset (Zenodo / AI4Bharat)
- **Scale**: 4,287+ videos containing ~270,000 individual frames covering 263 word signs across 15 domains (Greetings, Pronouns, Family, Food, Actions, Numbers, Places, Animals, Colours, Questions, Clothing, Emotions, Medical, Office), plus INCLUDE-50.
- **Repository**: [`INCLUDE Dataset on Zenodo`](https://data.niaid.nih.gov/resources?id=zenodo_4010759).

### 2. iSign / ISLTranslate
- **Citation**: *iSign: A Benchmark for Indian Sign Language Processing* (Joshi et al., Findings of ACL 2024; IIT Kanpur / Exploration-Lab).
- **Scale**: Over 31,000 ISL-English sentence and phrase pairs for continuous sign language translation and NLP tasks.
- **Repositories**: [`Exploration-Lab/iSign`](https://exploration-lab.github.io/iSign/), [`Exploration-Lab/ISLTranslate`](https://github.com/Exploration-Lab/ISLTranslate), and [`HuggingFace Exploration-Lab/iSign`](https://huggingface.co/datasets/Exploration-Lab/iSign).

### 3. MediaPipe Pose-Estimated ISL Dataset
- **Scale**: Over 50,000 high-quality images targeting the 26 letters of the English alphabet (A–Z).
- **Format**: Pre-processed with Google MediaPipe pose estimation tracking.
- **Kaggle Link**: [`prekshapalva/indian-sign-language`](https://www.kaggle.com/datasets/prekshapalva/indian-sign-language).

### 4. ISL-dataset (Alphabet & Digits)
- **Scale**: 36,000 total images (1,000 images per class across 36 folders covering digits 0–9 and alphabets A–Z).
- **Format**: Preprocessed 250x250 JPEG format, referencing gestures approved by the Indian Sign Language Research and Training Centre (ISLRTC).
- **Kaggle Link**: [`ananyaarya22/isl-data`](https://www.kaggle.com/datasets/ananyaarya22/isl-data) & [`atharvadumbre/indian-sign-language-islrtc-referred`](https://www.kaggle.com/datasets/atharvadumbre/indian-sign-language-islrtc-referred).

### 5. ISL-CSLTR Corpus
- **Scale**: 700 fully annotated videos, 18,863 sentence-level frames, and 1,036 word-level images tracking 100 spoken language sentences performed by 7 distinct native signers.
- **Mendeley Link**: [`ISL-CSLTR Mendeley Repository`](https://data.mendeley.com/datasets/kcmpdxky7p/1) & Kaggle [`drblack00/isl-csltr-indian-sign-language-dataset`](https://www.kaggle.com/datasets/drblack00/isl-csltr-indian-sign-language-dataset).

---

## Directory Layout

Place downloaded dataset files in their corresponding subdirectories within `data/sources/`:

```
data/
└── sources/
    ├── isign/
    │   ├── isign_dataset.csv
    │   └── isign_dataset.json
    ├── include_landmarks/
    │   ├── include_landmarks.json
    │   └── include_landmarks.csv
    ├── mediapipe_isl/
    │   ├── mediapipe_isl_annotations.json
    │   └── mediapipe_isl_annotations.csv
    ├── isl_alphabet_digits/
    │   ├── isl_alphabet_digits.json
    │   └── isl_alphabet_digits.csv
    ├── isl_csltr/
    │   ├── isl_csltr_annotations.json
    │   └── isl_csltr_annotations.csv
    └── isl_50/
        ├── isl_50_dataset.csv
        └── isl_50_dataset.json
```

---

## Running the ISL Multi-Dataset Integrator

To ingest annotations, unify glosses, map gestures into HamNoSys/SiGML, and update Kozha's ISL database files:

```bash
# Initialize sample datasets for local testing without downloading full video files
python scripts/isl_multi_dataset_integrate.py --init-sample

# Run multi-dataset integration pipeline
python scripts/isl_multi_dataset_integrate.py
```

---

## Generated Artifacts

Running `scripts/isl_multi_dataset_integrate.py` updates and creates:

- [`data/ISL_authored.sigml`](file:///c:/Users/bc/Downloads/Kozha-main/data/ISL_authored.sigml): Active SiGML XML collection for multi-dataset ISL signs.
- [`data/ISL_authored.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/ISL_authored.sigml.meta.json): Metadata sidecar with provenance, citation, and category counts.
- [`data/Indian_SL.sigml.meta.json`](file:///c:/Users/bc/Downloads/Kozha-main/data/Indian_SL.sigml.meta.json): Updated master ISL metadata sidecar.

---

## Automated Verification

Run unit test verification for the multi-dataset pipeline:

```bash
.\venv\Scripts\python.exe -m pytest scripts/tests/test_isl_multi_dataset_integrate.py -v
```
