from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from app.models import AdminUser, SavedCraft, CraftStatus, get_db
from app.schemas.saved_craft import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminUserResponse,
    CraftListItem,
    CraftListResponse,
    CraftSubmission,
    CraftUpdate,
    SavedCraftResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


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


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> AdminLoginResponse:
    """Authenticate admin user and return JWT token."""
    admin = db.query(AdminUser).filter(AdminUser.username == request.username).first()

    if admin is None or not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(days=settings.access_token_expire_days),
    )

    logger.info(f"Admin login successful: {admin.username}")

    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_days * 24 * 60 * 60,
    )


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_user(
    admin: AdminUser = Depends(get_current_admin),
) -> AdminUserResponse:
    """Get current admin user info."""
    return AdminUserResponse(
        id=admin.id,
        username=admin.username,
        created_at=admin.created_at,
        last_login=admin.last_login,
    )


@router.get("/crafts", response_model=CraftListResponse)
async def list_all_crafts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> CraftListResponse:
    """List all crafts (including pending) - admin only."""
    query = db.query(SavedCraft)

    if status:
        query = query.filter(SavedCraft.status == status)

    # Get total count
    total = query.count()

    # Pending first, then by created_at
    crafts = (
        query.order_by(
            SavedCraft.status.desc(),  # pending comes after approved alphabetically, so desc
            SavedCraft.created_at.desc(),
        )
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


@router.get("/crafts/{craft_id}", response_model=SavedCraftResponse)
async def get_craft_admin(
    craft_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SavedCraftResponse:
    """Get a craft by ID (admin can see any status)."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

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


@router.post("/crafts/{craft_id}/approve")
async def approve_craft(
    craft_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Approve a pending craft submission."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    craft.status = CraftStatus.APPROVED.value
    craft.reviewed_at = datetime.utcnow()
    db.commit()

    logger.info(f"Craft approved: {craft.short_id} by {admin.username}")

    return {"message": "Craft approved", "short_id": craft.short_id}


@router.post("/crafts/{craft_id}/reject")
async def reject_craft(
    craft_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Reject a pending craft submission."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    craft.status = CraftStatus.REJECTED.value
    craft.reviewed_at = datetime.utcnow()
    db.commit()

    logger.info(f"Craft rejected: {craft.short_id} by {admin.username}")

    return {"message": "Craft rejected"}


@router.post("/crafts/{craft_id}/feature")
async def toggle_featured(
    craft_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Toggle featured status of a craft."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    craft.is_featured = not craft.is_featured
    db.commit()

    logger.info(f"Craft featured toggled: {craft.short_id} -> {craft.is_featured}")

    return {"message": "Featured status updated", "is_featured": craft.is_featured}


@router.post("/crafts", status_code=201)
async def create_official_craft(
    submission: CraftSubmission,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Create an official/curated craft (admin only)."""
    craft = SavedCraft(
        name=submission.name,
        description=submission.description,
        submitter_name=admin.username,
        initial_item=submission.initial_item.model_dump(),
        final_item=submission.final_item.model_dump(),
        history=submission.history,
        item_history=[item.model_dump() for item in submission.item_history],
        action_history=[action.model_dump() if action else None for action in submission.action_history],
        currency_spent=submission.currency_spent,
        currency_spent_history=submission.currency_spent_history,
        status=CraftStatus.APPROVED.value,
        is_official=True,
    )

    db.add(craft)
    db.commit()
    db.refresh(craft)

    logger.info(f"Official craft created: {craft.short_id} by {admin.username}")

    return {
        "short_id": craft.short_id,
        "message": "Official craft created",
    }


@router.patch("/crafts/{craft_id}")
async def update_craft(
    craft_id: int,
    update: CraftUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update craft metadata (admin only)."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    if update.name is not None:
        craft.name = update.name
    if update.description is not None:
        craft.description = update.description
    if update.is_featured is not None:
        craft.is_featured = update.is_featured
    if update.is_official is not None:
        craft.is_official = update.is_official

    db.commit()

    logger.info(f"Craft updated: {craft.short_id} by {admin.username}")

    return {"message": "Craft updated"}


@router.delete("/crafts/{craft_id}")
async def delete_craft(
    craft_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a craft (admin only)."""
    craft = db.query(SavedCraft).filter(SavedCraft.id == craft_id).first()

    if craft is None:
        raise HTTPException(status_code=404, detail="Craft not found")

    short_id = craft.short_id
    db.delete(craft)
    db.commit()

    logger.info(f"Craft deleted: {short_id} by {admin.username}")

    return {"message": "Craft deleted"}
