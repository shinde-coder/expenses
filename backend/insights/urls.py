from django.urls import path

from insights.views import (
    AnalyticsView,
    CalendarView,
    DashboardView,
    ForecastView,
    InsightsView,
    ReportExportView,
    ReportPreviewView,
    SettlementView,
    SummaryView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("summaries/", SummaryView.as_view(), name="summaries"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("insights/", InsightsView.as_view(), name="insights"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("forecast/", ForecastView.as_view(), name="forecast"),
    path("settlement/", SettlementView.as_view(), name="settlement"),
    path("reports/<slug:report_type>/", ReportPreviewView.as_view(), name="report-preview"),
    path(
        "reports/<slug:report_type>/export/",
        ReportExportView.as_view(),
        name="report-export",
    ),
]
