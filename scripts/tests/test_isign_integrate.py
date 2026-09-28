"""Unit tests for the iSign ISL dataset integrator script (scripts/isign_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.isign_integrate import (
    build_sigml_document,
    create_sample_isign_dataset,
    load_isign_dataset,
    process_isign_dataset,
)


def test_create_sample_isign_dataset(tmp_path: Path) -> None:
    csv_file = tmp_path / "sample_isign.csv"
    create_sample_isign_dataset(csv_file)
    assert csv_file.exists()
    rows = load_isign_dataset(csv_file)
    assert len(rows) >= 5
    assert any("NAMASTE" in r.get("gloss_sequence", "") for r in rows)


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "NAMASTE", "sigml": "<hamsymmpar/><hamflathand/><hamextfingeru/><hampalml/>"},
        {"gloss": "INDIA", "sigml": "<hamfinger23/><hamextfingeru/><hampalml/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="Indian_SL_iSign"' in xml
    assert 'gloss="NAMASTE"' in xml
    assert '<hamsymmpar/>' in xml


def test_process_isign_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_file = tmp_path / "isign_test.csv"
    create_sample_isign_dataset(csv_file)

    sigml_file = tmp_path / "ISL_isign_authored.sigml"
    meta_file = tmp_path / "ISL_isign_authored.sigml.meta.json"

    monkeypatch.setattr("scripts.isign_integrate.ISL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.isign_integrate.ISL_AUTHORED_META", meta_file)

    active_cnt, gloss_cnt = process_isign_dataset(csv_file)
    assert active_cnt >= 8
    assert gloss_cnt >= 8
    assert sigml_file.exists()
    assert meta_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["dataset"] == "iSign: A Benchmark for Indian Sign Language Processing"
