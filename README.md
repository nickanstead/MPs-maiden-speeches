# UK House of Commons maiden speeches

This pilot covers Commons maiden speeches delivered from 1 January 1961 through
31 December 1965. It contains 180 verified speeches and one unresolved candidate.

- [Annual verified CSVs](data/maiden_speeches)
- [Unresolved candidate](data/unresolved.csv)
- [Older index discrepancy](data/legacy_only.csv)
- [Validation findings and source decisions](docs/validation.md)
- [Data dictionary](docs/data-dictionary.md)
- [Read-only PMQs audit](docs/pmqs-audit.md)

## Rebuild

Use Python 3.10 or later and install Poppler's `pdftotext`. From the
repository root, run:

```sh
python -m pip install -r requirements.txt
python scripts/collect.py
python scripts/validate.py
```

The collector caches source downloads under `.cache/`. The manifest records
the index and membership source hashes. Each row gives the hash of its source
page. Clear the cache to collect the current versions of upstream sources.

Contains Parliamentary information licensed under the
[Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/).
