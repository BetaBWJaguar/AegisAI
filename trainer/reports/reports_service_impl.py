import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, List

from trainer.reports.reports_service import ReportsService
from trainer.reports.training_tracker import TrainingCostTracker, TrainingConfig
from trainer.reports.training_report import TrainingCostReportPDF
from trainer.reports.excel_report import TrainingCostExcelReport
from trainer.reports.report_config import ReportConfigLoader, TrainingConfig as ReportTrainingConfig, ReportConfig
from trainer.reports.trainingvalidation import TrainingConfigValidator
from trainer.reports.intelligence.scenario_intelligence import ScenarioIntelligenceEngine


class ReportsServiceImpl(ReportsService):

    def __init__(self, config_path: str = "trainer/reports/report_config.json"):
        self.config_path = Path(config_path)
        self.config_loader = ReportConfigLoader(self.config_path)
        self._training_config, self._report_config = self.config_loader.load()

    def calculate_cost_breakdown(
        self,
        training_hours: float,
        gpu_hour_price: float,
        cpu_hour_price: float,
        dataset_size_gb: float,
        storage_price_per_gb: float,
        tokens_used: int,
        token_price_per_million: float,
        energy_source: str,
        currency: str
    ) -> Dict[str, Any]:
        config = TrainingConfig(
            training_hours=training_hours,
            gpu_hour_price=gpu_hour_price,
            cpu_hour_price=cpu_hour_price,
            dataset_size_gb=dataset_size_gb,
            storage_price_per_gb=storage_price_per_gb,
            tokens_used=tokens_used,
            token_price_per_million=token_price_per_million,
            energy_source=energy_source
        )

        TrainingConfigValidator.validate(config)
        tracker = TrainingCostTracker(config, currency)
        return tracker.breakdown()

    def calculate_scenario_cost(
        self,
        base_config: Dict[str, Any],
        scenario_overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged_config = {**base_config, **scenario_overrides}

        return self.calculate_cost_breakdown(
            training_hours=merged_config.get("training_hours", 0.0),
            gpu_hour_price=merged_config.get("gpu_hour_price", 0.0),
            cpu_hour_price=merged_config.get("cpu_hour_price", 0.0),
            dataset_size_gb=merged_config.get("dataset_size_gb", 0.0),
            storage_price_per_gb=merged_config.get("storage_price_per_gb", 0.0),
            tokens_used=merged_config.get("tokens_used", 0),
            token_price_per_million=merged_config.get("token_price_per_million", 0.0),
            energy_source=merged_config.get("energy_source", "EXTERNAL"),
            currency=merged_config.get("currency", "USD")
        )

    def generate_pdf_report(
            self,
            report_data: Dict[str, Any],
            scenarios: List[Dict[str, Any]],
            output_path: str
    ) -> str:

        breakdown = report_data["breakdown"]

        intelligence = ScenarioIntelligenceEngine.analyze(breakdown, scenarios)

        template_data = {
            "breakdown": breakdown,
            "scenarios": scenarios,
            "intelligence": intelligence
        }

        context = SimpleNamespace(
            title=report_data.get("title"),
            generated_at=datetime.utcnow()
        )

        pdf_generator = TrainingCostReportPDF(
            template_data=template_data,
            context=context
        )

        pdf_generator.generate(output_path)
        return output_path

    def generate_excel_report(
            self,
            report_data: Dict[str, Any],
            output_path: str
    ) -> str:
        excel_generator = TrainingCostExcelReport(report_data=report_data)
        return excel_generator.generate(output_path)

    def get_report_config(self) -> Dict[str, Any]:
        self._training_config, self._report_config = self.config_loader.load()

        return {
            "training": {
                "training_hours": self._training_config.training_hours,
                "gpu_hour_price": self._training_config.gpu_hour_price,
                "cpu_hour_price": self._training_config.cpu_hour_price,
                "dataset_size_gb": self._training_config.dataset_size_gb,
                "storage_price_per_gb": self._training_config.storage_price_per_gb,
                "tokens_used": self._training_config.tokens_used,
                "token_price_per_million": self._training_config.token_price_per_million,
                "energy_source": self._training_config.energy_source
            },
            "report": {
                "currency": self._report_config.currency,
                "title": self._report_config.title
            }
        }

    def update_report_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "training" in updates:
            training_updates = updates["training"]
            for key, value in training_updates.items():
                if key in data["training"]:
                    data["training"][key] = value

        if "report" in updates:
            report_updates = updates["report"]
            for key, value in report_updates.items():
                if key in data["report"]:
                    data["report"][key] = value

        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self._training_config, self._report_config = self.config_loader.load()
        TrainingConfigValidator.validate(self._training_config)

        return self.get_report_config()
