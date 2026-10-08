"""Verify the Phase 0 environment. Run: .\\.venv\\Scripts\\python.exe scripts\\verify_setup.py [--live]"""

import argparse
import sys
from pathlib import Path

# Lets `python scripts\verify_setup.py` import regassess without installing it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def check_python():
    v = sys.version_info
    return (v.major, v.minor) == (3, 11), f"{v.major}.{v.minor}.{v.micro}"


def check_torch():
    import torch

    return torch.__version__.endswith("+cpu"), torch.__version__


def check_config():
    # Imported here so a missing .env or key becomes a FAIL line, not a crash.
    from regassess.config import settings  # noqa: F401

    return True, "settings loaded"


def check_api_key():
    from regassess.config import settings

    is_set = bool(settings.gemini_api_key.strip())
    return is_set, "set" if is_set else "not set"  # never print the value


def check_dirs():
    from regassess.config import settings

    dirs = [settings.data_dir, settings.raw_dir, settings.processed_dir]
    missing = [str(d) for d in dirs if not d.is_dir()]
    return not missing, "all present" if not missing else f"missing: {missing}"


def check_live():
    from google import genai
    from google.genai import errors

    from regassess.config import settings

    try:
        with genai.Client(api_key=settings.gemini_api_key) as client:
            response = client.models.generate_content(
                model=settings.gemini_model, contents="Reply with the single word OK."
            )
        return True, f"{settings.gemini_model} replied ({len(response.text or '')} chars)"
    except errors.APIError as e:
        return False, f"API error {e.code}: {e.message}"


def run(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # any failure here is a failed check, not a script crash
        ok, detail = False, f"{type(e).__name__}: {e}"
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="make one Gemini API call")
    args = parser.parse_args()

    checks = [
        ("Python 3.11.x", check_python),
        ("torch is CPU build", check_torch),
        ("regassess.config loads", check_config),
        ("GEMINI_API_KEY present", check_api_key),
        ("data directories exist", check_dirs),
    ]
    if args.live:
        checks.append(("Gemini live call", check_live))

    results = [run(name, fn) for name, fn in checks]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
