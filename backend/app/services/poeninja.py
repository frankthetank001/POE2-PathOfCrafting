from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PoeNinjaClient:
    def __init__(self) -> None:
        self.base_url = settings.poeninja_base_url
        self.poe2_base_url = "https://poe.ninja/poe2/api/data"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self.client.aclose()

    async def get_index_state(self) -> Dict[str, Any]:
        try:
            url = f"{self.poe2_base_url}/index-state"
            logger.info(f"Fetching index state from poe.ninja: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching index state: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching index state: {e}")
            raise

    async def get_build_index_state(self) -> Dict[str, Any]:
        try:
            url = f"{self.poe2_base_url}/build-index-state"
            logger.info(f"Fetching build index state from poe.ninja: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching build index state: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching build index state: {e}")
            raise

    async def get_builds(
        self,
        league: str = "Standard",
        class_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/getbuilds"
            params: Dict[str, str] = {"league": league}

            if class_filter:
                params["class"] = class_filter

            logger.info(f"Fetching builds from poe.ninja: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("builds", [])

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching builds: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching builds: {e}")
            raise

    async def get_item_overview(
        self,
        league: str,
        item_type: str,
    ) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/itemoverview"
            params = {"league": league, "type": item_type}

            logger.info(f"Fetching items from poe.ninja: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching items: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching items: {e}")
            raise

    async def get_currency_overview(
        self,
        league: str,
        currency_type: str = "Currency",
    ) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/currencyoverview"
            params = {"league": league, "type": currency_type}

            logger.info(f"Fetching currency from poe.ninja: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching currency: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching currency: {e}")
            raise