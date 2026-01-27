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
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie


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

    @staticmethod
    def _build_cost_pie_chart(breakdown: dict):
        drawing = Drawing(450, 220)

        pie = Pie()
        pie.x = 65
        pie.y = 15
        pie.width = 150
        pie.height = 150

        pie.data = [
            breakdown["hardware_cost"],
            breakdown["storage_cost"],
            breakdown["token_cost"],
            breakdown["energy_cost"],
        ]

        pie.labels = ["Hardware", "Storage", "Token", "Energy"]

        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor("#1f77b4")
        pie.slices[1].fillColor = colors.HexColor("#ff7f0e")
        pie.slices[2].fillColor = colors.HexColor("#2ca02c")
        pie.slices[3].fillColor = colors.HexColor("#d62728")

        pie.slices.labelRadius = 1.2
        pie.slices.popout = 2

        drawing.add(pie)

        drawing.add(String(
            225, 190,
            "Cost Distribution",
            fontSize=14,
            fillColor=colors.darkblue
        ))

        return drawing

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

        primary_driver = max(
            [
                ("Hardware Cost", breakdown["hardware_cost"]),
                ("Storage Cost", breakdown["storage_cost"]),
                ("Token Cost", breakdown["token_cost"]),
                ("Energy Cost", breakdown["energy_cost"]),
            ],
            key=lambda x: x[1]
        )[0]

        best_scenario = None
        if scenarios:
            best_scenario = min(scenarios, key=lambda s: s["total_cost"])["scenario"]

        summary_text = (
            f"This report provides a comprehensive analysis of the training cost structure. "
            f"The total training cost is <b>{breakdown['total_cost']} {currency}</b>. "
            f"The primary cost driver identified in this analysis is <b>{primary_driver}</b>."
        )

        if best_scenario:
            summary_text += (
                f" Among the evaluated scenarios, "
                f"<b>{best_scenario}</b> represents the most cost-efficient option."
            )

        elements.append(Paragraph("Executive Summary", self.styles["SectionTitle"]))
        elements.append(Paragraph(summary_text, self.styles["Note"]))
        elements.append(Spacer(1, 25))

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

        elements.append(Spacer(1, 25))
        elements.append(Paragraph("Cost Distribution Overview", self.styles["SectionTitle"]))
        elements.append(self._build_cost_pie_chart(breakdown))

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
