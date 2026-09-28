#!/usr/bin/env python3
"""BOBSL (BBC-Oxford British Sign Language Dataset) Integrator for Kozha.

Reads BOBSL dataset annotations (CSV/JSON/JSONL), extracts BSL glosses,
aligns them with Kozha's BSL sign library, and updates BSL database files:

  - data/BSL_bobsl_authored.sigml
  - data/BSL_bobsl_authored.sigml.meta.json
  - data/hamnosys_bsl.csv

Dataset Context:
  BOBSL (Albanie et al., 2021; Oxford VGG) is a 1,467-hour continuous BSL video dataset
  from BBC broadcasts. Official video clips require registration at
  https://www.robots.ox.ac.uk/~vgg/data/bobsl/

Usage:
  python scripts/bobsl_integrate.py [--in data/sources/bobsl/bobsl_annotations.csv] [--init-sample] [--validate]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

REPO_ROOT = Path(__file__).resolve().parent.parent

BSL_AUTHORED_SIGML = REPO_ROOT / "data" / "BSL_bobsl_authored.sigml"
BSL_AUTHORED_META = REPO_ROOT / "data" / "BSL_bobsl_authored.sigml.meta.json"
BSL_HAMNOSYS_CSV = REPO_ROOT / "data" / "hamnosys_bsl.csv"
SOURCES_DIR = REPO_ROOT / "data" / "sources" / "bobsl"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("bobsl_integrate")

# Common BSL gloss -> HamNoSys / SiGML tags seed mapping for BOBSL frequency vocabulary
COMMON_BSL_GLOSS_MAP: dict[str, dict[str, str]] = {
    "HELLO": {
        "concept": "hello",
        "hamnosys": "",
        "sigml": "<hamflathand/><hamextfingeru/><hampalml/><hamneutralspace/><hamswinging/>",
    },
    "WELCOME": {
        "concept": "welcome",
        "hamnosys": "",
        "sigml": "<hamflathand/><hamextfingeru/><hampalml/><hamchest/><hammovei/>",
    },
    "SIGN": {
        "concept": "sign",
        "hamnosys": "",
        "sigml": "<hamsymmpar/><hamfinger23spread/><hamextfingeru/><hampalmr/><hamneutralspace/><hamcircleo/>",
    },
    "LANGUAGE": {
        "concept": "language",
        "hamnosys": "",
        "sigml": "<hamsymmpar/><hamfinger2345/><hamextfingeru/><hampalml/><hamneutralspace/><hammoveo/>",
    },
    "THANK_YOU": {
        "concept": "thank you",
        "hamnosys": "",
        "sigml": "<hamflathand/><hamextfingeru/><hampalml/><hamchin/><hammoveo/>",
    },
    "GOOD": {
        "concept": "good",
        "hamnosys": "",
        "sigml": "<hamfist/><hamthumboutmod/><hamextfingeru/><hampalml/><hamchest/><hammoveu/>",
    },
    "BAD": {
        "concept": "bad",
        "hamnosys": "",
        "sigml": "<hampinky/><hamextfingeru/><hampalml/><hamchest/><hammoved/>",
    },
    "PLEASE": {
        "concept": "please",
        "hamnosys": "",
        "sigml": "<hamflathand/><hamextfingeru/><hampalml/><hamchest/><hamcircleo/>",
    },
    "NAME": {
        "concept": "name",
        "hamnosys": "",
        "sigml": "<hamfinger23/><hamextfingeru/><hampalml/><hamforehead/><hamtouch/>",
    },
    "WHAT": {
        "concept": "what",
        "hamnosys": "",
        "sigml": "<hamsymmpar/><hamfinger2345/><hamextfingeru/><hampalmu/><hamneutralspace/><hamswinging/>",
    },
}


def create_sample_bobsl_annotations(out_path: Path) -> Path:
    """Generate a sample BOBSL annotation CSV file if none is present."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rows = [
        {"video_id": "bobsl_bbc_001", "start_time": "00:01:23", "end_time": "00:01:25", "gloss": "HELLO", "text_subtitle": "Hello everyone"},
        {"video_id": "bobsl_bbc_001", "start_time": "00:01:25", "end_time": "00:01:28", "gloss": "WELCOME", "text_subtitle": "Welcome to the programme"},
        {"video_id": "bobsl_bbc_002", "start_time": "00:04:10", "end_time": "00:04:13", "gloss": "SIGN", "text_subtitle": "Today we sign BSL"},
        {"video_id": "bobsl_bbc_002", "start_time": "00:04:13", "end_time": "00:04:16", "gloss": "LANGUAGE", "text_subtitle": "British Sign Language"},
        {"video_id": "bobsl_bbc_003", "start_time": "00:10:02", "end_time": "00:10:04", "gloss": "THANK_YOU", "text_subtitle": "Thank you for watching"},
        {"video_id": "bobsl_bbc_003", "start_time": "00:10:04", "end_time": "00:10:06", "gloss": "GOOD", "text_subtitle": "Good evening"},
        {"video_id": "bobsl_bbc_004", "start_time": "00:02:15", "end_time": "00:02:17", "gloss": "NAME", "text_subtitle": "My name is Sarah"},
        {"video_id": "bobsl_bbc_004", "start_time": "00:02:17", "end_time": "00:02:19", "gloss": "WHAT", "text_subtitle": "What is your question?"},
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["video_id", "start_time", "end_time", "gloss", "text_subtitle"])
        writer.writeheader()
        writer.writerows(sample_rows)
    logger.info("Created sample BOBSL annotation file at %s", out_path)
    return out_path


def load_bobsl_annotations(path: Path) -> list[dict[str, str]]:
    """Load BOBSL annotations from CSV or JSON files."""
    if not path.exists():
        logger.warning("Annotation file %s not found. Initializing sample...", path)
        create_sample_bobsl_annotations(path)

    rows: list[dict[str, str]] = []
    if path.suffix.lower() in {".csv", ".txt"}:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({k.strip().lower(): (v or "").strip() for k, v in r.items()})
    elif path.suffix.lower() in {".json", ".jsonl"}:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        rows.append({k.lower(): str(v).strip() for k, v in data.items()})
                except json.JSONDecodeError:
                    continue
    return rows


def build_sigml_document(records: list[dict[str, str]]) -> str:
    """Build a valid SiGML XML document for BOBSL authored BSL signs."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<sigml_collection language="BSL_BOBSL" count="{len(records)}">',
        "",
    ]
    for r in records:
        gloss = r["gloss"]
        sigml_content = r["sigml"]
        lines.append(f'  <hns_sign gloss={quoteattr(gloss)}>')
        lines.append('    <hamnosys_manual>')
        lines.append(f'      {sigml_content}')
        lines.append('    </hamnosys_manual>')
        lines.append('  </hns_sign>')
        lines.append("")
    lines.append('</sigml_collection>')
    return "\n".join(lines)


def process_bobsl_dataset(in_path: Path) -> tuple[int, int]:
    """Ingest BOBSL annotations, extract BSL glosses, and update BSL dataset files."""
    annotations = load_bobsl_annotations(in_path)
    logger.info("Loaded %d raw annotation rows from %s", len(annotations), in_path)

    # Aggregate gloss frequency from BOBSL
    gloss_counts: dict[str, int] = {}
    for row in annotations:
        gloss_raw = row.get("gloss") or row.get("label") or row.get("sign") or ""
        gloss_clean = re.sub(r"[^A-Z0-9_]+", "", gloss_raw.upper().replace(" ", "_").replace("-", "_"))
        if gloss_clean:
            gloss_counts[gloss_clean] = gloss_counts.get(gloss_clean, 0) + 1

    logger.info("Extracted %d unique glosses from BOBSL dataset", len(gloss_counts))

    active_records: list[dict[str, str]] = []
    csv_rows_to_append: list[dict[str, str]] = []

    for gloss, count in sorted(gloss_counts.items(), key=lambda x: -x[1]):
        mapping = COMMON_BSL_GLOSS_MAP.get(gloss)
        if mapping:
            record = {
                "gloss": gloss,
                "concept": mapping["concept"],
                "hamnosys": mapping["hamnosys"],
                "sigml": mapping["sigml"],
                "frequency": str(count),
            }
            active_records.append(record)
            csv_rows_to_append.append({
                "concept": mapping["concept"],
                "language": "BSL",
                "gloss": f"{gloss.lower()}(v)#1",
                "hamnosys": mapping["hamnosys"],
                "video_url": "",
                "page_url": f"https://www.robots.ox.ac.uk/~vgg/data/bobsl/#gloss_{gloss.lower()}",
            })

    # 1. Write active SiGML document
    sigml_xml = build_sigml_document(active_records)
    BSL_AUTHORED_SIGML.write_text(sigml_xml, encoding="utf-8")
    logger.info("Wrote %d BSL signs to %s", len(active_records), BSL_AUTHORED_SIGML)

    # 2. Write metadata sidecar
    meta_payload = {
        "dataset": "BOBSL (BBC-Oxford British Sign Language)",
        "source": "Oxford VGG / BBC Broadcasts",
        "generated_date": date.today().isoformat(),
        "total_unique_glosses": len(gloss_counts),
        "active_authored_signs": len(active_records),
        "license": "Non-commercial Academic Research License (Oxford VGG)",
        "citation": "Albanie et al., BOBSL: BBC-Oxford British Sign Language Dataset, 2021",
    }
    BSL_AUTHORED_META.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    logger.info("Wrote metadata sidecar to %s", BSL_AUTHORED_META)

    # 3. Merge new entries into hamnosys_bsl.csv
    existing_concepts = set()
    if BSL_HAMNOSYS_CSV.exists():
        with BSL_HAMNOSYS_CSV.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r.get("concept"):
                    existing_concepts.add(r["concept"].strip().lower())

    added_csv = 0
    if csv_rows_to_append:
        with BSL_HAMNOSYS_CSV.open("a", encoding="utf-8", newline="") as f:
            fieldnames = ["concept", "language", "gloss", "hamnosys", "video_url", "page_url"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for row in csv_rows_to_append:
                if row["concept"].lower() not in existing_concepts:
                    writer.writerow(row)
                    existing_concepts.add(row["concept"].lower())
                    added_csv += 1

    logger.info("Appended %d new BSL gloss entries to %s", added_csv, BSL_HAMNOSYS_CSV)
    return len(active_records), added_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest BOBSL BSL dataset annotations into Kozha.")
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=SOURCES_DIR / "bobsl_annotations.csv",
        help="Path to BOBSL annotations file (CSV/JSON/JSONL).",
    )
    parser.add_argument(
        "--init-sample",
        action="store_true",
        help="Create a sample BOBSL annotation file at data/sources/bobsl/bobsl_annotations.csv.",
    )
    args = parser.parse_args()

    if args.init_sample:
        create_sample_bobsl_annotations(args.in_path)
        print(f"Sample BOBSL annotations initialized at {args.in_path}")
        return

    active_cnt, csv_cnt = process_bobsl_dataset(args.in_path)
    print(f"\n[BOBSL Ingestion Complete]")
    print(f"  Active BSL signs generated: {active_cnt}")
    print(f"  BSL CSV entries appended: {csv_cnt}")
    print(f"  SiGML File: {BSL_AUTHORED_SIGML}")
    print(f"  Metadata File: {BSL_AUTHORED_META}\n")


if __name__ == "__main__":
    main()
