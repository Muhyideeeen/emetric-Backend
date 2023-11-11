from datetime import datetime
from django.utils.translation import gettext_lazy as _

from import_export.formats.base_formats import (
    CSV,
    HTML,
    JSON,
    ODS,
    TSV,
    XLS,
    XLSX,
    YAML,
)
from import_export.resources import ModelResource
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from tablib import Dataset
from django.http import HttpResponse
from core.utils.exception import ExportError, ImportError


TODAY = datetime.now()


EXPORT_FORMATS_DICT = {
    "csv": CSV.CONTENT_TYPE,
    "xls": XLS.CONTENT_TYPE,
    "xlsx": XLSX.CONTENT_TYPE,
    "tsv": TSV.CONTENT_TYPE,
    "ods": ODS.CONTENT_TYPE,
    "yaml": YAML.CONTENT_TYPE,
    "json": JSON.CONTENT_TYPE,
    "html": HTML.CONTENT_TYPE,
}
IMPORT_FORMATS_DICT = EXPORT_FORMATS_DICT


class ExportMixin:
    """Export Mixin"""

    export_filename: str = "Default"
    resource_class: ModelResource = None

    @action(detail=False, methods=["get"])
    def export(self, request, *args, **kwargs):
        filename = self.export_filename
        eformat = request.query_params.get("eformat", "xlsx")

        queryset = self.filter_queryset(self.get_queryset())

        dataset = self.get_resource_class().export(queryset)

        if not hasattr(dataset, eformat):
            raise ExportError(
                detail=_("Unsupport export format"),
                code="unsupport_export_format",
            )

        data, content_type = (
            getattr(dataset, eformat),
            EXPORT_FORMATS_DICT[eformat],
        )

        response = HttpResponse(
            data,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}_{TODAY}.{eformat}"'
            },
            content_type=content_type,
        )
        return response

    def get_resource_class(self):
        if not self.resource_class:
            raise ExportError(detail=_("Pleause set export resource"))
        return self.resource_class()


class ImportMixin:
    """Import Mixin"""

    resource_class: ModelResource = None

    @action(methods=["post"], detail=False)
    def import_data(self, request, *args, **kwargs):
        file = request.FILES["file"]
        extension = file.name.split(".")[-1].lower()
        resource_class = self.get_resource_class()
        dataset = Dataset()

        if extension in IMPORT_FORMATS_DICT and extension not in ['html', 'ods']:
            if extension in ['xls', 'xlsx', 'yaml', 'json']:
                dataset.load(file.read(), format=extension)
            else:
                dataset.load(file.read().decode(), format=extension)
        else:
            raise ImportError(
                "Unsupport import format", code="unsupport_import_format"
            )

        try:
            result = resource_class.import_data(
                dataset,
                dray_run=True,
                collect_failed_rows=True,
                raise_errors=True,
            )
        except AttributeError:
            raise ImportError("Import data failed", code="import_data_failed")

        if not result.has_validation_errors() or result.has_errors():
            result = resource_class.import_data(
                dataset, dry_run=False, raise_errors=True
            )
        else:
            raise ImportError("Import data failed", code="import_data_failed")

        return Response(
            data={"message": "Import successful"},
            status=status.HTTP_201_CREATED,
        )

    def get_resource_class(self):
        if not self.resource_class:
            raise ImportError(detail=_("Please set import resource"))
        return self.resource_class()
