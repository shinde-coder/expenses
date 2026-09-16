import csv
import io
from decimal import Decimal

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from catalogs.lookups import master_codes
from insights.analytics import build_analytics
from insights.services import build_dashboard, build_summary
from insights.settlement import build_settlement


def allowed_report_types():
    try:
        codes = master_codes("report_type")
    except Exception:
        codes = []
    return set(codes) if codes else {
        "monthly",
        "category",
        "member",
        "payment-method",
        "budget",
        "income-vs-expense",
        "savings",
    }


REPORT_TYPES = allowed_report_types()


def build_report(family, report_type, month=None):
    if report_type not in allowed_report_types():
        raise ValueError("Unknown report type.")
    summary = build_summary(family, month)
    dashboard = build_dashboard(family, month)
    analytics = build_analytics(family, period="monthly", month=summary["month"])
    if report_type == "monthly":
        rows = [
            ["Metric", "Value"],
            ["Month", summary["month"]],
            ["Income", summary["total_income"]],
            ["Expenses", summary["total_expenses"]],
            ["Allocated savings", summary["total_savings"]],
            ["Net savings", summary["net_savings"]],
            ["Budget", summary["total_budget"]],
            ["Remaining", summary["remaining_budget"]],
            ["Transactions", summary["transaction_count"]],
        ]
        title = f"Monthly expense report {summary['month']}"
    elif report_type == "category":
        rows = [["Category", "Budget", "Actual", "Difference", "Status"]]
        for item in summary["categories"]:
            rows.append(
                [
                    item["category_name"],
                    item["budget"],
                    item["actual"],
                    item["difference"],
                    item["status"],
                ]
            )
        title = f"Category report {summary['month']}"
    elif report_type == "member":
        rows = [["Member", "Amount", "Count"]]
        for item in summary["members"]:
            rows.append([item["name"], item["amount"], item["count"]])
        title = f"Family member report {summary['month']}"
    elif report_type == "payment-method":
        rows = [["Method", "Amount", "Count"]]
        for item in summary["payment_methods"]:
            rows.append([item["name"], item["amount"], item["count"]])
        title = f"Payment method report {summary['month']}"
    elif report_type == "budget":
        rows = [["Category", "Budget", "Actual", "Remaining", "Status"]]
        for item in dashboard["budget"]["items"]:
            rows.append(
                [
                    item["category_name"],
                    item["budget"],
                    item["actual"],
                    item["difference"],
                    item["status"],
                ]
            )
        title = f"Budget report {summary['month']}"
    elif report_type == "income-vs-expense":
        rows = [
            ["Metric", "Value"],
            ["Income", dashboard["total_income"]],
            ["Expenses", dashboard["total_expenses"]],
            ["Net", dashboard["net_savings"]],
            ["Vs previous expenses", dashboard["vs_previous_month"]["change_amount"]],
        ]
        title = f"Income vs expense {summary['month']}"
    else:
        rows = [
            ["Metric", "Value"],
            ["Allocated savings", dashboard["allocated_savings"]],
            ["Net savings", dashboard["net_savings"]],
            ["Savings rate", analytics["savings_rate"]],
        ]
        title = f"Savings report {summary['month']}"
    return {
        "type": report_type,
        "title": title,
        "month": summary["month"],
        "rows": rows,
        "settlement": build_settlement(family, summary["month"]),
    }


def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def render_csv(report):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([report["title"]])
    writer.writerows([[_stringify(cell) for cell in row] for row in report["rows"]])
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{report["type"]}.csv"'
    return response


def render_xlsx(report):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = report["type"][:31]
    sheet.append([report["title"]])
    for row in report["rows"]:
        sheet.append([_stringify(cell) for cell in row])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{report["type"]}.xlsx"'
    return response


def render_pdf(report):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, report["title"])
    y -= 1.2 * cm
    pdf.setFont("Helvetica", 10)
    for row in report["rows"]:
        pdf.drawString(2 * cm, y, "  |  ".join(_stringify(cell) for cell in row))
        y -= 0.55 * cm
        if y < 2 * cm:
            pdf.showPage()
            y = height - 2 * cm
            pdf.setFont("Helvetica", 10)
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report["type"]}.pdf"'
    return response


def render_report(report, fmt):
    if fmt == "xlsx":
        return render_xlsx(report)
    if fmt == "pdf":
        return render_pdf(report)
    return render_csv(report)
