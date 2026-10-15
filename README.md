# RBI Regulatory Gap Assessment

Agentic RAG system that takes an RBI circular and produces a traceable
compliance gap register.

## The RBI corpus

Eight real documents, listed in [`data/corpus_manifest.yaml`](data/corpus_manifest.yaml):

- **Three Master Directions**: Prepaid Payment Instruments (`md-ppi-2021`),
  Know Your Customer (`md-kyc-2016`) and Digital Payment Security Controls
  (`md-dpsc-2021`).
- **One earlier version of a Master Direction**: the KYC Master Direction as
  updated on 2018-07-12 (`md-kyc-2016-v2018`), in force until the next
  revision on 2019-05-29. It is in the corpus so that the same paragraph exists
  in two versions with different wording, and retrieval can be tested on
  returning the version in force on a given date.
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
should return it, and a query for today should not. The KYC Master Direction
(`md-kyc-2016`) is also repealed, on 2025-11-28. Its entity-specific successor
is likewise out of scope.

The raw PDFs live in `data/raw/` and are not committed. Rebuild them with:

```
.\.venv\Scripts\python.exe scripts\download_corpus.py
```

## The internal policy corpus is synthetic

**The 18 internal policy documents in [`data/internal/`](data/internal/) are
fictional.** They were written for this project and are not real company
data. They describe Kestrel Wallet Services Private Limited (KestrelPay), an
invented non-bank PPI issuer, along with its invented systems and teams. Each
file carries a banner saying so.

The corpus was designed backwards from a known answer. 31 real obligations
were chosen from `md-ppi-2021` and `md-kyc-2016`, and each was given a
planted outcome before any policy was written: 16 covered, 6 partial, 5 gaps
and 4 stale. The stale ones are anchored to an amendment the policy predates,
or to the repealed `md-dpsc-2021`, which never applied to a non-bank PPI
issuer. That answer key is
[`data/internal/gap_ground_truth.yaml`](data/internal/gap_ground_truth.yaml).

Covered obligations are written in operational company language, not the
regulation's wording, so keyword overlap alone cannot match them.
`scripts/check_policy_overlap.py` enforces this. It reports every run of five
or more consecutive words a policy shares with any RBI chunk, ignoring
statute and list names that cannot be paraphrased. It also scores each
covered obligation's distinctive words against only the policy that is meant
to cover it. On the current corpus it reports 0 flagged runs. Adding the
2018 KYC text to the corpus raised one: a generic five-word phrase in a
grievance-policy section (KST-CX-001 §4.4) that matched a 2018 sentence. That
section was reworded to preserve the no-verbatim-overlap property the
synthetic corpus was designed around. The control it describes did not change. The median
keyword overlap is 0.30 (plain) and 0.25 (IDF-weighted), and no covered
obligation reaches 0.40.

```
.\.venv\Scripts\python.exe scripts\check_policy_overlap.py
```

## The retrieval gold set is LLM-drafted and human-reviewed

[`data/eval/gold_set.yaml`](data/eval/gold_set.yaml) holds 100 retrieval
questions, each with the chunk or chunks a correct retriever should return.
It is **LLM-drafted and human-reviewed**, not independently hand-labelled.
Claude read each gold chunk and drafted the question and labels, and the
author reviewed and revised them. The same model family that drafted the questions
may later be scored against them, and that bias should be kept in mind when
reading results.

The questions are phrased the way an analyst would ask, not in the clause's
wording. Otherwise a keyword search would score well and the item would
measure nothing. Four categories: straightforward (30), paraphrased (23),
version-sensitive (23) and repealed-document (24). The last two carry an
`as_of` date. Their correct answer depends on which version of a document was
in force on that date, or on whether the document had been repealed by then.
Scoring rules are in [`docs/EVALUATION.md`](docs/EVALUATION.md).

```
.\.venv\Scripts\python.exe scripts\validate_gold_set.py
```
