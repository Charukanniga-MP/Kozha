"""Unit tests for the ISL Multi-Dataset Integrator script (scripts/isl_multi_dataset_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.isl_multi_dataset_integrate import (
    build_sigml_document,
    create_sample_datasets,
    load_isign_dataset,
    load_include_landmarks_dataset,
    load_mediapipe_isl_dataset,
    load_isl_alphabet_digits_dataset,
    load_isl_csltr_dataset,
    load_isl50_dataset,
    normalize_gloss,
    process_multi_datasets,
)


def test_normalize_gloss() -> None:
    assert normalize_gloss("namaste-test") == "NAMASTE_TEST"
    assert normalize_gloss("Thank  You!") == "THANK_YOU"


def test_create_sample_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isign_dir = tmp_path / "isign"
    include_dir = tmp_path / "include_landmarks"
    mp_dir = tmp_path / "mediapipe_isl"
    ad_dir = tmp_path / "isl_alphabet_digits"
    csltr_dir = tmp_path / "isl_csltr"
    isl50_dir = tmp_path / "isl_50"

    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISIGN_DIR", isign_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.INCLUDE_DIR", include_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.MEDIAPIPE_ISL_DIR", mp_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL_ALPHABET_DIGITS_DIR", ad_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.CSLTR_DIR", csltr_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL50_DIR", isl50_dir)

    create_sample_datasets()

    assert (isign_dir / "isign_dataset.csv").exists()
    assert (include_dir / "include_landmarks.json").exists()
    assert (mp_dir / "mediapipe_isl_annotations.json").exists()
    assert (ad_dir / "isl_alphabet_digits.json").exists()
    assert (csltr_dir / "isl_csltr_annotations.json").exists()
    assert (isl50_dir / "isl_50_dataset.csv").exists()


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "NAMASTE", "sigml": "<hamsymmpar/><hamflathand/><hamextfingeru/><hampalml/>"},
        {"gloss": "WATER", "sigml": "<hamfinger23/><hamextfingeru/><hampalml/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="Indian_SL_MultiDataset"' in xml
    assert 'gloss="NAMASTE"' in xml
    assert 'gloss="WATER"' in xml


def test_process_multi_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isign_dir = tmp_path / "isign"
    include_dir = tmp_path / "include_landmarks"
    mp_dir = tmp_path / "mediapipe_isl"
    ad_dir = tmp_path / "isl_alphabet_digits"
    csltr_dir = tmp_path / "isl_csltr"
    isl50_dir = tmp_path / "isl_50"

    sigml_file = tmp_path / "ISL_authored.sigml"
    meta_file = tmp_path / "ISL_authored.sigml.meta.json"
    indian_sl_meta = tmp_path / "Indian_SL.sigml.meta.json"
    indian_sl_meta.write_text(json.dumps({"version": 1, "language": "isl"}), encoding="utf-8")

    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISIGN_DIR", isign_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.INCLUDE_DIR", include_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.MEDIAPIPE_ISL_DIR", mp_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL_ALPHABET_DIGITS_DIR", ad_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.CSLTR_DIR", csltr_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL50_DIR", isl50_dir)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.ISL_AUTHORED_META", meta_file)
    monkeypatch.setattr("scripts.isl_multi_dataset_integrate.INDIAN_SL_META", indian_sl_meta)

    active_cnt, stats = process_multi_datasets()
    assert active_cnt >= 20
    assert stats["total"] >= 10
    assert sigml_file.exists()
    assert meta_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["dataset"] == "Kozha ISL Multi-Dataset Pipeline"
    assert len(meta_data["sources"]) == 6
