#!/usr/bin/env python3
"""Validate a maiden-speeches CSV. Standard library only.

Usage: python scripts/validate.py data/maiden_speeches/1961.csv
The main dataset must contain verified speeches only.
"""
import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

REQUIRED = {
    "speech_id", "speech_date", "chamber", "speaker_name_hansard",
    "hansard_url", "original_text", "identification_basis",
    "verification_status",
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
            if not (row.get("hansard_url") or "").startswith("https://"):
                errors.append(f"{prefix}: source URL must be HTTPS")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.csv_file)
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"Cannot validate: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {args.csv_file}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
