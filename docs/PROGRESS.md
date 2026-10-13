# Progress

Updated at the end of every phase. A new session reads this first.

## Current state

Phases 0, 1 and 2 complete. Phase 0: config default is `gemini-3.8-flash`; `--live` unconfirmed after a 503. Phase 1: seven PDFs on disk, hashes pinned. Phase 2: seven chunk files in `data/processed/` (see Phase 2). **Open decision for Mohammad:** three amendments are stamped Withdrawn but the manifest says `in_force` (see Phase 2). Next: Phase 3 (synthetic internal corpus).

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

## Next: Phase 3 — Synthetic internal policy corpus
