# RBI Regulatory Gap Assessment

Agentic RAG system that takes an RBI circular and produces a traceable
compliance gap register.

## The RBI corpus

Seven real documents, listed in [`data/corpus_manifest.yaml`](data/corpus_manifest.yaml):

- **Three Master Directions**: Prepaid Payment Instruments (`md-ppi-2021`),
  Know Your Customer (`md-kyc-2016`) and Digital Payment Security Controls
  (`md-dpsc-2021`).
- **Four amendment circulars**: three amending the KYC Master Direction
  (`amd-kyc-2024-11`, `amd-kyc-2025-06`, `amd-kyc-2025-08`) and one amending
  the PPI Master Direction (`amd-ppi-2024-02`).

All were taken from RBI's own website. The manifest records each document's
circular and reference numbers, issue date, "amended up to" date,
`effective_from` / `effective_to`, status (`in_force`, `superseded` or
`repealed`), and the document it amends.

**Versions are pinned by SHA-256.** `scripts/download_corpus.py` hashes every
PDF it downloads and writes the hash into the manifest. On later runs a file
whose hash differs from the manifest is never overwritten; the script fails
loudly instead. Every measurement in this project is therefore tied to the
exact bytes of each document.

**`md-dpsc-2021` is deliberately retained even though it is repealed.** The
Master Direction on Digital Payment Security Controls was repealed on
2026-07-31 and replaced by entity-specific Directions, which are out of scope
for this corpus. It stays in so that as-of-date retrieval has a real
supersession case: a query for any date between 2021-08-18 and 2026-07-31
should return it, and a query for today should not.

The raw PDFs live in `data/raw/` and are not committed. Rebuild them with:

```
.\.venv\Scripts\python.exe scripts\download_corpus.py
```
