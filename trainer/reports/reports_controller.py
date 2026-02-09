from fastapi import APIRouter, Depends
from datetime import datetime
from pathlib import Path
from fastapi.responses import FileResponse

from auth.authcontroller import get_current_user
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.role import Role
from trainer.reports.create.create import ReportCreate, ReportConfigUpdate
from trainer.reports.create.public import SimpleReportCreate
from trainer.reports.response.response import (
    ReportResponse,
    ReportGenerationResponse,
    ReportConfigResponse,
    ScenarioIntelligenceResponse
)
from trainer.reports.response.public import SimpleReportResponse
from trainer.reports.reports_service_impl import ReportsServiceImpl
from trainer.reports.intelligence.scenario_intelligence import ScenarioIntelligenceEngine
from error.errortypes import ErrorType

router = APIRouter()
service = ReportsServiceImpl("trainer/reports/report_config.json")

def build_breakdown_and_scenarios(report: ReportCreate):
    breakdown = service.calculate_cost_breakdown(
        training_hours=report.training_hours,
        gpu_hour_price=report.gpu_hour_price,
        cpu_hour_price=report.cpu_hour_price,
        dataset_size_gb=report.dataset_size_gb,
        storage_price_per_gb=report.storage_price_per_gb,
        tokens_used=report.tokens_used,
        token_price_per_million=report.token_price_per_million,
        energy_source=report.energy_source,
        currency=report.currency,
        gpu_model=report.gpu_model,
        site=report.site
    )

    base_config = report.dict()
    scenarios = []

    for scenario in report.scenarios or []:
        overrides = {k: v for k, v in scenario.dict().items() if v is not None}
        scenario_result = service.calculate_scenario_cost(base_config, overrides)

        scenarios.append({
            "scenario": scenario.scenario_name,
            "tags": scenario.tags,
            "total_cost": scenario_result["total_cost"],
            "currency": scenario_result.get("currency", report.currency)
        })

    return breakdown, scenarios



@router.post("/calculate", response_model=ReportResponse,
             dependencies=[Depends(require_perm([Role.ADMIN]))])
async def calculate_report(report: ReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown, scenarios = build_breakdown_and_scenarios(report)

        intelligence_data = ScenarioIntelligenceEngine.analyze(breakdown, scenarios)

        return ReportResponse(
            breakdown=breakdown,
            scenarios=scenarios,
            intelligence=ScenarioIntelligenceResponse(**intelligence_data),
            generated_at=datetime.utcnow()
        )
    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid report data provided.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )


@router.post("/generate-pdf",
             dependencies=[Depends(require_perm([Role.ADMIN]))])
async def generate_pdf_report(report: ReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown, scenarios = build_breakdown_and_scenarios(report)

        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)

        file_name = f"training_cost_report_{datetime.utcnow():%Y%m%d_%H%M%S}.pdf"
        output_path = output_dir / file_name

        report_data = {
            "breakdown": breakdown,
            "scenarios": scenarios,
            "title": report.title or "AI Training Cost Report"
        }

        service.generate_pdf_report(report_data, scenarios, str(output_path))

        return FileResponse(output_path, media_type="application/pdf", filename=file_name)

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to generate PDF report.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.post("/generate-excel",
             dependencies=[Depends(require_perm([Role.ADMIN]))])
async def generate_excel_report(report: ReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown, scenarios = build_breakdown_and_scenarios(report)

        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)

        file_name = f"training_cost_report_{datetime.utcnow():%Y%m%d_%H%M%S}.xlsx"
        output_path = output_dir / file_name

        report_data = {
            "breakdown": breakdown,
            "scenarios": scenarios,
            "title": report.title or "AI Training Cost Report",
            "generated_at": datetime.utcnow()
        }

        service.generate_excel_report(report_data, str(output_path))

        return FileResponse(output_path,
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            filename=file_name)

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to generate Excel report.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/config",
    response_model=ReportConfigResponse,
    dependencies=[Depends(require_perm([Role.ADMIN]))]
)
async def get_report_config(current_user=Depends(get_current_user)):
    try:
        config = service.get_report_config()

        return ReportConfigResponse(
            training_hours=config["training"]["training_hours"],
            gpu_hour_price=config["training"]["gpu_hour_price"],
            cpu_hour_price=config["training"]["cpu_hour_price"],
            dataset_size_gb=config["training"]["dataset_size_gb"],
            storage_price_per_gb=config["training"]["storage_price_per_gb"],
            tokens_used=config["training"]["tokens_used"],
            token_price_per_million=config["training"]["token_price_per_million"],
            energy_source=config["training"]["energy_source"],
            currency=config["report"]["currency"],
            title=config["report"]["title"]
        )

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve report configuration.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/config",
    response_model=ReportConfigResponse,
    dependencies=[Depends(require_perm([Role.ADMIN]))]
)
async def update_report_config(updates: ReportConfigUpdate, current_user=Depends(get_current_user)):
    try:
        update_dict = {}

        if updates.training_hours is not None:
            update_dict.setdefault("training", {})["training_hours"] = updates.training_hours
        if updates.gpu_hour_price is not None:
            update_dict.setdefault("training", {})["gpu_hour_price"] = updates.gpu_hour_price
        if updates.cpu_hour_price is not None:
            update_dict.setdefault("training", {})["cpu_hour_price"] = updates.cpu_hour_price
        if updates.dataset_size_gb is not None:
            update_dict.setdefault("training", {})["dataset_size_gb"] = updates.dataset_size_gb
        if updates.storage_price_per_gb is not None:
            update_dict.setdefault("training", {})["storage_price_per_gb"] = updates.storage_price_per_gb
        if updates.tokens_used is not None:
            update_dict.setdefault("training", {})["tokens_used"] = updates.tokens_used
        if updates.token_price_per_million is not None:
            update_dict.setdefault("training", {})["token_price_per_million"] = updates.token_price_per_million
        if updates.energy_source is not None:
            update_dict.setdefault("training", {})["energy_source"] = updates.energy_source
        if updates.currency is not None:
            update_dict.setdefault("report", {})["currency"] = updates.currency
        if updates.title is not None:
            update_dict.setdefault("report", {})["title"] = updates.title

        if not update_dict:
            raise ExpectionHandler(
                message="No valid fields to update.",
                error_type=ErrorType.VALIDATION_ERROR
            )

        updated_config = service.update_report_config(update_dict)

        return ReportConfigResponse(
            training_hours=updated_config["training"]["training_hours"],
            gpu_hour_price=updated_config["training"]["gpu_hour_price"],
            cpu_hour_price=updated_config["training"]["cpu_hour_price"],
            dataset_size_gb=updated_config["training"]["dataset_size_gb"],
            storage_price_per_gb=updated_config["training"]["storage_price_per_gb"],
            tokens_used=updated_config["training"]["tokens_used"],
            token_price_per_million=updated_config["training"]["token_price_per_million"],
            energy_source=updated_config["training"]["energy_source"],
            currency=updated_config["report"]["currency"],
            title=updated_config["report"]["title"]
        )

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to update report configuration.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



def build_simple_breakdown(report: SimpleReportCreate):
    return service.calculate_cost_breakdown(
        training_hours=report.training_hours,
        gpu_hour_price=report.gpu_hour_price,
        cpu_hour_price=report.cpu_hour_price,
        dataset_size_gb=report.dataset_size_gb,
        storage_price_per_gb=report.storage_price_per_gb,
        tokens_used=report.tokens_used,
        token_price_per_million=report.token_price_per_million,
        energy_source=report.energy_source,
        currency=report.currency,
        gpu_model=report.gpu_model,
        site=report.site
    )


@router.post("/public/calculate", response_model=SimpleReportResponse,
             dependencies=[Depends(require_perm([Role.USER]))])
async def calculate_simple_report(report: SimpleReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown = build_simple_breakdown(report)

        return SimpleReportResponse(
            hardware_cost=breakdown["hardware_cost"],
            storage_cost=breakdown["storage_cost"],
            token_cost=breakdown["token_cost"],
            energy_cost=breakdown["energy_cost"],
            energy_source=breakdown["energy_source"],
            currency=breakdown["currency"],
            total_cost=breakdown["total_cost"],
            gpu_model=breakdown.get("gpu_model"),
            site=breakdown.get("site"),
            generated_at=datetime.utcnow()
        )
    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid report data provided.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )


@router.post("/public/generate-pdf",
             dependencies=[Depends(require_perm([Role.USER, Role.DEVELOPER]))])
async def generate_simple_pdf_report(report: SimpleReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown = build_simple_breakdown(report)

        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)

        file_name = f"simple_cost_report_{datetime.utcnow():%Y%m%d_%H%M%S}.pdf"
        output_path = output_dir / file_name

        report_data = {
            "breakdown": breakdown,
            "scenarios": [],
            "title": "Simple AI Training Cost Report"
        }

        service.generate_pdf_report(report_data, [], str(output_path))

        return FileResponse(output_path, media_type="application/pdf", filename=file_name)

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to generate PDF report.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/public/generate-excel",
             dependencies=[Depends(require_perm([Role.USER, Role.DEVELOPER]))])
async def generate_simple_excel_report(report: SimpleReportCreate, current_user=Depends(get_current_user)):
    try:
        breakdown = build_simple_breakdown(report)

        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)

        file_name = f"simple_cost_report_{datetime.utcnow():%Y%m%d_%H%M%S}.xlsx"
        output_path = output_dir / file_name

        report_data = {
            "breakdown": breakdown,
            "scenarios": [],
            "title": "Simple AI Training Cost Report",
            "generated_at": datetime.utcnow()
        }

        service.generate_excel_report(report_data, str(output_path))

        return FileResponse(output_path,
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            filename=file_name)

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to generate Excel report.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/public/config",
    response_model=ReportConfigResponse,
    dependencies=[Depends(require_perm([Role.USER]))]
)
async def get_public_report_config(current_user=Depends(get_current_user)):
    try:
        config = service.get_report_config()

        return ReportConfigResponse(
            training_hours=config["training"]["training_hours"],
            gpu_hour_price=config["training"]["gpu_hour_price"],
            cpu_hour_price=config["training"]["cpu_hour_price"],
            dataset_size_gb=config["training"]["dataset_size_gb"],
            storage_price_per_gb=config["training"]["storage_price_per_gb"],
            tokens_used=config["training"]["tokens_used"],
            token_price_per_million=config["training"]["token_price_per_million"],
            energy_source=config["training"]["energy_source"],
            currency=config["report"]["currency"],
            title=config["report"]["title"]
        )

    except Exception as e:
        raise ExpectionHandler(
            message="Failed to retrieve report configuration.",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
