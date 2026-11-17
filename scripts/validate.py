#!/usr/bin/env python3
"""Validate a maiden-speeches CSV. Standard library only.

Usage: python scripts/validate.py data/maiden_speeches/1961.csv
The main dataset must contain verified speeches only.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter
from urllib.parse import urlsplit
from pathlib import Path

REQUIRED = {
    "speech_id", "speech_date", "chamber", "speaker_name_hansard",
    "hansard_url", "original_text", "identification_basis",
    "verification_status", "index_row", "member_id", "member_id_source",
    "party_at_speech", "party_source", "constituency_at_speech",
    "constituency_membership", "source_record_id", "hansard_reference",
    "index_url", "text_sha256", "transcript_sha256", "word_count",
}

def validate(path: Path) -> list[str]:
    errors = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return ["CSV has no header"]
        missing = REQUIRED - set(reader.fieldnames)
        if missing:
            return [f"Missing required columns: {', '.join(sorted(missing))}"]
        seen = set()
        for n, row in enumerate(reader, start=2):
            prefix = f"row {n}"
            for field in REQUIRED:
                if not (row.get(field) or "").strip():
                    errors.append(f"{prefix}: empty {field}")
            sid = (row.get("speech_id") or "").strip()
            if sid and sid in seen:
                errors.append(f"{prefix}: duplicate speech_id {sid}")
            seen.add(sid)
            try:
                date = dt.date.fromisoformat(row["speech_date"])
                if not dt.date(1961, 1, 1) <= date <= dt.date(1965, 12, 31):
                    errors.append(f"{prefix}: date outside pilot period")
            except (ValueError, TypeError):
                errors.append(f"{prefix}: invalid ISO speech_date")
            if (row.get("chamber") or "").strip() != "House of Commons":
                errors.append(f"{prefix}: unexpected chamber")
            if (row.get("verification_status") or "").strip() != "verified":
                errors.append(f"{prefix}: unverified record in main dataset")
            source = urlsplit(row["hansard_url"] or "")
            if source.scheme != "https" or source.hostname not in {
                "hansard.parliament.uk", "api.parliament.uk"
            }:
                errors.append(f"{prefix}: expected an official Hansard URL")
            if source.fragment not in {row["source_record_id"],
                                       "contribution-" + (row["source_record_id"] or "")}:
                errors.append(f"{prefix}: source ID differs from URL anchor")
            if sid != "commons-" + (row["source_record_id"] or ""):
                errors.append(f"{prefix}: speech and source IDs disagree")
            text = row["original_text"] or ""
            if hashlib.sha256(text.encode()).hexdigest() != row["text_sha256"]:
                errors.append(f"{prefix}: text hash mismatch")
            if str(len(text.split())) != row["word_count"]:
                errors.append(f"{prefix}: incorrect word count")
            if not re.fullmatch("[0-9a-f]{64}", row["transcript_sha256"] or ""):
                errors.append(f"{prefix}: missing or invalid transcript hash")
    return errors

def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_pilot(directory):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    errors = []
    verified = []
    for year in range(1961, 1966):
        path = directory / "maiden_speeches" / f"{year}.csv"
        errors.extend(f"{year}: {error}" for error in validate(path))
        rows = read_rows(path)
        if any(not row["speech_date"].startswith(str(year)) for row in rows):
            errors.append(f"{year}: speech is in the wrong annual file")
        verified.extend(rows)
    ids = [row["speech_id"] for row in verified]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate speech IDs across years")
    unresolved = read_rows(directory / "unresolved.csv")
    if any(row["verification_status"] != "candidate" or not row["verification_notes"]
           for row in unresolved):
        errors.append("Unresolved rows require candidate status and an explanation")
    seen = Counter(row["index_row"] for row in verified + unresolved)
    if seen != Counter(map(str, manifest["index_rows"])) or any(n != 1 for n in seen.values()):
        errors.append("The two datasets must account for each modern index row exactly once")
    counts = Counter(row["speech_date"][:4] for row in verified)
    if counts != manifest["verified_by_year"]:
        errors.append("Manifest and annual verified counts differ")
    legacy = read_rows(directory / "legacy_only.csv")
    accounted = {(row["legacy_index_page"], row["legacy_index_entry"])
                 for row in verified + unresolved if row["legacy_index_page"]}
    accounted.update((row["page"], row["entry"]) for row in legacy)
    if len(accounted) != manifest["legacy_index_entries"]:
        errors.append("Legacy index reconciliation is incomplete")
    if not errors:
        pending = len(unresolved) + sum(row["disposition"] == "candidate" for row in legacy)
        print(f"{len(verified)} verified, {pending} unresolved, annual counts {dict(sorted(counts.items()))}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    try:
        errors = validate_pilot(args.path) if args.path.is_dir() else validate(args.path)
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        print(f"Cannot validate: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {args.path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
