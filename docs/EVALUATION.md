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

- **nDCG@k**: binary relevance (gain 1 for a gold chunk), discounted by
  log2(rank + 1), divided by the best possible score for that item (all its gold
  chunks, up to k, at the top).
- **Stale rate**: 1 if any of the item's `stale_chunk_ids` is in the top `k`,
  else 0.

All are averaged over items, each item weighted equally. Reported overall and
per category. **Stale rate averages only over items that have `stale_chunk_ids`**
(22 of 100: 8 version_sensitive, 14 repealed_document). Averaging over all 100
would dilute it with items that cannot score a hit. Every report prints the
count (`n_stale`) next to it.

`as_of` is part of the item. A configuration without version awareness ignores
it. A version-aware configuration must use it.

## Harness

```
.\.venv\Scripts\python.exe scripts\run_eval.py --variant naive --k 10
.\.venv\Scripts\python.exe scripts\compare_runs.py data\eval\runs\<run1>.json data\eval\runs\<run2>.json
```

No LLM calls. A retrieval configuration is a function registered in
`regassess/variants.py`; `--variant` selects it. Every variant receives each
item's `as_of`. The `naive` variant ignores it by design.

**Run files** (`data/eval/runs/<variant>_<timestamp>.json`) record the variant,
`k`, retrieval `depth`, embedding model, query prefix, SHA-256 of the gold file,
and each item's gold set, stale set and raw ranking (chunk_id, score). Metrics
are recomputed from the rankings, so a new metric applies to old runs.
`compare_runs.py` warns when runs differ in gold hash, `k`, model or prefix.

**Depth.** Rankings are stored to depth 50 (`--depth`), metrics computed at `k`.
Deeper than `k` so recall at a larger cutoff needs no re-run; not the whole
corpus (709 regulation chunks), which would be mostly noise.

**Corpus scoping.** Each query is searched in its item's `corpus` only. This
measures the real path: the production graph has separate regulation-retriever
and control-retriever nodes, each scoped to one corpus. Searching both corpora
together would let internal policies crowd out regulation answers, a failure the
real system cannot have.

**Query prefix.** bge-small-en-v1.5 expects the instruction `Represent this
sentence for searching relevant passages: ` on queries and nothing on passages.
`regassess/embeddings.py` already did exactly that before Phase 7, so no A/B run
was needed. The prefix is now the `query_prefix` setting in `config.py` (override
with `QUERY_PREFIX` in `.env`) and is stored in every run file. No with/without
comparison has been measured. Changing it invalidates every recorded run.

**Parent-heading context.** A chunk filed under a nested clause (`9.2(c)`) is a
tail whose parent heading (`9.2 Full-KYC PPIs`) sits in an earlier chunk.
`regassess/chunking.py` records that heading in a separate `context` field: the
nearest parent clause's first line, cut at the first `": "`, capped at 200
characters, set only when the parent is not already inside the chunk. The
embedding input is `context + "\n" + text` only when `PARENT_CONTEXT` is on
(`embeddings.passage_text`); **the default is off**, because it lowered naive
recall@10 from 0.700 to 0.670 (README, "A negative result"). `text` stays verbatim
so citations quote the source, and chunk ids, boundaries and `clause_path` are
unchanged. A table unit is never chosen as a parent. Internal policy chunks have no
context. Run files record the flag; changing it needs `build_index.py` and a new
baseline.

**Hybrid retrieval (`--variant hybrid`, Phase 8).** Vector search and BM25 over the
item's corpus, fused by Reciprocal Rank Fusion: `score = sum over lists of 1/(k + rank)`,
rank from 1, ties broken by `chunk_id`. Settings that change the numbers are written
to each run file as `variant_config`, and `compare_runs.py` warns when two runs of one
variant differ in it:

- `rrf_k` = 60 (literature default, **not tuned** on the gold set; `RRF_K` in `.env`);
- `rrf_candidates` = 50: each list is cut to 50 before fusing, independent of `--depth`;
- BM25: `rank_bm25.BM25Okapi`, k1 = 1.5, b = 0.75, epsilon = 0.25 (library defaults, passed
  explicitly, **not tuned**), one in-memory index per corpus built from Postgres at first
  use;
- tokenizer: lowercase; a comma-joined digit group (`2,00,000`, `10,000`) is one token,
  everything else a `[a-z0-9]+` run. No stemming, no stopwords. The digit rule exists
  because the plain split turned `Rs.2,00,000` into `rs 2 00 000`, which cannot match an
  exact amount. It is the only tokenizer rule beyond the plain split.

BM25 indexes `embeddings.passage_text()`, the function `build_index.py` embeds, so both
retrievers see the same text (plain `text`; `context + text` if `PARENT_CONTEXT` is on).
The bge query prefix is added inside `embed_query()` and never reaches BM25. Chunks that
share no token with the query are left out of the BM25 list. Like `naive`, `hybrid`
ignores `as_of`.

**Two more variants, same BM25 settings.** `bm25_only` is keyword search alone, no
fusion; chunks sharing no token with the query are excluded, so its rankings can be
shorter than the depth. `hybrid_nostop` is `hybrid` with the NLTK English stopword list
(`regassess/stopwords.py`, checked equal to `nltk.corpus.stopwords.words('english')`)
removed from the BM25 query and documents; the vector side is untouched. It is its own
row; `hybrid` is unchanged (its recorded `variant_config` is identical to the saved run's).
The list removes `not`, `no`, `should` and single letters such as the clause markers
`(a)`, `(i)`, and keeps `must`, `may`, `shall`. Its `tokenizer` string reads "no stemming,
no stopwords; then NLTK English stopwords removed", which is clumsy wording, not a
contradiction; it is left as recorded in the run file.

`compare_runs.py --k 50` scores every run at k=50 from the stored depth-50 rankings, with
no re-run (`--k` may not exceed a run's depth).

**Gold set revisions.** The first run's diagnosis found two incomplete golds. G-061
gained `amd-kyc-2024-11:0005` and G-079 gained `md-dpsc-2021:0000`; G-012 was
reviewed and left alone. Both changes were made after the baseline misses were
seen, which makes later results slightly more lenient. The notes in the gold file
say so. The gold file hash changed, so the first run was kept as
`naive_preheadings_*.json` and a new baseline recorded.

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
