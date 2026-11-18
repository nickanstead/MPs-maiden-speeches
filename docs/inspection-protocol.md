# Manual inspection worksheet

The file `data/inspection_sample_1961_1965.csv` is a **preliminary, unreviewed** inspection worksheet, not a completed quality audit.

## Current coverage
- Six selected records each for 1961, 1962, 1963 and 1965 (24 total).
- **1964 is not yet sampled.** The GitHub file-fetch interface did not return the large 1964 CSV; do not interpret this as missing 1964 data.
- Target: add six 1964 records for a 30-record stratified sample.

## Sampling
Within each available year, records were sorted by `word_count`; five selections target the minimum, lower quartile, median, upper quartile and maximum. A sixth prioritises a source exception or a different party, where possible. This is a purposive quality-assurance sample, **not a random or representative sample**, and cannot estimate error prevalence.

## Review procedure
For each record, open the linked official Hansard contribution and compare the full text, opening and closing boundaries, all same-speaker continuations, interventions, date, name, constituency and party. Record each field as pass / fail / uncertain, the reviewer and date, source evidence, and any correction. Do not mark an item reviewed without opening the source.

## Priority flags
- Albert Williams, 1965: only five words in the CSV. Check whether this is genuinely the entire maiden contribution.
- Patrick Duffy, 1963: index date discrepancy.
- Joan Quennell, 1961: date and transcription discrepancies.
- Ronald Brown, 1964: separate unresolved case; review independently, not counted as a verified-speech sample item.

## Interpretation
No manual source comparison has been completed by creating this worksheet. Blank reviewer/date and `not_checked` values are intentional.
