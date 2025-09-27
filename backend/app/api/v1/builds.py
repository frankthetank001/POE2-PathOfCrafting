from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.logging import get_logger
from app.schemas.build import Build, BuildsResponse, LeaguesResponse
from app.services.poeninja import PoeNinjaClient

logger = get_logger(__name__)

router = APIRouter(prefix="/builds", tags=["builds"])


async def get_poeninja_client() -> PoeNinjaClient:
    client = PoeNinjaClient()
    try:
        yield client
    finally:
        await client.close()


@router.get("/leagues", response_model=LeaguesResponse)
async def get_leagues(
    client: PoeNinjaClient = Depends(get_poeninja_client),
) -> LeaguesResponse:
    try:
        logger.info("Fetching available leagues")
        data = await client.get_index_state()
        return LeaguesResponse(**data)
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_build_stats(
    client: PoeNinjaClient = Depends(get_poeninja_client),
):
    try:
        logger.info("Fetching build statistics")
        data = await client.get_build_index_state()
        return data
    except Exception as e:
        logger.error(f"Error fetching build stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=BuildsResponse)
async def get_builds(
    league: str = Query(default="Standard", description="League name"),
    class_filter: str = Query(default=None, alias="class", description="Filter by class"),
    limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    client: PoeNinjaClient = Depends(get_poeninja_client),
) -> BuildsResponse:
    try:
        logger.info(f"Fetching builds for league: {league}, class: {class_filter}")

        builds_data = await client.get_builds(league=league, class_filter=class_filter)

        builds: List[Build] = []
        for build_data in builds_data[:limit]:
            try:
                build = Build(**build_data)
                builds.append(build)
            except Exception as e:
                logger.warning(f"Failed to parse build: {e}")
                continue

        return BuildsResponse(builds=builds, total=len(builds), league=league)

    except Exception as e:
        logger.error(f"Error fetching builds: {e}")
        raise HTTPException(status_code=500, detail=str(e))