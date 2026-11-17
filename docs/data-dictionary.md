# Proposed schema — draft

The final main table will contain verified speeches; a separate candidate log retains uncertain and rejected items.

| Column | Description |
|---|---|
| speech_id | Stable project identifier, tied to source |
| speech_date | ISO date |
| chamber | House of Commons |
| speaker_name_hansard | Speaker name as printed |
| member_id | Stable identifier, system documented |
| member_id_source | Provenance of ID match |
| party_at_speech | Party at speech date |
| constituency_at_speech | Constituency at speech date |
| hansard_url | Canonical source URL |
| source_record_id | Native source ID where available |
| original_text | Text as retrieved |
| clean_text | Normalised analysis text |
| word_count | Count based on clean_text |
| identification_basis | Hansard label / index / independent verification |
| verification_status | verified / candidate / rejected |
| verification_notes | Review comments |
| retrieved_at | UTC timestamp |

Exact identifier formats and text-cleaning rules will be fixed after the source audit. Missing values must not be inferred.
