from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.item import ItemParseRequest, ItemParseResponse
from app.services.item_parser import ItemParser

logger = get_logger(__name__)

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/parse", response_model=ItemParseResponse)
async def parse_item(request: ItemParseRequest) -> ItemParseResponse:
    try:
        logger.info("Parsing item text")
        parser = ItemParser()
        parsed_item = parser.parse(request.item_text)

        return ItemParseResponse(success=True, item=parsed_item)

    except ValueError as e:
        logger.warning(f"Item parsing failed: {e}")
        return ItemParseResponse(success=False, error=str(e))

    except Exception as e:
        logger.error(f"Unexpected error parsing item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")