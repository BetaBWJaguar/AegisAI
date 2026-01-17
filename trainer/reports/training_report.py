from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors


class TrainingCostReportPDF:

    def __init__(self, tracker, report_title: str, scenario_results: list[dict] | None = None):
        self.tracker = tracker
        self.report_title = report_title
        self.scenario_results = scenario_results or []
        self.styles = getSampleStyleSheet()

    def generate(self, output_path: str):
        data = self.tracker.breakdown()
        currency = data["currency"]

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        elements = []

        elements.append(Paragraph(
            f"<b>{self.report_title}</b>",
            self.styles["Title"]
        ))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(
            f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles["Normal"]
        ))
        elements.append(Spacer(1, 20))

        base_table_data = [
            ["Category", f"Cost ({currency})"],
            ["Hardware Cost", f"{data['hardware_cost']} {currency}"],
            ["Storage Cost", f"{data['storage_cost']} {currency}"],
            ["Token Cost", f"{data['token_cost']} {currency}"],
            ["Energy Cost", f"{data['energy_cost']} ({data['energy_source']})"],
            ["", ""],
            ["TOTAL COST", f"{data['total_cost']} {currency}"],
        ]

        base_table = Table(base_table_data, colWidths=[250, 150])
        base_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        elements.append(base_table)


        if self.scenario_results:
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(
                "<b>Scenario Cost Comparison</b>",
                self.styles["Heading2"]
            ))
            elements.append(Spacer(1, 10))

            scenario_table_data = [
                ["Scenario", f"Total Cost ({currency})"]
            ]

            for result in self.scenario_results:
                scenario_table_data.append([
                    result["scenario"],
                    f"{result['total_cost']} {currency}"
                ])

            scenario_table = Table(scenario_table_data, colWidths=[250, 150])
            scenario_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))

            elements.append(scenario_table)


        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "<b>Notes</b>",
            self.styles["Heading2"]
        ))
        elements.append(Paragraph(
            "• Energy costs are excluded as they are provided externally.<br/>"
            "• All scenario calculations are derived from the base training configuration.",
            self.styles["Normal"]
        ))

        doc.build(elements)
