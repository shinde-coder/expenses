from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from core.mixins import FamilyContextMixin
from core.responses import error_response, success_response
from imports.excel import batch_payload, import_workbook
from imports.models import ImportBatch


class ExcelImportView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return error_response("Upload an Excel file as 'file'.", status=400)
        dry_run = str(request.data.get("dry_run", "true")).lower() in {"1", "true", "yes"}
        lenient = str(request.data.get("lenient", "false")).lower() in {"1", "true", "yes"}
        batch = import_workbook(
            upload,
            family=self.get_family(),
            user=request.user,
            dry_run=dry_run,
            filename=upload.name,
            lenient=lenient,
        )
        return success_response(batch_payload(batch), "Import finished.")


class ImportBatchView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        batch = ImportBatch.objects.filter(family=self.get_family(), pk=pk).first()
        if batch is None:
            return error_response("Import batch not found.", status=404)
        return success_response(batch_payload(batch))
