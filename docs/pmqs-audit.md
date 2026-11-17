# PMQs reuse audit — initial inventory

Read-only reference: https://github.com/nickanstead/PMQs

The PMQs README documents annual CSVs in `data/pmqs/`, diagnostics in `data/diagnostics/`, historical speaker resolution in `data/reference/`, collection scripts in `scripts/`, and automated workflows in `.github/workflows/`.

Sources documented there include ParlParse/TheyWorkForYou, historic Hansard, and UK general election data.

## Reuse candidates
- historical MP name matching and identification provenance
- date-specific party attribution and party-switch handling
- diagnostics and reproducible collection patterns
- GitHub Actions conventions

## Limitations
PMQs includes questioners, not all MPs. Its roles and party metadata must not be copied across dates without checking. Maiden-speech extraction needs a distinct identification method.

## Next audit step
Inspect actual script files and historical reference formats before copying or adapting code. This is an initial README-level assessment, not yet a completed source-code audit.
