# Real-Time Bidirectional Speech ↔ Sign Language Translation Using SLL-SM

This repository contains the complete implementation, mathematical specification, unit test suite, research benchmark results, and patent-readiness documentation for the **Spatial-Locus Lifecycle State Machine (SLL-SM)** algorithm.

---

## 🌟 Core Innovation
SLL-SM decouples **entity representation embeddings** ($\mathbf{E}$) from **physical 3D spatial loci coordinates** ($\mathbf{M}$) using a **bipartite entity-locus binding matrix** ($\mathbf{B}$) and a **discrete 5-state finite state machine (FSM)** controller (`UNASSIGNED`, `CREATED`, `ACTIVE`, `SHIFTED`, `RELEASED`) with **validity masking** ($\mathbf{v}$).

This structural decoupling resolves the fundamental problem of **identity memory overwriting / identity collision** during spatial locus reuse in continuous signing discourse, achieving **100% Joint Counterfactual Accuracy** and **0% Ghost Reference Rate** on spatial locus reuse benchmarks.

---

## 📂 Quick Links & Documentation
- 📄 **Master Report:** [`research/FINAL_PROJECT_MASTER_REPORT.md`](research/FINAL_PROJECT_MASTER_REPORT.md)
- 📖 **Reproduction Guide:** [`research/REPRODUCTION_GUIDE.md`](research/REPRODUCTION_GUIDE.md)
- 📊 **Technical Summary:** [`research/FINAL_TECHNICAL_SUMMARY.md`](research/FINAL_TECHNICAL_SUMMARY.md)
- 📋 **Project Checklist:** [`research/FINAL_PROJECT_CHECKLIST.md`](research/FINAL_PROJECT_CHECKLIST.md)
- 📜 **Patentability & Prior Art Analysis:** [`research/PHASE_13_FORMAL_PATENT_ANALYSIS.md`](research/PHASE_13_FORMAL_PATENT_ANALYSIS.md)
- 🏁 **Completion Status:** [`research/PROJECT_COMPLETION_STATUS.md`](research/PROJECT_COMPLETION_STATUS.md)

---

## 🚀 Quick Start & Verification

### 1. Run Unit & Integration Test Suite (32 Tests, ~3s Execution)
```bash
python -m unittest discover tests
```

### 2. Run Standalone Demonstration
```bash
python demo/final_sllsm_demo.py
```

### 3. Run Real-World Schema Validation Runner
```bash
python scripts/real_world_validation.py
```

### 4. Run Accelerated Multi-Seed Research Benchmark
```bash
python scripts/run_phase12_fast_training.py
```

---

## ⚙️ Repository Structure
```
.
├── demo/
│   ├── final_sllsm_demo.py          # Standalone final demonstration script
│   └── phase8_demo.py               # Phase 8 bidirectional prototype demo
├── research/                        # Complete scientific, audit & patent reports (Phases 1 - 13)
├── scripts/
│   ├── real_world_validation.py     # Real-world schema & latency validation runner
│   └── run_phase12_fast_training.py # Multi-seed accelerated benchmark runner
├── src/
│   └── slds_core/                   # Core production SLL-SM engine
│       ├── bidirectional_pipeline.py# Bidirectional manager
│       ├── common_representation.py # Modality-independent payload bus
│       ├── decoders.py              # Pose and Text decoders
│       ├── sign_adapter.py          # Sign keypoint adapter
│       ├── speech_adapter.py        # Speech spectrogram adapter
│       └── sllsm_core.py            # Frozen SLLSMCore state machine
└── tests/                           # Fast unit & integration test suite
```

---

## 📊 Summary of Verified Results

| Metric | Measured Result | Reference Source |
| :--- | :---: | :--- |
| **Unit Test Pass Rate** | **32 / 32 PASSED (100%)** | `python -m unittest discover tests` |
| **Counterfactual Joint Accuracy** | **100.0 ± 0.0%** | `tests/test_sllsm_counterfactual.py` |
| **Ghost Reference Rate** | **0.0 ± 0.0%** | `research/PHASE_12_TRAINING_RESULTS.json` |
| **Single-Frame Core Pass Latency** | **3.56 ms** | CPU benchmark |
| **Speech $\rightarrow$ Sign Batch Latency** | **44.47 ms** | `demo/final_sllsm_demo.py` |
| **Sign $\rightarrow$ Speech Batch Latency** | **58.52 ms** | `demo/final_sllsm_demo.py` |
| **Model Parameter Count** | **204,485 parameters** | `SLLSMCore` |

---

## ⚖️ License & Disclaimer
This repository contains research and software prototype code. Scientific evaluation was performed on synthetic sequence data proxies. Real-world continuous sign language video evaluation (e.g. PHOENIX-2014T) and formal patent filings require external dataset fine-tuning and registered patent counsel review.
