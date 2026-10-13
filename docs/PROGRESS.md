# Progress

Updated at the end of every phase. A new session reads this first.

## Current state

Phase 0 complete (config default now `gemini-3.8-flash`; `--live` unconfirmed after a 503). Phase 1 code complete but blocked on manual PDF downloads (see Phase 1). Next: Phase 2, after Phase 1's exit criterion is met.

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

## Phase 1 — RBI corpus acquisition (code complete; corpus NOT yet on disk)

**Status: blocked on two manual steps by Mohammad, below. Phase 1's exit criterion ("PDFs on disk, manifest complete") is not met yet.**

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

## Next: Phase 2 — Parsing and structure-aware chunking
