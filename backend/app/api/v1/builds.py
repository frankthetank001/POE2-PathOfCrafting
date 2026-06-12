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
    trade_url: Optional[str] = None  # base + this specific mod (live listings for it)


class MarketInfo(BaseModel):
    chaos_floor: Optional[float] = None
    divine: Optional[float] = None
    exalted: Optional[float] = None
    num_listings: Optional[int] = None
    confidence: Optional[str] = None
    trade_url: Optional[str] = None
    error: Optional[str] = None


class MagicVariant(BaseModel):
    mods: List[str] = Field(default_factory=list)  # [prefix_text, suffix_text]
    trade_url: str


class BasePricingResponse(BaseModel):
    base_name: str
    resolved_name: Optional[str] = None
    category: Optional[str] = None
    slot: Optional[str] = None
    item_level: Optional[int] = None
    base_ilvl: Optional[int] = None  # the ilvl a base needs to hold the good-roll mods
    trade_search_url: Optional[str] = None
    base_trade_url: Optional[str] = None  # raw white base (rarity=normal) trade search
    magic_trade_url: Optional[str] = None  # magic "partial" (rarity=magic) trade search
    target_mods: List[TargetMod] = Field(default_factory=list)  # the GOOD roll's mods
    magic_mods: List[TargetMod] = Field(default_factory=list)  # the 1 prefix + 1 suffix of the partial
    magic_variants: List["MagicVariant"] = Field(default_factory=list)  # blue-base combos to flip through
    prefixes: int = 0
    suffixes: int = 0
    craftable: bool = False
    is_unique: bool = False  # base only ever runs as a unique - buy-only, no craft ladder
    priced: bool = False
    market: Optional[MarketInfo] = None  # GOOD finished meta Rare (headline)
    market_typical: Optional[MarketInfo] = None  # typical/modal finished Rare
    magic_market: Optional[MarketInfo] = None  # magic partial ("buy a blue base and finish")
    base_market: Optional[MarketInfo] = None  # raw white base at the target ilvl
    verdict: str
    message: Optional[str] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Builds-browser schemas (the per-build sample)
# ---------------------------------------------------------------------------
class BuildsBrowserMeta(BaseModel):
    league: str
    league_slug: str
    snapshot_version: str
    scraped_at: str
    sample_size: int
    roster_size: int
    disclaimer: str


class MainSkillBrief(BaseModel):
    name: str
    dps: int = 0


class BuildSummaryResponse(BaseModel):
    id: str
    character: str
    account: str
    level: int
    base_class: Optional[str] = None
    ascendancy: Optional[str] = None
    main_skill: Optional[MainSkillBrief] = None
    life: int = 0
    energy_shield: int = 0
    ehp: int = 0
    item_count: int = 0
    notable_uniques: List[str] = Field(default_factory=list)
    poeninja_url: str = ""
    has_pob: bool = False


class BuildsListResponse(BaseModel):
    meta: BuildsBrowserMeta
    total: int
    builds: List[BuildSummaryResponse] = Field(default_factory=list)
    ascendancies: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class BuildSkillResponse(BaseModel):
    name: str
    dps: int = 0
    supports: List[str] = Field(default_factory=list)


class ResolvedBuildMod(BaseModel):
    text: str
    origin: str
    values: List[float] = Field(default_factory=list)
    resolved: bool = False
    mod_group: Optional[str] = None
    mod_type: Optional[str] = None
    tier: Optional[int] = None
    mod_id: Optional[str] = None


class ResolvedBuildItem(BaseModel):
    slot: str
    name: Optional[str] = None
    base_type: str
    resolved_base: Optional[str] = None
    category: Optional[str] = None
    resolves_in_app: bool = False
    rarity: str
    item_level: int = 0
    icon: Optional[str] = None
    corrupted: bool = False
    runes: List[str] = Field(default_factory=list)
    mods: List[ResolvedBuildMod] = Field(default_factory=list)


class BuildDetailResponse(BaseModel):
    id: str
    account: str
    character: str
    level: int
    base_class: Optional[str] = None
    ascendancy: Optional[str] = None
    main_skills: List[BuildSkillResponse] = Field(default_factory=list)
    defense: Dict[str, int] = Field(default_factory=dict)
    items: List[ResolvedBuildItem] = Field(default_factory=list)
    poeninja_url: str = ""
    pob_export: Optional[str] = None
    updated_utc: str = ""


_UNAVAILABLE = "Build data is not available. Configure BUILDS_ARTIFACT_URL or add a local artifact."
_BUILDS_UNAVAILABLE = (
    "Builds-browser data is not available. The scraper's builds-<slug>.json sample "
    "has not been published/configured yet."
)


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
    max_mods: int = Query(6, ge=1, le=6, description="How many top meta affixes to price together (3 prefix + 3 suffix)"),
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


# ---------------------------------------------------------------------------
# Builds browser  (served at /api/v1/builds/browser...)
# Declared after the literal/2-segment routes above; the "browser" prefix keeps
# /browser/{build_id} from shadowing /meta, /base/{name}, /price/{name}.
# ---------------------------------------------------------------------------
@router.get("/browser", response_model=BuildsListResponse)
async def list_builds(
    ascendancy: Optional[str] = Query(None, description="Filter to one ascendancy"),
    base_class: Optional[str] = Query(None, description="Filter to one base class"),
    skill: Optional[str] = Query(None, description="Filter to builds whose main skill matches"),
    q: Optional[str] = Query(None, description="Free-text search (character, skill, unique items)"),
    limit: int = Query(60, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> BuildsListResponse:
    """Paginated, filterable list of real builds (summaries) from the scraped sample."""
    try:
        service = await get_builds_service()
        if not service.builds_available:
            raise HTTPException(status_code=503, detail=_BUILDS_UNAVAILABLE)
        meta = service.builds_meta()
        data = service.list_builds(
            ascendancy=ascendancy, base_class=base_class, skill=skill, q=q,
            limit=limit, offset=offset,
        )
        return BuildsListResponse(meta=meta, **data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing builds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browser/{build_id}", response_model=BuildDetailResponse)
async def build_detail(build_id: str) -> BuildDetailResponse:
    """A single build's full loadout with each item's mods resolved to tier/mod_id."""
    try:
        service = await get_builds_service()
        if not service.builds_available:
            raise HTTPException(status_code=503, detail=_BUILDS_UNAVAILABLE)
        detail = service.get_build(build_id)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found")
        return BuildDetailResponse(**detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting build detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
