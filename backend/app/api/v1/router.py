from fastapi import APIRouter

from app.api.v1 import builds, crafting, items, market

api_router = APIRouter()

api_router.include_router(items.router)
api_router.include_router(builds.router)
api_router.include_router(crafting.router)
api_router.include_router(market.router)