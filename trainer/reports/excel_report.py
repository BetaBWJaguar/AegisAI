# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment
)
from openpyxl.chart import BarChart, Reference


class TrainingCostExcelReport:

    def __init__(self, report_data: Dict[str, Any]):
        self.report_data = report_data
        self.breakdown = report_data.get("breakdown", {})
        self.scenarios = report_data.get("scenarios", [])
        self.title = report_data.get("title", "AI Training Cost Report")
        self.generated_at = report_data.get("generated_at", datetime.utcnow())
        self.currency = self.breakdown.get("currency", "USD")

    def generate(self, output_path: str) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        wb.remove(wb.active)

        self._create_summary_sheet(wb)

        self._create_breakdown_sheet(wb)

        if self.scenarios:
            self._create_scenarios_sheet(wb)

        wb.save(str(output_path))
        return str(output_path)

    def _create_summary_sheet(self, wb: Workbook):
        ws = wb.create_sheet("Executive Summary")

        ws.merge_cells("A1:E1")
        title_cell = ws["A1"]
        title_cell.value = self.title
        title_cell.font = Font(size=18, bold=True, color="1F3A8A")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells("A2:E2")
        ws["A2"].value = f"Generated at: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        ws["A2"].font = Font(size=10, color="666666")
        ws["A2"].alignment = Alignment(horizontal="center")

        ws["A4"].value = "Total Training Cost:"
        ws["A4"].font = Font(size=14, bold=True)
        ws["B4"].value = f"{self.breakdown.get('total_cost', 0):.2f} {self.currency}"
        ws["B4"].font = Font(size=18, bold=True, color="166534")

        cost_items = [
            ("Hardware", self.breakdown.get("hardware_cost", 0)),
            ("Storage", self.breakdown.get("storage_cost", 0)),
            ("Token", self.breakdown.get("token_cost", 0)),
            ("Energy", self.breakdown.get("energy_cost", 0)),
        ]
        primary_driver = max(cost_items, key=lambda x: x[1])
        ws["A6"].value = f"Primary Cost Driver: {primary_driver[0]}"
        ws["A6"].font = Font(italic=True)

        if self.scenarios:
            best_scenario = min(self.scenarios, key=lambda s: s.get("total_cost", float("inf")))
            ws["A7"].value = f"Most Cost-Efficient Scenario: {best_scenario.get('scenario', 'N/A')}"
            ws["A7"].font = Font(italic=True)

        ws["A10"].value = "Cost Breakdown"
        ws["A10"].font = Font(size=14, bold=True, color="1F3A8A")

        headers = ["Category", f"Cost ({self.currency})", "Percentage"]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=11, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F3A8A", end_color="1F3A8A", fill_type="solid")

        total = self.breakdown.get("total_cost", 1)
        if total == 0:
            total = 1

        cost_data = [
            ("Hardware", self.breakdown.get("hardware_cost", 0)),
            ("Storage", self.breakdown.get("storage_cost", 0)),
            ("Token", self.breakdown.get("token_cost", 0)),
            ("Energy", self.breakdown.get("energy_cost", 0)),
        ]

        for row, (category, cost) in enumerate(cost_data, start=12):
            ws.cell(row=row, column=1, value=category)
            ws.cell(row=row, column=2, value=f"{cost:.2f}")
            percentage = (cost / total) * 100
            cost_cell = ws.cell(row=row, column=2, value=float(cost))
            cost_cell.number_format = '#,##0.00'
            pct_cell = ws.cell(row=row, column=3, value=percentage / 100)
            pct_cell.number_format = '0.0%'

        self._add_summary_bar_chart(ws, cost_data)

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 15

    def _create_breakdown_sheet(self, wb: Workbook):
        ws = wb.create_sheet("Detailed Breakdown")

        ws["A1"].value = "Detailed Cost Breakdown"
        ws["A1"].font = Font(size=16, bold=True, color="1F3A8A")

        ws["A3"].value = "Training Parameters"
        ws["A3"].font = Font(size=12, bold=True)

        params = [
            ("Training Hours", self.breakdown.get("training_hours", "N/A")),
            ("GPU Hour Price", f"{self.breakdown.get('gpu_hour_price', 0):.4f} {self.currency}"),
            ("CPU Hour Price", f"{self.breakdown.get('cpu_hour_price', 0):.4f} {self.currency}"),
            ("Dataset Size", f"{self.breakdown.get('dataset_size_gb', 0):.2f} GB"),
            ("Storage Price", f"{self.breakdown.get('storage_price_per_gb', 0):.4f} {self.currency}/GB"),
            ("Tokens Used", f"{self.breakdown.get('tokens_used', 0):,}"),
            ("Token Price", f"{self.breakdown.get('token_price_per_million', 0):.4f} {self.currency}/M"),
            ("Energy Source", self.breakdown.get("energy_source", "N/A")),
        ]

        for row, (param, value) in enumerate(params, start=4):
            ws.cell(row=row, column=1, value=param)
            ws.cell(row=row, column=2, value=value)
            ws.cell(row=row, column=1).font = Font(bold=True)

        ws["A14"].value = "Cost Calculations"
        ws["A14"].font = Font(size=12, bold=True)

        calc_headers = ["Component", "Calculation", f"Cost ({self.currency})"]
        for col, header in enumerate(calc_headers, start=1):
            cell = ws.cell(row=15, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F3A8A", end_color="1F3A8A", fill_type="solid")

        training_hours = self.breakdown.get("training_hours", 0)
        gpu_price = self.breakdown.get("gpu_hour_price", 0)
        cpu_price = self.breakdown.get("cpu_hour_price", 0)
        dataset_size = self.breakdown.get("dataset_size_gb", 0)
        storage_price = self.breakdown.get("storage_price_per_gb", 0)
        tokens = self.breakdown.get("tokens_used", 0)
        token_price = self.breakdown.get("token_price_per_million", 0)

        calculations = [
            (
                "Hardware",
                f"{training_hours:.2f}h × ({gpu_price:.4f} + {cpu_price:.4f})",
                self.breakdown.get("hardware_cost", 0)
            ),
            (
                "Storage",
                f"{dataset_size:.2f} GB × {storage_price:.4f}",
                self.breakdown.get("storage_cost", 0)
            ),
            (
                "Token",
                f"{tokens:,} / 1,000,000 × {token_price:.4f}",
                self.breakdown.get("token_cost", 0)
            ),
            (
                "Energy",
                "External / Not Calculated",
                self.breakdown.get("energy_cost", 0)
            ),
        ]

        for row, (component, calc, cost) in enumerate(calculations, start=16):
            ws.cell(row=row, column=1, value=component)
            ws.cell(row=row, column=2, value=calc)
            ws.cell(row=row, column=3, value=f"{cost:.2f}")

        ws.cell(row=20, column=1, value="TOTAL")
        ws.cell(row=20, column=1).font = Font(bold=True, size=12)
        ws.cell(row=20, column=3, value=f"{self.breakdown.get('total_cost', 0):.2f}")
        ws.cell(row=20, column=3).font = Font(bold=True, size=12, color="166534")

        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["C"].width = 20

    def _create_scenarios_sheet(self, wb: Workbook):
        ws = wb.create_sheet("Scenario Comparison")

        ws["A1"].value = "Scenario Cost Comparison"
        ws["A1"].font = Font(size=16, bold=True, color="1F3A8A")

        headers = ["Scenario", "Tags", f"Total Cost ({self.currency})", "vs Baseline"]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="166534", end_color="166534", fill_type="solid")

        baseline_cost = self.breakdown.get("total_cost", 0)

        for row, scenario in enumerate(self.scenarios, start=4):
            ws.cell(row=row, column=1, value=scenario.get("scenario", "N/A"))
            tags = ", ".join(scenario.get("tags", []))
            ws.cell(row=row, column=2, value=tags)
            cost = scenario.get("total_cost", 0)
            ws.cell(row=row, column=3, value=f"{cost:.2f}")

            diff = cost - baseline_cost
            diff_pct = (diff / baseline_cost * 100) if baseline_cost > 0 else 0
            diff_str = f"{diff:+.2f} ({diff_pct:+.1f}%)"
            ws.cell(row=row, column=4, value=diff_str)

            diff_cell = ws.cell(row=row, column=4)
            if diff < 0:
                diff_cell.font = Font(color="166534", bold=True)
            elif diff > 0:
                diff_cell.font = Font(color="DC2626", bold=True)

        self._add_scenario_comparison_chart(ws)

        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 20
        ws.column_dimensions["D"].width = 20

    def _add_summary_bar_chart(self, ws, cost_data):
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = "Cost Distribution"
        chart.y_axis.title = f"Cost ({self.currency})"
        chart.x_axis.title = "Category"

        data = Reference(ws, min_col=2, min_row=11, max_row=11 + len(cost_data), max_col=2)
        cats = Reference(ws, min_col=1, min_row=12, max_row=11 + len(cost_data))

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        ws.add_chart(chart, "E4")

    def _add_scenario_comparison_chart(self, ws):
        chart = BarChart()
        chart.type = "bar"
        chart.style = 11
        chart.title = "Scenario Cost Comparison"
        chart.x_axis.title = f"Cost ({self.currency})"

        data = Reference(ws, min_col=3, min_row=3, max_row=3 + len(self.scenarios), max_col=3)
        cats = Reference(ws, min_col=1, min_row=4, max_row=3 + len(self.scenarios))

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        ws.add_chart(chart, "F4")
