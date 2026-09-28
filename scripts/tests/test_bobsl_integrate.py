"""Unit tests for the BOBSL dataset integrator script (scripts/bobsl_integrate.py)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.bobsl_integrate import (
    build_sigml_document,
    create_sample_bobsl_annotations,
    load_bobsl_annotations,
    process_bobsl_dataset,
)


def test_create_sample_bobsl_annotations(tmp_path: Path) -> None:
    csv_file = tmp_path / "sample.csv"
    create_sample_bobsl_annotations(csv_file)
    assert csv_file.exists()
    rows = load_bobsl_annotations(csv_file)
    assert len(rows) >= 8
    assert any(r.get("gloss") == "HELLO" for r in rows)


def test_build_sigml_document() -> None:
    records = [
        {"gloss": "HELLO", "sigml": "<hamflathand/><hamextfingeru/><hampalml/>"},
        {"gloss": "SIGN", "sigml": "<hamfinger23spread/><hamextfingeru/><hampalmr/>"},
    ]
    xml = build_sigml_document(records)
    assert '<sigml_collection language="BSL_BOBSL"' in xml
    assert 'gloss="HELLO"' in xml
    assert '<hamflathand/>' in xml


def test_process_bobsl_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_file = tmp_path / "bobsl_test.csv"
    create_sample_bobsl_annotations(csv_file)

    sigml_file = tmp_path / "BSL_bobsl_authored.sigml"
    meta_file = tmp_path / "BSL_bobsl_authored.sigml.meta.json"
    csv_dest = tmp_path / "hamnosys_bsl.csv"

    monkeypatch.setattr("scripts.bobsl_integrate.BSL_AUTHORED_SIGML", sigml_file)
    monkeypatch.setattr("scripts.bobsl_integrate.BSL_AUTHORED_META", meta_file)
    monkeypatch.setattr("scripts.bobsl_integrate.BSL_HAMNOSYS_CSV", csv_dest)

    active_cnt, csv_cnt = process_bobsl_dataset(csv_file)
    assert active_cnt >= 8
    assert sigml_file.exists()
    assert meta_file.exists()

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["dataset"] == "BOBSL (BBC-Oxford British Sign Language)"
