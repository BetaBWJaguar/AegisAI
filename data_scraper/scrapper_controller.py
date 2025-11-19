import json

from fastapi import APIRouter, Query, Depends
from typing import List, Optional

from config_loader import ConfigLoader
from data_scraper.scrapper_dataset_integrator import ScrapperDatasetIntegrator
from data_scraper.scrapper_serviceimpl import ScrapperServiceImpl
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType
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
        subreddits: List[str] = Query(["all"]),
        auto_dataset: bool = Query(False),
        dataset_id: Optional[str] = Query(None),
        label: Optional[str] = Query(None),
        entry_type: Optional[str] = Query("MANUAL"),
        template_id: Optional[str] = Query(None),
        values: Optional[str] = Query(None),
):
    try:
        data = service.scrape_reddit(query=query, limit=limit, subreddits=subreddits)

        if auto_dataset:
            if not dataset_id:
                raise ExpectionHandler(
                    message="dataset_id is required when auto_dataset=True",
                    error_type=ErrorType.VALIDATION_ERROR
                )

            data = data[:limit]

            integrator = ScrapperDatasetIntegrator("config.json")

            from dataset_builder.entrytype import EntryType
            selected_type = EntryType(entry_type.upper())

            parsed_values = None
            if values:
                try:
                    parsed_values = json.loads(values)
                except Exception:
                    raise ExpectionHandler(
                        message="Invalid JSON in 'values'",
                        error_type=ErrorType.VALIDATION_ERROR
                    )

            final_label = label or f"REDDIT_{query.upper().replace(' ', '_')}"

            added_entries = integrator.integrate(
                dataset_id=dataset_id,
                scrapped_data=data,
                entry_type=selected_type,
                label=final_label,
                template_id=template_id,
                values=parsed_values
            )

            return {
                "status": "success",
                "auto_dataset": True,
                "dataset_id": dataset_id,
                "entry_type": selected_type,
                "label_used": final_label,
                "added_count": len(added_entries),
                "entries": added_entries
            }

        return {
            "status": "success",
            "count": len(data),
            "data": data
        }

    except ExpectionHandler:
        raise
    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid parameters provided for Reddit scraping.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
