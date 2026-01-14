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

    def __init__(self, tracker):
        self.tracker = tracker
        self.styles = getSampleStyleSheet()

    def generate(self, output_path: str):
        data = self.tracker.breakdown()

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
            "<b>AI Training Cost Report</b>",
            self.styles["Title"]
        ))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(
            f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles["Normal"]
        ))
        elements.append(Spacer(1, 20))

        table_data = [
            ["Category", "Cost (USD)"],
            ["Hardware Cost", f"${data['hardware_cost']}"],
            ["Storage Cost", f"${data['storage_cost']}"],
            ["Token Cost", f"${data['token_cost']}"],
            ["Energy Cost", f"${data['energy_cost']} ({data['energy_source']})"],
            ["", ""],
            ["TOTAL COST", f"${data['total_cost']}"],
        ]

        table = Table(table_data, colWidths=[250, 150])
        table.setStyle(TableStyle([
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

        elements.append(table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph(
            "<b>Notes</b>",
            self.styles["Heading2"]
        ))
        elements.append(Paragraph(
            "• Energy costs are excluded as they are provided externally.<br/>"
            "• Hardware costs include GPU and CPU usage.",
            self.styles["Normal"]
        ))

        doc.build(elements)
