from fastapi import APIRouter

from app.api.v1 import admin, builds, crafting, crafts, items, market

api_router = APIRouter()

api_router.include_router(items.router)
api_router.include_router(crafting.router)
api_router.include_router(market.router)
api_router.include_router(crafts.router)
api_router.include_router(admin.router)
api_router.include_router(builds.router)