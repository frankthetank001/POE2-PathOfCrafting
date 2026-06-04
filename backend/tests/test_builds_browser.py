"""Tests for the builds-browser backend (list/detail + per-item mod resolution).

Loads the real sampled artifact from source_data/builds/builds-runesofaldur.json and the
local pob-data cache (the resolver), so it runs offline.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services.builds.service import BuildsService


@pytest.fixture(scope="module")
def service() -> BuildsService:
    svc = BuildsService()
    asyncio.run(svc.initialize())
    if not svc.builds_available:
        pytest.skip("builds-browser artifact not available locally")
    return svc


def test_meta(service: BuildsService):
    meta = service.builds_meta()
    assert meta is not None
    assert meta["league_slug"] == "runesofaldur"
    assert meta["sample_size"] >= 1
    assert meta["disclaimer"]


def test_list_builds_basic(service: BuildsService):
    data = service.list_builds()
    assert data["total"] == len(service._builds_artifact.builds)
    assert data["builds"], "expected at least one build summary"
    first = data["builds"][0]
    for key in ("id", "character", "level", "ascendancy", "main_skill", "poeninja_url"):
        assert key in first
    # Facets populated for the filter UI.
    assert data["ascendancies"]
    assert data["skills"]
    # Sorted by level desc.
    levels = [b["level"] for b in data["builds"]]
    assert levels == sorted(levels, reverse=True)


def test_list_builds_filters(service: BuildsService):
    asc = service.list_builds()["ascendancies"][0]
    filtered = service.list_builds(ascendancy=asc)
    assert filtered["total"] >= 1
    assert all(b["ascendancy"] == asc for b in filtered["builds"])

    # A nonsense filter yields nothing but still returns stable facets.
    empty = service.list_builds(ascendancy="Not A Real Ascendancy")
    assert empty["total"] == 0
    assert empty["ascendancies"]


def test_list_builds_pagination(service: BuildsService):
    page1 = service.list_builds(limit=5, offset=0)
    page2 = service.list_builds(limit=5, offset=5)
    assert len(page1["builds"]) <= 5
    ids1 = {b["id"] for b in page1["builds"]}
    ids2 = {b["id"] for b in page2["builds"]}
    assert ids1.isdisjoint(ids2)  # no overlap across pages


def test_get_build_resolves_items(service: BuildsService):
    some_id = service._builds_artifact.builds[0].id
    detail = service.get_build(some_id)
    assert detail is not None
    assert detail["id"] == some_id
    assert detail["items"], "expected equipped items"
    assert "pob_export" in detail

    # Every item mod carries the resolution fields; at least one explicit mod resolves to a
    # tier across the whole loadout (the meta uses craftable mods we know).
    resolved_any = False
    for it in detail["items"]:
        for m in it["mods"]:
            assert {"text", "origin", "resolved", "tier", "mod_id"} <= set(m)
            if m["resolved"] and m["tier"] is not None:
                resolved_any = True
    assert resolved_any, "expected at least one mod to resolve to a tier"


def test_get_build_unknown(service: BuildsService):
    assert service.get_build("nope__nobody") is None


def test_api_endpoints():
    """End-to-end through FastAPI. Mounts only the builds router so the test doesn't pull
    in the DB stack (admin/sqlalchemy) just to exercise these endpoints."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1 import builds as builds_api

    test_app = FastAPI()
    test_app.include_router(builds_api.router, prefix="/api/v1")
    client = TestClient(test_app)
    r = client.get("/api/v1/builds/browser", params={"limit": 60})
    if r.status_code == 503:
        pytest.skip("builds-browser artifact not configured in this environment")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["league_slug"] == "runesofaldur"
    assert body["builds"]

    build_id = body["builds"][0]["id"]
    r2 = client.get(f"/api/v1/builds/browser/{build_id}")
    assert r2.status_code == 200, r2.text
    detail = r2.json()
    assert detail["id"] == build_id
    assert detail["items"]

    # Unknown build -> 404.
    r3 = client.get("/api/v1/builds/browser/does__notexist")
    assert r3.status_code == 404
