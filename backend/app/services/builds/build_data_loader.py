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
from app.services.builds.models import BuildsArtifact, BuildStats

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


def _builds_local_path(slug: str) -> Path:
    return _LOCAL_DIR / f"builds-{slug}.json"


def _builds_remote_url(slug: str) -> Optional[str]:
    """URL of the per-build sample (builds-{slug}.json). Uses builds_browser_url if set,
    else derives it from builds_artifact_url by swapping the 'latest-' filename for 'builds-'."""
    url = settings.builds_browser_url or settings.builds_artifact_url.replace(
        "latest-{slug}", "builds-{slug}"
    )
    if not url:
        return None
    return url.replace("{slug}", slug)


def _load_json(url: Optional[str], local: Path, label: str) -> Optional[dict]:
    """Remote-fetch (cached to disk on success) -> local-file fallback. Returns raw dict.

    Try the remote first when configured so a deployed app picks up the daily-refreshed
    artifact, but a fetch failure falls back to whatever is cached locally.
    """
    data: Optional[dict] = None
    if url:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(data), encoding="utf-8")
            logger.info("builds: fetched %s from %s", label, url)
        except Exception as e:
            logger.warning("builds: remote fetch failed for %s (%s); using local cache", label, e)

    if data is None and local.exists():
        try:
            data = json.loads(local.read_text(encoding="utf-8"))
            logger.info("builds: loaded local %s %s", label, local.name)
        except Exception as e:
            logger.error("builds: failed reading local %s %s: %s", label, local, e)
            return None

    if data is None:
        logger.warning("builds: no %s available (no remote URL and %s missing)", label, local)
    return data


def load_build_stats(slug: Optional[str] = None) -> Optional[BuildStats]:
    """Return the aggregate BuildStats for a league, or None if no artifact is available."""
    slug = slug or settings.builds_league_slug
    data = _load_json(_remote_url(slug), _local_path(slug), f"stats artifact ({slug})")
    if data is None:
        return None
    try:
        return BuildStats.model_validate(data)
    except Exception as e:
        logger.error("builds: stats artifact for %s failed validation: %s", slug, e)
        return None


def load_builds_artifact(slug: Optional[str] = None) -> Optional[BuildsArtifact]:
    """Return the per-build sample (builds-<slug>.json), or None if unavailable.

    Independent of the aggregate stats artifact: a deployment may have one without the
    other (older scraper outputs predate the builds sample).
    """
    slug = slug or settings.builds_league_slug
    data = _load_json(_builds_remote_url(slug), _builds_local_path(slug), f"builds sample ({slug})")
    if data is None:
        return None
    try:
        return BuildsArtifact.model_validate(data)
    except Exception as e:
        logger.error("builds: builds sample for %s failed validation: %s", slug, e)
        return None
