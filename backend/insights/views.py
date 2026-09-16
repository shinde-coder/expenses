from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from catalogs.lookups import master_codes, master_default
from core.mixins import FamilyContextMixin
from core.responses import error_response, success_response
from insights.analytics import build_analytics
from insights.dates import parse_month
from insights.intelligence import build_calendar, build_structured_insights, month_forecast
from insights.reports import allowed_report_types, build_report, render_report
from insights.services import build_dashboard, build_summary
from insights.settlement import build_settlement


class DashboardView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_dashboard(self.get_family(), label))


class SummaryView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_summary(self.get_family(), label))


class AnalyticsView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = build_analytics(
                self.get_family(),
                period=request.query_params.get("period")
                or master_default("analytics_period", "monthly"),
                month=request.query_params.get("month"),
                date_from=request.query_params.get("from"),
                date_to=request.query_params.get("to"),
            )
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(data)


class SettlementView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_settlement(self.get_family(), label))


class InsightsView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_structured_insights(self.get_family(), label))


class CalendarView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_calendar(self.get_family(), label))


class ForecastView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(month_forecast(self.get_family(), label))


class ReportPreviewView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, report_type):
        if report_type not in allowed_report_types():
            return error_response("Unknown report type.", status=404)
        try:
            report = build_report(
                self.get_family(), report_type, request.query_params.get("month")
            )
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(report)


class ReportExportView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, report_type):
        if report_type not in allowed_report_types():
            return error_response("Unknown report type.", status=404)
        fmt = (request.data.get("format") or master_default("export_format", "csv") or "csv").lower()
        allowed_formats = set(master_codes("export_format"))
        if not allowed_formats:
            allowed_formats = {"csv", "xlsx", "pdf"}
        if fmt not in allowed_formats:
            return error_response("Unknown export format.", status=400)
        try:
            report = build_report(
                self.get_family(), report_type, request.data.get("month")
            )
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return render_report(report, fmt)
