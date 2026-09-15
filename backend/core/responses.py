from rest_framework.response import Response


def success_response(data=None, message="", status=200, pagination=None):
    payload = {"success": True, "message": message, "data": data}
    if pagination is not None:
        payload["pagination"] = pagination
    return Response(payload, status=status)


def error_response(message="Request failed.", errors=None, status=400):
    return Response(
        {"success": False, "message": message, "errors": errors or {}},
        status=status,
    )
