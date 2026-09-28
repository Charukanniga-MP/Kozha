"""Unit tests for the BSL Multi-Dataset Integrator script (scripts/bsl_multi_dataset_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.bsl_multi_dataset_integrate import (
    build_sigml_document,
    create_sample_bsl_datasets,
    load_bird_bsl_glosses,
    load_bobsl_glosses,
    load_fs23k_glosses,
    normalize_gloss,
    process_bsl_multi_datasets,
)


def test_normalize_gloss() -> None:
    assert normalize_gloss("hello-world") == "HELLO_WORLD"
    assert normalize_gloss("Thank  You!") == "THANK_YOU"


def test_create_sample_bsl_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bobsl_dir = tmp_path / "bobsl"
    fs23k_dir = tmp_path / "fs23k"
    bird_dir = tmp_path / "bird_bsl"

    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BOBSL_DIR", bobsl_dir)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.FS23K_DIR", fs23k_dir)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BIRD_DIR", bird_dir)

    create_sample_bsl_datasets()

    assert (bobsl_dir / "bobsl_annotations.csv").exists()
    assert (fs23k_dir / "fs23k_dataset.json").exists()
    assert (bird_dir / "bird_bsl_dataset.json").exists()


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "HELLO", "sigml": "<hamflathand/><hamextfingeru/><hampalml/>"},
        {"gloss": "NAME", "sigml": "<hamfinger23/><hamextfingeru/><hampalml/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="BSL_MultiDataset"' in xml
    assert 'gloss="HELLO"' in xml
    assert 'gloss="NAME"' in xml


def test_process_bsl_multi_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bobsl_dir = tmp_path / "bobsl"
    fs23k_dir = tmp_path / "fs23k"
    bird_dir = tmp_path / "bird_bsl"

    sigml_file = tmp_path / "BSL_bobsl_authored.sigml"
    meta_file = tmp_path / "BSL_bobsl_authored.sigml.meta.json"
    csv_file = tmp_path / "hamnosys_bsl.csv"
    csv_file.write_text("concept,language,gloss,hamnosys,video_url,page_url\n", encoding="utf-8")

    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BOBSL_DIR", bobsl_dir)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.FS23K_DIR", fs23k_dir)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BIRD_DIR", bird_dir)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BSL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BSL_AUTHORED_META", meta_file)
    monkeypatch.setattr("scripts.bsl_multi_dataset_integrate.BSL_HAMNOSYS_CSV", csv_file)

    active_cnt, stats = process_bsl_multi_datasets()
    assert active_cnt >= 15
    assert stats["total"] >= 10
    assert sigml_file.exists()
    assert meta_file.exists()
    assert csv_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["dataset"] == "Kozha BSL Multi-Dataset Pipeline"
    assert len(meta_data["sources"]) == 3
