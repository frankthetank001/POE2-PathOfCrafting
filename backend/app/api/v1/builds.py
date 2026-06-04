"""
Builds API

Popular-build analysis from the POE2-Builds-Scraper artifact: which item bases and mods
the current meta uses, enriched with this app's craftable mod identifiers (mod_group,
tier family, tier distribution) so the data connects to crafting.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.builds import get_builds_service

logger = get_logger(__name__)

router = APIRouter(prefix="/builds", tags=["builds"])


# ---------------------------------------------------------------------------
# Response schemas (defined in-file, like market.py)
# ---------------------------------------------------------------------------
class BuildsMetaResponse(BaseModel):
    league: str
    league_slug: str
    snapshot_version: str
    scraped_at: str
    sample_size: int
    roster_size: int
    base_count: int
    mod_count: int
    bases_resolved: int
    disclaimer: str


class TrendingBaseResponse(BaseModel):
    base_name: str
    slot: str
    usage_count: int
    usage_pct: float
    rarity_mix: Dict[str, int] = Field(default_factory=dict)
    common_skills: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    resolves_in_app: bool = False


class TrendingModResponse(BaseModel):
    base_name: str
    slot: str
    mod_template: str
    mod_origin: str
    usage_count: int
    usage_pct: float
    resolved: bool
    mod_group: Optional[str] = None
    mod_type: Optional[str] = None
    tier_count: int = 0
    best_tier_seen: Optional[int] = None
    modal_tier: Optional[int] = None
    tier_distribution: Dict[int, int] = Field(default_factory=dict)


class BaseDetailResponse(BaseModel):
    base_name: str
    slot: str
    category: Optional[str] = None
    resolves_in_app: bool = False
    usage_count: int
    usage_pct: float
    rarity_mix: Dict[str, int] = Field(default_factory=dict)
    common_skills: List[str] = Field(default_factory=list)
    mods: List[TrendingModResponse] = Field(default_factory=list)


class TargetMod(BaseModel):
    stat_text: str
    value: float
    tier: int
    mod_type: str
    origin: str
    usage_pct: float


class MarketInfo(BaseModel):
    chaos_floor: Optional[float] = None
    divine: Optional[float] = None
    exalted: Optional[float] = None
    num_listings: Optional[int] = None
    confidence: Optional[str] = None
    trade_url: Optional[str] = None
    error: Optional[str] = None


class BasePricingResponse(BaseModel):
    base_name: str
    resolved_name: Optional[str] = None
    category: Optional[str] = None
    slot: Optional[str] = None
    item_level: Optional[int] = None
    trade_search_url: Optional[str] = None
    target_mods: List[TargetMod] = Field(default_factory=list)
    prefixes: int = 0
    suffixes: int = 0
    craftable: bool = False
    priced: bool = False
    market: Optional[MarketInfo] = None
    verdict: str
    message: Optional[str] = None
    note: Optional[str] = None


_UNAVAILABLE = "Build data is not available. Configure BUILDS_ARTIFACT_URL or add a local artifact."


# ---------------------------------------------------------------------------
# Endpoints  (served at /api/v1/builds/...)
# ---------------------------------------------------------------------------
@router.get("/meta", response_model=BuildsMetaResponse)
async def get_meta() -> BuildsMetaResponse:
    """League + snapshot metadata for the loaded build-stats artifact."""
    try:
        service = await get_builds_service()
        meta = service.get_meta()
        if meta is None:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)
        return BuildsMetaResponse(**meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting builds meta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending-bases", response_model=List[TrendingBaseResponse])
async def trending_bases(
    slot: Optional[str] = Query(None, description="Filter to one equipment slot"),
    limit: int = Query(50, ge=1, le=500),
) -> List[TrendingBaseResponse]:
    """Item bases ranked by how many popular builds use them."""
    try:
        service = await get_builds_service()
        if not service.available:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)
        return [TrendingBaseResponse(**row) for row in service.trending_bases(slot, limit)]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trending bases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending-mods", response_model=List[TrendingModResponse])
async def trending_mods(
    base: Optional[str] = Query(None, description="Filter to one base name"),
    origin: Optional[str] = Query(None, description="explicit | implicit | rune | crafted | ..."),
    limit: int = Query(50, ge=1, le=500),
) -> List[TrendingModResponse]:
    """Mods ranked by usage across popular builds, resolved to mod_group/tier family."""
    try:
        service = await get_builds_service()
        if not service.available:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)
        return [TrendingModResponse(**row) for row in service.trending_mods(base, origin, limit)]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trending mods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/base/{base_name}", response_model=BaseDetailResponse)
async def base_detail(base_name: str) -> BaseDetailResponse:
    """A single base's usage plus its most-used mods (resolved)."""
    try:
        service = await get_builds_service()
        if not service.available:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)
        detail = service.base_detail(base_name)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Base '{base_name}' not in build data")
        return BaseDetailResponse(**detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting base detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{base_name}", response_model=BasePricingResponse)
async def price_base(
    base_name: str,
    max_mods: int = Query(4, ge=1, le=6, description="How many top meta mods to price together"),
) -> BasePricingResponse:
    """Buy-vs-craft signal for a base: prices a Rare with its top meta mods on the live
    market (rate-limited + cached), with craftability. Craft gamble-cost is not modelled;
    listing scarcity is the buy-vs-craft signal."""
    try:
        service = await get_builds_service()
        if not service.available:
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)
        result = await service.price_base(base_name, max_mods=max_mods)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Base '{base_name}' not in build data")
        return BasePricingResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pricing base: {e}")
        raise HTTPException(status_code=500, detail=str(e))
