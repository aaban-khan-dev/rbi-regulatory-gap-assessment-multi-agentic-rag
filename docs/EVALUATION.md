# Evaluation rules

Decisions about how retrieval is scored. Settled here so Phase 7 implements
them rather than re-deciding them.

## Gold set

`data/eval/gold_set.yaml`. LLM-drafted and human-reviewed: Claude read each gold
chunk and drafted the query and labels; Mohammad reviewed and revised the set.
It is not independently hand-labelled. Field meanings are in the file header.

Validate after every re-chunk or re-index (chunk ids are positional):

```
.\.venv\Scripts\python.exe scripts\validate_gold_set.py
```

## Retrieval metrics

Each item is scored on the top `k` chunks the retriever returns for its query,
searched over the item's `corpus` only.

- **Recall@k** = the fraction of the item's gold chunks found in the top `k`.
  An item with two gold chunks that finds one scores 0.5.
- **MRR** = 1 / rank of the first gold chunk in the ranking, or 0 if none is
  found within `k`. Later gold hits do not count.

Both are averaged over items, each item weighted equally. Reported overall and
per category.

`as_of` is part of the item. A configuration without version awareness ignores
it. A version-aware configuration must use it.

## Document dates

Three manifest dates, deliberately different things:

- **`issue_date`**: the date the instrument was first issued. It never changes
  across versions: `md-kyc-2016` and `md-kyc-2016-v2018` are both 2016-02-25.
- **`effective_from` / `effective_to`**: the validity window of *this text*,
  the exact consolidated version in the PDF. For a consolidated Master
  Direction, `effective_from` is its "updated as on" / `amended_up_to` date,
  and `effective_to` is the date the next version or a repeal replaced it
  (null while in force). So `md-kyc-2016-v2018` is valid 2018-07-12 to
  2019-05-29, and `md-kyc-2016` (as amended to 2025-08-14) is valid 2025-08-14
  to 2025-11-28. Versions between those dates are not in the corpus. For
  `md-ppi-2021` and `md-dpsc-2021`, `effective_from` is still the original
  commencement date, because no earlier version of either is in the corpus.

**Amendment circulars**: `effective_from` = `issue_date`; `effective_to` = the
`effective_to` of the document it amends (null if that document is in force).
The three KYC amendments therefore end 2025-11-28; `amd-ppi-2024-02` is open.

**In force on a date**: a chunk is in force on `as_of` when
`effective_from <= as_of < effective_to`, with a null `effective_to` open-ended.
`scripts/validate_gold_set.py` checks every gold chunk is in force on its
item's `as_of` and every stale chunk is not.

**Which items carry `as_of`**: every regulation item. Items built from a
`gap_ground_truth.yaml` obligation use that obligation's date (2025-10-01 for
`md-kyc-2016`, 2026-10-01 for `md-ppi-2021`). Internal items carry none.

**Internal policies are assessed in their current version.** The assessment
asks whether the company is compliant *now* with the rule that applied at the
stated date. So regulation is versioned and controls are not. A KYC obligation
assessed as of 2025-10-01 is compared with today's KYC policy, even if that
policy's own `effective_from` is later. The internal corpus is never
date-filtered, and a policy's `effective_from` is not compared with `as_of`.

**Status must agree with the dates.** On today's date, a document is
`in_force` exactly when its `effective_to` is null or in the future, and
`repealed` or `superseded` exactly when its `effective_to` is in the past.
`scripts/validate_gold_set.py` checks this for every regulation document.
