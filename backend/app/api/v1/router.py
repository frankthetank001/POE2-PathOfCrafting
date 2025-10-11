from fastapi import APIRouter

from app.api.v1 import ai_assistant, builds, crafting, items

api_router = APIRouter()

api_router.include_router(items.router)
api_router.include_router(builds.router)
api_router.include_router(crafting.router)
api_router.include_router(ai_assistant.router)