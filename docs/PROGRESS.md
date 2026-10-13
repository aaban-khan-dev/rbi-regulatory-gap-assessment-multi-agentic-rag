# Progress

Updated at the end of every phase. A new session reads this first.

## Current state

Phases 0, 1 and 2 complete. Phase 0: config default is `gemini-3.8-flash`; `--live` unconfirmed after a 503. Phase 1: seven PDFs on disk, hashes pinned. Phase 2: seven chunk files in `data/processed/` (see Phase 2). **Open decision for Mohammad:** three amendments are stamped Withdrawn but the manifest says `in_force` (see Phase 2). Phase 3 in progress: ground truth and 18 policies written, overlap check passes. **Not yet done:** parsing the policies through the chunking pipeline (Phase 3 exit criterion). Four more open decisions are listed under Phase 3.

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

**Manifest discrepancy (needs your decision; manifest NOT changed)**: `amd-kyc-2024-11`, `amd-kyc-2025-06` and `amd-kyc-2025-08` are `status: in_force` in the manifest but their PDFs carry the Withdrawn stamp. Everything else agrees (PPI and amd-ppi in force and unstamped; KYC and DPSC repealed and stamped). `status` and `effective_to` drive Phase 10's as-of-date filtering, so this needs resolving before then.

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
1. `assessment_as_of: 2026-10-01` and the KYC assumption. The manifest marks md-kyc-2016 repealed, and its successors are not in the corpus. The ground truth treats it, as amended to 2025-08-14, as the operative KYC text, citing md-ppi-2021 para 6.1. Phase 10's as-of filter will drop every KYC chunk while the manifest says `repealed`.
2. md-dpsc-2021 repeal date: manifest `effective_to: 2025-11-28`; README and `docs/phase1_corpus.md` say 2026-07-31. Doesn't affect Phase 3 (both precede the as-of date); matters for Phase 10.
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
