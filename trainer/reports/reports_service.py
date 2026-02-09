from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ReportsService(ABC):


    @abstractmethod
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
        currency: str,
        gpu_model: Optional[str] = None,
        site: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def calculate_scenario_cost(
        self,
        base_config: Dict[str, Any],
        scenario_overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_pdf_report(
        self,
        report_data: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        pass

    @abstractmethod
    def generate_excel_report(
        self,
        report_data: Dict[str, Any],
        output_path: str
    ) -> str:
        pass

    @abstractmethod
    def get_report_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_report_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        pass
