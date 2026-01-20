from trainer.reports.templates.core.report_base_template import ReportBaseTemplate


class DefaultPdfTemplate(ReportBaseTemplate):

    template_name = "default"

    def build(self, breakdown, scenarios):
        return {
            "breakdown": breakdown,
            "scenarios": scenarios
        }
