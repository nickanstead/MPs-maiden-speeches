# Data dictionary

One row represents one indexed speech candidate. The annual files contain
the verified corpus. The unresolved file uses the same columns.

| Fields | Meaning |
| --- | --- |
| `speech_id`, `source_record_id` | Project identifier and native Hansard contribution ID. |
| `speech_date`, `chamber` | Sitting date and House validated against the transcript. |
| `index_date`, `index_row`, `index_url` | Date, spreadsheet row, and source of the modern Library index entry. |
| `member_name`, `surname`, `wikidata_id`, `mnis_id` | Member details as indexed. Missing MNIS IDs are blank. |
| `member_id`, `member_id_source` | ParlParse person identifier and source. |
| `speaker_name_hansard`, `constituency_hansard` | Hansard attribution and printed seat when available. |
| `constituency_at_speech`, `constituency_membership` | Seat in the modern index and name in the matched Commons membership record. Historical naming variants are retained. |
| `party_at_speech`, `party_source` | Party label for the speech and citation. |
| `hansard_url`, `hansard_reference`, `hansard_start_column` | Official contribution URL, indexed volume and columns, and preceding column marker from the transcript. |
| `legacy_index_url`, `legacy_index_page`, `legacy_index_entry` | Older index, PDF page, and source line where matched. |
| `original_text`, `word_count`, `text_sha256` | Verbatim wording from the anchored speaker turn, excluding HTML and navigational markup. Whitespace at block edges is trimmed. The word count uses whitespace-separated tokens and the digest hashes the UTF-8 text. Historic OCR spellings and punctuation are retained. |
| `transcript_sha256` | SHA-256 of the downloaded HTML page. |
| `identification_basis`, `verification_status`, `verification_notes` | Evidence, decision and any unresolved issue. |
| Other note, URL and continuation fields | Source disagreements, corrections and reviewed transcript boundaries, where applicable. |

The legacy-only CSV holds older entries with no direct current index
match. Its disposition distinguishes superseded entries from candidates.
