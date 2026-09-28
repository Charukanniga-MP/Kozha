"""Unit tests for the WLASL and MS-ASL dataset integrator script (scripts/wlasl_msasl_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.wlasl_msasl_integrate import (
    build_sigml_document,
    create_sample_asl_datasets,
    load_msasl_glosses,
    load_wlasl_glosses,
    process_asl_datasets,
)


def test_create_sample_asl_datasets(tmp_path: Path) -> None:
    wlasl, msasl = create_sample_asl_datasets(tmp_path)
    assert wlasl.exists()
    assert msasl.exists()

    w_glosses = load_wlasl_glosses(wlasl)
    m_glosses = load_msasl_glosses(msasl)

    assert "HELLO" in w_glosses
    assert "BOOK" in w_glosses
    assert "FAMILY" in m_glosses


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "BOOK", "sigml": "<hamflathand/><hamextfingero/><hampalmu/>"},
        {"gloss": "COMPUTER", "sigml": "<hamceeall/><hamextfingeru/><hampalml/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="American_SL_WLASL_MSASL"' in xml
    assert 'gloss="BOOK"' in xml
    assert '<hamflathand/>' in xml


def test_process_asl_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wlasl, msasl = create_sample_asl_datasets(tmp_path)

    sigml_file = tmp_path / "ASL_wlasl_msasl_authored.sigml"
    meta_file = tmp_path / "ASL_wlasl_msasl_authored.sigml.meta.json"

    monkeypatch.setattr("scripts.wlasl_msasl_integrate.ASL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.wlasl_msasl_integrate.ASL_AUTHORED_META", meta_file)

    active_cnt, total_glosses = process_asl_datasets(wlasl, msasl)
    assert active_cnt >= 7
    assert total_glosses >= 7
    assert sigml_file.exists()
    assert meta_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert "WLASL" in meta_data["dataset"]
