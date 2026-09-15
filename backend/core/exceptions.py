from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def _flatten_errors(detail):
    if isinstance(detail, dict):
        return {key: _flatten_errors(value) for key, value in detail.items()}
    if isinstance(detail, list):
        return [_flatten_errors(item) for item in detail]
    return str(detail)


def _message_from_detail(detail):
    if isinstance(detail, dict):
        for key in ("non_field_errors", "detail"):
            if key in detail:
                return _message_from_detail(detail[key])
        first = next(iter(detail.values()), None)
        return _message_from_detail(first) if first is not None else "Request failed."
    if isinstance(detail, (list, tuple)):
        return _message_from_detail(detail[0]) if detail else "Request failed."
    text = str(detail).strip()
    return text or "Request failed."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    message = _message_from_detail(detail)
    if isinstance(detail, dict):
        errors = _flatten_errors(detail)
    elif isinstance(detail, list):
        errors = {"detail": _flatten_errors(detail)}
    else:
        errors = {"detail": str(detail)}

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response


class FamilyAccessDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have access to this family."
    default_code = "family_denied"
