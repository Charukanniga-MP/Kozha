"""Unit tests for the ASL Multi-Dataset Integrator script (scripts/asl_multi_dataset_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.asl_multi_dataset_integrate import (
    build_sigml_document,
    create_sample_asl_datasets,
    load_asl_alphabet_glosses,
    load_asl_citizen_glosses,
    load_asl_hg_glosses,
    load_sign_language_mnist_glosses,
    load_wlasl_glosses,
    normalize_gloss,
    process_asl_multi_datasets,
)


def test_normalize_gloss() -> None:
    assert normalize_gloss("hello-world") == "HELLO_WORLD"
    assert normalize_gloss("Thank  You!") == "THANK_YOU"


def test_create_sample_asl_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources_dir = tmp_path / "asl_datasets"
    asl_citizen_dir = sources_dir / "asl_citizen"
    wlasl_dir = sources_dir / "wlasl"
    asl_alphabet_dir = sources_dir / "asl_alphabet"
    asl_hg_dir = sources_dir / "asl_hg"
    sign_mnist_dir = sources_dir / "sign_language_mnist"

    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.SOURCES_DIR", sources_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_CITIZEN_DIR", asl_citizen_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.WLASL_DIR", wlasl_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_ALPHABET_DIR", asl_alphabet_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_HG_DIR", asl_hg_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.SL_MNIST_DIR", sign_mnist_dir)

    create_sample_asl_datasets()

    assert (asl_citizen_dir / "asl_citizen_dataset.json").exists()
    assert (wlasl_dir / "WLASL_v0.3.json").exists()
    assert (asl_alphabet_dir / "asl_alphabet_metadata.json").exists()
    assert (asl_hg_dir / "asl_hg_metadata.json").exists()
    assert (sign_mnist_dir / "sign_mnist_metadata.json").exists()


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "HELLO", "sigml": "<hamflathand/><hamextfingeru/><hampalml/>"},
        {"gloss": "BOOK", "sigml": "<hamsymmpar/><hamflathand/><hamextfingero/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="American_SL_MultiDataset"' in xml
    assert 'gloss="HELLO"' in xml
    assert 'gloss="BOOK"' in xml


def test_process_asl_multi_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources_dir = tmp_path / "asl_datasets"
    asl_citizen_dir = sources_dir / "asl_citizen"
    wlasl_dir = sources_dir / "wlasl"
    asl_alphabet_dir = sources_dir / "asl_alphabet"
    asl_hg_dir = sources_dir / "asl_hg"
    sign_mnist_dir = sources_dir / "sign_language_mnist"

    sigml_file = tmp_path / "ASL_wlasl_msasl_authored.sigml"
    meta_file = tmp_path / "ASL_wlasl_msasl_authored.sigml.meta.json"
    asl_meta = tmp_path / "American_SL_ASL.sigml.meta.json"
    asl_meta.write_text(json.dumps({"version": 1, "language": "asl"}), encoding="utf-8")

    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.SOURCES_DIR", sources_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_CITIZEN_DIR", asl_citizen_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.WLASL_DIR", wlasl_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_ALPHABET_DIR", asl_alphabet_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_HG_DIR", asl_hg_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.SL_MNIST_DIR", sign_mnist_dir)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.ASL_AUTHORED_META", meta_file)
    monkeypatch.setattr("scripts.asl_multi_dataset_integrate.AMERICAN_SL_META", asl_meta)

    active_cnt, stats = process_asl_multi_datasets()
    assert active_cnt >= 15
    assert stats["total"] >= 10
    assert sigml_file.exists()
    assert meta_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["dataset"] == "Kozha ASL Multi-Dataset Pipeline"
    assert len(meta_data["sources"]) == 5

