from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from trainer.reports.intelligence.scenario_intelligence_utils import (
    find_best_scenario,
    generate_scenario_comment,
    calculate_cost_difference
)
from trainer.reports.intelligence.scenario_intelligence import ScenarioIntelligenceEngine

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
            name="TableText",
            fontSize=9,
            leading=12,
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

        values = [
            breakdown["hardware_cost"],
            breakdown["storage_cost"],
            breakdown["token_cost"],
            breakdown["energy_cost"],
        ]

        total = sum(values)

        if total == 0:
            drawing.add(String(
                120, 110,
                "No cost data available for distribution chart",
                fontSize=12,
                fillColor=colors.grey
            ))
            return drawing

        pie = Pie()
        pie.x = 65
        pie.y = 15
        pie.width = 150
        pie.height = 150
        pie.data = values
        pie.labels = ["Hardware", "Storage", "Token", "Energy"]

        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor("#1f77b4")
        pie.slices[1].fillColor = colors.HexColor("#ff7f0e")
        pie.slices[2].fillColor = colors.HexColor("#2ca02c")
        pie.slices[3].fillColor = colors.HexColor("#d62728")

        pie.slices.labelRadius = 1.2

        for i in range(len(values)):
            pie.slices[i].popout = 2

        drawing.add(pie)

        drawing.add(String(
            225, 190,
            "Cost Distribution",
            fontSize=14,
            fillColor=colors.darkblue
        ))

        return drawing

    @staticmethod
    def _build_cost_bar_chart(breakdown: dict):
        drawing = Drawing(450, 220)

        values = [
            breakdown["hardware_cost"],
            breakdown["storage_cost"],
            breakdown["token_cost"],
            breakdown["energy_cost"],
        ]

        labels = ["Hardware", "Storage", "Token", "Energy"]
        colors_list = [
            colors.HexColor("#1f77b4"),
            colors.HexColor("#ff7f0e"),
            colors.HexColor("#2ca02c"),
            colors.HexColor("#d62728")
        ]

        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        bar_chart = VerticalBarChart()
        bar_chart.x = 50
        bar_chart.y = 30
        bar_chart.width = 350
        bar_chart.height = 150
        bar_chart.data = [values]
        bar_chart.categoryAxis.categoryNames = labels
        bar_chart.valueAxis.valueMin = 0
        bar_chart.valueAxis.valueMax = max_val * 1.2
        bar_chart.valueAxis.valueStep = max_val / 5 if max_val > 0 else 1
        bar_chart.bars[0].fillColor = colors.HexColor("#1f3a8a")
        bar_chart.bars[0].strokeColor = None
        bar_chart.bars[0].strokeWidth = 0

        drawing.add(bar_chart)

        drawing.add(String(
            200, 200,
            "Cost Breakdown by Category",
            fontSize=14,
            fillColor=colors.darkblue
        ))

        return drawing

    @staticmethod
    def _build_waterfall_chart(breakdown: dict, scenarios: list = None):
        drawing = Drawing(500, 280)

        categories = ["Hardware", "Storage", "Token", "Energy", "Total"]
        values = [
            breakdown["hardware_cost"],
            breakdown["storage_cost"],
            breakdown["token_cost"],
            breakdown["energy_cost"],
            breakdown["total_cost"]
        ]

        if scenarios:
            best_scenario = find_best_scenario(scenarios)
            categories.append(f"Best: {best_scenario['scenario'][:15]}")
            values.append(best_scenario["total_cost"])

        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        bar_width = 50
        gap = 15
        x_start = 50
        y_base = 50
        scale = 200 / max_val

        bar_colors = [
            colors.HexColor("#1f77b4"),
            colors.HexColor("#ff7f0e"),
            colors.HexColor("#2ca02c"),
            colors.HexColor("#d62728"),
            colors.HexColor("#1f3a8a"),
            colors.HexColor("#166534"),
        ]

        for i, (cat, val) in enumerate(zip(categories, values)):
            x = x_start + i * (bar_width + gap)
            bar_height = val * scale

            rect = Rect(x, y_base, bar_width, bar_height)
            rect.fillColor = bar_colors[i] if i < len(bar_colors) else colors.grey
            rect.strokeColor = None
            drawing.add(rect)

            drawing.add(String(
                x + bar_width / 2,
                y_base + bar_height + 5,
                f"{val:.0f}",
                fontSize=8,
                textAnchor="middle",
                fillColor=colors.black
            ))

            label = cat if len(cat) <= 10 else cat[:8] + ".."
            drawing.add(String(
                x + bar_width / 2,
                y_base - 15,
                label,
                fontSize=8,
                textAnchor="middle",
                fillColor=colors.darkblue
            ))

        drawing.add(String(
            250, 270,
            "Cost Accumulation & Scenario Comparison",
            fontSize=14,
            textAnchor="middle",
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

        intelligence = ScenarioIntelligenceEngine.analyze(breakdown, scenarios)

        summary_text = (
            f"This report provides a comprehensive analysis of the training cost structure. "
            f"The total training cost is <b>{breakdown['total_cost']} {currency}</b>. "
            f"{intelligence['summary']}"
        )

        elements.append(Paragraph("Executive Summary", self.styles["SectionTitle"]))
        elements.append(Paragraph(summary_text, self.styles["Note"]))
        elements.append(Spacer(1, 25))

        base_table_data = [
            ["Category", f"Cost ({currency})"],
            ["Hardware Cost", f"{breakdown['hardware_cost']} {currency}"],
            ["Storage Cost", f"{breakdown['storage_cost']} {currency}"],
            ["Token Cost", f"{breakdown['token_cost']} {currency}"],
            ["Energy Cost", f"{breakdown['energy_cost']} {currency} ({breakdown['energy_source']})"],
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

        elements.append(Spacer(1, 25))
        elements.append(Paragraph("Cost Breakdown by Category", self.styles["SectionTitle"]))
        elements.append(self._build_cost_bar_chart(breakdown))

        elements.append(Spacer(1, 25))
        elements.append(Paragraph("Cost Accumulation & Scenario Comparison", self.styles["SectionTitle"]))
        elements.append(self._build_waterfall_chart(breakdown, scenarios))

        if scenarios:
            elements.append(Spacer(1, 25))
            elements.append(Paragraph("Scenario Cost Comparison", self.styles["SectionTitle"]))

            scenario_table_data = [
                [
                    Paragraph("Scenario", self.styles["TableText"]),
                    Paragraph(f"Total Cost ({currency})", self.styles["TableText"]),
                    Paragraph("Comparison to Baseline", self.styles["TableText"])
                ]
            ]

            for s in scenarios:
                diff_info = calculate_cost_difference(breakdown["total_cost"], s["total_cost"])
                comment = generate_scenario_comment(s["scenario"], diff_info)

                scenario_table_data.append([
                    Paragraph(s["scenario"], self.styles["TableText"]),
                    Paragraph(f"{s['total_cost']} {currency}", self.styles["TableText"]),
                    Paragraph(comment, self.styles["TableText"])
                ])

            elements.append(self._styled_table(
                scenario_table_data,
                col_widths=[200, 100, 100],
                header_bg=colors.HexColor("#166534")
            ))

            if intelligence["scenario_insights"]:
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("Scenario Insights", self.styles["SectionTitle"]))
                for insight in intelligence["scenario_insights"]:
                    elements.append(Paragraph(f"• {insight}", self.styles["Note"]))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Notes", self.styles["SectionTitle"]))
        elements.append(Paragraph(
            "• Energy costs are provided externally and may vary by region.<br/>"
            "• Scenario calculations are derived from the same base training configuration.",
            self.styles["Note"]
        ))

        doc.build(elements)
