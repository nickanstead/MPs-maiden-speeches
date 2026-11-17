# PMQs read-only source audit

Reviewed [PMQs at ec68459](https://github.com/nickanstead/PMQs/tree/ec6845906cb161c183de1cce429df1069db9376c).

| PMQs source | Method assessed and pilot decision |
| --- | --- |
| `scripts/resolve_names.py` | Checks dated memberships and uses forenames and constituency context to distinguish similar Hansard speaker names. The pilot adapts the dated join, requiring a unique identity keyed by surname and seat or parliamentary ID. |
| `scripts/enrich_parties.py` | Combines election winners and dated defection exceptions. Its nearest-general-election fallback for by-elections can span a party change. The pilot uses the contemporary affiliation reported by the maiden-speech index and checks explicit exceptions against parliamentary evidence. |
| `scripts/extract_pmqs.py` | Separates retrieval, transcription and annual CSV output, and reports missing source material. The pilot uses the same approach but starts from the official maiden-speech index and Hansard contribution anchors. |
| `data/reference/{historic_hansard_matches,manual_names,ambiguous_names}.csv` | Match status, stable person IDs and explicit ambiguity or override evidence are useful patterns. PMQs rows are exchange-specific, so the pilot builds its own matches and exceptions. |

No PMQs code, exchange records or metadata rows were imported into this repository.
