from django.core.exceptions import ValidationError


def validate_file_extension_for_pdf(value):
    if not value.name.endswith(".pdf"):
        raise ValidationError(u"Unsupported file extension.")


def validate_file_extension_for_xlsx(value):
    if not value.name.endswith(".xlsx"):
        raise ValidationError(u"Unsupported file extension.")
