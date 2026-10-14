"""Gemini calls with schema-enforced output, a disk cache, and long-horizon retry."""

import hashlib
import json
import os
import random
import time
from functools import lru_cache
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from regassess.config import settings

T = TypeVar("T", bound=BaseModel)

# 429 = free-tier rate limit, 503 = model overloaded. Anything else (400, 404, auth)
# will not fix itself on retry, so it raises immediately.
RETRYABLE_CODES = {429, 503}

# Free-tier overloads last hours, so we wait long rather than fail fast. Waits double
# from 4s up to a 120s cap: 4+8+16+32+64 = 124s, then 120s each. 18 attempts = 17
# waits, about 26 minutes in total before giving up (plus up to 1s jitter per wait).
MAX_ATTEMPTS = 18
BASE_DELAY_S = 4.0
MAX_DELAY_S = 120.0


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _cache_path(prompt: str):
    # Keyed on (model, prompt). Changing either is a different call, so a different file.
    key = hashlib.sha256(f"{settings.gemini_model}\n{prompt}".encode("utf-8")).hexdigest()
    return settings.cache_dir / f"{key}.json"


def _cache_read(path, schema: type[T]) -> T | None:
    if not path.exists():
        return None
    try:
        return schema.model_validate_json(json.loads(path.read_text(encoding="utf-8"))["response"])
    except (ValueError, KeyError, ValidationError):
        # Corrupt file, or the schema changed since it was written: treat as a miss.
        return None


def _cache_write(path, response_text: str) -> None:
    # Write to a temp file and rename, so a crash mid-write never leaves a half file
    # that looks like a valid entry.
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"model": settings.gemini_model, "response": response_text}),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def generate_structured(prompt: str, schema: type[T]) -> T:
    """Ask Gemini for JSON matching `schema` and return it as a validated instance.

    Passing the Pydantic class as response_schema makes Gemini constrain its output
    to that shape; we then validate again, so a malformed reply raises instead of
    flowing downstream. Only validated successes are cached, so a rerun after a
    failure repeats only the calls that did not finish.
    """
    path = _cache_path(prompt)
    cached = _cache_read(path, schema)
    if cached is not None:
        print("  (cache hit)")
        return cached

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0,
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = _client().models.generate_content(
                model=settings.gemini_model, contents=prompt, config=config
            )
            result = schema.model_validate_json(response.text)
            _cache_write(path, response.text)
            return result
        except errors.APIError as exc:
            if exc.code not in RETRYABLE_CODES or attempt == MAX_ATTEMPTS:
                raise
            # Exponential backoff, capped per wait, with jitter so retries don't align.
            delay = min(BASE_DELAY_S * 2 ** (attempt - 1), MAX_DELAY_S) + random.uniform(0, 1)
            print(
                f"  gemini {exc.code}: attempt {attempt}/{MAX_ATTEMPTS} failed, "
                f"waiting {delay:.0f}s",
                flush=True,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")
