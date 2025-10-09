from fastapi import APIRouter, Query, Depends
from typing import List

from config_loader import ConfigLoader
from data_scraper.scrapper_serviceimpl import ScrapperServiceImpl
from permcontrol.permissionscontrol import require_perm
from user.role import Role

router = APIRouter()
config = ConfigLoader("config.json").get_scrapper_config("reddit")
service = ScrapperServiceImpl(config)

@router.get(
    "/reddit",
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def scrape_reddit(
        query: str = Query(...),
        limit: int = Query(50),
        subreddits: List[str] = Query(["all"])
):
    data = service.scrape_reddit(query=query, limit=limit, subreddits=subreddits)
    return {
        "status": "success",
        "count": len(data),
        "data": data
    }
