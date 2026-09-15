from django.urls import path

from imports.views import ExcelImportView, ImportBatchView

urlpatterns = [
    path("imports/excel/", ExcelImportView.as_view(), name="import-excel"),
    path("imports/<uuid:pk>/", ImportBatchView.as_view(), name="import-batch"),
]
