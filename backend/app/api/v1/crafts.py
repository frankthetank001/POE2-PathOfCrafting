from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import SavedCraft, CraftStatus, get_db
from app.schemas.saved_craft import (
    CraftSubmission,
    SavedCraftResponse,
    CraftListItem,
    CraftListResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/crafts", tags=["crafts"])


def craft_to_list_item(craft: SavedCraft) -> CraftListItem:
    """Convert a SavedCraft model to a CraftListItem response."""
    final_item = craft.final_item or {}
    currency_spent = craft.currency_spent or {}
    history = craft.history or []

    return CraftListItem(
        short_id=craft.short_id,
        name=craft.name,
        description=craft.description,
        submitter_name=craft.submitter_name,
        base_name=final_item.get("base_name", "Unknown"),
        base_category=final_item.get("base_category", "Unknown"),
        total_currency_spent=sum(currency_spent.values()),
        step_count=len(history),
        status=craft.status,
        is_official=craft.is_official,
        is_featured=craft.is_featured,
        view_count=craft.view_count,
        import_count=craft.import_count,
        created_at=craft.created_at,
    )


@router.get("", response_model=CraftListResponse)
async def list_crafts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    base_category: Optional[str] = Query(default=None),
    featured_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> CraftListResponse:
    """List approved public crafts with pagination and filtering."""
    query = db.query(SavedCraft).filter(SavedCraft.status == CraftStatus.APPROVED.value)

    if featured_only:
        query = query.filter(SavedCraft.is_featured == True)

    if search:
        query = query.filter(SavedCraft.name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    crafts = (
        query.order_by(SavedCraft.is_featured.desc(), SavedCraft.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CraftListResponse(
        items=[craft_to_list_item(craft) for craft in crafts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/featured", response_model=CraftListResponse)
async def list_featured_crafts(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> CraftListResponse:
    """Get featured/official crafts for homepage display."""
    crafts = (
        db.query(SavedCraft)
        .filter(SavedCraft.status == CraftStatus.APPROVED.value)
        .filter((SavedCraft.is_featured == True) | (SavedCraft.is_official == True))
        .order_by(SavedCraft.is_official.desc(), SavedCraft.is_featured.desc(), SavedCraft.import_count.desc())
        .limit(limit)
        .all()
    )

    return CraftListResponse(
        items=[craft_to_list_item(craft) for craft in crafts],
        total=len(crafts),
        page=1,
        page_size=limit,
    )


@router.get("/{short_id}", response_model=SavedCraftResponse)
async def get_craft(
    short_id: str,
    db: Session = Depends(get_db),
) -> SavedCraftResponse:
    """Get a single craft by its short ID."""
    craft = db.query(SavedCraft).filter(SavedCraft.short_id == short_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    # Only show approved crafts publicly
    if craft.status != CraftStatus.APPROVED.value:
        raise HTTPException(status_code=404, detail="Craft not found")

    # Increment view count
    craft.view_count += 1
    db.commit()

    return SavedCraftResponse(
        short_id=craft.short_id,
        name=craft.name,
        description=craft.description,
        submitter_name=craft.submitter_name,
        initial_item=craft.initial_item,
        final_item=craft.final_item,
        history=craft.history,
        item_history=craft.item_history,
        action_history=craft.action_history,
        currency_spent=craft.currency_spent,
        currency_spent_history=craft.currency_spent_history,
        status=craft.status,
        is_official=craft.is_official,
        is_featured=craft.is_featured,
        view_count=craft.view_count,
        import_count=craft.import_count,
        created_at=craft.created_at,
        reviewed_at=craft.reviewed_at,
    )


@router.post("/submit", status_code=201)
async def submit_craft(
    submission: CraftSubmission,
    db: Session = Depends(get_db),
) -> dict:
    """Submit a craft for admin review."""
    logger.info(f"New craft submission: {submission.name}")

    craft = SavedCraft(
        name=submission.name,
        description=submission.description,
        submitter_name=submission.submitter_name,
        initial_item=submission.initial_item.model_dump(),
        final_item=submission.final_item.model_dump(),
        history=submission.history,
        item_history=[item.model_dump() for item in submission.item_history],
        action_history=[action.model_dump() if action else None for action in submission.action_history],
        currency_spent=submission.currency_spent,
        currency_spent_history=submission.currency_spent_history,
        status=CraftStatus.PENDING.value,
    )

    db.add(craft)
    db.commit()
    db.refresh(craft)

    logger.info(f"Craft submitted with short_id: {craft.short_id}")

    return {
        "short_id": craft.short_id,
        "message": "Craft submitted for review",
    }


@router.post("/{short_id}/import")
async def record_import(
    short_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Record that a craft was imported into the simulator."""
    craft = db.query(SavedCraft).filter(SavedCraft.short_id == short_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    craft.import_count += 1
    db.commit()

    return {"message": "Import recorded"}
