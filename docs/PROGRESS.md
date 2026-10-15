# Progress

Updated at the end of every phase. A new session reads this first.

## Current state

Phases 0, 1 and 2 complete. Phase 0: config default is `gemini-3.8-flash`; `--live` unconfirmed after a 503. Phase 1: seven PDFs on disk, hashes pinned (an eighth, `md-kyc-2016-v2018`, was added in Phase 6). Phase 2: chunk files in `data/processed/` (see Phase 2). The Phase 2 Withdrawn-stamp discrepancy is resolved (the three KYC amendments are `repealed`, Phase 6). Phase 4 complete (pgvector index and naive CLI search, see Phase 4). Phase 3 in progress: ground truth and 18 policies written, overlap check passes. **Not yet done:** parsing the policies through the chunking pipeline (Phase 3 exit criterion). Open decisions are listed under Phase 3. Phase 5 built, not verified (Gemini 503). **Phase 6 complete:** 100-item gold set, validator passes 12/12 (see Phase 6); its end-of-phase decisions are resolved.

## Phase 0 — Repo and environment

**Built**
- `regassess` package with a version string.
- `regassess/config.py`: pydantic-settings `settings` object. Reads `.env` through an absolute path, so cwd doesn't matter. Exposes `project_root`, `data_dir`, `raw_dir`, `processed_dir`, `gemini_api_key` (required), `gemini_model`, `embedding_model`. Creates the data directories on import.
- `scripts/verify_setup.py`: five PASS/FAIL checks, plus `--live` for one Gemini call. Exit code 1 on any failure.

**Files added**
- `regassess/__init__.py`
- `regassess/config.py`
- `scripts/verify_setup.py`

**Files changed**
- `.gitignore`: added `.venv/` (it only ignored `venv/`).
- `docs/PROGRESS.md`: this file.

**Decisions**
- Environment is `.venv`, Python **3.11.9** (measured). The Python check enforces 3.11.x, matching CLAUDE.md. The original Phase 0 prompt said 3.12; that was wrong.
- `pydantic-settings` (reads `.env` into typed settings) and `google-genai` (current Gemini SDK) were listed in `requirements.txt` but not installed. Both are now installed in `.venv`; `requirements.txt` is unchanged.
- `gemini_api_key` has no default, so a missing key fails at import. `verify_setup.py` reports that as a FAIL line.
- numpy is not installed; torch warns about it. Not needed yet; add when a phase imports it.

**Open item — Gemini model name (needs your decision)**
`--live` fails with 404 for the default `gemini-2.5-flash`: "no longer available to new users", and the API suggests `gemini-3.8-flash`. A one-off override to `gemini-3.8-flash` reached the model but returned 503 (high demand), so it was not confirmed end to end. Options: change the default in `config.py`, or set `GEMINI_MODEL` in `.env`. Not changed, since you specified the default.

**Verify**
```
.\.venv\Scripts\python.exe scripts\verify_setup.py
.\.venv\Scripts\python.exe scripts\verify_setup.py --live
```
Measured: the first command passes all 5 checks (exit 0). `--live` fails as described above.

## Phase 1 — RBI corpus acquisition (complete)

**Status: complete.** The manual steps below were done: seven PDFs are in `data/raw/` and every SHA-256 is pinned in the manifest. (This section was stale until Phase 2 and described Phase 1 as blocked.) The "Manual steps needed" list is kept as a record of how the PDFs were obtained.

**Built**
- `data/corpus_manifest.yaml`: seven documents, fields copied from `docs/phase1_corpus.md`. All `sha256` empty. The four amendments omit `amended_up_to`, `effective_from`, `effective_to` because the source file doesn't give them.
- `scripts/download_corpus.py`: downloads to `data/raw/<doc_id>.pdf`, pins SHA-256 in the manifest. Idempotent; fails loudly on hash mismatch (never overwrites); per-document error for empty url, HTTP errors, network errors; continues past failures; prints downloaded / skipped / failed; exit 1 if any failed.
- `README.md`: corpus section.

**Files added**: `data/corpus_manifest.yaml`, `scripts/download_corpus.py`, `README.md`
**Files changed**: `requirements.txt`, `docs/PROGRESS.md`

**Finding — RBI blocks scripted downloads.** The three Master Direction URLs return HTTP 200 with an F5 bot-protection HTML page, not a PDF. My first version saved and hashed these as PDFs (caught because all three were ~45 KB). The script now checks for the `%PDF-` signature and fails with a clear message. I did not try to evade the protection.

**Manual steps needed**
1. Open each Master Direction url in a browser and save the PDF as `data/raw/md-ppi-2021.pdf`, `md-kyc-2016.pdf`, `md-dpsc-2021.pdf`.
2. Fill in the four empty amendment `url` fields in the manifest, then save those PDFs as `data/raw/<doc_id>.pdf` the same way (the url fields may be useless given the bot block, but keep them for provenance).
3. Run the script; files already present and valid are adopted and their hashes recorded.
4. Open the KYC PDF: if it carries a "Withdrawn" watermark, set `md-kyc-2016` to `status: repealed` and set `effective_to`.

**Decisions**
- New dependency `pyyaml`: read and write the manifest.
- New dependency `requests`: HTTP download.
- Existing file with an empty manifest hash is adopted (hash recorded), not re-downloaded. This is the path manual downloads take.
- PyYAML rewrites the manifest and drops comments, so it holds data only.
- Importing `regassess.config` means the downloader needs `GEMINI_API_KEY` in `.env` even though it never calls Gemini. Deferred; harmless for now.

**Verify**
```
.\.venv\Scripts\python.exe scripts\download_corpus.py
```
Expected once the manual steps are done: `7 skipped, 0 failed` on a second run. Measured so far: with no PDFs, all 7 fail with the messages above (exit 1); a dummy `%PDF-` file is adopted, and altering it afterwards triggers the SOURCE CHANGED failure.

## Phase 2 — Parsing and structure-aware chunking (complete)

**Built**
- `regassess/parsing.py`: thin Docling wrapper. Long PDFs are parsed in 25-page segments (documents of 40 pages or fewer in one go), each cached as Docling JSON in `data/processed/_docling_cache/`, keyed by the manifest SHA-256. Also holds the watermark stripper.
- `regassess/chunking.py`: structure-aware chunker (details below).
- `scripts/build_chunks.py`: parse + chunk + write `data/processed/<doc_id>.jsonl`, print the tables below, write `data/processed/_build_report.json` (per-document `watermark_detected`, `watermark_count`, pages hit, and the text around every hit).

**Files added**: `regassess/parsing.py`, `regassess/chunking.py`, `scripts/build_chunks.py`
**Files changed**: `requirements.txt`, `docs/PROGRESS.md`
**Generated, not committed**: `data/processed/*.jsonl` (7), `_build_report.json`, `_docling_cache/`

**Chunk record**: `chunk_id, doc_id, clause_path, clause_depth, covers, heading, page_start, page_end, text`, plus from the manifest `status, effective_from, effective_to, issue_date, amended_up_to, document_type, amends`. `clause_path` is the path of the chunk's *first* clause; `covers` lists every clause inside the chunk (a chunk is a clause plus its children, up to 2000 characters). `clause_path` is `null` when no clause number could be established; never guessed.

**Results (measured, from the last run of `build_chunks.py`)**

| doc_id | pages | chunks | null clause_path | median chars |
|---|---|---|---|---|
| md-ppi-2021 | 40 | 157 | 15 (10%) | 456 |
| md-kyc-2016 | 107 | 303 | 7 (2%) | 525 |
| md-dpsc-2021 | 22 | 87 | 5 (6%) | 347 |
| amd-kyc-2024-11 | 3 | 7 | 2 (29%) | 595 |
| amd-kyc-2025-06 | 3 | 6 | 1 (17%) | 249 |
| amd-kyc-2025-08 | 2 | 5 | 1 (20%) | 371 |
| amd-ppi-2024-02 | 1 | 3 | 1 (33%) | 429 |

Clause depth, counted over every clause inside the chunks (not just each chunk's first): PPI 150 / 159 / 33, KYC 168 / 292 / 197, DPSC 71 / 68 / 0 at 1 / 2 / 3+ levels. The hierarchy comes through for the three Master Directions. The amendments are nearly flat: their instructions arrive from Docling as one long text blob.

Page-break continuation merges: PPI 3, KYC 16, DPSC 4, amd-kyc-2024-11 0, amd-kyc-2025-06 1, amd-kyc-2025-08 1, amd-ppi-2024-02 0 (25 total). Same-page merges (Docling split a sentence mid-line): 9 total. The PPI §2.8 "Small PPIs" case is verified: one chunk, `2.8` covering `2.8`, `2.8(i)`, `2.8(ii)`, pages 3-4.

**Watermark (stripped at the parsing stage, reported, not silent)**: the red "Withdrawn" stamp is extracted as plain text, merged into body paragraphs (sometimes mid-sentence, sometimes glued to a word with no space, sometimes as its own item). It is removed in memory with a case-sensitive pattern (`\s*Withdrawn(?![a-z])`); the on-disk cache keeps the raw parse. Hits equal pages hit in every document (one stamp per page): KYC 98 hits on 98 of 107 pages, DPSC 19 on 19 of 22, amd-kyc-2024-11 3 on 3, amd-kyc-2025-06 2 on 3, amd-kyc-2025-08 2 on 2, PPI 0, amd-ppi-2024-02 0. I read the context of every DPSC and amendment hit and a filtered sample of the KYC hits; no false positives. Lowercase "withdrawn" in prose (e.g. PPI 5.5) is untouched.

**Manifest discrepancy (resolved in Phase 6: the three amendments are now `status: repealed`)**: `amd-kyc-2024-11`, `amd-kyc-2025-06` and `amd-kyc-2025-08` are `status: in_force` in the manifest but their PDFs carry the Withdrawn stamp. Everything else agrees (PPI and amd-ppi in force and unstamped; KYC and DPSC repealed and stamped). `status` and `effective_to` drive Phase 10's as-of-date filtering, so this needs resolving before then.

**Decisions**
- New dependency `docling`: PDF parsing with layout and table models.
- New dependency `pypdfium2`: page count of a PDF, to plan parse segments. Already installed as a Docling dependency; listed because the code imports it directly.
- OCR off (`do_ocr=False`). Measured on `md-ppi-2021`: all 437 items identical with OCR on and off; 643 s vs 414 s. The PDFs have a text layer.
- Parse in cached segments, because Docling is ~10 s/page on this CPU (KYC alone would be ~18 minutes, over the tool timeout).
- Clause numbers are resolved by sequence, not by a per-document setting: `b` after `a` is its sibling, a first `a`/`i`/`1` is a child, and a bare integer marker is a top-level paragraph if it is the next one after the current top-level number, else a sub-item. My first version used a per-document flag and was wrong: md-kyc-2016 uses `9.`, `10.` as top-level list markers *and* `1.`, `2.` as sub-items (122 unplaced numbers before the fix, 8 after).
- Tables are always their own chunks under the enclosing clause; oversize tables split by rows with the header repeated. Docling puts a table's caption inside its markdown, and the caption is sometimes a clause (PPI 17.5); the caption is now emitted as a normal text element first.
- Chunk size: at most 2000 characters (bge-small's window is 512 tokens). A clause that fits stays whole with its children; one that does not splits at child clauses, each child its own chunk, fragments under 250 characters joined to a neighbour.
- A sub-level number with no enclosing clause gets `clause_path: null`.
- Footnote text is dropped from chunks (163 items in KYC alone). It records amendment provenance ("Amended vide circular ... dated ..."). **Deferred**: candidate input for Phase 10 version awareness.
- `heading` is the enclosing top-level section heading, not a sub-heading.

**Known limitations (not fixed)**
- Docling sometimes merges a clause heading into the previous paragraph's text (e.g. KYC `55A.` inside the end of paragraph 55). The boundary is inside one Docling item, so the chunk keeps the earlier path and contains the next clause's start.
- Amendment instructions (i), (ii), (iii) in a single Docling text blob stay one chunk.
- Annex I (uppercase `A.`..`K.` steps) and Annex II (a Government of India order) have `null` or unreliable paths. Annex II of md-kyc-2016 is external text and at least one chunk there carries a path (`15`) taken from a distribution list.
- `amd-*` documents have no `effective_from`/`effective_to`/`amended_up_to` in the manifest, so those chunk fields are `null`.
- Unplaced numbers remain: PPI 3, KYC 8, amd-kyc-2024-11 3. The first 12 examples per document are in `_build_report.json`.
- I checked chunks against Docling's output and a consistency test (0 of 298 chunks that open with a clause number disagree with their `clause_path`), not against the PDFs by eye. The 20-chunk check against the PDFs is yours.

**Spot-check list (20 chunks, to compare against the PDFs)**
`md-ppi-2021`: 0012 (p5, 4.6), 0035 (p8, 7.11(d)), 0058 (p12, 9.2(n)), 0081 (p16, 12.3(iii)(a)), 0104 (p20, 15.3(g)), 0127 (p24, 17.5 with its table)
`md-kyc-2016`: 0022 (p10, 3(xx)), 0064 (p22-23, 14), 0106 (p33-34, 24), 0148 (p49, 46(b)), 0190 (p64, 64(v)), 0236 (p79, 7(vi)), 0280 (p91, 7.1)
`md-dpsc-2021`: 0012 (p5-6, 8), 0032 (p9, 28), 0052 (p13, 44), 0074 (p17, 64)
`amd-kyc-2024-11`: 0003 (p2, II); `amd-kyc-2025-06`: 0003 (p1, 3(ii)); `amd-kyc-2025-08`: 0003 (p1, 3(ii))
(Chunk ids are `<doc_id>:<number>`. The list was chosen by position, spread evenly through each document, so it is not cherry-picked. It was generated from the final files.)

**Verify**
```
.\.venv\Scripts\python.exe scripts\build_chunks.py
```
Expected: the summary tables above and seven `.jsonl` files in `data/processed/`. A cold run is slow (about 10 s/page, ~25 minutes for all seven). Use `--max-new-segments 2` to bound one invocation to about 8 minutes and re-run to resume. With the cache warm it takes seconds.

**Suggested commit breakdown**
1. `add docling and pypdfium2 dependencies` — `requirements.txt`
2. `add pdf parsing wrapper with segmented docling cache and watermark stripping` — `regassess/parsing.py` (one file; to split the watermark stripper into its own commit use `git add -p`)
3. `add structure-aware clause chunker` — `regassess/chunking.py`
4. `add build_chunks script with watermark and manifest cross-check` — `scripts/build_chunks.py`
5. `update progress for phase 2` — `docs/PROGRESS.md`

Nothing untracked needs flagging: `data/processed/` and `data/raw/` are gitignored.

## Phase 3 — Synthetic internal policy corpus (in progress)

**Status:** the design (Stage A) and the policy documents (Stage B) are done. Not yet done: parsing the policies through the chunking pipeline, which the phase plan's exit criterion requires. `scripts/build_chunks.py` is driven by the manifest and reads PDFs only, so the Markdown policies need a new input path.

**Built**
- `data/internal/gap_ground_truth.yaml`: 31 real obligations, each with `doc_id`, `clause_path`, `outcome`, `policy_doc`, and a one-line `note` for non-covered rows. Every `(doc_id, clause_path)` pair, stale sources included, is the `clause_path` of exactly one chunk in `data/processed/`. Lookup fields: `sub_clause` (the precise paragraph when the obligation sits inside a chunk filed under an earlier clause), `chunk_id`, and `stale_source` on STALE rows. Split: 16 COVERED, 6 PARTIAL, 5 GAP, 4 STALE. By source: 20 from md-ppi-2021, 11 from md-kyc-2016. md-dpsc-2021 appears only as a stale source.
- 18 policy documents, `data/internal/KST-*.md`, for the fictional non-bank PPI issuer Kestrel Wallet Services (KestrelPay). They share one set of fictional systems (Sentinel, Rules Console, Ledger Core, Onboard, Watchlist Hub, CareDesk, Notify, Vault, TreasuryDesk), have numbered paragraphs, and carry a synthetic-document banner. Each contains content unrelated to the planted obligations, so the planted controls are not the only text.
- `scripts/check_policy_overlap.py`, three reports:
  1. every run of 5+ consecutive words a policy shares with any RBI chunk (all seven documents), allowing only an explicit list of statute and list names;
  2. the longest run each ground-truth row's policy shares with that row's own chunk;
  3. keyword overlap for COVERED rows: the chunk's distinctive words (lowercase alphabetic, 3+ letters, stopwords removed, crude plural fold, numbers excluded) against only that row's `policy_doc`, as a plain share and an IDF-weighted share (IDF over all RBI chunks).

  Exit 1 if any run is flagged or either median exceeds 0.4.

**Files added**: `data/internal/gap_ground_truth.yaml`, `data/internal/KST-*.md` (18), `scripts/check_policy_overlap.py`
**Files changed**: `regassess/config.py` (new `internal_dir` setting), `README.md` (synthetic corpus disclosure), `docs/PROGRESS.md`

**Results (measured, runs of `check_policy_overlap.py`)**
- Phrase reuse, corpus-wide: 0 flagged runs across 18 policies; 1 allowed name match (KST-AML-009, the 2007 Terrorism Order). The first run, before any rewording, had 15 flagged runs. Two of them were real echoes of other clauses: "in english hindi and the" (PPI 16.1) and "with full details of the" (KYC 52(h)). All 15 were reworded rather than allowlisted, except "ministry of home affairs".
- Keyword overlap, COVERED rows against their own policy_doc. **Before:** median plain 0.35, median IDF 0.33; worst five by plain OBL-06 0.57, OBL-11 0.47, OBL-04 0.44, OBL-16 0.42, OBL-05 0.41. The 0.4 median rule did not trigger, but those five sections were reworded anyway (SEC-001, AUD-001, PRD-001, AML-004, FIN-003), keeping the controls themselves unchanged. **After:** median plain 0.30, median IDF 0.25; worst five by plain OBL-11 0.39, OBL-01 0.38, OBL-10 0.37, OBL-07 0.34, OBL-16 0.33.
- The "before" figures were taken after the ground-truth fix below, so both runs score the same 16 rows.
- What remains shared is mostly domain nouns a real policy must use (CERT-In, auditor, escrow, CKYCR, PEP, wallet, cash). The header table ("Approved by", "Last reviewed") also adds "approved" and "review" to every policy. It was left alone as normal policy formatting.

**Ground-truth fix (after review)**: 18 obligations and 2 stale sources had a `clause_path` that is not any chunk's `clause_path`. The addresses were real paragraph numbers read from the chunk text, but the chunker files a chunk under its first clause, so sub-clauses only appear in `covers`. 38(e) and amd-kyc-2025-06 4(iii) appeared nowhere in the chunk metadata (chunker mislabel). Fixes:
- 15 rows: `clause_path` now points at the containing chunk, with the precise paragraph in `sub_clause`.
- 4 rows replaced because their only available path was wrong or ambiguous:
  - OBL-13: KYC 12(a) → 5A (path `12` matched 2 chunks);
  - OBL-26: KYC 8(b) → 54, a GAP on FATF-listed jurisdictions (`8` matched 3);
  - OBL-30: KYC 38(e) → 38, the June 2025 low-risk proviso, still STALE in KST-AML-006;
  - OBL-31: KYC 11 → 18(iii)(b), the August 2025 V-CIP liveness insertion, STALE in KST-AML-004 (`11` matched 18 chunks).
- KST-AML-001 §3 was extended to cover 5A. KST-AML-004 gained a V-CIP procedure section and was backdated to 2025-04-22 so it predates amd-kyc-2025-08.

**Decisions**
- Company is a non-bank PPI issuer. md-dpsc-2021 para 2 limits DPSC to SCBs (excl. RRBs), SFBs, Payments Banks and credit-card NBFCs, so no DPSC clause is a binding obligation. The two DPSC-anchored policies (KST-SEC-012, KST-SEC-015) are STALE rows whose binding obligation is a PPI clause.
- KYC STALE rows use amendments that insert text (amd-kyc-2025-06 4(i) adds the low-risk proviso to 38; amd-kyc-2025-08 4(v) inserts the special-needs sentence into the V-CIP procedure), so the pre-amendment wording can be read directly from the corpus. A 56(h) row was dropped: that amendment rewrites the paragraph, and the old text is not in the corpus.
- The ground truth requires each `(doc_id, clause_path)` to match exactly one chunk, not just exist. Retrieval scoring in Phase 7 can then join on it without false matches from Annex chunks that reuse paragraph numbers.
- GAP rows name the document a reader would expect to cover the obligation (`policy_doc`), which is silent on it. Three GAP rows have a near miss: a related control that must not be credited.
- Stale documents show it in their metadata (old "last reviewed" date, overdue next review). The DPSC-anchored ones also name DPSC under "Regulatory basis".
- No new dependency: the overlap check uses the standard library plus pyyaml.

**Open decisions for Mohammad**
1. **Resolved in Phase 6:** KYC obligations are assessed as of 2025-10-01 (row-level `as_of`); md-kyc-2016 is repealed 2025-11-28. Original note: `assessment_as_of: 2026-10-01` and the KYC assumption. The manifest marks md-kyc-2016 repealed, and its successors are not in the corpus. The ground truth treats it, as amended to 2025-08-14, as the operative KYC text, citing md-ppi-2021 para 6.1. Phase 10's as-of filter will drop every KYC chunk while the manifest says `repealed`.
2. ~~md-dpsc-2021 repeal date~~ **Resolved in Phase 6:** `effective_to` is 2026-07-31 (2025-11-28 is the KYC replacement date and had been applied to the wrong document).
3. Chunker mislabels (Phase 2 fix, now worked around in the ground truth):
   - md-kyc-2016 paragraphs 38(c), (d) and (e) come out as `38(b)(ii)(…)`;
   - Annex chunks reuse paragraph numbers (`11` matches 18 chunks, `8` 3, `12` 2);
   - amendment sub-items are merged into one chunk (amd-kyc-2025-06 4(ii)/(iii) inside `4(i)`; amd-kyc-2025-08 4(iii)–(vi) inside `4`).

   Every obligation was moved to an unambiguous chunk, but the Phase 6 gold set will hit the same problem.
4. Whether Phase 3's parse step should extend `build_chunks.py` to Markdown or use a separate script. Either way, the synthetic banner should be stripped at parse time.

**Deferred**
- `CLAUDE.md` says the venv is `venv`; it is `.venv`.
- The company name has not been checked against RBI's list of authorised PPI issuers.

**Verify**
```
.\.venv\Scripts\python.exe scripts\check_policy_overlap.py
```
Expected: `ok` for all 18 policies, keyword-overlap `median plain 0.30, median idf 0.25`, `0 flagged run(s) across 18 policies`, exit code 0.

**Suggested commit breakdown**
1. `add internal_dir setting to config`: `regassess/config.py`
2. `add planted-gap ground truth for synthetic policy corpus`: `data/internal/gap_ground_truth.yaml`
3. `add synthetic product, agent, escrow and dormancy policies`: `data/internal/KST-PRD-001.md`, `KST-AGT-001.md`, `KST-FIN-003.md`, `KST-OPS-021.md`
4. `add synthetic fraud, security and audit policies`: `data/internal/KST-RSK-002.md`, `KST-SEC-001.md`, `KST-SEC-007.md`, `KST-SEC-012.md`, `KST-SEC-015.md`, `KST-AUD-001.md`
5. `add synthetic kyc, aml, records and vendor policies`: `data/internal/KST-AML-001.md`, `KST-AML-004.md`, `KST-AML-006.md`, `KST-AML-009.md`, `KST-DAT-002.md`, `KST-VND-001.md`
6. `add synthetic grievance and customer liability policies`: `data/internal/KST-CX-001.md`, `KST-CX-004.md`
7. `add policy wording overlap check`: `scripts/check_policy_overlap.py`
8. `document synthetic policy corpus`: `README.md`, `docs/PROGRESS.md`

Nothing untracked needs flagging: `data/internal/` holds only committed design files, and no raw or processed data was touched.

## Phase 4 — Vector store and naive retrieval (complete)

**Built**
- `docker-compose.yml`: `pgvector/pgvector:0.8.0-pg16` (pinned), host port 5433, credentials from `.env`, named volume `pgdata`, healthcheck.
- `regassess/db.py`: `get_connection()` (creates the `vector` extension, registers the type) and `init_schema()`. Table `chunks` with real columns: `chunk_id` (PK), `corpus` (CHECK regulation/internal), `doc_id`, `clause_path`, `text`, `embedding vector(384)`, `status`, `effective_from`, `effective_to`, `document_type`, `amends`, `page_start`, `page_end`. Plain btree indexes on `corpus` and `doc_id`; **no vector index** (exact scan over 693 rows).
- `regassess/chunking_internal.py`: one chunk per `##` section of `data/internal/KST-*.md`. `doc_id` = filename stem; `clause_path` = `<title> > <section heading>`; `effective_from` read from the header table; `status` = `in_force`, `document_type` = `policy`. Synthetic banner and header table are not in chunk text. Oversize sections would split at numbered paragraphs; none exceeds the 2000-char cap (max 1444), so none did.
- `regassess/embeddings.py`: bge-small-en-v1.5, CPU, batched, normalized. The bge query instruction prefix is added to queries only.
- `scripts/build_index.py`: loads both corpora, embeds, and replaces the table with TRUNCATE + insert in one transaction (a failed run keeps the old index). Run twice; counts identical.
- `scripts/query.py`: `query "<text>" [--k 10]`; prints rank, cosine score, corpus, doc_id, clause_path, first 150 chars.

**Files added**: `docker-compose.yml`, `.env.example`, `regassess/db.py`, `regassess/chunking_internal.py`, `regassess/embeddings.py`, `scripts/build_index.py`, `scripts/query.py`
**Files changed**: `regassess/config.py` (Postgres settings, `database_url`), `requirements.txt`, `docs/PROGRESS.md`. `.env` (gitignored) gained `POSTGRES_*` keys.

**Measured**: 693 chunks loaded: regulation 568 (7 docs), internal 125 (18 docs). The regulation count equals the sum of the seven Phase 2 files.

**Observations from the three required queries (read by me, not scored; no metrics yet)**
- "KYC requirements for opening a small PPI account": top hits are PPI 15.4, 9.1(i), 9.1(ii), KYC 24. Plausible. No internal policy in the top 10.
- "two factor authentication for wallet transactions": 7 of the top 10 are DPSC (md-dpsc-2021), which the Phase 3 notes say does not bind a non-bank PPI issuer, and which the manifest marks repealed. PPI 15.3(b) is rank 2. The acronym table (`clause_path` null) is rank 6. No internal security policy appears. This is the stale/inapplicable-document problem that Phase 10 targets.
- "how long must transaction records be retained": rank 1 is internal KST-DAT-002 (2. Principles), not the retention schedule table (rank 5). KYC 46 and 46(b) are in the top 4. Mixed corpora in one ranking means a regulation question gets internal answers; later phases will query the corpora separately.

**Decisions**
- New dependency `sentence-transformers`: runs bge-small locally.
- New dependency `psycopg[binary]`: Postgres driver (v3).
- New dependency `pgvector`: registers the `vector` type with psycopg.
- New dependency `numpy`: embeddings are numpy arrays that the pgvector adapter takes; imported directly.
- `postgres_password` has no default in `config.py`: a missing one fails at import.
- Regulation chunks embed their raw text only (no heading prepended); that is Phase 10's contextual retrieval.
- `status`/`effective_*` are loaded exactly as the chunk files carry them; the Phase 2 Withdrawn-stamp manifest discrepancy is untouched and nothing filters on it yet.
- Both corpora share one table and one ranking in `query.py`; there is no corpus filter, by design for the baseline.

**Deferred**
- ANN index (HNSW) until row count or latency justifies it.
- Hugging Face unauthenticated-download warning and Windows symlink warning on model load; harmless.

**Verify**
```
docker compose up -d
.\.venv\Scripts\python.exe scriptsuild_index.py
.\.venv\Scripts\python.exe scripts\query.py "how long must transaction records be retained" --k 10
```
Expected: `internal 125 chunks 18 documents`, `regulation 568 chunks 7 documents`, then ten ranked rows.

**Suggested commit breakdown**
1. `add embedding, postgres and numpy dependencies`: `requirements.txt`
2. `add postgres settings to config`: `regassess/config.py`, `.env.example`
3. `add pgvector docker compose service`: `docker-compose.yml`
4. `add chunks table schema and connection helper`: `regassess/db.py`
5. `add heading-based chunker for internal policies`: `regassess/chunking_internal.py`
6. `add local bge-small embedding wrapper`: `regassess/embeddings.py`
7. `add rebuildable index loader`: `scripts/build_index.py`
8. `add naive top-k query cli`: `scripts/query.py`
9. `update progress for phase 4`: `docs/PROGRESS.md`

`config.py` was already staged before this session with the Phase 3 `internal_dir` change (together with `scripts/check_policy_overlap.py`); check `git diff --cached` so commit 2 does not swallow it. Nothing untracked needs flagging: `.env` is gitignored, and no `data/raw/`, `data/processed/` or model cache is involved.

## Phase 5 — Naive end-to-end baseline (built, NOT verified end to end)

**Status:** code is written, but I have no real register yet. Every Gemini call returned 503 (high demand) on the day of the run, so `assess_gaps` has never completed and no `data/output/*_register.json` exists. Phase 5 is not complete until `run_assessment.py` succeeds once.

**Built**
- `regassess/retrieval.py`: `search(query, k, corpus=None)`, the Phase 4 SQL with an optional corpus filter. `scripts/query.py` now calls it; output diffed byte-identical before and after.
- `regassess/llm.py`: `generate_structured(prompt, schema)`. Pydantic class as Gemini `response_schema`, temperature 0, re-validated on our side. Backoff on 429/503: 18 attempts, waits double from 4 s to a 120 s cap, about 26 min in total (1564 s plus jitter), each wait printed. Other errors raise at once. Successful, validated responses are cached on disk in `data/cache/`, keyed on SHA-256 of (model, prompt); a rerun skips finished calls. A corrupt or schema-mismatched entry counts as a miss.
- `regassess/graph.py`: LangGraph, four nodes in a line: `extract_obligations` -> `retrieve_controls` -> `assess_gaps` -> `write_register`. `TOP_K_CONTROLS = 5`.
- `scripts/run_assessment.py`: takes a chunked `doc_id` or a text-file path, writes `data/output/<name>_register.json`, prints the table.

**Files added**: `regassess/retrieval.py`, `regassess/llm.py`, `regassess/graph.py`, `scripts/run_assessment.py`
**Files changed**: `regassess/config.py` (`output_dir`, `cache_dir`), `scripts/query.py`, `requirements.txt`, `docs/PROGRESS.md`

**Measured so far**
- `query.py` refactor: identical output.
- `retrieve_controls` on a stub obligation returns 5 internal-only chunks (KST-FIN-003, KST-PRD-001, KST-SEC-001, KST-CX-004, KST-AGT-001).
- `write_register` and the table printer ran on a hand-written stub assessment (labelled STUB, not saved). Control doc ids and chunk ids come through.
- Run 2 of the real graph: `extract_obligations` succeeded after 4 retries and returned **1 obligation** from `amd-ppi-2024-02`; `assess_gaps` then exhausted its 5 retries on 503.
- Model probe: `gemini-3.8-flash`, `gemini-3.5-flash` and `gemini-flash-latest` returned 503. `gemini-3.7-flash` returned 503 in a full run. `gemini-2.5-flash` and `-flash-lite` return 404 (not available to new users).
- No quality numbers exist. Metrics are TBD until Phase 7.

**Decisions**
- New dependency `langgraph`: the agent graph framework.
- New dependency `pydantic`: model classes used as Gemini schemas. Already installed as a sub-dependency of pydantic-settings; listed because the code imports it directly.
- Obligation IDs (`OBL-01`...) are assigned by code, not the LLM, so they are stable and cannot collide.
- One `assess_gaps` Gemini call per obligation, so each verdict is attributable to one set of controls. Cost is N calls.
- `write_register` is pure code: traceability fields are copied from state, never generated by a model.
- The retrieval query is the raw obligation text. No rewriting.

**Deferred / risks**
- `amd-*` chunks are nearly flat, so amendment `clause_path` values will be coarse.
- Unresolved Phase 0 item: `gemini_model` default (`gemini-3.8-flash`) has still never completed a call.
- `data/cache/` holds raw model responses and is gitignored.
- `data/output/` is not gitignored. Decide whether registers are committed; the final baseline register may be worth committing as the demo artifact.

**Verify (once Gemini is reachable)**
```
.\.venv\Scripts\python.exe scripts\run_assessment.py amd-ppi-2024-02
```
Expected: `data/output/amd-ppi-2024-02_register.json` and a table with a clause path and control doc ids on every row.

**Suggested commit breakdown**
1. `add langgraph and pydantic dependencies`: `requirements.txt`
2. `add output and cache directory settings to config`: `regassess/config.py`
3. `add corpus-filtered retrieval function`: `regassess/retrieval.py`
4. `use shared search function in query cli`: `scripts/query.py`
5. `add gemini structured-output wrapper with backoff and disk cache`: `regassess/llm.py`
6. `add four-node baseline langgraph`: `regassess/graph.py`
7. `add run_assessment cli`: `scripts/run_assessment.py`
8. `update progress for phase 5`: `docs/PROGRESS.md`

Nothing untracked to flag except `.env.example` (carried over from Phase 4).

## Phase 6 — Gold set (complete)

**Built**
- `data/eval/gold_set.yaml`: 100 retrieval items. **LLM-drafted and human-reviewed**: Claude read each gold chunk and drafted the query and labels; Mohammad reviewed and revised. Not independently hand-labelled. Fields: `item_id`, `source`, `corpus`, `category`, `query`, `gold_chunk_ids`, `gold_clause_paths`, `as_of` (regulation items only); optional `stale_chunk_ids`, `note`. The file header defines each field, category and date.
- `scripts/validate_gold_set.py`: checks the gold set against Postgres and `gap_ground_truth.yaml`, 12 checks: every item has a gold chunk; every gold id exists; every gold clause path matches the stored `clause_path`; no duplicate `(query, as_of)`; unique item ids; corpus matches; every stale id exists; regulation items have `as_of` and internal items do not; every gold chunk is in force on `as_of`; no stale chunk is in force on `as_of`; obligation items use their obligation's date; every regulation document's status agrees with its `effective_to` on today's date. Exit 1 on any failure.
- `docs/EVALUATION.md`: recall and MRR definitions, the document-date conventions and the in-force rule, so Phase 7 and Phase 10 implement them rather than re-deciding.
- Corpus: `md-kyc-2016-v2018` (KYC Master Direction as updated 2018-07-12) added to the manifest, hash pinned, chunked and indexed. Manifest dates revised (see Decisions).
- `gap_ground_truth.yaml`: the 11 md-kyc-2016 obligations carry `as_of: "2025-10-01"`; the meta assumption now says KYC is repealed 2025-11-28.

**Files added**: `data/eval/gold_set.yaml`, `scripts/validate_gold_set.py`, `docs/EVALUATION.md`
**Files changed**: `data/corpus_manifest.yaml`, `data/internal/gap_ground_truth.yaml`, `data/internal/KST-CX-001.md`, `README.md`, `docs/PROJECT_BRIEF.md`, `docs/PHASE_PLAN.md`, `docs/phase1_corpus.md`, `docs/PROGRESS.md`
**Generated, not committed**: `data/processed/md-kyc-2016-v2018.jsonl`, the other seven `.jsonl` files (regenerated with the new manifest dates; chunk counts and ids unchanged), `_build_report.json`, Docling cache; Postgres reloaded.

**Gold set composition (measured by the validator)**

| category | items |
|---|---|
| straightforward | 30 |
| paraphrased | 23 |
| version_sensitive | 23 |
| repealed_document | 24 |
| **total** | **100** (regulation 74, internal 26) |

By source: 57 from the 31 ground-truth obligations (31 regulation queries, plus 26 internal queries for the non-GAP rows; GAP rows have no control to retrieve), 13 amendment-chain, 18 DPSC, 4 KYC-repeal, 8 KYC version pairs. 12 items have two gold chunks; 110 distinct chunks referenced.

**Query wording (measured, scratch script, not committed)**: the median share of a query's content words that appear in its gold text is 0.30 (paraphrased 0.22, straightforward 0.32, version_sensitive 0.36, repealed_document 0.25). No query shares more than 3 consecutive words with its gold text. Measured before the G-054 gold cut.

**md-kyc-2016-v2018 chunking (measured, `build_chunks.py`)**: 63 pages, 141 chunks, 6 null `clause_path` (4%), 21 unplaced numbers, 30 same-page merges. Worse than the current KYC file. Paragraphs 15 and 18-23 come out null or merged into neighbours (`v2018:0047` holds 17 plus deleted 18-22 and small accounts 23). Its paragraph numbers differ from the current text from 52 on (FATF is 55, CKYCR 57). **Checked against the PDF** (pages rendered with pypdfium2 and read, plus pdfium's own text layer, independent of Docling): page 31 prints "55. Jurisdictions that do not or insufficiently apply the FATF Recommendations", its own Explanation cites "Section 55 a & b", and 54 is "Freezing of Assets under Section 51A". The difference is genuine renumbering between versions, not a parser shift. Pages 18 (17), 25 (38) and 26 (40) match the other three v2018 gold labels. No gold clause path was wrong. No Withdrawn stamp; the watermark census reports "DISAGREES" for it because the check assumes anything not `in_force` is stamped, which does not hold for a historical consolidated version.

**Index (measured, `build_index.py`)**: regulation 709 chunks / 8 documents, internal 125 / 18.

**Policy overlap re-check (measured, `check_policy_overlap.py`)**: adding the v2018 text raised one flagged run, "if the customer is not", in KST-CX-001 4.4 (generic wording that matches a 2018 sentence). Reworded, as Phase 3 did for every flagged run. Now 0 flagged runs, medians unchanged (plain 0.30, IDF 0.25), exit 0.

**Decisions**
- Recall@k = fraction of an item's gold chunks found in the top k. MRR = 1 / rank of the first gold chunk (0 if none in top k). Both averaged over items with equal weight. In `docs/EVALUATION.md`.
- Gold rule: a chunk is gold if its text answers the query. Amendment circulars repeat inserted text verbatim, so amended-KYC items list both the Master Direction chunk and the amendment chunk.
- Date conventions (in `docs/EVALUATION.md`): `issue_date` is the instrument's original date; `effective_from`/`effective_to` are the validity window of this text. `md-kyc-2016` `effective_from` 2016-02-25 → 2025-08-14 (its `amended_up_to`), `effective_to` null → 2025-11-28 (repeal; status stays `repealed`). `md-dpsc-2021` `effective_to` 2025-11-28 → 2026-07-31. Amendments: `effective_from` = `issue_date`, `effective_to` = the parent's `effective_to`; the three KYC amendments end 2025-11-28, `amd-ppi-2024-02` is open. In force on a date: `effective_from <= as_of < effective_to`, null end open.
- `as_of` dates: 2019-01-01 (v2018 in force), 2024-06-01 (DPSC in force), 2025-10-01 (md-kyc-2016 as amended to 2025-08-14 in force: after the last amendment, before the repeal), 2026-10-01 (assessment date). The 10 amended-KYC items use 2025-10-01, not 2025-06-01: seven ask about text inserted on 2025-06-12 or 2025-08-14.
- Every regulation item has an `as_of`; obligation items take their obligation's date from `gap_ground_truth.yaml`. 31 items were dated in the last pass: 19 PPI items at 2026-10-01 (18 obligation items and G-069), and 12 at 2025-10-01 (the 9 KYC obligation items and G-058, G-061, G-070). Internal items have none: the policy corpus is not versioned. The validator enforces that both files agree.
- Version pairs: 4 KYC paragraphs (38 periodic updation, 40 first transaction for non-face-to-face accounts, 17 OTP e-KYC account limit, 54/55 FATF jurisdictions), each asked with identical wording at 2019-01-01 and 2025-10-01. Each item's `stale_chunk_ids` is the other version. Duplicates are checked on `(query, as_of)`.
- KYC-repeal items (as_of 2026-10-01) use questions an in-force PPI clause answers, with md-kyc-2016 chunks as stale. A pure KYC question on that date has no correct chunk in the corpus; that needs an abstention item type, deferred to Phase 13.
- G-054 gold cut to `KST-SEC-012:0003` (contact register) alone, by Mohammad's decision.
- G-064 gold `amd-kyc-2024-11:0005` kept: it is the amended text of 56(h) (end) and 56(j) (full), not boilerplate. Its `clause_path` is null.
- No new dependency.

**Decisions taken at the end of the phase (were open, now resolved by Mohammad)**
1. **Internal policies are assessed in their current version.** Found: with KYC obligations assessed on 2025-10-01, OBL-12 (COVERED) and OBL-27 (GAP, near miss) name KST-AML-009, effective 2026-01-10, and OBL-15 (COVERED) names KST-DAT-002, effective 2026-04-01 (measured by comparing each policy's header `effective_from` with its obligation's date; the other 28 rows were fine). Resolved by rule, not by backdating: the assessment asks whether the company is compliant now with the rule that applied at the stated date, so regulation is versioned and controls are not. Recorded in `gap_ground_truth.yaml` meta and `docs/EVALUATION.md`. No policy file changed.
2. **The three KYC amendments are `status: repealed`.** Their `effective_to` (2025-11-28) is past, so `in_force` contradicted it. This also closes the Phase 2 Withdrawn-stamp discrepancy: the watermark census now reports `ok` for all three (measured, `build_chunks.py`). The only remaining "DISAGREES" is `md-kyc-2016-v2018`, expected because a historical consolidated version carries no stamp. New invariant, checked by `validate_gold_set.py` for every regulation document in Postgres: on today's date, `in_force` exactly when `effective_to` is null or in the future. Run before re-indexing, it failed on exactly the three amendments; after, it passes.
3. **`docs/phase1_corpus.md`** now has the v2018 entry (section 2a) and a note listing the Phase 6 date and status changes, with the manifest named as the authority. README notes the KST-CX-001 §4.4 rewording.

**Document dates now (measured, Postgres)**

| doc_id | status | issue_date | effective_from | effective_to |
|---|---|---|---|---|
| md-kyc-2016-v2018 | superseded | 2016-02-25 | 2018-07-12 | 2019-05-29 |
| md-dpsc-2021 | repealed | 2021-02-18 | 2021-08-18 | 2026-07-31 |
| md-ppi-2021 | in_force | 2021-08-27 | 2021-08-27 | null |
| amd-ppi-2024-02 | in_force | 2024-02-23 | 2024-02-23 | null |
| amd-kyc-2024-11 | repealed | 2024-11-06 | 2024-11-06 | 2025-11-28 |
| amd-kyc-2025-06 | repealed | 2025-06-12 | 2025-06-12 | 2025-11-28 |
| amd-kyc-2025-08 | repealed | 2025-08-14 | 2025-08-14 | 2025-11-28 |
| md-kyc-2016 | repealed | 2016-02-25 | 2025-08-14 | 2025-11-28 |

In force under the window rule: 2019-01-01 md-kyc-2016-v2018 only; 2024-06-01 md-ppi-2021, amd-ppi-2024-02, md-dpsc-2021 (no KYC version in the corpus covers that date); 2025-10-01 all except v2018; 2026-10-01 md-ppi-2021 and amd-ppi-2024-02.

**Verify**
```
.\.venv\Scripts\python.exe scripts\validate_gold_set.py
```
Expected: 12 `[PASS]` lines, `100 items, 110 distinct chunks referenced, 110 found in Postgres`, `all checks passed`, exit 0. Requires `docker compose up -d` and a current index (`build_index.py`). Two negative tests against deliberately broken copies failed on exactly the planted faults with exit 1. The first planted a missing id, a wrong path, a duplicate query, an empty gold list and a wrong corpus. The second moved a 2019 item to 2025 and a KYC item to 2026, gave an internal item a date, and removed a regulation item's date.

Also: `.\.venv\Scripts\python.exe scripts\check_policy_overlap.py` → `0 flagged run(s) across 18 policies`, exit 0.

**Suggested commit breakdown**
1. `fix repeal and validity dates for kyc and dpsc master directions`: `data/corpus_manifest.yaml` (md-kyc-2016 and md-dpsc-2021 date lines; `git add -p`)
2. `date and repeal the kyc amendment circulars`: `data/corpus_manifest.yaml` (the four `amd-*` date lines and the three `status: repealed` lines; `git add -p`)
3. `add 2018 kyc master direction to corpus manifest`: `data/corpus_manifest.yaml` (the new entry)
4. `assess kyc obligations as of their operative date`: `data/internal/gap_ground_truth.yaml`
5. `reword grievance policy phrase shared with 2018 kyc text`: `data/internal/KST-CX-001.md`
6. `add retrieval gold set`: `data/eval/gold_set.yaml`
7. `add gold set validator with date and status checks`: `scripts/validate_gold_set.py`
8. `document retrieval scoring and document date rules`: `docs/EVALUATION.md`
9. `add 2018 kyc version to corpus record`: `docs/phase1_corpus.md`
10. `describe gold set and policy rewording in docs`: `README.md`, `docs/PROJECT_BRIEF.md`, `docs/PHASE_PLAN.md`
11. `update progress for phase 6`: `docs/PROGRESS.md`

Flags: `.gitignore` (modified) and `.env.example` (untracked) predate this phase. `data/raw/md-kyc-2016-v2018.pdf` and `data/processed/` are gitignored; do not commit them.
