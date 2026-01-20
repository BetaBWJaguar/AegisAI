from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors


class TrainingCostReportPDF:

    def __init__(self, template_data: dict, context):
        self.template_data = template_data
        self.context = context
        self.styles = self._build_styles()

    def _build_styles(self):
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name="ReportTitle",
            fontSize=20,
            leading=24,
            spaceAfter=20,
            alignment=1,
            fontName="Helvetica-Bold"
        ))

        styles.add(ParagraphStyle(
            name="Meta",
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=1
        ))

        styles.add(ParagraphStyle(
            name="SectionTitle",
            fontSize=14,
            leading=18,
            spaceBefore=20,
            spaceAfter=10,
            fontName="Helvetica-Bold",
            textColor=colors.darkblue
        ))

        styles.add(ParagraphStyle(
            name="Note",
            fontSize=10,
            leading=14
        ))

        return styles

    @staticmethod
    def _styled_table(data, col_widths, header_bg, total_row=False):
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]

        if total_row:
            style.extend([
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
            ])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(style))
        return table

    def generate(self, output_path: str):
        breakdown = self.template_data["breakdown"]
        scenarios = self.template_data.get("scenarios", [])
        currency = breakdown["currency"]

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        elements = []

        elements.append(Paragraph(self.context.title, self.styles["ReportTitle"]))
        elements.append(Paragraph(
            f"Generated at {self.context.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles["Meta"]
        ))

        base_table_data = [
            ["Category", f"Cost ({currency})"],
            ["Hardware Cost", f"{breakdown['hardware_cost']} {currency}"],
            ["Storage Cost", f"{breakdown['storage_cost']} {currency}"],
            ["Token Cost", f"{breakdown['token_cost']} {currency}"],
            ["Energy Cost", f"{breakdown['energy_cost']} ({breakdown['energy_source']})"],
            ["", ""],
            ["TOTAL COST", f"{breakdown['total_cost']} {currency}"],
        ]

        elements.append(Paragraph("Training Cost Breakdown", self.styles["SectionTitle"]))
        elements.append(self._styled_table(
            base_table_data,
            col_widths=[260, 140],
            header_bg=colors.HexColor("#1f3a8a"),
            total_row=True
        ))

        if scenarios:
            elements.append(Spacer(1, 25))
            elements.append(Paragraph("Scenario Cost Comparison", self.styles["SectionTitle"]))

            scenario_table_data = [
                ["Scenario", f"Total Cost ({currency})"]
            ]

            for s in scenarios:
                scenario_table_data.append([
                    s["scenario"],
                    f"{s['total_cost']} {currency}"
                ])

            elements.append(self._styled_table(
                scenario_table_data,
                col_widths=[260, 140],
                header_bg=colors.HexColor("#166534")
            ))


        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Notes", self.styles["SectionTitle"]))
        elements.append(Paragraph(
            "• Energy costs are provided externally and may vary by region.<br/>"
            "• Scenario calculations are derived from the same base training configuration.",
            self.styles["Note"]
        ))

        doc.build(elements)
