"""Loads the popular-builds usage artifact, fetching from GitHub if configured.

Mirrors `app/services/crafting/pob_data_loader.py`: prefer a local cached file, else
fetch from a configured URL and cache it to disk. Keeps the volatile scrape entirely in
the sibling POE2-Builds-Scraper repo; this app only consumes a versioned JSON artifact.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.builds.models import BuildStats

logger = get_logger(__name__)

# Local cache dir: backend/source_data/builds/ (resolved relative to this file's repo root)
_BACKEND_ROOT = Path(__file__).parent.parent.parent.parent  # .../backend
_LOCAL_DIR = _BACKEND_ROOT / settings.builds_artifact_dir


def _local_path(slug: str) -> Path:
    return _LOCAL_DIR / f"latest-{slug}.json"


def _remote_url(slug: str) -> Optional[str]:
    url = settings.builds_artifact_url
    if not url:
        return None
    return url.replace("{slug}", slug)


def load_build_stats(slug: Optional[str] = None) -> Optional[BuildStats]:
    """Return the BuildStats for a league, or None if no artifact is available.

    Order: configured remote URL (cached to disk on success) -> local file. We try the
    remote first when set so a deployed app picks up the daily-refreshed artifact, but a
    fetch failure falls back to whatever is cached locally.
    """
    slug = slug or settings.builds_league_slug
    local = _local_path(slug)
    url = _remote_url(slug)

    data: Optional[dict] = None
    if url:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(data), encoding="utf-8")
            logger.info("builds: fetched artifact for %s from %s", slug, url)
        except Exception as e:
            logger.warning("builds: remote fetch failed (%s); falling back to local cache", e)

    if data is None and local.exists():
        try:
            data = json.loads(local.read_text(encoding="utf-8"))
            logger.info("builds: loaded local artifact %s", local.name)
        except Exception as e:
            logger.error("builds: failed reading local artifact %s: %s", local, e)
            return None

    if data is None:
        logger.warning(
            "builds: no artifact for %s (no remote URL configured and %s missing)", slug, local
        )
        return None

    try:
        return BuildStats.model_validate(data)
    except Exception as e:
        logger.error("builds: artifact for %s failed validation: %s", slug, e)
        return None
