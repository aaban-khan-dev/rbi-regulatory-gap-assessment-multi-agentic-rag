# Progress

Updated at the end of every phase. A new session reads this first.

## Current state

Phase 0 complete, with one open item (Gemini model name, below). Next: Phase 1.

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

## Next: Phase 1 — RBI corpus acquisition
