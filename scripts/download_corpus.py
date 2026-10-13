"""Download the RBI corpus listed in data/corpus_manifest.yaml and pin each file by SHA-256.

Run: .\\.venv\\Scripts\\python.exe scripts\\download_corpus.py
"""

import hashlib
import sys
from pathlib import Path

import requests
import yaml

# Lets `python scripts\download_corpus.py` import regassess without installing it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.config import settings  # noqa: E402

MANIFEST_PATH = settings.data_dir / "corpus_manifest.yaml"
# Some government servers reject the default python-requests User-Agent.
HEADERS = {"User-Agent": "regassess-corpus-downloader/0.1 (research project)"}
TIMEOUT_S = 60


class NotAPdfError(Exception):
    pass


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        # Chunked read: PDFs can be large and we never need them fully in memory.
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_manifest(manifest: dict) -> None:
    # sort_keys=False keeps the field order we wrote by hand. PyYAML drops comments,
    # so the manifest holds data only; explanations live in docs/.
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True, width=200)


def looks_like_pdf(path: Path) -> bool:
    """Every real PDF starts with %PDF-. Servers behind bot protection return an HTML
    challenge page with HTTP 200, which would otherwise be saved and hashed as if valid."""
    with path.open("rb") as f:
        return f.read(5) == b"%PDF-"


def fetch(url: str, dest: Path) -> None:
    """Stream the URL to dest via a .part file, so a crash never leaves a half-written PDF."""
    part = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, headers=HEADERS, timeout=TIMEOUT_S, stream=True) as r:
            r.raise_for_status()
            with part.open("wb") as f:
                for block in r.iter_content(chunk_size=1 << 20):
                    f.write(block)
        if not looks_like_pdf(part):
            raise NotAPdfError("response is not a PDF (likely a bot-protection page)")
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)


def process(doc: dict) -> str:
    """Handle one document. Returns 'downloaded', 'skipped' or 'failed'. Mutates doc['sha256']."""
    doc_id = doc["doc_id"]
    dest = settings.raw_dir / f"{doc_id}.pdf"
    pinned = doc.get("sha256") or ""

    if dest.exists():
        if not looks_like_pdf(dest):
            print(f"[FAIL] {doc_id}: {dest.name} exists but is not a PDF. Delete it and re-run.")
            return "failed"
        actual = sha256_of(dest)
        if not pinned:
            # File on disk but never recorded (e.g. an interrupted earlier run): adopt it.
            doc["sha256"] = actual
            print(f"[SKIP] {doc_id}: file present, hash recorded in manifest")
            return "skipped"
        if actual == pinned:
            print(f"[SKIP] {doc_id}: already downloaded, hash matches")
            return "skipped"
        # Never overwrite: a differing hash means the evidence base changed under us.
        print(
            f"[FAIL] {doc_id}: SOURCE CHANGED. {dest.name} hashes to {actual[:12]}..., "
            f"manifest pins {pinned[:12]}.... Not overwriting. Investigate before proceeding."
        )
        return "failed"

    url = (doc.get("url") or "").strip()
    if not url:
        print(f"[FAIL] {doc_id}: url field is empty in the manifest. Fill it in and re-run.")
        return "failed"

    try:
        fetch(url, dest)
    except requests.HTTPError as e:
        print(f"[FAIL] {doc_id}: HTTP {e.response.status_code} from {url}")
        return "failed"
    except NotAPdfError as e:
        print(f"[FAIL] {doc_id}: {e}. Download it in a browser and save as data/raw/{doc_id}.pdf")
        return "failed"
    except requests.RequestException as e:
        print(f"[FAIL] {doc_id}: network error ({type(e).__name__}: {e})")
        return "failed"

    doc["sha256"] = sha256_of(dest)
    size_kb = dest.stat().st_size / 1024
    print(f"[ OK ] {doc_id}: downloaded {size_kb:.0f} KB, sha256 {doc['sha256'][:12]}...")
    return "downloaded"


def main() -> int:
    manifest = load_manifest()
    counts = {"downloaded": 0, "skipped": 0, "failed": 0}

    try:
        for doc in manifest["documents"]:
            try:
                result = process(doc)
            except Exception as e:  # one document must never abort the rest
                print(f"[FAIL] {doc.get('doc_id', '?')}: unexpected error ({type(e).__name__}: {e})")
                result = "failed"
            counts[result] += 1
    finally:
        # Persist hashes of whatever succeeded, even if something blew up mid-loop.
        save_manifest(manifest)

    print(
        f"\nSummary: {counts['downloaded']} downloaded, "
        f"{counts['skipped']} skipped, {counts['failed']} failed"
    )
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
