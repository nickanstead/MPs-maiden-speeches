# Maiden speeches pilot: 1961–1965

## Aim
Build a reproducible, source-linked corpus of maiden speeches delivered in the UK House of Commons between 1961-01-01 and 1965-12-31, as a pilot for a 1945–present dataset.

## Unit of analysis
One row per maiden speech, not one row per MP. Do not infer maiden status from the first contribution recorded for an MP. Preserve uncertain candidates separately until verified.

## Sources
- Official Hansard for speech text, date and citations.
- Parliamentary maiden-speech indexes for independent cross-checking, after verifying coverage.
- ParlParse / TheyWorkForYou for historical debate data and speaker identifiers.
- The PMQs repository as a **read-only** reference for historic name resolution, party histories, diagnostics and ingestion patterns. PMQs questioners are not a complete MP register.

## Pilot steps
1. Audit PMQs scripts and metadata, documenting which parts can be reused.
2. Establish an independently sourced candidate list for 1961–1965.
3. Retrieve and preserve raw speech text and source references.
4. Resolve members and party/constituency **as of speech date**.
5. Verify candidates against the parliamentary index and the source transcript; log disagreements.
6. Publish validated annual CSVs, candidate diagnostics and an auditable quality report.

## Quality gates
- Commons chamber and speech date in range.
- Full text, source URL and identification basis present.
- No duplicate source speech IDs.
- Unknown party or constituency remains missing, not guessed.
- Distinguish verified, candidate and rejected records.
- Report precision on a reviewed sample and coverage against the index, with denominators.

## Scope boundaries
No PMQs repository writes. No merge into main without explicit approval. No unverified speech will be presented as confirmed.

## Open decisions
- Whether a speech documented in an authoritative index but not explicitly labelled in Hansard can qualify after independent verification.
- How to handle historic OCR issues and interruptions in speech boundaries.
